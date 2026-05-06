"""
layer5_session.py — Session Layer (OSI Layer 5)
Handles session lifecycle, persistence, multiplexing, heartbeat.
"""

import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from config import SESSION, Packet, QoSClass


class SessionState(Enum):
    INIT = "INIT"
    ESTABLISHED = "ESTABLISHED"
    DATA_TRANSFER = "DATA_TRANSFER"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"
    FAILED = "FAILED"


@dataclass
class Session:
    """Represents an active session between two endpoints."""
    session_id: str
    source_id: str
    destination_id: str
    state: SessionState = SessionState.INIT
    created_at: float = 0.0
    last_activity: float = 0.0
    packets_transferred: int = 0
    qos_class: QoSClass = QoSClass.BEST_EFFORT
    setup_delay_ms: float = 0.0
    is_pooled: bool = False


class SessionLayer:
    """
    OSI Layer 5 — Session Layer
    Features:
    - Session lifecycle management (INIT → ESTABLISHED → DATA → CLOSING → CLOSED)
    - Session persistence and connection pooling
    - Multiplexing (multiple sessions per transport connection)
    - Heartbeat mechanism for dead session detection
    - Fast-path session establishment for URLLC traffic
    """

    def __init__(self, params: dict = None):
        self.params = params or SESSION
        self.sessions: Dict[str, Session] = {}
        self.session_pool: Dict[str, Session] = {}
        self.session_counter = 0
        self.metrics_log = []

    # ─── Session Management ──────────────────────

    def _session_key(self, src: str, dst: str) -> str:
        return f"{src}<->{dst}"

    def establish_session(self, packet: Packet, current_time: float) -> Tuple[Session, float]:
        """
        Establish or reuse a session.
        URLLC gets fast-path establishment.
        """
        key = self._session_key(packet.source_id, packet.destination_id)

        # Check session pool first
        if key in self.session_pool and self.session_pool[key].state == SessionState.ESTABLISHED:
            session = self.session_pool[key]
            session.last_activity = current_time
            session.is_pooled = True
            return session, 0.0  # Zero setup delay for pooled sessions

        # Check existing sessions
        if key in self.sessions and self.sessions[key].state in (
            SessionState.ESTABLISHED, SessionState.DATA_TRANSFER
        ):
            session = self.sessions[key]
            session.last_activity = current_time
            return session, 0.0

        # Create new session
        self.session_counter += 1
        session_id = f"SES_{self.session_counter:05d}"

        # Setup delay depends on QoS class
        if packet.qos_class == QoSClass.URLLC:
            setup_delay = self.params["fast_setup_delay_ms"]
        elif packet.qos_class == QoSClass.EMBB:
            setup_delay = self.params["setup_delay_ms"] * 0.7
        else:
            setup_delay = self.params["setup_delay_ms"]

        # Add some variance
        setup_delay *= random.uniform(0.8, 1.2)

        session = Session(
            session_id=session_id,
            source_id=packet.source_id,
            destination_id=packet.destination_id,
            state=SessionState.ESTABLISHED,
            created_at=current_time,
            last_activity=current_time,
            qos_class=packet.qos_class,
            setup_delay_ms=round(setup_delay, 3),
        )

        self.sessions[key] = session
        return session, setup_delay

    def transfer_data(self, session: Session, current_time: float) -> float:
        """Mark session as in data transfer mode. Returns any additional delay."""
        session.state = SessionState.DATA_TRANSFER
        session.packets_transferred += 1
        session.last_activity = current_time
        return 0.0  # No additional delay during transfer

    def close_session(self, session: Session):
        """Close a session and add to pool for reuse."""
        session.state = SessionState.CLOSED
        key = self._session_key(session.source_id, session.destination_id)
        # Pool the session for potential reuse
        pooled_session = Session(
            session_id=session.session_id,
            source_id=session.source_id,
            destination_id=session.destination_id,
            state=SessionState.ESTABLISHED,
            created_at=session.created_at,
            last_activity=session.last_activity,
            qos_class=session.qos_class,
            is_pooled=True,
        )
        self.session_pool[key] = pooled_session

    # ─── Heartbeat ───────────────────────────────

    def check_heartbeats(self, current_time: float) -> int:
        """Check for dead sessions and clean up. Returns number of timed-out sessions."""
        timeout = self.params["session_timeout_s"]
        timed_out = 0
        keys_to_remove = []

        for key, session in self.sessions.items():
            if session.state in (SessionState.ESTABLISHED, SessionState.DATA_TRANSFER):
                if current_time - session.last_activity > timeout:
                    session.state = SessionState.FAILED
                    keys_to_remove.append(key)
                    timed_out += 1

        for key in keys_to_remove:
            del self.sessions[key]

        return timed_out

    # ─── Multiplexing ────────────────────────────

    def active_session_count(self, node_id: str) -> int:
        """Count active sessions for a node."""
        return sum(
            1 for s in self.sessions.values()
            if (s.source_id == node_id or s.destination_id == node_id)
            and s.state in (SessionState.ESTABLISHED, SessionState.DATA_TRANSFER)
        )

    def can_create_session(self, node_id: str) -> bool:
        """Check if node can create new sessions."""
        return self.active_session_count(node_id) < self.params["max_sessions_per_node"]

    # ─── Full Layer Processing ───────────────────

    def process_outgoing(self, packet: Packet, current_time: float) -> dict:
        """Process a packet through the session layer."""
        can_create = self.can_create_session(packet.source_id)

        if not can_create:
            metrics = {
                "session_id": "",
                "session_action": "rejected",
                "setup_delay_ms": 0,
                "session_state": "REJECTED",
                "active_sessions": self.active_session_count(packet.source_id),
                "is_pooled": False,
                "total_delay_ms": 0,
            }
            self.metrics_log.append(metrics)
            return metrics

        session, setup_delay = self.establish_session(packet, current_time)
        transfer_delay = self.transfer_data(session, current_time)
        total_delay = setup_delay + transfer_delay

        # Session header overhead (minimal)
        packet.current_size += 4

        metrics = {
            "session_id": session.session_id,
            "session_action": "reused" if session.is_pooled else "created",
            "setup_delay_ms": round(setup_delay, 3),
            "session_state": session.state.value,
            "active_sessions": self.active_session_count(packet.source_id),
            "is_pooled": session.is_pooled,
            "packets_in_session": session.packets_transferred,
            "total_delay_ms": round(total_delay, 3),
            "overhead_bytes": 4,
        }

        self.metrics_log.append(metrics)
        return metrics

    def get_aggregate_metrics(self) -> dict:
        """Aggregate all session layer metrics."""
        if not self.metrics_log:
            return {}

        total = len(self.metrics_log)
        created = sum(1 for m in self.metrics_log if m["session_action"] == "created")
        reused = sum(1 for m in self.metrics_log if m["session_action"] == "reused")
        rejected = sum(1 for m in self.metrics_log if m["session_action"] == "rejected")
        setup_delays = [m["setup_delay_ms"] for m in self.metrics_log if m["setup_delay_ms"] > 0]
        total_delays = [m["total_delay_ms"] for m in self.metrics_log]

        return {
            "total_session_operations": total,
            "sessions_created": created,
            "sessions_reused": reused,
            "sessions_rejected": rejected,
            "pool_hit_rate": round(reused / (created + reused), 3) if (created + reused) > 0 else 0,
            "avg_setup_delay_ms": round(sum(setup_delays) / len(setup_delays), 3) if setup_delays else 0,
            "avg_total_delay_ms": round(sum(total_delays) / total, 3) if total else 0,
            "active_sessions": len([s for s in self.sessions.values()
                                    if s.state in (SessionState.ESTABLISHED, SessionState.DATA_TRANSFER)]),
            "pooled_sessions": len(self.session_pool),
            "setup_delays": setup_delays,
            "total_delays": total_delays,
        }

    def reset(self):
        self.metrics_log.clear()
        self.sessions.clear()
        self.session_pool.clear()
        self.session_counter = 0

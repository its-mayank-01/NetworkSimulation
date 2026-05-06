"""
layer4_transport.py — Transport Layer (OSI Layer 4)
Handles end-to-end delivery: TCP/UDP modes, flow/congestion control, priority scheduling.
"""

import random
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from config import TRANSPORT, Packet, QoSClass


@dataclass
class TCPState:
    """TCP connection state."""
    cwnd: int = 4              # Congestion window
    ssthresh: int = 32         # Slow-start threshold
    rto_ms: float = 200        # Retransmission timeout
    in_slow_start: bool = True
    ack_count: int = 0
    duplicate_acks: int = 0
    retransmissions: int = 0
    phase: str = "slow_start"  # slow_start, congestion_avoidance, fast_recovery


class TransportLayer:
    """
    OSI Layer 4 — Transport Layer
    Features:
    - TCP-like mode: 3-way handshake, sliding window, congestion control
      (Slow Start → Congestion Avoidance → Fast Recovery)
    - UDP-like mode: fire-and-forget with minimal overhead
    - Priority scheduling (strict priority for URLLC)
    - Segmentation and reassembly
    - Jitter modeling
    """

    def __init__(self, params: dict = None):
        self.params = params or TRANSPORT
        self.connections: Dict[str, TCPState] = {}
        self.metrics_log = []
        self.port_counter = 49152  # Dynamic port range start

    # ─── Port Management ─────────────────────────

    def assign_port(self) -> int:
        """Assign a dynamic port number."""
        port = self.port_counter
        self.port_counter = (self.port_counter + 1 - 49152) % 16384 + 49152
        return port

    # ─── Transport Mode Selection ────────────────

    def select_mode(self, qos_class: QoSClass) -> str:
        """Select transport protocol based on QoS class."""
        if qos_class in (QoSClass.URLLC, QoSClass.MMTC):
            return "UDP"  # Low-latency, minimal overhead
        elif qos_class == QoSClass.EMBB:
            return "TCP"  # Reliable, high-throughput
        else:
            return "TCP"  # Default to reliable

    # ─── TCP Congestion Control ──────────────────

    def _get_tcp_state(self, connection_key: str) -> TCPState:
        """Get or create TCP state for a connection."""
        if connection_key not in self.connections:
            self.connections[connection_key] = TCPState(
                cwnd=self.params["tcp_initial_cwnd"],
                ssthresh=self.params["tcp_ssthresh"],
                rto_ms=self.params["tcp_rto_ms"],
            )
        return self.connections[connection_key]

    def tcp_congestion_control(self, state: TCPState, packet_lost: bool) -> Tuple[str, int]:
        """
        TCP congestion control state machine.
        Returns: (phase_name, current_cwnd)
        """
        if packet_lost:
            # Packet loss detected — enter fast recovery
            state.ssthresh = max(state.cwnd // 2, 2)
            state.cwnd = state.ssthresh + 3
            state.in_slow_start = False
            state.phase = "fast_recovery"
            state.duplicate_acks = 0
        elif state.in_slow_start:
            # Slow start: exponential growth
            state.cwnd = min(state.cwnd * 2, self.params["tcp_max_cwnd"])
            if state.cwnd >= state.ssthresh:
                state.in_slow_start = False
                state.phase = "congestion_avoidance"
            else:
                state.phase = "slow_start"
        else:
            # Congestion avoidance: linear growth
            state.cwnd = min(state.cwnd + 1, self.params["tcp_max_cwnd"])
            state.phase = "congestion_avoidance"

        return state.phase, state.cwnd

    # ─── Handshake ───────────────────────────────

    def tcp_handshake_delay(self) -> float:
        """Simulate 3-way handshake delay (SYN → SYN-ACK → ACK)."""
        rtt_estimate = random.uniform(2, 8)  # ms
        return rtt_estimate * 1.5  # 1.5 RTTs for handshake

    # ─── Segmentation ────────────────────────────

    def segment_count(self, payload_size: int) -> int:
        """Calculate number of segments needed."""
        mss = self.params["segment_size"]
        return max(1, math.ceil(payload_size / mss))

    # ─── Priority Scheduling ─────────────────────

    def scheduling_delay(self, packet: Packet, queue_depth: int = 5) -> float:
        """
        Strict priority scheduling.
        URLLC traffic skips the queue entirely.
        """
        if packet.qos_class == QoSClass.URLLC:
            return 0.1  # Near-instant scheduling
        elif packet.qos_class == QoSClass.EMBB:
            return 0.3 * min(queue_depth, 3)
        elif packet.qos_class == QoSClass.MMTC:
            return 0.5 * min(queue_depth, 5)
        else:
            return 1.0 * min(queue_depth, 10)

    # ─── Jitter ──────────────────────────────────

    def add_jitter(self, base_delay: float) -> float:
        """Add realistic jitter to delay."""
        jitter = max(0, random.gauss(0, self.params["jitter_std_ms"]))
        return base_delay + jitter

    # ─── ACK Processing ──────────────────────────

    def ack_delay(self, path_hops: int) -> float:
        """Calculate ACK round-trip delay."""
        per_hop = random.uniform(0.5, 2.0)
        return path_hops * per_hop * 2  # Round trip

    # ─── Full Layer Processing ───────────────────

    def process_outgoing(self, packet: Packet, physical_corrupted: bool = False) -> dict:
        """Process a packet through the transport layer."""
        mode = self.select_mode(packet.qos_class)
        src_port = self.assign_port()
        dst_port = self.assign_port()
        segments = self.segment_count(packet.current_size)

        total_delay = 0.0
        retransmissions = 0
        cwnd = 0
        tcp_phase = "N/A"
        handshake_ms = 0.0

        if mode == "TCP":
            # TCP processing
            conn_key = f"{packet.source_id}:{src_port}->{packet.destination_id}:{dst_port}"
            tcp_state = self._get_tcp_state(conn_key)

            # Handshake (first connection only)
            if tcp_state.ack_count == 0:
                handshake_ms = self.tcp_handshake_delay()
                total_delay += handshake_ms

            # Congestion control
            phase, cwnd = self.tcp_congestion_control(tcp_state, physical_corrupted)
            tcp_phase = phase

            # TCP retransmission
            if physical_corrupted:
                max_retries = self.params["tcp_max_retries"]
                rto = self.params["tcp_rto_ms"]
                for attempt in range(max_retries):
                    retransmissions += 1
                    total_delay += rto * (2 ** attempt)  # Exponential backoff
                    if random.random() > 0.3:  # Retry success probability
                        break

            # ACK delay
            ack_ms = self.ack_delay(packet.hops or 1)
            total_delay += ack_ms

            # Header overhead
            packet.current_size += self.params["tcp_header_bytes"] * segments
            tcp_state.ack_count += 1

        else:
            # UDP processing — minimal overhead
            packet.current_size += self.params["udp_header_bytes"] * segments

        # Scheduling delay
        sched_delay = self.scheduling_delay(packet)
        total_delay += sched_delay

        # Jitter
        total_delay = self.add_jitter(total_delay)

        # Segmentation overhead delay
        if segments > 1:
            total_delay += 0.1 * segments

        metrics = {
            "protocol": mode,
            "src_port": src_port,
            "dst_port": dst_port,
            "segments": segments,
            "handshake_delay_ms": round(handshake_ms, 3),
            "scheduling_delay_ms": round(sched_delay, 3),
            "total_delay_ms": round(total_delay, 3),
            "retransmissions": retransmissions,
            "tcp_cwnd": cwnd,
            "tcp_phase": tcp_phase,
            "header_overhead_bytes": (
                self.params["tcp_header_bytes"] if mode == "TCP"
                else self.params["udp_header_bytes"]
            ) * segments,
        }

        self.metrics_log.append(metrics)
        return metrics

    def get_aggregate_metrics(self) -> dict:
        """Aggregate all transport layer metrics."""
        if not self.metrics_log:
            return {}

        total = len(self.metrics_log)
        tcp_entries = [m for m in self.metrics_log if m["protocol"] == "TCP"]
        udp_entries = [m for m in self.metrics_log if m["protocol"] == "UDP"]
        delays = [m["total_delay_ms"] for m in self.metrics_log]
        retries = sum(m["retransmissions"] for m in self.metrics_log)
        cwnds = [m["tcp_cwnd"] for m in tcp_entries if m["tcp_cwnd"] > 0]

        phases = {}
        for m in tcp_entries:
            p = m["tcp_phase"]
            phases[p] = phases.get(p, 0) + 1

        return {
            "total_segments_processed": total,
            "tcp_connections": len(tcp_entries),
            "udp_connections": len(udp_entries),
            "tcp_ratio": round(len(tcp_entries) / total, 3) if total else 0,
            "avg_delay_ms": round(sum(delays) / total, 3) if total else 0,
            "max_delay_ms": round(max(delays), 3) if delays else 0,
            "min_delay_ms": round(min(delays), 3) if delays else 0,
            "total_retransmissions": retries,
            "avg_cwnd": round(sum(cwnds) / len(cwnds), 1) if cwnds else 0,
            "tcp_phases": phases,
            "delay_values": delays,
            "cwnd_values": cwnds,
        }

    def reset(self):
        self.metrics_log.clear()
        self.connections.clear()
        self.port_counter = 49152

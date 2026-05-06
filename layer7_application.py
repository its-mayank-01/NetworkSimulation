"""
layer7_application.py — Application Layer (OSI Layer 7)
Handles application protocols, QoS classification, message generation.
"""

import random
from dataclasses import dataclass
from typing import List, Dict, Optional
from config import (
    Packet, QoSClass, QOS_REQUIREMENTS, MESSAGE_TYPES,
    NodeType, EMERGENCY_VEHICLES, BASE_STATIONS, IOT_DEVICES,
)


class ApplicationLayer:
    """
    OSI Layer 7 — Application Layer
    Features:
    - Application protocol simulation (Emergency SOS, Video, Telemetry, General)
    - QoS policy engine with traffic classification
    - Realistic traffic generation per node type
    - Application-level ACK for critical messages
    - Adaptive message rate based on network conditions
    """

    def __init__(self):
        self.packet_counter = 0
        self.metrics_log = []
        self.delivery_log = []

    # ─── Traffic Generation ──────────────────────

    def generate_messages(
        self, nodes: list, current_time: float, network_load: float = 0.0
    ) -> List[Packet]:
        """
        Generate messages from all nodes based on their type and traffic patterns.
        Adapts message rate based on network load.
        """
        packets = []

        for node in nodes:
            node_type = node["type"]
            node_id = node["id"]

            # Determine which message types this node generates
            msg_types = self._get_node_message_types(node_type)

            for msg_type_name in msg_types:
                spec = MESSAGE_TYPES[msg_type_name]
                rate = spec["rate"]

                # Adaptive rate: reduce non-critical traffic under high load
                if network_load > 0.7 and spec["qos_class"] == QoSClass.BEST_EFFORT:
                    rate *= 0.5
                elif network_load > 0.9 and spec["qos_class"] == QoSClass.MMTC:
                    rate *= 0.7

                if random.random() <= rate:
                    destination = self._choose_destination(node, nodes, msg_type_name)
                    if destination is None:
                        continue

                    self.packet_counter += 1
                    qos = spec["qos_class"]
                    qos_req = QOS_REQUIREMENTS[qos]

                    packet = Packet(
                        packet_id=self.packet_counter,
                        qos_class=qos,
                        message_type=msg_type_name,
                        source_id=node_id,
                        destination_id=destination,
                        payload_size=spec["size_bytes"],
                        created_at=current_time,
                        priority=qos_req["priority"],
                        deadline_ms=qos_req["max_delay_ms"],
                    )

                    packets.append(packet)

        # Sort by priority (highest first)
        packets.sort(key=lambda p: p.priority, reverse=True)

        # Log generation metrics
        if packets:
            by_qos = {}
            for p in packets:
                q = p.qos_class.value
                by_qos[q] = by_qos.get(q, 0) + 1

            self.metrics_log.append({
                "time": current_time,
                "packets_generated": len(packets),
                "by_qos_class": by_qos,
                "network_load": network_load,
            })

        return packets

    def _get_node_message_types(self, node_type: NodeType) -> List[str]:
        """Determine which message types a node can generate."""
        if node_type in EMERGENCY_VEHICLES:
            return ["emergency_sos", "collision_alert", "status_update"]
        elif node_type in BASE_STATIONS:
            return ["dispatch_command", "video_stream"]
        elif node_type in IOT_DEVICES:
            return ["sensor_telemetry"]
        return ["status_update"]

    def _choose_destination(self, source_node: dict, all_nodes: list, msg_type: str) -> Optional[str]:
        """Choose appropriate destination based on message type."""
        source_id = source_node["id"]
        source_type = source_node["type"]

        if msg_type == "emergency_sos":
            # SOS goes to nearest hospital or dispatch
            targets = [n for n in all_nodes if n["type"] in BASE_STATIONS and n["id"] != source_id]
        elif msg_type == "collision_alert":
            # Collision alert goes to nearby vehicles
            targets = [n for n in all_nodes if n["type"] in EMERGENCY_VEHICLES and n["id"] != source_id]
        elif msg_type == "dispatch_command":
            # Dispatch goes to emergency vehicles
            targets = [n for n in all_nodes if n["type"] in EMERGENCY_VEHICLES]
        elif msg_type == "video_stream":
            # Video streams to hospitals
            targets = [n for n in all_nodes if n["type"] == NodeType.HOSPITAL]
        elif msg_type == "sensor_telemetry":
            # Sensor data goes to dispatch or hospital
            targets = [n for n in all_nodes if n["type"] in BASE_STATIONS]
        else:
            # General traffic to anyone
            targets = [n for n in all_nodes if n["id"] != source_id]

        if not targets:
            targets = [n for n in all_nodes if n["id"] != source_id]

        return random.choice(targets)["id"] if targets else None

    # ─── QoS Classification ──────────────────────

    def classify_qos(self, packet: Packet) -> dict:
        """Classify and tag packet with QoS parameters."""
        qos_req = QOS_REQUIREMENTS[packet.qos_class]
        return {
            "qos_class": packet.qos_class.value,
            "priority": packet.priority,
            "max_delay_ms": qos_req["max_delay_ms"],
            "min_reliability": qos_req["min_reliability"],
            "description": qos_req["description"],
        }

    # ─── Application-Level Processing ────────────

    def process_outgoing(self, packet: Packet) -> dict:
        """Process a packet at the application layer."""
        qos_info = self.classify_qos(packet)

        # Application header overhead
        app_overhead = 16  # Application protocol header
        packet.current_size += app_overhead

        # Application processing delay
        if packet.qos_class == QoSClass.URLLC:
            app_delay = 0.1  # Fast path
        elif packet.qos_class == QoSClass.EMBB:
            app_delay = 0.5  # Video processing
        else:
            app_delay = 0.3  # Standard

        app_delay *= random.uniform(0.8, 1.2)

        metrics = {
            "packet_id": packet.packet_id,
            "message_type": packet.message_type,
            "qos_class": qos_info["qos_class"],
            "priority": qos_info["priority"],
            "payload_size_bytes": packet.payload_size,
            "app_overhead_bytes": app_overhead,
            "app_delay_ms": round(app_delay, 3),
            "deadline_ms": packet.deadline_ms,
            "source": packet.source_id,
            "destination": packet.destination_id,
        }

        return metrics

    # ─── Delivery Verification ───────────────────

    def verify_delivery(self, packet: Packet) -> dict:
        """Verify if packet met its QoS requirements."""
        qos_req = QOS_REQUIREMENTS[packet.qos_class]

        delay_met = packet.total_delay_ms <= qos_req["max_delay_ms"]
        delivered = packet.delivered and not packet.dropped

        result = {
            "packet_id": packet.packet_id,
            "qos_class": packet.qos_class.value,
            "message_type": packet.message_type,
            "delivered": delivered,
            "total_delay_ms": round(packet.total_delay_ms, 3),
            "deadline_ms": qos_req["max_delay_ms"],
            "delay_met": delay_met,
            "qos_satisfied": delivered and delay_met,
            "source": packet.source_id,
            "destination": packet.destination_id,
        }

        self.delivery_log.append(result)
        return result

    def get_aggregate_metrics(self) -> dict:
        """Aggregate all application layer metrics."""
        if not self.delivery_log:
            return {}

        total = len(self.delivery_log)
        delivered = sum(1 for d in self.delivery_log if d["delivered"])
        qos_satisfied = sum(1 for d in self.delivery_log if d["qos_satisfied"])
        delays = [d["total_delay_ms"] for d in self.delivery_log if d["delivered"]]

        # Per QoS class breakdown
        by_qos = {}
        for qos_class in QoSClass:
            qos_entries = [d for d in self.delivery_log if d["qos_class"] == qos_class.value]
            if not qos_entries:
                continue
            qos_delivered = sum(1 for d in qos_entries if d["delivered"])
            qos_met = sum(1 for d in qos_entries if d["qos_satisfied"])
            qos_delays = [d["total_delay_ms"] for d in qos_entries if d["delivered"]]

            by_qos[qos_class.value] = {
                "total": len(qos_entries),
                "delivered": qos_delivered,
                "delivery_rate": round(qos_delivered / len(qos_entries), 4),
                "qos_satisfied": qos_met,
                "qos_satisfaction_rate": round(qos_met / len(qos_entries), 4),
                "avg_delay_ms": round(sum(qos_delays) / len(qos_delays), 3) if qos_delays else 0,
            }

        # Per message type breakdown
        by_type = {}
        for d in self.delivery_log:
            mt = d["message_type"]
            if mt not in by_type:
                by_type[mt] = {"total": 0, "delivered": 0, "qos_met": 0}
            by_type[mt]["total"] += 1
            if d["delivered"]:
                by_type[mt]["delivered"] += 1
            if d["qos_satisfied"]:
                by_type[mt]["qos_met"] += 1

        # Generation stats
        total_generated = sum(m["packets_generated"] for m in self.metrics_log)

        return {
            "total_generated": total_generated,
            "total_processed": total,
            "delivered": delivered,
            "delivery_rate": round(delivered / total, 4) if total else 0,
            "overall_qos_satisfaction": round(qos_satisfied / total, 4) if total else 0,
            "avg_delay_ms": round(sum(delays) / len(delays), 3) if delays else 0,
            "by_qos_class": by_qos,
            "by_message_type": by_type,
            "delay_values": delays,
        }

    def reset(self):
        self.metrics_log.clear()
        self.delivery_log.clear()
        self.packet_counter = 0

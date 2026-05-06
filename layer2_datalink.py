"""
layer2_datalink.py — Data Link Layer (OSI Layer 2)
Handles framing, CRC error detection, ARQ, MAC access control, flow control.
"""

import binascii
import random
import struct
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from config import DATALINK, Packet, QoSClass


@dataclass
class Frame:
    """Data Link frame with header, payload, and CRC."""
    frame_id: int
    src_mac: str
    dst_mac: str
    frame_type: int      # 0x0800 = IP, 0x0806 = ARP
    sequence_num: int
    payload_size: int
    total_size: int
    crc: int
    is_valid: bool = True


class DataLinkLayer:
    """
    OSI Layer 2 — Data Link Layer
    Features:
    - Frame construction with MAC addressing
    - CRC-32 error detection
    - Selective Repeat ARQ (configurable)
    - Priority-based TDMA MAC sublayer
    - Sliding window flow control
    """

    def __init__(self, params: dict = None):
        self.params = params or DATALINK
        self.mac_table = {}
        self.sequence_counter = 0
        self.metrics_log = []
        self._next_mac_id = 1

    # ─── MAC Address Management ──────────────────

    def assign_mac(self, node_id: str) -> str:
        """Assign a MAC address to a node."""
        if node_id not in self.mac_table:
            mac_bytes = struct.pack(">I", self._next_mac_id)
            mac = "5G:" + ":".join(f"{b:02X}" for b in mac_bytes[-3:])
            self.mac_table[node_id] = mac
            self._next_mac_id += 1
        return self.mac_table[node_id]

    def get_mac(self, node_id: str) -> str:
        return self.mac_table.get(node_id, self.assign_mac(node_id))

    # ─── Frame Construction ──────────────────────

    def create_frame(self, src_id: str, dst_id: str, payload_size: int) -> Frame:
        """Build a frame with header and CRC."""
        src_mac = self.get_mac(src_id)
        dst_mac = self.get_mac(dst_id)
        self.sequence_counter += 1

        header_size = self.params["frame_header_bytes"]
        crc_size = self.params["crc_bytes"]
        total_size = header_size + payload_size + crc_size

        # Simulate CRC-32 calculation
        fake_payload = bytes(payload_size % 256 for _ in range(min(payload_size, 64)))
        crc = binascii.crc32(fake_payload) & 0xFFFFFFFF

        return Frame(
            frame_id=self.sequence_counter,
            src_mac=src_mac,
            dst_mac=dst_mac,
            frame_type=0x0800,
            sequence_num=self.sequence_counter,
            payload_size=payload_size,
            total_size=total_size,
            crc=crc,
        )

    # ─── Error Detection ─────────────────────────

    def check_crc(self, frame: Frame, bit_corrupted: bool) -> bool:
        """Verify frame integrity using CRC-32."""
        if bit_corrupted:
            frame.is_valid = False
            return False
        frame.is_valid = True
        return True

    # ─── ARQ Protocol ────────────────────────────

    def selective_repeat_arq(
        self, packet: Packet, physical_corrupted: bool
    ) -> Tuple[bool, int, float]:
        """
        Selective Repeat ARQ: retransmit only failed frames.
        Returns: (success, retransmission_count, total_arq_delay_ms)
        """
        max_retries = self.params["arq_max_retries"]
        timeout = self.params["arq_timeout_ms"]
        window_size = self.params["arq_window_size"]

        # Adjust based on priority — URLLC gets fewer retries but faster timeout
        if packet.qos_class == QoSClass.URLLC:
            max_retries = min(max_retries, 1)
            timeout = timeout * 0.5
        elif packet.qos_class == QoSClass.EMBB:
            max_retries = max_retries
            timeout = timeout * 0.8

        retries = 0
        arq_delay = 0.0

        if physical_corrupted:
            # Frame was corrupted — need retransmission
            for attempt in range(max_retries):
                retries += 1
                arq_delay += timeout
                # Each retry has better chance (adaptive — lower error on retry)
                retry_fail_prob = 0.3 * (0.5 ** attempt)
                if random.random() > retry_fail_prob:
                    return True, retries, arq_delay
            return False, retries, arq_delay

        return True, 0, 0.0

    # ─── MAC Access Control ──────────────────────

    def mac_access_delay(self, packet: Packet, current_load: float = 0.5) -> float:
        """
        Priority-based TDMA MAC.
        Emergency traffic gets dedicated slots with near-zero wait.
        """
        slot_duration = self.params["tdma_slot_duration_ms"]
        priority_ratio = self.params["priority_slots_ratio"]

        if packet.qos_class == QoSClass.URLLC:
            # Guaranteed priority slot — minimal delay
            delay = slot_duration * random.uniform(0.1, 0.3)
        elif packet.qos_class == QoSClass.EMBB:
            # High priority — short wait
            delay = slot_duration * random.uniform(0.5, 1.5)
        elif packet.qos_class == QoSClass.MMTC:
            # Medium priority — normal contention
            contention_slots = max(1, int(current_load * 4))
            delay = slot_duration * contention_slots * random.uniform(0.8, 1.2)
        else:
            # Best effort — wait for available slot
            contention_slots = max(2, int(current_load * 8))
            delay = slot_duration * contention_slots * random.uniform(1.0, 2.0)

        return delay

    # ─── Flow Control ────────────────────────────

    def flow_control_delay(self, packet: Packet, link_utilization: float = 0.5) -> float:
        """Sliding window flow control delay based on utilization."""
        window_size = self.params["arq_window_size"]
        if link_utilization > 0.8:
            # Congested — reduce window, increase delay
            effective_window = max(1, int(window_size * (1 - link_utilization)))
            return 0.5 * (window_size / effective_window)
        return 0.1  # Minimal flow control overhead

    # ─── Full Layer Processing ───────────────────

    def process_outgoing(
        self, packet: Packet, physical_corrupted: bool, link_utilization: float = 0.5
    ) -> dict:
        """
        Process a packet through the data link layer (outgoing).
        Returns per-layer metrics.
        """
        # Frame construction
        frame = self.create_frame(packet.source_id, packet.destination_id, packet.current_size)

        # Overhead added
        overhead = self.params["frame_header_bytes"] + self.params["crc_bytes"]
        packet.current_size += overhead

        # MAC access
        mac_delay = self.mac_access_delay(packet, link_utilization)

        # CRC check
        crc_valid = self.check_crc(frame, physical_corrupted)

        # ARQ
        arq_success, retries, arq_delay = self.selective_repeat_arq(packet, physical_corrupted)

        # Flow control
        fc_delay = self.flow_control_delay(packet, link_utilization)

        total_delay = mac_delay + arq_delay + fc_delay

        metrics = {
            "frame_id": frame.frame_id,
            "src_mac": frame.src_mac,
            "dst_mac": frame.dst_mac,
            "frame_size_bytes": frame.total_size,
            "overhead_bytes": overhead,
            "crc_valid": crc_valid,
            "arq_success": arq_success,
            "retransmissions": retries,
            "arq_delay_ms": round(arq_delay, 3),
            "mac_access_delay_ms": round(mac_delay, 3),
            "flow_control_delay_ms": round(fc_delay, 3),
            "total_delay_ms": round(total_delay, 3),
            "link_utilization": link_utilization,
        }

        self.metrics_log.append(metrics)
        return metrics

    def get_aggregate_metrics(self) -> dict:
        """Aggregate all data link layer metrics."""
        if not self.metrics_log:
            return {}

        total = len(self.metrics_log)
        crc_failures = sum(1 for m in self.metrics_log if not m["crc_valid"])
        arq_failures = sum(1 for m in self.metrics_log if not m["arq_success"])
        total_retries = sum(m["retransmissions"] for m in self.metrics_log)
        mac_delays = [m["mac_access_delay_ms"] for m in self.metrics_log]
        arq_delays = [m["arq_delay_ms"] for m in self.metrics_log]
        total_delays = [m["total_delay_ms"] for m in self.metrics_log]
        overhead = [m["overhead_bytes"] for m in self.metrics_log]

        return {
            "total_frames": total,
            "crc_failure_rate": round(crc_failures / total, 4) if total else 0,
            "arq_failure_rate": round(arq_failures / total, 4) if total else 0,
            "total_retransmissions": total_retries,
            "avg_retransmissions": round(total_retries / total, 3) if total else 0,
            "avg_mac_delay_ms": round(sum(mac_delays) / total, 3) if total else 0,
            "avg_arq_delay_ms": round(sum(arq_delays) / total, 3) if total else 0,
            "avg_total_delay_ms": round(sum(total_delays) / total, 3) if total else 0,
            "avg_overhead_bytes": round(sum(overhead) / total, 1) if total else 0,
            "throughput_efficiency": round(
                1 - (sum(overhead) / sum(m["frame_size_bytes"] for m in self.metrics_log)), 4
            ) if total else 0,
            "mac_delays": mac_delays,
            "arq_delays": arq_delays,
            "total_delays": total_delays,
        }

    def reset(self):
        self.metrics_log.clear()
        self.sequence_counter = 0

"""
layer6_presentation.py — Presentation Layer (OSI Layer 6)
Handles data encoding, encryption, and compression.
"""

import random
from dataclasses import dataclass
from typing import Dict, Tuple
from config import PRESENTATION, Packet, QoSClass


@dataclass
class PresentationResult:
    """Result of presentation layer processing."""
    original_size: int
    compressed_size: int
    encrypted_size: int
    final_size: int
    compression_ratio: float
    encryption_type: str
    encoding_type: str
    processing_delay_ms: float


class PresentationLayer:
    """
    OSI Layer 6 — Presentation Layer
    Features:
    - AES-256 encryption simulation (with overhead modeling)
    - Adaptive compression (different ratios for different data types)
    - Data encoding (binary serialization)
    - Priority-aware processing (lighter encryption for URLLC)
    """

    def __init__(self, params: dict = None):
        self.params = params or PRESENTATION
        self.metrics_log = []

    # ─── Encryption ──────────────────────────────

    def encrypt(self, packet: Packet) -> Tuple[int, float, str]:
        """
        Apply encryption based on QoS class.
        URLLC: lightweight encryption (speed priority)
        eMBB: full AES-256 encryption
        mMTC: lightweight encryption (power efficiency)
        BestEffort: standard encryption
        Returns: (overhead_bytes, delay_ms, encryption_type)
        """
        if packet.qos_class == QoSClass.URLLC:
            overhead = self.params["encryption_overhead_bytes"] // 2  # Lightweight
            delay = self.params["light_encryption_delay_ms"]
            enc_type = "AES-128-Light"
        elif packet.qos_class == QoSClass.EMBB:
            overhead = self.params["encryption_overhead_bytes"]
            delay = self.params["encryption_delay_ms"]
            enc_type = "AES-256-Full"
        elif packet.qos_class == QoSClass.MMTC:
            overhead = self.params["encryption_overhead_bytes"] // 2
            delay = self.params["light_encryption_delay_ms"]
            enc_type = "AES-128-Light"
        else:
            overhead = self.params["encryption_overhead_bytes"]
            delay = self.params["encryption_delay_ms"] * 0.8
            enc_type = "AES-256-Std"

        # Add slight variance
        delay *= random.uniform(0.9, 1.1)
        return overhead, delay, enc_type

    # ─── Compression ─────────────────────────────

    def compress(self, packet: Packet) -> Tuple[float, float]:
        """
        Apply compression based on message type.
        Returns: (compression_ratio, delay_ms)
        """
        msg_type = packet.message_type

        if msg_type == "video_stream":
            ratio = self.params["compression_ratio_video"]
        elif msg_type in ("sensor_telemetry",):
            ratio = self.params["compression_ratio_telemetry"]
        elif msg_type in ("emergency_sos", "collision_alert", "dispatch_command"):
            ratio = 0.90  # Minimal compression for critical small messages
        else:
            ratio = self.params["compression_ratio_text"]

        # URLLC: skip compression entirely (speed priority)
        if packet.qos_class == QoSClass.URLLC:
            ratio = 1.0
            delay = 0.0
        else:
            delay = self.params["compression_delay_ms"] * random.uniform(0.8, 1.2)
            # Larger payloads take longer to compress
            delay *= 1 + (packet.current_size / 10000)

        return ratio, delay

    # ─── Encoding ────────────────────────────────

    def encode(self, packet: Packet) -> Tuple[int, float]:
        """
        Apply data encoding/serialization.
        Returns: (overhead_bytes, delay_ms)
        """
        overhead = self.params["encoding_overhead_bytes"]
        delay = 0.05  # Encoding is fast
        return overhead, delay

    # ─── Full Layer Processing ───────────────────

    def process_outgoing(self, packet: Packet) -> dict:
        """Process a packet through the presentation layer."""
        original_size = packet.current_size

        # Step 1: Compression
        comp_ratio, comp_delay = self.compress(packet)
        compressed_size = int(original_size * comp_ratio)

        # Step 2: Encryption
        enc_overhead, enc_delay, enc_type = self.encrypt(packet)
        encrypted_size = compressed_size + enc_overhead

        # Step 3: Encoding
        enc_bytes, encoding_delay = self.encode(packet)
        final_size = encrypted_size + enc_bytes

        # Update packet size
        packet.current_size = final_size

        total_delay = comp_delay + enc_delay + encoding_delay

        actual_ratio = round(final_size / original_size, 3) if original_size > 0 else 1.0

        metrics = {
            "original_size_bytes": original_size,
            "compressed_size_bytes": compressed_size,
            "encrypted_size_bytes": encrypted_size,
            "final_size_bytes": final_size,
            "compression_ratio": round(comp_ratio, 3),
            "actual_size_ratio": actual_ratio,
            "encryption_type": enc_type,
            "encryption_overhead_bytes": enc_overhead,
            "encoding_overhead_bytes": enc_bytes,
            "compression_delay_ms": round(comp_delay, 3),
            "encryption_delay_ms": round(enc_delay, 3),
            "encoding_delay_ms": round(encoding_delay, 3),
            "total_delay_ms": round(total_delay, 3),
        }

        self.metrics_log.append(metrics)
        return metrics

    def get_aggregate_metrics(self) -> dict:
        """Aggregate all presentation layer metrics."""
        if not self.metrics_log:
            return {}

        total = len(self.metrics_log)
        orig_sizes = [m["original_size_bytes"] for m in self.metrics_log]
        final_sizes = [m["final_size_bytes"] for m in self.metrics_log]
        comp_ratios = [m["compression_ratio"] for m in self.metrics_log]
        delays = [m["total_delay_ms"] for m in self.metrics_log]

        enc_types = {}
        for m in self.metrics_log:
            et = m["encryption_type"]
            enc_types[et] = enc_types.get(et, 0) + 1

        total_original = sum(orig_sizes)
        total_final = sum(final_sizes)

        return {
            "total_processed": total,
            "avg_compression_ratio": round(sum(comp_ratios) / total, 3),
            "overall_size_ratio": round(total_final / total_original, 3) if total_original > 0 else 1,
            "total_bytes_saved": total_original - total_final,
            "avg_processing_delay_ms": round(sum(delays) / total, 3),
            "encryption_distribution": enc_types,
            "compression_ratios": comp_ratios,
            "delay_values": delays,
            "size_before": orig_sizes,
            "size_after": final_sizes,
        }

    def reset(self):
        self.metrics_log.clear()

"""
layer1_physical.py — Physical Layer (OSI Layer 1)
Handles raw bit transmission: channel modeling, modulation, BER, power control.
"""

import math
import random
import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional
from config import PHYSICAL, MODULATION_SCHEMES, Packet, QoSClass


@dataclass
class ChannelState:
    """Snapshot of channel conditions for a link."""
    distance_m: float
    path_loss_db: float
    shadow_fading_db: float
    rayleigh_fading_db: float
    total_loss_db: float
    snr_db: float
    selected_modulation: str
    ber: float
    spectral_efficiency: float
    tx_power_dbm: float
    rx_power_dbm: float


class PhysicalLayer:
    """
    OSI Layer 1 — Physical Layer
    Models realistic 5G wireless channel with:
    - Log-distance path loss model
    - Log-normal shadow fading
    - Rayleigh flat fading
    - Adaptive modulation (BPSK/QPSK/16-QAM/64-QAM)
    - BER calculation per modulation scheme
    - Power control
    """

    def __init__(self, params: dict = None):
        self.params = params or PHYSICAL
        self.noise_power_dbm = self._calc_noise_power()
        self.link_cache = {}
        self.metrics_log = []

    def _calc_noise_power(self) -> float:
        """Calculate receiver noise power in dBm."""
        bw_hz = self.params["bandwidth_mhz"] * 1e6
        noise_dbm = self.params["thermal_noise_dbm_hz"] + 10 * math.log10(bw_hz)
        return noise_dbm + self.params["noise_figure_db"]

    # ─── Channel Modeling ────────────────────────

    def path_loss(self, distance_m: float) -> float:
        """Log-distance path loss model with urban environment."""
        if distance_m <= 0:
            distance_m = 0.1
        d0 = self.params["reference_distance_m"]
        pl0 = self.params["reference_loss_db"]
        n = self.params["path_loss_exponent"]
        return pl0 + 10 * n * math.log10(max(distance_m / d0, 0.01))

    def shadow_fading(self) -> float:
        """Log-normal shadow fading (slow fading)."""
        return np.random.normal(0, self.params["shadow_std_db"])

    def rayleigh_fading(self) -> float:
        """Rayleigh flat fading magnitude in dB."""
        h = np.random.rayleigh(self.params["rayleigh_scale"])
        return 20 * math.log10(max(h, 1e-10))

    def calculate_snr(self, distance_m: float, tx_power_dbm: float = None) -> ChannelState:
        """Calculate full channel state including SNR for a link."""
        tx_power = tx_power_dbm or self.params["tx_power_dbm"]

        pl = self.path_loss(distance_m)
        sf = self.shadow_fading()
        rf = self.rayleigh_fading()

        total_loss = pl + abs(sf) - max(rf, -20)  # Clamp extreme fading
        rx_power = tx_power - total_loss
        snr_db = rx_power - self.noise_power_dbm

        mod, ber, spec_eff = self.select_modulation(snr_db)

        return ChannelState(
            distance_m=distance_m,
            path_loss_db=round(pl, 2),
            shadow_fading_db=round(sf, 2),
            rayleigh_fading_db=round(rf, 2),
            total_loss_db=round(total_loss, 2),
            snr_db=round(snr_db, 2),
            selected_modulation=mod,
            ber=ber,
            spectral_efficiency=spec_eff,
            tx_power_dbm=tx_power,
            rx_power_dbm=round(rx_power, 2),
        )

    # ─── Modulation ──────────────────────────────

    def select_modulation(self, snr_db: float) -> Tuple[str, float, float]:
        """Adaptive modulation: choose best scheme for current SNR."""
        selected = "BPSK"
        for name, spec in MODULATION_SCHEMES.items():
            if snr_db >= spec["snr_threshold_db"]:
                selected = name
        ber = self.calculate_ber(snr_db, selected)
        spec_eff = MODULATION_SCHEMES[selected]["spectral_eff"]
        return selected, ber, spec_eff

    def calculate_ber(self, snr_db: float, modulation: str) -> float:
        """Analytical BER for given modulation and SNR."""
        snr_linear = 10 ** (snr_db / 10)
        if snr_linear <= 0:
            return 0.5  # No signal

        if modulation == "BPSK":
            ber = 0.5 * math.erfc(math.sqrt(snr_linear))
        elif modulation == "QPSK":
            ber = 0.5 * math.erfc(math.sqrt(snr_linear))
        elif modulation == "16-QAM":
            ber = (3 / 8) * math.erfc(math.sqrt(snr_linear * 2 / 5))
        elif modulation == "64-QAM":
            ber = (7 / 24) * math.erfc(math.sqrt(snr_linear * 1 / 7))
        else:
            ber = 0.5

        return max(ber, 1e-12)

    # ─── Power Control ───────────────────────────

    def adaptive_power(self, distance_m: float, qos_class: QoSClass) -> float:
        """Adjust transmit power based on distance and priority."""
        base_power = self.params["tx_power_dbm"]
        # Boost power for critical traffic
        if qos_class == QoSClass.URLLC:
            boost = 3.0  # +3 dB for emergency
        elif qos_class == QoSClass.EMBB:
            boost = 1.5
        else:
            boost = 0.0
        # Distance-based adjustment
        if distance_m > 200:
            boost += 2.0
        return min(base_power + boost, base_power + 6)  # Cap at +6 dB

    # ─── Transmission Delay ──────────────────────

    def transmission_delay_ms(self, size_bytes: int, spectral_efficiency: float) -> float:
        """Calculate transmission delay based on data size and modulation."""
        bw_hz = self.params["bandwidth_mhz"] * 1e6
        data_rate_bps = bw_hz * spectral_efficiency
        if data_rate_bps <= 0:
            return 1000.0
        delay_s = (size_bytes * 8) / data_rate_bps
        return delay_s * 1000

    def propagation_delay_ms(self, distance_m: float) -> float:
        """Signal propagation delay (speed of light)."""
        c = 3e8  # m/s
        return (distance_m / c) * 1000

    # ─── Packet Processing ───────────────────────

    def process_link(self, packet: Packet, distance_m: float) -> dict:
        """
        Process a packet over a single physical link.
        Returns metrics dict for this layer.
        """
        tx_power = self.adaptive_power(distance_m, packet.qos_class)
        channel = self.calculate_snr(distance_m, tx_power)

        # Calculate delays
        tx_delay = self.transmission_delay_ms(packet.current_size, channel.spectral_efficiency)
        prop_delay = self.propagation_delay_ms(distance_m)
        total_delay = tx_delay + prop_delay

        # Determine if bits are corrupted based on BER
        n_bits = packet.current_size * 8
        packet_error_prob = 1 - (1 - channel.ber) ** n_bits
        corrupted = random.random() < packet_error_prob

        metrics = {
            "distance_m": round(distance_m, 2),
            "tx_power_dbm": tx_power,
            "rx_power_dbm": channel.rx_power_dbm,
            "snr_db": channel.snr_db,
            "path_loss_db": channel.path_loss_db,
            "modulation": channel.selected_modulation,
            "ber": channel.ber,
            "spectral_efficiency_bps_hz": channel.spectral_efficiency,
            "tx_delay_ms": round(tx_delay, 4),
            "propagation_delay_ms": round(prop_delay, 6),
            "total_delay_ms": round(total_delay, 4),
            "corrupted": corrupted,
            "packet_error_prob": round(packet_error_prob, 6),
        }

        self.metrics_log.append(metrics)
        return metrics

    def get_aggregate_metrics(self) -> dict:
        """Aggregate all recorded link metrics."""
        if not self.metrics_log:
            return {}
        snrs = [m["snr_db"] for m in self.metrics_log]
        bers = [m["ber"] for m in self.metrics_log]
        delays = [m["total_delay_ms"] for m in self.metrics_log]
        corrupted = sum(1 for m in self.metrics_log if m["corrupted"])
        mods = {}
        for m in self.metrics_log:
            mod = m["modulation"]
            mods[mod] = mods.get(mod, 0) + 1

        return {
            "total_transmissions": len(self.metrics_log),
            "avg_snr_db": round(np.mean(snrs), 2),
            "min_snr_db": round(min(snrs), 2),
            "max_snr_db": round(max(snrs), 2),
            "avg_ber": float(np.mean(bers)),
            "avg_delay_ms": round(np.mean(delays), 4),
            "corruption_rate": round(corrupted / len(self.metrics_log), 4),
            "modulation_distribution": mods,
            "snr_values": snrs,
            "ber_values": bers,
            "delay_values": delays,
        }

    def reset(self):
        self.metrics_log.clear()
        self.link_cache.clear()

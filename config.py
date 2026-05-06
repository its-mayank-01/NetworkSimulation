"""
config.py — System Configuration & QoS Definitions
5G Smart City Emergency Response Network Simulation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import enum


# ─────────────────────────────────────────────
# QoS Traffic Classes (3GPP 5G-aligned)
# ─────────────────────────────────────────────

class QoSClass(enum.Enum):
    URLLC = "URLLC"            # Ultra-Reliable Low-Latency Communication
    EMBB = "eMBB"              # Enhanced Mobile Broadband
    MMTC = "mMTC"              # Massive Machine-Type Communication
    BEST_EFFORT = "BestEffort" # Best Effort


QOS_REQUIREMENTS = {
    QoSClass.URLLC: {
        "max_delay_ms": 10,
        "min_reliability": 0.99999,
        "min_throughput_kbps": 0,
        "priority": 4,
        "description": "Emergency SOS alerts",
    },
    QoSClass.EMBB: {
        "max_delay_ms": 100,
        "min_reliability": 0.95,
        "min_throughput_kbps": 5000,
        "priority": 3,
        "description": "Live ambulance video feed",
    },
    QoSClass.MMTC: {
        "max_delay_ms": 500,
        "min_reliability": 0.90,
        "min_throughput_kbps": 100,
        "priority": 2,
        "description": "IoT sensor telemetry",
    },
    QoSClass.BEST_EFFORT: {
        "max_delay_ms": 2000,
        "min_reliability": 0.80,
        "min_throughput_kbps": 0,
        "priority": 1,
        "description": "Infotainment / logs",
    },
}


# ─────────────────────────────────────────────
# Message Types
# ─────────────────────────────────────────────

MESSAGE_TYPES = {
    "emergency_sos": {
        "qos_class": QoSClass.URLLC,
        "size_bytes": 256,
        "rate": 0.15,
        "description": "Emergency SOS alert",
    },
    "collision_alert": {
        "qos_class": QoSClass.URLLC,
        "size_bytes": 512,
        "rate": 0.10,
        "description": "Collision / hazard alert",
    },
    "video_stream": {
        "qos_class": QoSClass.EMBB,
        "size_bytes": 8192,
        "rate": 0.25,
        "description": "Live camera / video feed",
    },
    "sensor_telemetry": {
        "qos_class": QoSClass.MMTC,
        "size_bytes": 128,
        "rate": 0.60,
        "description": "IoT sensor data",
    },
    "status_update": {
        "qos_class": QoSClass.BEST_EFFORT,
        "size_bytes": 512,
        "rate": 0.35,
        "description": "Vehicle status / logs",
    },
    "dispatch_command": {
        "qos_class": QoSClass.URLLC,
        "size_bytes": 384,
        "rate": 0.08,
        "description": "Dispatch instruction to vehicle",
    },
}


# ─────────────────────────────────────────────
# Node Definitions
# ─────────────────────────────────────────────

class NodeType(enum.Enum):
    AMBULANCE = "ambulance"
    FIRE_TRUCK = "fire_truck"
    POLICE_CAR = "police_car"
    HOSPITAL = "hospital"
    DISPATCH = "dispatch"
    TRAFFIC_CAM = "traffic_camera"
    ENV_SENSOR = "env_sensor"


NODE_DEFINITIONS = [
    # Emergency vehicles (mobile)
    {"id": "AMB_01", "type": NodeType.AMBULANCE, "x": 120, "y": 200, "mobile": True},
    {"id": "AMB_02", "type": NodeType.AMBULANCE, "x": 350, "y": 400, "mobile": True},
    {"id": "AMB_03", "type": NodeType.AMBULANCE, "x": 480, "y": 150, "mobile": True},
    {"id": "FIRE_01", "type": NodeType.FIRE_TRUCK, "x": 180, "y": 350, "mobile": True},
    {"id": "FIRE_02", "type": NodeType.FIRE_TRUCK, "x": 420, "y": 280, "mobile": True},
    {"id": "POL_01", "type": NodeType.POLICE_CAR, "x": 80, "y": 80, "mobile": True},
    {"id": "POL_02", "type": NodeType.POLICE_CAR, "x": 300, "y": 480, "mobile": True},
    {"id": "POL_03", "type": NodeType.POLICE_CAR, "x": 500, "y": 380, "mobile": True},
    # Fixed infrastructure (strategically placed for coverage)
    {"id": "HOSP_01", "type": NodeType.HOSPITAL, "x": 150, "y": 300, "mobile": False},
    {"id": "HOSP_02", "type": NodeType.HOSPITAL, "x": 450, "y": 250, "mobile": False},
    {"id": "DISP_01", "type": NodeType.DISPATCH, "x": 300, "y": 300, "mobile": False},
    {"id": "DISP_02", "type": NodeType.DISPATCH, "x": 250, "y": 150, "mobile": False},
    # IoT sensors (distributed across grid)
    {"id": "CAM_01", "type": NodeType.TRAFFIC_CAM, "x": 80, "y": 400, "mobile": False},
    {"id": "CAM_02", "type": NodeType.TRAFFIC_CAM, "x": 250, "y": 80, "mobile": False},
    {"id": "CAM_03", "type": NodeType.TRAFFIC_CAM, "x": 400, "y": 180, "mobile": False},
    {"id": "CAM_04", "type": NodeType.TRAFFIC_CAM, "x": 480, "y": 480, "mobile": False},
    {"id": "ENV_01", "type": NodeType.ENV_SENSOR, "x": 50, "y": 250, "mobile": False},
    {"id": "ENV_02", "type": NodeType.ENV_SENSOR, "x": 350, "y": 350, "mobile": False},
    {"id": "ENV_03", "type": NodeType.ENV_SENSOR, "x": 420, "y": 80, "mobile": False},
    {"id": "ENV_04", "type": NodeType.ENV_SENSOR, "x": 520, "y": 300, "mobile": False},
]


# ─────────────────────────────────────────────
# Node Category Helpers
# ─────────────────────────────────────────────

EMERGENCY_VEHICLES = {NodeType.AMBULANCE, NodeType.FIRE_TRUCK, NodeType.POLICE_CAR}
BASE_STATIONS = {NodeType.HOSPITAL, NodeType.DISPATCH}
IOT_DEVICES = {NodeType.TRAFFIC_CAM, NodeType.ENV_SENSOR}


# ─────────────────────────────────────────────
# Physical Layer Parameters
# ─────────────────────────────────────────────

PHYSICAL = {
    "carrier_frequency_ghz": 3.5,       # 5G mid-band
    "bandwidth_mhz": 100,               # Channel bandwidth
    "tx_power_dbm": 26,                 # Max transmit power
    "noise_figure_db": 5,               # Receiver noise figure
    "path_loss_exponent": 2.8,          # Urban environment (tuned)
    "reference_distance_m": 1.0,        # Reference distance for path loss
    "reference_loss_db": 35.0,          # Path loss at reference distance
    "shadow_std_db": 4.0,               # Log-normal shadowing std dev (tuned)
    "rayleigh_scale": 1.0,              # Rayleigh fading scale
    "thermal_noise_dbm_hz": -174,       # Thermal noise density
}

# Modulation schemes with SNR thresholds and spectral efficiency
MODULATION_SCHEMES = {
    "BPSK":   {"snr_threshold_db": 3,  "bits_per_symbol": 1, "spectral_eff": 1.0},
    "QPSK":   {"snr_threshold_db": 6,  "bits_per_symbol": 2, "spectral_eff": 2.0},
    "16-QAM": {"snr_threshold_db": 12, "bits_per_symbol": 4, "spectral_eff": 4.0},
    "64-QAM": {"snr_threshold_db": 18, "bits_per_symbol": 6, "spectral_eff": 6.0},
}


# ─────────────────────────────────────────────
# Data Link Layer Parameters
# ─────────────────────────────────────────────

DATALINK = {
    "frame_header_bytes": 22,      # src_mac(6) + dst_mac(6) + type(2) + seq(4) + len(4)
    "crc_bytes": 4,                # CRC-32 trailer
    "max_frame_payload": 1500,     # MTU
    "arq_window_size": 8,          # Selective Repeat window
    "arq_max_retries": 3,          # Max retransmission attempts
    "arq_timeout_ms": 50,          # Retransmission timeout
    "tdma_slot_duration_ms": 1.0,  # TDMA time slot
    "priority_slots_ratio": 0.4,   # Fraction of slots reserved for priority traffic
}


# ─────────────────────────────────────────────
# Network Layer Parameters
# ─────────────────────────────────────────────

NETWORK = {
    "communication_range_m": 450,   # Max link distance (5G range)
    "default_ttl": 16,              # Time To Live
    "max_packet_size": 65535,       # Max IP packet size
    "congestion_threshold": 0.75,   # Link utilization threshold for rerouting
    "routing_update_interval": 5,   # Seconds between routing table updates
    "qos_weight_delay": 0.5,       # Weight for delay in QoS routing
    "qos_weight_reliability": 0.3, # Weight for reliability
    "qos_weight_bandwidth": 0.2,   # Weight for bandwidth
}


# ─────────────────────────────────────────────
# Transport Layer Parameters
# ─────────────────────────────────────────────

TRANSPORT = {
    "tcp_initial_cwnd": 4,          # Initial congestion window (segments)
    "tcp_max_cwnd": 64,             # Maximum congestion window
    "tcp_ssthresh": 32,             # Slow-start threshold
    "tcp_rto_ms": 200,              # Retransmission timeout
    "tcp_max_retries": 5,           # Max TCP retries
    "udp_header_bytes": 8,          # UDP header size
    "tcp_header_bytes": 20,         # TCP header size
    "segment_size": 1460,           # MSS (Maximum Segment Size)
    "ack_size_bytes": 64,           # ACK packet size
    "jitter_std_ms": 2.0,           # Jitter standard deviation
}


# ─────────────────────────────────────────────
# Session Layer Parameters
# ─────────────────────────────────────────────

SESSION = {
    "setup_delay_ms": 5.0,          # Session establishment time
    "fast_setup_delay_ms": 1.0,     # Fast setup for URLLC
    "heartbeat_interval_s": 10,     # Keepalive interval
    "session_timeout_s": 60,        # Inactive session timeout
    "max_sessions_per_node": 50,    # Max concurrent sessions
}


# ─────────────────────────────────────────────
# Presentation Layer Parameters
# ─────────────────────────────────────────────

PRESENTATION = {
    "encryption_overhead_bytes": 32,     # AES-256 overhead
    "encryption_delay_ms": 0.5,          # Encryption processing time
    "light_encryption_delay_ms": 0.1,    # Lightweight encryption for URLLC
    "compression_ratio_video": 0.30,     # 70% compression for video
    "compression_ratio_telemetry": 0.50, # 50% compression for sensor data
    "compression_ratio_text": 0.60,      # 40% compression for text
    "compression_delay_ms": 0.3,         # Compression processing time
    "encoding_overhead_bytes": 8,        # Serialization header
}


# ─────────────────────────────────────────────
# Simulation Parameters
# ─────────────────────────────────────────────

SIMULATION = {
    "duration_s": 60,              # Total simulation time
    "time_step_s": 1.0,            # Simulation granularity
    "random_seed": 42,             # Reproducibility
    "area_width": 550,             # Simulation area width (meters)
    "area_height": 520,            # Simulation area height (meters)
    "vehicle_speed_range": (3, 10),  # m/s (11-36 km/h, urban)
    "results_dir": "results",      # Output directory
}


# ─────────────────────────────────────────────
# Packet Dataclass
# ─────────────────────────────────────────────

@dataclass
class Packet:
    """Represents a packet flowing through all OSI layers."""
    packet_id: int
    qos_class: QoSClass
    message_type: str
    source_id: str
    destination_id: str
    payload_size: int
    created_at: float
    priority: int
    deadline_ms: float

    # Mutable state
    current_size: int = 0
    delivered: bool = False
    dropped: bool = False
    drop_reason: str = ""
    drop_layer: str = ""
    delivery_time: float = 0.0
    total_delay_ms: float = 0.0
    path: List[str] = field(default_factory=list)
    hops: int = 0
    retransmissions: int = 0

    # Per-layer metrics
    layer_metrics: Dict[str, dict] = field(default_factory=dict)

    def __post_init__(self):
        self.current_size = self.payload_size

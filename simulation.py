"""
simulation.py — Simulation Engine
Orchestrates the full 7-layer OSI simulation across all nodes.
"""

import random
import math
import copy
from typing import List, Dict, Tuple
from pathlib import Path

import numpy as np

from config import (
    Packet, QoSClass, NODE_DEFINITIONS, SIMULATION,
    EMERGENCY_VEHICLES, QOS_REQUIREMENTS,
)
from layer1_physical import PhysicalLayer
from layer2_datalink import DataLinkLayer
from layer3_network import NetworkLayer
from layer4_transport import TransportLayer
from layer5_session import SessionLayer
from layer6_presentation import PresentationLayer
from layer7_application import ApplicationLayer


class SimulationEngine:
    """
    Main simulation engine that:
    1. Creates the network with all nodes
    2. Steps through time
    3. Moves mobile nodes
    4. Generates traffic at the application layer
    5. Processes each packet through all 7 OSI layers
    6. Collects per-layer and per-packet metrics
    """

    def __init__(self, config: dict = None):
        self.config = config or SIMULATION
        self.nodes = []
        self.current_time = 0.0

        # Initialize all 7 layers
        self.layer7 = ApplicationLayer()
        self.layer6 = PresentationLayer()
        self.layer5 = SessionLayer()
        self.layer4 = TransportLayer()
        self.layer3 = NetworkLayer()
        self.layer2 = DataLinkLayer()
        self.layer1 = PhysicalLayer()

        # Global metrics
        self.all_packets: List[Packet] = []
        self.timeline_metrics: List[dict] = []
        self.per_layer_timeline: Dict[str, list] = {
            f"layer{i}": [] for i in range(1, 8)
        }

    # ─── Node Management ─────────────────────────

    def initialize_nodes(self):
        """Create all nodes from configuration."""
        self.nodes = []
        for node_def in NODE_DEFINITIONS:
            node = copy.deepcopy(node_def)
            # Assign speed for mobile nodes
            if node["mobile"]:
                speed_min, speed_max = self.config["vehicle_speed_range"]
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(speed_min, speed_max)
                node["speed_x"] = speed * math.cos(angle)
                node["speed_y"] = speed * math.sin(angle)
            else:
                node["speed_x"] = 0.0
                node["speed_y"] = 0.0

            # Assign MAC and IP addresses
            self.layer2.assign_mac(node["id"])
            self.layer3.assign_ip(node["id"])
            self.nodes.append(node)

    def move_nodes(self, dt: float):
        """Move mobile nodes with bounce-off-boundary physics."""
        w = self.config["area_width"]
        h = self.config["area_height"]

        for node in self.nodes:
            if not node["mobile"]:
                continue
            node["x"] += node["speed_x"] * dt
            node["y"] += node["speed_y"] * dt

            # Bounce off boundaries
            if node["x"] < 0 or node["x"] > w:
                node["speed_x"] *= -1
                node["x"] = max(0, min(node["x"], w))
            if node["y"] < 0 or node["y"] > h:
                node["speed_y"] *= -1
                node["y"] = max(0, min(node["y"], h))

    # ─── Packet Processing Through All Layers ────

    def process_packet(self, packet: Packet) -> Packet:
        """
        Process a single packet through all 7 OSI layers (top-down).
        Each layer adds its processing delay and overhead.
        """
        total_delay = 0.0

        # ── Layer 7: Application ──
        l7_metrics = self.layer7.process_outgoing(packet)
        total_delay += l7_metrics.get("app_delay_ms", 0)
        packet.layer_metrics["layer7"] = l7_metrics

        # ── Layer 6: Presentation ──
        l6_metrics = self.layer6.process_outgoing(packet)
        total_delay += l6_metrics.get("total_delay_ms", 0)
        packet.layer_metrics["layer6"] = l6_metrics

        # ── Layer 5: Session ──
        l5_metrics = self.layer5.process_outgoing(packet, self.current_time)
        total_delay += l5_metrics.get("total_delay_ms", 0)
        packet.layer_metrics["layer5"] = l5_metrics

        if l5_metrics.get("session_action") == "rejected":
            packet.dropped = True
            packet.drop_reason = "session_limit_exceeded"
            packet.drop_layer = "layer5"
            packet.total_delay_ms = total_delay
            return packet

        # ── Layer 3: Network (routing first to determine path) ──
        l3_metrics = self.layer3.process_outgoing(packet)
        total_delay += l3_metrics.get("routing_delay_ms", 0)
        packet.layer_metrics["layer3"] = l3_metrics

        if not l3_metrics.get("routed", False):
            packet.dropped = True
            packet.drop_reason = "no_route"
            packet.drop_layer = "layer3"
            packet.total_delay_ms = total_delay
            return packet

        path = l3_metrics.get("path", [])
        packet.path = path
        packet.hops = l3_metrics.get("hops", 0)

        # ── Layer 4: Transport ──
        # Determine if there's physical corruption (calculated ahead for transport)
        # Simulate per-hop physical layer first to get corruption status
        any_corrupted = False
        physical_delays = 0.0
        l1_hop_metrics = []

        for i in range(len(path) - 1):
            src_node = next((n for n in self.nodes if n["id"] == path[i]), None)
            dst_node = next((n for n in self.nodes if n["id"] == path[i + 1]), None)
            if src_node and dst_node:
                distance = math.dist(
                    (src_node["x"], src_node["y"]),
                    (dst_node["x"], dst_node["y"]),
                )
            else:
                distance = 100  # Default

            hop_metrics = self.layer1.process_link(packet, distance)
            l1_hop_metrics.append(hop_metrics)
            physical_delays += hop_metrics.get("total_delay_ms", 0)
            if hop_metrics.get("corrupted", False):
                any_corrupted = True

        l4_metrics = self.layer4.process_outgoing(packet, any_corrupted)
        total_delay += l4_metrics.get("total_delay_ms", 0)
        packet.layer_metrics["layer4"] = l4_metrics

        # ── Layer 2: Data Link ──
        link_util = l3_metrics.get("max_link_utilization", 0.3)
        l2_metrics = self.layer2.process_outgoing(packet, any_corrupted, link_util)
        total_delay += l2_metrics.get("total_delay_ms", 0)
        packet.layer_metrics["layer2"] = l2_metrics

        if not l2_metrics.get("arq_success", True):
            packet.dropped = True
            packet.drop_reason = "arq_failure"
            packet.drop_layer = "layer2"
            packet.retransmissions = l2_metrics.get("retransmissions", 0)
            packet.total_delay_ms = total_delay
            return packet

        packet.retransmissions = l2_metrics.get("retransmissions", 0)

        # ── Layer 1: Physical (aggregate) ──
        total_delay += physical_delays
        packet.layer_metrics["layer1"] = {
            "hop_count": len(l1_hop_metrics),
            "total_physical_delay_ms": round(physical_delays, 4),
            "any_corruption": any_corrupted,
            "per_hop": l1_hop_metrics,
            "avg_snr_db": round(
                np.mean([h["snr_db"] for h in l1_hop_metrics]), 2
            ) if l1_hop_metrics else 0,
            "modulations_used": [h["modulation"] for h in l1_hop_metrics],
        }

        # ── Final delivery ──
        packet.delivered = True
        packet.total_delay_ms = total_delay
        packet.delivery_time = self.current_time + total_delay / 1000

        return packet

    # ─── Main Simulation Loop ────────────────────

    def run(self, progress_callback=None) -> Dict:
        """
        Run the complete simulation.
        Returns a dict with all metrics.
        """
        random.seed(self.config["random_seed"])
        np.random.seed(self.config["random_seed"])

        duration = self.config["duration_s"]
        dt = self.config["time_step_s"]
        steps = int(duration / dt)

        # Initialize
        self.initialize_nodes()
        self.layer3.build_topology(self.nodes)

        print(f"+--------------------------------------------------+")
        print(f"|  5G Emergency Response Network Simulation        |")
        print(f"|  Nodes: {len(self.nodes):2d}  |  Duration: {duration}s  |  dt: {dt}s   |")
        print(f"+--------------------------------------------------+")
        print()

        for step in range(steps):
            self.current_time = step * dt

            # Move mobile nodes
            self.move_nodes(dt)

            # Update network topology
            self.layer3.update_topology(self.nodes)
            self.layer3.decay_utilization(0.92)

            # Check session heartbeats
            self.layer5.check_heartbeats(self.current_time)

            # Calculate network load
            total_util = sum(self.layer3.link_utilization.values())
            n_links = max(1, len(self.layer3.link_utilization))
            network_load = total_util / n_links

            # Generate messages
            packets = self.layer7.generate_messages(
                self.nodes, self.current_time, network_load
            )

            # Process each packet through all layers
            step_delivered = 0
            step_dropped = 0
            step_delays = []

            for packet in packets:
                processed = self.process_packet(packet)
                self.all_packets.append(processed)

                # Verify delivery at application layer
                self.layer7.verify_delivery(processed)

                if processed.delivered:
                    step_delivered += 1
                    step_delays.append(processed.total_delay_ms)
                else:
                    step_dropped += 1

            # Timeline metrics
            self.timeline_metrics.append({
                "time": self.current_time,
                "packets_generated": len(packets),
                "delivered": step_delivered,
                "dropped": step_dropped,
                "avg_delay_ms": round(np.mean(step_delays), 3) if step_delays else 0,
                "network_load": round(network_load, 3),
                "active_sessions": len([
                    s for s in self.layer5.sessions.values()
                    if s.state.value in ("ESTABLISHED", "DATA_TRANSFER")
                ]),
            })

            # Progress
            if progress_callback:
                progress_callback(step + 1, steps)
            elif (step + 1) % max(1, steps // 10) == 0:
                pct = int((step + 1) / steps * 100)
                bar = "#" * (pct // 5) + "-" * (20 - pct // 5)
                print(f"\r  [{bar}] {pct:3d}%  t={self.current_time:.0f}s  "
                      f"pkts={len(self.all_packets)}  "
                      f"delivered={step_delivered}  dropped={step_dropped}", end="")

        print(f"\n\n  [OK] Simulation complete -- {len(self.all_packets)} total packets processed\n")

        return self.compile_results()

    # ─── Results Compilation ─────────────────────

    def compile_results(self) -> Dict:
        """Compile all results from all layers."""
        results = {
            "simulation": {
                "duration_s": self.config["duration_s"],
                "total_packets": len(self.all_packets),
                "delivered": sum(1 for p in self.all_packets if p.delivered),
                "dropped": sum(1 for p in self.all_packets if p.dropped),
            },
            "timeline": self.timeline_metrics,
            "packets": self.all_packets,
            "nodes": self.nodes,
            "layer_metrics": {
                "layer1_physical": self.layer1.get_aggregate_metrics(),
                "layer2_datalink": self.layer2.get_aggregate_metrics(),
                "layer3_network": self.layer3.get_aggregate_metrics(),
                "layer4_transport": self.layer4.get_aggregate_metrics(),
                "layer5_session": self.layer5.get_aggregate_metrics(),
                "layer6_presentation": self.layer6.get_aggregate_metrics(),
                "layer7_application": self.layer7.get_aggregate_metrics(),
            },
            "qos_compliance": self._calculate_qos_compliance(),
            "network_graph": self.layer3.graph.copy() if self.layer3.graph else None,
        }

        # Print summary
        self._print_summary(results)
        return results

    def _calculate_qos_compliance(self) -> Dict:
        """Calculate QoS compliance per traffic class."""
        compliance = {}
        for qos_class in QoSClass:
            qos_packets = [p for p in self.all_packets if p.qos_class == qos_class]
            if not qos_packets:
                continue

            req = QOS_REQUIREMENTS[qos_class]
            delivered = [p for p in qos_packets if p.delivered]
            on_time = [p for p in delivered if p.total_delay_ms <= req["max_delay_ms"]]

            delivery_rate = len(delivered) / len(qos_packets) if qos_packets else 0
            delays = [p.total_delay_ms for p in delivered]

            compliance[qos_class.value] = {
                "total_packets": len(qos_packets),
                "delivered": len(delivered),
                "delivery_rate": round(delivery_rate, 4),
                "on_time": len(on_time),
                "on_time_rate": round(len(on_time) / len(qos_packets), 4) if qos_packets else 0,
                "avg_delay_ms": round(np.mean(delays), 3) if delays else 0,
                "max_delay_ms": round(max(delays), 3) if delays else 0,
                "min_delay_ms": round(min(delays), 3) if delays else 0,
                "required_max_delay_ms": req["max_delay_ms"],
                "required_reliability": req["min_reliability"],
                "delay_met": (np.mean(delays) if delays else 0) <= req["max_delay_ms"],
                "reliability_met": delivery_rate >= req["min_reliability"],
                "fully_compliant": (
                    delivery_rate >= req["min_reliability"]
                    and (np.mean(delays) if delays else 0) <= req["max_delay_ms"]
                ),
            }

        return compliance

    def _print_summary(self, results: Dict):
        """Print a formatted summary of simulation results."""
        sim = results["simulation"]
        print("+--------------------------------------------------+")
        print("|          SIMULATION RESULTS SUMMARY               |")
        print("+--------------------------------------------------+")
        print(f"  Total Packets:  {sim['total_packets']:>6d}")
        print(f"  Delivered:      {sim['delivered']:>6d}  "
              f"({sim['delivered']/max(sim['total_packets'],1)*100:5.1f}%)")
        print(f"  Dropped:        {sim['dropped']:>6d}  "
              f"({sim['dropped']/max(sim['total_packets'],1)*100:5.1f}%)")
        print("+--------------------------------------------------+")
        print("  QoS Compliance:")

        for qos_name, comp in results["qos_compliance"].items():
            status = "PASS" if comp["fully_compliant"] else "FAIL"
            print(f"    {qos_name:>12s}: [{status}]  "
                  f"(delay={comp['avg_delay_ms']:7.2f}ms, "
                  f"rel={comp['delivery_rate']*100:5.1f}%)")

        print("+--------------------------------------------------+")

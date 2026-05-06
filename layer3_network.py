"""
layer3_network.py — Network Layer (OSI Layer 3)
Handles routing, IP addressing, congestion control, traffic engineering.
"""

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

import networkx as nx

from config import NETWORK, Packet, QoSClass, QOS_REQUIREMENTS


@dataclass
class IPAddress:
    """IPv4-style address."""
    subnet: str
    host: int
    full: str = ""

    def __post_init__(self):
        self.full = f"{self.subnet}.{self.host}"


class NetworkLayer:
    """
    OSI Layer 3 — Network Layer
    Features:
    - IPv4-style addressing with subnet management
    - Dijkstra shortest path routing (baseline)
    - QoS-aware routing (weighted: delay + reliability + bandwidth)
    - Congestion detection and adaptive rerouting
    - TTL management
    - Load balancing across multiple paths
    """

    def __init__(self, params: dict = None):
        self.params = params or NETWORK
        self.graph = nx.Graph()
        self.ip_table: Dict[str, str] = {}
        self.link_utilization: Dict[tuple, float] = {}
        self.routing_table: Dict[str, Dict[str, list]] = {}
        self.metrics_log = []
        self._next_host = 1

    # ─── IP Address Management ───────────────────

    def assign_ip(self, node_id: str, subnet: str = "10.5.0") -> str:
        """Assign an IP address to a node."""
        if node_id not in self.ip_table:
            ip = f"{subnet}.{self._next_host}"
            self.ip_table[node_id] = ip
            self._next_host += 1
        return self.ip_table[node_id]

    def get_ip(self, node_id: str) -> str:
        return self.ip_table.get(node_id, self.assign_ip(node_id))

    # ─── Topology Management ────────────────────

    def build_topology(self, nodes: list) -> nx.Graph:
        """Build network graph from node list with distance-based links."""
        self.graph.clear()
        comm_range = self.params["communication_range_m"]

        for node in nodes:
            self.graph.add_node(
                node["id"],
                pos=(node["x"], node["y"]),
                node_type=node["type"].value if hasattr(node["type"], "value") else str(node["type"]),
                ip=self.assign_ip(node["id"]),
            )

        for i, n1 in enumerate(nodes):
            for n2 in nodes[i + 1:]:
                dist = math.dist((n1["x"], n1["y"]), (n2["x"], n2["y"]))
                if dist <= comm_range:
                    link = (n1["id"], n2["id"])
                    utilization = self.link_utilization.get(link, 0.0)
                    self.graph.add_edge(
                        n1["id"], n2["id"],
                        distance=round(dist, 2),
                        delay_weight=1 + dist / 100 + utilization * 5,
                        reliability=max(0.5, 1 - dist / (comm_range * 1.5)),
                        bandwidth_available=max(0.1, 1 - utilization),
                        utilization=utilization,
                    )

        return self.graph

    def update_topology(self, nodes: list) -> nx.Graph:
        """Update topology with new node positions."""
        return self.build_topology(nodes)

    # ─── Routing ─────────────────────────────────

    def route_shortest(self, source: str, destination: str) -> Optional[List[str]]:
        """Baseline: Dijkstra shortest path (hop count)."""
        if source not in self.graph or destination not in self.graph:
            return None
        try:
            return nx.shortest_path(self.graph, source, destination)
        except nx.NetworkXNoPath:
            return None

    def route_qos_aware(self, source: str, destination: str, qos_class: QoSClass) -> Optional[List[str]]:
        """QoS-aware routing using weighted cost function."""
        if source not in self.graph or destination not in self.graph:
            return None

        w_delay = self.params["qos_weight_delay"]
        w_rel = self.params["qos_weight_reliability"]
        w_bw = self.params["qos_weight_bandwidth"]

        # Adjust weights based on QoS class
        if qos_class == QoSClass.URLLC:
            w_delay, w_rel, w_bw = 0.6, 0.3, 0.1  # Prioritize low delay
        elif qos_class == QoSClass.EMBB:
            w_delay, w_rel, w_bw = 0.2, 0.2, 0.6  # Prioritize bandwidth
        elif qos_class == QoSClass.MMTC:
            w_delay, w_rel, w_bw = 0.3, 0.5, 0.2  # Prioritize reliability

        # Calculate QoS cost for each edge
        for u, v, data in self.graph.edges(data=True):
            delay_cost = data.get("delay_weight", 1)
            rel_cost = 1 - data.get("reliability", 0.9)
            bw_cost = 1 - data.get("bandwidth_available", 0.5)
            data["qos_cost"] = w_delay * delay_cost + w_rel * rel_cost * 10 + w_bw * bw_cost * 5

        try:
            return nx.shortest_path(self.graph, source, destination, weight="qos_cost")
        except nx.NetworkXNoPath:
            return None

    def route_congestion_aware(self, source: str, destination: str, qos_class: QoSClass) -> Optional[List[str]]:
        """Congestion-aware routing: avoid congested links."""
        threshold = self.params["congestion_threshold"]

        # First try QoS-aware path
        path = self.route_qos_aware(source, destination, qos_class)
        if path is None:
            return None

        # Check if path has congested links
        congested = False
        for u, v in zip(path, path[1:]):
            util = self.graph[u][v].get("utilization", 0)
            if util > threshold:
                congested = True
                break

        if congested:
            # Try alternative paths
            try:
                paths = list(nx.all_simple_paths(self.graph, source, destination, cutoff=6))
                best_path = path
                best_cost = float("inf")
                for alt_path in paths[:10]:  # Limit search
                    max_util = max(
                        self.graph[u][v].get("utilization", 0)
                        for u, v in zip(alt_path, alt_path[1:])
                    )
                    cost = len(alt_path) + max_util * 10
                    if cost < best_cost:
                        best_cost = cost
                        best_path = alt_path
                return best_path
            except Exception:
                return path

        return path

    def get_route(self, source: str, destination: str, qos_class: QoSClass) -> Optional[List[str]]:
        """Main routing entry point — selects best routing strategy."""
        path = self.route_congestion_aware(source, destination, qos_class)
        if path:
            return path
        path = self.route_qos_aware(source, destination, qos_class)
        if path:
            return path
        return self.route_shortest(source, destination)

    # ─── Congestion & Load ───────────────────────

    def update_link_utilization(self, path: List[str], packet_size: int):
        """Update link utilization after sending a packet."""
        for u, v in zip(path, path[1:]):
            link = tuple(sorted((u, v)))
            current = self.link_utilization.get(link, 0.0)
            # Increase utilization proportionally
            increase = min(0.05, packet_size / 50000)
            self.link_utilization[link] = min(1.0, current + increase)

    def decay_utilization(self, factor: float = 0.95):
        """Decay link utilization over time (traffic clears)."""
        for link in self.link_utilization:
            self.link_utilization[link] *= factor

    def get_path_metrics(self, path: List[str]) -> dict:
        """Calculate aggregate metrics for a path."""
        if not path or len(path) < 2:
            return {"hops": 0, "total_distance_m": 0, "avg_reliability": 1.0, "max_utilization": 0, "path_reliability": 1.0}

        total_dist = 0
        reliabilities = []
        max_util = 0

        for u, v in zip(path, path[1:]):
            if self.graph.has_edge(u, v):
                edge = self.graph[u][v]
                total_dist += edge.get("distance", 0)
                reliabilities.append(edge.get("reliability", 0.9))
                max_util = max(max_util, edge.get("utilization", 0))

        return {
            "hops": len(path) - 1,
            "total_distance_m": round(total_dist, 2),
            "avg_reliability": round(sum(reliabilities) / len(reliabilities), 4) if reliabilities else 0,
            "max_utilization": round(max_util, 3),
            "path_reliability": round(
                math.prod(reliabilities), 4
            ) if reliabilities else 0,
        }

    # ─── TTL Management ──────────────────────────

    def check_ttl(self, packet: Packet, hops: int) -> bool:
        """Check if packet has exceeded TTL."""
        return hops < self.params["default_ttl"]

    # ─── Full Layer Processing ───────────────────

    def process_outgoing(self, packet: Packet) -> dict:
        """Process a packet through the network layer."""
        src_ip = self.get_ip(packet.source_id)
        dst_ip = self.get_ip(packet.destination_id)

        # Route the packet
        path = self.get_route(packet.source_id, packet.destination_id, packet.qos_class)

        if path is None:
            metrics = {
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "routed": False,
                "drop_reason": "no_route",
                "path": [],
                "hops": 0,
                "routing_delay_ms": 0,
            }
            self.metrics_log.append(metrics)
            return metrics

        path_info = self.get_path_metrics(path)

        # Routing decision delay
        routing_delay = 0.2 * path_info["hops"]
        if packet.qos_class == QoSClass.URLLC:
            routing_delay *= 0.3  # Fast-path for emergency

        # Update link utilization
        self.update_link_utilization(path, packet.current_size)

        # IP header overhead (20 bytes)
        packet.current_size += 20
        packet.path = path
        packet.hops = path_info["hops"]

        # TTL check
        ttl_ok = self.check_ttl(packet, path_info["hops"])

        metrics = {
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "routed": True,
            "path": path,
            "hops": path_info["hops"],
            "total_distance_m": path_info["total_distance_m"],
            "path_reliability": path_info["path_reliability"],
            "max_link_utilization": path_info["max_utilization"],
            "routing_delay_ms": round(routing_delay, 3),
            "ttl_ok": ttl_ok,
            "ip_overhead_bytes": 20,
        }

        self.metrics_log.append(metrics)
        return metrics

    def get_aggregate_metrics(self) -> dict:
        """Aggregate all network layer metrics."""
        if not self.metrics_log:
            return {}

        routed = [m for m in self.metrics_log if m.get("routed")]
        unrouted = len(self.metrics_log) - len(routed)

        if not routed:
            return {"total_packets": len(self.metrics_log), "routing_failure_rate": 1.0}

        hops = [m["hops"] for m in routed]
        distances = [m["total_distance_m"] for m in routed]
        reliabilities = [m["path_reliability"] for m in routed]
        delays = [m["routing_delay_ms"] for m in routed]
        utilizations = [m["max_link_utilization"] for m in routed]

        return {
            "total_packets": len(self.metrics_log),
            "routed_packets": len(routed),
            "routing_failure_rate": round(unrouted / len(self.metrics_log), 4),
            "avg_hops": round(sum(hops) / len(hops), 2),
            "avg_distance_m": round(sum(distances) / len(distances), 2),
            "avg_path_reliability": round(sum(reliabilities) / len(reliabilities), 4),
            "avg_routing_delay_ms": round(sum(delays) / len(delays), 3),
            "avg_link_utilization": round(sum(utilizations) / len(utilizations), 3),
            "congested_links": sum(1 for u in utilizations if u > self.params["congestion_threshold"]),
            "hop_distribution": hops,
            "delay_values": delays,
            "utilization_values": utilizations,
        }

    def reset(self):
        self.metrics_log.clear()
        self.link_utilization.clear()

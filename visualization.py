"""
visualization.py — Matplotlib Plots for all 7 OSI layers
Generates comprehensive static plots saved to results/ directory.
"""

import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from pathlib import Path
from config import QoSClass, QOS_REQUIREMENTS


COLORS = {
    "URLLC": "#e74c3c", "eMBB": "#3498db",
    "mMTC": "#2ecc71", "BestEffort": "#95a5a6",
    "primary": "#2f80ed", "success": "#27ae60",
    "warning": "#f39c12", "danger": "#e74c3c",
    "dark": "#2c3e50", "light": "#ecf0f1",
}

def _save(fig, path):
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
    plt.close(fig)

def _style_ax(ax, title="", xlabel="", ylabel=""):
    ax.set_facecolor("#16213e")
    ax.set_title(title, color="white", fontsize=11, fontweight="bold", pad=8)
    ax.set_xlabel(xlabel, color="#b0b0b0", fontsize=9)
    ax.set_ylabel(ylabel, color="#b0b0b0", fontsize=9)
    ax.tick_params(colors="#b0b0b0", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#333355")


def plot_all(results: dict, output_dir: str = "results"):
    """Generate all plots and save to output directory."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    lm = results["layer_metrics"]
    tl = results["timeline"]
    qos = results["qos_compliance"]

    plot_overview(results, output_dir)
    plot_qos_compliance(qos, output_dir)
    plot_layer1(lm.get("layer1_physical", {}), output_dir)
    plot_layer2(lm.get("layer2_datalink", {}), output_dir)
    plot_layer3(lm.get("layer3_network", {}), output_dir)
    plot_layer4(lm.get("layer4_transport", {}), output_dir)
    plot_layer5(lm.get("layer5_session", {}), output_dir)
    plot_layer6(lm.get("layer6_presentation", {}), output_dir)
    plot_layer7(lm.get("layer7_application", {}), output_dir)
    plot_timeline(tl, output_dir)
    plot_network_topology(results, output_dir)
    plot_packet_journey(results, output_dir)
    print(f"  [OK] All plots saved to {output_dir}/")


def plot_overview(results, out):
    sim = results["simulation"]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), facecolor="#1a1a2e")
    # Delivery pie
    ax = axes[0]
    ax.set_facecolor("#1a1a2e")
    vals = [sim["delivered"], sim["dropped"]]
    ax.pie(vals, labels=["Delivered", "Dropped"], colors=[COLORS["success"], COLORS["danger"]],
           autopct="%1.1f%%", textprops={"color": "white", "fontsize": 9}, startangle=90)
    ax.set_title("Packet Delivery", color="white", fontsize=11, fontweight="bold")
    # QoS bar
    ax = axes[1]
    _style_ax(ax, "QoS Compliance Rate", "", "Rate (%)")
    qos = results["qos_compliance"]
    names = list(qos.keys())
    rates = [qos[n]["on_time_rate"] * 100 for n in names]
    colors = [COLORS.get(n, COLORS["primary"]) for n in names]
    ax.bar(names, rates, color=colors, alpha=0.85)
    ax.axhline(y=100, color="#555", linestyle="--", alpha=0.5)
    ax.set_ylim(0, 110)
    # Delay box
    ax = axes[2]
    _style_ax(ax, "Delay by QoS Class", "", "Delay (ms)")
    delay_data, labels_d = [], []
    for p_list_name in qos:
        pkts = [p for p in results["packets"] if p.qos_class.value == p_list_name and p.delivered]
        if pkts:
            delay_data.append([p.total_delay_ms for p in pkts])
            labels_d.append(p_list_name)
    if delay_data:
        bp = ax.boxplot(delay_data, labels=labels_d, patch_artist=True)
        for patch, c in zip(bp["boxes"], [COLORS.get(l, "#777") for l in labels_d]):
            patch.set_facecolor(c)
            patch.set_alpha(0.6)
        for element in ["whiskers", "caps", "medians"]:
            plt.setp(bp[element], color="white")
        plt.setp(bp["fliers"], markeredgecolor="#999", markersize=3)
    fig.suptitle("5G Emergency Response Network — Overview", color="white", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    _save(fig, f"{out}/00_overview.png")


def plot_qos_compliance(qos, out):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), facecolor="#1a1a2e")
    names = list(qos.keys())
    # Delay vs requirement
    ax = axes[0]
    _style_ax(ax, "Avg Delay vs Requirement", "QoS Class", "Delay (ms)")
    avg_d = [qos[n]["avg_delay_ms"] for n in names]
    req_d = [qos[n]["required_max_delay_ms"] for n in names]
    x = np.arange(len(names))
    ax.bar(x - 0.15, avg_d, 0.3, label="Actual", color=COLORS["primary"], alpha=0.85)
    ax.bar(x + 0.15, req_d, 0.3, label="Required Max", color=COLORS["warning"], alpha=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=8)
    ax.legend(fontsize=8, facecolor="#16213e", edgecolor="#333", labelcolor="white")
    # Reliability
    ax = axes[1]
    _style_ax(ax, "Reliability vs Requirement", "QoS Class", "Rate")
    actual_r = [qos[n]["delivery_rate"] for n in names]
    req_r = [qos[n]["required_reliability"] for n in names]
    ax.bar(x - 0.15, actual_r, 0.3, label="Actual", color=COLORS["success"], alpha=0.85)
    ax.bar(x + 0.15, req_r, 0.3, label="Required Min", color=COLORS["warning"], alpha=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=8)
    ax.set_ylim(0, 1.15)
    ax.legend(fontsize=8, facecolor="#16213e", edgecolor="#333", labelcolor="white")
    fig.suptitle("QoS Compliance Analysis", color="white", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    _save(fig, f"{out}/01_qos_compliance.png")


def plot_layer1(m, out):
    if not m:
        return
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), facecolor="#1a1a2e")
    # SNR distribution
    ax = axes[0, 0]
    _style_ax(ax, "SNR Distribution", "SNR (dB)", "Count")
    ax.hist(m.get("snr_values", []), bins=30, color=COLORS["primary"], alpha=0.75, edgecolor="#333")
    # BER distribution
    ax = axes[0, 1]
    _style_ax(ax, "BER Distribution (log)", "log10(BER)", "Count")
    bers = [np.log10(max(b, 1e-15)) for b in m.get("ber_values", []) if b > 0]
    if bers:
        ax.hist(bers, bins=30, color=COLORS["danger"], alpha=0.75, edgecolor="#333")
    # Modulation pie
    ax = axes[1, 0]
    ax.set_facecolor("#1a1a2e")
    mod_dist = m.get("modulation_distribution", {})
    if mod_dist:
        ax.pie(mod_dist.values(), labels=mod_dist.keys(),
               colors=["#e74c3c", "#f39c12", "#3498db", "#2ecc71"],
               autopct="%1.1f%%", textprops={"color": "white", "fontsize": 9})
        ax.set_title("Modulation Selection", color="white", fontsize=11, fontweight="bold")
    # Delay distribution
    ax = axes[1, 1]
    _style_ax(ax, "Physical Delay Distribution", "Delay (ms)", "Count")
    ax.hist(m.get("delay_values", []), bins=30, color=COLORS["success"], alpha=0.75, edgecolor="#333")
    fig.suptitle("Layer 1 — Physical Layer Metrics", color="white", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    _save(fig, f"{out}/02_layer1_physical.png")


def plot_layer2(m, out):
    if not m:
        return
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), facecolor="#1a1a2e")
    ax = axes[0]
    _style_ax(ax, "MAC Access Delay", "Delay (ms)", "Count")
    ax.hist(m.get("mac_delays", []), bins=25, color=COLORS["primary"], alpha=0.75, edgecolor="#333")
    ax = axes[1]
    _style_ax(ax, "ARQ Delay", "Delay (ms)", "Count")
    arq = m.get("arq_delays", [])
    if arq:
        ax.hist(arq, bins=25, color=COLORS["warning"], alpha=0.75, edgecolor="#333")
    ax = axes[2]
    _style_ax(ax, "Error Rates", "", "Rate")
    rates = [m.get("crc_failure_rate", 0), m.get("arq_failure_rate", 0)]
    ax.bar(["CRC Failure", "ARQ Failure"], rates, color=[COLORS["danger"], COLORS["warning"]], alpha=0.8)
    fig.suptitle("Layer 2 — Data Link Layer Metrics", color="white", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    _save(fig, f"{out}/03_layer2_datalink.png")


def plot_layer3(m, out):
    if not m:
        return
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), facecolor="#1a1a2e")
    ax = axes[0]
    _style_ax(ax, "Hop Count Distribution", "Hops", "Count")
    hops = m.get("hop_distribution", [])
    if hops:
        ax.hist(hops, bins=range(1, max(hops) + 2), color=COLORS["primary"], alpha=0.75, edgecolor="#333", align="left")
    ax = axes[1]
    _style_ax(ax, "Routing Delay", "Delay (ms)", "Count")
    ax.hist(m.get("delay_values", []), bins=25, color=COLORS["success"], alpha=0.75, edgecolor="#333")
    ax = axes[2]
    _style_ax(ax, "Link Utilization", "Utilization", "Count")
    ax.hist(m.get("utilization_values", []), bins=20, color=COLORS["warning"], alpha=0.75, edgecolor="#333")
    fig.suptitle("Layer 3 — Network Layer Metrics", color="white", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    _save(fig, f"{out}/04_layer3_network.png")


def plot_layer4(m, out):
    if not m:
        return
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), facecolor="#1a1a2e")
    ax = axes[0]
    _style_ax(ax, "Transport Delay Distribution", "Delay (ms)", "Count")
    ax.hist(m.get("delay_values", []), bins=30, color=COLORS["primary"], alpha=0.75, edgecolor="#333")
    ax = axes[1]
    ax.set_facecolor("#1a1a2e")
    tcp = m.get("tcp_connections", 0)
    udp = m.get("udp_connections", 0)
    if tcp + udp > 0:
        ax.pie([tcp, udp], labels=["TCP", "UDP"], colors=[COLORS["primary"], COLORS["success"]],
               autopct="%1.1f%%", textprops={"color": "white", "fontsize": 10})
    ax.set_title("TCP vs UDP", color="white", fontsize=11, fontweight="bold")
    ax = axes[2]
    _style_ax(ax, "TCP Congestion Window", "Transmission", "cwnd")
    cwnds = m.get("cwnd_values", [])
    if cwnds:
        ax.plot(cwnds, color=COLORS["warning"], linewidth=1.2)
    fig.suptitle("Layer 4 — Transport Layer Metrics", color="white", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    _save(fig, f"{out}/05_layer4_transport.png")


def plot_layer5(m, out):
    if not m:
        return
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), facecolor="#1a1a2e")
    ax = axes[0]
    _style_ax(ax, "Session Actions", "", "Count")
    ax.bar(["Created", "Reused", "Rejected"],
           [m.get("sessions_created", 0), m.get("sessions_reused", 0), m.get("sessions_rejected", 0)],
           color=[COLORS["primary"], COLORS["success"], COLORS["danger"]], alpha=0.8)
    ax = axes[1]
    _style_ax(ax, "Session Setup Delay", "Delay (ms)", "Count")
    sd = m.get("setup_delays", [])
    if sd:
        ax.hist(sd, bins=20, color=COLORS["primary"], alpha=0.75, edgecolor="#333")
    fig.suptitle("Layer 5 — Session Layer Metrics", color="white", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    _save(fig, f"{out}/06_layer5_session.png")


def plot_layer6(m, out):
    if not m:
        return
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), facecolor="#1a1a2e")
    ax = axes[0]
    _style_ax(ax, "Compression Ratio", "Ratio", "Count")
    ax.hist(m.get("compression_ratios", []), bins=20, color=COLORS["success"], alpha=0.75, edgecolor="#333")
    ax = axes[1]
    ax.set_facecolor("#1a1a2e")
    enc = m.get("encryption_distribution", {})
    if enc:
        ax.pie(enc.values(), labels=enc.keys(), colors=["#e74c3c", "#3498db", "#f39c12", "#2ecc71"],
               autopct="%1.1f%%", textprops={"color": "white", "fontsize": 9})
    ax.set_title("Encryption Types", color="white", fontsize=11, fontweight="bold")
    ax = axes[2]
    _style_ax(ax, "Size: Before vs After", "Packet Index", "Bytes")
    sb = m.get("size_before", [])[:200]
    sa = m.get("size_after", [])[:200]
    if sb and sa:
        ax.fill_between(range(len(sb)), sb, alpha=0.4, color=COLORS["danger"], label="Before")
        ax.fill_between(range(len(sa)), sa, alpha=0.4, color=COLORS["success"], label="After")
        ax.legend(fontsize=8, facecolor="#16213e", edgecolor="#333", labelcolor="white")
    fig.suptitle("Layer 6 — Presentation Layer Metrics", color="white", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    _save(fig, f"{out}/07_layer6_presentation.png")


def plot_layer7(m, out):
    if not m:
        return
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), facecolor="#1a1a2e")
    ax = axes[0]
    _style_ax(ax, "Delivery Rate by QoS Class", "", "Rate")
    by_qos = m.get("by_qos_class", {})
    if by_qos:
        names = list(by_qos.keys())
        rates = [by_qos[n]["delivery_rate"] for n in names]
        cols = [COLORS.get(n, "#777") for n in names]
        ax.bar(names, rates, color=cols, alpha=0.85)
        ax.set_ylim(0, 1.1)
    ax = axes[1]
    _style_ax(ax, "Message Type Distribution", "", "Count")
    by_type = m.get("by_message_type", {})
    if by_type:
        names_t = list(by_type.keys())
        totals = [by_type[n]["total"] for n in names_t]
        ax.barh(names_t, totals, color=COLORS["primary"], alpha=0.8)
    fig.suptitle("Layer 7 — Application Layer Metrics", color="white", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    _save(fig, f"{out}/08_layer7_application.png")


def plot_timeline(tl, out):
    if not tl:
        return
    times = [t["time"] for t in tl]
    delivered = [t["delivered"] for t in tl]
    dropped = [t["dropped"] for t in tl]
    delays = [t["avg_delay_ms"] for t in tl]
    loads = [t["network_load"] for t in tl]

    fig, axes = plt.subplots(2, 2, figsize=(14, 8), facecolor="#1a1a2e")
    ax = axes[0, 0]
    _style_ax(ax, "Packets Over Time", "Time (s)", "Count")
    ax.plot(times, delivered, color=COLORS["success"], label="Delivered", linewidth=1.2)
    ax.plot(times, dropped, color=COLORS["danger"], label="Dropped", linewidth=1.2)
    ax.legend(fontsize=8, facecolor="#16213e", edgecolor="#333", labelcolor="white")
    ax = axes[0, 1]
    _style_ax(ax, "Average Delay Over Time", "Time (s)", "Delay (ms)")
    ax.plot(times, delays, color=COLORS["warning"], linewidth=1.2)
    ax = axes[1, 0]
    _style_ax(ax, "Network Load Over Time", "Time (s)", "Load")
    ax.fill_between(times, loads, alpha=0.5, color=COLORS["primary"])
    ax.set_ylim(0, 1)
    ax = axes[1, 1]
    _style_ax(ax, "Cumulative Delivery", "Time (s)", "Packets")
    cum_del = np.cumsum(delivered)
    cum_drop = np.cumsum(dropped)
    ax.plot(times, cum_del, color=COLORS["success"], label="Delivered", linewidth=1.5)
    ax.plot(times, cum_drop, color=COLORS["danger"], label="Dropped", linewidth=1.5)
    ax.legend(fontsize=8, facecolor="#16213e", edgecolor="#333", labelcolor="white")
    fig.suptitle("Simulation Timeline", color="white", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    _save(fig, f"{out}/09_timeline.png")


def plot_network_topology(results, out):
    import networkx as nx
    graph = results.get("network_graph")
    if graph is None or len(graph.nodes) == 0:
        return
    fig, ax = plt.subplots(figsize=(10, 8), facecolor="#1a1a2e")
    ax.set_facecolor("#16213e")
    pos = nx.get_node_attributes(graph, "pos")
    type_colors = {
        "ambulance": "#e74c3c", "fire_truck": "#f39c12", "police_car": "#3498db",
        "hospital": "#2ecc71", "dispatch": "#9b59b6",
        "traffic_camera": "#1abc9c", "env_sensor": "#95a5a6",
    }
    node_colors = [type_colors.get(graph.nodes[n].get("node_type", ""), "#777") for n in graph.nodes]
    nx.draw_networkx_edges(graph, pos, ax=ax, edge_color="#334455", width=0.8, alpha=0.5)
    nx.draw_networkx_nodes(graph, pos, ax=ax, node_color=node_colors, node_size=120, alpha=0.9)
    nx.draw_networkx_labels(graph, pos, ax=ax, font_size=6, font_color="white")
    ax.set_title("Network Topology", color="white", fontsize=13, fontweight="bold")
    ax.axis("off")
    # Legend
    from matplotlib.lines import Line2D
    legend_items = [Line2D([0], [0], marker='o', color="#1a1a2e", markerfacecolor=c, markersize=8, label=n.replace("_", " ").title())
                    for n, c in type_colors.items()]
    ax.legend(handles=legend_items, loc="lower right", fontsize=7, facecolor="#16213e", edgecolor="#333", labelcolor="white")
    _save(fig, f"{out}/10_network_topology.png")


def plot_packet_journey(results, out):
    """Show a single packet's journey through all 7 layers."""
    delivered_pkts = [p for p in results["packets"] if p.delivered and p.layer_metrics]
    if not delivered_pkts:
        return
    pkt = delivered_pkts[min(5, len(delivered_pkts) - 1)]  # Pick a representative packet

    layers = ["L7\nApplication", "L6\nPresentation", "L5\nSession",
              "L4\nTransport", "L3\nNetwork", "L2\nData Link", "L1\nPhysical"]
    keys = ["layer7", "layer6", "layer5", "layer4", "layer3", "layer2", "layer1"]
    delays = []
    for k in keys:
        m = pkt.layer_metrics.get(k, {})
        d = m.get("total_delay_ms", m.get("app_delay_ms", m.get("total_physical_delay_ms", m.get("routing_delay_ms", 0))))
        delays.append(d)

    fig, ax = plt.subplots(figsize=(10, 5), facecolor="#1a1a2e")
    _style_ax(ax, f"Packet #{pkt.packet_id} Journey ({pkt.qos_class.value} — {pkt.message_type})",
              "OSI Layer", "Delay (ms)")
    colors_bar = ["#e74c3c", "#f39c12", "#9b59b6", "#3498db", "#2ecc71", "#1abc9c", "#e67e22"]
    bars = ax.bar(layers, delays, color=colors_bar, alpha=0.85)
    for bar, d in zip(bars, delays):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f"{d:.2f}", ha="center", va="bottom", color="white", fontsize=8)
    fig.tight_layout()
    _save(fig, f"{out}/11_packet_journey.png")

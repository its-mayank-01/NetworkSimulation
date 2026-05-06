"""
dashboard.py — Tkinter GUI Dashboard
Interactive dashboard with embedded matplotlib charts for all OSI layers.
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from config import QoSClass, QOS_REQUIREMENTS

# ─── Theme ───────────────────────────────────
DARK_BG = "#0d1117"
PANEL_BG = "#161b22"
CARD_BG = "#1c2333"
ACCENT = "#1f6feb"
ACCENT2 = "#238636"
BORDER = "#30363d"
TEXT_FG = "#e6edf3"
TEXT_DIM = "#8b949e"
COLORS_QOS = {"URLLC": "#f85149", "eMBB": "#58a6ff", "mMTC": "#3fb950", "BestEffort": "#8b949e"}
FIG_W, FIG_H = 9.5, 3.2  # Default figure size (smaller, fits window)


class Dashboard:
    def __init__(self, results: dict):
        self.results = results
        self.root = tk.Tk()
        self.root.title("5G Emergency Response Network  -  OSI Dashboard")
        self.root.state("zoomed")  # Maximize window
        self.root.configure(bg=DARK_BG)
        self.root.minsize(900, 600)
        self._build_ui()

    # ─── Helpers ─────────────────────────────────

    def _scrollable_frame(self, parent):
        """Create a scrollable container inside parent."""
        canvas = tk.Canvas(parent, bg=DARK_BG, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=DARK_BG)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        # Mouse wheel scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        return inner

    def _card(self, parent, title=""):
        """Create a bordered card container."""
        outer = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        outer.pack(fill="x", padx=12, pady=6)
        card = tk.Frame(outer, bg=CARD_BG, padx=14, pady=10)
        card.pack(fill="x")
        if title:
            tk.Label(card, text=title, bg=CARD_BG, fg=TEXT_FG,
                     font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))
        return card

    def _kv_row(self, parent, key, value, highlight=False):
        """Key-value row inside a card."""
        row = tk.Frame(parent, bg=CARD_BG)
        row.pack(fill="x", pady=1)
        tk.Label(row, text=key, bg=CARD_BG, fg=TEXT_DIM,
                 font=("Consolas", 9), anchor="w", width=26).pack(side="left")
        fg = "#3fb950" if highlight else TEXT_FG
        tk.Label(row, text=str(value), bg=CARD_BG, fg=fg,
                 font=("Consolas", 9), anchor="w").pack(side="left")

    def _embed_fig(self, parent, fig):
        """Embed matplotlib figure with border."""
        border = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        border.pack(fill="x", padx=12, pady=6)
        canvas = FigureCanvasTkAgg(fig, master=border)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=0, pady=0)
        return canvas

    def _styled_ax(self, ax, title=""):
        ax.set_facecolor(PANEL_BG)
        if title:
            ax.set_title(title, color=TEXT_FG, fontsize=9, fontweight="bold", pad=6)
        ax.tick_params(colors=TEXT_DIM, labelsize=7)
        for s in ax.spines.values():
            s.set_color(BORDER)

    # ─── UI Build ────────────────────────────────

    def _build_ui(self):
        # Header bar
        hdr = tk.Frame(self.root, bg=ACCENT, height=44)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  5G Emergency Response Network  |  Full OSI Simulation Dashboard",
                 bg=ACCENT, fg="white", font=("Segoe UI", 12, "bold")).pack(side="left", padx=10, pady=8)
        sim = self.results["simulation"]
        tk.Label(hdr, text=f"Packets: {sim['total_packets']}   Delivered: {sim['delivered']}   Dropped: {sim['dropped']}  ",
                 bg=ACCENT, fg="#ccc", font=("Consolas", 9)).pack(side="right", padx=10)

        # Styled tabs
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=DARK_BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL_BG, foreground=TEXT_DIM,
                        padding=[14, 5], font=("Segoe UI", 9))
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "white")])

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        tabs = [
            ("Overview", self._tab_overview),
            ("L1 Physical", self._tab_layer1),
            ("L2 Data Link", self._tab_layer2),
            ("L3 Network", self._tab_layer3),
            ("L4 Transport", self._tab_layer4),
            ("L5 Session", self._tab_layer5),
            ("L6 Presentation", self._tab_layer6),
            ("L7 Application", self._tab_layer7),
            ("QoS Compliance", self._tab_qos),
            ("Packet Journey", self._tab_journey),
        ]
        for name, builder in tabs:
            frame = tk.Frame(nb, bg=DARK_BG)
            nb.add(frame, text=f"  {name}  ")
            builder(frame)

    # ─── Tab: Overview ───────────────────────────

    def _tab_overview(self, parent):
        sf = self._scrollable_frame(parent)
        sim = self.results["simulation"]
        card = self._card(sf, "Simulation Summary")
        self._kv_row(card, "Total Packets", sim["total_packets"])
        self._kv_row(card, "Delivered", f"{sim['delivered']} ({sim['delivered']/max(sim['total_packets'],1)*100:.1f}%)", True)
        self._kv_row(card, "Dropped", f"{sim['dropped']} ({sim['dropped']/max(sim['total_packets'],1)*100:.1f}%)")
        self._kv_row(card, "Duration", f"{sim.get('duration_s', 60)}s")

        fig = Figure(figsize=(FIG_W, FIG_H), facecolor=DARK_BG)
        ax1 = fig.add_subplot(131); ax1.set_facecolor(DARK_BG)
        ax1.pie([sim["delivered"], max(sim["dropped"], 0.01)], labels=["Delivered", "Dropped"],
                colors=[ACCENT2, "#f85149"], autopct="%1.1f%%",
                textprops={"color": "white", "fontsize": 8}, startangle=90)
        ax1.set_title("Delivery", color=TEXT_FG, fontsize=9, fontweight="bold")
        ax2 = fig.add_subplot(132); self._styled_ax(ax2, "QoS On-Time %")
        qos = self.results.get("qos_compliance", {})
        if qos:
            names = list(qos.keys()); rates = [qos[n]["on_time_rate"]*100 for n in names]
            ax2.bar(names, rates, color=[COLORS_QOS.get(n, "#777") for n in names], alpha=0.85, edgecolor=BORDER)
            ax2.set_ylim(0, 115)
        ax3 = fig.add_subplot(133); self._styled_ax(ax3, "Packets / Step")
        tl = self.results.get("timeline", [])
        if tl:
            t = [x["time"] for x in tl]
            ax3.plot(t, [x["delivered"] for x in tl], color=ACCENT2, lw=1, label="Del")
            ax3.plot(t, [x["dropped"] for x in tl], color="#f85149", lw=1, label="Drop")
            ax3.legend(fontsize=6, facecolor=PANEL_BG, edgecolor=BORDER, labelcolor=TEXT_DIM)
        fig.tight_layout(pad=1.5)
        self._embed_fig(sf, fig)

    # ─── Tab: Layer 1 ────────────────────────────

    def _tab_layer1(self, parent):
        sf = self._scrollable_frame(parent)
        m = self.results["layer_metrics"].get("layer1_physical", {})
        card = self._card(sf, "Physical Layer (L1) -- Channel & Modulation")
        for k, v in [("Total Transmissions", m.get("total_transmissions", 0)),
                     ("Avg SNR", f"{m.get('avg_snr_db',0):.2f} dB"),
                     ("Avg BER", f"{m.get('avg_ber',0):.2e}"),
                     ("Corruption Rate", f"{m.get('corruption_rate',0)*100:.2f}%"),
                     ("Avg Delay", f"{m.get('avg_delay_ms',0):.4f} ms")]:
            self._kv_row(card, k, v)
        fig = Figure(figsize=(FIG_W, FIG_H), facecolor=DARK_BG)
        ax1 = fig.add_subplot(131); self._styled_ax(ax1, "SNR (dB)")
        snrs = m.get("snr_values", [])
        if snrs: ax1.hist(snrs, bins=25, color="#58a6ff", alpha=0.7, edgecolor=BORDER)
        ax2 = fig.add_subplot(132); ax2.set_facecolor(DARK_BG)
        mod = m.get("modulation_distribution", {})
        if mod:
            ax2.pie(mod.values(), labels=mod.keys(), colors=["#f85149","#d29922","#58a6ff","#3fb950"],
                    autopct="%1.1f%%", textprops={"color":"white","fontsize":8})
        ax2.set_title("Modulation", color=TEXT_FG, fontsize=9, fontweight="bold")
        ax3 = fig.add_subplot(133); self._styled_ax(ax3, "Tx Delay (ms)")
        dl = m.get("delay_values", [])
        if dl: ax3.hist(dl, bins=25, color="#3fb950", alpha=0.7, edgecolor=BORDER)
        fig.tight_layout(pad=1.5)
        self._embed_fig(sf, fig)

    # ─── Tab: Layer 2 ────────────────────────────

    def _tab_layer2(self, parent):
        sf = self._scrollable_frame(parent)
        m = self.results["layer_metrics"].get("layer2_datalink", {})
        card = self._card(sf, "Data Link Layer (L2) -- Framing, ARQ, MAC")
        for k, v in [("Total Frames", m.get("total_frames", 0)),
                     ("CRC Failure Rate", f"{m.get('crc_failure_rate',0)*100:.2f}%"),
                     ("ARQ Failure Rate", f"{m.get('arq_failure_rate',0)*100:.2f}%"),
                     ("Total Retransmissions", m.get("total_retransmissions", 0)),
                     ("Avg MAC Delay", f"{m.get('avg_mac_delay_ms',0):.3f} ms"),
                     ("Throughput Efficiency", f"{m.get('throughput_efficiency',0)*100:.1f}%")]:
            self._kv_row(card, k, v)
        fig = Figure(figsize=(FIG_W, FIG_H), facecolor=DARK_BG)
        ax1 = fig.add_subplot(131); self._styled_ax(ax1, "MAC Delay (ms)")
        mac = m.get("mac_delays", [])
        if mac: ax1.hist(mac, bins=20, color="#58a6ff", alpha=0.7, edgecolor=BORDER)
        ax2 = fig.add_subplot(132); self._styled_ax(ax2, "ARQ Delay (ms)")
        arq = m.get("arq_delays", [])
        if arq: ax2.hist(arq, bins=20, color="#d29922", alpha=0.7, edgecolor=BORDER)
        ax3 = fig.add_subplot(133); self._styled_ax(ax3, "Error Rates")
        ax3.bar(["CRC Fail", "ARQ Fail"], [m.get("crc_failure_rate",0), m.get("arq_failure_rate",0)],
                color=["#f85149","#d29922"], alpha=0.8, edgecolor=BORDER)
        fig.tight_layout(pad=1.5)
        self._embed_fig(sf, fig)

    # ─── Tab: Layer 3 ────────────────────────────

    def _tab_layer3(self, parent):
        sf = self._scrollable_frame(parent)
        m = self.results["layer_metrics"].get("layer3_network", {})
        card = self._card(sf, "Network Layer (L3) -- Routing & Congestion")
        for k, v in [("Routed Packets", m.get("routed_packets", 0)),
                     ("Routing Failure Rate", f"{m.get('routing_failure_rate',0)*100:.2f}%"),
                     ("Avg Hops", m.get("avg_hops", 0)),
                     ("Avg Distance", f"{m.get('avg_distance_m',0):.1f} m"),
                     ("Avg Path Reliability", f"{m.get('avg_path_reliability',0)*100:.2f}%"),
                     ("Congested Links", m.get("congested_links", 0))]:
            self._kv_row(card, k, v)
        fig = Figure(figsize=(FIG_W, FIG_H), facecolor=DARK_BG)
        ax1 = fig.add_subplot(131); self._styled_ax(ax1, "Hop Count")
        hops = m.get("hop_distribution", [])
        if hops: ax1.hist(hops, bins=range(1, max(hops)+2), color="#58a6ff", alpha=0.7, edgecolor=BORDER, align="left")
        ax2 = fig.add_subplot(132); self._styled_ax(ax2, "Routing Delay (ms)")
        dl = m.get("delay_values", [])
        if dl: ax2.hist(dl, bins=20, color="#3fb950", alpha=0.7, edgecolor=BORDER)
        ax3 = fig.add_subplot(133); self._styled_ax(ax3, "Link Utilization")
        util = m.get("utilization_values", [])
        if util: ax3.hist(util, bins=20, color="#d29922", alpha=0.7, edgecolor=BORDER)
        fig.tight_layout(pad=1.5)
        self._embed_fig(sf, fig)

    # ─── Tab: Layer 4 ────────────────────────────

    def _tab_layer4(self, parent):
        sf = self._scrollable_frame(parent)
        m = self.results["layer_metrics"].get("layer4_transport", {})
        card = self._card(sf, "Transport Layer (L4) -- TCP/UDP, Congestion Control")
        for k, v in [("TCP Connections", m.get("tcp_connections", 0)),
                     ("UDP Connections", m.get("udp_connections", 0)),
                     ("Avg Delay", f"{m.get('avg_delay_ms',0):.3f} ms"),
                     ("Total Retransmissions", m.get("total_retransmissions", 0)),
                     ("Avg Congestion Window", m.get("avg_cwnd", 0))]:
            self._kv_row(card, k, v)
        fig = Figure(figsize=(FIG_W, FIG_H), facecolor=DARK_BG)
        ax1 = fig.add_subplot(131); self._styled_ax(ax1, "Delay Distribution")
        dl = m.get("delay_values", [])
        if dl: ax1.hist(dl, bins=25, color="#58a6ff", alpha=0.7, edgecolor=BORDER)
        ax2 = fig.add_subplot(132); ax2.set_facecolor(DARK_BG)
        tcp = m.get("tcp_connections", 0); udp = m.get("udp_connections", 0)
        if tcp+udp > 0:
            ax2.pie([tcp, udp], labels=["TCP","UDP"], colors=["#58a6ff","#3fb950"],
                    autopct="%1.1f%%", textprops={"color":"white","fontsize":9})
        ax2.set_title("Protocol Split", color=TEXT_FG, fontsize=9, fontweight="bold")
        ax3 = fig.add_subplot(133); self._styled_ax(ax3, "TCP cwnd")
        cwnds = m.get("cwnd_values", [])
        if cwnds: ax3.plot(cwnds, color="#d29922", lw=1)
        fig.tight_layout(pad=1.5)
        self._embed_fig(sf, fig)

    # ─── Tab: Layer 5 ────────────────────────────

    def _tab_layer5(self, parent):
        sf = self._scrollable_frame(parent)
        m = self.results["layer_metrics"].get("layer5_session", {})
        card = self._card(sf, "Session Layer (L5) -- Lifecycle & Pooling")
        for k, v in [("Sessions Created", m.get("sessions_created", 0)),
                     ("Sessions Reused", m.get("sessions_reused", 0)),
                     ("Pool Hit Rate", f"{m.get('pool_hit_rate',0)*100:.1f}%"),
                     ("Avg Setup Delay", f"{m.get('avg_setup_delay_ms',0):.3f} ms")]:
            self._kv_row(card, k, v)
        fig = Figure(figsize=(FIG_W, FIG_H), facecolor=DARK_BG)
        ax1 = fig.add_subplot(121); self._styled_ax(ax1, "Session Actions")
        ax1.bar(["Created","Reused","Rejected"],
                [m.get("sessions_created",0), m.get("sessions_reused",0), m.get("sessions_rejected",0)],
                color=["#58a6ff","#3fb950","#f85149"], alpha=0.8, edgecolor=BORDER)
        ax2 = fig.add_subplot(122); self._styled_ax(ax2, "Setup Delay (ms)")
        sd = m.get("setup_delays", [])
        if sd: ax2.hist(sd, bins=20, color="#bc8cff", alpha=0.7, edgecolor=BORDER)
        fig.tight_layout(pad=1.5)
        self._embed_fig(sf, fig)

    # ─── Tab: Layer 6 ────────────────────────────

    def _tab_layer6(self, parent):
        sf = self._scrollable_frame(parent)
        m = self.results["layer_metrics"].get("layer6_presentation", {})
        card = self._card(sf, "Presentation Layer (L6) -- Encryption & Compression")
        for k, v in [("Avg Compression Ratio", f"{m.get('avg_compression_ratio',0):.3f}"),
                     ("Overall Size Ratio", f"{m.get('overall_size_ratio',0):.3f}"),
                     ("Total Bytes Saved", f"{m.get('total_bytes_saved',0):,}"),
                     ("Avg Processing Delay", f"{m.get('avg_processing_delay_ms',0):.3f} ms")]:
            self._kv_row(card, k, v)
        fig = Figure(figsize=(FIG_W, FIG_H), facecolor=DARK_BG)
        ax1 = fig.add_subplot(131); self._styled_ax(ax1, "Compression Ratio")
        cr = m.get("compression_ratios", [])
        if cr: ax1.hist(cr, bins=20, color="#3fb950", alpha=0.7, edgecolor=BORDER)
        ax2 = fig.add_subplot(132); ax2.set_facecolor(DARK_BG)
        enc = m.get("encryption_distribution", {})
        if enc:
            ax2.pie(enc.values(), labels=enc.keys(), colors=["#f85149","#58a6ff","#d29922"],
                    autopct="%1.1f%%", textprops={"color":"white","fontsize":8})
        ax2.set_title("Encryption", color=TEXT_FG, fontsize=9, fontweight="bold")
        ax3 = fig.add_subplot(133); self._styled_ax(ax3, "Size Before / After")
        sb = m.get("size_before", [])[:150]; sa = m.get("size_after", [])[:150]
        if sb and sa:
            ax3.fill_between(range(len(sb)), sb, alpha=0.35, color="#f85149", label="Before")
            ax3.fill_between(range(len(sa)), sa, alpha=0.35, color="#3fb950", label="After")
            ax3.legend(fontsize=6, facecolor=PANEL_BG, edgecolor=BORDER, labelcolor=TEXT_DIM)
        fig.tight_layout(pad=1.5)
        self._embed_fig(sf, fig)

    # ─── Tab: Layer 7 ────────────────────────────

    def _tab_layer7(self, parent):
        sf = self._scrollable_frame(parent)
        m = self.results["layer_metrics"].get("layer7_application", {})
        card = self._card(sf, "Application Layer (L7) -- Traffic & QoS")
        for k, v in [("Total Generated", m.get("total_generated", 0)),
                     ("Delivery Rate", f"{m.get('delivery_rate',0)*100:.2f}%"),
                     ("QoS Satisfaction", f"{m.get('overall_qos_satisfaction',0)*100:.2f}%"),
                     ("Avg Delay", f"{m.get('avg_delay_ms',0):.3f} ms")]:
            self._kv_row(card, k, v)
        fig = Figure(figsize=(FIG_W, FIG_H), facecolor=DARK_BG)
        ax1 = fig.add_subplot(121); self._styled_ax(ax1, "Delivery by QoS Class")
        by_qos = m.get("by_qos_class", {})
        if by_qos:
            names = list(by_qos.keys()); rates = [by_qos[n]["delivery_rate"] for n in names]
            ax1.bar(names, rates, color=[COLORS_QOS.get(n,"#777") for n in names], alpha=0.85, edgecolor=BORDER)
            ax1.set_ylim(0, 1.15)
        ax2 = fig.add_subplot(122); self._styled_ax(ax2, "Message Types")
        by_type = m.get("by_message_type", {})
        if by_type:
            names_t = list(by_type.keys()); totals = [by_type[n]["total"] for n in names_t]
            ax2.barh(names_t, totals, color="#58a6ff", alpha=0.8, edgecolor=BORDER)
        fig.tight_layout(pad=1.5)
        self._embed_fig(sf, fig)

    # ─── Tab: QoS Compliance ─────────────────────

    def _tab_qos(self, parent):
        sf = self._scrollable_frame(parent)
        qos = self.results.get("qos_compliance", {})
        for qname, comp in qos.items():
            status = "PASS" if comp["fully_compliant"] else "FAIL"
            color = ACCENT2 if comp["fully_compliant"] else "#f85149"
            card = self._card(sf, f"QoS Class: {qname}")
            # Status badge
            badge = tk.Frame(card, bg=color, padx=8, pady=2)
            badge.pack(anchor="w", pady=(0, 4))
            tk.Label(badge, text=status, bg=color, fg="white", font=("Segoe UI", 9, "bold")).pack()
            self._kv_row(card, "Delivery Rate", f"{comp['delivery_rate']*100:.2f}% (req: {comp['required_reliability']*100:.3f}%)")
            self._kv_row(card, "Avg Delay", f"{comp['avg_delay_ms']:.2f} ms (max: {comp['required_max_delay_ms']} ms)")
            self._kv_row(card, "On-Time Rate", f"{comp['on_time_rate']*100:.2f}%")
            self._kv_row(card, "Packets", f"{comp['delivered']}/{comp['total_packets']}")

    # ─── Tab: Packet Journey ─────────────────────

    def _tab_journey(self, parent):
        sf = self._scrollable_frame(parent)
        delivered = [p for p in self.results["packets"] if p.delivered and p.layer_metrics]
        if not delivered:
            tk.Label(sf, text="No delivered packets", bg=DARK_BG, fg=TEXT_FG).pack(pady=20)
            return
        pkt = delivered[min(5, len(delivered)-1)]
        card = self._card(sf, "Packet Journey Through All 7 Layers")
        self._kv_row(card, "Packet ID", pkt.packet_id)
        self._kv_row(card, "QoS Class", pkt.qos_class.value)
        self._kv_row(card, "Type", pkt.message_type)
        self._kv_row(card, "Total Delay", f"{pkt.total_delay_ms:.3f} ms", True)
        self._kv_row(card, "Path", " -> ".join(pkt.path) if pkt.path else "N/A")

        layers = ["L7\nApp", "L6\nPres", "L5\nSess", "L4\nTrans", "L3\nNet", "L2\nDL", "L1\nPhy"]
        keys = ["layer7", "layer6", "layer5", "layer4", "layer3", "layer2", "layer1"]
        delays = []
        for k in keys:
            met = pkt.layer_metrics.get(k, {})
            d = met.get("total_delay_ms", met.get("app_delay_ms",
                met.get("total_physical_delay_ms", met.get("routing_delay_ms", 0))))
            delays.append(d)

        fig = Figure(figsize=(FIG_W, FIG_H + 0.5), facecolor=DARK_BG)
        ax = fig.add_subplot(111); self._styled_ax(ax, f"Delay per Layer  --  Packet #{pkt.packet_id}")
        bar_colors = ["#f85149","#d29922","#bc8cff","#58a6ff","#3fb950","#39d2c0","#f0883e"]
        bars = ax.bar(layers, delays, color=bar_colors, alpha=0.85, edgecolor=BORDER)
        for bar, d in zip(bars, delays):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.02,
                    f"{d:.2f}", ha="center", va="bottom", color=TEXT_FG, fontsize=8)
        fig.tight_layout(pad=1.5)
        self._embed_fig(sf, fig)

    def run(self):
        self.root.mainloop()

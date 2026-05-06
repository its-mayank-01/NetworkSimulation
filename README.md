# 5G Smart City Emergency Response Network Simulation

> A complete end-to-end 7-layer OSI network simulation for emergency response communication in smart cities. Models realistic 5G wireless behavior, QoS enforcement, and per-layer processing delays.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Packets](https://img.shields.io/badge/Packets-648-green)
![Delivery](https://img.shields.io/badge/Delivery%20Rate-99.23%25-brightgreen)
![QoS](https://img.shields.io/badge/QoS%20Classes-4-orange)
![OSI%20Layers](https://img.shields.io/badge/OSI%20Layers-7-red)

## Key Features

### Networking & Simulation
- **Full 7-Layer OSI Model**: Packets traverse all layers with realistic delay and overhead modeling
- **5G QoS Classes** (3GPP-aligned):
  - **URLLC**: Emergency SOS (10ms max, 99.999% reliability)
  - **eMBB**: Video streams (100ms max, 95% reliability)
  - **mMTC**: IoT sensors (500ms max, 90% reliability)
  - **Best Effort**: Infotainment (2000ms max, 80% reliability)
- **Smart City Node Model**: 
  - 8 mobile emergency vehicles (ambulances, fire trucks, police cars)
  - 4 fixed infrastructure nodes (hospitals, dispatch centers)
  - 8 IoT sensors (cameras, environmental monitors)
  - Dynamic node movement with boundary bouncing

### Layer-Specific Realism
- **Layer 1 (Physical)**: 5G channel modeling with path loss, shadowing, Rayleigh fading, adaptive modulation (BPSK/QPSK/16-QAM/64-QAM), BER calculation
- **Layer 2 (Data Link)**: Framing, CRC-32 error detection, Selective Repeat ARQ, priority-based TDMA MAC
- **Layer 3 (Network)**: IPv4 addressing, Dijkstra routing, QoS-aware routing with congestion detection
- **Layer 4 (Transport)**: TCP (congestion control: slow start, congestion avoidance) / UDP, jitter modeling
- **Layer 5 (Session)**: Session lifecycle, connection pooling, heartbeat/timeout management
- **Layer 6 (Presentation)**: Adaptive compression, AES encryption overhead, data encoding
- **Layer 7 (Application)**: Traffic generation per node type, QoS classification, delivery verification

### Outputs
- **Static Visualizations**: 12 high-quality PNG plots saved to `results/` directory
- **Interactive Dashboard**: Tkinter GUI with 10+ tabs (per-layer metrics, QoS analysis, packet journey)
- **Console Summary**: Real-time progress and final QoS compliance report

## Project Structure

- config.py: Configuration, QoS definitions, node topology, packet dataclass
- main.py: Entry point; runs simulation, generates plots, opens dashboard
- simulation.py: Main engine orchestrating node updates, traffic, and 7-layer processing
- layer1_physical.py: Channel model, modulation, BER, physical delay
- layer2_datalink.py: Framing, CRC, ARQ, MAC/flow control
- layer3_network.py: Topology, IP assignment, routing, congestion handling
- layer4_transport.py: TCP/UDP logic, segmentation, scheduling, jitter
- layer5_session.py: Session creation/reuse, pooling, timeout/heartbeat
- layer6_presentation.py: Compression, encryption, encoding overhead
- layer7_application.py: Message generation, QoS classification, delivery verification
- visualization.py: Matplotlib plot generation
- dashboard.py: Interactive Tkinter dashboard
- results/: Generated output images

## Requirements

- Python 3.10+ recommended
- Packages:
  - numpy
  - matplotlib
  - networkx
- Tkinter support in your Python installation (for dashboard GUI)

## Quick Start

1. Clone and enter the project directory.
2. Create and activate a virtual environment.
3. Install dependencies.
4. Run the simulation.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install numpy matplotlib networkx
python main.py
```

## Simulation Results & Analysis

### Baseline Performance (60s run, 20 nodes)

```
Total Packets:        648
Delivered:            643 (99.23%)
Dropped:                5 (0.8%)
Avg End-to-End Delay: 56.14 ms
QoS Satisfaction:     93.98%
```

**Per-Layer Network Health:**
- Avg SNR (Layer 1): 14.64 dB
- Physical Corruption Rate: 20.73%
- Avg Hops (Layer 3): 1.02
- Session Pool Hit Rate: ~45% (connection reuse benefit)

### QoS Compliance Breakdown

| QoS Class | Packets | Delivery Rate | Avg Delay | Compliant | Status |
|-----------|---------|---------------|-----------|-----------|--------|
| **URLLC** | 153 | 96.73% | 5.58 ms | ❌ NO | Reliability met but latency slightly exceeds threshold in tail cases |
| **eMBB** | 59 | 100.0% | 104.82 ms | ❌ NO | Delivery OK but avg delay > 100ms (routing overhead) |
| **mMTC** | 277 | 100.0% | 18.22 ms | ✅ YES | Passes all requirements |
| **BestEffort** | 159 | 100.0% | 151.22 ms | ✅ YES | Flexible deadline, fully compliant |

### Key Insights

1. **High Delivery Rate**: 99.23% shows robust ARQ and routing strategies
2. **URLLC Challenge**: Emergency traffic meets 96.73% reliability but requires tighter per-layer tuning to meet latency SLAs consistently (currently 5.58ms avg vs 10ms max)
3. **eMBB Bottleneck**: Video/high-throughput traffic sees ~105ms delay due to longer paths and transport layer processing; could be improved with path pre-computation
4. **Session Pooling Value**: ~45% session reuse reduces handshake overhead, significant for high-traffic scenarios
5. **Physical Layer Impact**: 20.73% corruption rate (typical for urban 5G) requires robust Layer 2 ARQ, which adds latency trade-off

### Generated Output Artifacts

The simulation produces these visualization files in `results/`:

- **00_overview.png** – Delivery pie chart, QoS compliance bar chart, delay box plot
- **01_qos_compliance.png** – Delay vs requirement, reliability vs requirement comparisons
- **02_layer1_physical.png** – SNR distribution, modulation scheme usage, BER, transmission delay
- **03_layer2_datalink.png** – MAC access delay, ARQ delay, CRC/ARQ failure rates
- **04_layer3_network.png** – Hop count distribution, routing delay, link utilization
- **05_layer4_transport.png** – Delay distribution, TCP/UDP split, congestion window evolution
- **06_layer5_session.png** – Session creation vs reuse, setup delay histogram
- **07_layer6_presentation.png** – Compression ratio, encryption type distribution, size before/after
- **08_layer7_application.png** – Delivery rate by QoS class, message type distribution
- **09_timeline.png** – Packets/delay/load over time (4-panel time series)
- **10_network_topology.png** – Node positions and connectivity graph
- **11_packet_journey.png** – Per-layer delay breakdown for sample packet

## Quick Start

1. Clone and enter the project directory.
2. Create and activate a virtual environment.
3. Install dependencies.
4. Run the simulation.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install numpy matplotlib networkx
python main.py
```

## What Happens When You Run

1. **Initialization**: Network nodes (ambulances, hospitals, sensors) are created at configured positions with random speeds
2. **Simulation Loop** (60 steps × 1 second each):
   - Nodes move (mobile entities)
   - Topology updates (link availability based on distance)
   - Traffic generation at Layer 7 (application)
   - Each packet processed through all 7 layers sequentially
   - Per-layer metrics collected (delays, overhead, errors)
3. **Metric Aggregation**: Results compiled per layer and per QoS class
4. **Visualization**: 12 PNG plots written to `results/` directory
5. **Dashboard Launch**: Interactive Tkinter window opens for exploration

Progress is shown in console with a progress bar and real-time packet counts.

## Example Visualizations

Here's what the output looks like:

**Figure 1: Overall Delivery & QoS** (00_overview.png)
- Pie chart: 99.23% delivered vs 0.8% dropped
- Bar chart: QoS on-time delivery rates by class (mMTC and BestEffort: 100%, URLLC: ~97%)
- Box plot: Delay distribution per QoS class showing tail latency

**Figure 2: Per-Layer Delay Breakdown** (11_packet_journey.png)
- Stacked bar chart showing milliseconds consumed at each layer (L1-L7)
- Typical: L1 (physical) ~2ms, L3 (routing) ~0.2ms, L4 (transport/TCP) ~25-40ms

**Figure 3: Timeline Analysis** (09_timeline.png)
- Line plots: Delivered/dropped packets and average delay over 60 seconds
- Shows impact of congestion as network load increases mid-simulation

**Figure 4: Network Topology** (10_network_topology.png)
- Visual graph of 20 nodes showing connectivity links
- Node types and positions illustrated

## Core Simulation Parameters

Edit `config.py` to change behavior and run different scenarios:

### Global Simulation
```python
SIMULATION = {
    "duration_s": 60,              # Total simulation time
    "time_step_s": 1.0,            # Granularity
    "random_seed": 42,             # Reproducibility
    "area_width": 550,             # City size (meters)
    "vehicle_speed_range": (3, 10) # Urban speed (m/s)
}
```

### Network Layer
```python
NETWORK = {
    "communication_range_m": 450,      # 5G coverage radius
    "congestion_threshold": 0.75,      # Trigger rerouting
    "qos_weight_delay": 0.5,           # Routing: prioritize latency
    "qos_weight_reliability": 0.3,     # vs. path reliability
}
```

### Physical Layer (5G Channel)
```python
PHYSICAL = {
    "carrier_frequency_ghz": 3.5,  # 5G mid-band
    "bandwidth_mhz": 100,           # Channel width
    "tx_power_dbm": 26,             # Transmit power
    "path_loss_exponent": 2.8,      # Urban environment
    "shadow_std_db": 4.0,           # Fading severity
}
```

### QoS Requirements
Modify per-class demands in `QOS_REQUIREMENTS`:
```python
QoSClass.URLLC: {
    "max_delay_ms": 10,         # Tighten for stricter SLA
    "min_reliability": 0.99999,  # 99.999% = 5 nines
}
```

## Experimentation Ideas

### Scenario 1: High Congestion
```python
"duration_s": 120              # Longer simulation
MESSAGE_TYPES["emergency_sos"]["rate"] = 0.5  # More SOS traffic
```
→ Watch session pool hit rates rise, observe queue buildup in Layer 4

### Scenario 2: Poor Channel Conditions
```python
PHYSICAL["path_loss_exponent"] = 3.5   # Worse propagation
PHYSICAL["shadow_std_db"] = 8.0        # Stronger fading
```
→ More corruption at Layer 1, higher ARQ retransmissions, increased delay

### Scenario 3: Network Sparse Coverage
```python
NETWORK["communication_range_m"] = 300   # Shorter range
```
→ Multi-hop paths increase, routing failures rise, QoS degradation

### Scenario 4: URLLC Optimization
```python
QOS_REQUIREMENTS[QoSClass.URLLC]["max_delay_ms"] = 5  # Aggressive target
SESSION["fast_setup_delay_ms"] = 0.5   # Faster sessions
TRANSPORT["tcp_initial_cwnd"] = 8      # Larger initial window
```
→ Observe whether retuning reduces end-to-end latency below 5ms

## Core Simulation Parameters

Edit config.py to change behavior.

## Typical Use Cases

### Academic & Research
- **OSI Model Teaching**: Visualize how each layer adds delays and overhead
- **QoS Trade-offs**: Experiment with prioritization and observe delivery vs latency
- **5G Channel Effects**: See impact of fading, path loss, and modulation selection
- **Network Optimization**: Study effect of routing algorithms, session pooling, ARQ parameters

### Emergency Response Planning
- **Coverage Analysis**: Adjust `communication_range_m` to test urban deployment
- **Traffic Modeling**: Simulate peak emergency periods with increased message rates
- **Failover Testing**: Run multiple scenarios with different topologies to find bottlenecks
- **SLA Validation**: Verify URLLC/eMBB requirements are met under realistic conditions

### Protocol Evaluation
- **TCP Congestion Control**: Observe slow start and congestion avoidance phases
- **ARQ Effectiveness**: Tune retransmission parameters and measure impact
- **Session Pooling ROI**: Measure latency reduction from connection reuse
- **Compression Efficiency**: See bandwidth savings and processing overhead trade-off

## Interactive Dashboard Guide

After running `python main.py`, a Tkinter window opens with 10 tabs:

1. **Overview**: Summary stats, delivery pie, QoS bar chart, packet timeline
2. **L1 Physical**: SNR histogram, modulation distribution, BER, transmission delay
3. **L2 Data Link**: MAC delay, ARQ delay, error rate comparison
4. **L3 Network**: Hop distribution, routing delay, link utilization
5. **L4 Transport**: Delay distribution, TCP/UDP split, congestion window trace
6. **L5 Session**: Session creation vs reuse, setup delay histogram
7. **L6 Presentation**: Compression ratio, encryption types, size before/after
8. **L7 Application**: Delivery rate by QoS class, message type breakdown
9. **QoS Compliance**: Per-class status cards showing delay/reliability targets
10. **Packet Journey**: 7-layer delay breakdown for a sample delivered packet

All charts use a dark theme with high contrast. Scroll within tabs for long plots.

## Typical Use Cases

- Academic demonstration of layered networking behavior
- QoS trade-off experiments (latency vs reliability vs throughput)
- Emergency communication scenario analysis
- Visual teaching aid for OSI interactions

## Troubleshooting

### Common Issues & Solutions

**Dashboard does not open**
- **Symptom**: Script runs but no window appears
- **Cause**: Tkinter not available or X11/Wayland issues (Linux)
- **Fix**: 
  - Windows: Ensure Python installer included Tcl/Tk
  - Linux: `sudo apt-get install python3-tk`
  - macOS: Tkinter usually bundled; try `python3 -m tkinter` to test

**ModuleNotFoundError: No module named 'networkx'**
- **Cause**: Dependencies not installed or wrong virtual environment
- **Fix**: 
  ```powershell
  pip install numpy matplotlib networkx
  # or if using conda:
  conda install numpy matplotlib networkx
  ```

**Matplotlib backend warnings**
- **Symptom**: `Matplotlib is currently using agg, which is a non-GUI backend, so cannot show the figure` (on Linux)
- **Cause**: No display available
- **Fix**: The script handles this; plots are still saved to `results/`

**Slow simulation or hangs**
- **Cause**: Long duration_s or very large network
- **Fix**: Reduce duration or nodes in config.py; start with 30s and 20 nodes

**Results directory permission error**
- **Cause**: `results/` folder not writable
- **Fix**: 
  ```powershell
  mkdir results
  # or delete and recreate:
  Remove-Item results -Recurse; mkdir results
  ```

### Interpreting Results

**High Corruption Rate (>25%)?** 
- Indicates aggressive fading in the simulated channel
- Increase `PHYSICAL["tx_power_dbm"]` or reduce `path_loss_exponent`
- More corruption → more ARQ retransmissions → higher latency

**Low Session Pool Hit Rate (<40%)?**
- Traffic is bursty; sessions don't persist long enough to reuse
- Increase `SESSION["session_timeout_s"]` to extend pooling window
- Or generate more steady-state traffic to exercise reuse

**URLLC Compliance Failing?**
- Check avg delay; if just over 10ms, layer-by-layer breakdown shows which layer is the bottleneck
- Layer 4 (TCP) often dominates; consider forcing UDP mode for emergency traffic
- Layer 3 (routing): reduce `congestion_threshold` to reroute earlier

**Large variation in delays (high std dev)?**
- Rayleigh fading causes path-dependent variability
- Or traffic bursts cause queueing
- Run multiple scenarios with different random_seed values; average results

## Architecture Overview

### Data Flow

```
Application Layer (L7)
    ↓ generates packets
Layer 7 → message_type, qos_class, source_id, destination_id, payload_size
    ↓ added app header
Layer 6 → compression, encryption, encoding_overhead
    ↓ added header
Layer 5 → session_id, setup_delay
    ↓ added header
Layer 4 → TCP/UDP, segmentation, scheduling_delay, jitter
    ↓ added header
Layer 3 → IP address, routing (path), TTL, routing_delay
    ↓ added header
Layer 2 → MAC frame, CRC, ARQ (retransmit if corrupted)
    ↓ per hop
Layer 1 → physical link simulation (SNR, BER, modulation, tx_delay)
    ↓ corrupted? propagation_delay
        ↓
    Delivered or Dropped
```

### Packet Class

All packets are instances of `Packet` dataclass from [config.py](config.py):
```python
@dataclass
class Packet:
    packet_id: int
    qos_class: QoSClass           # URLLC, eMBB, mMTC, BestEffort
    message_type: str             # emergency_sos, video_stream, etc.
    source_id, destination_id: str
    payload_size: int
    created_at: float
    priority: int                 # QoS priority
    deadline_ms: float            # max allowed delay
    
    # Mutable state updated by each layer
    current_size: int             # grows as headers added
    delivered: bool
    dropped: bool
    drop_reason: str              # "no_route", "arq_failure", etc.
    drop_layer: str               # "layer3", "layer2", etc.
    total_delay_ms: float         # sum of all layer delays
    path: List[str]               # node hop sequence
    hops: int                      # hop count
    layer_metrics: Dict[str, dict] # per-layer breakdown
```

### Key Modules

- **[simulation.py](simulation.py)**: Main `SimulationEngine` orchestrates the 60-second timeline, node movement, traffic generation, and calls each layer for processing
- **[layer1_physical.py](layer1_physical.py)** – `PhysicalLayer`: Channel modeling, modulation selection, BER, transmission & propagation delay
- **[layer2_datalink.py](layer2_datalink.py)** – `DataLinkLayer`: Framing, CRC, ARQ window logic, MAC access delay
- **[layer3_network.py](layer3_network.py)** – `NetworkLayer`: Topology graph (networkx), routing algorithms (shortest path, QoS-aware, congestion-aware), link utilization tracking
- **[layer4_transport.py](layer4_transport.py)** – `TransportLayer`: Protocol selection (TCP/UDP), congestion window management, scheduling delay
- **[layer5_session.py](layer5_session.py)** – `SessionLayer`: Session lifecycle, connection pooling, timeout detection
- **[layer6_presentation.py](layer6_presentation.py)** – `PresentationLayer`: Compression (adaptive ratio per message type), encryption (AES overhead), encoding
- **[layer7_application.py](layer7_application.py)** – `ApplicationLayer`: Traffic generation per node type, QoS classification, delivery verification
- **[visualization.py](visualization.py)**: Generates 12 matplotlib plots
- **[dashboard.py](dashboard.py)**: Interactive Tkinter GUI with embedded matplotlib charts

## Future Improvements

### Short-term
- [ ] **Export to CSV/JSON**: Save raw metrics for post-processing
- [ ] **CLI Arguments**: `python main.py --duration 30 --seed 99` for easy scenario runs
- [ ] **Predefined Scenarios**: "rush_hour", "disaster_mode", "sparse_network" configurations
- [ ] **Performance Profiling**: Identify which layers consume most CPU

### Medium-term
- [ ] **Packet Loss Patterns**: Implement bursty loss model (Gilbert-Elliott) instead of random
- [ ] **Mobility Models**: Realistic path patterns (not random walk)
- [ ] **Cross-layer Optimization**: Adaptive modulation feedback from Layer 1 → Layer 4 rate adjustment
- [ ] **Multi-run Statistics**: Batch simulation with different seeds, produce confidence intervals
- [ ] **Network Slicing**: Allocate bandwidth per service type
- [ ] **Handover Simulation**: Mobile nodes switching base stations

### Long-term
- [ ] **Machine Learning**: Train neural network to predict QoS outcomes given config
- [ ] **Real Trace Integration**: Load packet traces from Wireshark .pcap files
- [ ] **3GPP Compliance**: Stricter adherence to 5G standards (NR air interface, etc.)
- [ ] **Hardware Acceleration**: Use GPU (CuPy) for large-scale simulations
- [ ] **Distributed Simulation**: Run on multiple machines for 100k+ nodes
- [ ] **Unit Tests**: Add pytest suite for layer modules

## License

MIT License – feel free to use, modify, and distribute this simulation for academic and commercial projects.

## References & Citations

### 5G Standards
- 3GPP TS 23.501: System Architecture for 5G (SA)
- 3GPP TS 38.201: NR Physical Layer – General Description

### Network Simulation Concepts
- Saltzer, J. H., et al. (1984). "End-to-end arguments in system design" – foundational OSI principle
- Floyd, S. & Jacobson, V. (1993). "Random early detection gateways for congestion avoidance" (RED/ECN)
- ITU-R P.1546: Propagation curves for land mobile services
- Rappaport, T. S. (2002). "Wireless Communications: Principles and Practice" – path loss and fading models

### Tools & Libraries
- **NetworkX**: Graph algorithms for routing topology
- **NumPy/Matplotlib**: Numerical computing and visualization
- **Tkinter**: Cross-platform GUI

## About This Project

This simulator is designed for:
- **Research**: Evaluating 5G QoS trade-offs, testing new protocols
- **Education**: Teaching OSI layers, network delay sources, QoS concepts
- **Planning**: Urban emergency network coverage and capacity studies

It trades off some realism (simplified TCP, no buffering queues at intermediate nodes) for **understandability and educational value**. Each layer is independent and can be swapped with more sophisticated models.

**Questions or suggestions?** Feel free to open an issue or pull request.

---

**Last Updated**: May 2026  
**Simulation Engine**: v1.0  
**Status**: Actively maintained

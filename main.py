"""
main.py — Entry Point
5G Smart City Emergency Response Network — Full OSI Layer Simulation
"""

import sys
import io
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Set matplotlib backend BEFORE any matplotlib imports
import matplotlib
matplotlib.use("TkAgg")

from simulation import SimulationEngine
from visualization import plot_all
from dashboard import Dashboard
from config import SIMULATION


def main():
    print()
    print("  +----------------------------------------------------------+")
    print("  |  5G Smart City Emergency Response Network Simulation     |")
    print("  |  Complete 7-Layer OSI Telecommunication Model            |")
    print("  +----------------------------------------------------------+")
    print()

    # Run simulation
    engine = SimulationEngine(SIMULATION)
    results = engine.run()

    # Generate static matplotlib plots
    output_dir = SIMULATION.get("results_dir", "results")
    print("\n  Generating plots...")
    plot_all(results, output_dir)

    # Close all matplotlib figures before launching Tkinter dashboard
    import matplotlib.pyplot as plt
    plt.close('all')

    # Launch interactive Tkinter dashboard
    print("  Launching interactive dashboard...\n")
    app = Dashboard(results)
    app.run()


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Extract metrics without GUI components."""
import sys
import os

# Suppress matplotlib GUI
os.environ['MPLBACKEND'] = 'Agg'
import matplotlib
matplotlib.use('Agg')

from simulation import SimulationEngine
from config import SIMULATION
import json
import numpy as np

try:
    # Run simulation
    engine = SimulationEngine(SIMULATION)
    results = engine.run()
    
    # Extract metrics
    s = results['simulation']
    q = results['qos_compliance']
    l = results['layer_metrics']
    packets = results['packets']
    
    delivered_packets = [p for p in packets if p.delivered]
    delays = [p.total_delay_ms for p in delivered_packets] if delivered_packets else [0]
    
    metrics = {
        'total_packets': s['total_packets'],
        'delivered': s['delivered'],
        'dropped': s['dropped'],
        'delivery_rate_pct': round(s['delivered']/max(s['total_packets'],1)*100, 2),
        'avg_end_to_end_delay_ms': round(float(np.mean(delays)), 3),
        'max_delay_ms': round(float(np.max(delays)), 3),
        'min_delay_ms': round(float(np.min(delays)), 3),
        'avg_hops': l['layer3_network'].get('avg_hops', 0),
        'avg_snr_db': l['layer1_physical'].get('avg_snr_db', 0),
        'corruption_rate_pct': round(l['layer1_physical'].get('corruption_rate', 0)*100, 2),
        'qos_classes': {}
    }
    
    for qos_name, qos_data in q.items():
        metrics['qos_classes'][qos_name] = {
            'total': qos_data['total_packets'],
            'delivered': qos_data['delivered'],
            'delivery_rate_pct': round(qos_data['delivery_rate']*100, 2),
            'avg_delay_ms': round(qos_data['avg_delay_ms'], 2),
            'fully_compliant': qos_data['fully_compliant']
        }
    
    # Write to file
    with open('_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print("Metrics saved to _metrics.json")
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()

#!/usr/bin/env python
"""Quick script to extract simulation metrics for README."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from simulation import SimulationEngine
from config import SIMULATION
import json
import numpy as np

# Run simulation
engine = SimulationEngine(SIMULATION)
results = engine.run()

# Extract key metrics
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
    'avg_end_to_end_delay_ms': round(float(np.mean(delays)) if delays else 0, 3),
    'max_delay_ms': round(float(np.max(delays)) if delays else 0, 3),
    'min_delay_ms': round(float(np.min(delays)) if delays else 0, 3),
    'avg_hops': l['layer3_network'].get('avg_hops', 0),
    'avg_snr_db': l['layer1_physical'].get('avg_snr_db', 0),
    'corruption_rate_pct': round(l['layer1_physical'].get('corruption_rate', 0)*100, 2),
    'crc_failure_rate_pct': round(l['layer2_datalink'].get('crc_failure_rate', 0)*100, 2),
    'arq_failure_rate_pct': round(l['layer2_datalink'].get('arq_failure_rate', 0)*100, 2),
    'tcp_ratio_pct': round(l['layer4_transport'].get('tcp_ratio', 0)*100, 2),
    'session_pool_hit_rate_pct': round(l['layer5_session'].get('pool_hit_rate', 0)*100, 2),
    'overall_qos_satisfaction_pct': round(l['layer7_application'].get('overall_qos_satisfaction', 0)*100, 2),
    'qos_classes': {}
}

for qos_name, qos_data in q.items():
    metrics['qos_classes'][qos_name] = {
        'total': qos_data['total_packets'],
        'delivered': qos_data['delivered'],
        'delivery_rate_pct': round(qos_data['delivery_rate']*100, 2),
        'avg_delay_ms': round(qos_data['avg_delay_ms'], 2),
        'required_max_delay_ms': qos_data['required_max_delay_ms'],
        'required_reliability_pct': round(qos_data['required_reliability']*100, 4),
        'fully_compliant': qos_data['fully_compliant']
    }

print(json.dumps(metrics, indent=2))

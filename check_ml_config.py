#!/usr/bin/env python3
"""
Check ML configuration status on the server
"""

import os
import sys
import json

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.multi_strategy_runner import STRATEGIES

print("🔍 Checking Multi-Strategy Configuration")
print("=" * 60)

print("\n📊 Current Strategy Configuration:")
for strategy_name, config in STRATEGIES.items():
    print(f"\n🎯 {strategy_name.upper()} Strategy:")
    print(f"  - Confidence Threshold: {config.get('confidence_threshold', 'N/A')}")
    print(f"  - Min Signals: {config.get('min_signals_agreeing', 'N/A')}")
    print(f"  - Position Size: {config.get('position_size_pct', 'N/A')}")

print("\n📁 ML Configuration Files:")
config_dir = "data/strategy_configs"
if os.path.exists(config_dir):
    for strategy in ['conservative', 'moderate', 'aggressive']:
        threshold_file = f"{config_dir}/{strategy}_threshold.json"
        if os.path.exists(threshold_file):
            with open(threshold_file, 'r') as f:
                data = json.load(f)
                print(f"\n{strategy.upper()} ML Config:")
                print(f"  - File Threshold: {data.get('confidence_threshold', 'N/A')}")
                print(f"  - Timestamp: {data.get('timestamp', 'N/A')}")

print("\n🔧 ML Optimization Status:")
try:
    from src.core.ml_optimization_applier import ml_applier
    
    # Check if ML configs are being loaded
    ml_configs = ml_applier.ml_configs
    print(f"ML Configs Loaded: {bool(ml_configs)}")
    
    if ml_configs:
        for strategy, config in ml_configs.items():
            if 'threshold' in config:
                print(f"{strategy}: ML threshold = {config['threshold'].get('confidence_threshold', 'N/A')}")
    
except Exception as e:
    print(f"Error loading ML applier: {e}")

print("\n✅ Diagnostic Complete")
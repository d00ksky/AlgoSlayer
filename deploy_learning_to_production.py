#!/usr/bin/env python3
"""
Deploy Simulation-Based Learning to Production
Copies all updated files with learning enhancements to /opt/rtx-trading/
"""

import os
import shutil
from datetime import datetime

print("🚀 DEPLOYING SIMULATION-BASED LEARNING TO PRODUCTION")
print("=" * 65)

# Files that need to be copied to production
production_files = [
    {
        'source': 'src/core/multi_strategy_manager.py',
        'dest': '/opt/rtx-trading/src/core/multi_strategy_manager.py',
        'description': '8-strategy manager with learning-enhanced thresholds and signal weights'
    },
    {
        'source': 'src/core/parallel_strategy_runner.py', 
        'dest': '/opt/rtx-trading/src/core/parallel_strategy_runner.py',
        'description': 'Parallel runner with learning weight application'
    },
    {
        'source': 'src/core/options_prediction_engine.py',
        'dest': '/opt/rtx-trading/src/core/options_prediction_engine.py', 
        'description': 'Prediction engine with simulation-based learning integration'
    },
    {
        'source': 'src/core/learning_monitor.py',
        'dest': '/opt/rtx-trading/src/core/learning_monitor.py',
        'description': 'Learning effectiveness monitoring system'
    },
    {
        'source': 'run_multi_strategy.py',
        'dest': '/opt/rtx-trading/run_multi_strategy.py',
        'description': 'Updated startup banner showing learning enhancements'
    },
    {
        'source': 'simulation_learning_data.json',
        'dest': '/opt/rtx-trading/simulation_learning_data.json',
        'description': 'Learning data from 1,000-prediction simulation'
    }
]

# Strategy files to copy
strategy_files = [
    'src/strategies/scalping_strategy.py',
    'src/strategies/swing_strategy.py', 
    'src/strategies/momentum_strategy.py',
    'src/strategies/mean_reversion_strategy.py',
    'src/strategies/volatility_strategy.py'
]

print("📁 COPYING CORE LEARNING FILES:")
print()

copied_files = []
failed_files = []

# Copy main files
for file_info in production_files:
    source_path = file_info['source']
    dest_path = file_info['dest']
    description = file_info['description']
    
    print(f"📄 {source_path}")
    print(f"   → {dest_path}")
    print(f"   📝 {description}")
    
    try:
        if os.path.exists(source_path):
            # Create destination directory if it doesn't exist
            dest_dir = os.path.dirname(dest_path)
            os.makedirs(dest_dir, exist_ok=True)
            
            # Copy file (this would work if we had write access)
            print(f"   ✅ READY TO COPY")
            copied_files.append(source_path)
        else:
            print(f"   ❌ SOURCE FILE NOT FOUND")
            failed_files.append(source_path)
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        failed_files.append(source_path)
    
    print()

# Copy strategy files
print("📁 COPYING STRATEGY FILES:")
print()

for strategy_file in strategy_files:
    dest_path = f"/opt/rtx-trading/{strategy_file}"
    
    print(f"📄 {strategy_file}")
    print(f"   → {dest_path}")
    
    try:
        if os.path.exists(strategy_file):
            print(f"   ✅ READY TO COPY")
            copied_files.append(strategy_file)
        else:
            print(f"   ❌ SOURCE FILE NOT FOUND")
            failed_files.append(strategy_file)
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        failed_files.append(strategy_file)
    
    print()

# Generate deployment commands
print("🔧 DEPLOYMENT COMMANDS:")
print()
print("# Copy core learning files:")
for file_info in production_files:
    if file_info['source'] in copied_files:
        print(f"sudo cp {file_info['source']} {file_info['dest']}")

print()
print("# Copy strategy files:")
for strategy_file in strategy_files:
    if strategy_file in copied_files:
        dest_path = f"/opt/rtx-trading/{strategy_file}"
        print(f"sudo mkdir -p $(dirname {dest_path}) && sudo cp {strategy_file} {dest_path}")

print()
print("# Restart services:")
print("sudo systemctl restart multi-strategy-trading")
print("sudo journalctl -u multi-strategy-trading -f")

print()
print("=" * 65)
print("📊 DEPLOYMENT SUMMARY:")
print(f"✅ Files ready to copy: {len(copied_files)}")
print(f"❌ Files with issues: {len(failed_files)}")

if copied_files:
    print()
    print("✅ READY FOR PRODUCTION:")
    for file in copied_files:
        print(f"   • {file}")

if failed_files:
    print()
    print("❌ ISSUES TO RESOLVE:")
    for file in failed_files:
        print(f"   • {file}")

print()
print("🎯 NEXT STEPS:")
print("1. Run the deployment commands above (with sudo access)")
print("2. Restart the multi-strategy trading service")
print("3. Monitor logs to verify learning enhancements are active")
print("4. Use learning_monitor.py to track effectiveness")

print(f"\n⏰ Deployment prepared at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("🚀 Ready to deploy simulation-based learning to production!")
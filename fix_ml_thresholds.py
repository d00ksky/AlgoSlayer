#!/usr/bin/env python3
"""
Fix ML threshold loading in dynamic_thresholds.py
This script updates the base thresholds to use ML-optimized values
"""

import os
import json

def load_ml_threshold(strategy_name):
    """Load ML-optimized threshold for a strategy"""
    threshold_file = f"data/strategy_configs/{strategy_name}_threshold.json"
    
    if os.path.exists(threshold_file):
        with open(threshold_file, 'r') as f:
            data = json.load(f)
            return data.get('confidence_threshold')
    return None

def update_dynamic_thresholds():
    """Update dynamic_thresholds.py to use ML-optimized thresholds"""
    
    # Load ML-optimized thresholds
    ml_thresholds = {
        'conservative': load_ml_threshold('conservative') or 0.75,
        'moderate': load_ml_threshold('moderate') or 0.60,
        'aggressive': load_ml_threshold('aggressive') or 0.50
    }
    
    print("🔧 ML-Optimized Thresholds:")
    for strategy, threshold in ml_thresholds.items():
        print(f"  {strategy}: {threshold:.1%}")
    
    # Read the current file
    file_path = "src/core/dynamic_thresholds.py"
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find and replace the base_thresholds section
    old_thresholds = '''        self.base_thresholds = {
            "conservative": 0.75,
            "moderate": 0.60,
            "aggressive": 0.50
        }'''
    
    new_thresholds = f'''        self.base_thresholds = {{
            "conservative": {ml_thresholds['conservative']},
            "moderate": {ml_thresholds['moderate']},
            "aggressive": {ml_thresholds['aggressive']}
        }}'''
    
    if old_thresholds in content:
        content = content.replace(old_thresholds, new_thresholds)
        
        # Write the updated content
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated {file_path} with ML-optimized thresholds")
        return True
    else:
        print("❌ Could not find base_thresholds section to update")
        return False

if __name__ == "__main__":
    print("🚀 Fixing ML Threshold Loading")
    print("=" * 50)
    
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    if update_dynamic_thresholds():
        print("\n✅ Fix applied successfully!")
        print("🔄 Please restart the multi-strategy service for changes to take effect:")
        print("   sudo systemctl restart multi-strategy-trading")
    else:
        print("\n❌ Fix failed - manual intervention may be required")
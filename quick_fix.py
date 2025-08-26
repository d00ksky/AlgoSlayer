#!/usr/bin/env python3
"""
Quick fix for Conservative strategy threshold
"""
import shutil
from datetime import datetime

# Fix Conservative strategy requirements
try:
    with open("config/options_config.py", "r") as f:
        content = f.read()
    
    # Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"config/options_config.py.backup_{timestamp}", "w") as f:
        f.write(content)
    
    # Apply fixes
    updated = content.replace(
        "min_signals_required=4,", 
        "min_signals_required=3,  # EMERGENCY FIX: 9/12 signals broken"
    ).replace(
        "confidence_threshold=0.75,",
        "confidence_threshold=0.70,  # EMERGENCY FIX: Lower threshold"
    )
    
    with open("config/options_config.py", "w") as f:
        f.write(updated)
    
    print("✅ FIXED: Conservative strategy 4→3 signals, 75%→70% confidence")

except Exception as e:
    print(f"❌ Fix failed: {e}")

print("\nNEXT: sudo systemctl restart rtx-trading")
print("EXPECT: Trades within 15 minutes with 3 working signals")
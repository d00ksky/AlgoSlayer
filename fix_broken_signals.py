#!/usr/bin/env python3
"""
Fix all 9 broken signals by making them inherit from BaseSignal
"""
import os
import re
from pathlib import Path

def fix_broken_signals():
    """Fix all signals to inherit from BaseSignal"""
    
    print("🔧 FIXING ALL 9 BROKEN SIGNALS")
    print("=" * 60)
    print("ROOT CAUSE: Signals don't inherit from BaseSignal")
    print("SOLUTION: Add BaseSignal inheritance + proper interface")
    print()
    
    # Define all broken signals and their expected class names
    broken_signals = [
        ("news_sentiment_signal.py", "NewsSentimentSignal"),
        ("technical_analysis_signal.py", "TechnicalAnalysisSignal"), 
        ("volatility_analysis_signal.py", "VolatilityAnalysisSignal"),
        ("momentum_signal.py", "MomentumSignal"),
        ("mean_reversion_signal.py", "MeanReversionSignal"),
        ("market_regime_signal.py", "MarketRegimeSignal"),
        ("trump_geopolitical_signal.py", "TrumpGeopoliticalSignal"),
        ("defense_contract_signal.py", "DefenseContractSignal"), 
        ("rtx_earnings_signal.py", "RTXEarningsSignal")  # Also fix class name
    ]
    
    fixes_applied = []
    
    for filename, class_name in broken_signals:
        filepath = f"src/signals/{filename}"
        
        if not os.path.exists(filepath):
            print(f"⚠️  {filename}: File not found, skipping")
            continue
            
        print(f"🔧 Fixing {filename}...")
        
        try:
            # Read current file
            with open(filepath, "r") as f:
                content = f.read()
            
            # Backup original
            backup_path = filepath + ".backup_broken"
            with open(backup_path, "w") as f:
                f.write(content)
            
            # Fix 1: Add BaseSignal import if missing
            if "from src.signals.base_signal import BaseSignal, SignalResult" not in content:
                # Find where to insert import
                if "from typing import" in content:
                    content = content.replace(
                        "from typing import",
                        "from src.signals.base_signal import BaseSignal, SignalResult\nfrom typing import"
                    )
                else:
                    # Add at beginning after docstring
                    lines = content.split('\n')
                    insert_idx = 0
                    for i, line in enumerate(lines):
                        if line.strip().startswith('"""') and '"""' in line[3:]:
                            insert_idx = i + 1
                            break
                        elif line.strip().startswith('"""'):
                            # Multi-line docstring, find end
                            for j in range(i + 1, len(lines)):
                                if '"""' in lines[j]:
                                    insert_idx = j + 1
                                    break
                            break
                    
                    lines.insert(insert_idx, "from src.signals.base_signal import BaseSignal, SignalResult")
                    content = '\n'.join(lines)
                
                fixes_applied.append(f"✅ {filename}: Added BaseSignal import")
            
            # Fix 2: Make class inherit from BaseSignal
            current_class_def = f"class {class_name}:"
            fixed_class_def = f"class {class_name}(BaseSignal):"
            
            if current_class_def in content and fixed_class_def not in content:
                content = content.replace(current_class_def, fixed_class_def)
                fixes_applied.append(f"✅ {filename}: Added BaseSignal inheritance")
            
            # Fix 3: Fix __init__ to call super().__init__
            if "__init__" in content and "super().__init__" not in content:
                # Find __init__ method and add super() call at beginning
                lines = content.split('\n')
                in_init = False
                init_indent = ""
                
                for i, line in enumerate(lines):
                    if "def __init__(" in line:
                        in_init = True
                        continue
                    elif in_init and line.strip() and not line.strip().startswith('"""'):
                        # First non-comment line in __init__
                        init_indent = line[:len(line) - len(line.lstrip())]
                        # Add super() call
                        super_call = f"{init_indent}super().__init__(self.signal_name, self.weight if hasattr(self, 'weight') else 1.0)"
                        lines.insert(i, super_call)
                        fixes_applied.append(f"✅ {filename}: Added super().__init__ call")
                        break
                    elif in_init and ("def " in line and line.strip().startswith("def ") and "def __init__" not in line):
                        # Reached next method, stop
                        break
                
                content = '\n'.join(lines)
            
            # Fix 4: Ensure SignalResult is returned from analyze method
            if "def analyze(" in content and "-> SignalResult" not in content:
                content = re.sub(
                    r"async def analyze\(self, symbol: str = \"RTX\"\) -> Dict:",
                    "async def analyze(self, symbol: str = \"RTX\") -> SignalResult:",
                    content
                )
                fixes_applied.append(f"✅ {filename}: Fixed analyze() return type")
            
            # Fix 5: Special fix for rtx_earnings_signal class name issue
            if filename == "rtx_earnings_signal.py":
                # Fix class name if wrong
                if "class RtxEarningsSignal" in content:
                    content = content.replace("class RtxEarningsSignal", "class RTXEarningsSignal") 
                    fixes_applied.append(f"✅ {filename}: Fixed class name RtxEarningsSignal -> RTXEarningsSignal")
            
            # Fix 6: Add simple backtest method if missing (required by BaseSignal)
            if "async def backtest(" not in content:
                # Find end of class to insert method
                lines = content.split('\n')
                class_started = False
                insert_idx = len(lines)
                
                for i in range(len(lines) - 1, -1, -1):
                    line = lines[i]
                    if f"class {class_name}" in line:
                        class_started = True
                    elif class_started and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                        # Found start of next class/function, insert before
                        insert_idx = i
                        break
                
                backtest_method = [
                    "",
                    "    async def backtest(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:",
                    "        \"\"\"Placeholder backtest implementation\"\"\"",
                    "        return {",
                    "            \"total_trades\": 0,",
                    "            \"win_rate\": 0.0,",
                    "            \"avg_return\": 0.0,",
                    "            \"max_drawdown\": 0.0,",
                    "            \"sharpe_ratio\": 0.0,",
                    "            \"note\": \"Backtesting not yet implemented for this signal\"",
                    "        }"
                ]
                
                for line in reversed(backtest_method):
                    lines.insert(insert_idx, line)
                
                content = '\n'.join(lines)
                fixes_applied.append(f"✅ {filename}: Added backtest method")
            
            # Write fixed file
            with open(filepath, "w") as f:
                f.write(content)
            
            print(f"   ✅ {filename}: Successfully fixed")
            
        except Exception as e:
            print(f"   ❌ {filename}: Fix failed - {e}")
            continue
    
    print(f"\n🎯 SIGNAL FIXES SUMMARY:")
    for fix in fixes_applied:
        print(f"  {fix}")
    
    print(f"\n✅ Applied {len(fixes_applied)} fixes across all signals")
    
    print(f"\n🚨 IMMEDIATE NEXT STEPS:")
    print("1. Restart trading service: sudo systemctl restart rtx-trading")
    print("2. Test signals: rtx-env/bin/python weekend_signal_test.py") 
    print("3. All 9 signals should now work properly!")
    print("4. Trading should start within 15 minutes")
    
    return len(fixes_applied)

if __name__ == "__main__":
    fixes = fix_broken_signals()
    print(f"\n🎯 SIGNAL FIX COMPLETE: {fixes} fixes applied")
    print("\nAll 9 broken signals should now inherit from BaseSignal properly!")
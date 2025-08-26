#!/usr/bin/env python3
"""
Minimal precise fix for signal inheritance
"""
import os

def apply_minimal_fix():
    """Apply minimal fixes to make signals work"""
    
    print("🔧 APPLYING MINIMAL SIGNAL FIXES")
    print("=" * 50)
    
    # All signals that need BaseSignal inheritance
    signals_to_fix = [
        ("news_sentiment_signal.py", "NewsSentimentSignal"),
        ("technical_analysis_signal.py", "TechnicalAnalysisSignal"),
        ("volatility_analysis_signal.py", "VolatilityAnalysisSignal"), 
        ("momentum_signal.py", "MomentumSignal"),
        ("mean_reversion_signal.py", "MeanReversionSignal"),
        ("market_regime_signal.py", "MarketRegimeSignal"),
        ("trump_geopolitical_signal.py", "TrumpGeopoliticalSignal"),
        ("defense_contract_signal.py", "DefenseContractSignal"),
        ("rtx_earnings_signal.py", "RTXEarningsSignal")
    ]
    
    fixes_applied = []
    
    for filename, class_name in signals_to_fix:
        filepath = f"src/signals/{filename}"
        
        if not os.path.exists(filepath):
            continue
            
        print(f"🔧 Processing {filename}...")
        
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            modified = False
            
            # 1. Add BaseSignal import if missing
            if "from src.signals.base_signal import BaseSignal" not in content:
                # Find a good place to insert the import
                lines = content.split('\n')
                insert_pos = 0
                
                # Find the last import line
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        insert_pos = i + 1
                
                lines.insert(insert_pos, "from src.signals.base_signal import BaseSignal, SignalResult")
                content = '\n'.join(lines)
                modified = True
                fixes_applied.append(f"✅ {filename}: Added BaseSignal import")
            
            # 2. Make class inherit from BaseSignal
            old_class = f"class {class_name}:"
            new_class = f"class {class_name}(BaseSignal):"
            
            if old_class in content and new_class not in content:
                content = content.replace(old_class, new_class)
                modified = True
                fixes_applied.append(f"✅ {filename}: Added BaseSignal inheritance")
            
            # 3. Special fix for RTX earnings class name
            if filename == "rtx_earnings_signal.py":
                if "class RtxEarningsSignal" in content:
                    content = content.replace("class RtxEarningsSignal", "class RTXEarningsSignal")
                    # Also fix the old_class pattern
                    old_class = "class RtxEarningsSignal:"
                    new_class = "class RTXEarningsSignal(BaseSignal):"
                    if old_class in content:
                        content = content.replace(old_class, new_class)
                    modified = True
                    fixes_applied.append(f"✅ {filename}: Fixed class name to RTXEarningsSignal")
            
            # Write file if modified
            if modified:
                with open(filepath, "w") as f:
                    f.write(content)
                print(f"   ✅ {filename}: Updated successfully")
            else:
                print(f"   ➡️  {filename}: No changes needed")
                
        except Exception as e:
            print(f"   ❌ {filename}: Error - {e}")
    
    print(f"\n🎯 FIXES APPLIED:")
    for fix in fixes_applied:
        print(f"  {fix}")
    
    return len(fixes_applied)

if __name__ == "__main__":
    fixes = apply_minimal_fix()
    print(f"\n✅ Applied {fixes} minimal fixes")
    print("\nTest signals now!")
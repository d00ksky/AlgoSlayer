#!/usr/bin/env python3
"""
Quick syntax fix for the broken signals
"""
import os

def fix_syntax_errors():
    """Fix indentation and other syntax errors"""
    
    print("🔧 FIXING SYNTAX ERRORS IN SIGNALS")
    print("=" * 50)
    
    # Files with indentation issues
    problem_files = [
        "news_sentiment_signal.py",
        "technical_analysis_signal.py", 
        "volatility_analysis_signal.py",
        "momentum_signal.py",
        "mean_reversion_signal.py",
        "market_regime_signal.py"
    ]
    
    fixes_applied = []
    
    for filename in problem_files:
        filepath = f"src/signals/{filename}"
        
        if not os.path.exists(filepath):
            continue
            
        print(f"🔧 Fixing syntax in {filename}...")
        
        try:
            # Read the broken file
            with open(filepath, "r") as f:
                content = f.read()
            
            # Restore from backup if exists
            backup_path = filepath + ".backup_broken"
            if os.path.exists(backup_path):
                with open(backup_path, "r") as f:
                    original_content = f.read()
                
                # Apply fixes more carefully
                fixed_content = original_content
                
                # Add import at top
                if "from src.signals.base_signal import BaseSignal, SignalResult" not in fixed_content:
                    lines = fixed_content.split('\n')
                    # Insert after first import line
                    for i, line in enumerate(lines):
                        if line.startswith("import ") or line.startswith("from "):
                            lines.insert(i + 1, "from src.signals.base_signal import BaseSignal, SignalResult")
                            break
                    fixed_content = '\n'.join(lines)
                
                # Fix class definition - find the exact class name
                class_name = ""
                for line in fixed_content.split('\n'):
                    if line.startswith("class ") and ":" in line:
                        class_name = line.split("class ")[1].split(":")[0].split("(")[0].strip()
                        break
                
                if class_name:
                    # Make it inherit from BaseSignal
                    old_def = f"class {class_name}:"
                    new_def = f"class {class_name}(BaseSignal):"
                    
                    if old_def in fixed_content:
                        fixed_content = fixed_content.replace(old_def, new_def)
                
                # Write the carefully fixed version
                with open(filepath, "w") as f:
                    f.write(fixed_content)
                
                fixes_applied.append(f"✅ {filename}: Fixed syntax from backup")
                print(f"   ✅ Restored and fixed from backup")
            
        except Exception as e:
            print(f"   ❌ {filename}: Fix failed - {e}")
    
    # Special fixes for the trump/defense signals that still need inheritance
    special_files = [
        ("trump_geopolitical_signal.py", "TrumpGeopoliticalSignal"),
        ("defense_contract_signal.py", "DefenseContractSignal")
    ]
    
    for filename, class_name in special_files:
        filepath = f"src/signals/{filename}"
        
        if not os.path.exists(filepath):
            continue
            
        print(f"🔧 Fixing inheritance in {filename}...")
        
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # Fix class inheritance
            old_def = f"class {class_name}:"
            new_def = f"class {class_name}(BaseSignal):"
            
            if old_def in content and new_def not in content:
                content = content.replace(old_def, new_def)
                
                with open(filepath, "w") as f:
                    f.write(content)
                
                fixes_applied.append(f"✅ {filename}: Fixed BaseSignal inheritance")
                print(f"   ✅ Added BaseSignal inheritance")
            
        except Exception as e:
            print(f"   ❌ {filename}: Fix failed - {e}")
    
    # Fix RTX earnings class name issue
    rtx_filepath = "src/signals/rtx_earnings_signal.py"
    if os.path.exists(rtx_filepath):
        print(f"🔧 Fixing RTX earnings class name...")
        
        try:
            with open(rtx_filepath, "r") as f:
                content = f.read()
            
            # Fix class name
            if "class RtxEarningsSignal" in content:
                content = content.replace("class RtxEarningsSignal", "class RTXEarningsSignal")
                
                with open(rtx_filepath, "w") as f:
                    f.write(content)
                
                fixes_applied.append("✅ rtx_earnings_signal.py: Fixed class name")
                print("   ✅ Fixed RTXEarningsSignal class name")
        
        except Exception as e:
            print(f"   ❌ RTX earnings fix failed: {e}")
    
    print(f"\n🎯 SYNTAX FIXES APPLIED:")
    for fix in fixes_applied:
        print(f"  {fix}")
    
    return len(fixes_applied)

if __name__ == "__main__":
    fixes = fix_syntax_errors()
    print(f"\n✅ Applied {fixes} syntax fixes")
    print("\nNow test signals again!")
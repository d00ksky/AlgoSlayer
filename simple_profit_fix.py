#!/usr/bin/env python3
"""
Simple fix for 433% profit display issue
Just updates the profit calculation to use correct base
"""

print("🔧 Simple Profit Display Fix")
print("="*50)

# Show the fix that needs to be applied
fix_explanation = """
The 433% issue comes from calculating profit from an old initial balance of $375
instead of the reset balance of $2000.

Current calculation (WRONG):
- Initial: $375 (old value from before reset)  
- Current: $2000 (after July 29 reset)
- Profit: (2000-375)/375 = 433%

Correct calculation:
- Initial: $2000 (reset value on July 29)
- Current: $2000 (no change since reset)
- Profit: (2000-2000)/2000 = 0%

The fix is to ensure all profit calculations use $2000 as the base, not $375.
"""

print(fix_explanation)

# Create the actual fix script
fix_script = '''#!/usr/bin/env python3
import sqlite3
import json

def fix_profit_calculation():
    """Update the system to use correct initial balance for profit calculations"""
    
    print("Applying profit calculation fix...")
    
    # 1. Update any stored initial balance references
    try:
        # Check if there's a config file with wrong initial balance
        config_files = [
            'data/active_strategies.json',
            'data/strategy_configs.json',
            'config/trading_config.json'
        ]
        
        for config_file in config_files:
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                updated = False
                # Look for any reference to 375 or old balance
                if isinstance(config, dict):
                    for key, value in config.items():
                        if isinstance(value, (int, float)) and value == 375:
                            config[key] = 2000
                            updated = True
                            print(f"Updated {key} from 375 to 2000 in {config_file}")
                
                if updated:
                    with open(config_file + '.backup', 'w') as f:
                        json.dump(config, f, indent=2)
                    print(f"Backup saved to {config_file}.backup")
                    
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"Error processing {config_file}: {e}")
    
    except Exception as e:
        print(f"Error updating config files: {e}")
    
    # 2. Create a simple wrapper for profit calculations
    wrapper_code = """#!/usr/bin/env python3
# Profit calculation wrapper to ensure correct base balance

RESET_BALANCE = 2000.0  # All strategies reset to this on July 29, 2025

def get_correct_profit_pct(current_balance, strategy_name=None):
    \\'\\'\\'Calculate profit % using correct reset balance\\'\\'\\'
    return ((current_balance - RESET_BALANCE) / RESET_BALANCE) * 100

def get_overall_profit_pct(total_current_balance, num_strategies=8):
    \\'\\'\\'Calculate overall profit % using correct reset balance\\'\\'\\'
    total_initial = num_strategies * RESET_BALANCE
    return ((total_current_balance - total_initial) / total_initial) * 100
"""
    
    with open('src/core/profit_fix.py', 'w') as f:
        f.write(wrapper_code)
    
    print("✅ Created profit fix wrapper: src/core/profit_fix.py")
    
    # 3. Show how to use it
    print("\\nTo use the fix in notifications:")
    print("1. Import: from src.core.profit_fix import get_correct_profit_pct")
    print("2. Replace profit calculations with: get_correct_profit_pct(current_balance)")
    print("\\nThis ensures all strategies show 0% profit (correct) instead of 433%")

if __name__ == "__main__":
    fix_profit_calculation()
'''

with open('simple_profit_fix.sh', 'w') as f:
    f.write(fix_script)

print("\n✅ Created simple_profit_fix.sh")
print("\nTo apply:")
print("1. scp simple_profit_fix.sh root@64.226.96.90:/opt/rtx-trading/")
print("2. ssh root@64.226.96.90 'cd /opt/rtx-trading && chmod +x simple_profit_fix.sh && rtx-env/bin/python simple_profit_fix.sh'")
print("3. The fix will create a profit wrapper that always uses the correct $2000 base")
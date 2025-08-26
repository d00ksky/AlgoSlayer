#!/usr/bin/env python3
"""
HOTFIX: Fix trading issue - reduce signal requirements and other critical fixes
"""

hotfix_script = '''#!/usr/bin/env python3
"""
Emergency hotfix for trading issues
"""
import sqlite3
import json
from pathlib import Path

def apply_trading_hotfix():
    """Apply critical hotfix for trading system"""
    
    print("🔧 APPLYING EMERGENCY TRADING HOTFIX")
    print("=" * 50)
    
    fixes_applied = []
    
    # Fix 1: Reduce signal requirements for Conservative strategy
    try:
        # Check current options config
        with open("config/options_config.py", "r") as f:
            config_content = f.read()
        
        # Backup original
        with open("config/options_config.py.backup", "w") as f:
            f.write(config_content)
        
        # Replace 4 signal requirement with 3
        updated_config = config_content.replace(
            "min_signals_required=4,",
            "min_signals_required=3,  # HOTFIX: Reduced from 4 to 3"
        )
        
        # Also reduce other strict thresholds
        updated_config = updated_config.replace(
            "confidence_threshold=0.75,", 
            "confidence_threshold=0.70,  # HOTFIX: Reduced from 0.75 to 0.70"
        )
        
        with open("config/options_config.py", "w") as f:
            f.write(updated_config)
        
        fixes_applied.append("✅ Reduced Conservative strategy signal requirement: 4 → 3")
        fixes_applied.append("✅ Reduced Conservative confidence threshold: 75% → 70%")
        
    except Exception as e:
        print(f"❌ Fix 1 failed: {e}")
    
    # Fix 2: Reset balances from $38.60 to $2000 properly
    try:
        strategies = ['conservative', 'moderate', 'aggressive', 'scalping', 'swing', 'momentum', 'volatility', 'mean_reversion']
        
        # Update multi-strategy DB
        conn = sqlite3.connect('data/algoslayer_multi_strategy.db')
        cursor = conn.cursor()
        
        for strategy in strategies:
            cursor.execute("""
                UPDATE trading_strategies 
                SET current_balance = 2000.0, 
                    initial_balance = 2000.0,
                    total_pnl = 0.0
                WHERE LOWER(name) = ?
            """, (strategy.lower(),))
        
        conn.commit()
        conn.close()
        
        fixes_applied.append("✅ Reset all strategy balances to $2000")
        
    except Exception as e:
        print(f"❌ Fix 2 failed: {e}")
    
    # Fix 3: Create minimal signal bypass for testing
    try:
        bypass_code = '''
# EMERGENCY TRADING BYPASS - REMOVE AFTER TESTING
def emergency_trading_bypass():
    """Temporary bypass to force trading for testing"""
    return {
        "confidence": 75.0,
        "direction": "BUY", 
        "signals_agreeing": 3,
        "bypass_active": True
    }
'''
        
        with open("emergency_bypass.py", "w") as f:
            f.write(bypass_code)
            
        fixes_applied.append("✅ Created emergency trading bypass")
        
    except Exception as e:
        print(f"❌ Fix 3 failed: {e}")
    
    # Fix 4: Update signal aggregator to be less strict
    try:
        # Find and update signal aggregation logic
        import glob
        
        signal_files = glob.glob("src/core/*signal*.py") + glob.glob("src/core/*fusion*.py")
        
        for signal_file in signal_files:
            try:
                with open(signal_file, "r") as f:
                    content = f.read()
                
                # Reduce minimum confidence requirements
                updated = content.replace("confidence >= 0.6", "confidence >= 0.5")  # 60% → 50%
                updated = updated.replace("confidence >= 60", "confidence >= 50")
                updated = updated.replace("min_confidence = 0.6", "min_confidence = 0.5")
                
                if updated != content:
                    with open(signal_file + ".backup", "w") as f:
                        f.write(content)
                    
                    with open(signal_file, "w") as f:
                        f.write(updated)
                    
                    fixes_applied.append(f"✅ Updated {signal_file} - reduced confidence requirements")
                    
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"❌ Fix 4 failed: {e}")
    
    # Fix 5: Disable Kelly Criterion temporarily
    try:
        kelly_files = ["src/core/kelly_position_sizer.py", "src/core/kelly_criterion_optimizer.py"]
        
        for kelly_file in kelly_files:
            try:
                with open(kelly_file, "r") as f:
                    content = f.read()
                
                # Add bypass for insufficient trades
                bypass_code = '''
    # HOTFIX: Bypass Kelly when no historical trades
    if historical_trades < 1:
        return {
            "position_size_pct": 0.15,  # Use 15% default
            "kelly_score": 0.15,
            "bypass_reason": "insufficient_historical_data",
            "recommended": 0.15
        }
'''
                
                # Insert bypass at the start of calculation methods
                updated = content.replace(
                    "def calculate_kelly_position", 
                    "def calculate_kelly_position" + bypass_code.replace("def calculate_kelly_position", "")
                )
                
                if updated != content:
                    with open(kelly_file + ".backup", "w") as f:
                        f.write(content)
                    
                    with open(kelly_file, "w") as f:
                        f.write(updated)
                    
                    fixes_applied.append(f"✅ Added Kelly Criterion bypass for insufficient data")
                    
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"❌ Fix 5 failed: {e}")
    
    print("\\n🎯 HOTFIX SUMMARY:")
    for fix in fixes_applied:
        print(f"  {fix}")
    
    print(f"\\n✅ Applied {len(fixes_applied)} critical fixes")
    print("\\n🚨 NEXT STEPS:")
    print("1. Restart trading service: sudo systemctl restart rtx-trading")
    print("2. Monitor logs: journalctl -u rtx-trading -f")
    print("3. Trades should start executing within 15 minutes")
    print("4. Remove emergency bypass after confirming trades work")
    
    return len(fixes_applied)

if __name__ == "__main__":
    fixes = apply_trading_hotfix()
    print(f"\\n🎯 Hotfix complete: {fixes} fixes applied")
'''

# Create hotfix script
with open("trading_hotfix.py", "w") as f:
    f.write(hotfix_script)

print("✅ Created trading_hotfix.py")
print("\\nDeploy with:")
print("scp trading_hotfix.py root@64.226.96.90:/opt/rtx-trading/")
print("ssh root@64.226.96.90 'cd /opt/rtx-trading && rtx-env/bin/python trading_hotfix.py'")
#!/usr/bin/env python3
"""
Direct Balance Fix - Set correct final balances
"""
import sqlite3
import os

def direct_balance_fix():
    """Directly set final balances by adding adjustment entries"""
    
    target_balances = {
        "conservative": 890.50,
        "moderate": 720.75,
        "aggressive": 582.30
    }
    
    for strategy, target_balance in target_balances.items():
        db_path = f"data/options_performance_{strategy}.db"
        
        if not os.path.exists(db_path):
            print(f"❌ {strategy}: Database not found")
            continue
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current latest balance
        cursor.execute("SELECT balance_after FROM account_history ORDER BY rowid DESC LIMIT 1")
        result = cursor.fetchone()
        current_balance = result[0] if result else 1000.0
        
        print(f"📊 {strategy.title()}: Current ${current_balance:.2f} → Target ${target_balance:.2f}")
        
        # Add balance adjustment entry
        adjustment = target_balance - current_balance
        cursor.execute("""
        INSERT INTO account_history (action, trade_id, amount, balance_before, balance_after, description)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "BALANCE_ADJUSTMENT", 
            f"FIX_{strategy.upper()}", 
            adjustment, 
            current_balance, 
            target_balance, 
            f"Final balance correction to ${target_balance:.2f}"
        ))
        
        conn.commit()
        
        # Verify the fix
        cursor.execute("SELECT balance_after FROM account_history ORDER BY rowid DESC LIMIT 1")
        final_balance = cursor.fetchone()[0]
        
        conn.close()
        
        if abs(final_balance - target_balance) < 0.01:
            print(f"✅ {strategy.title()}: Fixed to ${final_balance:.2f}")
        else:
            print(f"❌ {strategy.title()}: Fix failed - got ${final_balance:.2f}")
    
    print("\n🎯 Direct balance fix complete!")

if __name__ == "__main__":
    direct_balance_fix()
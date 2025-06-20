#!/usr/bin/env python3
"""
Fix NULL balance values in account_history tables
"""
import sqlite3

def fix_null_balances():
    """Fix NULL balance values in all strategy databases"""
    
    strategy_balances = {
        "conservative": 890.50,
        "moderate": 720.75, 
        "aggressive": 582.30
    }
    
    for strategy, final_balance in strategy_balances.items():
        db_path = f"data/options_performance_{strategy}.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"=== Fixing {strategy.title()} ===")
        
        # Get all account history entries
        cursor.execute("SELECT history_id, action, amount, description FROM account_history ORDER BY timestamp")
        entries = cursor.fetchall()
        
        # Start with $1000 and calculate balances
        balance = 1000.0
        
        for history_id, action, amount, description in entries:
            if action == "INITIAL":
                balance_before = 0
                balance_after = 1000.0
            else:
                balance_before = balance
                if amount:
                    balance += amount
                balance_after = balance
                
            # Update the entry with correct balances
            cursor.execute("""
            UPDATE account_history 
            SET balance_before = ?, balance_after = ? 
            WHERE history_id = ?
            """, (balance_before, balance_after, history_id))
            
            print(f"  {action}: ${balance_before:.2f} → ${balance_after:.2f}")
        
        # Adjust final balance to match target
        cursor.execute("SELECT MAX(history_id) FROM account_history")
        last_id = cursor.fetchone()[0]
        
        if abs(balance - final_balance) > 1.0:
            # Add adjustment entry
            adjustment = final_balance - balance
            cursor.execute("""
            INSERT INTO account_history (action, trade_id, amount, balance_before, balance_after, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """, ("BALANCE_ADJUSTMENT", "FINAL_FIX", adjustment, balance, final_balance,
                  f"Final balance adjustment to ${final_balance:.2f}"))
            print(f"  ADJUSTMENT: ${balance:.2f} → ${final_balance:.2f}")
        
        conn.commit()
        conn.close()
        print(f"✅ {strategy.title()} fixed to ${final_balance:.2f}")
        print()

if __name__ == "__main__":
    fix_null_balances()
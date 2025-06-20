#!/usr/bin/env python3
import sys
import os
sys.path.append('/opt/rtx-trading')

# Suppress logging
import logging
logging.disable(logging.CRITICAL)
os.environ["LOGURU_LEVEL"] = "CRITICAL"

# Simple direct database query
import sqlite3

print("📊 **Account Status:**")
print()

strategies = ["conservative", "moderate", "aggressive"]
emojis = {"conservative": "🥇", "moderate": "🥈", "aggressive": "🥉"}

total_positions = 0
for strategy in strategies:
    try:
        db_path = f"/opt/rtx-trading/data/options_performance_{strategy}.db"
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get balance
            cursor.execute("SELECT balance_after FROM account_history ORDER BY timestamp DESC LIMIT 1")
            balance_row = cursor.fetchone()
            balance = balance_row[0] if balance_row else 1000.0
            
            # Count positions
            cursor.execute("SELECT COUNT(*) FROM options_predictions WHERE status = 'OPEN'")
            positions = cursor.fetchone()[0]
            total_positions += positions
            
            emoji = emojis.get(strategy, "📊")
            print(f"{emoji} **{strategy.title()}**: ${balance:.2f}")
            print(f"   📈 Open Positions: {positions}")
            
            if positions > 0:
                cursor.execute("SELECT contract_symbol, entry_price FROM options_predictions WHERE status = 'OPEN' LIMIT 2")
                for row in cursor.fetchall():
                    print(f"      • {row[0]} @ ${row[1]:.2f}")
            
            if balance < 300 and positions == 0:
                print(f"   ⚠️ Ready for reset!")
            
            conn.close()
        else:
            print(f"{strategy}: No database found")
        print()
        
    except Exception as e:
        print(f"{strategy}: Error - {str(e)}")

print(f"💰 **Total Positions**: {total_positions}")
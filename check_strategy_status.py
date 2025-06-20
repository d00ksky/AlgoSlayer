#!/usr/bin/env python3
import sys
import os
sys.path.append('/opt/rtx-trading' if os.path.exists('/opt/rtx-trading') else '.')

from src.core.options_paper_trader import OptionsPaperTrader

print("📊 Strategy Status After Reset:")
print()

strategies = ["conservative", "moderate", "aggressive"]
emojis = ["🥇", "🥈", "🥉"]

for i, strategy in enumerate(strategies):
    try:
        trader = OptionsPaperTrader(db_suffix=f"_{strategy}")
        balance = trader.account_balance
        positions = getattr(trader, "open_positions", {})
        pos_count = len(positions)
        
        print(f"{emojis[i]} {strategy.title()}: ${balance:.2f}, {pos_count} positions")
        
        if pos_count > 0:
            for contract, data in list(positions.items())[:2]:
                entry_price = data.get('entry_price', 0)
                quantity = data.get('quantity', 1)
                print(f"   • {contract} x{quantity} @ ${entry_price:.2f}")
        print()
        
    except Exception as e:
        print(f"{emojis[i]} {strategy}: Error - {e}")
        print()

print("✅ Database separation test complete!")
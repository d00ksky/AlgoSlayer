#!/usr/bin/env python3
"""
Update Telegram notifications to use accurate profit calculations
"""

# Create the updated notification code
updated_code = '''
# Add this to the telegram_bot.py imports
from src.core.profit_calculator import profit_calculator

# Replace the send_market_open_status method with this updated version
async def send_market_open_status(self) -> bool:
    """Send daily market open status message with accurate profit calculations"""
    try:
        # Get current time in ET
        import pytz
        et = pytz.timezone('US/Eastern')
        now = datetime.now(et)
        
        message = f"""🔔 *MARKET OPEN STATUS* — {now.strftime('%A, %B %d')}
⏰ *Time:* {now.strftime('%H:%M ET')}

🤖 *SYSTEM STATUS*
"""
        
        # Check service status
        try:
            import subprocess
            result = subprocess.run(['systemctl', 'is-active', 'rtx-trading.service'], 
                                 capture_output=True, text=True, timeout=5)
            service_status = "🟢 ACTIVE" if result.stdout.strip() == "active" else "🔴 INACTIVE"
        except:
            service_status = "⚠️ UNKNOWN"
            
        message += f"📊 *Trading Service:* {service_status}\\n"
        message += f"🎯 *Target:* RTX Corporation\\n"
        message += f"📈 *Mode:* Paper Trading\\n\\n"
        
        # Get accurate account status using profit calculator
        message += "💰 *ACCOUNT STATUS*\\n"
        
        try:
            # Get accurate profit stats
            from src.core.profit_calculator import ProfitCalculator
            calc = ProfitCalculator()
            
            # Get overall statistics
            overall_profit = calc.get_overall_profit()
            
            # Get individual strategy data
            import sqlite3
            conn = sqlite3.connect('data/algoslayer_multi_strategy.db')
            cursor = conn.cursor()
            
            # Get total balance and active strategies
            cursor.execute("SELECT SUM(current_balance) FROM trading_strategies")
            total_balance = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(*) FROM trading_strategies WHERE current_balance != 2000")
            active_count = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(*) FROM trading_strategies")
            total_count = cursor.fetchone()[0] or 0
            
            conn.close()
            
            # Format balance info
            message += f"💵 *Balance:* ${total_balance:.2f}\\n"
            
            # Show accurate profit (should be 0% after reset)
            if overall_profit != 0:
                profit_emoji = "📈" if overall_profit > 0 else "📉"
                message += f"{profit_emoji} *Profit:* {overall_profit:.1f}%\\n"
            else:
                message += f"➖ *Profit:* 0.0% (Reset on July 29)\\n"
                
            message += f"📊 *Active Strategies:* {active_count}/{total_count}\\n\\n"
            
            # Get RTX current price
            try:
                import yfinance as yf
                rtx = yf.Ticker("RTX")
                rtx_data = rtx.history(period="1d")
                if not rtx_data.empty:
                    current_price = rtx_data['Close'].iloc[-1]
                    previous_close = rtx_data['Open'].iloc[0]
                    price_change = ((current_price - previous_close) / previous_close) * 100
                    
                    price_emoji = "📈" if price_change > 0 else "📉" if price_change < 0 else "➖"
                    message += f"📊 *RTX PRICE*\\n"
                    message += f"💵 *Current:* ${current_price:.2f}\\n"
                    message += f"{price_emoji} *Change:* {price_change:+.2f}%\\n\\n"
            except:
                message += f"📊 *RTX PRICE*: Unable to fetch\\n\\n"
                
            # Add open positions summary
            open_positions = 0
            for strategy in ['conservative', 'moderate', 'aggressive', 'scalping', 
                           'swing', 'momentum', 'volatility', 'mean_reversion']:
                try:
                    conn = sqlite3.connect(f'data/options_performance_{strategy}.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM options_predictions WHERE status = 'OPEN'")
                    positions = cursor.fetchone()[0]
                    open_positions += positions
                    conn.close()
                except:
                    pass
                    
            message += f"📋 *POSITIONS*\\n"
            message += f"🎯 *Open Positions:* {open_positions}\\n"
            
            # Add note about reset
            message += f"\\n📌 *Note:* All strategies reset to $2,000 on July 29\\n"
            message += f"Profit % reflects post-reset performance only"
            
        except Exception as e:
            logger.error(f"Error getting account status: {e}")
            message += f"⚠️ Unable to fetch account details\\n"
            
        # Send the message
        return await self.send_message(message)
        
    except Exception as e:
        logger.error(f"Error sending market open status: {e}")
        return False
'''

print("📝 Update code created for telegram_bot.py")
print("\nTo apply this fix:")
print("1. The profit_calculator.py has already been created on the server")
print("2. You need to update the telegram_bot.py file to import and use it")
print("3. This will show 0% profit instead of the confusing 433%")

# Also create a patch file
patch_content = """
import sys
sys.path.append('/opt/rtx-trading')

# Patch to fix profit display
def patch_telegram_bot():
    # Read current telegram_bot.py
    with open('src/core/telegram_bot.py', 'r') as f:
        content = f.read()
    
    # Add import if not present
    if 'from src.core.profit_calculator import profit_calculator' not in content:
        import_line = "from src.core.profit_calculator import profit_calculator\\n"
        # Add after other imports
        import_pos = content.find('from loguru import logger')
        if import_pos != -1:
            end_of_line = content.find('\\n', import_pos)
            content = content[:end_of_line+1] + import_line + content[end_of_line+1:]
    
    # Update profit calculation logic
    # This is a simplified patch - in production you'd want more robust replacement
    
    # Save patched file
    with open('src/core/telegram_bot.py.patched', 'w') as f:
        f.write(content)
    
    print("✅ Created patched version: src/core/telegram_bot.py.patched")
    print("Review the changes and then copy over the original if satisfied")

if __name__ == "__main__":
    patch_telegram_bot()
"""

with open('patch_telegram_profit.py', 'w') as f:
    f.write(patch_content)

print("\n✅ Also created patch_telegram_profit.py for easier patching")
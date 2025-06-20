#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append('/opt/rtx-trading')
from src.core.telegram_bot import telegram_bot
import subprocess
import json
from datetime import datetime

class TelegramCommands:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
    async def handle_command(self, command):
        """Handle different commands"""
        command = command.lower().strip()
        
        if command == '/logs':
            return await self.get_logs()
        elif command == '/status':
            return await self.get_status()
        elif command == '/restart':
            return await self.restart_service()
        elif command == '/memory':
            return await self.get_memory()
        elif command == '/positions':
            return await self.get_positions()
        elif command == '/help':
            return await self.get_help()
        else:
            return "❓ Unknown command. Send /help for available commands."
    
    async def get_logs(self):
        """Get last 5 log entries"""
        try:
            result = subprocess.run([
                'journalctl', '-u', 'multi-strategy-trading', '--no-pager', '-n', '3'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logs = result.stdout.strip()
                if logs:
                    lines = logs.split('\n')[-3:]
                    formatted = "📋 Recent Logs:\n\n"
                    for line in lines:
                        if 'multi-strategy-trading' in line:
                            # Simple extraction
                            parts = line.split()
                            if len(parts) >= 3:
                                time_part = parts[2]
                                # Get message after the process ID
                                msg_start = line.find(': ')
                                if msg_start > 0:
                                    message = line[msg_start + 2:msg_start + 50]  # First 50 chars
                                    formatted += f"{time_part}: {message}\n"
                    
                    return formatted if len(formatted) > 20 else "📋 No recent activity"
                else:
                    return "📋 No log entries found"
            else:
                return "❌ Error getting logs"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def get_status(self):
        """Get service status"""
        try:
            # Check service status
            result = subprocess.run(['systemctl', 'is-active', 'multi-strategy-trading'], 
                                  capture_output=True, text=True)
            
            service_status = result.stdout.strip()
            status_emoji = "✅" if service_status == "active" else "❌"
            
            # Get more details
            detail_result = subprocess.run(['systemctl', 'status', 'multi-strategy-trading', '--no-pager'], 
                                         capture_output=True, text=True)
            
            lines = detail_result.stdout.split('\n')
            memory_info = ""
            for line in lines:
                if 'Memory:' in line:
                    memory_info = line.strip()
                    break
            
            return f"""📊 **Service Status:**
{status_emoji} Status: {service_status}
{memory_info}

⏰ **Time:** {datetime.now().strftime('%H:%M:%S UTC')}"""
            
        except Exception as e:
            return f"❌ **Error getting status:** {str(e)}"
    
    async def restart_service(self):
        """Restart the trading service"""
        try:
            result = subprocess.run(['systemctl', 'restart', 'multi-strategy-trading'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                await asyncio.sleep(3)  # Wait for restart
                status_result = subprocess.run(['systemctl', 'is-active', 'multi-strategy-trading'], 
                                             capture_output=True, text=True)
                status = status_result.stdout.strip()
                
                if status == 'active':
                    return "🔄 **Service restarted successfully!** ✅"
                else:
                    return f"⚠️ **Service restarted but status is:** {status}"
            else:
                return f"❌ **Restart failed:** {result.stderr}"
        except Exception as e:
            return f"❌ **Error restarting:** {str(e)}"
    
    async def get_memory(self):
        """Get memory usage"""
        try:
            result = subprocess.run(['free', '-h'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            mem_line = lines[1].split()
            
            return f"""💾 **Memory Usage:**
📊 RAM: {mem_line[2]} used / {mem_line[1]} total
💚 Available: {mem_line[6]}

⏰ {datetime.now().strftime('%H:%M:%S UTC')}"""
        except Exception as e:
            return f"❌ **Error getting memory:** {str(e)}"
    
    async def get_positions(self):
        """Get account positions and strategy status"""
        try:
            result = subprocess.run([
                '/opt/rtx-trading/rtx-env/bin/python', '-c',
                '''
import sys
import os
sys.path.append("/opt/rtx-trading")

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
'''
            ], capture_output=True, text=True, timeout=10, env={**os.environ, 'PYTHONWARNINGS': 'ignore'})
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            else:
                return f"❌ Error: {result.stderr or 'No data'}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    async def get_help(self):
        """Show available commands"""
        return """🤖 **Available Commands:**

/status - Service status & health
/logs - Recent log entries  
/positions - Account balances & trades
/memory - Memory usage
/restart - Restart trading service
/help - Show this help

💡 **Usage:** Just send any command as a message"""

# Main execution for testing
async def main():
    if len(sys.argv) > 1:
        cmd_handler = TelegramCommands()
        command = ' '.join(sys.argv[1:])
        response = await cmd_handler.handle_command(command)
        await telegram_bot.send_message(response)
        print(f"Command '{command}' executed, response sent to Telegram")
    else:
        print("Usage: python telegram_commands.py <command>")
        print("Example: python telegram_commands.py /logs")

if __name__ == '__main__':
    asyncio.run(main())
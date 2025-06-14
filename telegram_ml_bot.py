#!/usr/bin/env python3
"""
Telegram ML Bot - Two-way communication for ML system control
Allows remote monitoring and control of local ML training while traveling
"""
import os
import sys
import json
import time
import requests
import subprocess
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

class TelegramMLBot:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.cloud_server = "root@64.226.96.90"
        self.bot_token = None
        self.chat_id = None
        self.last_update_id = 0
        self.authorized_users = set()
        
        # Load credentials
        self._load_credentials()
    
    def _load_credentials(self):
        """Load bot credentials from cloud server"""
        try:
            # Get bot token
            result = subprocess.run([
                'ssh', '-o', 'ConnectTimeout=10', self.cloud_server,
                'grep TELEGRAM_BOT_TOKEN /opt/rtx-trading/.env | cut -d= -f2'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                self.bot_token = result.stdout.strip()
            
            # Get chat ID
            result = subprocess.run([
                'ssh', '-o', 'ConnectTimeout=10', self.cloud_server,
                'grep TELEGRAM_CHAT_ID /opt/rtx-trading/.env | cut -d= -f2'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                self.chat_id = result.stdout.strip()
                self.authorized_users.add(self.chat_id)
            
        except Exception as e:
            print(f"Error loading credentials: {e}")
    
    def send_message(self, message, silent=False):
        """Send message to Telegram"""
        if not self.bot_token or not self.chat_id:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_notification': silent
            }
            
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def get_updates(self):
        """Get new messages from Telegram"""
        if not self.bot_token:
            return []
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            params = {'offset': self.last_update_id + 1, 'timeout': 10}
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                updates = data.get('result', [])
                
                if updates:
                    self.last_update_id = updates[-1]['update_id']
                
                return updates
            
        except Exception as e:
            print(f"Error getting updates: {e}")
        
        return []
    
    def is_authorized(self, user_id):
        """Check if user is authorized"""
        return str(user_id) in self.authorized_users
    
    def handle_command(self, command, user_id):
        """Handle incoming command"""
        if not self.is_authorized(user_id):
            return "❌ Unauthorized user"
        
        command = command.lower().strip()
        
        if command in ['/start', '/help']:
            return self._help_command()
        elif command in ['/status', '/st']:
            return self._status_command()
        elif command in ['/train', '/tr']:
            return self._train_command()
        elif command in ['/cloud', '/cl']:
            return self._cloud_status_command()
        elif command in ['/logs', '/lg']:
            return self._logs_command()
        elif command in ['/disable', '/dis']:
            return self._disable_command()
        elif command in ['/enable', '/en']:
            return self._enable_command()
        elif command in ['/stats', '/data']:
            return self._stats_command()
        elif command in ['/restart', '/rs']:
            return self._restart_cloud_command()
        else:
            return f"❓ Unknown command: {command}\nSend /help for available commands"
    
    def _help_command(self):
        """Show help message"""
        return """🤖 **AlgoSlayer ML Bot Commands**

📊 **Status & Monitoring:**
/status - Local ML system status
/cloud - Cloud server status  
/logs - Recent training logs
/stats - Trading statistics

⚙️ **Control:**
/train - Force ML training now
/enable - Enable auto-training
/disable - Disable auto-training
/restart - Restart cloud service

📱 **Shortcuts:**
/st = status, /tr = train, /cl = cloud
/lg = logs, /en = enable, /dis = disable

💡 **Tips:**
• Commands work from anywhere with internet
• Perfect for monitoring while traveling
• Get instant notifications when training completes"""
    
    def _status_command(self):
        """Get ML system status"""
        try:
            # Check if auto-training is enabled
            disable_file = self.script_dir / "DISABLE_AUTO_ML"
            auto_status = "❌ DISABLED" if disable_file.exists() else "✅ ENABLED"
            
            # Check last training time
            last_training_file = self.script_dir / "ml_training_data" / "last_training_time"
            if last_training_file.exists():
                last_training = int(last_training_file.read_text().strip())
                hours_ago = (time.time() - last_training) / 3600
                last_status = f"⏰ {hours_ago:.1f} hours ago"
            else:
                last_status = "⚠️ NEVER"
            
            # Check connectivity
            try:
                subprocess.run(['ping', '-c', '1', '-W', '3', 'google.com'], 
                             capture_output=True, timeout=5)
                internet = "🌐 CONNECTED"
            except:
                internet = "🌐 DISCONNECTED"
            
            # Check cloud server
            try:
                subprocess.run(['ssh', '-o', 'ConnectTimeout=5', self.cloud_server, 'echo test'], 
                             capture_output=True, timeout=10)
                cloud = "☁️ REACHABLE"
            except:
                cloud = "☁️ UNREACHABLE"
            
            # System uptime
            uptime_hours = int(subprocess.run(['awk', '{print int($1/3600)}', '/proc/uptime'], 
                                            capture_output=True, text=True).stdout.strip())
            
            return f"""📊 **Local ML System Status**

🤖 Auto-training: {auto_status}
{last_status}
{internet}
{cloud}
💻 Laptop uptime: {uptime_hours}h

Type /cloud for cloud server details
Type /train to force training now"""
            
        except Exception as e:
            return f"❌ Error getting status: {e}"
    
    def _train_command(self):
        """Force ML training"""
        try:
            self.send_message("🚀 Starting ML training...", silent=True)
            
            # Run training script
            script_path = self.script_dir / "run_smart_ml_training.sh"
            result = subprocess.run([str(script_path)], 
                                  capture_output=True, text=True, timeout=1800)
            
            if result.returncode == 0:
                # Get training results
                log_file = self.script_dir / "logs" / f"ml_training_{datetime.now().strftime('%Y%m%d')}.log"
                if log_file.exists():
                    recent_logs = log_file.read_text().split('\n')[-5:]
                    logs_text = '\n'.join(recent_logs)
                else:
                    logs_text = "No log file found"
                
                return f"✅ **ML Training Completed**\n\n```\n{logs_text}\n```"
            else:
                return f"❌ **ML Training Failed**\n\nExit code: {result.returncode}\n```\n{result.stderr}\n```"
                
        except subprocess.TimeoutExpired:
            return "⏰ ML training timed out (30min limit)"
        except Exception as e:
            return f"❌ Error running training: {e}"
    
    def _cloud_status_command(self):
        """Get cloud server status"""
        try:
            # Get cloud stats using Python instead of sqlite3 command
            commands = [
                "systemctl is-active rtx-trading",
                "cd /opt/rtx-trading && /opt/rtx-trading/rtx-env/bin/python -c \"import sqlite3; conn=sqlite3.connect('data/signal_performance.db'); print(conn.execute('SELECT COUNT(*) FROM predictions').fetchone()[0]); conn.close()\"",
                "cd /opt/rtx-trading && /opt/rtx-trading/rtx-env/bin/python -c \"import sqlite3; conn=sqlite3.connect('data/signal_performance.db'); print(conn.execute('SELECT COUNT(*) FROM predictions WHERE datetime(timestamp) > datetime(\\\"now\\\", \\\"-24 hours\\\")').fetchone()[0]); conn.close()\"",
                "cd /opt/rtx-trading && /opt/rtx-trading/rtx-env/bin/python -c \"import sqlite3; conn=sqlite3.connect('data/options_performance.db'); print(conn.execute('SELECT COUNT(*) FROM options_predictions').fetchone()[0]); conn.close()\" 2>/dev/null || echo '0'",
                "uptime"
            ]
            
            results = []
            for cmd in commands:
                result = subprocess.run(['ssh', '-o', 'ConnectTimeout=10', self.cloud_server, cmd], 
                                      capture_output=True, text=True, timeout=15)
                results.append(result.stdout.strip() if result.returncode == 0 else 'error')
            
            service_status = "✅ ACTIVE" if results[0] == "active" else f"❌ {results[0]}"
            total_predictions = results[1]
            recent_predictions = results[2] 
            options_predictions = results[3]
            uptime = results[4]
            
            return f"""☁️ **Cloud Server Status**

🚀 RTX Trading Service: {service_status}
📊 Total predictions: {total_predictions}
📈 Last 24h: {recent_predictions} predictions
🎯 Options predictions: {options_predictions}
⏰ Server uptime: {uptime}

Type /restart to restart trading service"""
            
        except Exception as e:
            return f"❌ Error getting cloud status: {e}"
    
    def _logs_command(self):
        """Get recent training logs"""
        try:
            log_file = self.script_dir / "logs" / f"ml_training_{datetime.now().strftime('%Y%m%d')}.log"
            
            if log_file.exists():
                recent_logs = log_file.read_text().split('\n')[-10:]
                logs_text = '\n'.join(recent_logs)
                return f"📋 **Recent Training Logs**\n\n```\n{logs_text}\n```"
            else:
                return "📋 No training logs found for today"
                
        except Exception as e:
            return f"❌ Error reading logs: {e}"
    
    def _disable_command(self):
        """Disable auto-training"""
        try:
            disable_file = self.script_dir / "DISABLE_AUTO_ML"
            disable_file.touch()
            return "🛑 **Auto-training DISABLED**\n\nUse /enable to re-enable"
        except Exception as e:
            return f"❌ Error disabling: {e}"
    
    def _enable_command(self):
        """Enable auto-training"""
        try:
            disable_file = self.script_dir / "DISABLE_AUTO_ML"
            if disable_file.exists():
                disable_file.unlink()
            return "✅ **Auto-training ENABLED**\n\nUse /disable to disable"
        except Exception as e:
            return f"❌ Error enabling: {e}"
    
    def _stats_command(self):
        """Get trading statistics"""
        try:
            # Get stats from cloud
            result = subprocess.run([
                'ssh', '-o', 'ConnectTimeout=10', self.cloud_server,
                'cd /opt/rtx-trading && python3 -c "import sqlite3; conn=sqlite3.connect(\\"data/signal_performance.db\\"); cursor=conn.cursor(); cursor.execute(\\"SELECT direction, confidence, timestamp FROM predictions ORDER BY timestamp DESC LIMIT 5\\"); print(cursor.fetchall())"'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                return f"📊 **Recent Predictions**\n\n```\n{result.stdout}\n```\n\nType /cloud for more details"
            else:
                return "❌ Error getting statistics from cloud"
                
        except Exception as e:
            return f"❌ Error getting stats: {e}"
    
    def _restart_cloud_command(self):
        """Restart cloud trading service"""
        try:
            result = subprocess.run([
                'ssh', '-o', 'ConnectTimeout=10', self.cloud_server,
                'systemctl restart rtx-trading && sleep 3 && systemctl is-active rtx-trading'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and 'active' in result.stdout:
                return "✅ **Cloud service restarted successfully**\n\nService is now active"
            else:
                return f"❌ **Restart failed**\n\n```\n{result.stderr}\n```"
                
        except Exception as e:
            return f"❌ Error restarting service: {e}"
    
    def run_daemon(self):
        """Run bot as daemon, listening for commands"""
        print("🤖 Starting Telegram ML Bot daemon...")
        
        if not self.bot_token:
            print("❌ No bot token found")
            return
        
        # Send startup notification
        self.send_message("🚀 **ML Bot Online**\n\nLocal ML system is now controllable via Telegram\nSend /help for commands", silent=True)
        
        while True:
            try:
                updates = self.get_updates()
                
                for update in updates:
                    if 'message' in update:
                        message = update['message']
                        
                        if 'text' in message:
                            text = message['text']
                            user_id = message['from']['id']
                            
                            if text.startswith('/'):
                                response = self.handle_command(text, user_id)
                                self.send_message(response)
                
                time.sleep(2)  # Poll every 2 seconds
                
            except KeyboardInterrupt:
                self.send_message("🛑 **ML Bot Offline**\n\nLocal ML bot daemon stopped", silent=True)
                break
            except Exception as e:
                print(f"Error in daemon loop: {e}")
                time.sleep(10)  # Wait longer on error

if __name__ == "__main__":
    bot = TelegramMLBot()
    
    if len(sys.argv) > 1 and sys.argv[1] == "daemon":
        bot.run_daemon()
    elif len(sys.argv) > 2:
        # Send single message
        message = sys.argv[1]
        silent = len(sys.argv) > 2 and sys.argv[2].lower() == 'true'
        bot.send_message(message, silent)
    else:
        print("Usage:")
        print("  python telegram_ml_bot.py daemon          # Run interactive bot")
        print("  python telegram_ml_bot.py 'message'       # Send single message")
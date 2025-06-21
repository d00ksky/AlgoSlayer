#!/usr/bin/env python3
"""
Telegram Bot Debug Script
Comprehensive debugging tool for the RTX Trading System Telegram bot
"""

import os
import sys
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def run_command(command):
    """Run shell command and return output"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

async def test_telegram_connection():
    """Test direct Telegram API connection"""
    try:
        # Import the bot
        sys.path.append('/opt/rtx-trading')
        from src.core.telegram_bot import telegram_bot
        
        print("📱 Testing Telegram bot connection...")
        
        # Check if bot is enabled
        if not telegram_bot.enabled:
            print("❌ Telegram bot is not enabled!")
            print(f"   Bot Token: {'SET' if telegram_bot.bot_token else 'MISSING'}")
            print(f"   Chat ID: {'SET' if telegram_bot.chat_id else 'MISSING'}")
            return False
        
        # Test connection
        success = await telegram_bot.test_connection()
        if success:
            print("✅ Telegram connection successful!")
        else:
            print("❌ Telegram connection failed!")
            
        return success
        
    except Exception as e:
        print(f"❌ Error testing Telegram connection: {e}")
        return False

async def test_telegram_commands():
    """Test specific Telegram commands"""
    try:
        sys.path.append('/opt/rtx-trading')
        from src.core.telegram_bot import telegram_bot
        
        print("🤖 Testing Telegram commands...")
        
        # Test each command
        commands_to_test = [
            "/help",
            "/status", 
            "/dashboard",
            "/thresholds",
            "/positions",
            "/explain",
            "/terms",
            "/signals"
        ]
        
        for command in commands_to_test:
            try:
                print(f"   Testing {command}...")
                success = await telegram_bot.handle_command(command)
                status = "✅" if success else "❌"
                print(f"   {status} {command}")
            except Exception as e:
                print(f"   ❌ {command}: {e}")
                
    except Exception as e:
        print(f"❌ Error testing commands: {e}")

def check_system_status():
    """Check overall system status"""
    print_header("SYSTEM STATUS CHECK")
    
    # Check service status
    stdout, stderr, code = run_command("systemctl status rtx-trading")
    if code == 0:
        print("✅ RTX Trading service is running")
        # Extract key info
        for line in stdout.split('\n'):
            if 'Active:' in line or 'Main PID:' in line or 'Memory:' in line:
                print(f"   {line.strip()}")
    else:
        print("❌ RTX Trading service is not running")
        print(f"   Error: {stderr}")
    
    # Check process
    stdout, stderr, code = run_command("pgrep -f 'run_server.py'")
    if code == 0:
        print("✅ run_server.py process found")
        print(f"   PID: {stdout.strip()}")
    else:
        print("❌ run_server.py process not found")
    
    # Check Python process
    stdout, stderr, code = run_command("ps aux | grep python | grep rtx")
    if stdout:
        print("✅ Python RTX processes:")
        for line in stdout.split('\n'):
            if 'rtx' in line.lower() and 'grep' not in line:
                print(f"   {line.strip()}")
    else:
        print("❌ No Python RTX processes found")

def check_environment():
    """Check environment configuration"""
    print_header("ENVIRONMENT CHECK")
    
    # Check if we're in the right directory
    current_dir = os.getcwd()
    print(f"📁 Current directory: {current_dir}")
    
    # Check if we're in the project directory
    project_files = ['src/core/telegram_bot.py', 'run_server.py', 'config/trading_config.py']
    missing_files = []
    
    for file in project_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            missing_files.append(file)
    
    if missing_files:
        print(f"⚠️  Missing files suggest we're not in the project directory")
        print(f"   Try running from /opt/rtx-trading/")
    
    # Check Python path
    print(f"🐍 Python executable: {sys.executable}")
    print(f"🐍 Python version: {sys.version}")
    
    # Check environment variables
    env_vars = ['TRADING_ENABLED', 'PAPER_TRADING', 'USE_OPTIONS_SYSTEM', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
    print("\n🔧 Environment Variables:")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Hide sensitive values
            if 'TOKEN' in var or 'KEY' in var:
                display_value = f"***{value[-4:]}" if len(value) > 4 else "***"
            else:
                display_value = value
            print(f"   ✅ {var} = {display_value}")
        else:
            print(f"   ❌ {var} = NOT SET")

def check_logs():
    """Check recent logs"""
    print_header("RECENT LOGS CHECK")
    
    # Get recent logs
    stdout, stderr, code = run_command("journalctl -u rtx-trading --no-pager -n 20")
    if code == 0:
        print("📋 Recent 20 log entries:")
        lines = stdout.split('\n')
        for line in lines[-15:]:  # Show last 15 lines
            if line.strip():
                print(f"   {line}")
    else:
        print(f"❌ Error getting logs: {stderr}")
    
    # Check for errors
    stdout, stderr, code = run_command("journalctl -u rtx-trading --no-pager -n 100 | grep -i error")
    if stdout:
        print("\n🚨 Recent errors found:")
        for line in stdout.split('\n')[:5]:  # Show first 5 errors
            if line.strip():
                print(f"   {line}")
    else:
        print("\n✅ No recent errors in logs")

def check_telegram_setup():
    """Check Telegram configuration"""
    print_header("TELEGRAM CONFIGURATION CHECK")
    
    # Check .env file
    env_file = '/opt/rtx-trading/.env'
    if os.path.exists(env_file):
        print(f"✅ .env file exists: {env_file}")
        try:
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            telegram_vars = []
            for line in lines:
                if 'TELEGRAM' in line and '=' in line:
                    var_name = line.split('=')[0].strip()
                    var_value = line.split('=', 1)[1].strip()
                    if var_value:
                        display_value = f"***{var_value[-4:]}" if len(var_value) > 4 else "***"
                        telegram_vars.append(f"   ✅ {var_name} = {display_value}")
                    else:
                        telegram_vars.append(f"   ❌ {var_name} = EMPTY")
            
            if telegram_vars:
                print("📱 Telegram variables in .env:")
                for var in telegram_vars:
                    print(var)
            else:
                print("❌ No Telegram variables found in .env")
                
        except Exception as e:
            print(f"❌ Error reading .env file: {e}")
    else:
        print(f"❌ .env file not found: {env_file}")
    
    # Check if bot files exist
    bot_file = '/opt/rtx-trading/src/core/telegram_bot.py'
    if os.path.exists(bot_file):
        print(f"✅ Telegram bot file exists: {bot_file}")
        
        # Check file size and modification time
        stat = os.stat(bot_file)
        size = stat.st_size
        mtime = datetime.fromtimestamp(stat.st_mtime)
        print(f"   📊 Size: {size} bytes")
        print(f"   📅 Last modified: {mtime}")
    else:
        print(f"❌ Telegram bot file missing: {bot_file}")

def check_imports():
    """Check if all required modules can be imported"""
    print_header("IMPORT CHECK")
    
    # Test critical imports
    imports_to_test = [
        'src.core.telegram_bot',
        'src.core.dashboard', 
        'src.core.dynamic_thresholds',
        'config.trading_config',
        'aiohttp',
        'asyncio',
        'sqlite3',
        'loguru'
    ]
    
    # Add project root to Python path
    sys.path.insert(0, '/opt/rtx-trading')
    
    for module in imports_to_test:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
        except Exception as e:
            print(f"⚠️  {module}: {e}")

async def main():
    """Run comprehensive debugging"""
    print_header("RTX TRADING TELEGRAM BOT DEBUG")
    print(f"🕐 Debug started at: {datetime.now()}")
    
    # Change to project directory if needed
    if not os.path.exists('src/core/telegram_bot.py'):
        if os.path.exists('/opt/rtx-trading/src/core/telegram_bot.py'):
            os.chdir('/opt/rtx-trading')
            print("📁 Changed to /opt/rtx-trading/")
        else:
            print("❌ Cannot find project directory!")
            return
    
    # Run all checks
    check_system_status()
    check_environment()
    check_telegram_setup()
    check_imports()
    check_logs()
    
    # Test Telegram functionality
    print_header("TELEGRAM FUNCTIONALITY TEST")
    await test_telegram_connection()
    await test_telegram_commands()
    
    print_header("DEBUG COMPLETE")
    print("🎯 Summary:")
    print("   1. Check system status above")
    print("   2. Verify Telegram credentials are set")
    print("   3. Ensure service is running")
    print("   4. Test command imports")
    print("   5. Check recent logs for errors")
    print(f"\n🕐 Debug completed at: {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Test Dashboard Command Specifically
Isolated test for the /dashboard command that's failing
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project to Python path
if os.path.exists('/opt/rtx-trading'):
    sys.path.insert(0, '/opt/rtx-trading')
    os.chdir('/opt/rtx-trading')
elif os.path.exists('src/core/telegram_bot.py'):
    sys.path.insert(0, '.')
else:
    print("❌ Cannot find project directory!")
    sys.exit(1)

async def test_dashboard_import():
    """Test importing dashboard module"""
    print("🧪 Testing dashboard import...")
    
    try:
        # Test direct import
        from src.core.dashboard import dashboard
        print("✅ Dashboard module imported successfully")
        return dashboard
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return None
    except Exception as e:
        print(f"❌ Other error: {e}")
        return None

async def test_dashboard_generation():
    """Test dashboard generation"""
    print("🧪 Testing dashboard generation...")
    
    dashboard = await test_dashboard_import()
    if not dashboard:
        return False
    
    try:
        dashboard_text = dashboard.generate_dashboard()
        print("✅ Dashboard generated successfully")
        print(f"📊 Dashboard length: {len(dashboard_text)} characters")
        
        # Show first few lines
        lines = dashboard_text.split('\n')[:10]
        print("📋 Dashboard preview:")
        for line in lines:
            print(f"   {line}")
        
        return True
    except Exception as e:
        print(f"❌ Dashboard generation error: {e}")
        return False

async def test_telegram_dashboard_method():
    """Test the Telegram bot's dashboard method"""
    print("🧪 Testing Telegram dashboard method...")
    
    try:
        from src.core.telegram_bot import telegram_bot
        
        # Check if bot is configured
        if not telegram_bot.enabled:
            print("⚠️  Telegram bot not enabled")
            print(f"   Bot token set: {'Yes' if telegram_bot.bot_token else 'No'}")
            print(f"   Chat ID set: {'Yes' if telegram_bot.chat_id else 'No'}")
        
        # Test the dashboard method directly (without sending)
        try:
            # Import dashboard here to mimic the bot's behavior
            from src.core.dashboard import dashboard
            dashboard_text = dashboard.generate_dashboard()
            
            # Check message length
            if len(dashboard_text) > 4000:
                dashboard_text = dashboard_text[:3900] + "\n\n... (Dashboard truncated for Telegram)"
            
            print("✅ Telegram dashboard method logic works")
            print(f"📊 Final message length: {len(dashboard_text)} characters")
            
            # Test the actual method (but don't send)
            print("🧪 Testing handle_command('/dashboard')...")
            
            # This will test the import logic in the method
            success = await telegram_bot.send_dashboard_message()
            if success:
                print("✅ send_dashboard_message() succeeded")
            else:
                print("❌ send_dashboard_message() failed")
            
            return True
            
        except Exception as e:
            print(f"❌ Dashboard method error: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Telegram bot import error: {e}")
        return False

async def test_command_handler():
    """Test the command handler specifically"""
    print("🧪 Testing command handler...")
    
    try:
        from src.core.telegram_bot import telegram_bot
        
        # Test handle_command method with /dashboard
        print("   Testing handle_command('/dashboard')...")
        success = await telegram_bot.handle_command('/dashboard')
        
        if success:
            print("✅ handle_command('/dashboard') succeeded")
        else:
            print("❌ handle_command('/dashboard') failed")
        
        # Test with other commands for comparison
        test_commands = ['/help', '/status', '/thresholds']
        for cmd in test_commands:
            print(f"   Testing handle_command('{cmd}')...")
            try:
                success = await telegram_bot.handle_command(cmd)
                status = "✅" if success else "❌"
                print(f"   {status} {cmd}")
            except Exception as e:
                print(f"   ❌ {cmd}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Command handler test error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("🔍 DASHBOARD COMMAND DEBUG TEST")
    print("=" * 50)
    
    # Test each component
    await test_dashboard_import()
    print()
    
    await test_dashboard_generation()
    print()
    
    await test_telegram_dashboard_method()
    print()
    
    await test_command_handler()
    
    print("\n" + "=" * 50)
    print("🎯 TEST COMPLETE")
    print("\nIf all tests pass but /dashboard still fails in Telegram:")
    print("1. Check server is actually running the updated code")
    print("2. Restart the rtx-trading service")
    print("3. Check logs: journalctl -u rtx-trading -f")
    print("4. Verify Telegram bot is processing messages")

if __name__ == "__main__":
    asyncio.run(main())
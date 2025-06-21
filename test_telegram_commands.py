#!/usr/bin/env python3
"""
Test Telegram Bot Commands
Tests all the enhanced telegram commands to ensure they work correctly
"""

import asyncio
import sys
from src.core.telegram_bot import telegram_bot

async def test_telegram_commands():
    """Test all telegram bot commands"""
    print("🧪 Testing Telegram Bot Commands")
    print("="*50)
    
    commands_to_test = [
        "/help",
        "/dashboard", 
        "/thresholds",
        "/positions",
        "/status",
        "/memory"
    ]
    
    for command in commands_to_test:
        print(f"\n🔍 Testing {command}...")
        try:
            # Test the command handler
            result = await telegram_bot.handle_command(command)
            
            if result:
                print(f"✅ {command} - SUCCESS")
            else:
                print(f"❌ {command} - FAILED")
                
        except Exception as e:
            print(f"❌ {command} - ERROR: {str(e)}")
    
    print(f"\n{'='*50}")
    print("✅ Telegram Commands Test Complete!")
    print("\n💡 Notes:")
    print("• All commands should work in both local and production environments")
    print("• Dashboard and thresholds use fallback import paths")
    print("• Database paths automatically detect production vs local")
    print("• Commands send actual messages to Telegram if configured")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test single command
        command = sys.argv[1]
        print(f"🧪 Testing single command: {command}")
        
        async def test_single():
            try:
                result = await telegram_bot.handle_command(command)
                print(f"✅ Command result: {result}")
            except Exception as e:
                print(f"❌ Command error: {str(e)}")
        
        asyncio.run(test_single())
    else:
        # Test all commands
        asyncio.run(test_telegram_commands())
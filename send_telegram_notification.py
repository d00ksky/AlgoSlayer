#!/usr/bin/env python3
"""
Send Telegram notifications from local ML training
Uses same bot token as cloud server
"""
import os
import sys
import requests
import json
from datetime import datetime

def send_telegram_message(message, silent=False):
    """Send message to Telegram bot"""
    try:
        # Get bot token from cloud server
        import subprocess
        result = subprocess.run([
            'ssh', '-o', 'ConnectTimeout=10', 'root@64.226.96.90',
            'grep TELEGRAM_BOT_TOKEN /opt/rtx-trading/.env | cut -d= -f2'
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode != 0:
            print(f"Failed to get bot token: {result.stderr}", file=sys.stderr)
            return False
        
        bot_token = result.stdout.strip()
        if not bot_token:
            print("Bot token is empty", file=sys.stderr)
            return False
        
        # Get chat ID from cloud server
        result = subprocess.run([
            'ssh', '-o', 'ConnectTimeout=10', 'root@64.226.96.90',
            'grep TELEGRAM_CHAT_ID /opt/rtx-trading/.env | cut -d= -f2'
        ], capture_output=True, text=True, timeout=15)
        
        chat_id = result.stdout.strip()
        if not chat_id:
            print("Chat ID is empty", file=sys.stderr)
            return False
        
        # Send message
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        # Add emoji and formatting for ML notifications
        formatted_message = f"🤖 **Local ML Training**\n\n{message}"
        
        payload = {
            'chat_id': chat_id,
            'text': formatted_message,
            'parse_mode': 'Markdown',
            'disable_notification': silent
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return True
        else:
            print(f"Telegram API error: {response.status_code} {response.text}", file=sys.stderr)
            return False
            
    except Exception as e:
        print(f"Error sending Telegram message: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python send_telegram_notification.py 'message' [silent]")
        sys.exit(1)
    
    message = sys.argv[1]
    silent = len(sys.argv) > 2 and sys.argv[2].lower() == 'true'
    
    success = send_telegram_message(message, silent)
    sys.exit(0 if success else 1)
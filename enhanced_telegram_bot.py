#!/usr/bin/env python3
"""
Enhanced Telegram Bot with 409 conflict prevention
Implements proper singleton pattern and webhook fallback
"""
import asyncio
import aiohttp
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger
import time

class TelegramBotSingleton:
    """Singleton Telegram bot to prevent multiple instances"""
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Bot configuration
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Conflict prevention
        self.last_update_id = 0
        self.polling_active = False
        self.session = None
        self.last_poll_time = 0
        self.poll_cooldown = 2  # Minimum seconds between polls
        
        # Error tracking
        self.consecutive_409_errors = 0
        self.max_409_retries = 3
        self.backoff_multiplier = 2
        
        self._initialized = True
        logger.info("📱 Enhanced Telegram bot initialized (singleton)")
    
    async def get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close_session(self):
        """Properly close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("📱 Telegram session closed")
    
    async def clear_pending_updates(self):
        """Clear any pending updates to prevent 409 conflicts"""
        try:
            session = await self.get_session()
            url = f"{self.api_url}/getUpdates"
            
            # Get all pending updates with high offset to clear them
            params = {"offset": -1, "limit": 1}
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    updates = data.get('result', [])
                    
                    if updates:
                        # Set offset to last update + 1 to clear pending
                        last_id = max(update.get('update_id', 0) for update in updates)
                        self.last_update_id = last_id
                        
                        # Clear with final call
                        params = {"offset": last_id + 1, "limit": 1, "timeout": 1}
                        async with session.get(url, params=params) as clear_response:
                            if clear_response.status == 200:
                                logger.info(f"📱 Cleared {len(updates)} pending Telegram updates")
                                return True
                                
                logger.info("📱 No pending Telegram updates to clear")
                return True
                
        except Exception as e:
            logger.warning(f"📱 Error clearing pending updates: {e}")
            return False
    
    async def get_updates_safe(self, offset: int = 0, timeout: int = 5) -> List[Dict]:
        """Get updates with 409 conflict prevention"""
        if not self.bot_token:
            return []
        
        # Prevent rapid polling
        current_time = time.time()
        if current_time - self.last_poll_time < self.poll_cooldown:
            await asyncio.sleep(self.poll_cooldown - (current_time - self.last_poll_time))
        
        try:
            session = await self.get_session()
            url = f"{self.api_url}/getUpdates"
            params = {
                'offset': offset, 
                'timeout': timeout,
                'limit': 10  # Limit batch size
            }
            
            self.last_poll_time = time.time()
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    updates = data.get('result', [])
                    
                    # Reset error counter on success
                    self.consecutive_409_errors = 0
                    
                    return updates
                    
                elif response.status == 409:
                    # Handle 409 Conflict specifically
                    self.consecutive_409_errors += 1
                    error_text = await response.text()
                    
                    logger.warning(f"📱 Telegram 409 Conflict (#{self.consecutive_409_errors}): {error_text}")
                    
                    if self.consecutive_409_errors >= self.max_409_retries:
                        logger.error("📱 Too many 409 errors - clearing pending updates")
                        await self.clear_pending_updates()
                        self.consecutive_409_errors = 0
                    
                    # Exponential backoff
                    backoff_time = self.backoff_multiplier ** self.consecutive_409_errors
                    await asyncio.sleep(min(backoff_time, 30))  # Max 30 sec backoff
                    
                    return []
                    
                else:
                    logger.warning(f"📱 Telegram API error {response.status}: {await response.text()}")
                    return []
                    
        except asyncio.TimeoutError:
            logger.warning("📱 Telegram API timeout")
            return []
        except Exception as e:
            logger.error(f"📱 Error getting Telegram updates: {e}")
            return []
    
    async def send_message_safe(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Send message with error handling"""
        if not self.bot_token or not self.chat_id:
            logger.warning("📱 Missing Telegram credentials")
            return False
            
        try:
            session = await self.get_session()
            url = f"{self.api_url}/sendMessage"
            
            data = {
                'chat_id': self.chat_id,
                'text': text[:4000],  # Telegram limit
                'parse_mode': parse_mode
            }
            
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"📱 Send message error {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"📱 Error sending Telegram message: {e}")
            return False
    
    async def process_messages_safe(self):
        """Process messages with enhanced safety"""
        if not self.bot_token or not self.chat_id:
            logger.warning("📱 Telegram not configured")
            return
            
        if self.polling_active:
            logger.warning("📱 Telegram polling already active")
            return
            
        self.polling_active = True
        logger.info("📱 Starting enhanced Telegram message listener")
        
        # Clear any pending updates first
        await self.clear_pending_updates()
        
        try:
            while self.polling_active:
                updates = await self.get_updates_safe(self.last_update_id + 1)
                
                for update in updates:
                    self.last_update_id = update.get('update_id', 0)
                    
                    # Process message
                    if 'message' in update:
                        message = update['message']
                        text = message.get('text', '').strip()
                        chat_id = str(message.get('chat', {}).get('id', ''))
                        
                        # Only respond to authorized chat
                        if chat_id == self.chat_id and text:
                            logger.info(f"📱 Processing Telegram command: {text}")
                            await self.handle_command_safe(text)
                
                # Prevent busy waiting
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("📱 Telegram polling cancelled")
        except Exception as e:
            logger.error(f"📱 Error in Telegram message processing: {e}")
        finally:
            self.polling_active = False
            await self.close_session()
            logger.info("📱 Telegram message listener stopped")
    
    async def handle_command_safe(self, text: str):
        """Handle commands with comprehensive error handling"""
        try:
            # Import commands here to avoid circular imports
            from src.core.telegram_commands import handle_telegram_command
            
            result = await handle_telegram_command(text)
            if result:
                await self.send_message_safe(result)
                
        except Exception as e:
            error_msg = f"❌ Command error: {str(e)[:200]}"
            await self.send_message_safe(error_msg)
            logger.error(f"📱 Command handling error: {e}")
    
    def stop_polling(self):
        """Stop the polling loop"""
        self.polling_active = False
        logger.info("📱 Telegram polling stop requested")

# Create singleton instance
enhanced_telegram_bot = TelegramBotSingleton()

# Compatibility layer for existing code
class TelegramBot:
    """Compatibility wrapper for existing telegram_bot usage"""
    
    def __init__(self):
        self.bot = enhanced_telegram_bot
    
    async def send_message(self, text: str) -> bool:
        return await self.bot.send_message_safe(text)
    
    async def process_incoming_messages(self):
        await self.bot.process_messages_safe()
    
    def stop_listener(self):
        self.bot.stop_polling()

# Global instance for backward compatibility
telegram_bot = TelegramBot()

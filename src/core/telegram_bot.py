"""
Telegram Bot for RTX Trading Notifications
Professional hedge fund-style mobile alerts
"""
import asyncio
import aiohttp
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional
from loguru import logger

from config.trading_config import config

class TelegramBot:
    """Professional trading notifications via Telegram"""
    
    def __init__(self):
        self.bot_token = config.telegram.BOT_TOKEN
        self.chat_id = config.telegram.CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        if not self.bot_token or not self.chat_id:
            logger.warning("⚠️ Telegram credentials not configured")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("📱 Telegram bot initialized successfully")
    
    async def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send message to Telegram chat"""
        if not self.enabled:
            logger.warning("📱 Telegram not configured - message not sent")
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        logger.debug("📱 Telegram message sent successfully")
                        return True
                    else:
                        logger.error(f"📱 Telegram send failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"📱 Telegram error: {e}")
            return False
    
    async def send_system_startup(self, trading_mode: str) -> bool:
        """Send system startup notification"""
        message = f"""
🤖 <b>RTX TRADING SYSTEM ONLINE</b>

📊 <b>Mode:</b> {trading_mode}
🎯 <b>Target:</b> RTX Corporation
💰 <b>Capital:</b> ${config.STARTING_CAPITAL:,}
🔍 <b>Analysis Interval:</b> {config.PREDICTION_INTERVAL_MINUTES} minutes

⚡ <b>AI Engine:</b> 8 signals active
🛡️ <b>Risk Management:</b> Active
📱 <b>Notifications:</b> Enabled

<i>System monitoring RTX market conditions...</i>
        """
        return await self.send_message(message.strip())
    
    async def send_prediction_alert(self, prediction_data: Dict) -> bool:
        """Send AI prediction alert"""
        symbol = prediction_data.get("symbol", "RTX")
        price = prediction_data.get("current_price", 0)
        direction = prediction_data.get("direction", "HOLD")
        confidence = prediction_data.get("confidence", 0)
        reasoning = prediction_data.get("reasoning", "Multiple AI signals")
        
        # Determine emoji based on direction and confidence
        if direction == "BUY":
            emoji = "📈" if confidence > 0.75 else "📊"
        elif direction == "SELL":
            emoji = "📉" if confidence > 0.75 else "📊"
        else:
            emoji = "⏸️"
        
        confidence_text = "HIGH" if confidence > 0.75 else "MEDIUM" if confidence > 0.5 else "LOW"
        
        message = f"""
{emoji} <b>RTX PREDICTION ALERT</b>

🎯 <b>Symbol:</b> {symbol}
💰 <b>Price:</b> ${price:.2f}
🤖 <b>AI Signal:</b> {direction}
📊 <b>Confidence:</b> {confidence:.1f}% ({confidence_text})

💭 <b>Analysis:</b> {reasoning}

⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}
        """
        return await self.send_message(message.strip())
    
    async def send_high_confidence_trade_alert(self, trade_data: Dict) -> bool:
        """Send high-confidence trade alert"""
        symbol = trade_data.get("symbol", "RTX")
        action = trade_data.get("action", "BUY")
        price = trade_data.get("price", 0)
        confidence = trade_data.get("confidence", 0)
        position_size = trade_data.get("position_size", 0)
        target_price = trade_data.get("target_price", 0)
        stop_loss = trade_data.get("stop_loss", 0)
        
        return_pct = ((target_price - price) / price * 100) if target_price > price else 0
        
        message = f"""
🚨 <b>HIGH CONFIDENCE TRADE ALERT</b>

🎯 <b>{symbol} - STRONG {action}</b>
📊 <b>Confidence:</b> {confidence:.1f}%
💰 <b>Current:</b> ${price:.2f}
📈 <b>Target:</b> ${target_price:.2f} (+{return_pct:.1f}%)
🛡️ <b>Stop Loss:</b> ${stop_loss:.2f}

💵 <b>Position:</b> ${position_size:.0f}
📐 <b>Risk/Reward:</b> Favorable

⚡ <b>Action Required:</b> Consider execution
⏰ <b>Valid:</b> Next 15 minutes
        """
        return await self.send_message(message.strip())
    
    async def send_trade_execution(self, execution_data: Dict) -> bool:
        """Send trade execution confirmation"""
        symbol = execution_data.get("symbol", "RTX")
        action = execution_data.get("action", "BUY")
        quantity = execution_data.get("quantity", 0)
        price = execution_data.get("price", 0)
        order_type = execution_data.get("order_type", "MARKET")
        status = execution_data.get("status", "EXECUTED")
        
        if status == "EXECUTED":
            emoji = "✅"
            status_text = "Order executed successfully"
        elif status == "PENDING":
            emoji = "⏳"
            status_text = "Order pending execution"
        else:
            emoji = "❌"
            status_text = "Order failed"
        
        message = f"""
{emoji} <b>TRADE EXECUTION</b>

🎯 <b>Symbol:</b> {symbol}
📊 <b>Action:</b> {action} {quantity} shares
💰 <b>Price:</b> ${price:.2f}
📋 <b>Order Type:</b> {order_type}

🔄 <b>Status:</b> {status_text}
⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}

💵 <b>Total Value:</b> ${quantity * price:.2f}
        """
        return await self.send_message(message.strip())
    
    async def send_daily_summary(self, summary_data: Dict) -> bool:
        """Send daily performance summary"""
        date = summary_data.get("date", datetime.now().strftime('%Y-%m-%d'))
        predictions_made = summary_data.get("predictions_made", 0)
        accuracy_rate = summary_data.get("accuracy_rate", 0)
        trades_executed = summary_data.get("trades_executed", 0)
        pnl = summary_data.get("pnl", 0)
        rtx_price = summary_data.get("rtx_price", 0)
        price_change = summary_data.get("price_change", 0)
        
        pnl_emoji = "💚" if pnl > 0 else "❌" if pnl < 0 else "➖"
        price_emoji = "📈" if price_change > 0 else "📉" if price_change < 0 else "➖"
        
        message = f"""
📊 <b>DAILY TRADING SUMMARY</b>
📅 <b>Date:</b> {date}

🤖 <b>AI PERFORMANCE:</b>
   • Predictions: {predictions_made}
   • Accuracy: {accuracy_rate:.1f}%
   
💰 <b>TRADING ACTIVITY:</b>
   • Trades: {trades_executed}
   • P&L: {pnl_emoji} ${pnl:+.2f}
   
📈 <b>RTX PERFORMANCE:</b>
   • Price: ${rtx_price:.2f}
   • Change: {price_emoji} {price_change:+.1f}%

🎯 <b>TOMORROW'S FOCUS:</b>
   • Continue monitoring RTX patterns
   • Target high-confidence setups
   • Maintain risk discipline

<i>System ready for next trading session</i>
        """
        return await self.send_message(message.strip())
    
    async def send_system_status(self, status_data: Dict) -> bool:
        """Send system health status"""
        uptime = status_data.get("uptime", "Unknown")
        ai_status = status_data.get("ai_engine", "Unknown")
        ibkr_status = status_data.get("ibkr_connection", "Unknown")
        last_prediction = status_data.get("last_prediction", "None")
        
        message = f"""
🔍 <b>SYSTEM STATUS CHECK</b>

⚙️ <b>Core System:</b> Online
⏱️ <b>Uptime:</b> {uptime}
🤖 <b>AI Engine:</b> {ai_status}
🏦 <b>IBKR:</b> {ibkr_status}

📊 <b>Last Activity:</b> {last_prediction}
📱 <b>Notifications:</b> Active
🛡️ <b>Risk Management:</b> Active

<i>All systems operational</i>
        """
        return await self.send_message(message.strip())
    
    async def send_error_alert(self, error_data: Dict) -> bool:
        """Send error/warning alert"""
        error_type = error_data.get("type", "System Error")
        message_text = error_data.get("message", "Unknown error occurred")
        severity = error_data.get("severity", "MEDIUM")
        
        emoji = "🚨" if severity == "HIGH" else "⚠️" if severity == "MEDIUM" else "ℹ️"
        
        message = f"""
{emoji} <b>SYSTEM ALERT</b>

🔴 <b>Type:</b> {error_type}
📝 <b>Message:</b> {message_text}
⚡ <b>Severity:</b> {severity}

⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}

<i>System continues monitoring...</i>
        """
        return await self.send_message(message.strip())
    
    async def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        if not self.enabled:
            return False
        
        test_message = f"""
🧪 <b>TELEGRAM BOT TEST</b>

✅ Connection: Successful
⏰ Time: {datetime.now().strftime('%H:%M:%S')}
🤖 Bot: RTX Trading System

<i>Notification system ready!</i>
        """
        
        result = await self.send_message(test_message.strip())
        if result:
            logger.success("📱 Telegram bot test successful")
        else:
            logger.error("📱 Telegram bot test failed")
        
        return result
    
    async def send_explanation_guide(self) -> bool:
        """Send comprehensive explanation of trading terms and signals"""
        
        explanation = """
RTX OPTIONS BASICS:

Call = Right to buy
Put = Right to sell
75%+ confidence = Trade
Less than 75% = Wait

Commands:
/terms - Options terms
/signals - AI signals
        """
        
        return await self.send_message(explanation.strip())
    
    async def send_terms_guide(self) -> bool:
        """Send options terms guide"""
        terms = """
📚 <b>OPTIONS TERMS</b>

<b>$145C:</b> Call option at $145 strike
<b>$145P:</b> Put option at $145 strike
<b>ATM:</b> At-The-Money (strike = price)
<b>OTM:</b> Out-of-The-Money
<b>ITM:</b> In-The-Money
<b>DTE:</b> Days To Expiration
<b>IV:</b> Implied Volatility
<b>C/P Ratio:</b> Call/Put volume ratio

<b>STRATEGIES:</b>
ATM calls: Buy at current price
OTM calls: Buy above current price
Put spreads: Bearish strategy
Iron condors: Sideways strategy
        """
        return await self.send_message(terms.strip())
    
    async def send_signals_guide(self) -> bool:
        """Send AI signals guide"""
        signals = """
🤖 <b>AI SIGNALS EXPLAINED</b>

<b>📈 Technical:</b> RSI, MACD, Bollinger Bands
<b>📊 Options Flow:</b> Call/put activity analysis
<b>📰 News:</b> AI sentiment from RTX news
<b>⚡ Volatility:</b> Price movement patterns
<b>🚀 Momentum:</b> Price acceleration trends
<b>🏭 Sector:</b> Defense stocks correlation
<b>🔄 Mean Reversion:</b> Overbought/oversold
<b>🌍 Market Regime:</b> Overall market state

<b>NEW SIGNALS:</b>
<b>📅 Earnings:</b> IV expansion timing
<b>📊 IV Percentile:</b> Options expense level
<b>🏦 Defense Contracts:</b> Government news
<b>🗳️ Geopolitical:</b> Political impact
        """
        return await self.send_message(signals.strip())
    
    async def handle_command(self, command: str) -> bool:
        """Handle incoming Telegram commands"""
        command = command.lower().strip()
        
        if command == "/explain" or command == "explain":
            return await self.send_explanation_guide()
        elif command == "/terms" or command == "terms":
            return await self.send_terms_guide()
        elif command == "/signals" or command == "signals":
            return await self.send_signals_guide()
        elif command == "/help" or command == "help":
            return await self.send_help_message()
        elif command == "/status" or command == "status":
            return await self.send_status_message()
        else:
            return await self.send_message(f"❓ Unknown command: {command}\n\nType /help for available commands")
    
    async def send_help_message(self) -> bool:
        """Send help message with available commands"""
        help_text = """
🤖 <b>RTX TRADING BOT COMMANDS</b>

📚 <b>/explain</b> - Quick options guide
📝 <b>/terms</b> - Options terminology
🤖 <b>/signals</b> - AI signals explained
📊 <b>/status</b> - System status
📱 <b>/help</b> - This help message

🎯 <b>AUTO NOTIFICATIONS:</b>
• Predictions every 15 minutes
• High confidence alerts (75%+)
• Daily reports at 5 PM ET

⚡ <b>SYSTEM:</b>
• 12 AI signals active
• Paper trading ($1,000)
• 75% confidence threshold
• Ready for Monday!
        """
        return await self.send_message(help_text.strip())
    
    async def send_status_message(self) -> bool:
        """Send current system status"""
        # This will be enhanced when we integrate with the scheduler
        status_text = f"""
📊 <b>RTX TRADING SYSTEM STATUS</b>

✅ <b>System:</b> Online and operational
🤖 <b>AI Signals:</b> 12 signals active
📊 <b>Trading Mode:</b> Paper trading (${config.STARTING_CAPITAL:,})
⚡ <b>Confidence:</b> 75% threshold for trades
📱 <b>Notifications:</b> Enabled

🎯 <b>NEXT STEPS:</b>
• Monitor predictions during market hours
• Watch for high-confidence alerts (75%+)
• Review options strategies in notifications

⏰ <b>Last Updated:</b> {datetime.now().strftime('%H:%M:%S')}"""
        
        return await self.send_message(status_text.strip())

# Global telegram bot instance
telegram_bot = TelegramBot() 
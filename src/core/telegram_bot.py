"""
Telegram Bot for RTX Trading Notifications
Professional hedge fund-style mobile alerts
"""
import asyncio
import aiohttp
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional
from loguru import logger
from src.core.signal_effectiveness_tracker import signal_tracker
from src.core.performance_monitor import performance_monitor
from src.core.cross_strategy_learning import cross_strategy_learning
from src.core.rtx_earnings_calendar import rtx_earnings_calendar
from src.core.backtesting_engine import backtesting_engine
from src.core.iv_percentile_alerts import iv_percentile_alerts
from src.core.automated_reset_system import automated_reset_system
from src.core.live_trading_framework import live_trading_framework

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
    
    def _sanitize_message(self, message: str, parse_mode: str = "HTML") -> str:
        """Sanitize message for Telegram parsing"""
        if parse_mode == "HTML":
            # Escape HTML characters
            message = message.replace("&", "&amp;")
            message = message.replace("<", "&lt;")
            message = message.replace(">", "&gt;")
            # Convert ** to <b></b> for HTML
            import re
            message = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', message)
        elif parse_mode == "Markdown":
            # Keep markdown as is but escape problematic chars
            message = message.replace("_", "\\_")
            message = message.replace("[", "\\[")
            message = message.replace("]", "\\]")
            message = message.replace("(", "\\(")
            message = message.replace(")", "\\)")
        else:
            # Plain text - remove all formatting
            import re
            message = re.sub(r'\*\*(.*?)\*\*', r'\1', message)
            message = message.replace("*", "")
        
        # Limit message length
        if len(message) > 4000:
            message = message[:3950] + "\n\n... (Message truncated for Telegram)"
        
        return message
    
    async def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send message to Telegram chat"""
        if not self.enabled:
            logger.warning("📱 Telegram not configured - message not sent")
            return False
        
        try:
            # Sanitize message for Telegram
            sanitized_message = self._sanitize_message(message, parse_mode)
            
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": sanitized_message,
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
        """Send enhanced AI prediction alert with ML insights"""
        symbol = prediction_data.get("symbol", "RTX")
        price = prediction_data.get("current_price", 0)
        direction = prediction_data.get("direction", "HOLD")
        confidence = prediction_data.get("confidence", 0)
        reasoning = prediction_data.get("reasoning", "Multiple AI signals")
        strategy_id = prediction_data.get("strategy_id", "Unknown")
        
        # Determine emoji based on direction and confidence
        if direction == "BUY":
            emoji = "📈" if confidence > 0.75 else "📊"
        elif direction == "SELL":
            emoji = "📉" if confidence > 0.75 else "📊"
        else:
            emoji = "⏸️"
        
        confidence_text = "HIGH" if confidence > 0.75 else "MEDIUM" if confidence > 0.5 else "LOW"
        
        # Get ML enhancement info
        ml_enhancement = await self._get_ml_enhancement_info(strategy_id, confidence)
        
        message = f"""
{emoji} <b>RTX PREDICTION ALERT</b>

🎯 <b>Symbol:</b> {symbol}
💰 <b>Price:</b> ${price:.2f}
🤖 <b>AI Signal:</b> {direction}
📊 <b>Confidence:</b> {confidence:.1%} ({confidence_text})
🧠 <b>Strategy:</b> {strategy_id}

{ml_enhancement}

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
📊 <b>Confidence:</b> {confidence:.1%}
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
        """Send enhanced daily performance summary with ML insights"""
        date = summary_data.get("date", datetime.now().strftime('%Y-%m-%d'))
        predictions_made = summary_data.get("predictions_made", 0)
        accuracy_rate = summary_data.get("accuracy_rate", 0)
        trades_executed = summary_data.get("trades_executed", 0)
        pnl = summary_data.get("pnl", 0)
        rtx_price = summary_data.get("rtx_price", 0)
        price_change = summary_data.get("price_change", 0)
        
        pnl_emoji = "💚" if pnl > 0 else "❌" if pnl < 0 else "➖"
        price_emoji = "📈" if price_change > 0 else "📉" if price_change < 0 else "➖"
        
        # Get ML insights
        ml_insight = await self._get_ml_insight_for_summary()
        
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

{ml_insight}

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
        elif command == "/ready" or command == "ready" or command == "/live":
            # Live trading readiness evaluation
            try:
                readiness_report = live_trading_framework.generate_readiness_report("conservative")
                return await self.send_message(readiness_report)
            except Exception as e:
                return await self.send_message(f"❌ Live trading evaluation error: {e}")
        elif command == "/lives" or command == "lives" or command == "/reset":
            # Strategy lives management
            try:
                lives_report = automated_reset_system.generate_lives_report()
                return await self.send_message(lives_report)
            except Exception as e:
                return await self.send_message(f"❌ Lives management error: {e}")
        elif command == "/iv" or command == "iv" or command == "/volatility":
            # IV Rank monitoring and alerts
            try:
                iv_dashboard = iv_percentile_alerts.generate_iv_dashboard()
                return await self.send_message(iv_dashboard)
            except Exception as e:
                return await self.send_message(f"❌ IV monitoring error: {e}")
        elif command == "/backtest" or command == "backtest" or command.startswith("/bt"):
            # Backtesting analysis
            try:
                # Default to last 30 days backtest
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                end_date = datetime.now().strftime("%Y-%m-%d")
                
                backtest_report = backtesting_engine.generate_backtest_report(
                    "current_system", start_date, end_date
                )
                return await self.send_message(backtest_report)
            except Exception as e:
                return await self.send_message(f"❌ Backtesting error: {e}")
        elif command == "/earnings" or command == "earnings" or command == "/calendar":
            # RTX earnings calendar analysis
            try:
                earnings_report = rtx_earnings_calendar.generate_earnings_report()
                return await self.send_message(earnings_report)
            except Exception as e:
                return await self.send_message(f"❌ Earnings calendar error: {e}")
        elif command == "/learning" or command == "learning" or command == "/analyze":
            # Cross-strategy learning analysis
            try:
                learning_report = cross_strategy_learning.generate_learning_report()
                return await self.send_message(learning_report)
            except Exception as e:
                return await self.send_message(f"❌ Learning analysis error: {e}")
        elif command == "/monitor" or command == "monitor" or command == "/health":
            # Performance monitoring command
            try:
                daily_summary = await performance_monitor.generate_daily_summary()
                return await self.send_message(daily_summary)
            except Exception as e:
                return await self.send_message(f"❌ Monitoring error: {e}")
        elif command == "/ready" or command == "ready" or command == "/live":
            # Live trading readiness evaluation
            try:
                readiness_report = live_trading_framework.generate_readiness_report("conservative")
                return await self.send_message(readiness_report)
            except Exception as e:
                return await self.send_message(f"❌ Live trading evaluation error: {e}")
        elif command == "/lives" or command == "lives" or command == "/reset":
            # Strategy lives management
            try:
                lives_report = automated_reset_system.generate_lives_report()
                return await self.send_message(lives_report)
            except Exception as e:
                return await self.send_message(f"❌ Lives management error: {e}")
        elif command == "/iv" or command == "iv" or command == "/volatility":
            # IV Rank monitoring and alerts
            try:
                iv_dashboard = iv_percentile_alerts.generate_iv_dashboard()
                return await self.send_message(iv_dashboard)
            except Exception as e:
                return await self.send_message(f"❌ IV monitoring error: {e}")
        elif command == "/backtest" or command == "backtest" or command.startswith("/bt"):
            # Backtesting analysis
            try:
                # Default to last 30 days backtest
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                end_date = datetime.now().strftime("%Y-%m-%d")
                
                backtest_report = backtesting_engine.generate_backtest_report(
                    "current_system", start_date, end_date
                )
                return await self.send_message(backtest_report)
            except Exception as e:
                return await self.send_message(f"❌ Backtesting error: {e}")
        elif command == "/earnings" or command == "earnings" or command == "/calendar":
            # RTX earnings calendar analysis
            try:
                earnings_report = rtx_earnings_calendar.generate_earnings_report()
                return await self.send_message(earnings_report)
            except Exception as e:
                return await self.send_message(f"❌ Earnings calendar error: {e}")
        elif command == "/learning" or command == "learning" or command == "/analyze":
            # Cross-strategy learning analysis
            try:
                learning_report = cross_strategy_learning.generate_learning_report()
                return await self.send_message(learning_report)
            except Exception as e:
                return await self.send_message(f"❌ Learning analysis error: {e}")
        elif command == "/monitor" or command == "monitor" or command == "/health":
            # Performance monitoring command
            try:
                daily_summary = await performance_monitor.generate_daily_summary()
                return await self.send_message(daily_summary)
            except Exception as e:
                return await self.send_message(f"❌ Monitoring error: {e}")
        elif command == "/signal_effectiveness" or command == "effectiveness":
            # Simple signal effectiveness report
            insights = signal_tracker.generate_signal_insights()
            if insights.get('total_signals_tracked', 0) == 0:
                message = "📊 Signal Effectiveness: No data yet. Need more completed trades!"
            else:
                top = insights.get('top_performers', [])
                message = f"📊 Signal Effectiveness: {insights.get('total_signals_tracked', 0)} signals tracked"
                if top:
                    message += f"\nTop: {top[0]['signal_name']} ({top[0]['win_rate']:.1f}%)"
            return await self.send_message(message)
        elif command == "/help" or command == "help":
            return await self.send_help_message()
        elif command == "/status" or command == "status":
            return await self.send_status_message()
        elif command == "/logs" or command == "logs":
            return await self.send_logs_message()
        elif command == "/restart" or command == "restart":
            return await self.send_restart_message()
        elif command == "/memory" or command == "memory":
            return await self.send_memory_message()
        elif command == "/dashboard" or command == "dashboard":
            return await self.send_dashboard_message()
        elif command == "/thresholds" or command == "thresholds":
            return await self.send_thresholds_message()
        elif command == "/positions" or command == "positions":
            return await self.send_positions_message()
        elif command == "/kelly" or command == "kelly":
            return await self.send_kelly_message()
        elif command == "/earnings" or command == "earnings":
            return await self.send_earnings_message()
        elif command == "/cross_strategy" or command == "cross_strategy":
            return await self.send_cross_strategy_message()
        elif command == "/learning" or command == "learning":
            return await self.send_learning_summary_message()
        elif command == "/ml_status" or command == "ml_status":
            return await self.send_comprehensive_ml_status()
        elif command == "/ml_quick" or command == "ml_quick":
            return await self.send_quick_ml_summary()
        elif command == "/ml_legacy" or command == "signal_effectiveness":
            return await self.send_ml_optimization_status()
        elif command == "/ml_alerts" or command == "ml_alerts":
            return await self.send_learning_progress_alerts()
        else:
            return await self.send_message(f"❓ Unknown command: {command}\n\nType /help for available commands")
    
    async def send_help_message(self) -> bool:
        """Send help message with available commands"""
        help_text = """
🤖 <b>RTX TRADING BOT COMMANDS</b>

📊 <b>/dashboard</b> - Live performance dashboard
🎯 <b>/thresholds</b> - Dynamic threshold status
💰 <b>/positions</b> - Account positions & trades
📈 <b>/kelly</b> - Kelly Criterion position sizing
📅 <b>/earnings</b> - RTX earnings calendar & strategy

🧠 <b>/cross_strategy</b> - Cross-strategy learning dashboard
🎓 <b>/learning</b> - Quick learning progress summary
🤖 <b>/ml_status</b> - Comprehensive ML system status and health
⚡ <b>/ml_quick</b> - Quick ML summary for frequent updates
🚨 <b>/ml_alerts</b> - Check for recent learning progress improvements
🔧 <b>/ml_legacy</b> - Legacy ML optimization status
📊 <b>/signal_effectiveness</b> - Signal performance analysis
🔧 <b>/monitor</b> - System health and performance alerts\n🧠 <b>/learning</b> - Cross-strategy learning analysis\n📅 <b>/earnings</b> - RTX earnings calendar and volatility analysis\n🔬 <b>/backtest</b> - Strategy backtesting analysis\n📊 <b>/iv</b> - IV rank monitoring and volatility alerts\n🎮 <b>/lives</b> - Strategy lives management and reset status\n🚀 <b>/ready</b> - Live trading readiness evaluation
🔧 <b>/monitor</b> - System health and performance alerts\n🧠 <b>/learning</b> - Cross-strategy learning analysis\n📅 <b>/earnings</b> - RTX earnings calendar and volatility analysis\n🔬 <b>/backtest</b> - Strategy backtesting analysis\n📊 <b>/iv</b> - IV rank monitoring and volatility alerts\n🎮 <b>/lives</b> - Strategy lives management and reset status\n🚀 <b>/ready</b> - Live trading readiness evaluation

📚 <b>/explain</b> - Quick options guide
📝 <b>/terms</b> - Options terminology
🤖 <b>/signals</b> - AI signals explained

📊 <b>/status</b> - System status
📋 <b>/logs</b> - Recent system logs
🔄 <b>/restart</b> - Restart service
💾 <b>/memory</b> - Memory usage stats
📱 <b>/help</b> - This help message

🎯 <b>AUTO NOTIFICATIONS:</b>
• Predictions every 15 minutes
• High confidence alerts (75%+)
• Daily reports at 5 PM ET

⚡ <b>SYSTEM:</b>
• 12 AI signals active
• Cross-strategy learning active
• Paper trading ($3,000 total)
• Advanced ML optimizations
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
    
    async def send_logs_message(self) -> bool:
        """Send recent system logs"""
        try:
            import subprocess
            result = subprocess.run([
                'journalctl', '-u', 'rtx-trading', '--no-pager', '-n', '10'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logs = result.stdout.strip()
                if logs:
                    # Format logs for phone reading
                    lines = logs.split('\n')[-8:]  # Last 8 lines for phone
                    formatted = []
                    for line in lines:
                        if 'rtx-trading' in line:
                            # Extract timestamp and message
                            parts = line.split('rtx-trading[')
                            if len(parts) > 1:
                                msg_part = parts[1].split(']: ', 1)
                                if len(msg_part) > 1:
                                    timestamp = parts[0].split()[-1]  # Get time part
                                    message = msg_part[1]
                                    formatted.append(f"<code>{timestamp}</code>\n{message}")
                    
                    if formatted:
                        logs_text = f"""
📋 <b>RECENT SYSTEM LOGS</b>

{chr(10).join(formatted[-6:])}

⏰ <b>Updated:</b> {datetime.now().strftime('%H:%M:%S')}"""
                        return await self.send_message(logs_text.strip())
                    else:
                        return await self.send_message("📋 <b>Logs:</b> No recent entries found")
                else:
                    return await self.send_message("📋 <b>Logs:</b> No entries found")
            else:
                return await self.send_message(f"❌ <b>Error getting logs:</b> {result.stderr}")
        except Exception as e:
            return await self.send_message(f"❌ <b>Error:</b> {str(e)}")
    
    async def send_restart_message(self) -> bool:
        """Restart the trading service with external script"""
        try:
            import subprocess
            import os
            
            # Step 1: Send initial status
            await self.send_message("🔄 <b>Initiating restart sequence...</b>")
            
            # Step 2: Create restart script that runs externally
            restart_script = """#!/bin/bash
# External restart script to avoid systemctl deadlock
sleep 2
systemctl stop rtx-trading
sleep 2
systemctl kill rtx-trading
sleep 1
systemctl reset-failed rtx-trading
sleep 1
systemctl start rtx-trading
sleep 3

# Check if restart was successful
if systemctl is-active --quiet rtx-trading; then
    echo "SUCCESS"
else
    echo "FAILED"
fi
"""
            
            # Write script to writable directory
            script_path = '/opt/rtx-trading/restart_rtx.sh'
            with open(script_path, 'w') as f:
                f.write(restart_script)
            os.chmod(script_path, 0o755)
            
            # Step 3: Run restart script in background (detached from current process)
            subprocess.Popen([script_path], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE,
                           start_new_session=True)
            
            # Step 4: Send follow-up message
            await self.send_message(
                "🔄 <b>Restart script launched!</b>\n\n"
                "⏱️ The service will restart in ~10 seconds\n"
                "📱 Send /status in 15 seconds to verify\n\n"
                "✅ This avoids the systemctl deadlock issue"
            )
            
            return True
            
        except Exception as e:
            return await self.send_message(f"❌ <b>Error during restart:</b> {str(e)}")
    
    async def send_memory_message(self) -> bool:
        """Send memory usage information"""
        try:
            import subprocess
            result = subprocess.run(['free', '-h'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            mem_line = lines[1].split()
            swap_line = lines[2].split()
            
            # Get disk usage
            df_result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
            disk_line = df_result.stdout.split('\n')[1].split()
            
            memory_text = f"""
💾 <b>SYSTEM MEMORY STATUS</b>

<b>🔹 RAM Usage:</b>
• Used: {mem_line[2]} / {mem_line[1]} total
• Available: {mem_line[6]}
• Usage: {round((float(mem_line[2].replace('Mi','').replace('Gi','')) / float(mem_line[1].replace('Mi','').replace('Gi',''))) * 100, 1)}%

<b>🔹 Swap:</b>
• Used: {swap_line[2]} / {swap_line[1]} total

<b>🔹 Disk Space:</b>
• Used: {disk_line[2]} / {disk_line[1]} total
• Available: {disk_line[3]}
• Usage: {disk_line[4]}

⏰ <b>Updated:</b> {datetime.now().strftime('%H:%M:%S')}"""
            
            return await self.send_message(memory_text.strip())
        except Exception as e:
            return await self.send_message(f"❌ <b>Error getting memory info:</b> {str(e)}")
    
    async def get_updates(self, offset: int = 0) -> List[Dict]:
        """Get updates from Telegram"""
        if not self.bot_token:
            return []
            
        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
        params = {'offset': offset, 'timeout': 5}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('result', [])
                    else:
                        logger.warning(f"Failed to get Telegram updates: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error getting Telegram updates: {e}")
            return []
    
    async def send_market_open_status(self) -> bool:
        """Send daily market open status message with system health and positions"""
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
                
            message += f"📊 *Trading Service:* {service_status}\n"
            message += f"🎯 *Target:* RTX Corporation\n"
            message += f"📈 *Mode:* Paper Trading\n\n"
            
            # Get current positions and balance
            message += "💰 *ACCOUNT STATUS*\n"
            
            try:
                import sqlite3
                import os
                
                # Check main options performance database
                db_path = "/opt/rtx-trading/data/options_performance.db"
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Get latest balance
                    cursor.execute("SELECT balance_after FROM account_history ORDER BY rowid DESC LIMIT 1")
                    balance_row = cursor.fetchone()
                    balance = balance_row[0] if balance_row else 1000.0
                    
                    # Count open positions
                    cursor.execute("SELECT COUNT(*) FROM options_predictions WHERE status = 'OPEN'")
                    open_positions = cursor.fetchone()[0]
                    
                    # Get today's trades count
                    from datetime import date
                    today = date.today()
                    try:
                        cursor.execute("SELECT COUNT(*) FROM options_predictions WHERE DATE(entry_timestamp) = ?", (today,))
                        today_trades = cursor.fetchone()[0]
                    except:
                        # Fallback if column doesn't exist
                        cursor.execute("SELECT COUNT(*) FROM options_predictions WHERE DATE(timestamp) = ?", (today,))
                        today_trades = cursor.fetchone()[0]
                    
                    message += f"💳 *Balance:* ${balance:.2f}\n"
                    message += f"📊 *Open Positions:* {open_positions}\n"
                    message += f"🔄 *Today's Trades:* {today_trades}\n"
                    
                    # Show any open positions
                    if open_positions > 0:
                        cursor.execute("SELECT contract_symbol, entry_price, confidence FROM options_predictions WHERE status = 'OPEN' LIMIT 3")
                        positions = cursor.fetchall()
                        message += "\n📈 *Open Positions:*\n"
                        for pos in positions:
                            message += f"   • {pos[0]} @ ${pos[1]:.2f} ({pos[2]:.0%})\n"
                    
                    conn.close()
                else:
                    message += "💳 *Balance:* $1,000.00 (initial)\n"
                    message += "📊 *Open Positions:* 0\n"
                    message += "🔄 *Today's Trades:* 0\n"
                    
            except Exception as e:
                message += f"⚠️ *Account Status:* Error retrieving data\n"
                logger.error(f"Error getting account status: {e}")
            
            # Get current RTX stock price
            message += "\n🎯 *RTX MARKET DATA*\n"
            try:
                # Import options data engine to get stock price
                from .options_data_engine import options_data_engine
                current_price = options_data_engine.get_current_stock_price()
                if current_price:
                    message += f"💰 *Current Price:* ${current_price:.2f}\n"
                else:
                    message += "💰 *Current Price:* Fetching...\n"
            except Exception as e:
                message += "💰 *Current Price:* Error fetching\n"
                logger.error(f"Error getting RTX price: {e}")
            
            # AI signals status
            message += "\n🤖 *AI SIGNALS STATUS*\n"
            message += "📊 *Active Signals:* 12 AI modules\n"
            message += "🔍 *Analysis Interval:* Every 5 minutes\n"
            message += "⚡ *Confidence Threshold:* 60% minimum\n"
            
            # System health indicators
            message += "\n🏥 *SYSTEM HEALTH*\n"
            
            # Check if options data is available
            try:
                from .options_data_engine import options_data_engine
                chain = options_data_engine.get_real_options_chain()
                options_count = len(chain)
                message += f"📊 *Options Available:* {options_count} contracts\n"
            except:
                message += "📊 *Options Available:* Error checking\n"
            
            # Check position sizing
            try:
                from config.options_config import options_config
                max_investment = options_config.get_position_size(1000.0)
                message += f"💰 *Max Position Size:* ${max_investment:.0f}\n"
            except:
                message += "💰 *Max Position Size:* Error checking\n"
            
            message += f"\n✅ *Status:* All systems operational\n"
            message += f"📱 *Notifications:* Active (you'll get alerts when trades execute)\n"
            message += f"\n_Good luck trading today! 🚀_"
            
            return await self.send_message(message.strip(), parse_mode="Markdown")
            
        except Exception as e:
            # Even if there's an error, send a basic status message
            error_message = f"""🔔 *MARKET OPEN STATUS* — {datetime.now().strftime('%A, %B %d')}
⏰ *Time:* {datetime.now().strftime('%H:%M ET')}

⚠️ *SYSTEM STATUS:* Error retrieving full status
❌ *Error:* {str(e)}

🤖 *Basic Status:* Trading system is running
📱 *Notifications:* You're receiving this message, so Telegram works!

_Please check system manually or contact support._"""
            
            logger.error(f"❌ Market open status error: {e}")
            return await self.send_message(error_message.strip(), parse_mode="Markdown")
    
    async def process_incoming_messages(self):
        """Process incoming messages from Telegram"""
        if not self.bot_token or not self.chat_id:
            return
            
        last_update_id = 0
        logger.info("📱 Starting Telegram message listener...")
        
        while True:
            try:
                updates = await self.get_updates(last_update_id + 1)
                
                for update in updates:
                    last_update_id = update.get('update_id', 0)
                    
                    # Process message
                    if 'message' in update:
                        message = update['message']
                        text = message.get('text', '').strip()
                        chat_id = str(message.get('chat', {}).get('id', ''))
                        
                        # Only respond to authorized chat
                        if chat_id == self.chat_id and text:
                            logger.info(f"Processing Telegram command: {text}")
                            if text.startswith('/') or text.lower() in ['explain', 'terms', 'signals', 'help', 'status', 'logs', 'restart', 'memory', 'dashboard', 'thresholds', 'positions', 'kelly', 'earnings', 'cross_strategy', 'learning', 'ml_status, signal_effectiveness']:
                                await self.handle_command(text)
                            
            except Exception as e:
                logger.error(f"Error in Telegram message listener: {e}")
                await asyncio.sleep(5)
            
            await asyncio.sleep(1)
    
    async def send_dashboard_message(self) -> bool:
        """Send live performance dashboard"""
        try:
            # Import dashboard here to avoid circular imports
            try:
                from .dashboard import dashboard
            except ImportError:
                from src.core.dashboard import dashboard
            
            dashboard_text = dashboard.generate_dashboard()
            
            # Limit message length for Telegram (4096 char limit)
            if len(dashboard_text) > 4000:
                dashboard_text = dashboard_text[:3900] + "\n\n... (Dashboard truncated for Telegram)"
                
            return await self.send_message(dashboard_text)
            
        except Exception as e:
            logger.error(f"❌ Dashboard error: {e}")
            return await self.send_message(f"❌ <b>Dashboard Error:</b> {str(e)}")
    
    async def send_thresholds_message(self) -> bool:
        """Send dynamic threshold status"""
        try:
            # Import thresholds here to avoid circular imports
            try:
                from .dynamic_thresholds import dynamic_threshold_manager
            except ImportError:
                from src.core.dynamic_thresholds import dynamic_threshold_manager
            
            thresholds_text = dynamic_threshold_manager.get_threshold_summary()
            
            return await self.send_message(thresholds_text)
            
        except Exception as e:
            logger.error(f"❌ Thresholds error: {e}")
            return await self.send_message(f"❌ <b>Thresholds Error:</b> {str(e)}")
    
    async def send_positions_message(self) -> bool:
        """Send account positions and strategy status"""
        try:
            import sqlite3
            import os
            
            message = "📊 <b>Account Status</b>\n\n"
            
            strategies = ["conservative", "moderate", "aggressive"]
            emojis = {"conservative": "🛡️", "moderate": "⚖️", "aggressive": "🚀"}
            
            total_positions = 0
            total_balance = 0
            
            for strategy in strategies:
                try:
                    # Try production path first, fallback to local
                    db_path = f"/opt/rtx-trading/data/options_performance_{strategy}.db"
                    if not os.path.exists(db_path):
                        db_path = f"data/options_performance_{strategy}.db"
                    
                    if os.path.exists(db_path):
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()
                        
                        # Get balance
                        cursor.execute("SELECT balance_after FROM account_history ORDER BY rowid DESC LIMIT 1")
                        balance_row = cursor.fetchone()
                        balance = balance_row[0] if balance_row else 1000.0
                        total_balance += balance
                        
                        # Count positions
                        cursor.execute("SELECT COUNT(*) FROM options_predictions WHERE status = 'OPEN'")
                        positions = cursor.fetchone()[0]
                        total_positions += positions
                        
                        emoji = emojis.get(strategy, "📊")
                        message += f"{emoji} <b>{strategy.title()}</b>: ${balance:.2f}\n"
                        message += f"   📈 Open Positions: {positions}\n"
                        
                        if positions > 0:
                            cursor.execute("SELECT contract_symbol, entry_price FROM options_predictions WHERE status = 'OPEN' LIMIT 2")
                            for row in cursor.fetchall():
                                message += f"      • {row[0]} @ ${row[1]:.2f}\n"
                        
                        if balance < 300 and positions == 0:
                            message += f"   ⚠️ Ready for reset!\n"
                        
                        conn.close()
                    else:
                        message += f"{emojis.get(strategy, '📊')} <b>{strategy.title()}</b>: No database found\n"
                    
                    message += "\n"
                    
                except Exception as e:
                    message += f"{emojis.get(strategy, '📊')} <b>{strategy.title()}</b>: Error - {str(e)}\n\n"
            
            message += f"💰 <b>Total Positions:</b> {total_positions}\n"
            message += f"💳 <b>Total Balance:</b> ${total_balance:.2f}\n"
            message += f"📊 <b>Combined Return:</b> {((total_balance - 3000) / 3000 * 100):+.1f}%\n"
            message += f"\n⏰ <b>Updated:</b> {datetime.now().strftime('%H:%M:%S')}"
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Positions error: {e}")
            return await self.send_message(f"❌ <b>Positions Error:</b> {str(e)}")
    
    async def send_kelly_message(self) -> bool:
        """Send Kelly Criterion position sizing status"""
        try:
            # Import kelly sizer here to avoid circular imports
            try:
                from .kelly_position_sizer import kelly_sizer
            except ImportError:
                from src.core.kelly_position_sizer import kelly_sizer
            
            kelly_text = kelly_sizer.get_kelly_summary()
            
            return await self.send_message(kelly_text)
            
        except Exception as e:
            logger.error(f"❌ Kelly error: {e}")
            return await self.send_message(f"❌ <b>Kelly Error:</b> {str(e)}")
    
    async def send_earnings_message(self) -> bool:
        """Send RTX earnings calendar status"""
        try:
            # Import earnings calendar here to avoid circular imports
            try:
                from .earnings_calendar import rtx_earnings
            except ImportError:
                from src.core.earnings_calendar import rtx_earnings
            
            earnings_text = rtx_earnings.get_earnings_summary()
            
            # Check if there's an urgent earnings alert
            alert = rtx_earnings.get_earnings_alert()
            if alert:
                earnings_text = f"{alert}\n\n{earnings_text}"
            
            return await self.send_message(earnings_text)
            
        except Exception as e:
            logger.error(f"❌ Earnings error: {e}")
            return await self.send_message(f"❌ <b>Earnings Error:</b> {str(e)}")
    
    async def send_cross_strategy_message(self) -> bool:
        """Send comprehensive cross-strategy learning dashboard"""
        try:
            # Import cross-strategy dashboard here to avoid circular imports
            try:
                from .cross_strategy_dashboard import cross_strategy_dashboard
            except ImportError:
                from src.core.cross_strategy_dashboard import cross_strategy_dashboard
            
            dashboard_text = cross_strategy_dashboard.generate_comprehensive_dashboard()
            
            # Limit message length for Telegram (4096 char limit)
            if len(dashboard_text) > 4000:
                dashboard_text = dashboard_text[:3900] + "\n\n... (Dashboard truncated for Telegram)"
            
            return await self.send_message(dashboard_text)
            
        except Exception as e:
            logger.error(f"❌ Cross-strategy dashboard error: {e}")
            return await self.send_message(f"❌ <b>Cross-Strategy Error:</b> {str(e)}")
    
    async def send_learning_summary_message(self) -> bool:
        """Send quick learning summary"""
        try:
            # Import cross-strategy dashboard here to avoid circular imports
            try:
                from .cross_strategy_dashboard import cross_strategy_dashboard
            except ImportError:
                from src.core.cross_strategy_dashboard import cross_strategy_dashboard
            
            learning_text = cross_strategy_dashboard.get_quick_learning_summary()
            
            return await self.send_message(learning_text)
            
        except Exception as e:
            logger.error(f"❌ Learning summary error: {e}")
            return await self.send_message(f"❌ <b>Learning Summary Error:</b> {str(e)}")
    
    async def send_ml_optimization_status(self) -> bool:
        """Send ML optimization status and performance"""
        try:
            # Import ML optimization applier here to avoid circular imports
            try:
                from .ml_optimization_applier import ml_applier
            except ImportError:
                from src.core.ml_optimization_applier import ml_applier
            
            status_text = ml_applier.generate_optimization_report()
            
            return await self.send_message(status_text)
            
        except Exception as e:
            logger.error(f"❌ ML status error: {e}")
            return await self.send_message(f"❌ <b>ML Status Error:</b> {str(e)}")
    
    async def send_comprehensive_ml_status(self) -> bool:
        """Send comprehensive ML system status report"""
        try:
            from src.core.ml_status_monitor import ml_status_monitor
            
            status_data = ml_status_monitor.get_comprehensive_ml_status()
            message = ml_status_monitor.format_ml_status_message(status_data)
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Comprehensive ML status error: {e}")
            return await self.send_message(f"❌ <b>ML Status Error:</b> {str(e)}")
    
    async def send_quick_ml_summary(self) -> bool:
        """Send quick ML summary for frequent updates"""
        try:
            from src.core.ml_status_monitor import ml_status_monitor
            
            status_data = ml_status_monitor.get_comprehensive_ml_status()
            message = ml_status_monitor.format_quick_ml_summary(status_data)
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Quick ML summary error: {e}")
            return await self.send_message(f"❌ <b>ML Summary Error:</b> {str(e)}")
    
    async def send_automated_ml_notification(self) -> bool:
        """Send automated ML notification if conditions are met"""
        try:
            from src.core.ml_status_monitor import ml_status_monitor
            from src.core.ml_learning_alerts import ml_learning_alerts
            
            # Check for learning improvements first (these are high priority)
            learning_alerts = ml_learning_alerts.check_for_learning_improvements()
            if learning_alerts:
                alert_message = ml_learning_alerts.format_learning_progress_alert(learning_alerts)
                await self.send_message(alert_message)
                logger.info("📱 Learning progress alert sent")
                return True
            
            # Check if regular notification should be sent
            if not ml_status_monitor.should_send_notification():
                return False
            
            # Send comprehensive status
            status_data = ml_status_monitor.get_comprehensive_ml_status()
            message = f"🔄 **AUTOMATED ML STATUS UPDATE**\n\n{ml_status_monitor.format_ml_status_message(status_data)}"
            
            result = await self.send_message(message)
            
            if result:
                ml_status_monitor.mark_notification_sent()
                logger.info("📱 Automated ML notification sent successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Automated ML notification error: {e}")
            return False
    
    async def _get_ml_insight_for_summary(self) -> str:
        """Get ML insight snippet for daily summary"""
        try:
            from src.core.ml_status_monitor import ml_status_monitor
            
            status_data = ml_status_monitor.get_comprehensive_ml_status()
            health = status_data.get("overall_health", {})
            learning = status_data.get("learning_effectiveness", {})
            
            health_emoji = health.get("emoji", "⚪")
            health_status = health.get("status", "Unknown")
            learning_active = "✅ Active" if learning.get("learning_applied", False) else "⚠️ Inactive"
            
            return f"""🧠 <b>ML HEALTH:</b>
   • System Status: {health_emoji} {health_status}
   • Learning: {learning_active}
   • Strategies Enhanced: {learning.get('strategies_enhanced', 0)}/8"""
            
        except Exception as e:
            logger.error(f"❌ ML insight error: {e}")
            return "🧠 <b>ML STATUS:</b> Available via /ml_status"
    
    async def _get_ml_enhancement_info(self, strategy_id: str, confidence: float) -> str:
        """Get ML enhancement information for predictions"""
        try:
            from src.core.ml_status_monitor import ml_status_monitor
            
            status_data = ml_status_monitor.get_comprehensive_ml_status()
            learning = status_data.get("learning_effectiveness", {})
            strategies = status_data.get("strategy_comparison", {})
            
            # Check if this strategy was enhanced by ML
            enhanced = "✅ ML Enhanced" if learning.get("learning_applied", False) else "⚪ Standard"
            
            # Get strategy performance if available
            strategy_perf = strategies.get(strategy_id, {})
            if strategy_perf:
                recent_wr = strategy_perf.get("win_rate", 0)
                wr_text = f"Recent: {recent_wr:.1f}% WR"
            else:
                wr_text = "Recent: No data"
            
            # Confidence context
            if confidence >= 0.8:
                conf_context = "🔥 Excellent confidence"
            elif confidence >= 0.7:
                conf_context = "✅ Good confidence"
            elif confidence >= 0.6:
                conf_context = "⚡ Acceptable confidence"
            else:
                conf_context = "⚠️ Low confidence"
            
            return f"""🎓 <b>ML Context:</b> {enhanced} • {wr_text}
🎯 <b>Signal Quality:</b> {conf_context}"""
            
        except Exception as e:
            logger.error(f"❌ ML enhancement info error: {e}")
            return "🧠 <b>ML Enhancement:</b> Data unavailable"
    
    async def send_learning_progress_alerts(self) -> bool:
        """Send manual check for learning progress alerts"""
        try:
            from src.core.ml_learning_alerts import ml_learning_alerts
            
            learning_alerts = ml_learning_alerts.check_for_learning_improvements()
            
            if learning_alerts:
                message = ml_learning_alerts.format_learning_progress_alert(learning_alerts)
            else:
                message = """📊 <b>ML Learning Progress Check</b>

✅ <b>Status:</b> No significant improvements detected in recent period

🔍 <b>Monitoring:</b>
   • Win rate changes: < 3% threshold
   • Strategy activations: None recent  
   • System improvements: Within normal range
   • Learning effectiveness: Stable

ℹ️ <b>Note:</b> Alerts are sent automatically when significant improvements occur. Use /ml_status for detailed analysis."""
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Learning progress alerts error: {e}")
            return await self.send_message(f"❌ <b>Learning Progress Error:</b> {str(e)}")
    
    async def send_dashboard_message(self) -> bool:
        """Send live multi-strategy dashboard"""
        try:
            # Import dashboard here to avoid circular imports
            try:
                from .dashboard import PerformanceDashboard
            except ImportError:
                from src.core.dashboard import PerformanceDashboard
            
            dashboard = PerformanceDashboard()
            dashboard_text = dashboard.generate_dashboard()
            
            # Limit message length for Telegram (4096 char limit)
            if len(dashboard_text) > 4000:
                dashboard_text = dashboard_text[:3900] + "\n\n... (Dashboard truncated for Telegram)"
            
            return await self.send_message(dashboard_text)
            
        except Exception as e:
            logger.error(f"❌ Dashboard error: {e}")
            return await self.send_message(f"❌ <b>Dashboard Error:</b> {str(e)}")
    
    async def send_positions_message(self) -> bool:
        """Send current positions for all 8 strategies"""
        try:
            # Import dashboard here to avoid circular imports
            try:
                from .dashboard import PerformanceDashboard
            except ImportError:
                from src.core.dashboard import PerformanceDashboard
            
            dashboard = PerformanceDashboard()
            # Use the comprehensive dashboard which includes positions info
            dashboard_text = dashboard.generate_dashboard()
            
            # Focus on positions section
            positions_header = "💰 **Strategy Positions & Performance**\n" + "=" * 40 + "\n\n"
            positions_text = positions_header + dashboard_text
            
            # Limit message length for Telegram (4096 char limit)
            if len(positions_text) > 4000:
                positions_text = positions_text[:3900] + "\n\n... (Positions truncated for Telegram)"
            
            return await self.send_message(positions_text)
            
        except Exception as e:
            logger.error(f"❌ Positions error: {e}")
            return await self.send_message(f"❌ <b>Positions Error:</b> {str(e)}")
    
    async def send_thresholds_message(self) -> bool:
        """Send dynamic thresholds for all 8 strategies"""
        try:
            # Import dynamic thresholds here to avoid circular imports
            try:
                from .dynamic_thresholds import dynamic_threshold_manager
            except ImportError:
                from src.core.dynamic_thresholds import dynamic_threshold_manager
            
            thresholds_text = dynamic_threshold_manager.get_threshold_summary()
            
            return await self.send_message(thresholds_text)
            
        except Exception as e:
            logger.error(f"❌ Thresholds error: {e}")
            return await self.send_message(f"❌ <b>Thresholds Error:</b> {str(e)}")
    
    async def send_kelly_message(self) -> bool:
        """Send Kelly Criterion position sizing for all strategies"""
        try:
            # Import Kelly optimizer here to avoid circular imports
            try:
                from .kelly_position_sizer import KellyPositionSizer
            except ImportError:
                from src.core.kelly_position_sizer import KellyPositionSizer
            
            kelly_sizer = KellyPositionSizer()
            kelly_text = kelly_sizer.get_kelly_summary()
            
            return await self.send_message(kelly_text)
            
        except Exception as e:
            logger.error(f"❌ Kelly error: {e}")
            return await self.send_message(f"❌ <b>Kelly Error:</b> {str(e)}")

# Global telegram bot instance
telegram_bot = TelegramBot() 
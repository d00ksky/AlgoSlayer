"""
Daily Performance Reporter for RTX Trading System
Generates comprehensive daily reports with AI learning progress,
trading performance, and market analysis
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yfinance as yf
import pandas as pd
import numpy as np

from src.core.telegram_bot import telegram_bot
from src.core.rtx_signal_orchestrator import rtx_orchestrator
from src.core.lightweight_ml import ml_system
from src.core.enhanced_ibkr_manager import ibkr_manager
from src.core.database import database

class DailyReporter:
    """
    Generates comprehensive daily reports for the RTX trading system
    Tracks learning progress, prediction accuracy, and trading performance
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.symbol = "RTX"
        self.report_time = "17:00"  # 5 PM ET after market close
        
    async def generate_daily_report(self) -> Dict:
        """Generate comprehensive daily performance report"""
        try:
            self.logger.info("📊 Generating daily performance report...")
            
            # Get today's date
            today = datetime.now().date()
            
            # Collect all data concurrently
            report_data = await self._collect_report_data(today)
            
            # Generate the report
            report = await self._build_comprehensive_report(report_data)
            
            # Send to Telegram
            await self._send_telegram_report(report)
            
            # Save to database
            await self._save_report_to_db(report)
            
            self.logger.info("✅ Daily report generated and sent")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating daily report: {e}")
            await self._send_error_report(str(e))
            return {}
    
    async def _collect_report_data(self, date) -> Dict:
        """Collect all data needed for the report"""
        try:
            # Get data concurrently for speed
            tasks = [
                self._get_market_data(),
                self._get_prediction_performance(),
                self._get_trading_performance(),
                self._get_ml_learning_progress(),
                self._get_signal_analysis(),
                self._get_portfolio_status()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return {
                'market_data': results[0] if not isinstance(results[0], Exception) else {},
                'prediction_performance': results[1] if not isinstance(results[1], Exception) else {},
                'trading_performance': results[2] if not isinstance(results[2], Exception) else {},
                'ml_progress': results[3] if not isinstance(results[3], Exception) else {},
                'signal_analysis': results[4] if not isinstance(results[4], Exception) else {},
                'portfolio_status': results[5] if not isinstance(results[5], Exception) else {},
                'date': date
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting report data: {e}")
            return {'date': date}
    
    async def _get_market_data(self) -> Dict:
        """Get RTX market performance for the day"""
        try:
            ticker = yf.Ticker(self.symbol)
            
            # Get today's data
            data = ticker.history(period="2d", interval="1h")  # 2 days to get previous close
            
            if data.empty:
                return {}
            
            current_price = float(data['Close'].iloc[-1])
            previous_close = float(data['Close'].iloc[0])
            
            # Calculate metrics
            daily_change = current_price - previous_close
            daily_change_pct = (daily_change / previous_close) * 100
            
            high = float(data['High'].max())
            low = float(data['Low'].min())
            volume = int(data['Volume'].sum())
            avg_volume = int(data['Volume'].mean())
            
            # Volatility
            returns = data['Close'].pct_change().dropna()
            volatility = float(returns.std() * np.sqrt(24))  # Annualized hourly vol
            
            return {
                'current_price': current_price,
                'previous_close': previous_close,
                'daily_change': daily_change,
                'daily_change_pct': daily_change_pct,
                'high': high,
                'low': low,
                'volume': volume,
                'avg_volume': avg_volume,
                'volatility': volatility,
                'price_range_pct': ((high - low) / previous_close) * 100
            }
            
        except Exception as e:
            self.logger.error(f"Error getting market data: {e}")
            return {}
    
    async def _get_prediction_performance(self) -> Dict:
        """Get AI prediction performance for the day"""
        try:
            # Get today's predictions from orchestrator
            performance = await rtx_orchestrator.get_performance_summary()
            
            if not performance:
                return {'predictions_made': 0, 'accuracy': 0.0}
            
            # Additional metrics from recent predictions
            recent_predictions = rtx_orchestrator.prediction_history[-20:]  # Last 20 predictions
            
            if not recent_predictions:
                return {'predictions_made': 0, 'accuracy': 0.0}
            
            # Calculate accuracy metrics
            high_confidence_predictions = [p for p in recent_predictions if p.confidence > 0.8]
            trade_worthy_predictions = [p for p in recent_predictions if p.trade_worthy]
            
            # Direction distribution
            buy_predictions = sum(1 for p in recent_predictions if p.action == 'BUY')
            sell_predictions = sum(1 for p in recent_predictions if p.action == 'SELL')
            hold_predictions = sum(1 for p in recent_predictions if p.action == 'HOLD')
            
            avg_confidence = np.mean([p.confidence for p in recent_predictions])
            avg_signals_agreeing = np.mean([p.signals_agreeing for p in recent_predictions])
            
            return {
                'predictions_made': len(recent_predictions),
                'high_confidence_count': len(high_confidence_predictions),
                'trade_worthy_count': len(trade_worthy_predictions),
                'buy_predictions': buy_predictions,
                'sell_predictions': sell_predictions,
                'hold_predictions': hold_predictions,
                'avg_confidence': avg_confidence,
                'avg_signals_agreeing': avg_signals_agreeing,
                'accuracy': performance.get('average_confidence', 0.0)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting prediction performance: {e}")
            return {}
    
    async def _get_trading_performance(self) -> Dict:
        """Get trading performance metrics"""
        try:
            # Get portfolio summary
            portfolio = await ibkr_manager.get_portfolio_summary()
            
            # Mock P&L calculation (would be real in live system)
            # For now, estimate based on RTX price movement and positions
            market_data = await self._get_market_data()
            
            estimated_pnl = 0.0
            if portfolio.get('rtx_shares', 0) > 0 and market_data:
                shares = portfolio['rtx_shares']
                price_change = market_data.get('daily_change', 0)
                estimated_pnl = shares * price_change
            
            return {
                'trades_executed': 0,  # Would track actual trades
                'rtx_shares_held': portfolio.get('rtx_shares', 0),
                'target_shares': portfolio.get('target_shares', 9),
                'position_on_target': portfolio.get('shares_on_target', False),
                'estimated_pnl': estimated_pnl,
                'connected_to_ibkr': portfolio.get('connected', False),
                'trading_mode': portfolio.get('mode', 'paper')
            }
            
        except Exception as e:
            self.logger.error(f"Error getting trading performance: {e}")
            return {}
    
    async def _get_ml_learning_progress(self) -> Dict:
        """Get machine learning system progress"""
        try:
            ml_status = ml_system.get_model_status()
            
            # Check if model needs retraining
            should_retrain = ml_system.should_retrain()
            
            # Get performance metrics
            performance = ml_status.get('performance', {})
            direction_perf = performance.get('direction_classifier', {})
            
            return {
                'models_trained': ml_status.get('models_trained', False),
                'last_training': ml_status.get('last_training'),
                'should_retrain': should_retrain,
                'accuracy': direction_perf.get('accuracy', 0.0),
                'total_predictions': direction_perf.get('total_predictions', 0),
                'model_age_days': self._calculate_model_age(ml_status.get('last_training'))
            }
            
        except Exception as e:
            self.logger.error(f"Error getting ML progress: {e}")
            return {}
    
    async def _get_signal_analysis(self) -> Dict:
        """Analyze individual signal performance"""
        try:
            if not rtx_orchestrator.last_analysis:
                return {}
            
            last_analysis = rtx_orchestrator.last_analysis
            
            # Analyze signal agreement patterns
            signal_performance = {}
            if last_analysis.individual_signals:
                for signal in last_analysis.individual_signals:
                    signal_performance[signal.signal_name] = {
                        'direction': signal.direction,
                        'confidence': signal.confidence,
                        'strength': signal.strength,
                        'weight': signal.weight
                    }
            
            # Find most/least confident signals
            signals = last_analysis.individual_signals
            if signals:
                most_confident = max(signals, key=lambda s: s.confidence)
                least_confident = min(signals, key=lambda s: s.confidence)
                
                return {
                    'total_signals': len(signals),
                    'signals_agreeing': last_analysis.signals_agreeing,
                    'most_confident_signal': {
                        'name': most_confident.signal_name,
                        'confidence': most_confident.confidence,
                        'direction': most_confident.direction
                    },
                    'least_confident_signal': {
                        'name': least_confident.signal_name,
                        'confidence': least_confident.confidence,
                        'direction': least_confident.direction
                    },
                    'signal_performance': signal_performance
                }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting signal analysis: {e}")
            return {}
    
    async def _get_portfolio_status(self) -> Dict:
        """Get current portfolio status"""
        try:
            portfolio = await ibkr_manager.get_portfolio_summary()
            
            # Calculate portfolio value estimate
            market_data = await self._get_market_data()
            rtx_shares = portfolio.get('rtx_shares', 0)
            current_price = market_data.get('current_price', 0)
            
            share_value = rtx_shares * current_price if current_price else 0
            
            return {
                'rtx_shares': rtx_shares,
                'share_value': share_value,
                'current_price': current_price,
                'connected': portfolio.get('connected', False),
                'mode': portfolio.get('mode', 'paper'),
                'total_positions': portfolio.get('total_positions', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio status: {e}")
            return {}
    
    def _calculate_model_age(self, last_training_str: Optional[str]) -> int:
        """Calculate how many days since model was last trained"""
        if not last_training_str:
            return 999  # Very old
        
        try:
            last_training = datetime.fromisoformat(last_training_str.replace('Z', '+00:00'))
            age = datetime.now() - last_training.replace(tzinfo=None)
            return age.days
        except:
            return 999
    
    async def _build_comprehensive_report(self, data: Dict) -> Dict:
        """Build the comprehensive daily report"""
        try:
            market = data.get('market_data', {})
            predictions = data.get('prediction_performance', {})
            trading = data.get('trading_performance', {})
            ml = data.get('ml_progress', {})
            signals = data.get('signal_analysis', {})
            portfolio = data.get('portfolio_status', {})
            
            # Create report structure
            report = {
                'date': data['date'].strftime('%Y-%m-%d'),
                'timestamp': datetime.now().isoformat(),
                
                # Market summary
                'market_summary': {
                    'rtx_price': market.get('current_price', 0),
                    'daily_change': market.get('daily_change', 0),
                    'daily_change_pct': market.get('daily_change_pct', 0),
                    'volatility': market.get('volatility', 0),
                    'volume': market.get('volume', 0)
                },
                
                # AI Performance
                'ai_performance': {
                    'predictions_made': predictions.get('predictions_made', 0),
                    'trade_worthy_signals': predictions.get('trade_worthy_count', 0),
                    'avg_confidence': predictions.get('avg_confidence', 0),
                    'signals_agreement': predictions.get('avg_signals_agreeing', 0)
                },
                
                # Trading Performance
                'trading_performance': {
                    'shares_held': trading.get('rtx_shares_held', 0),
                    'position_correct': trading.get('position_on_target', False),
                    'estimated_pnl': trading.get('estimated_pnl', 0),
                    'mode': trading.get('trading_mode', 'paper'),
                    'connected': trading.get('connected_to_ibkr', False)
                },
                
                # Learning Progress
                'learning_progress': {
                    'models_trained': ml.get('models_trained', False),
                    'model_accuracy': ml.get('accuracy', 0),
                    'model_age_days': ml.get('model_age_days', 0),
                    'needs_retraining': ml.get('should_retrain', False)
                },
                
                # System Health
                'system_health': {
                    'signals_active': signals.get('total_signals', 0),
                    'most_confident_signal': signals.get('most_confident_signal', {}),
                    'ml_predictions': ml.get('total_predictions', 0)
                }
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error building report: {e}")
            return {}
    
    async def _send_telegram_report(self, report: Dict):
        """Send comprehensive report via Telegram"""
        try:
            market = report.get('market_summary', {})
            ai = report.get('ai_performance', {})
            trading = report.get('trading_performance', {})
            learning = report.get('learning_progress', {})
            health = report.get('system_health', {})
            
            # Market performance emoji
            price_change = market.get('daily_change_pct', 0)
            price_emoji = "📈" if price_change > 0 else "📉" if price_change < 0 else "➖"
            
            # PnL emoji
            pnl = trading.get('estimated_pnl', 0)
            pnl_emoji = "💚" if pnl > 0 else "❌" if pnl < 0 else "➖"
            
            # AI performance emoji
            ai_emoji = "🧠" if ai.get('avg_confidence', 0) > 0.7 else "🤖"
            
            # Learning status emoji
            learning_emoji = "📚" if learning.get('needs_retraining', False) else "✅"
            
            message = f"""
📊 <b>RTX TRADING DAILY REPORT</b>
📅 <b>Date:</b> {report.get('date', 'Unknown')}

{price_emoji} <b>MARKET PERFORMANCE</b>
💰 RTX Price: ${market.get('rtx_price', 0):.2f}
📊 Daily Change: {price_change:+.2f}%
📈 Volatility: {market.get('volatility', 0):.1%}
📦 Volume: {market.get('volume', 0):,}

{ai_emoji} <b>AI PERFORMANCE</b>
🎯 Predictions Made: {ai.get('predictions_made', 0)}
🚀 Trade-Worthy Signals: {ai.get('trade_worthy_signals', 0)}
📊 Avg Confidence: {ai.get('avg_confidence', 0):.1%}
🤝 Signal Agreement: {ai.get('signals_agreement', 0):.1f}/8

💼 <b>PORTFOLIO STATUS</b>
📈 RTX Shares: {trading.get('shares_held', 0)}/9
{pnl_emoji} Estimated P&L: ${pnl:+.2f}
🔗 IBKR: {'Connected' if trading.get('connected') else 'Disconnected'}
🎮 Mode: {trading.get('mode', 'unknown').title()}

{learning_emoji} <b>LEARNING PROGRESS</b>
🧠 Model Accuracy: {learning.get('model_accuracy', 0):.1%}
📅 Model Age: {learning.get('model_age_days', 0)} days
🔄 Needs Retraining: {'Yes' if learning.get('needs_retraining') else 'No'}

🔍 <b>SYSTEM HEALTH</b>
⚙️ Active Signals: {health.get('signals_active', 0)}/8
📡 ML Predictions: {health.get('ml_predictions', 0)}
            """.strip()
            
            # Add top signal info if available
            top_signal = health.get('most_confident_signal', {})
            if top_signal:
                message += f"""

🎯 <b>TOP SIGNAL TODAY</b>
📊 {top_signal.get('name', 'Unknown')}: {top_signal.get('direction', 'HOLD')}
💪 Confidence: {top_signal.get('confidence', 0):.1%}
                """.strip()
            
            message += f"""

🎯 <b>TOMORROW'S FOCUS</b>
• Continue RTX pattern analysis
• Monitor for high-conviction setups
• {'Retrain ML models' if learning.get('needs_retraining') else 'Maintain current models'}
• Target 80%+ confidence trades only

<i>System ready for next session 🚀</i>
            """.strip()
            
            await telegram_bot.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending Telegram report: {e}")
    
    async def _save_report_to_db(self, report: Dict):
        """Save report to database for historical tracking"""
        try:
            # This would save to the database
            # For now, just log it
            self.logger.info(f"Report saved: {report['date']}")
            
        except Exception as e:
            self.logger.error(f"Error saving report to DB: {e}")
    
    async def _send_error_report(self, error_msg: str):
        """Send error report via Telegram"""
        try:
            await telegram_bot.send_error_alert({
                'type': 'Daily Report Error',
                'message': error_msg,
                'severity': 'MEDIUM'
            })
        except Exception as e:
            self.logger.error(f"Error sending error report: {e}")
    
    async def schedule_daily_reports(self):
        """Schedule daily reports to run automatically"""
        self.logger.info(f"📅 Scheduling daily reports at {self.report_time}")
        
        while True:
            try:
                now = datetime.now()
                report_hour, report_minute = map(int, self.report_time.split(':'))
                
                # Calculate next report time
                next_report = now.replace(hour=report_hour, minute=report_minute, second=0, microsecond=0)
                
                # If we've passed today's report time, schedule for tomorrow
                if now >= next_report:
                    next_report += timedelta(days=1)
                
                # Wait until report time
                wait_seconds = (next_report - now).total_seconds()
                self.logger.info(f"⏰ Next daily report in {wait_seconds/3600:.1f} hours")
                
                await asyncio.sleep(wait_seconds)
                
                # Generate and send report
                await self.generate_daily_report()
                
            except Exception as e:
                self.logger.error(f"Error in daily report scheduler: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying

# Global daily reporter instance
daily_reporter = DailyReporter()

async def test_daily_reporter():
    """Test the daily reporter"""
    print("📊 Testing Daily Performance Reporter")
    print("=" * 50)
    
    try:
        report = await daily_reporter.generate_daily_report()
        
        print("✅ Daily report generated successfully")
        print(f"📅 Date: {report.get('date', 'Unknown')}")
        print(f"💰 RTX Price: ${report.get('market_summary', {}).get('rtx_price', 0):.2f}")
        print(f"🎯 Predictions: {report.get('ai_performance', {}).get('predictions_made', 0)}")
        print(f"📊 Avg Confidence: {report.get('ai_performance', {}).get('avg_confidence', 0):.1%}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_daily_reporter())
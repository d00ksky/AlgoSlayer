"""
Options Trading Scheduler
Enhanced scheduler that focuses on options predictions and trading
Integrates all AI signals with options-specific logic
"""
import asyncio
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional
from loguru import logger

from config.trading_config import config, TradingModeConfig
from config.options_config import options_config
from src.core.telegram_bot import telegram_bot
from src.core.options_data_engine import options_data_engine
from src.core.options_prediction_engine import options_prediction_engine
from src.core.options_paper_trader import options_paper_trader
from src.core.prediction_outcome_tracker import outcome_tracker

# Import all AI signals
from src.signals.news_sentiment_signal import NewsSentimentSignal
from src.signals.technical_analysis_signal import TechnicalAnalysisSignal
from src.signals.options_flow_signal import OptionsFlowSignal
from src.signals.volatility_analysis_signal import VolatilityAnalysisSignal
from src.signals.momentum_signal import MomentumSignal
from src.signals.sector_correlation_signal import SectorCorrelationSignal
from src.signals.mean_reversion_signal import MeanReversionSignal
from src.signals.market_regime_signal import MarketRegimeSignal

# Import new high-value options signals
from src.signals.trump_geopolitical_signal import TrumpGeopoliticalSignal
from src.signals.defense_contract_signal import DefenseContractSignal
from src.signals.rtx_earnings_signal import RTXEarningsSignal
from src.signals.options_iv_percentile_signal import OptionsIVPercentileSignal

class OptionsScheduler:
    """Advanced scheduler for autonomous RTX options trading"""
    
    def __init__(self):
        self.running = False
        self.start_time = None
        self.trading_mode = TradingModeConfig.load_from_env()
        
        # Initialize AI signals with adaptive weights (12 signals total)
        self.signal_weights = {
            # Classic signals (rebalanced)
            "news_sentiment": 0.10,
            "technical_analysis": 0.12,
            "options_flow": 0.12,
            "volatility_analysis": 0.08,
            "momentum": 0.08,
            "sector_correlation": 0.08,
            "mean_reversion": 0.08,
            "market_regime": 0.10,
            
            # New high-value options signals
            "trump_geopolitical": 0.08,  # Political impact on defense
            "defense_contract": 0.06,    # Government contracts
            "rtx_earnings": 0.05,        # Earnings timing & IV
            "options_iv_percentile": 0.05 # IV rank analysis
        }
        
        self.signals = {
            # Classic signals
            "news_sentiment": NewsSentimentSignal(),
            "technical_analysis": TechnicalAnalysisSignal(),
            "options_flow": OptionsFlowSignal(),
            "volatility_analysis": VolatilityAnalysisSignal(),
            "momentum": MomentumSignal(),
            "sector_correlation": SectorCorrelationSignal(),
            "mean_reversion": MeanReversionSignal(),
            "market_regime": MarketRegimeSignal(),
            
            # New high-value options signals
            "trump_geopolitical": TrumpGeopoliticalSignal(),
            "defense_contract": DefenseContractSignal(),
            "rtx_earnings": RTXEarningsSignal(),
            "options_iv_percentile": OptionsIVPercentileSignal()
        }
        
        # Options trading state
        self.last_options_prediction = None
        self.prediction_count = 0
        self.cycle_count = 0
        
        logger.info("🎯 Options Trading Scheduler initialized")
        logger.info(f"📊 Mode: {self.trading_mode.get_mode_description()}")
        logger.info(f"💰 Starting balance: ${options_paper_trader.account_balance:.2f}")
    
    async def start_autonomous_trading(self):
        """Start the main autonomous trading loop"""
        
        if self.running:
            logger.warning("⚠️ Scheduler already running")
            return
        
        self.running = True
        self.start_time = datetime.now()
        
        logger.info("🚀 Starting autonomous options trading")
        await telegram_bot.send_message(
            "🚀 **RTX Options Trading Started**\n\n"
            f"Mode: {self.trading_mode.get_mode_description()}\n"
            f"Balance: ${options_paper_trader.account_balance:.2f}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        try:
            # Start Telegram listener as background task
            telegram_task = asyncio.create_task(telegram_bot.process_incoming_messages())
            logger.info("📱 Started Telegram command listener")
            
            while self.running:
                # Check if market is open
                if not options_config.is_market_hours():
                    logger.info("⏰ Market closed - sleeping")
                    await asyncio.sleep(300)  # Check every 5 minutes
                    continue
                
                # Run trading cycle
                await self._run_trading_cycle()
                
                # Wait for next cycle (15 minutes)
                await asyncio.sleep(900)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Keyboard interrupt received")
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
            await telegram_bot.send_message(f"🚨 **Scheduler Error:** {e}")
        finally:
            self.running = False
            # Cancel Telegram listener task
            if 'telegram_task' in locals():
                telegram_task.cancel()
                try:
                    await telegram_task
                except asyncio.CancelledError:
                    pass
            logger.info("⏹️ Autonomous trading stopped")
    
    async def _run_trading_cycle(self):
        """Run a complete trading cycle"""
        
        self.cycle_count += 1
        cycle_start = datetime.now()
        
        logger.info(f"🔄 Starting trading cycle #{self.cycle_count}")
        
        try:
            # Step 1: Check existing positions
            await self._check_existing_positions()
            
            # Step 2: Track prediction outcomes (every 5th cycle)
            if self.cycle_count % 5 == 0:
                asyncio.create_task(outcome_tracker.track_all_outcomes())
            
            # Step 3: Generate new signals
            signals_data = await self._generate_signals()
            
            if not signals_data:
                logger.warning("⚠️ No signals generated")
                return
            
            # Step 3: Create options prediction
            prediction = await self._create_options_prediction(signals_data)
            
            if prediction:
                # Step 4: Execute trade (if conditions are met)
                await self._execute_options_trade(prediction)
            
            # Step 5: Send status update
            await self._send_cycle_update(signals_data, prediction)
            
        except Exception as e:
            logger.error(f"❌ Trading cycle error: {e}")
            await telegram_bot.send_message(f"🚨 **Cycle Error:** {e}")
        
        cycle_duration = (datetime.now() - cycle_start).total_seconds()
        logger.info(f"✅ Trading cycle #{self.cycle_count} completed in {cycle_duration:.1f}s")
    
    async def _check_existing_positions(self):
        """Check and manage existing positions"""
        
        if not options_paper_trader.open_positions:
            return
        
        logger.info(f"📊 Checking {len(options_paper_trader.open_positions)} open positions")
        
        # Check all positions for exit conditions
        actions = options_paper_trader.check_positions()
        
        if actions:
            for action in actions:
                logger.info(f"📈 Position action: {action}")
                await telegram_bot.send_message(f"📈 **Position Update**\n{action}")
    
    async def _generate_signals(self) -> Optional[Dict]:
        """Generate and aggregate all AI signals"""
        
        logger.info("🤖 Generating AI signals...")
        
        signal_results = {}
        successful_signals = 0
        
        # Run all signals in parallel for speed
        signal_tasks = []
        
        for signal_name, signal_instance in self.signals.items():
            task = asyncio.create_task(
                self._run_single_signal(signal_name, signal_instance),
                name=signal_name
            )
            signal_tasks.append(task)
        
        # Wait for all signals to complete
        results = await asyncio.gather(*signal_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            signal_name = list(self.signals.keys())[i]
            
            if isinstance(result, Exception):
                logger.error(f"❌ Signal {signal_name} failed: {result}")
                signal_results[signal_name] = {
                    "direction": "HOLD",
                    "confidence": 0.5,
                    "strength": 0.0,
                    "error": str(result)
                }
            else:
                signal_results[signal_name] = result
                if result.get("direction") != "HOLD":
                    successful_signals += 1
        
        if successful_signals == 0:
            logger.warning("⚠️ No actionable signals generated")
            return None
        
        # Aggregate signals using weighted voting
        aggregated = self._aggregate_signals(signal_results)
        
        logger.success(f"✅ Generated {successful_signals}/{len(self.signals)} actionable signals")
        
        return {
            "individual_signals": signal_results,
            "signal_weights": self.signal_weights,
            "signals_agreeing": successful_signals,
            "total_signals": len(self.signals),
            **aggregated
        }
    
    async def _run_single_signal(self, name: str, signal_instance) -> Dict:
        """Run a single signal with error handling"""
        
        try:
            result = await signal_instance.analyze("RTX")
            
            # Ensure result has required fields
            if not isinstance(result, dict):
                raise ValueError(f"Signal {name} returned invalid format")
            
            result.setdefault("direction", "HOLD")
            result.setdefault("confidence", 0.5)
            result.setdefault("strength", 0.1)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Signal {name} error: {e}")
            return {
                "direction": "HOLD",
                "confidence": 0.5,
                "strength": 0.0,
                "error": str(e)
            }
    
    def _aggregate_signals(self, signal_results: Dict) -> Dict:
        """Aggregate signals using weighted voting with options-specific logic"""
        
        buy_strength = 0.0
        sell_strength = 0.0
        total_confidence = 0.0
        
        for signal_name, result in signal_results.items():
            if "error" in result:
                continue
            
            direction = result.get("direction", "HOLD")
            strength = result.get("strength", 0.1)
            confidence = result.get("confidence", 0.5)
            weight = self.signal_weights.get(signal_name, 0.1)
            
            # Apply weight to strength
            weighted_strength = strength * weight
            
            if direction == "BUY":
                buy_strength += weighted_strength
            elif direction == "SELL":
                sell_strength += weighted_strength
            
            total_confidence += confidence * weight
        
        # Determine final direction - higher threshold for options
        strength_diff = abs(buy_strength - sell_strength)
        min_strength = 0.35  # Higher than stock trading
        min_agreement = 0.25  # Require stronger agreement
        
        if buy_strength > sell_strength and buy_strength > min_strength and strength_diff > min_agreement:
            final_direction = "BUY"
            final_confidence = min(0.95, buy_strength / (buy_strength + sell_strength + 0.1))
        elif sell_strength > buy_strength and sell_strength > min_strength and strength_diff > min_agreement:
            final_direction = "SELL"
            final_confidence = min(0.95, sell_strength / (buy_strength + sell_strength + 0.1))
        else:
            final_direction = "HOLD"
            final_confidence = 0.5
        
        # Calculate expected move based on signal strength
        expected_move = min(0.08, strength_diff * 2)  # Max 8% expected move
        
        return {
            "direction": final_direction,
            "confidence": final_confidence,
            "expected_move": expected_move,
            "buy_strength": buy_strength,
            "sell_strength": sell_strength
        }
    
    async def _create_options_prediction(self, signals_data: Dict) -> Optional[Dict]:
        """Create options-specific prediction"""
        
        if signals_data["direction"] == "HOLD":
            return None
        
        if signals_data["confidence"] < 0.75:  # Higher threshold for options
            logger.info(f"📊 Confidence {signals_data['confidence']:.1%} below 75% options threshold")
            return None
        
        # Generate options prediction
        prediction = options_prediction_engine.generate_options_prediction(
            signals_data, options_paper_trader.account_balance
        )
        
        if prediction:
            self.last_options_prediction = prediction
            self.prediction_count += 1
            logger.success(f"🎯 Options prediction #{self.prediction_count}: {prediction['action']}")
        
        return prediction
    
    async def _execute_options_trade(self, prediction: Dict):
        """Execute options trade based on prediction"""
        
        if not self.trading_mode.trading_enabled:
            logger.info("📊 Trading disabled - prediction only mode")
            return
        
        # Check if we should limit position count
        if len(options_paper_trader.open_positions) >= 3:  # Max 3 concurrent positions
            logger.info("📊 Maximum positions reached - skipping trade")
            return
        
        # Execute the trade
        success = options_paper_trader.open_position(prediction)
        
        if success:
            await telegram_bot.send_message(
                f"🎯 **OPTIONS TRADE EXECUTED**\n\n"
                f"📊 **Contract Details:**\n"
                f"• Action: {prediction['action']}\n"
                f"• Contract: {prediction['contract_symbol']}\n"
                f"• Type: {prediction['option_type'].upper()}\n"
                f"• Strike: ${prediction['strike']}\n"
                f"• Expiry: {prediction['expiry']} ({prediction['days_to_expiry']}d)\n\n"
                f"💰 **Trade Details:**\n"
                f"• Contracts: {prediction['contracts']}x\n"
                f"• Entry Price: ${prediction['entry_price']:.2f} (Ask)\n"
                f"• Total Cost: ${prediction['total_cost']:.2f}\n"
                f"• Commission: ${prediction['commission']:.2f}\n\n"
                f"📈 **Greeks & Analytics:**\n"
                f"• Delta: {prediction['delta']:.3f}\n"
                f"• IV: {prediction['implied_volatility']*100:.1f}%\n"
                f"• Confidence: {prediction['confidence']:.1f}%\n"
                f"• Expected Profit: {prediction['expected_profit_pct']:.1f}%\n\n"
                f"🎯 **Exit Strategy:**\n"
                f"• Target: ${prediction['profit_target_price']:.2f} (+100%)\n"
                f"• Stop Loss: ${prediction['stop_loss_price']:.2f} (-50%)\n"
                f"• Time Exit: {prediction['exit_before_expiry_days']}d before expiry"
            )
        else:
            await telegram_bot.send_message(
                f"❌ **Trade Failed**\n\n"
                f"Could not execute: {prediction['contract_symbol']}"
            )
    
    async def _send_cycle_update(self, signals_data: Dict, prediction: Optional[Dict]):
        """Send cycle status update"""
        
        # Only send updates every 4 cycles (hourly) to avoid spam
        if self.cycle_count % 4 != 0:
            return
        
        # Get performance summary
        performance = options_paper_trader.get_performance_summary()
        open_positions = options_paper_trader.get_open_positions_summary()
        
        message = f"📊 **Hourly Update #{self.cycle_count // 4}**\n\n"
        
        # Account status
        message += f"💰 **Account**: ${performance['account_balance']:.2f} "
        message += f"({performance['total_return']:+.2f}, {performance['total_return_pct']:+.1%})\n\n"
        
        # Current prediction
        if prediction:
            message += f"🎯 **Latest Signal**: {prediction['action']} "
            message += f"{prediction['contract_symbol']} ({prediction['confidence']:.1f}%)\n\n"
        else:
            message += f"🎯 **Latest Signal**: {signals_data['direction']} "
            message += f"({signals_data['confidence']:.1f}%) - No options trade\n\n"
        
        # Open positions
        if open_positions:
            message += f"📈 **Open Positions** ({len(open_positions)}):  \n"
            for pos in open_positions[:3]:  # Show up to 3
                pnl_emoji = "💰" if pos['unrealized_pnl'] > 0 else "💸"
                message += f"{pnl_emoji} {pos['contract_symbol']}: {pos['unrealized_pnl']:+.0f} ({pos['unrealized_pnl_pct']:+.1f}%)\n"
            message += "\n"
        
        # Performance stats
        if performance['total_trades'] > 0:
            message += f"📊 **Performance**: {performance['win_rate']:.1f}% win rate, "
            message += f"{performance['total_trades']} trades, "
            message += f"PF: {performance['profit_factor']:.1f}"
        
        await telegram_bot.send_message(message)
    
    def stop(self):
        """Stop the trading scheduler"""
        self.running = False
        logger.info("⏹️ Stop signal sent to scheduler")
    
    def get_status(self) -> Dict:
        """Get current scheduler status"""
        
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            "running": self.running,
            "uptime_seconds": uptime,
            "cycle_count": self.cycle_count,
            "prediction_count": self.prediction_count,
            "last_prediction": self.last_options_prediction,
            "open_positions": len(options_paper_trader.open_positions),
            "account_balance": options_paper_trader.account_balance,
            "performance": options_paper_trader.get_performance_summary()
        }

# Create global instance
options_scheduler = OptionsScheduler()

if __name__ == "__main__":
    # Test the scheduler
    logger.info("🧪 Testing Options Scheduler...")
    
    async def test_scheduler():
        scheduler = OptionsScheduler()
        
        # Test signal generation
        signals = await scheduler._generate_signals()
        if signals:
            print(f"Generated signals: {signals['direction']} ({signals['confidence']:.1%})")
            
            # Test prediction creation
            prediction = await scheduler._create_options_prediction(signals)
            if prediction:
                print(f"Generated prediction: {prediction['contract_symbol']}")
    
    asyncio.run(test_scheduler())
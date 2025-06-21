#!/usr/bin/env python3
"""
Parallel Strategy Runner
Runs multiple trading strategies simultaneously with independent decision making
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger
from copy import deepcopy

from src.core.multi_strategy_manager import MultiStrategyManager, StrategyConfig
from src.core.options_scheduler import OptionsScheduler
from src.core.options_prediction_engine import OptionsPredictionEngine
from src.core.options_paper_trader import OptionsPaperTrader
from src.core.telegram_bot import telegram_bot
from src.core.adaptive_learning_system import AdaptiveLearningSystem
from src.core.dynamic_thresholds import dynamic_threshold_manager
from src.core.dashboard import dashboard
from src.core.kelly_position_sizer import kelly_sizer
from config.trading_config import config as base_config
from config.options_config import options_config

class StrategyInstance:
    """Independent instance of a trading strategy"""
    
    def __init__(self, strategy_id: str, strategy_config: StrategyConfig, initial_balance: float = 1000.0):
        self.strategy_id = strategy_id
        self.strategy_config = strategy_config
        self.balance = initial_balance
        
        # Create independent paper trader for this strategy
        self.paper_trader = OptionsPaperTrader(
            initial_balance=initial_balance,
            db_suffix=f"_{strategy_id}"  # Separate DB for each strategy
        )
        
        # Create prediction engine with strategy-specific config
        self.prediction_engine = OptionsPredictionEngine()
        
        # Track predictions for this strategy
        self.predictions_made = 0
        self.last_prediction = None
        
        logger.info(f"🎯 Initialized {strategy_config.name} strategy with ${initial_balance}")
        
    def update_config(self, confidence: float, min_signals: int, position_size: float):
        """Update strategy configuration dynamically"""
        self.strategy_config.confidence_threshold = confidence
        self.strategy_config.min_signals_required = min_signals
        self.strategy_config.position_size_pct = position_size
        
    def update_signal_weights(self, weights: Dict[str, float]):
        """Update signal weights from ML optimization"""
        self.strategy_config.signal_weights = weights

class ParallelStrategyRunner:
    """Run multiple strategies in parallel with shared market data"""
    
    def __init__(self):
        self.manager = MultiStrategyManager()
        self.strategies = {}
        self.scheduler = OptionsScheduler()  # Shared scheduler for signals
        self.ml_system = AdaptiveLearningSystem()
        self.running = False
        
        # Initialize strategy instances
        self._init_strategies()
        
    def _init_strategies(self):
        """Initialize all strategy instances"""
        for strategy_id in ["conservative", "moderate", "aggressive"]:
            config, state = self.manager.get_strategy_config(strategy_id)
            
            # Create strategy instance with current balance
            instance = StrategyInstance(
                strategy_id=strategy_id,
                strategy_config=config,
                initial_balance=state["balance"]
            )
            
            # Apply ML-optimized weights if available
            if state.get("signal_weights"):
                instance.update_signal_weights(state["signal_weights"])
                
            self.strategies[strategy_id] = instance
            
    async def start_parallel_trading(self):
        """Start all strategies trading in parallel"""
        if self.running:
            logger.warning("⚠️ Parallel runner already active")
            return
            
        self.running = True
        logger.info("🚀 Starting parallel multi-strategy trading")
        
        # Send startup notification
        await self._send_startup_notification()
        
        try:
            while self.running:
                # Check if market is open
                if not options_config.is_market_hours():
                    logger.info("⏰ Market closed - sleeping")
                    await asyncio.sleep(300)  # 5 minutes
                    continue
                    
                # Run trading cycle for all strategies
                await self._run_parallel_cycle()
                
                # Run ML optimization every 10 cycles
                if hasattr(self, 'cycle_count') and self.cycle_count % 10 == 0:
                    await self._run_ml_optimization()
                    
                # Send periodic updates every hour
                if hasattr(self, 'cycle_count') and self.cycle_count % 4 == 0:
                    await self._send_performance_update()
                    
                # Send full dashboard every 4 hours (16 cycles at 15min intervals)
                if hasattr(self, 'cycle_count') and self.cycle_count % 16 == 0:
                    await self._send_dashboard_update()
                    
                # Sleep until next cycle
                await asyncio.sleep(base_config.PREDICTION_INTERVAL_MINUTES * 60)
                
        except Exception as e:
            logger.error(f"❌ Parallel trading error: {e}")
            await telegram_bot.send_message(f"❌ Multi-strategy error: {str(e)}")
            
    async def _run_parallel_cycle(self):
        """Run one trading cycle for all strategies in parallel"""
        self.cycle_count = getattr(self, 'cycle_count', 0) + 1
        logger.info(f"🔄 Parallel cycle #{self.cycle_count}")
        
        # Step 1: Generate signals (shared across all strategies)
        signals_data = await self.scheduler._generate_signals()
        
        if not signals_data or signals_data.get("direction") == "HOLD":
            logger.info("📊 No actionable signals - all strategies holding")
            return
            
        # Step 2: Each strategy makes independent decisions
        tasks = []
        for strategy_id, instance in self.strategies.items():
            task = self._process_strategy_decision(
                strategy_id, instance, signals_data
            )
            tasks.append(task)
            
        # Run all strategies in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log results
        for strategy_id, result in zip(self.strategies.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"❌ {strategy_id} error: {result}")
            elif result:
                logger.success(f"✅ {strategy_id}: {result}")
                
    async def _process_strategy_decision(self, strategy_id: str, instance: StrategyInstance, signals_data: Dict) -> Optional[str]:
        """Process trading decision for a single strategy"""
        try:
            config = instance.strategy_config
            
            # Check if signals meet strategy requirements
            confidence = signals_data.get("confidence", 0)
            signals_agreeing = signals_data.get("signals_agreeing", 0)
            
            # Get dynamic confidence threshold
            dynamic_threshold, threshold_reason = dynamic_threshold_manager.calculate_optimal_threshold(strategy_id)
            
            # Update the instance config with dynamic threshold
            original_threshold = config.confidence_threshold
            config.confidence_threshold = dynamic_threshold
            
            logger.info(f"🎯 {config.name}: Confidence {confidence:.1%}, Dynamic threshold: {dynamic_threshold:.1%} (was {original_threshold:.1%}, reason: {threshold_reason}), Signals agreeing: {signals_agreeing}")
            
            # Apply dynamic threshold
            if confidence < dynamic_threshold:
                return f"Below dynamic threshold ({confidence:.1%} < {dynamic_threshold:.1%}, reason: {threshold_reason})"
                
            if signals_agreeing < config.min_signals_required:
                return f"Insufficient signals ({signals_agreeing} < {config.min_signals_required})"
                
            # Get Kelly-optimized position size
            kelly_size, kelly_reason, kelly_metrics = kelly_sizer.calculate_optimal_position_size(strategy_id)
            
            logger.info(f"🎯 {config.name}: Kelly position size {kelly_size:.1%} (reason: {kelly_reason})")
            
            # Generate prediction with Kelly-optimized position size
            prediction = await self._generate_strategy_prediction(
                instance, signals_data, kelly_size
            )
            
            if prediction and isinstance(prediction, dict) and "id" in prediction:
                # Execute trade
                instance.paper_trader.open_position(prediction)
                
                # Record prediction for tracking
                self.manager.record_prediction(strategy_id, prediction["id"])
                instance.predictions_made += 1
                instance.last_prediction = prediction
                
                # Update balance
                new_balance = instance.paper_trader.account_balance
                self.manager.update_strategy_balance(
                    strategy_id, new_balance, 
                    {"profitable": False}  # Will be updated when trade closes
                )
                
                return f"Executed: {prediction['contract_symbol']} @ ${prediction['entry_price']:.2f}"
            else:
                return "No suitable options found"
                
        except Exception as e:
            logger.error(f"❌ Strategy {strategy_id} error: {e}")
            return f"Error: {str(e)}"
            
    async def _generate_strategy_prediction(self, instance: StrategyInstance, signals_data: Dict, position_size_pct: float) -> Optional[Dict]:
        """Generate prediction with strategy-specific parameters"""
        # Override position size for this prediction
        original_max = base_config.MAX_POSITION_SIZE
        base_config.MAX_POSITION_SIZE = int(instance.balance * position_size_pct)
        
        try:
            # Use strategy's signal weights if available
            if instance.strategy_config.signal_weights:
                # Apply custom weights to signals
                weighted_signals = self._apply_custom_weights(
                    signals_data, instance.strategy_config.signal_weights
                )
                prediction = instance.prediction_engine.generate_options_prediction(
                    weighted_signals, instance.balance, instance.strategy_id
                )
            else:
                prediction = instance.prediction_engine.generate_options_prediction(
                    signals_data, instance.balance, instance.strategy_id
                )
                
            return prediction
            
        finally:
            # Restore original position size
            base_config.MAX_POSITION_SIZE = original_max
            
    def _apply_custom_weights(self, signals_data: Dict, weights: Dict[str, float]) -> Dict:
        """Apply custom signal weights to signals data"""
        # This would recalculate confidence based on custom weights
        # For now, return original (can be enhanced)
        return signals_data
        
    async def _run_ml_optimization(self):
        """Run ML optimization for each strategy"""
        logger.info("🧠 Running ML optimization for all strategies")
        
        for strategy_id, instance in self.strategies.items():
            try:
                # Get performance data for this strategy
                analysis = self.ml_system.analyze_signal_performance(
                    strategy_filter=strategy_id
                )
                
                if analysis["total_trades"] >= 5:  # Need minimum trades
                    # Generate optimized weights
                    optimized = self.ml_system.generate_adaptive_weights(
                        strategy_filter=strategy_id
                    )
                    
                    if optimized["status"] == "success":
                        # Apply new weights
                        new_weights = optimized["optimized_weights"]
                        instance.update_signal_weights(new_weights)
                        self.manager.apply_ml_optimization(strategy_id, new_weights)
                        
                        logger.success(f"✅ Applied ML optimization to {instance.strategy_config.name}")
                        
            except Exception as e:
                logger.error(f"❌ ML optimization error for {strategy_id}: {e}")
                
    async def _send_startup_notification(self):
        """Send notification when starting parallel trading"""
        leaderboard = self.manager.get_leaderboard()
        
        message = "🚀 **Multi-Strategy Trading Started**\n\n"
        message += "📊 **Current Standings:**\n"
        
        for entry in leaderboard:
            emoji = "🥇" if entry["rank"] == 1 else "🥈" if entry["rank"] == 2 else "🥉"
            message += f"{emoji} {entry['strategy']}: ${entry['balance']:.2f} ({entry['status']})\n"
            
        message += "\n🎯 **Active Strategies:**\n"
        message += "• Conservative: 75% conf, 4+ signals\n"
        message += "• Moderate: 60% conf, 3+ signals\n" 
        message += "• Aggressive: 50% conf, 2+ signals\n"
        message += "\nMay the best strategy win! 🏆"
        
        await telegram_bot.send_message(message)
        
    async def _send_performance_update(self):
        """Send periodic performance update with dashboard"""
        try:
            # Get dashboard summary for quick update
            quick_summary = dashboard.get_quick_summary()
            
            message = "📊 **Multi-Strategy Performance Update**\n\n"
            message += quick_summary + "\n\n"
            
            # Add dynamic threshold status
            message += dynamic_threshold_manager.get_threshold_summary()
            
            # Add Kelly position sizing summary
            message += "\n" + kelly_sizer.get_kelly_summary()
            
            # Add insights from manager if available
            report = self.manager.get_comparison_report()
            if report.get("insights"):
                message += "\n💡 **Insights:**\n"
                for insight in report["insights"][:2]:  # Limit to 2 for space
                    message += f"• {insight}\n"
                    
            message += "\n💡 Use /dashboard for full details"
                
            await telegram_bot.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Performance update error: {e}")
            # Fallback to basic update
            await telegram_bot.send_message(f"📊 Performance update error: {str(e)}")
            
    async def _send_dashboard_update(self):
        """Send full dashboard update (less frequent)"""
        try:
            full_dashboard = dashboard.generate_dashboard()
            
            # Check if message is too long for Telegram (4096 char limit)
            if len(full_dashboard) > 4000:
                # Send in parts
                await telegram_bot.send_message("📊 **Live Dashboard** (Part 1/2)")
                await telegram_bot.send_message(full_dashboard[:2000])
                await asyncio.sleep(1)
                await telegram_bot.send_message("📊 **Live Dashboard** (Part 2/2)")
                await telegram_bot.send_message(full_dashboard[2000:4000])
            else:
                await telegram_bot.send_message(full_dashboard)
                
        except Exception as e:
            logger.error(f"❌ Dashboard update error: {e}")
            await telegram_bot.send_message(f"❌ Dashboard error: {str(e)}")
        
    def stop(self):
        """Stop parallel trading"""
        self.running = False
        logger.info("⏹️ Stopping parallel strategy runner")

if __name__ == "__main__":
    # Test the parallel runner
    runner = ParallelStrategyRunner()
    
    # Show initial state
    print("🎯 Parallel Strategy Runner Test")
    print("="*50)
    
    for strategy_id, instance in runner.strategies.items():
        config = instance.strategy_config
        print(f"\n{config.name}:")
        print(f"  Confidence: {config.confidence_threshold:.0%}")
        print(f"  Min Signals: {config.min_signals_required}")
        print(f"  Position Size: {config.position_size_pct:.0%}")
        print(f"  Balance: ${instance.balance:.2f}")
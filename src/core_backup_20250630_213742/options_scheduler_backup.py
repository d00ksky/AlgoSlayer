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

# Import all AI signals
from src.signals.news_sentiment_signal import NewsSentimentSignal
from src.signals.technical_analysis_signal import TechnicalAnalysisSignal
from src.signals.options_flow_signal import OptionsFlowSignal
from src.signals.volatility_analysis_signal import VolatilityAnalysisSignal
from src.signals.momentum_signal import MomentumSignal
from src.signals.sector_correlation_signal import SectorCorrelationSignal
from src.signals.mean_reversion_signal import MeanReversionSignal
from src.signals.market_regime_signal import MarketRegimeSignal

class OptionsScheduler:
    """Advanced scheduler for autonomous RTX options trading"""
    
    def __init__(self):
        self.running = False
        self.start_time = None
        self.trading_mode = TradingModeConfig.load_from_env()
        
        # Initialize AI signals with adaptive weights
        self.signal_weights = {
            "news_sentiment": 0.15,
            "technical_analysis": 0.15,
            "options_flow": 0.15,
            "volatility_analysis": 0.10,
            "momentum": 0.10,
            "sector_correlation": 0.10,
            "mean_reversion": 0.10,
            "market_regime": 0.15
        }
        
        self.signals = {
            "news_sentiment": NewsSentimentSignal(),
            "technical_analysis": TechnicalAnalysisSignal(),
            "options_flow": OptionsFlowSignal(),
            "volatility_analysis": VolatilityAnalysisSignal(),
            "momentum": MomentumSignal(),
            "sector_correlation": SectorCorrelationSignal(),
            "mean_reversion": MeanReversionSignal(),
            "market_regime": MarketRegimeSignal()
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
            logger.info("⏹️ Autonomous trading stopped")
    
    async def _run_trading_cycle(self):
        """Run a complete trading cycle"""
        
        self.cycle_count += 1
        cycle_start = datetime.now()
        
        logger.info(f"🔄 Starting trading cycle #{self.cycle_count}")
        
        try:
            # Step 1: Check existing positions
            await self._check_existing_positions()
            
            # Step 2: Generate new signals
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
                await telegram_bot.send_message(f"📈 **Position Update**\n{action}")\n    \n    async def _generate_signals(self) -> Optional[Dict]:\n        \"\"\"Generate and aggregate all AI signals\"\"\"\n        \n        logger.info(\"🤖 Generating AI signals...\")\n        \n        signal_results = {}\n        successful_signals = 0\n        \n        # Run all signals in parallel for speed\n        signal_tasks = []\n        \n        for signal_name, signal_instance in self.signals.items():\n            task = asyncio.create_task(\n                self._run_single_signal(signal_name, signal_instance),\n                name=signal_name\n            )\n            signal_tasks.append(task)\n        \n        # Wait for all signals to complete\n        results = await asyncio.gather(*signal_tasks, return_exceptions=True)\n        \n        for i, result in enumerate(results):\n            signal_name = list(self.signals.keys())[i]\n            \n            if isinstance(result, Exception):\n                logger.error(f\"❌ Signal {signal_name} failed: {result}\")\n                signal_results[signal_name] = {\n                    \"direction\": \"HOLD\",\n                    \"confidence\": 0.5,\n                    \"strength\": 0.0,\n                    \"error\": str(result)\n                }\n            else:\n                signal_results[signal_name] = result\n                if result.get(\"direction\") != \"HOLD\":\n                    successful_signals += 1\n        \n        if successful_signals == 0:\n            logger.warning(\"⚠️ No actionable signals generated\")\n            return None\n        \n        # Aggregate signals using weighted voting\n        aggregated = self._aggregate_signals(signal_results)\n        \n        logger.success(f\"✅ Generated {successful_signals}/{len(self.signals)} actionable signals\")\n        \n        return {\n            \"individual_signals\": signal_results,\n            \"signal_weights\": self.signal_weights,\n            \"signals_agreeing\": successful_signals,\n            \"total_signals\": len(self.signals),\n            **aggregated\n        }\n    \n    async def _run_single_signal(self, name: str, signal_instance) -> Dict:\n        \"\"\"Run a single signal with error handling\"\"\"\n        \n        try:\n            result = await signal_instance.analyze(\"RTX\")\n            \n            # Ensure result has required fields\n            if not isinstance(result, dict):\n                raise ValueError(f\"Signal {name} returned invalid format\")\n            \n            result.setdefault(\"direction\", \"HOLD\")\n            result.setdefault(\"confidence\", 0.5)\n            result.setdefault(\"strength\", 0.1)\n            \n            return result\n            \n        except Exception as e:\n            logger.error(f\"❌ Signal {name} error: {e}\")\n            return {\n                \"direction\": \"HOLD\",\n                \"confidence\": 0.5,\n                \"strength\": 0.0,\n                \"error\": str(e)\n            }\n    \n    def _aggregate_signals(self, signal_results: Dict) -> Dict:\n        \"\"\"Aggregate signals using weighted voting with options-specific logic\"\"\"\n        \n        buy_strength = 0.0\n        sell_strength = 0.0\n        total_confidence = 0.0\n        \n        for signal_name, result in signal_results.items():\n            if \"error\" in result:\n                continue\n            \n            direction = result.get(\"direction\", \"HOLD\")\n            strength = result.get(\"strength\", 0.1)\n            confidence = result.get(\"confidence\", 0.5)\n            weight = self.signal_weights.get(signal_name, 0.1)\n            \n            # Apply weight to strength\n            weighted_strength = strength * weight\n            \n            if direction == \"BUY\":\n                buy_strength += weighted_strength\n            elif direction == \"SELL\":\n                sell_strength += weighted_strength\n            \n            total_confidence += confidence * weight\n        \n        # Determine final direction - higher threshold for options\n        strength_diff = abs(buy_strength - sell_strength)\n        min_strength = 0.35  # Higher than stock trading\n        min_agreement = 0.25  # Require stronger agreement\n        \n        if buy_strength > sell_strength and buy_strength > min_strength and strength_diff > min_agreement:\n            final_direction = \"BUY\"\n            final_confidence = min(0.95, buy_strength / (buy_strength + sell_strength + 0.1))\n        elif sell_strength > buy_strength and sell_strength > min_strength and strength_diff > min_agreement:\n            final_direction = \"SELL\"\n            final_confidence = min(0.95, sell_strength / (buy_strength + sell_strength + 0.1))\n        else:\n            final_direction = \"HOLD\"\n            final_confidence = 0.5\n        \n        # Calculate expected move based on signal strength\n        expected_move = min(0.08, strength_diff * 2)  # Max 8% expected move\n        \n        return {\n            \"direction\": final_direction,\n            \"confidence\": final_confidence,\n            \"expected_move\": expected_move,\n            \"buy_strength\": buy_strength,\n            \"sell_strength\": sell_strength\n        }\n    \n    async def _create_options_prediction(self, signals_data: Dict) -> Optional[Dict]:\n        \"\"\"Create options-specific prediction\"\"\"\n        \n        if signals_data[\"direction\"] == \"HOLD\":\n            return None\n        \n        if signals_data[\"confidence\"] < 0.75:  # Higher threshold for options\n            logger.info(f\"📊 Confidence {signals_data['confidence']:.1%} below 75% options threshold\")\n            return None\n        \n        # Generate options prediction\n        prediction = options_prediction_engine.generate_options_prediction(\n            signals_data, options_paper_trader.account_balance\n        )\n        \n        if prediction:\n            self.last_options_prediction = prediction\n            self.prediction_count += 1\n            logger.success(f\"🎯 Options prediction #{self.prediction_count}: {prediction['action']}\")\n        \n        return prediction\n    \n    async def _execute_options_trade(self, prediction: Dict):\n        \"\"\"Execute options trade based on prediction\"\"\"\n        \n        if not self.trading_mode.trading_enabled:\n            logger.info(\"📊 Trading disabled - prediction only mode\")\n            return\n        \n        # Check if we should limit position count\n        if len(options_paper_trader.open_positions) >= 3:  # Max 3 concurrent positions\n            logger.info(\"📊 Maximum positions reached - skipping trade\")\n            return\n        \n        # Execute the trade\n        success = options_paper_trader.open_position(prediction)\n        \n        if success:\n            await telegram_bot.send_message(\n                f\"📈 **Options Trade Executed**\\n\\n\"\n                f\"Action: {prediction['action']}\\n\"\n                f\"Contract: {prediction['contract_symbol']}\\n\"\n                f\"Contracts: {prediction['contracts']}\\n\"\n                f\"Entry: ${prediction['entry_price']:.2f}\\n\"\n                f\"Total Cost: ${prediction['total_cost']:.2f}\\n\"\n                f\"Confidence: {prediction['confidence']:.1%}\\n\"\n                f\"Expected Profit: {prediction['expected_profit_pct']:.1%}\"\n            )\n        else:\n            await telegram_bot.send_message(\n                f\"❌ **Trade Failed**\\n\\n\"\n                f\"Could not execute: {prediction['contract_symbol']}\"\n            )\n    \n    async def _send_cycle_update(self, signals_data: Dict, prediction: Optional[Dict]):\n        \"\"\"Send cycle status update\"\"\"\n        \n        # Only send updates every 4 cycles (hourly) to avoid spam\n        if self.cycle_count % 4 != 0:\n            return\n        \n        # Get performance summary\n        performance = options_paper_trader.get_performance_summary()\n        open_positions = options_paper_trader.get_open_positions_summary()\n        \n        message = f\"📊 **Hourly Update #{self.cycle_count // 4}**\\n\\n\"\n        \n        # Account status\n        message += f\"💰 **Account**: ${performance['account_balance']:.2f} \"\n        message += f\"({performance['total_return']:+.2f}, {performance['total_return_pct']:+.1%})\\n\\n\"\n        \n        # Current prediction\n        if prediction:\n            message += f\"🎯 **Latest Signal**: {prediction['action']} \"\n            message += f\"{prediction['contract_symbol']} ({prediction['confidence']:.1%})\\n\\n\"\n        else:\n            message += f\"🎯 **Latest Signal**: {signals_data['direction']} \"\n            message += f\"({signals_data['confidence']:.1%}) - No options trade\\n\\n\"\n        \n        # Open positions\n        if open_positions:\n            message += f\"📈 **Open Positions** ({len(open_positions)}):  \\n\"\n            for pos in open_positions[:3]:  # Show up to 3\n                pnl_emoji = \"💰\" if pos['unrealized_pnl'] > 0 else \"💸\"\n                message += f\"{pnl_emoji} {pos['contract_symbol']}: {pos['unrealized_pnl']:+.0f} ({pos['unrealized_pnl_pct']:+.1%})\\n\"\n            message += \"\\n\"\n        \n        # Performance stats\n        if performance['total_trades'] > 0:\n            message += f\"📊 **Performance**: {performance['win_rate']:.1%} win rate, \"\n            message += f\"{performance['total_trades']} trades, \"\n            message += f\"PF: {performance['profit_factor']:.1f}\"\n        \n        await telegram_bot.send_message(message)\n    \n    def stop(self):\n        \"\"\"Stop the trading scheduler\"\"\"\n        self.running = False\n        logger.info(\"⏹️ Stop signal sent to scheduler\")\n    \n    def get_status(self) -> Dict:\n        \"\"\"Get current scheduler status\"\"\"\n        \n        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0\n        \n        return {\n            \"running\": self.running,\n            \"uptime_seconds\": uptime,\n            \"cycle_count\": self.cycle_count,\n            \"prediction_count\": self.prediction_count,\n            \"last_prediction\": self.last_options_prediction,\n            \"open_positions\": len(options_paper_trader.open_positions),\n            \"account_balance\": options_paper_trader.account_balance,\n            \"performance\": options_paper_trader.get_performance_summary()\n        }\n\n# Create global instance\noptions_scheduler = OptionsScheduler()\n\nif __name__ == \"__main__\":\n    # Test the scheduler\n    logger.info(\"🧪 Testing Options Scheduler...\")\n    \n    async def test_scheduler():\n        scheduler = OptionsScheduler()\n        \n        # Test signal generation\n        signals = await scheduler._generate_signals()\n        if signals:\n            print(f\"Generated signals: {signals['direction']} ({signals['confidence']:.1%})\")\n            \n            # Test prediction creation\n            prediction = await scheduler._create_options_prediction(signals)\n            if prediction:\n                print(f\"Generated prediction: {prediction['contract_symbol']}\")\n    \n    asyncio.run(test_scheduler())"
#!/usr/bin/env python3
"""
Working Trading Scheduler for AlgoSlayer
Actually runs predictions and trades during market hours
"""
import asyncio
import sys
import os
from datetime import datetime, time, timedelta
from loguru import logger
import traceback

# Add src to path
sys.path.append('.')
sys.path.append('/opt/rtx-trading')

# Set environment variables
os.environ['TRADING_ENABLED'] = 'true'
os.environ['PAPER_TRADING'] = 'true'

class WorkingTradingScheduler:
    """A scheduler that actually works and trades"""
    
    def __init__(self):
        self.running = False
        self.last_run = None
        self.prediction_interval = 15  # minutes
        self.strategies_initialized = False
        
        # Initialize components
        self._init_components()
        
    def _init_components(self):
        """Initialize all trading components"""
        try:
            # Import after environment is set
            from config.trading_config import TradingModeConfig
            TradingModeConfig.load_from_env()
            
            from src.core.signal_fusion import SignalFusionEngine
            from src.core.options_data_engine import OptionsDataEngine
            from src.core.multi_strategy_manager import MultiStrategyManager
            from src.core.options_prediction_engine import OptionsPredictionEngine
            from src.core.telegram_bot import telegram_bot
            
            self.signal_fusion = SignalFusionEngine()
            self.options_engine = OptionsDataEngine()
            self.strategy_manager = MultiStrategyManager()
            self.prediction_engine = OptionsPredictionEngine()
            self.telegram = telegram_bot
            
            logger.success("✅ All components initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            traceback.print_exc()
            raise
    
    def is_market_hours(self):
        """Check if market is open"""
        now = datetime.now()
        
        # Check weekday
        if now.weekday() >= 5:  # Weekend
            return False
        
        # Market hours (9:30 AM - 4:00 PM ET)
        market_open = time(9, 30)
        market_close = time(16, 0)
        current_time = now.time()
        
        return market_open <= current_time <= market_close
    
    async def run_prediction_cycle(self):
        """Run one complete prediction cycle for all strategies"""
        cycle_start = datetime.now()
        logger.info("=" * 60)
        logger.info(f"🔄 STARTING PREDICTION CYCLE at {cycle_start.strftime('%H:%M:%S')}")
        logger.info("=" * 60)
        
        try:
            # Step 1: Get current RTX price
            current_price = self.options_engine.get_current_stock_price()
            if not current_price:
                logger.error("Could not get RTX price - skipping cycle")
                return
            
            logger.info(f"📊 RTX Current Price: ${current_price:.2f}")
            
            # Step 2: Get all signals
            logger.info("🔍 Gathering AI signals...")
            decision = await self.signal_fusion.make_trading_decision("RTX")
            fusion_result = decision.to_dict()
            
            direction = fusion_result.get("direction", "HOLD")
            confidence = fusion_result.get("confidence", 0)
            signals_data = fusion_result.get("signals_data", {})
            
            # Count actionable signals
            actionable = 0
            total = 0
            for signal in signals_data.get("signals", []):
                total += 1
                if signal.get("direction") != "HOLD":
                    actionable += 1
            
            logger.info(f"📈 Signal Fusion Result:")
            logger.info(f"   Direction: {direction}")
            logger.info(f"   Confidence: {confidence:.1%}")
            logger.info(f"   Signals: {actionable}/{total} actionable")
            
            # Step 3: Check each strategy
            trades_made = 0
            
            for strategy_id, strategy in self.strategy_manager.active_strategies.items():
                config = strategy["config"]
                balance = strategy["balance"]
                
                logger.info(f"\n🎯 Checking {strategy_id.upper()} strategy:")
                logger.info(f"   Balance: ${balance:.2f}")
                logger.info(f"   Threshold: {config.confidence_threshold:.1%}")
                logger.info(f"   Min Signals: {config.min_signals_required}")
                
                # Check if should trade
                should_trade = (
                    confidence >= config.confidence_threshold and
                    actionable >= config.min_signals_required and
                    direction != "HOLD"
                )
                
                if should_trade:
                    logger.success(f"   ✅ WOULD TRADE! {direction} @ {confidence:.1%}")
                    
                    # Create options prediction
                    try:
                        prediction = await self.prediction_engine.create_prediction(
                            fusion_result,
                            balance,
                            strategy_id
                        )
                        
                        if prediction:
                            logger.success(f"   📝 Created prediction: {prediction.get('contract_symbol')}")
                            trades_made += 1
                            
                            # Send Telegram notification
                            await self.send_trade_notification(
                                strategy_id,
                                direction,
                                confidence,
                                current_price,
                                prediction
                            )
                        else:
                            logger.warning(f"   ⚠️  No suitable options contracts found")
                            
                    except Exception as e:
                        logger.error(f"   ❌ Prediction error: {e}")
                        
                else:
                    reasons = []
                    if confidence < config.confidence_threshold:
                        reasons.append(f"confidence {confidence:.1%} < {config.confidence_threshold:.1%}")
                    if actionable < config.min_signals_required:
                        reasons.append(f"signals {actionable} < {config.min_signals_required}")
                    if direction == "HOLD":
                        reasons.append("direction is HOLD")
                    
                    logger.info(f"   ❌ No trade: {', '.join(reasons)}")
            
            # Summary
            cycle_end = datetime.now()
            duration = (cycle_end - cycle_start).total_seconds()
            
            logger.info("=" * 60)
            logger.success(f"✅ CYCLE COMPLETE in {duration:.1f}s")
            logger.info(f"   Trades made: {trades_made}")
            logger.info("=" * 60)
            
            self.last_run = cycle_end
            
        except Exception as e:
            logger.error(f"Error in prediction cycle: {e}")
            traceback.print_exc()
    
    async def send_trade_notification(self, strategy_id, direction, confidence, price, prediction):
        """Send Telegram notification for trade"""
        try:
            contract = prediction.get("contract_symbol", "Unknown")
            strike = prediction.get("strike", 0)
            expiry = prediction.get("expiry", "Unknown")
            
            message = f"""
🎯 **{strategy_id.upper()} TRADE SIGNAL**

Direction: {direction}
Confidence: {confidence:.1%}
RTX Price: ${price:.2f}

📊 **Options Contract:**
{contract}
Strike: ${strike}
Expiry: {expiry}

Time: {datetime.now().strftime('%H:%M:%S')}
"""
            await self.telegram.send_message(message)
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    async def start(self):
        """Start the scheduler"""
        self.running = True
        logger.info("🚀 Working Trading Scheduler started")
        
        # Send startup notification
        try:
            await self.telegram.send_message(
                "🚀 AlgoSlayer Trading System RESTARTED\n"
                f"Mode: Paper Trading\n"
                f"Time: {datetime.now().strftime('%H:%M:%S')}"
            )
        except:
            pass
        
        while self.running:
            try:
                now = datetime.now()
                
                if self.is_market_hours():
                    # Check if it's time to run
                    should_run = False
                    
                    if self.last_run is None:
                        should_run = True
                    else:
                        time_since_last = (now - self.last_run).total_seconds() / 60
                        if time_since_last >= self.prediction_interval:
                            should_run = True
                    
                    if should_run:
                        await self.run_prediction_cycle()
                    else:
                        # Wait a bit and check again
                        await asyncio.sleep(30)
                else:
                    # Market closed
                    logger.info(f"Market closed, waiting... (next check in 5 minutes)")
                    await asyncio.sleep(300)  # 5 minutes
                    
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Scheduler stopped")

async def main():
    """Run the working scheduler"""
    scheduler = WorkingTradingScheduler()
    
    try:
        await scheduler.start()
    except KeyboardInterrupt:
        scheduler.stop()
        logger.info("Shutdown complete")

if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
    logger.add("logs/working_scheduler.log", rotation="1 day", level="DEBUG")
    
    # Run
    asyncio.run(main())
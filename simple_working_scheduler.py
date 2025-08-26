#!/usr/bin/env python3
"""
Simple Working Scheduler for AlgoSlayer
Ensures predictions actually run every 15 minutes during market hours
"""
import asyncio
import sys
from datetime import datetime, time
from loguru import logger

sys.path.append('.')

from src.core.signal_fusion import SignalFusionEngine
from src.core.options_data_engine import OptionsDataEngine
from src.core.multi_strategy_manager import MultiStrategyManager
from src.core.telegram_bot import telegram_bot

class SimpleScheduler:
    """Simple scheduler that actually works"""
    
    def __init__(self):
        self.running = False
        self.signal_fusion = SignalFusionEngine()
        self.options_engine = OptionsDataEngine()
        self.strategy_manager = MultiStrategyManager()
        
    def is_market_hours(self):
        """Check if market is open"""
        now = datetime.now()
        if now.weekday() >= 5:  # Weekend
            return False
        
        market_open = time(9, 30)
        market_close = time(16, 0)
        current_time = now.time()
        
        return market_open <= current_time <= market_close
    
    async def run_prediction_cycle(self):
        """Run one prediction cycle"""
        try:
            logger.info("🔄 Running prediction cycle...")
            
            # Get current price
            current_price = self.options_engine.get_current_stock_price()
            if not current_price:
                logger.warning("Could not get RTX price")
                return
            
            logger.info(f"RTX Price: ${current_price:.2f}")
            
            # Get signals
            decision = await self.signal_fusion.make_trading_decision("RTX")
            result = decision.to_dict()
            
            direction = result.get("direction", "HOLD")
            confidence = result.get("confidence", 0)
            
            logger.info(f"Signal: {direction} @ {confidence:.1%}")
            
            # Check each strategy
            for strategy_id, strategy in self.strategy_manager.active_strategies.items():
                config = strategy["config"]
                
                # Check if this strategy should trade
                if confidence >= config.confidence_threshold:
                    logger.info(f"✅ {strategy_id} strategy would trade: {direction} @ {confidence:.1%}")
                    
                    # Send Telegram notification
                    await telegram_bot.send_message(
                        f"🎯 {strategy_id.upper()} SIGNAL\n"
                        f"Direction: {direction}\n"
                        f"Confidence: {confidence:.1%}\n"
                        f"RTX Price: ${current_price:.2f}"
                    )
                else:
                    logger.info(f"❌ {strategy_id}: confidence {confidence:.1%} < {config.confidence_threshold:.1%}")
            
            logger.success("✅ Prediction cycle complete")
            
        except Exception as e:
            logger.error(f"Error in prediction cycle: {e}")
    
    async def start(self):
        """Start the scheduler"""
        self.running = True
        logger.info("🚀 Simple Scheduler started")
        
        while self.running:
            if self.is_market_hours():
                await self.run_prediction_cycle()
                await asyncio.sleep(900)  # 15 minutes
            else:
                logger.info("Market closed, waiting...")
                await asyncio.sleep(1800)  # 30 minutes
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Scheduler stopped")

async def main():
    """Run the simple scheduler"""
    scheduler = SimpleScheduler()
    
    try:
        await scheduler.start()
    except KeyboardInterrupt:
        scheduler.stop()

if __name__ == "__main__":
    asyncio.run(main())

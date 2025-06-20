#!/usr/bin/env python3
"""
Run Multi-Strategy Trading System
Launches 3 parallel trading strategies with independent ML optimization
"""

import asyncio
import sys
from loguru import logger
from src.core.parallel_strategy_runner import ParallelStrategyRunner
from src.core.telegram_bot import telegram_bot

# Configure logging
logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")
logger.add("logs/multi_strategy.log", rotation="1 day")

async def main():
    """Run the multi-strategy trading system"""
    logger.info("🎯 STARTING MULTI-STRATEGY TRADING SYSTEM")
    logger.info("=" * 60)
    
    # Create and start the parallel runner
    runner = ParallelStrategyRunner()
    
    try:
        # Start parallel trading
        await runner.start_parallel_trading()
        
    except KeyboardInterrupt:
        logger.info("⌨️ Keyboard interrupt received")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        await telegram_bot.send_message(f"❌ Multi-strategy system error: {str(e)}")
    finally:
        runner.stop()
        logger.info("🛑 Multi-strategy system stopped")

if __name__ == "__main__":
    # Show startup banner
    print("""
    ╔══════════════════════════════════════════╗
    ║     MULTI-STRATEGY TRADING SYSTEM        ║
    ║     3 Parallel Self-Improving AIs        ║
    ╠══════════════════════════════════════════╣
    ║  Conservative │ Moderate │ Aggressive    ║
    ║  75% / 4 sig  │ 60% / 3  │ 50% / 2 sig  ║
    ╚══════════════════════════════════════════╝
    """)
    
    # Run the async main function
    asyncio.run(main())
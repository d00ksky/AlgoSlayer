#!/usr/bin/env python3
"""
Reset Strategy Databases
Creates fresh, independent databases for each strategy
"""
import sys
import os
sys.path.append('/opt/rtx-trading' if os.path.exists('/opt/rtx-trading') else '.')

from src.core.options_paper_trader import OptionsPaperTrader
from src.core.lives_tracker import LivesTracker
from loguru import logger

def reset_strategy_databases():
    """Reset all strategy databases to clean state"""
    
    strategies = ["conservative", "moderate", "aggressive"]
    initial_balances = {
        "conservative": 1000.0,
        "moderate": 1000.0, 
        "aggressive": 1000.0
    }
    
    logger.info("🔄 Resetting strategy databases...")
    
    for strategy in strategies:
        try:
            logger.info(f"📊 Resetting {strategy} strategy...")
            
            # Create fresh paper trader with separate database
            trader = OptionsPaperTrader(
                initial_balance=initial_balances[strategy],
                db_suffix=f"_{strategy}"
            )
            
            # Verify database is separate
            logger.info(f"✅ {strategy} database: {trader.db_path}")
            logger.info(f"💰 {strategy} balance: ${trader.account_balance:.2f}")
            logger.info(f"📈 {strategy} positions: {len(trader.open_positions)}")
            
            # Initialize lives tracker for this strategy
            lives = LivesTracker(db_path=trader.db_path)
            life_status = lives.check_life_status(trader.account_balance, len(trader.open_positions))
            logger.info(f"🎮 {strategy} life status: {life_status['message']}")
            
            print(f"✅ {strategy.title()}: ${trader.account_balance:.2f}, {len(trader.open_positions)} positions")
            
        except Exception as e:
            logger.error(f"❌ Error resetting {strategy}: {e}")
            print(f"❌ {strategy.title()}: Error - {e}")
    
    logger.success("🎯 Strategy database reset complete!")
    
    # Verify separation
    print("\n📊 Database Verification:")
    for strategy in strategies:
        db_path = f"data/options_performance_{strategy}.db"
        if os.path.exists(db_path):
            file_size = os.path.getsize(db_path)
            print(f"  {strategy}: {db_path} ({file_size} bytes)")
        else:
            print(f"  {strategy}: Database missing!")

if __name__ == "__main__":
    reset_strategy_databases()
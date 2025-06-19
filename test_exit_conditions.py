#!/usr/bin/env python3
"""Test exit conditions with fixed price monitoring"""

from src.core.options_paper_trader import options_paper_trader
from loguru import logger

def test_exit_conditions():
    """Test that exit conditions work with fixed price monitoring"""
    
    logger.info('🧪 Testing exit conditions check...')
    
    # Check positions for exit conditions
    actions = options_paper_trader.check_positions()
    logger.info(f'Actions taken: {actions}')
    
    # Show current position status
    summaries = options_paper_trader.get_open_positions_summary()
    
    if summaries:
        for pos in summaries:
            logger.info(f'📊 Position Status:')
            logger.info(f'   Contract: {pos["contract_symbol"]}')
            logger.info(f'   Entry: ${pos["entry_price"]:.2f}')
            logger.info(f'   Current: ${pos["current_price"]:.2f}')
            logger.info(f'   P&L: ${pos["unrealized_pnl"]:.2f} ({pos["unrealized_pnl_pct"]:.1%})')
            logger.info(f'   Days held: {pos["days_held"]}')
            logger.info(f'   Confidence: {pos["confidence"]:.1%}')
    else:
        logger.info('📊 No open positions found')
    
    # Show account performance
    perf = options_paper_trader.get_performance_summary()
    logger.info(f'\n💰 Account Summary:')
    logger.info(f'   Current balance: ${perf["account_balance"]:.2f}')
    logger.info(f'   Total return: ${perf["total_return"]:.2f} ({perf["total_return_pct"]:.1%})')
    logger.info(f'   Open positions: {perf["open_positions_count"]}')
    logger.info(f'   Closed positions: {perf["closed_positions_count"]}')

if __name__ == "__main__":
    test_exit_conditions()
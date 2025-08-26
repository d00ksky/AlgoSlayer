#!/usr/bin/env python3
"""Test with fresh paper trader"""
import sys
sys.path.append('.')

from src.core.options_paper_trader import OptionsPaperTrader
from src.core.options_prediction_engine import options_prediction_engine

# Create a fresh trader with a clean state
trader = OptionsPaperTrader("data/test_options_performance.db")

# Test with fresh trader
print(f"Fresh trader balance: ${trader.account_balance:.2f}")

test_signals = {
    'direction': 'BUY',
    'confidence': 0.85,
    'expected_move': 0.03,
    'signals_agreeing': 8,
    'total_signals': 12
}

prediction = options_prediction_engine.generate_options_prediction(test_signals, trader.account_balance)

if prediction:
    print(f"Prediction: {prediction['contract_symbol']}")
    print(f"Cost: ${prediction['total_cost']:.2f}")
    
    success = trader.open_position(prediction)
    if success:
        print("✅ FRESH TRADER EXECUTED TRADE!")
        print(f"New balance: ${trader.account_balance:.2f}")
        print(f"Open positions: {len(trader.open_positions)}")
    else:
        print("❌ Trade failed")
else:
    print("❌ No prediction")
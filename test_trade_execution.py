#!/usr/bin/env python3
"""Test if trades can actually execute"""
import sys
sys.path.append('.')

from src.core.options_prediction_engine import options_prediction_engine
from src.core.options_paper_trader import options_paper_trader

def test_trade_execution():
    print("Testing full trade execution...")
    
    # Test if paper trader can execute a trade
    test_signals = {
        'direction': 'BUY',
        'confidence': 0.85,
        'expected_move': 0.03,
        'signals_agreeing': 8,
        'total_signals': 12
    }
    
    print(f"Initial balance: ${options_paper_trader.account_balance:.2f}")
    
    # Generate prediction
    prediction = options_prediction_engine.generate_options_prediction(test_signals, options_paper_trader.account_balance)
    
    if prediction:
        print(f"Generated prediction: {prediction['contract_symbol']}")
        print(f"Cost: ${prediction['total_cost']:.2f}")
        
        # Try to execute trade
        success = options_paper_trader.open_position(prediction)
        
        if success:
            print("✅ TRADE EXECUTED SUCCESSFULLY!")
            print(f"New balance: ${options_paper_trader.account_balance:.2f}")
            print(f"Open positions: {len(options_paper_trader.open_positions)}")
            
            # Show the trade details
            for pos_id, position in options_paper_trader.open_positions.items():
                pred = position['prediction']
                print(f"  Position: {pred['contract_symbol']} x{pred['contracts']} @ ${position['execution']['execution_price']:.2f}")
            
            return True
        else:
            print("❌ TRADE EXECUTION FAILED")
            return False
    else:
        print("❌ NO PREDICTION GENERATED")
        return False

if __name__ == "__main__":
    test_trade_execution()
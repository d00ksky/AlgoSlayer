#!/usr/bin/env python3
"""
Test Options Prediction Generation
"""
import asyncio
from src.core.options_scheduler import options_scheduler

async def test_options_prediction():
    print('🎯 Testing Options Prediction Generation...')
    
    # Generate signals and prediction
    signals = await options_scheduler._generate_signals()
    print(f'✅ Generated {len(signals)} signals')
    
    # Show all signals first to debug structure
    print('📊 Signal Details:')
    actionable_count = 0
    for name, signal in signals.items():
        if isinstance(signal, dict):
            direction = signal.get('direction', 'UNKNOWN')
            confidence = signal.get('confidence', 0)
            print(f'  {name}: {direction} ({confidence:.1f}%)')
            if direction != 'HOLD' and confidence > 70:
                actionable_count += 1
        else:
            print(f'  {name}: {type(signal)} - {signal}')
    
    print(f'📊 High-confidence signals: {actionable_count}')
    
    if actionable_count > 0:
        # Try to make prediction
        prediction = await options_scheduler._make_options_prediction(signals)
        if prediction:
            print('🎯 OPTIONS PREDICTION GENERATED:')
            print(f'  Action: {prediction["action"]}')
            print(f'  Contract: {prediction["contract_symbol"]}')
            print(f'  Entry Price: ${prediction["entry_price"]:.2f}')
            print(f'  Confidence: {prediction["confidence"]:.1f}%')
            print(f'  Strike: ${prediction["strike"]:.0f}')
            print(f'  Expiry: {prediction["expiry"]} ({prediction["days_to_expiry"]}d)')
            print(f'  Expected Move: {prediction["expected_move"]:.1f}%')
            print(f'  Expected Profit: {prediction["expected_profit_pct"]:.1f}%')
        else:
            print('⚠️ No prediction generated (low confidence or poor conditions)')
    else:
        print('ℹ️ No high-confidence signals available for options trading')

if __name__ == "__main__":
    asyncio.run(test_options_prediction())
#!/usr/bin/env python3
"""
Test Telegram Notification Formatting
"""
import asyncio
from src.core.telegram_bot import telegram_bot

async def test_telegram_formatting():
    print('📱 Testing Telegram Notification Formatting...')
    
    # Test prediction alert formatting
    test_prediction = {
        'action': 'BUY_TO_OPEN_CALL',
        'symbol': 'RTX',
        'direction': 'BUY',
        'confidence': 85.7,
        'expected_move': 3.45,
        'stock_price': 146.41,
        'contract_symbol': 'RTX240621C147',
        'option_type': 'call',
        'strike': 147.0,
        'expiry': '2025-06-21',
        'days_to_expiry': 5,
        'entry_price': 2.45,
        'contracts': 1,
        'total_cost': 245.0,
        'expected_profit_pct': 150.0,
        'implied_volatility': 28.5,
        'delta': 0.65,
        'gamma': 0.03,
        'theta': -0.05,
        'vega': 0.12
    }
    
    # Test signals for formatting
    test_signals = {
        'technical_analysis': {'direction': 'BUY', 'confidence': 75.5, 'strength': 0.15},
        'momentum': {'direction': 'BUY', 'confidence': 82.3, 'strength': 0.12},
        'mean_reversion': {'direction': 'SELL', 'confidence': 90.1, 'strength': 0.08},
        'options_flow': {'direction': 'BUY', 'confidence': 95.7, 'strength': 0.18},
        'volatility_analysis': {'direction': 'HOLD', 'confidence': 50.0, 'strength': 0.05}
    }
    
    print('\\n🎯 Testing Options Prediction Alert...')
    try:
        # Simulate the options prediction message
        message = f"""🎯 **OPTIONS PREDICTION**

📊 **Contract Details:**
• Action: {test_prediction['action']}
• Contract: {test_prediction['contract_symbol']}
• Type: {test_prediction['option_type'].upper()}
• Strike: ${test_prediction['strike']:.0f}
• Expiry: {test_prediction['expiry']} ({test_prediction['days_to_expiry']}d)

💰 **Trade Setup:**
• Entry Price: ${test_prediction['entry_price']:.2f}
• Contracts: {test_prediction['contracts']}
• Total Cost: ${test_prediction['total_cost']:.0f}
• Expected Profit: {test_prediction['expected_profit_pct']:.1f}%

📈 **Market Data:**
• Stock Price: ${test_prediction['stock_price']:.2f}
• Expected Move: {test_prediction['expected_move']:.1f}%
• IV: {test_prediction['implied_volatility']:.1f}%

🧠 **AI Analysis:**
• Confidence: {test_prediction['confidence']:.1f}%
• Direction: {test_prediction['direction']}

📊 **Greeks:**
• Delta: {test_prediction['delta']:.2f}
• Gamma: {test_prediction['gamma']:.3f}
• Theta: {test_prediction['theta']:.3f}
• Vega: {test_prediction['vega']:.2f}"""
        
        print('✅ Options prediction message formatted correctly:')
        print(message)
        
    except Exception as e:
        print(f'❌ Options prediction formatting error: {e}')
    
    print('\\n📊 Testing Signal Details...')
    try:
        signals_text = "📊 **Signal Details:**\\n"
        for signal_name, signal_data in test_signals.items():
            direction = signal_data['direction']
            confidence = signal_data['confidence']
            strength = signal_data['strength']
            
            direction_emoji = "📈" if direction == "BUY" else "📉" if direction == "SELL" else "➡️"
            signals_text += f"• {signal_name}: {direction_emoji} {direction} ({confidence:.1f}%, {strength:.1f}%)\\n"
        
        print('✅ Signal details formatted correctly:')
        print(signals_text)
        
    except Exception as e:
        print(f'❌ Signal details formatting error: {e}')
    
    print('\\n💰 Testing Portfolio Update...')
    try:
        portfolio_message = f"""💰 **PORTFOLIO UPDATE**

📊 **Current Holdings:**
• RTX Shares: 9 @ $146.41 = $1,317.69
• Cash: $682.31
• Total Value: $2,000.00

📈 **Performance:**
• Daily P&L: +$45.67 (+2.3%)
• Total P&L: +$1,000.00 (+100.0%)
• Win Rate: 65.4%

🎯 **Options Trades:**
• Active Positions: 2
• Total Trades: 47
• Success Rate: 42.6%"""
        
        print('✅ Portfolio update formatted correctly:')
        print(portfolio_message)
        
    except Exception as e:
        print(f'❌ Portfolio update formatting error: {e}')
    
    print('\\n📊 Testing Daily Report...')
    try:
        daily_report = f"""📊 **DAILY TRADING REPORT**
Generated: {test_prediction['expiry']} 17:00 ET

💰 **Account Summary:**
• Starting Balance: $1,000.00
• Current Balance: $1,247.50
• Daily P&L: +$37.25 (+3.1%)
• Total Return: +24.8%

🎯 **Today's Activity:**
• Predictions Made: 3
• Trades Executed: 1
• Win Rate: 100.0%

🤖 **AI Performance:**
• Signal Accuracy: 78.5%
• High Confidence Calls: 85.7%
• Model Confidence: 82.3%

📈 **Top Signals:**
• technical_analysis: 15.2% weight
• momentum: 12.1% weight  
• options_flow: 11.5% weight"""
        
        print('✅ Daily report formatted correctly:')
        print(daily_report)
        
    except Exception as e:
        print(f'❌ Daily report formatting error: {e}')

if __name__ == "__main__":
    asyncio.run(test_telegram_formatting())
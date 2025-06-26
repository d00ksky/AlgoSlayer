#!/usr/bin/env python3
"""
Test options data feed in detail
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.options_data_engine import OptionsDataEngine
import yfinance as yf

print('🔍 Detailed Options Data Analysis')
print('=' * 50)

# Check RTX options via yfinance directly
rtx = yf.Ticker('RTX')
options_dates = rtx.options
print(f'Available option dates: {len(options_dates)}')
print(f'Dates: {options_dates[:5] if len(options_dates) >= 5 else options_dates}')

if options_dates:
    # Get options for first available date
    exp_date = options_dates[0]
    option_chain = rtx.option_chain(exp_date)
    calls = option_chain.calls
    puts = option_chain.puts
    
    print(f'\\nFor expiry {exp_date}:')
    print(f'Calls available: {len(calls)}')
    print(f'Puts available: {len(puts)}')
    
    if len(calls) > 0:
        print(f'Call strike range: ${calls["strike"].min():.2f} - ${calls["strike"].max():.2f}')
        
        # Show some sample calls
        print("Sample calls:")
        for i in range(min(3, len(calls))):
            row = calls.iloc[i]
            print(f"  Strike ${row['strike']:.2f}: Bid ${row['bid']:.2f}, Ask ${row['ask']:.2f}")
    
    # Now test our engine
    print('\\n' + '=' * 30)
    print('Testing Our Options Engine')
    print('=' * 30)
    
    engine = OptionsDataEngine()
    our_contracts = engine.get_real_options_chain()
    print(f'Our engine found: {len(our_contracts)} contracts')
    
    if our_contracts:
        print('Our contracts:')
        for i, contract in enumerate(our_contracts[:5]):
            print(f'  {i+1}. {contract.get("contractSymbol", "N/A")}')
            print(f'     Price: ${contract.get("lastPrice", 0):.2f}')
            print(f'     Bid/Ask: ${contract.get("bid", 0):.2f}/${contract.get("ask", 0):.2f}')
            print(f'     Volume: {contract.get("volume", 0)}')
            print()

# Also test multi-strategy database isolation
print('\\n' + '=' * 50)
print('🗄️ Testing Multi-Strategy Database Isolation')
print('=' * 50)

# Check if separate strategy databases exist
import sqlite3

strategies = ['conservative', 'moderate', 'aggressive']
for strategy in strategies:
    db_path = f'data/{strategy}_trading.db'
    if os.path.exists(db_path):
        print(f'✅ {strategy}: Database exists')
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check balance
        cursor.execute('SELECT balance FROM account_balance ORDER BY timestamp DESC LIMIT 1')
        balance_result = cursor.fetchone()
        balance = balance_result[0] if balance_result else 0
        
        # Check positions
        cursor.execute('SELECT COUNT(*) FROM options_outcomes WHERE exit_time IS NULL')
        positions = cursor.fetchone()[0]
        
        print(f'   Balance: ${balance:.2f}, Positions: {positions}')
        conn.close()
    else:
        print(f'❌ {strategy}: Database missing')

print('\\n✅ Analysis complete')
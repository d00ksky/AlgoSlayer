#!/usr/bin/env python3
"""
Diagnose the 433% profit display issue
"""
import os
import sys

# SSH command to run on server
ssh_command = """
cd /opt/rtx-trading && rtx-env/bin/python -c "
import sqlite3
import json
from datetime import datetime

print('🔍 DIAGNOSING 433% PROFIT ISSUE')
print('='*60)

# 1. Check multi-strategy database
print('\\n1. MULTI-STRATEGY DATABASE:')
conn = sqlite3.connect('data/algoslayer_multi_strategy.db')
cursor = conn.cursor()
cursor.execute('SELECT name, current_balance, total_pnl FROM trading_strategies')
for row in cursor.fetchall():
    print(f'  {row[0]}: Balance=${row[1]:.2f}, P&L=${row[2]:.2f}')
conn.close()

# 2. Check conservative strategy history
print('\\n2. CONSERVATIVE STRATEGY HISTORY:')
conn = sqlite3.connect('data/options_performance_conservative.db')
cursor = conn.cursor()

# Get balance range
cursor.execute('SELECT MIN(balance_after), MAX(balance_after) FROM account_history')
min_bal, max_bal = cursor.fetchone()
print(f'  Balance range: ${min_bal:.2f} to ${max_bal:.2f}')

# Calculate various profit scenarios
print('\\n3. POSSIBLE PROFIT CALCULATIONS:')
current_balance = 2000.0

# Scenario 1: From minimum balance
if min_bal and min_bal > 0:
    profit_from_min = ((current_balance - min_bal) / min_bal) * 100
    print(f'  From min balance (${min_bal:.2f}): {profit_from_min:.1f}%')

# Scenario 2: From 375 (433%)
profit_from_375 = ((current_balance - 375) / 375) * 100
print(f'  From $375: {profit_from_375:.1f}%')

# Scenario 3: From 460
profit_from_460 = ((current_balance - 460) / 460) * 100
print(f'  From $460: {profit_from_460:.1f}%')

# Check for stored initial balance
cursor.execute('SELECT balance_after FROM account_history ORDER BY timestamp ASC LIMIT 1')
first_balance = cursor.fetchone()
if first_balance:
    initial = first_balance[0]
    profit_from_initial = ((current_balance - initial) / initial) * 100
    print(f'  From initial balance (${initial:.2f}): {profit_from_initial:.1f}%')

# Check for any hardcoded value
print('\\n4. CHECKING FOR HARDCODED VALUES:')

# Check backup tables
cursor.execute(\\"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%backup%'\\")
backup_tables = cursor.fetchall()
print(f'  Backup tables found: {[t[0] for t in backup_tables]}')

# Check for original P&L
if any('original_pnl_backup' in t[0] for t in backup_tables):
    cursor.execute('SELECT COUNT(*), SUM(net_pnl) FROM original_pnl_backup')
    count, total_pnl = cursor.fetchone()
    if total_pnl:
        print(f'  Original P&L backup: {count} trades, total P&L: ${total_pnl:.2f}')
        # If we assume initial was $460 per strategy
        initial_total = 460 * 8  # 8 strategies
        profit_pct = (total_pnl / initial_total) * 100
        print(f'  If initial was $460 x 8 = ${initial_total}: {profit_pct:.1f}%')

conn.close()

# 5. Check active files
print('\\n5. CHECKING SOURCE FILES:')
import subprocess
try:
    # Look for 433 in Python files
    result = subprocess.run(['grep', '-r', '433\\\\|375\\\\|460.*capital', '.', '--include=*.py'], 
                          capture_output=True, text=True)
    if result.stdout:
        lines = result.stdout.strip().split('\\n')[:5]
        for line in lines:
            if '__pycache__' not in line and 'rtx-env' not in line:
                print(f'  Found: {line[:100]}...')
except:
    print('  Could not search files')

print('\\n🎯 MOST LIKELY CAUSE:')
print('  The system is calculating profit from an old initial balance of $375')
print('  Current: $2000, Initial: $375 → (2000-375)/375 = 433.3%')
print('\\n  This initial balance is probably hardcoded somewhere or stored')
print('  in a configuration that survived the July reset.')
"
"""

print("Running diagnostic on server...")
os.system(f'ssh root@64.226.96.90 "{ssh_command}"')
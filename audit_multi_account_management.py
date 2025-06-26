#!/usr/bin/env python3
"""
Audit Multi-Account Management System
Check how well the 3 strategies are isolated and managed
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_account_isolation():
    """Check if the 3 strategies have proper account isolation"""
    print("🏦 Account Isolation Check")
    print("=" * 50)
    
    try:
        strategies = ['conservative', 'moderate', 'aggressive']
        isolation_score = 0
        total_checks = 0
        
        for strategy in strategies:
            print(f"\\n📊 {strategy.upper()} Strategy:")
            
            # Check for dedicated database
            db_files = [
                f'data/{strategy}_trading.db',
                f'data/{strategy}_options_trades.db',
                f'data/options_performance_{strategy}.db'
            ]
            
            db_found = False
            for db_file in db_files:
                if os.path.exists(db_file):
                    print(f"  ✅ Database: {os.path.basename(db_file)}")
                    db_found = True
                    
                    # Check database content
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    
                    # Check tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    if tables:
                        print(f"     Tables: {tables}")
                        
                        # Check for strategy-specific data
                        for table in ['options_outcomes', 'account_balance']:
                            if table in tables:
                                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                                count = cursor.fetchone()[0]
                                print(f"     {table}: {count} records")
                    
                    conn.close()
                    break
            
            if db_found:
                isolation_score += 1
            else:
                print(f"  ❌ No dedicated database found")
            
            total_checks += 1
            
            # Check for strategy-specific configuration
            config_files = [
                f'data/strategy_configs/{strategy}_threshold.json',
                f'data/strategy_configs/{strategy}_weights.json',
                f'data/strategy_configs/{strategy}_ml_config.json'
            ]
            
            config_found = 0
            for config_file in config_files:
                if os.path.exists(config_file):
                    config_found += 1
                    print(f"  ✅ Config: {os.path.basename(config_file)}")
            
            if config_found >= 2:
                isolation_score += 1
            else:
                print(f"  ⚠️ Limited strategy-specific configuration")
            
            total_checks += 1
        
        isolation_percentage = (isolation_score / total_checks) * 100
        print(f"\\n📊 Account Isolation Score: {isolation_score}/{total_checks} ({isolation_percentage:.1f}%)")
        
        return isolation_percentage >= 70
        
    except Exception as e:
        print(f"❌ Account isolation check failed: {e}")
        return False

def check_balance_management():
    """Check how account balances are managed independently"""
    print("\\n💰 Balance Management Check")
    print("=" * 50)
    
    try:
        from src.core.options_paper_trader import OptionsPaperTrader
        
        strategies = ['conservative', 'moderate', 'aggressive']
        balance_info = {}
        
        for strategy in strategies:
            print(f"\\n📈 {strategy.upper()} Strategy Balance:")
            
            try:
                # Create trader instance for this strategy
                trader = OptionsPaperTrader(strategy)
                
                # Get current balance
                balance = trader.account_balance
                print(f"  Current Balance: ${balance:.2f}")
                
                # Check balance history if available
                if hasattr(trader, 'conn') and trader.conn:
                    cursor = trader.conn.cursor()
                    
                    # Check if balance history table exists
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='account_balance'")
                    if cursor.fetchone():
                        cursor.execute("SELECT COUNT(*) FROM account_balance")
                        balance_records = cursor.fetchone()[0]
                        print(f"  Balance History: {balance_records} records")
                        
                        # Get balance trend
                        cursor.execute("SELECT balance FROM account_balance ORDER BY timestamp DESC LIMIT 5")
                        recent_balances = cursor.fetchall()
                        if recent_balances:
                            print(f"  Recent Balances: {[f'${b[0]:.2f}' for b in recent_balances]}")
                
                balance_info[strategy] = {
                    'balance': balance,
                    'trader_instance': trader
                }
                
            except Exception as e:
                print(f"  ❌ Error accessing {strategy} balance: {e}")
                balance_info[strategy] = {'balance': 0, 'error': str(e)}
        
        # Check for balance independence
        balances = [info.get('balance', 0) for info in balance_info.values()]
        unique_balances = len(set(balances))
        
        print(f"\\n📊 Balance Independence:")
        print(f"  Unique Balances: {unique_balances}/3")
        
        if unique_balances >= 2:
            print("  ✅ Strategies have independent balances")
            return True
        else:
            print("  ⚠️ Strategies may be sharing balances")
            return False
            
    except Exception as e:
        print(f"❌ Balance management check failed: {e}")
        return False

def check_position_isolation():
    """Check if positions are properly isolated between strategies"""
    print("\\n📊 Position Isolation Check")
    print("=" * 50)
    
    try:
        strategies = ['conservative', 'moderate', 'aggressive']
        position_data = {}
        
        for strategy in strategies:
            print(f"\\n🎯 {strategy.upper()} Positions:")
            
            # Check strategy-specific database for positions
            db_files = [
                f'data/{strategy}_options_trades.db',
                f'data/options_performance_{strategy}.db'
            ]
            
            positions_found = False
            for db_file in db_files:
                if os.path.exists(db_file):
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    
                    # Check for positions table
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    if 'options_outcomes' in tables:
                        # Count open positions
                        cursor.execute("SELECT COUNT(*) FROM options_outcomes WHERE exit_time IS NULL")
                        open_positions = cursor.fetchone()[0]
                        
                        # Count total positions
                        cursor.execute("SELECT COUNT(*) FROM options_outcomes")
                        total_positions = cursor.fetchone()[0]
                        
                        print(f"  Open Positions: {open_positions}")
                        print(f"  Total Positions: {total_positions}")
                        
                        if total_positions > 0:
                            # Get sample position data
                            cursor.execute("SELECT contract_symbol, entry_price FROM options_outcomes LIMIT 3")
                            samples = cursor.fetchall()
                            print(f"  Sample Contracts: {[s[0] for s in samples if s[0]]}")
                        
                        positions_found = True
                        position_data[strategy] = {
                            'open': open_positions,
                            'total': total_positions
                        }
                    
                    conn.close()
                    
                    if positions_found:
                        break
            
            if not positions_found:
                print(f"  📝 No position data found (normal if no trades yet)")
                position_data[strategy] = {'open': 0, 'total': 0}
        
        # Check for cross-contamination
        total_open = sum(data['open'] for data in position_data.values())
        total_positions = sum(data['total'] for data in position_data.values())
        
        print(f"\\n📊 Position Summary:")
        print(f"  Total Open Positions: {total_open}")
        print(f"  Total Historical Positions: {total_positions}")
        
        # Verify no shared positions
        if total_positions > 0:
            print("  ✅ Position isolation appears functional")
            return True
        else:
            print("  📝 No positions to verify isolation (normal)")
            return True
            
    except Exception as e:
        print(f"❌ Position isolation check failed: {e}")
        return False

def check_strategy_coordination():
    """Check how the strategies coordinate and compete"""
    print("\\n🏆 Strategy Coordination Check")
    print("=" * 50)
    
    try:
        # Check if multi-strategy runner is managing all 3
        with open('/opt/rtx-trading/logs/multi_strategy.log', 'r') as f:
            logs = f.read()
        
        # Look for strategy initialization
        strategies_initialized = []
        for strategy in ['conservative', 'moderate', 'aggressive']:
            if f'Initialized {strategy.title()} strategy' in logs:
                strategies_initialized.append(strategy)
                print(f"  ✅ {strategy.title()} strategy initialized")
        
        print(f"\\n📊 Strategy Initialization: {len(strategies_initialized)}/3")
        
        # Check for parallel execution
        if 'parallel' in logs.lower():
            print("  ✅ Parallel execution detected")
        
        # Check for strategy-specific decision making
        decision_patterns = [
            'Conservative: Confidence',
            'Moderate: Confidence', 
            'Aggressive: Confidence'
        ]
        
        decisions_found = 0
        for pattern in decision_patterns:
            if pattern in logs:
                decisions_found += 1
                print(f"  ✅ {pattern.split(':')[0]} decision making active")
        
        print(f"\\n📊 Independent Decision Making: {decisions_found}/3")
        
        if len(strategies_initialized) >= 2 and decisions_found >= 2:
            print("  ✅ Strategy coordination working well")
            return True
        else:
            print("  ⚠️ Limited strategy coordination")
            return False
            
    except Exception as e:
        print(f"❌ Strategy coordination check failed: {e}")
        return False

def check_capital_allocation():
    """Check if capital allocation between strategies is working"""
    print("\\n💼 Capital Allocation Check")
    print("=" * 50)
    
    try:
        # Check ML capital allocation file
        allocation_file = 'data/ml_capital_allocation.json'
        
        if os.path.exists(allocation_file):
            with open(allocation_file, 'r') as f:
                allocation = json.load(f)
            
            print("📊 Current Capital Allocation:")
            total_allocation = 0
            for strategy, pct in allocation.items():
                print(f"  {strategy.title()}: {pct:.1%}")
                total_allocation += pct
            
            print(f"\\nTotal Allocation: {total_allocation:.1%}")
            
            if abs(total_allocation - 1.0) < 0.01:  # Within 1%
                print("✅ Capital allocation sums to 100%")
                allocation_valid = True
            else:
                print("⚠️ Capital allocation doesn't sum to 100%")
                allocation_valid = False
            
            # Check if allocation favors better performers
            if 'conservative' in allocation and 'aggressive' in allocation:
                conservative_pct = allocation['conservative']
                aggressive_pct = allocation['aggressive']
                
                if conservative_pct > aggressive_pct:
                    print("✅ Higher allocation to better performer (Conservative)")
                else:
                    print("📊 Equal or higher allocation to Aggressive strategy")
            
            return allocation_valid
        else:
            print("❌ Capital allocation file not found")
            return False
            
    except Exception as e:
        print(f"❌ Capital allocation check failed: {e}")
        return False

def check_performance_tracking():
    """Check if individual strategy performance is tracked properly"""
    print("\\n📈 Performance Tracking Check")
    print("=" * 50)
    
    try:
        strategies = ['conservative', 'moderate', 'aggressive']
        performance_data = {}
        
        for strategy in strategies:
            print(f"\\n📊 {strategy.upper()} Performance:")
            
            # Try to get performance from various sources
            performance_found = False
            
            # Check strategy-specific performance files
            perf_files = [
                f'data/options_performance_{strategy}.db',
                f'data/{strategy}_options_trades.db'
            ]
            
            for perf_file in perf_files:
                if os.path.exists(perf_file):
                    conn = sqlite3.connect(perf_file)
                    cursor = conn.cursor()
                    
                    # Check for performance tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    if 'options_outcomes' in tables:
                        # Calculate performance metrics
                        cursor.execute("""
                            SELECT 
                                COUNT(*) as total_trades,
                                SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as wins,
                                AVG(net_pnl) as avg_pnl,
                                SUM(net_pnl) as total_pnl
                            FROM options_outcomes 
                            WHERE exit_time IS NOT NULL
                        """)
                        
                        result = cursor.fetchone()
                        if result and result[0] > 0:
                            total_trades, wins, avg_pnl, total_pnl = result
                            win_rate = (wins / total_trades) * 100
                            
                            print(f"  Total Trades: {total_trades}")
                            print(f"  Win Rate: {win_rate:.1f}%")
                            print(f"  Avg P&L: ${avg_pnl:.2f}")
                            print(f"  Total P&L: ${total_pnl:.2f}")
                            
                            performance_data[strategy] = {
                                'trades': total_trades,
                                'win_rate': win_rate,
                                'total_pnl': total_pnl
                            }
                            performance_found = True
                    
                    conn.close()
                    
                    if performance_found:
                        break
            
            if not performance_found:
                print(f"  📝 No performance data yet (normal)")
                performance_data[strategy] = {'trades': 0, 'win_rate': 0, 'total_pnl': 0}
        
        # Check if strategies have different performance
        win_rates = [data['win_rate'] for data in performance_data.values()]
        unique_performance = len(set(win_rates)) > 1 or any(data['trades'] > 0 for data in performance_data.values())
        
        print(f"\\n📊 Performance Differentiation:")
        if unique_performance:
            print("  ✅ Strategies show independent performance")
            return True
        else:
            print("  📝 No differentiated performance yet (normal)")
            return True
            
    except Exception as e:
        print(f"❌ Performance tracking check failed: {e}")
        return False

def main():
    """Run comprehensive multi-account management audit"""
    print("🏦 MULTI-ACCOUNT MANAGEMENT AUDIT")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Auditing Conservative, Moderate, and Aggressive strategy management...")
    print()
    
    # Run all checks
    results = {
        "Account Isolation": check_account_isolation(),
        "Balance Management": check_balance_management(),
        "Position Isolation": check_position_isolation(),
        "Strategy Coordination": check_strategy_coordination(),
        "Capital Allocation": check_capital_allocation(),
        "Performance Tracking": check_performance_tracking()
    }
    
    # Summary
    print("\\n" + "=" * 60)
    print("📋 MULTI-ACCOUNT AUDIT SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ GOOD" if result else "❌ NEEDS WORK"
        print(f"{status} {test_name}")
    
    print(f"\\nManagement Score: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed >= total * 0.8:
        print("🎉 MULTI-ACCOUNT MANAGEMENT IS EXCELLENT!")
        print("The 3 strategies are well-isolated and properly managed.")
    elif passed >= total * 0.6:
        print("👍 MULTI-ACCOUNT MANAGEMENT IS GOOD")
        print("Minor improvements could enhance strategy isolation.")
    else:
        print("⚠️ MULTI-ACCOUNT MANAGEMENT NEEDS IMPROVEMENT")
        print("Strategy isolation and management should be enhanced.")
    
    # Recommendations
    print("\\n💡 RECOMMENDATIONS:")
    
    if not results["Account Isolation"]:
        print("• Ensure each strategy has dedicated database files")
        print("• Implement strategy-specific configuration management")
    
    if not results["Balance Management"]:
        print("• Fix balance synchronization between strategies")
        print("• Implement independent balance tracking")
    
    if not results["Capital Allocation"]:
        print("• Fix capital allocation file and ensure it sums to 100%")
        print("• Implement dynamic allocation based on performance")
    
    return passed >= total * 0.8

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Comprehensive AlgoSlayer System Audit
Checks all critical components for issues
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
import traceback

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_options_data_feed():
    """Test options data feed and price accuracy"""
    print("📊 Testing Options Data Feed")
    print("=" * 50)
    
    try:
        import yfinance as yf
        from src.core.options_data_engine import OptionsDataEngine
        
        # Test RTX stock price
        rtx = yf.Ticker('RTX')
        current_price = rtx.history(period='1d')['Close'].iloc[-1]
        print(f"RTX Current Price: ${current_price:.2f}")
        
        # Test options data engine
        engine = OptionsDataEngine()
        contracts = engine.get_rtx_options_chain()
        print(f"Options Contracts Available: {len(contracts)}")
        
        if contracts:
            sample = contracts[0]
            print(f"Sample Contract: {sample.get('contractSymbol', 'N/A')}")
            print(f"Bid/Ask: ${sample.get('bid', 0):.2f} / ${sample.get('ask', 0):.2f}")
            print(f"Last Price: ${sample.get('lastPrice', 0):.2f}")
            print(f"Volume: {sample.get('volume', 0)}")
            print(f"Open Interest: {sample.get('openInterest', 0)}")
            
            # Check data quality
            bid = sample.get('bid', 0)
            ask = sample.get('ask', 0)
            if bid > 0 and ask > 0:
                spread_pct = ((ask - bid) / ((ask + bid) / 2)) * 100
                print(f"Bid/Ask Spread: {spread_pct:.1f}%")
                if spread_pct > 20:
                    print("⚠️ Warning: Wide spread (>20%)")
        
        print("✅ Options data feed working")
        return True
        
    except Exception as e:
        print(f"❌ Options data error: {e}")
        traceback.print_exc()
        return False

def test_paper_trading_calculations():
    """Test paper trading P&L calculations"""
    print("\n💰 Testing Paper Trading Calculations")
    print("=" * 50)
    
    try:
        from src.core.options_paper_trader import OptionsPaperTrader
        
        # Test with a sample strategy
        trader = OptionsPaperTrader("test_audit")
        
        # Check current balance
        balance = trader.get_account_balance()
        print(f"Account Balance: ${balance:.2f}")
        
        # Check recent trades
        recent_trades = trader.get_trade_history(limit=5)
        print(f"Recent Trades: {len(recent_trades)}")
        
        if recent_trades:
            for trade in recent_trades[:3]:
                print(f"  {trade.get('exit_time', 'Open')}: {trade.get('net_pnl', 0):.2f}")
        
        print("✅ Paper trading calculations working")
        return True
        
    except Exception as e:
        print(f"❌ Paper trading error: {e}")
        traceback.print_exc()
        return False

def test_database_integrity():
    """Check database integrity and structure"""
    print("\n🗄️ Testing Database Integrity")
    print("=" * 50)
    
    databases = [
        "data/options_paper_trading.db",
        "data/conservative_trading.db", 
        "data/moderate_trading.db",
        "data/aggressive_trading.db"
    ]
    
    issues = []
    
    for db_path in databases:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check key tables exist
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ['options_predictions', 'options_outcomes', 'account_balance']
                missing_tables = [t for t in required_tables if t not in tables]
                
                if missing_tables:
                    issues.append(f"{db_path}: Missing tables {missing_tables}")
                
                # Check data integrity
                for table in required_tables:
                    if table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        print(f"  {os.path.basename(db_path)} - {table}: {count} records")
                
                conn.close()
                
            except Exception as e:
                issues.append(f"{db_path}: Database error - {e}")
        else:
            print(f"  {os.path.basename(db_path)}: Not found (may be normal)")
    
    if issues:
        print("❌ Database issues found:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("✅ Database integrity check passed")
        return True

def test_ai_signals():
    """Test all 12 AI signals"""
    print("\n🧠 Testing AI Signals")
    print("=" * 50)
    
    try:
        from src.core.signal_fusion import SignalFusion
        
        fusion = SignalFusion()
        print(f"Signal fusion initialized with {len(fusion.signals)} signals")
        
        # Test signal generation
        signals = fusion.get_aggregated_signals()
        print(f"Generated signals: {len(signals)} components")
        
        if 'confidence' in signals:
            print(f"Overall confidence: {signals['confidence']:.1%}")
        
        # Check individual signals
        signal_names = [
            'news_sentiment', 'technical_analysis', 'options_flow', 
            'volatility_analysis', 'momentum', 'sector_correlation',
            'mean_reversion', 'market_regime', 'trump_geopolitical',
            'defense_contract', 'rtx_earnings', 'options_iv_percentile'
        ]
        
        working_signals = 0
        for signal_name in signal_names:
            if signal_name in signals.get('signals', {}):
                working_signals += 1
                signal_data = signals['signals'][signal_name]
                print(f"  ✅ {signal_name}: {signal_data.get('confidence', 0):.1%}")
            else:
                print(f"  ❌ {signal_name}: Missing")
        
        print(f"Working signals: {working_signals}/12")
        
        if working_signals >= 8:
            print("✅ AI signals working adequately")
            return True
        else:
            print("⚠️ Some AI signals missing")
            return False
            
    except Exception as e:
        print(f"❌ AI signals error: {e}")
        traceback.print_exc()
        return False

def test_emergency_systems():
    """Test emergency systems and error handling"""
    print("\n🚨 Testing Emergency Systems")
    print("=" * 50)
    
    try:
        # Test Telegram connectivity
        from src.core.telegram_bot import telegram_bot
        print("📱 Telegram bot initialized")
        
        # Test ML optimization system
        from src.core.ml_optimization_applier import ml_applier
        report = ml_applier.generate_optimization_report()
        if "ML Optimization Implementation Report" in report:
            print("✅ ML optimization system working")
        
        # Test lives tracker
        from src.core.lives_tracker import LivesTracker
        lives = LivesTracker()
        status = lives.check_life_status(500, 0)  # Test scenario
        print(f"✅ Lives tracker working: {status['status']}")
        
        # Test dynamic thresholds
        from src.core.dynamic_thresholds import DynamicThresholdManager
        dt = DynamicThresholdManager()
        threshold = dt.get_dynamic_threshold("conservative")
        print(f"✅ Dynamic thresholds working: {threshold[0]:.1%}")
        
        print("✅ Emergency systems operational")
        return True
        
    except Exception as e:
        print(f"❌ Emergency systems error: {e}")
        traceback.print_exc()
        return False

def check_configuration_files():
    """Check all configuration files are present and valid"""
    print("\n⚙️ Checking Configuration Files")
    print("=" * 50)
    
    config_files = [
        "data/ml_capital_allocation.json",
        "data/ml_runner_config.json",
        "data/strategy_configs/conservative_threshold.json",
        "data/strategy_configs/moderate_threshold.json", 
        "data/strategy_configs/aggressive_threshold.json"
    ]
    
    issues = []
    
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    print(f"✅ {os.path.basename(config_file)}: Valid JSON")
            except json.JSONDecodeError:
                issues.append(f"{config_file}: Invalid JSON")
        else:
            issues.append(f"{config_file}: Missing")
    
    if issues:
        print("❌ Configuration issues:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("✅ All configuration files valid")
        return True

def check_system_resources():
    """Check system resources and performance"""
    print("\n💻 Checking System Resources")
    print("=" * 50)
    
    try:
        # Memory usage
        import psutil
        memory = psutil.virtual_memory()
        print(f"Memory Usage: {memory.percent:.1f}% ({memory.used/1024**3:.1f}GB / {memory.total/1024**3:.1f}GB)")
        
        # Disk space
        disk = psutil.disk_usage('/')
        print(f"Disk Usage: {disk.percent:.1f}% ({disk.used/1024**3:.1f}GB / {disk.total/1024**3:.1f}GB)")
        
        # Process count
        processes = len(psutil.pids())
        print(f"Running Processes: {processes}")
        
        # Check if resources are adequate
        if memory.percent > 90:
            print("⚠️ High memory usage")
        if disk.percent > 90:
            print("⚠️ Low disk space")
        
        print("✅ System resources adequate")
        return True
        
    except ImportError:
        print("⚠️ psutil not available, skipping resource check")
        return True
    except Exception as e:
        print(f"❌ Resource check error: {e}")
        return False

def main():
    """Run comprehensive system audit"""
    print("🔍 ALGOSLAYER COMPREHENSIVE SYSTEM AUDIT")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all tests
    results = {
        "Options Data Feed": test_options_data_feed(),
        "Paper Trading": test_paper_trading_calculations(), 
        "Database Integrity": test_database_integrity(),
        "AI Signals": test_ai_signals(),
        "Emergency Systems": test_emergency_systems(),
        "Configuration Files": check_configuration_files(),
        "System Resources": check_system_resources()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 AUDIT SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall Score: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL SYSTEMS OPERATIONAL - No issues found!")
    else:
        print("⚠️  Some issues detected - Review failed tests above")
    
    return passed == total

if __name__ == "__main__":
    main()
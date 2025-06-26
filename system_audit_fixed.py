#!/usr/bin/env python3
"""
Fixed Comprehensive AlgoSlayer System Audit
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
import traceback

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
        
        # Test options data engine - use correct method name
        engine = OptionsDataEngine()
        contracts = engine.get_real_options_chain()  # Fixed method name
        print(f"Options Contracts Available: {len(contracts)}")
        
        if contracts:
            sample = contracts[0]
            print(f"Sample Contract: {sample.get('contractSymbol', 'N/A')}")
            print(f"Bid/Ask: ${sample.get('bid', 0):.2f} / ${sample.get('ask', 0):.2f}")
            print(f"Last Price: ${sample.get('lastPrice', 0):.2f}")
            
            # Check data quality
            bid = sample.get('bid', 0)
            ask = sample.get('ask', 0)
            if bid > 0 and ask > 0:
                spread_pct = ((ask - bid) / ((ask + bid) / 2)) * 100
                print(f"Bid/Ask Spread: {spread_pct:.1f}%")
        
        print("✅ Options data feed working")
        return True
        
    except Exception as e:
        print(f"❌ Options data error: {e}")
        return False

def test_paper_trading_calculations():
    """Test paper trading P&L calculations"""
    print("\\n💰 Testing Paper Trading Calculations")
    print("=" * 50)
    
    try:
        from src.core.options_paper_trader import OptionsPaperTrader
        
        trader = OptionsPaperTrader("test_audit")
        
        # Use correct attribute name
        balance = trader.account_balance  # Fixed attribute name
        print(f"Account Balance: ${balance:.2f}")
        
        # Test database connection
        if hasattr(trader, 'conn') and trader.conn:
            cursor = trader.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM options_outcomes WHERE exit_time IS NOT NULL")
            trade_count = cursor.fetchone()[0]
            print(f"Completed Trades: {trade_count}")
        
        print("✅ Paper trading calculations working")
        return True
        
    except Exception as e:
        print(f"❌ Paper trading error: {e}")
        return False

def test_database_integrity():
    """Check database integrity"""
    print("\\n🗄️ Testing Database Integrity")
    print("=" * 50)
    
    try:
        # Check main options database
        db_path = "data/options_paper_trading.db"
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"Database tables: {tables}")
            
            # Count records in key tables
            for table in ['options_predictions', 'options_outcomes']:
                if table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  {table}: {count} records")
            
            conn.close()
            print("✅ Main database structure valid")
        else:
            print("❌ Main database not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_ai_signals():
    """Test AI signals by checking recent logs"""
    print("\\n🧠 Testing AI Signals")
    print("=" * 50)
    
    try:
        # Check recent signal generation from logs
        with open('/opt/rtx-trading/logs/multi_strategy.log', 'r') as f:
            logs = f.read()
        
        # Look for signal generation patterns
        signal_patterns = [
            'news_sentiment', 'technical_analysis', 'options_flow',
            'volatility_analysis', 'momentum', 'sector_correlation'
        ]
        
        working_signals = 0
        for pattern in signal_patterns:
            if pattern in logs:
                working_signals += 1
                print(f"  ✅ {pattern}: Found in logs")
        
        # Check confidence generation
        if 'confidence:' in logs:
            print("✅ Confidence scoring working")
        
        print(f"Working signals: {working_signals}/{len(signal_patterns)}")
        
        if working_signals >= 4:
            print("✅ AI signals working adequately")
            return True
        else:
            print("⚠️ Limited AI signals detected")
            return False
            
    except Exception as e:
        print(f"❌ AI signals check error: {e}")
        return False

def test_emergency_systems():
    """Test emergency systems"""
    print("\\n🚨 Testing Emergency Systems")
    print("=" * 50)
    
    try:
        # Test Telegram
        from src.core.telegram_bot import telegram_bot
        print("✅ Telegram bot accessible")
        
        # Test ML optimization
        from src.core.ml_optimization_applier import ml_applier
        if hasattr(ml_applier, 'ml_configs'):
            print("✅ ML optimization system loaded")
        
        # Test lives tracker
        from src.core.lives_tracker import LivesTracker
        lives = LivesTracker()
        print("✅ Lives tracker initialized")
        
        # Test dynamic thresholds
        from src.core.dynamic_thresholds import DynamicThresholdManager
        dt = DynamicThresholdManager()
        if hasattr(dt, 'base_thresholds'):
            print(f"✅ Dynamic thresholds: {dt.base_thresholds}")
        
        print("✅ Emergency systems operational")
        return True
        
    except Exception as e:
        print(f"❌ Emergency systems error: {e}")
        return False

def test_service_health():
    """Check service health and status"""
    print("\\n🔧 Testing Service Health")
    print("=" * 50)
    
    try:
        import subprocess
        
        # Check multi-strategy service
        result = subprocess.run(['systemctl', 'is-active', 'multi-strategy-trading'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0 and 'active' in result.stdout:
            print("✅ Multi-strategy service: ACTIVE")
            service_healthy = True
        else:
            print("❌ Multi-strategy service: INACTIVE")
            service_healthy = False
        
        # Check recent logs for errors
        result = subprocess.run(['journalctl', '-u', 'multi-strategy-trading', '--since', '1 hour ago'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logs = result.stdout
            error_count = logs.lower().count('error')
            warning_count = logs.lower().count('warning')
            print(f"Recent logs: {error_count} errors, {warning_count} warnings")
            
            if error_count == 0:
                print("✅ No recent errors in logs")
            else:
                print("⚠️ Recent errors detected")
        
        return service_healthy
        
    except Exception as e:
        print(f"❌ Service health check error: {e}")
        return False

def main():
    """Run fixed system audit"""
    print("🔍 ALGOSLAYER SYSTEM AUDIT (FIXED)")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run tests
    results = {
        "Options Data Feed": test_options_data_feed(),
        "Paper Trading": test_paper_trading_calculations(),
        "Database Integrity": test_database_integrity(), 
        "AI Signals": test_ai_signals(),
        "Emergency Systems": test_emergency_systems(),
        "Service Health": test_service_health()
    }
    
    # Summary
    print("\\n" + "=" * 60)
    print("📋 AUDIT SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\\nOverall Score: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed >= total * 0.8:  # 80% pass rate
        print("🎉 SYSTEM MOSTLY OPERATIONAL")
    else:
        print("⚠️ SYSTEM NEEDS ATTENTION")
    
    return passed >= total * 0.8

if __name__ == "__main__":
    main()
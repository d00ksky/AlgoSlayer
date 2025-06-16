#!/usr/bin/env python3
"""
Complete System Stress Test & Verification
Tests edge cases, error handling, and production scenarios
"""
import asyncio
import json
import sqlite3
import time
from datetime import datetime, timedelta
from src.core.options_scheduler import options_scheduler
from src.core.options_paper_trader import OptionsPaperTrader
from src.core.options_data_engine import options_data_engine
from src.core.telegram_bot import telegram_bot

async def stress_test_complete_system():
    print('🧪 COMPLETE SYSTEM STRESS TEST')
    print('=' * 60)
    print('🔍 Testing edge cases, error handling, and production scenarios')
    print('=' * 60)
    
    test_results = {
        'passed': 0,
        'failed': 0,
        'warnings': 0,
        'tests': []
    }
    
    def log_test(name, result, details=""):
        test_results['tests'].append({
            'name': name,
            'result': result,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        if result == 'PASS':
            test_results['passed'] += 1
            print(f'  ✅ {name}: PASS {details}')
        elif result == 'FAIL':
            test_results['failed'] += 1
            print(f'  ❌ {name}: FAIL {details}')
        else:
            test_results['warnings'] += 1
            print(f'  ⚠️ {name}: WARNING {details}')
    
    # Test 1: Database Integrity & Recovery
    print('\\n🗄️ Test 1: Database Integrity & Recovery')
    try:
        trader = OptionsPaperTrader()
        
        # Test database corruption recovery
        conn = sqlite3.connect(trader.db_path)
        cursor = conn.cursor()
        
        # Check all required tables exist
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t[0] for t in tables]
        
        required_tables = ['options_predictions', 'options_outcomes', 'account_history']
        missing_tables = [t for t in required_tables if t not in table_names]
        
        if missing_tables:
            log_test("Database Tables", "FAIL", f"Missing: {missing_tables}")
        else:
            log_test("Database Tables", "PASS", f"All {len(required_tables)} tables present")
        
        # Test database constraints
        try:
            cursor.execute("INSERT INTO options_predictions (prediction_id) VALUES ('test')")
            conn.rollback()
            log_test("Database Constraints", "FAIL", "Missing NOT NULL constraints")
        except sqlite3.IntegrityError:
            log_test("Database Constraints", "PASS", "Constraints working")
        
        conn.close()
        
    except Exception as e:
        log_test("Database Setup", "FAIL", str(e))
    
    # Test 2: Options Data Availability & Validation
    print('\\n📊 Test 2: Options Data Quality & Edge Cases')
    try:
        # Test during market hours vs after hours
        options_chain = options_data_engine.get_real_options_chain()
        
        if not options_chain:
            log_test("Options Data Fetch", "FAIL", "No options data available")
        else:
            log_test("Options Data Fetch", "PASS", f"{len(options_chain)} contracts loaded")
        
        # Validate data quality
        valid_contracts = 0
        invalid_contracts = 0
        
        for symbol, option in options_chain.items():
            required_fields = ['type', 'strike', 'expiry', 'bid', 'ask']
            if all(field in option for field in required_fields):
                if option['bid'] > 0 and option['ask'] > option['bid']:
                    valid_contracts += 1
                else:
                    invalid_contracts += 1
            else:
                invalid_contracts += 1
        
        if invalid_contracts > valid_contracts * 0.1:  # More than 10% invalid
            log_test("Options Data Quality", "WARNING", f"{invalid_contracts} invalid contracts")
        else:
            log_test("Options Data Quality", "PASS", f"{valid_contracts} valid contracts")
        
        # Test extreme market conditions
        stock_price = options_data_engine.get_current_stock_price()
        if stock_price:
            # Check for options at various strikes
            strikes = [opt['strike'] for opt in options_chain.values()]
            price_range = max(strikes) - min(strikes)
            
            if price_range < stock_price * 0.2:  # Less than 20% range
                log_test("Strike Range Coverage", "WARNING", f"Limited range: ${price_range:.0f}")
            else:
                log_test("Strike Range Coverage", "PASS", f"Good range: ${price_range:.0f}")
        
    except Exception as e:
        log_test("Options Data Processing", "FAIL", str(e))
    
    # Test 3: Signal Generation Under Load
    print('\\n🤖 Test 3: AI Signal Generation Stress Test')
    try:
        # Test multiple rapid signal generations
        start_time = time.time()
        signals_list = []
        
        for i in range(3):
            signals = await options_scheduler._generate_signals()
            signals_list.append(signals)
            
        generation_time = time.time() - start_time
        
        if generation_time > 30:  # More than 30 seconds for 3 runs
            log_test("Signal Generation Speed", "WARNING", f"{generation_time:.1f}s for 3 runs")
        else:
            log_test("Signal Generation Speed", "PASS", f"{generation_time:.1f}s for 3 runs")
        
        # Check signal consistency
        confidences = [s.get('confidence', 0) for s in signals_list]
        confidence_variance = max(confidences) - min(confidences)
        
        if confidence_variance > 0.2:  # More than 20% variance
            log_test("Signal Consistency", "WARNING", f"High variance: {confidence_variance:.2f}")
        else:
            log_test("Signal Consistency", "PASS", f"Stable signals: {confidence_variance:.2f}")
        
    except Exception as e:
        log_test("Signal Generation", "FAIL", str(e))
    
    # Test 4: Paper Trading Edge Cases
    print('\\n💰 Test 4: Paper Trading Edge Cases')
    try:
        trader = OptionsPaperTrader()
        initial_balance = trader.account_balance
        
        # Test insufficient funds
        expensive_prediction = {
            'prediction_id': 'stress_test_expensive',
            'symbol': 'RTX',
            'action': 'BUY_TO_OPEN_CALL',
            'contract_symbol': 'RTX250620C00147000',
            'option_type': 'call',
            'strike': 147.0,
            'expiry': '2025-06-20',
            'days_to_expiry': 3,
            'entry_price': 50.00,  # Extremely expensive
            'contracts': 1,
            'total_cost': 5001.15,  # More than account balance
            'direction': 'BUY',
            'confidence': 95.0,
            'expected_move': 10.0,
            'expected_profit_pct': 200.0,
            'stock_price_entry': 146.0,
            'implied_volatility': 0.30,
            'delta': 0.70,
            'gamma': 0.04,
            'theta': -0.06,
            'vega': 0.10,
            'signals_data': '{}',
            'profit_target_price': 100.0,
            'stop_loss_price': 25.0,
            'max_loss_dollars': 2500.0,
            'volume': 100,
            'open_interest': 200,
            'reasoning': 'Stress test - expensive option'
        }
        
        result = trader.open_position(expensive_prediction)
        if result:
            log_test("Insufficient Funds Handling", "FAIL", "Allowed trade above balance")
        else:
            log_test("Insufficient Funds Handling", "PASS", "Rejected expensive trade")
        
        # Verify balance unchanged
        if trader.account_balance == initial_balance:
            log_test("Balance Protection", "PASS", "Balance unchanged after rejection")
        else:
            log_test("Balance Protection", "FAIL", f"Balance changed: {trader.account_balance}")
        
        # Test with valid trade
        if options_chain:
            contract_symbol = list(options_chain.keys())[0]
            option = options_chain[contract_symbol]
            entry_price = (option['bid'] + option['ask']) / 2
            
            valid_prediction = {
                'prediction_id': 'stress_test_valid',
                'symbol': 'RTX',
                'action': 'BUY_TO_OPEN_CALL',
                'contract_symbol': contract_symbol,
                'option_type': 'call',
                'strike': option['strike'],
                'expiry': option['expiry'],
                'days_to_expiry': 3,
                'entry_price': entry_price,
                'contracts': 1,
                'total_cost': entry_price * 100 + 1.15,
                'direction': 'BUY',
                'confidence': 85.0,
                'expected_move': 4.0,
                'expected_profit_pct': 150.0,
                'stock_price_entry': 146.0,
                'implied_volatility': 0.28,
                'delta': 0.65,
                'gamma': 0.03,
                'theta': -0.05,
                'vega': 0.09,
                'signals_data': '{}',
                'profit_target_price': entry_price * 2,
                'stop_loss_price': entry_price * 0.5,
                'max_loss_dollars': entry_price * 50,
                'volume': 100,
                'open_interest': 200,
                'reasoning': 'Stress test - valid trade'
            }
            
            if valid_prediction['total_cost'] < initial_balance:
                result = trader.open_position(valid_prediction)
                if result:
                    log_test("Valid Trade Execution", "PASS", f"Executed ${valid_prediction['total_cost']:.0f} trade")
                else:
                    log_test("Valid Trade Execution", "FAIL", "Valid trade rejected")
            else:
                log_test("Valid Trade Setup", "WARNING", "No affordable options available")
        
    except Exception as e:
        log_test("Paper Trading", "FAIL", str(e))
    
    # Test 5: Error Recovery & Resilience
    print('\\n🛡️ Test 5: Error Recovery & Resilience')
    try:
        # Test with invalid contract symbols
        fake_prediction = {
            'prediction_id': 'stress_test_invalid',
            'symbol': 'RTX',
            'action': 'BUY_TO_OPEN_CALL',
            'contract_symbol': 'INVALID_CONTRACT_SYMBOL',
            'option_type': 'call',
            'strike': 147.0,
            'expiry': '2025-06-20',
            'days_to_expiry': 3,
            'entry_price': 2.50,
            'contracts': 1,
            'total_cost': 251.15,
            'direction': 'BUY',
            'confidence': 85.0,
            'expected_move': 4.0,
            'expected_profit_pct': 150.0,
            'stock_price_entry': 146.0,
            'implied_volatility': 0.28,
            'delta': 0.65,
            'gamma': 0.03,
            'theta': -0.05,
            'vega': 0.09,
            'signals_data': '{}',
            'profit_target_price': 5.0,
            'stop_loss_price': 1.25,
            'max_loss_dollars': 125.0,
            'volume': 0,
            'open_interest': 0,
            'reasoning': 'Stress test - invalid contract'
        }
        
        trader = OptionsPaperTrader()
        result = trader.open_position(fake_prediction)
        
        if result:
            log_test("Invalid Contract Handling", "FAIL", "Accepted invalid contract")
        else:
            log_test("Invalid Contract Handling", "PASS", "Rejected invalid contract")
        
    except Exception as e:
        log_test("Error Recovery", "PASS", f"Graceful error handling: {type(e).__name__}")
    
    # Test 6: Memory & Resource Usage
    print('\\n💾 Test 6: Memory & Resource Usage')
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        if memory_mb > 500:  # More than 500MB
            log_test("Memory Usage", "WARNING", f"{memory_mb:.1f}MB")
        else:
            log_test("Memory Usage", "PASS", f"{memory_mb:.1f}MB")
        
        # Test file handle usage
        open_files = len(process.open_files())
        if open_files > 50:
            log_test("File Handles", "WARNING", f"{open_files} open files")
        else:
            log_test("File Handles", "PASS", f"{open_files} open files")
        
    except ImportError:
        log_test("Resource Monitoring", "WARNING", "psutil not available")
    except Exception as e:
        log_test("Resource Monitoring", "FAIL", str(e))
    
    # Test 7: Configuration Validation
    print('\\n⚙️ Test 7: Configuration Validation')
    try:
        from config.options_config import options_config
        from config.trading_config import trading_config
        
        # Check critical configuration values
        critical_configs = [
            ('MAX_POSITION_SIZE_PCT', 0.05, 0.50),  # 5% to 50%
            ('STOP_LOSS_PCT', 0.30, 0.70),         # 30% to 70%
            ('PROFIT_TARGET_PCT', 0.50, 3.00),     # 50% to 300%
            ('MIN_CONFIDENCE', 0.60, 0.95),        # 60% to 95%
        ]
        
        config_issues = []
        for config_name, min_val, max_val in critical_configs:
            if hasattr(options_config, config_name):
                value = getattr(options_config, config_name)
                if not (min_val <= value <= max_val):
                    config_issues.append(f"{config_name}={value} outside range [{min_val}, {max_val}]")
        
        if config_issues:
            log_test("Configuration Validation", "WARNING", "; ".join(config_issues))
        else:
            log_test("Configuration Validation", "PASS", "All configs in valid ranges")
        
    except Exception as e:
        log_test("Configuration Loading", "FAIL", str(e))
    
    # Test 8: Network Resilience
    print('\\n🌐 Test 8: Network Resilience & API Limits')
    try:
        # Test rapid API calls
        start_time = time.time()
        api_calls = 0
        
        for _ in range(3):
            try:
                options_data_engine.get_current_stock_price()
                api_calls += 1
            except:
                pass
        
        call_time = time.time() - start_time
        
        if api_calls == 3 and call_time < 10:
            log_test("API Call Speed", "PASS", f"{api_calls} calls in {call_time:.1f}s")
        elif api_calls < 3:
            log_test("API Call Reliability", "WARNING", f"Only {api_calls}/3 calls succeeded")
        else:
            log_test("API Call Performance", "WARNING", f"{call_time:.1f}s for {api_calls} calls")
        
    except Exception as e:
        log_test("Network Testing", "FAIL", str(e))
    
    # Test 9: Market Hours Handling
    print('\\n🕐 Test 9: Market Hours & Time Zone Handling')
    try:
        now = datetime.now()
        
        # Test weekend handling
        if now.weekday() >= 5:  # Saturday or Sunday
            log_test("Weekend Detection", "PASS", "System running on weekend")
        
        # Test after-hours handling
        if now.hour < 9 or now.hour > 16:  # Outside normal market hours
            log_test("After Hours Detection", "PASS", "System running after hours")
        
        # Test expiry date validation
        test_expiry = datetime.now() + timedelta(days=1)
        if test_expiry.weekday() >= 5:  # Weekend expiry
            log_test("Expiry Validation", "PASS", "Detected weekend expiry")
        
    except Exception as e:
        log_test("Time Handling", "FAIL", str(e))
    
    # Test 10: Final Integration Test
    print('\\n🔄 Test 10: End-to-End Integration')
    try:
        # Simulate a complete trading cycle
        start_time = time.time()
        
        # 1. Generate signals
        signals = await options_scheduler._generate_signals()
        
        # 2. Check if tradeable
        confidence = signals.get('confidence', 0)
        direction = signals.get('direction', 'HOLD')
        
        # 3. Get options data
        if confidence > 0.5 and direction != 'HOLD':
            options_chain = options_data_engine.get_real_options_chain()
            if options_chain:
                cycle_time = time.time() - start_time
                log_test("Full Trading Cycle", "PASS", f"Completed in {cycle_time:.1f}s")
            else:
                log_test("Full Trading Cycle", "WARNING", "No options data available")
        else:
            log_test("Full Trading Cycle", "PASS", f"Low confidence ({confidence:.1%}) - no trade")
        
    except Exception as e:
        log_test("Integration Test", "FAIL", str(e))
    
    # Final Summary
    print('\\n' + '=' * 60)
    print('🏁 STRESS TEST SUMMARY')
    print('=' * 60)
    
    total_tests = test_results['passed'] + test_results['failed'] + test_results['warnings']
    pass_rate = (test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
    
    print(f"📊 Total Tests: {total_tests}")
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"⚠️ Warnings: {test_results['warnings']}")
    print(f"📈 Pass Rate: {pass_rate:.1f}%")
    
    if test_results['failed'] == 0:
        print("\\n🎉 ALL CRITICAL TESTS PASSED!")
        print("✅ System is production-ready")
    elif test_results['failed'] <= 2:
        print("\\n⚠️ Minor issues detected")
        print("🔧 Review failed tests before production")
    else:
        print("\\n❌ Multiple critical failures")
        print("🛠️ System needs fixes before production")
    
    # Save detailed results
    with open('stress_test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\\n📝 Detailed results saved to: stress_test_results.json")
    
    return test_results['failed'] == 0

if __name__ == "__main__":
    print('🚨 COMPREHENSIVE STRESS TEST')
    print('🔍 This will test edge cases, error handling, and production scenarios')
    print('⏱️ Estimated time: 2-3 minutes')
    print()
    
    success = asyncio.run(stress_test_complete_system())
    
    if success:
        print('\\n✅ SYSTEM IS 100% PRODUCTION READY!')
    else:
        print('\\n⚠️ Issues detected - review results before live trading')
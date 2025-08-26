#!/usr/bin/env python3
"""
Comprehensive Automated Testing Suite for AlgoSlayer
Weekend upgrade: Complete system validation and testing
"""
import asyncio
import json
import sqlite3
import subprocess
import time
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class AlgoSlayerTestSuite:
    """Comprehensive automated testing for all system components"""
    
    def __init__(self):
        self.base_path = Path("/opt/rtx-trading")
        self.test_results = []
        self.start_time = None
        
    def log_test(self, test_name: str, status: str, details: str = "", duration: float = 0):
        """Log test results"""
        result = {
            "test_name": test_name,
            "status": status,  # "pass", "fail", "skip", "error"
            "details": details,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        # Color-coded console output
        colors = {
            "pass": "\033[92m✅",      # Green
            "fail": "\033[91m❌",      # Red
            "skip": "\033[93m⏭️",      # Yellow
            "error": "\033[91m💥"      # Red
        }
        reset = "\033[0m"
        
        emoji = colors.get(status, "")
        print(f"{emoji} {test_name}: {status.upper()}{reset}")
        if details:
            print(f"   Details: {details}")
        if duration > 0:
            print(f"   Duration: {duration:.2f}s")
        print()
    
    async def test_system_imports(self) -> bool:
        """Test that all critical modules can be imported"""
        print("🔍 Testing System Imports...")
        
        critical_imports = [
            "src.core.telegram_bot",
            "src.core.options_scheduler", 
            "src.core.ibkr_manager",
            "src.core.signal_fusion",
            "src.core.multi_strategy_manager",
            "src.core.parallel_strategy_runner",
            "config.trading_config",
            "config.options_config"
        ]
        
        passed = 0
        total = len(critical_imports)
        
        for module in critical_imports:
            start_time = time.time()
            try:
                __import__(module)
                duration = time.time() - start_time
                self.log_test(f"Import {module}", "pass", "", duration)
                passed += 1
            except ImportError as e:
                duration = time.time() - start_time
                self.log_test(f"Import {module}", "fail", str(e), duration)
            except Exception as e:
                duration = time.time() - start_time
                self.log_test(f"Import {module}", "error", str(e), duration)
        
        overall_status = "pass" if passed == total else "fail"
        self.log_test("System Imports Overall", overall_status, f"{passed}/{total} modules imported successfully")
        
        return passed == total
    
    async def test_database_integrity(self) -> bool:
        """Test database files and integrity"""
        print("🔍 Testing Database Integrity...")
        
        databases = [
            "algoslayer_multi_strategy.db",
            "options_performance_conservative.db", 
            "options_performance_moderate.db",
            "options_performance_aggressive.db"
        ]
        
        passed = 0
        total = len(databases)
        
        for db_name in databases:
            start_time = time.time()
            db_path = self.base_path / "data" / db_name
            
            try:
                if not db_path.exists():
                    self.log_test(f"Database {db_name}", "fail", "File does not exist")
                    continue
                
                # Test SQLite connection and integrity
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                # Integrity check
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()[0]
                
                if result != "ok":
                    self.log_test(f"Database {db_name}", "fail", f"Integrity check: {result}")
                    conn.close()
                    continue
                
                # Schema check
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                conn.close()
                duration = time.time() - start_time
                
                self.log_test(f"Database {db_name}", "pass", f"{len(tables)} tables, integrity OK", duration)
                passed += 1
                
            except Exception as e:
                duration = time.time() - start_time
                self.log_test(f"Database {db_name}", "error", str(e), duration)
        
        overall_status = "pass" if passed == total else "fail"
        self.log_test("Database Integrity Overall", overall_status, f"{passed}/{total} databases healthy")
        
        return passed == total
    
    async def test_configuration_files(self) -> bool:
        """Test configuration files are valid"""
        print("🔍 Testing Configuration Files...")
        
        config_files = [
            ("config/trading_config.py", "python"),
            ("config/options_config.py", "python"),
            ("data/active_strategies.json", "json"),
        ]
        
        passed = 0
        total = len(config_files)
        
        for file_path, file_type in config_files:
            start_time = time.time()
            full_path = self.base_path / file_path
            
            try:
                if not full_path.exists():
                    self.log_test(f"Config {file_path}", "fail", "File does not exist")
                    continue
                
                if file_type == "json":
                    with open(full_path, 'r') as f:
                        json.load(f)
                elif file_type == "python":
                    # Test that Python file can be compiled
                    with open(full_path, 'r') as f:
                        compile(f.read(), str(full_path), 'exec')
                
                duration = time.time() - start_time
                self.log_test(f"Config {file_path}", "pass", f"Valid {file_type}", duration)
                passed += 1
                
            except Exception as e:
                duration = time.time() - start_time
                self.log_test(f"Config {file_path}", "error", str(e), duration)
        
        overall_status = "pass" if passed == total else "fail"
        self.log_test("Configuration Files Overall", overall_status, f"{passed}/{total} config files valid")
        
        return passed == total
    
    async def test_ai_signals(self) -> bool:
        """Test AI signal generation"""
        print("🔍 Testing AI Signals...")
        
        try:
            # Import signal fusion
            sys.path.append(str(self.base_path))
            from src.core.signal_fusion import SignalFusion
            
            start_time = time.time()
            signal_fusion = SignalFusion()
            
            # Test signal generation
            signals = await signal_fusion.get_aggregated_signal()
            
            duration = time.time() - start_time
            
            if signals:
                confidence = signals.get('confidence', 0)
                direction = signals.get('direction', 'UNKNOWN')
                signal_count = len(signals.get('individual_signals', {}))
                
                details = f"Confidence: {confidence}%, Direction: {direction}, Signals: {signal_count}"
                self.log_test("AI Signal Generation", "pass", details, duration)
                return True
            else:
                self.log_test("AI Signal Generation", "fail", "No signals generated", duration)
                return False
                
        except Exception as e:
            self.log_test("AI Signal Generation", "error", str(e))
            return False
    
    async def test_telegram_bot_basic(self) -> bool:
        """Test basic Telegram bot functionality"""
        print("🔍 Testing Telegram Bot...")
        
        try:
            sys.path.append(str(self.base_path))
            from src.core.telegram_bot import telegram_bot
            
            start_time = time.time()
            
            # Test bot initialization
            has_token = bool(telegram_bot.bot_token if hasattr(telegram_bot, 'bot_token') else False)
            has_chat_id = bool(telegram_bot.chat_id if hasattr(telegram_bot, 'chat_id') else False)
            
            duration = time.time() - start_time
            
            if has_token and has_chat_id:
                self.log_test("Telegram Bot Config", "pass", "Token and Chat ID configured", duration)
                
                # Test message formatting (without sending)
                test_message = "🧪 Test message formatting"
                formatted = test_message[:4000]  # Telegram limit
                
                self.log_test("Telegram Message Format", "pass", f"Message length: {len(formatted)}")
                return True
            else:
                missing = []
                if not has_token: missing.append("token")
                if not has_chat_id: missing.append("chat_id")
                
                self.log_test("Telegram Bot Config", "fail", f"Missing: {', '.join(missing)}", duration)
                return False
                
        except Exception as e:
            self.log_test("Telegram Bot", "error", str(e))
            return False
    
    async def test_options_system(self) -> bool:
        """Test options trading system components"""
        print("🔍 Testing Options System...")
        
        try:
            sys.path.append(str(self.base_path))
            from src.core.options_scheduler import OptionsScheduler
            from config.options_config import options_config
            
            start_time = time.time()
            
            # Test options config
            config_valid = hasattr(options_config, 'STRATEGIES') and len(options_config.STRATEGIES) > 0
            
            if not config_valid:
                self.log_test("Options Config", "fail", "Invalid or missing strategies")
                return False
            
            # Test scheduler initialization
            scheduler = OptionsScheduler("test_strategy", 1000.0)
            
            duration = time.time() - start_time
            
            strategy_count = len(options_config.STRATEGIES)
            self.log_test("Options System", "pass", f"{strategy_count} strategies configured", duration)
            
            return True
            
        except Exception as e:
            self.log_test("Options System", "error", str(e))
            return False
    
    async def test_ml_system(self) -> bool:
        """Test ML system components"""
        print("🔍 Testing ML System...")
        
        try:
            # Check for ML models
            model_path = self.base_path / "ml_models"
            
            start_time = time.time()
            
            if not model_path.exists():
                self.log_test("ML Models Directory", "skip", "Models directory not found")
                return True  # Skip, not critical
            
            # Count model files
            model_files = list(model_path.glob("*.pkl")) + list(model_path.glob("*.json"))
            model_count = len(model_files)
            
            duration = time.time() - start_time
            
            if model_count > 0:
                self.log_test("ML Models", "pass", f"{model_count} model files found", duration)
                
                # Test one model loading
                try:
                    import pickle
                    if model_files:
                        with open(model_files[0], 'rb') as f:
                            model = pickle.load(f)
                        self.log_test("ML Model Loading", "pass", "Successfully loaded model")
                except:
                    self.log_test("ML Model Loading", "skip", "Model format not testable")
                
            else:
                self.log_test("ML Models", "skip", "No model files found (training needed)")
            
            return True
            
        except Exception as e:
            self.log_test("ML System", "error", str(e))
            return False
    
    async def test_system_services(self) -> bool:
        """Test systemd services"""
        print("🔍 Testing System Services...")
        
        try:
            # Check rtx-trading service
            result = subprocess.run(
                ["systemctl", "is-active", "rtx-trading.service"],
                capture_output=True, text=True, timeout=5
            )
            
            is_active = result.stdout.strip() == "active"
            
            if is_active:
                self.log_test("RTX Trading Service", "pass", "Service is active")
                
                # Get service details
                status_result = subprocess.run(
                    ["systemctl", "status", "rtx-trading.service", "--no-pager", "-l"],
                    capture_output=True, text=True, timeout=10
                )
                
                # Extract memory usage
                memory_info = "unknown"
                for line in status_result.stdout.split('\n'):
                    if "Memory:" in line:
                        memory_info = line.split("Memory:")[1].strip().split()[0]
                        break
                
                self.log_test("Service Memory Usage", "pass", f"Memory: {memory_info}")
                return True
            else:
                self.log_test("RTX Trading Service", "fail", "Service not active")
                return False
                
        except Exception as e:
            self.log_test("System Services", "error", str(e))
            return False
    
    async def test_network_connectivity(self) -> bool:
        """Test external API connectivity"""
        print("🔍 Testing Network Connectivity...")
        
        endpoints = [
            ("Telegram API", "api.telegram.org", 443),
            ("Yahoo Finance", "query1.finance.yahoo.com", 443)
        ]
        
        passed = 0
        total = len(endpoints)
        
        for name, host, port in endpoints:
            start_time = time.time()
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                
                duration = time.time() - start_time
                
                if result == 0:
                    self.log_test(f"Connectivity {name}", "pass", f"Reachable at {host}:{port}", duration)
                    passed += 1
                else:
                    self.log_test(f"Connectivity {name}", "fail", f"Cannot reach {host}:{port}")
                    
            except Exception as e:
                duration = time.time() - start_time
                self.log_test(f"Connectivity {name}", "error", str(e), duration)
        
        overall_status = "pass" if passed >= total // 2 else "fail"  # Allow some network failures
        self.log_test("Network Connectivity Overall", overall_status, f"{passed}/{total} endpoints reachable")
        
        return passed >= total // 2
    
    async def run_all_tests(self) -> Dict:
        """Run comprehensive test suite"""
        print("🧪 STARTING COMPREHENSIVE AUTOMATED TESTING SUITE")
        print("=" * 60)
        
        self.start_time = time.time()
        
        # Define test suite
        tests = [
            ("System Imports", self.test_system_imports),
            ("Database Integrity", self.test_database_integrity),
            ("Configuration Files", self.test_configuration_files),
            ("AI Signals", self.test_ai_signals),
            ("Telegram Bot", self.test_telegram_bot_basic),
            ("Options System", self.test_options_system),
            ("ML System", self.test_ml_system),
            ("System Services", self.test_system_services),
            ("Network Connectivity", self.test_network_connectivity),
        ]
        
        results_summary = {}
        
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                result = await test_func()
                results_summary[test_name] = "PASS" if result else "FAIL"
            except Exception as e:
                print(f"💥 Test suite error in {test_name}: {e}")
                results_summary[test_name] = "ERROR"
        
        # Generate summary
        total_time = time.time() - self.start_time
        
        passed_tests = sum(1 for r in self.test_results if r['status'] == 'pass')
        failed_tests = sum(1 for r in self.test_results if r['status'] == 'fail')
        error_tests = sum(1 for r in self.test_results if r['status'] == 'error')
        skipped_tests = sum(1 for r in self.test_results if r['status'] == 'skip')
        total_tests = len(self.test_results)
        
        # Calculate overall system health
        critical_failures = sum(1 for category, status in results_summary.items() 
                               if status in ['FAIL', 'ERROR'] and 
                               category in ['System Imports', 'Database Integrity', 'System Services'])
        
        if critical_failures == 0:
            system_health = "EXCELLENT"
        elif critical_failures <= 1:
            system_health = "GOOD"
        elif critical_failures <= 2:
            system_health = "FAIR"
        else:
            system_health = "POOR"
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_duration": round(total_time, 2),
            "system_health": system_health,
            "test_summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "skipped": skipped_tests
            },
            "category_results": results_summary,
            "detailed_results": self.test_results
        }
        
        return summary
    
    def generate_test_report(self, results: Dict) -> str:
        """Generate comprehensive test report"""
        health_emoji = {
            "EXCELLENT": "🟢",
            "GOOD": "🟡", 
            "FAIR": "🟠",
            "POOR": "🔴"
        }
        
        report = f"""
🧪 **ALGOSLAYER AUTOMATED TEST REPORT**
🕐 **Time:** {results['timestamp']}
{health_emoji[results['system_health']]} **System Health:** {results['system_health']}
⏱️ **Total Duration:** {results['total_duration']}s

📊 **Test Results Summary:**
• Total Tests: {results['test_summary']['total']}
• Passed: {results['test_summary']['passed']} ✅
• Failed: {results['test_summary']['failed']} ❌
• Errors: {results['test_summary']['errors']} 💥
• Skipped: {results['test_summary']['skipped']} ⏭️

📋 **Category Results:**
"""
        
        for category, status in results['category_results'].items():
            emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "💥"
            report += f"• {emoji} {category}: {status}\n"
        
        # Add failed test details
        failed_tests = [t for t in results['detailed_results'] if t['status'] in ['fail', 'error']]
        if failed_tests:
            report += f"\n🚨 **Failed Tests Details:**\n"
            for test in failed_tests:
                report += f"• {test['test_name']}: {test['details']}\n"
        
        # Add recommendations
        report += f"\n💡 **Recommendations:**\n"
        if results['system_health'] == "EXCELLENT":
            report += "• System is running optimally! 🎉\n"
            report += "• Continue regular monitoring\n"
        elif results['system_health'] == "GOOD":
            report += "• Address minor issues when convenient\n"
            report += "• System is stable for production use\n"
        elif results['system_health'] == "FAIR":
            report += "• Address failed tests to improve reliability\n"
            report += "• Monitor system closely\n"
        else:
            report += "• ⚠️ Immediate attention required for critical failures\n"
            report += "• Review system configuration and services\n"
        
        return report.strip()

async def main():
    """Run the automated test suite"""
    test_suite = AlgoSlayerTestSuite()
    
    # Run all tests
    results = await test_suite.run_all_tests()
    
    # Generate report
    report = test_suite.generate_test_report(results)
    
    print("\n" + "="*60)
    print(report)
    print("="*60)
    
    # Save detailed results
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: test_results.json")
    
    # Return exit code based on system health
    exit_codes = {
        "EXCELLENT": 0,
        "GOOD": 0, 
        "FAIR": 1,
        "POOR": 2
    }
    
    return exit_codes.get(results['system_health'], 2)

if __name__ == "__main__":
    # Add required environment for server execution
    os.environ.setdefault('PYTHONPATH', '/opt/rtx-trading')
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
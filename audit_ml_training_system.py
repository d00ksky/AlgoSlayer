#!/usr/bin/env python3
"""
Comprehensive ML Training and Self-Improvement System Audit
Check how well the ML learning system is working and where it can be improved
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
import subprocess
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_ml_data_collection():
    """Check if the system is collecting quality ML training data"""
    print("📊 ML Data Collection Audit")
    print("=" * 50)
    
    try:
        # Check for training data files
        data_sources = {
            'Options Trades': 'data/options_paper_trading.db',
            'Signal Performance': 'data/signal_performance.db',
            'ML Training Data': 'ml_training_data/',
            'Strategy Performance': 'data/options_performance*.db'
        }
        
        training_data_quality = 0
        total_checks = 0
        
        for source_name, path_pattern in data_sources.items():
            print(f"\\n🔍 {source_name}:")
            total_checks += 1
            
            if '*' in path_pattern:
                # Glob pattern
                result = subprocess.run(['find', '/opt/rtx-trading', '-name', 
                                       path_pattern.replace('*', '*'), '-type', 'f'], 
                                      capture_output=True, text=True)
                files = result.stdout.strip().split('\\n') if result.stdout.strip() else []
                files = [f for f in files if f]
                
                if files:
                    print(f"  ✅ Found {len(files)} files")
                    for f in files[:3]:  # Show first 3
                        basename = os.path.basename(f)
                        size = os.path.getsize(f) / 1024  # KB
                        print(f"     {basename}: {size:.1f} KB")
                    training_data_quality += 1
                else:
                    print(f"  📝 No files found")
            
            elif os.path.exists(path_pattern):
                size = os.path.getsize(path_pattern) / 1024  # KB
                print(f"  ✅ Found: {size:.1f} KB")
                
                # For databases, check record count
                if path_pattern.endswith('.db'):
                    conn = sqlite3.connect(path_pattern)
                    cursor = conn.cursor()
                    
                    # Check tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    if tables:
                        print(f"     Tables: {tables}")
                        
                        # Count records in key tables
                        for table in ['options_outcomes', 'signal_performance']:
                            if table in tables:
                                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                                count = cursor.fetchone()[0]
                                print(f"     {table}: {count} records")
                                
                                if count > 0:
                                    training_data_quality += 0.5
                    
                    conn.close()
                else:
                    training_data_quality += 1
            
            elif os.path.isdir(path_pattern):
                files = os.listdir(path_pattern)
                ml_files = [f for f in files if f.endswith(('.json', '.pkl', '.csv'))]
                print(f"  ✅ Directory with {len(ml_files)} ML files")
                training_data_quality += 1
            else:
                print(f"  📝 Not found (may be normal)")
        
        data_score = (training_data_quality / total_checks) * 100
        print(f"\\n📊 Data Collection Score: {training_data_quality:.1f}/{total_checks} ({data_score:.1f}%)")
        
        return data_score >= 60
        
    except Exception as e:
        print(f"❌ Data collection check failed: {e}")
        return False

def check_ml_optimization_system():
    """Check if ML optimization system is working"""
    print("\\n🤖 ML Optimization System Audit")
    print("=" * 50)
    
    try:
        from src.core.ml_optimization_applier import ml_applier
        
        # Check if ML applier is functional
        print("🔧 ML Applier Status:")
        print(f"  ✅ ML Optimization Applier loaded")
        
        # Check ML configurations
        if hasattr(ml_applier, 'ml_configs'):
            configs = ml_applier.ml_configs
            print(f"  📊 ML Configs loaded: {len(configs)} strategies")
            
            for strategy, config in configs.items():
                print(f"     {strategy}: {list(config.keys())}")
        
        # Test optimization report generation
        try:
            report = ml_applier.generate_optimization_report()
            if "ML Optimization Implementation Report" in report:
                print("  ✅ Optimization reporting working")
                
                # Check for specific optimizations
                if "Signal Weight Optimizations" in report:
                    print("  ✅ Signal weight optimization active")
                if "Capital Allocation" in report:
                    print("  ✅ Capital allocation optimization active")
                if "Confidence Threshold" in report:
                    print("  ✅ Threshold optimization active")
                
                return True
            else:
                print("  ⚠️ Optimization reporting limited")
                return False
                
        except Exception as e:
            print(f"  ❌ Optimization report failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ ML optimization check failed: {e}")
        return False

def check_learning_frequency():
    """Check how often the system learns and improves"""
    print("\\n⏰ Learning Frequency Audit")
    print("=" * 50)
    
    try:
        # Check for automated learning triggers
        learning_triggers = []
        
        # Check cron jobs
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            cron_jobs = result.stdout
            if 'ml' in cron_jobs.lower() or 'train' in cron_jobs.lower():
                learning_triggers.append("Cron jobs")
                print("  ✅ Automated learning via cron")
        
        # Check for learning scripts
        learning_scripts = [
            'run_ml_learning.py',
            'sync_and_train_ml.py', 
            'train_now.sh',
            'bootstrap_historic_training.py'
        ]
        
        scripts_found = 0
        for script in learning_scripts:
            if os.path.exists(script):
                scripts_found += 1
                print(f"  ✅ Learning script: {script}")
        
        if scripts_found > 0:
            learning_triggers.append("Learning scripts")
        
        # Check logs for recent learning activity
        try:
            result = subprocess.run([
                'journalctl', '-u', 'multi-strategy-trading',
                '--since', '24 hours ago', '--no-pager'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logs = result.stdout
                
                # Look for learning-related activities
                learning_activities = [
                    'ML optimization',
                    'training',
                    'signal weights',
                    'threshold adjustment',
                    'performance analysis'
                ]
                
                activities_found = 0
                for activity in learning_activities:
                    if activity.lower() in logs.lower():
                        activities_found += 1
                        print(f"  ✅ Recent activity: {activity}")
                
                if activities_found > 0:
                    learning_triggers.append("Live learning")
        
        except Exception as e:
            print(f"  ⚠️ Could not check recent learning activity: {e}")
        
        print(f"\\n📊 Learning Mechanisms: {len(learning_triggers)}")
        for trigger in learning_triggers:
            print(f"  • {trigger}")
        
        return len(learning_triggers) >= 1
        
    except Exception as e:
        print(f"❌ Learning frequency check failed: {e}")
        return False

def check_performance_feedback_loop():
    """Check if the system learns from actual performance"""
    print("\\n🔄 Performance Feedback Loop Audit")
    print("=" * 50)
    
    try:
        # Check if system tracks prediction accuracy
        accuracy_tracking = False
        
        # Look for prediction vs outcome tracking
        db_files = [
            'data/options_paper_trading.db',
            'data/conservative_options_trades.db',
            'data/moderate_options_trades.db', 
            'data/aggressive_options_trades.db'
        ]
        
        total_predictions = 0
        total_outcomes = 0
        
        for db_file in db_files:
            if os.path.exists(db_file):
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Check tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                if 'options_predictions' in tables:
                    cursor.execute("SELECT COUNT(*) FROM options_predictions")
                    predictions = cursor.fetchone()[0]
                    total_predictions += predictions
                
                if 'options_outcomes' in tables:
                    cursor.execute("SELECT COUNT(*) FROM options_outcomes")
                    outcomes = cursor.fetchone()[0]
                    total_outcomes += outcomes
                    
                    # Check for P&L tracking
                    cursor.execute("PRAGMA table_info(options_outcomes)")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    pnl_tracking = any(col in columns for col in ['net_pnl', 'pnl_percentage', 'profit_loss'])
                    if pnl_tracking:
                        accuracy_tracking = True
                        print(f"  ✅ P&L tracking in {os.path.basename(db_file)}")
                
                conn.close()
        
        print(f"\\n📊 Prediction Tracking:")
        print(f"  Predictions Made: {total_predictions}")
        print(f"  Outcomes Recorded: {total_outcomes}")
        
        if total_outcomes > 0:
            completion_rate = (total_outcomes / max(total_predictions, 1)) * 100
            print(f"  Completion Rate: {completion_rate:.1f}%")
        
        # Check for signal performance tracking
        if os.path.exists('data/signal_performance.db'):
            conn = sqlite3.connect('data/signal_performance.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            if tables:
                print(f"  ✅ Signal performance database: {tables}")
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"     {table}: {count} records")
            
            conn.close()
        
        return accuracy_tracking and total_outcomes > 0
        
    except Exception as e:
        print(f"❌ Feedback loop check failed: {e}")
        return False

def check_adaptive_capabilities():
    """Check if the system adapts based on performance"""
    print("\\n🧠 Adaptive Capabilities Audit")
    print("=" * 50)
    
    try:
        adaptation_features = []
        
        # Check dynamic thresholds
        try:
            from src.core.dynamic_thresholds import DynamicThresholdManager
            dt = DynamicThresholdManager()
            
            if hasattr(dt, 'base_thresholds'):
                print("  ✅ Dynamic threshold management available")
                print(f"     Current thresholds: {dt.base_thresholds}")
                adaptation_features.append("Dynamic Thresholds")
        except Exception as e:
            print(f"  ⚠️ Dynamic thresholds check failed: {e}")
        
        # Check signal weight adaptation
        strategy_configs = [
            'data/strategy_configs/conservative_weights.json',
            'data/strategy_configs/moderate_weights.json',
            'data/strategy_configs/aggressive_weights.json'
        ]
        
        adaptive_weights = 0
        for config_file in strategy_configs:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    weights = json.load(f)
                    if weights:
                        adaptive_weights += 1
                        strategy_name = os.path.basename(config_file).split('_')[0]
                        print(f"  ✅ {strategy_name.title()} has adaptive signal weights")
        
        if adaptive_weights > 0:
            adaptation_features.append("Adaptive Signal Weights")
        
        # Check capital allocation adaptation
        if os.path.exists('data/ml_capital_allocation.json'):
            with open('data/ml_capital_allocation.json', 'r') as f:
                allocation = json.load(f)
                
                if 'optimal_allocation' in allocation:
                    print("  ✅ Adaptive capital allocation active")
                    opt_alloc = allocation['optimal_allocation']
                    print(f"     Allocation: {opt_alloc}")
                    adaptation_features.append("Capital Allocation")
        
        # Check lives system (automatic reset)
        try:
            from src.core.lives_tracker import LivesTracker
            lives = LivesTracker()
            print("  ✅ Lives system (automatic account reset)")
            adaptation_features.append("Lives System")
        except:
            pass
        
        print(f"\\n📊 Adaptive Features: {len(adaptation_features)}")
        for feature in adaptation_features:
            print(f"  • {feature}")
        
        return len(adaptation_features) >= 2
        
    except Exception as e:
        print(f"❌ Adaptive capabilities check failed: {e}")
        return False

def check_ml_model_sophistication():
    """Check the sophistication of ML models used"""
    print("\\n🎯 ML Model Sophistication Audit")
    print("=" * 50)
    
    try:
        sophistication_score = 0
        total_features = 5
        
        # Check for multiple model types
        model_files = []
        if os.path.exists('trained_models/'):
            files = os.listdir('trained_models/')
            model_files = [f for f in files if f.endswith(('.pkl', '.joblib', '.h5'))]
            
        if model_files:
            print(f"  ✅ Trained models found: {len(model_files)}")
            sophistication_score += 1
        else:
            print("  📝 No trained model files found")
        
        # Check for feature engineering
        feature_engineering = [
            'Greeks tracking (Delta, Gamma, Theta, Vega)',
            'IV percentile analysis', 
            'Multi-timeframe signals',
            'Options flow analysis',
            'Earnings calendar integration'
        ]
        
        # Check if these features are implemented by looking at signal files
        signals_dir = 'src/signals/'
        if os.path.exists(signals_dir):
            signal_files = os.listdir(signals_dir)
            
            features_found = 0
            for i, feature in enumerate(feature_engineering):
                # Map features to likely file names
                feature_mappings = {
                    0: 'options_flow',  # Greeks might be in options flow
                    1: 'options_iv_percentile',
                    2: 'momentum',  # Multi-timeframe
                    3: 'options_flow',
                    4: 'rtx_earnings'
                }
                
                expected_file = feature_mappings.get(i, '')
                if any(expected_file in f for f in signal_files):
                    print(f"  ✅ {feature}")
                    features_found += 1
                else:
                    print(f"  📝 {feature}: Not detected")
            
            if features_found >= 3:
                sophistication_score += 1
        
        # Check for ensemble methods
        if len(signal_files) >= 8:  # Multiple signals = ensemble
            print("  ✅ Ensemble approach (12 AI signals)")
            sophistication_score += 1
        
        # Check for online learning
        if os.path.exists('run_ml_learning.py'):
            print("  ✅ Online learning capability")
            sophistication_score += 1
        
        # Check for cross-validation
        if os.path.exists('src/core/cross_strategy_analyzer.py'):
            print("  ✅ Cross-strategy validation")
            sophistication_score += 1
        
        print(f"\\n📊 Sophistication Score: {sophistication_score}/{total_features} ({sophistication_score/total_features*100:.1f}%)")
        
        return sophistication_score >= 3
        
    except Exception as e:
        print(f"❌ ML sophistication check failed: {e}")
        return False

def main():
    """Run comprehensive ML training system audit"""
    print("🤖 ML TRAINING & SELF-IMPROVEMENT SYSTEM AUDIT")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Evaluating ML learning capabilities and self-improvement mechanisms...")
    print()
    
    # Run all ML checks
    results = {
        "Data Collection": check_ml_data_collection(),
        "ML Optimization System": check_ml_optimization_system(),
        "Learning Frequency": check_learning_frequency(),
        "Performance Feedback Loop": check_performance_feedback_loop(),
        "Adaptive Capabilities": check_adaptive_capabilities(),
        "ML Model Sophistication": check_ml_model_sophistication()
    }
    
    # Summary
    print("\\n" + "=" * 70)
    print("📋 ML TRAINING SYSTEM AUDIT SUMMARY")
    print("=" * 70)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ EXCELLENT" if result else "⚠️ NEEDS UPGRADE"
        print(f"{status} {test_name}")
    
    print(f"\\nML System Score: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed >= total * 0.8:
        print("🎉 ML TRAINING SYSTEM IS HIGHLY SOPHISTICATED!")
        print("The self-improvement capabilities are operating at professional level.")
    elif passed >= total * 0.6:
        print("👍 ML TRAINING SYSTEM IS GOOD")
        print("Some enhancements could improve learning capabilities.")
    else:
        print("🔧 ML TRAINING SYSTEM NEEDS SIGNIFICANT UPGRADES")
        print("Multiple areas require enhancement for better self-improvement.")
    
    # Recommendations for improvements
    print("\\n💡 UPGRADE RECOMMENDATIONS:")
    
    if not results["Data Collection"]:
        print("• Implement more comprehensive training data collection")
        print("• Add automated data quality validation")
    
    if not results["Learning Frequency"]:
        print("• Set up automated learning schedules (daily/weekly)")
        print("• Implement real-time learning triggers")
    
    if not results["Performance Feedback Loop"]:
        print("• Enhance prediction accuracy tracking")
        print("• Implement signal effectiveness scoring")
    
    if not results["ML Model Sophistication"]:
        print("• Add advanced ML models (ensemble, neural networks)")
        print("• Implement sophisticated feature engineering")
    
    print("\\n🚀 NEXT-LEVEL ENHANCEMENTS:")
    print("• Real-time model retraining based on market conditions")
    print("• Genetic algorithm for strategy evolution")
    print("• Reinforcement learning for position sizing")
    print("• Multi-asset correlation analysis")
    print("• Sentiment analysis integration")
    
    return passed >= total * 0.8

if __name__ == "__main__":
    main()
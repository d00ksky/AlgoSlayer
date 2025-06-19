#!/usr/bin/env python3
"""
Run ML Learning and Analysis
Analyzes trading performance and provides actionable insights for system improvement
Can be run manually or integrated into the trading system for continuous learning
"""
import asyncio
import json
import os
from datetime import datetime
from loguru import logger

from src.core.enhanced_options_ml import enhanced_options_ml
from src.core.adaptive_learning_system import adaptive_learning_system
from src.core.options_scheduler import OptionsScheduler

def run_comprehensive_analysis():
    """Run complete ML analysis and provide actionable insights"""
    
    print("🧠 STARTING COMPREHENSIVE ML ANALYSIS")
    print("=" * 60)
    
    # 1. Enhanced Options ML Analysis
    print("\n📊 STEP 1: Enhanced Options Analysis")
    enhanced_report = enhanced_options_ml.run_comprehensive_analysis()
    
    if 'error' not in enhanced_report:
        enhanced_options_ml.print_analysis_report(enhanced_report)
    else:
        print(f"❌ Enhanced analysis error: {enhanced_report['error']}")
    
    # 2. Adaptive Learning System
    print("\n🧠 STEP 2: Adaptive Learning Analysis")
    learning_summary = adaptive_learning_system.create_learning_summary()
    
    if 'error' not in learning_summary:
        adaptive_learning_system.print_learning_summary(learning_summary)
    else:
        print(f"❌ Learning analysis error: {learning_summary['error']}")
    
    # 3. Signal Weight Optimization
    print("\n⚖️ STEP 3: Signal Weight Optimization")
    
    # Get current weights from scheduler
    scheduler = OptionsScheduler()
    current_weights = scheduler.signal_weights
    
    print("Current signal weights:")
    for signal, weight in sorted(current_weights.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {signal}: {weight:.3f}")
    
    # Generate optimized weights if we have enough data
    if 'error' not in learning_summary and learning_summary['trades_analyzed'] >= 3:
        print("\n🔄 Generating optimized weights...")
        new_weights = adaptive_learning_system.generate_adaptive_weights(current_weights)
        
        print("Optimized signal weights:")
        for signal, weight in sorted(new_weights.items(), key=lambda x: x[1], reverse=True):
            old_weight = current_weights.get(signal, 0)
            change = weight - old_weight
            change_str = f"({change:+.3f})" if abs(change) > 0.001 else ""
            print(f"   • {signal}: {weight:.3f} {change_str}")
        
        # Save optimized weights
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        weights_file = f'reports/optimized_weights_{timestamp}.json'
        
        os.makedirs('reports', exist_ok=True)
        with open(weights_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'current_weights': current_weights,
                'optimized_weights': new_weights,
                'trades_analyzed': learning_summary['trades_analyzed'],
                'performance_improvement': learning_summary['performance_metrics']
            }, f, indent=2)
        
        print(f"\n💾 Optimized weights saved to: {weights_file}")
        
        # Provide integration instructions
        print("\n🔧 TO APPLY OPTIMIZED WEIGHTS:")
        print("1. Update src/core/options_scheduler.py signal_weights dict")
        print("2. Or create an auto-update system in the scheduler")
        print("3. Restart the trading system to use new weights")
        
    else:
        print("⚠️ Insufficient data for weight optimization (need 3+ completed trades)")
    
    # 4. Action Items Summary
    print("\n🎯 STEP 4: Priority Action Items")
    
    action_items = []
    
    # From enhanced analysis
    if 'error' not in enhanced_report:
        issues = enhanced_report.get('identified_issues', [])
        high_priority_issues = [issue for issue in issues if '❌' in issue]
        action_items.extend(high_priority_issues[:3])  # Top 3 critical issues
    
    # From adaptive learning
    if 'error' not in learning_summary:
        recommendations = learning_summary.get('strategy_recommendations', [])
        action_items.extend(recommendations[:3])  # Top 3 recommendations
    
    if action_items:
        print("Priority actions:")
        for i, item in enumerate(action_items[:5], 1):
            print(f"   {i}. {item}")
    else:
        print("✅ No critical issues identified")
    
    # 5. Generate comprehensive report
    print("\n📄 STEP 5: Comprehensive Report")
    
    report = {
        'analysis_timestamp': datetime.now().isoformat(),
        'enhanced_analysis': enhanced_report,
        'learning_analysis': learning_summary,
        'current_weights': current_weights,
        'action_items': action_items,
        'system_status': _assess_system_status(enhanced_report, learning_summary)
    }
    
    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f'reports/ml_analysis_comprehensive_{timestamp}.json'
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"📄 Comprehensive report saved to: {report_file}")
    
    # System status
    status = report['system_status']
    print(f"\n🎯 OVERALL SYSTEM STATUS: {status['status']}")
    print(f"   Readiness: {status['readiness']}")
    print(f"   Next Steps: {status['next_steps']}")
    
    print("\n" + "=" * 60)
    print("🎉 ML ANALYSIS COMPLETE")

def _assess_system_status(enhanced_report, learning_summary):
    """Assess overall system status and readiness"""
    
    if 'error' in enhanced_report or 'error' in learning_summary:
        return {
            'status': 'NEEDS_ATTENTION',
            'readiness': 'System has data issues that need resolution',
            'next_steps': 'Fix data collection and signals capture'
        }
    
    trades_analyzed = enhanced_report.get('performance_summary', {}).get('completed_trades', 0)
    
    if trades_analyzed < 5:
        return {
            'status': 'LEARNING_MODE',
            'readiness': f'Need more data ({trades_analyzed}/20 trades)',
            'next_steps': 'Continue paper trading to collect data'
        }
    elif trades_analyzed < 15:
        return {
            'status': 'EARLY_OPTIMIZATION',
            'readiness': 'Basic learning patterns available',
            'next_steps': 'Apply weight optimizations and collect more data'
        }
    else:
        return {
            'status': 'MATURE_LEARNING',
            'readiness': 'System ready for live trading optimization',
            'next_steps': 'Implement continuous learning and live trading'
        }

def apply_optimized_weights():
    """Apply optimized weights to the trading system"""
    
    logger.info("🔄 Applying optimized signal weights to trading system...")
    
    # Get latest optimized weights
    reports_dir = 'reports'
    if not os.path.exists(reports_dir):
        logger.error("❌ No reports directory found")
        return False
    
    weight_files = [f for f in os.listdir(reports_dir) if f.startswith('optimized_weights_')]
    
    if not weight_files:
        logger.error("❌ No optimized weights files found")
        return False
    
    # Get the most recent weights file
    latest_file = max(weight_files)
    weights_path = os.path.join(reports_dir, latest_file)
    
    with open(weights_path, 'r') as f:
        weights_data = json.load(f)
    
    optimized_weights = weights_data['optimized_weights']
    
    # Update scheduler weights (would need restart to take effect)
    scheduler = OptionsScheduler()
    scheduler.signal_weights.update(optimized_weights)
    
    logger.success(f"✅ Applied optimized weights from {latest_file}")
    logger.info("⚠️ Restart trading system for weights to take full effect")
    
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--apply-weights":
        apply_optimized_weights()
    else:
        run_comprehensive_analysis()
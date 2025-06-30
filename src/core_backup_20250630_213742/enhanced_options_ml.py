"""
Enhanced Options ML Learning System
Analyzes trading performance and provides actionable insights for improvement
Handles limited data scenarios and provides learning recommendations
"""
import sqlite3
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from loguru import logger
import os

class EnhancedOptionsML:
    """Enhanced ML system for options trading analysis and learning"""
    
    def __init__(self, options_db_path: str = "data/options_performance.db"):
        self.options_db_path = options_db_path
        self.insights = {}
        self.recommendations = []
        
    def analyze_current_performance(self) -> Dict[str, Any]:
        """Analyze current trading performance with whatever data we have"""
        
        logger.info("📊 Analyzing current options trading performance...")
        
        if not os.path.exists(self.options_db_path):
            return {'error': 'No trading database found'}
        
        conn = sqlite3.connect(self.options_db_path)
        
        # Get basic stats
        query = """
        SELECT 
            COUNT(*) as total_predictions,
            COUNT(o.net_pnl) as completed_trades,
            AVG(o.net_pnl) as avg_pnl,
            AVG(o.pnl_percentage) as avg_pnl_pct,
            SUM(CASE WHEN o.net_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
            MIN(o.pnl_percentage) as worst_loss_pct,
            MAX(o.pnl_percentage) as best_win_pct,
            AVG(p.confidence) as avg_confidence,
            AVG(p.days_to_expiry) as avg_dte,
            AVG(p.implied_volatility) as avg_iv_entry
        FROM options_predictions p
        LEFT JOIN options_outcomes o ON p.prediction_id = o.prediction_id
        """
        
        df = pd.read_sql_query(query, conn)
        stats = df.iloc[0].to_dict()
        
        # Calculate win rate
        stats['win_rate'] = stats['winning_trades'] / stats['completed_trades'] if stats['completed_trades'] > 0 else 0
        
        # Get detailed trade info
        trade_query = """
        SELECT 
            p.prediction_id,
            p.timestamp,
            p.confidence,
            p.expected_move,
            p.expected_profit_pct,
            p.days_to_expiry,
            p.implied_volatility,
            p.delta_entry,
            p.entry_price,
            p.signals_data,
            o.exit_timestamp,
            o.exit_reason,
            o.days_held,
            o.net_pnl,
            o.pnl_percentage,
            o.stock_move_pct
        FROM options_predictions p
        LEFT JOIN options_outcomes o ON p.prediction_id = o.prediction_id
        ORDER BY p.timestamp DESC
        """
        
        trades_df = pd.read_sql_query(trade_query, conn)
        conn.close()
        
        return {
            'summary_stats': stats,
            'trades': trades_df.to_dict('records'),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def identify_performance_issues(self, performance_data: Dict) -> List[str]:
        """Identify specific issues with current trading performance"""
        
        issues = []
        stats = performance_data['summary_stats']
        trades = performance_data['trades']
        
        # Check win rate
        if stats['completed_trades'] > 0:
            win_rate = stats['win_rate']
            if win_rate < 0.4:  # Target 40%+ for options
                issues.append(f"❌ Low win rate: {win_rate:.1%} (target: 40%+)")
            
            # Check average loss vs gain
            if stats['avg_pnl_pct'] < 0:
                issues.append(f"❌ Negative average P&L: {stats['avg_pnl_pct']:.1%}")
            
            # Check if losses are too large
            if stats['worst_loss_pct'] < -0.6:  # Worse than 60% loss
                issues.append(f"❌ Large losses: {stats['worst_loss_pct']:.1%} (stop loss may not be working)")
        
        # Check confidence calibration
        if stats['avg_confidence'] > 80 and stats['win_rate'] < 0.5:
            issues.append("❌ Overconfident predictions: High confidence but low win rate")
        
        # Check data quality issues
        empty_signals = sum(1 for trade in trades if not trade.get('signals_data') or trade['signals_data'] == '{}')
        if empty_signals > 0:
            issues.append(f"❌ Missing signals data: {empty_signals} trades have no signal information")
        
        # Check if we have enough data
        if stats['completed_trades'] < 10:
            issues.append(f"⚠️ Limited data: Only {stats['completed_trades']} completed trades (need 10+ for reliable analysis)")
        
        return issues
    
    def generate_learning_recommendations(self, performance_data: Dict, issues: List[str]) -> List[str]:
        """Generate specific recommendations for improving performance"""
        
        recommendations = []
        stats = performance_data['summary_stats']
        trades = performance_data['trades']
        
        # Data collection recommendations
        if len([t for t in trades if not t.get('signals_data') or t['signals_data'] == '{}']):
            recommendations.append("🔧 FIX CRITICAL: Enable signals_data logging in options predictions")
            recommendations.append("   - Check src/core/options_prediction_engine.py signal aggregation")
            recommendations.append("   - Ensure all 12 signals are being captured and stored")
        
        # Performance improvement recommendations
        if stats['completed_trades'] > 0:
            win_rate = stats['win_rate']
            
            if win_rate < 0.4:
                recommendations.append("📈 INCREASE WIN RATE:")
                recommendations.append("   - Raise confidence threshold from 60% to 75%+")
                recommendations.append("   - Require more signals to agree (4+ out of 12)")
                recommendations.append("   - Focus on high-conviction setups only")
            
            if stats['worst_loss_pct'] < -0.6:
                recommendations.append("🛡️ IMPROVE RISK MANAGEMENT:")
                recommendations.append("   - Reduce stop loss from 50% to 40%")
                recommendations.append("   - Add time-based stops (exit at 25% time decay)")
                recommendations.append("   - Consider smaller position sizes")
            
            # IV-specific recommendations
            if stats['avg_iv_entry'] and stats['avg_iv_entry'] > 30:
                recommendations.append("📊 IV OPTIMIZATION:")
                recommendations.append("   - Avoid high IV entries (>30%)")
                recommendations.append("   - Wait for IV compression after earnings")
                recommendations.append("   - Use IV percentile ranking for entry timing")
        
        # Strategy recommendations
        recommendations.append("🎯 STRATEGY IMPROVEMENTS:")
        recommendations.append("   - Track which signals actually correlate with profitable trades")
        recommendations.append("   - Implement signal weight adjustment based on P&L performance")
        recommendations.append("   - Add earnings calendar integration for timing")
        recommendations.append("   - Focus on RTX-specific patterns (defense contracts, earnings)")
        
        # Data collection for learning
        recommendations.append("📚 LEARNING SYSTEM:")
        recommendations.append("   - Run system for 2-4 weeks to collect 20+ trades")
        recommendations.append("   - Track signal combinations that lead to profits")
        recommendations.append("   - Analyze optimal DTE, IV, and Delta combinations")
        recommendations.append("   - Implement automatic signal weight adjustment")
        
        return recommendations
    
    def analyze_signal_gaps(self) -> Dict[str, Any]:
        """Analyze what signals are missing or not being captured"""
        
        logger.info("🔍 Analyzing signal data capture...")
        
        # Check if signals are being generated in recent logs
        log_file = "logs/rtx_trading_2025-06-19.log"
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_content = f.read()
            
            # Check for signal mentions
            signal_mentions = {
                'news_sentiment': 'news_sentiment' in log_content,
                'technical_analysis': 'technical_analysis' in log_content,
                'options_flow': 'options_flow' in log_content,
                'volatility_analysis': 'volatility_analysis' in log_content,
                'momentum': 'momentum' in log_content,
                'sector_correlation': 'sector_correlation' in log_content,
                'mean_reversion': 'mean_reversion' in log_content,
                'market_regime': 'market_regime' in log_content,
                'trump_geopolitical': 'trump_geopolitical' in log_content,
                'defense_contract': 'defense_contract' in log_content,
                'rtx_earnings': 'rtx_earnings' in log_content,
                'options_iv_percentile': 'options_iv_percentile' in log_content
            }
            
            missing_signals = [name for name, found in signal_mentions.items() if not found]
            
            return {
                'signal_mentions': signal_mentions,
                'missing_signals': missing_signals,
                'log_analysis': True
            }
        
        return {'log_analysis': False, 'error': 'No recent log file found'}
    
    def create_learning_plan(self, performance_data: Dict) -> Dict[str, Any]:
        """Create a specific plan for improving the ML system"""
        
        stats = performance_data['summary_stats']
        
        plan = {
            'immediate_actions': [],
            'short_term_goals': [],
            'long_term_objectives': [],
            'success_metrics': {}
        }
        
        # Immediate actions (today)
        plan['immediate_actions'] = [
            "Fix signals_data logging in options predictions",
            "Verify all 12 AI signals are operational",
            "Check signal aggregation in options_prediction_engine.py",
            "Test prediction cycle to ensure data capture"
        ]
        
        # Short-term goals (1-2 weeks)
        plan['short_term_goals'] = [
            "Collect 20+ trades with complete signal data",
            "Implement signal performance tracking",
            "Add confidence threshold adjustment (60% → 75%+)",
            "Implement dynamic position sizing based on confidence"
        ]
        
        # Long-term objectives (1 month+)
        plan['long_term_objectives'] = [
            "Achieve 40%+ win rate with positive expected value",
            "Implement automatic signal weight adjustment",
            "Add market regime detection for strategy adaptation",
            "Build RTX-specific pattern recognition"
        ]
        
        # Success metrics
        plan['success_metrics'] = {
            'min_win_rate': 0.40,  # 40%
            'min_profit_factor': 2.0,  # 2:1 win/loss ratio
            'max_drawdown': 0.30,  # 30%
            'min_trades_per_month': 8,  # 2 per week
            'target_monthly_return': 0.15  # 15%
        }
        
        return plan
    
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run complete analysis and provide actionable insights"""
        
        logger.info("🧠 Running comprehensive options trading analysis...")
        
        # Analyze current performance
        performance = self.analyze_current_performance()
        
        if 'error' in performance:
            return performance
        
        # Identify issues
        issues = self.identify_performance_issues(performance)
        
        # Generate recommendations
        recommendations = self.generate_learning_recommendations(performance, issues)
        
        # Analyze signal gaps
        signal_analysis = self.analyze_signal_gaps()
        
        # Create learning plan
        learning_plan = self.create_learning_plan(performance)
        
        # Compile comprehensive report
        report = {
            'performance_summary': {
                'total_predictions': performance['summary_stats']['total_predictions'],
                'completed_trades': performance['summary_stats']['completed_trades'],
                'win_rate': performance['summary_stats']['win_rate'],
                'avg_pnl_percentage': performance['summary_stats']['avg_pnl_pct'],
                'avg_confidence': performance['summary_stats']['avg_confidence']
            },
            'identified_issues': issues,
            'recommendations': recommendations,
            'signal_analysis': signal_analysis,
            'learning_plan': learning_plan,
            'raw_performance_data': performance,
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def print_analysis_report(self, report: Dict[str, Any]):
        """Print a formatted analysis report"""
        
        print("=" * 80)
        print("🧠 ENHANCED OPTIONS ML ANALYSIS REPORT")
        print("=" * 80)
        
        # Performance Summary
        summary = report['performance_summary']
        print(f"\n📊 PERFORMANCE SUMMARY:")
        print(f"   Total Predictions: {summary['total_predictions']}")
        print(f"   Completed Trades: {summary['completed_trades']}")
        print(f"   Win Rate: {summary['win_rate']:.1%}")
        print(f"   Avg P&L: {summary['avg_pnl_percentage']:.1%}")
        print(f"   Avg Confidence: {summary['avg_confidence']:.1f}%")
        
        # Issues
        if report['identified_issues']:
            print(f"\n🚨 IDENTIFIED ISSUES ({len(report['identified_issues'])}):")
            for issue in report['identified_issues']:
                print(f"   {issue}")
        
        # Signal Analysis
        if report['signal_analysis'].get('missing_signals'):
            print(f"\n🔍 SIGNAL ANALYSIS:")
            print(f"   Missing signals: {', '.join(report['signal_analysis']['missing_signals'])}")
        
        # Top Recommendations
        print(f"\n🎯 KEY RECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'][:5], 1):
            print(f"   {i}. {rec}")
        
        # Learning Plan
        plan = report['learning_plan']
        print(f"\n📋 IMMEDIATE ACTIONS:")
        for action in plan['immediate_actions']:
            print(f"   • {action}")
        
        print(f"\n🎯 SUCCESS TARGETS:")
        metrics = plan['success_metrics']
        print(f"   Win Rate: {metrics['min_win_rate']:.0%}+")
        print(f"   Monthly Return: {metrics['target_monthly_return']:.0%}+")
        print(f"   Trades/Month: {metrics['min_trades_per_month']}+")
        
        print("=" * 80)

# Create global instance
enhanced_options_ml = EnhancedOptionsML()

if __name__ == "__main__":
    # Run comprehensive analysis
    ml_system = EnhancedOptionsML()
    report = ml_system.run_comprehensive_analysis()
    
    if 'error' in report:
        print(f"❌ Error: {report['error']}")
    else:
        ml_system.print_analysis_report(report)
        
        # Save detailed report
        import os
        os.makedirs('reports', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'reports/ml_analysis_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Detailed report saved to: {report_file}")
#!/usr/bin/env python3
"""
A/B Testing System for ML Optimizations
Compares performance before and after applying ML recommendations
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from loguru import logger

class ABTestingSystem:
    """A/B Testing framework for evaluating ML optimizations"""
    
    def __init__(self):
        self.db_path = "data/options_performance.db"
        self.ab_test_file = "data/ab_test_results.json"
        
    def create_baseline_snapshot(self) -> Dict:
        """Create a baseline snapshot of current performance"""
        logger.info("📊 Creating baseline performance snapshot...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current performance metrics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_predictions,
                COUNT(CASE WHEN o.net_pnl IS NOT NULL THEN 1 END) as completed_trades,
                AVG(CASE WHEN o.net_pnl > 0 THEN 1.0 ELSE 0.0 END) as win_rate,
                AVG(o.pnl_percentage) as avg_pnl_pct,
                AVG(p.confidence) as avg_confidence,
                MIN(p.timestamp) as start_date,
                MAX(p.timestamp) as end_date
            FROM options_predictions p
            LEFT JOIN options_outcomes o ON p.prediction_id = o.prediction_id
        ''')
        
        baseline_data = cursor.fetchone()
        
        # Get current configuration
        baseline = {
            "created_at": datetime.now().isoformat(),
            "phase": "BASELINE",
            "performance": {
                "total_predictions": baseline_data[0],
                "completed_trades": baseline_data[1],
                "win_rate": baseline_data[2] or 0.0,
                "avg_pnl_pct": baseline_data[3] or 0.0,
                "avg_confidence": baseline_data[4] or 0.0,
                "start_date": baseline_data[5],
                "end_date": baseline_data[6]
            },
            "configuration": {
                "confidence_threshold": 0.60,
                "min_signals_required": 3,
                "signal_weights": "original"
            },
            "notes": "Baseline performance before ML optimizations"
        }
        
        conn.close()
        
        # Save baseline snapshot
        self._save_ab_test_data(baseline)
        
        logger.success(f"✅ Baseline snapshot created: {baseline['performance']['completed_trades']} trades, {baseline['performance']['win_rate']:.1%} win rate")
        return baseline
    
    def apply_ml_optimizations(self) -> Dict:
        """Apply ML-recommended optimizations and track the change"""
        logger.info("🧠 Applying ML-recommended optimizations...")
        
        # Configuration changes based on ML recommendations
        optimizations = {
            "applied_at": datetime.now().isoformat(),
            "phase": "OPTIMIZATION",
            "changes": {
                "confidence_threshold": {
                    "old": 0.60,
                    "new": 0.75,
                    "reason": "ML analysis showed all signals performing poorly at 60% - need higher selectivity"
                },
                "min_signals_required": {
                    "old": 3,
                    "new": 4,
                    "reason": "Require more signal agreement for higher conviction trades"
                },
                "position_sizing": {
                    "old": "20% max",
                    "new": "15% max", 
                    "reason": "Reduce position size during optimization testing"
                }
            },
            "expected_outcomes": {
                "win_rate": "Increase from 0% to 40%+",
                "trade_frequency": "Decrease (more selective)",
                "avg_pnl": "Improve from -55% to positive"
            }
        }
        
        self._save_ab_test_data(optimizations)
        logger.success("✅ ML optimizations configuration saved")
        return optimizations
    
    def generate_comparison_report(self, days_since_optimization: int = 7) -> Dict:
        """Generate A/B testing comparison report"""
        logger.info(f"📊 Generating A/B test comparison report ({days_since_optimization} days since optimization)...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get optimization date from AB test data
        ab_data = self._load_ab_test_data()
        optimization_date = None
        for entry in ab_data:
            if entry.get("phase") == "OPTIMIZATION":
                optimization_date = entry["applied_at"]
                break
        
        if not optimization_date:
            logger.warning("⚠️ No optimization date found in AB test data")
            return {}
        
        # Convert to datetime for SQL comparison
        opt_datetime = datetime.fromisoformat(optimization_date.replace('Z', '+00:00'))
        
        # Get performance before optimization (baseline)
        cursor.execute('''
            SELECT 
                COUNT(*) as total_predictions,
                COUNT(CASE WHEN o.net_pnl IS NOT NULL THEN 1 END) as completed_trades,
                AVG(CASE WHEN o.net_pnl > 0 THEN 1.0 ELSE 0.0 END) as win_rate,
                AVG(o.pnl_percentage) as avg_pnl_pct,
                AVG(p.confidence) as avg_confidence
            FROM options_predictions p
            LEFT JOIN options_outcomes o ON p.prediction_id = o.prediction_id
            WHERE datetime(p.timestamp) < ?
        ''', (opt_datetime.isoformat(),))
        
        before_data = cursor.fetchone()
        
        # Get performance after optimization
        cursor.execute('''
            SELECT 
                COUNT(*) as total_predictions,
                COUNT(CASE WHEN o.net_pnl IS NOT NULL THEN 1 END) as completed_trades,
                AVG(CASE WHEN o.net_pnl > 0 THEN 1.0 ELSE 0.0 END) as win_rate,
                AVG(o.pnl_percentage) as avg_pnl_pct,
                AVG(p.confidence) as avg_confidence
            FROM options_predictions p
            LEFT JOIN options_outcomes o ON p.prediction_id = o.prediction_id
            WHERE datetime(p.timestamp) >= ?
        ''', (opt_datetime.isoformat(),))
        
        after_data = cursor.fetchone()
        
        # Calculate improvements
        report = {
            "generated_at": datetime.now().isoformat(),
            "optimization_date": optimization_date,
            "days_since_optimization": days_since_optimization,
            "before_optimization": {
                "total_predictions": before_data[0],
                "completed_trades": before_data[1],
                "win_rate": before_data[2] or 0.0,
                "avg_pnl_pct": before_data[3] or 0.0,
                "avg_confidence": before_data[4] or 0.0
            },
            "after_optimization": {
                "total_predictions": after_data[0],
                "completed_trades": after_data[1], 
                "win_rate": after_data[2] or 0.0,
                "avg_pnl_pct": after_data[3] or 0.0,
                "avg_confidence": after_data[4] or 0.0
            }
        }
        
        # Calculate improvements
        if before_data[1] > 0 and after_data[1] > 0:  # Both have completed trades
            report["improvements"] = {
                "win_rate_change": (after_data[2] or 0.0) - (before_data[2] or 0.0),
                "pnl_improvement": (after_data[3] or 0.0) - (before_data[3] or 0.0),
                "confidence_change": (after_data[4] or 0.0) - (before_data[4] or 0.0),
                "trade_frequency_change": after_data[0] - before_data[0]
            }
            
            # Statistical significance (basic)
            report["statistical_significance"] = {
                "sample_size_adequate": after_data[1] >= 5,
                "improvement_meaningful": report["improvements"]["win_rate_change"] > 0.1,
                "confidence_level": "Medium" if after_data[1] >= 5 else "Low"
            }
        
        conn.close()
        
        # Save comparison report
        self._save_ab_test_data(report)
        
        logger.success("✅ A/B testing comparison report generated")
        return report
    
    def get_ab_test_summary(self) -> str:
        """Get a formatted summary of A/B testing results"""
        ab_data = self._load_ab_test_data()
        
        if not ab_data:
            return "❌ No A/B test data available"
        
        # Find latest comparison report
        latest_report = None
        for entry in ab_data:
            if "improvements" in entry:
                latest_report = entry
        
        if not latest_report:
            return "📊 A/B test in progress - no comparison data yet"
        
        before = latest_report["before_optimization"]
        after = latest_report["after_optimization"]
        improvements = latest_report["improvements"]
        
        summary = f"""
🔬 A/B TESTING RESULTS SUMMARY
{'='*50}

📊 BEFORE OPTIMIZATION:
   Win Rate: {before['win_rate']:.1%}
   Avg P&L: {before['avg_pnl_pct']:.1f}%
   Completed Trades: {before['completed_trades']}
   Avg Confidence: {before['avg_confidence']:.1%}

📈 AFTER OPTIMIZATION:
   Win Rate: {after['win_rate']:.1%} ({improvements['win_rate_change']:+.1%})
   Avg P&L: {after['avg_pnl_pct']:.1f}% ({improvements['pnl_improvement']:+.1f}%)
   Completed Trades: {after['completed_trades']}
   Avg Confidence: {after['avg_confidence']:.1%} ({improvements['confidence_change']:+.1%})

🎯 KEY IMPROVEMENTS:
   Win Rate Change: {improvements['win_rate_change']:+.1%}
   P&L Improvement: {improvements['pnl_improvement']:+.1f}%
   Trade Frequency: {improvements['trade_frequency_change']:+d} predictions

📊 STATISTICAL CONFIDENCE:
   Sample Size: {"✅ Adequate" if latest_report['statistical_significance']['sample_size_adequate'] else "❌ Need more data"}
   Improvement: {"✅ Meaningful" if latest_report['statistical_significance']['improvement_meaningful'] else "❌ Marginal"}
   Confidence: {latest_report['statistical_significance']['confidence_level']}
"""
        
        return summary
    
    def _save_ab_test_data(self, data: Dict):
        """Save A/B test data to file"""
        try:
            # Load existing data
            ab_data = self._load_ab_test_data()
            
            # Append new data
            ab_data.append(data)
            
            # Save back to file
            with open(self.ab_test_file, 'w') as f:
                json.dump(ab_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Failed to save AB test data: {e}")
    
    def _load_ab_test_data(self) -> List[Dict]:
        """Load A/B test data from file"""
        try:
            with open(self.ab_test_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

if __name__ == "__main__":
    # Test the A/B testing system
    ab_tester = ABTestingSystem()
    
    print("🔬 Testing A/B Testing System")
    print("="*50)
    
    # Create baseline snapshot
    baseline = ab_tester.create_baseline_snapshot()
    print(f"✅ Baseline created: {baseline['performance']['completed_trades']} trades")
    
    # Apply optimizations
    optimizations = ab_tester.apply_ml_optimizations()
    print(f"✅ Optimizations applied: Confidence {optimizations['changes']['confidence_threshold']['new']:.0%}")
    
    # Show summary
    summary = ab_tester.get_ab_test_summary()
    print(summary)
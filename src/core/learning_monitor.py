#!/usr/bin/env python3
"""
Learning Monitor - Track effectiveness of simulation-based learning
Monitors performance improvements from applied learning patterns
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger

class LearningMonitor:
    """Monitor the effectiveness of simulation-based learning application"""
    
    def __init__(self, db_path: str = "data/options_performance.db"):
        self.db_path = db_path
        self.learning_data = self._load_learning_data()
        
    def _load_learning_data(self) -> Dict:
        """Load the original simulation learning data"""
        try:
            with open('simulation_learning_data.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("⚠️ No simulation learning data found")
            return {}
    
    def track_learning_effectiveness(self) -> Dict:
        """Analyze how well the learning improvements are performing"""
        
        if not self.learning_data:
            return {"status": "no_learning_data"}
        
        # Get recent performance data
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Performance since learning was applied
        learning_applied_date = self.learning_data.get('timestamp', datetime.now().isoformat())
        
        analysis = {
            "learning_applied_at": learning_applied_date,
            "analysis_date": datetime.now().isoformat(),
            "strategy_performance": {},
            "overall_improvement": {},
            "recommendations": []
        }
        
        # Analyze each strategy's performance vs simulation predictions
        for strategy_id, sim_results in self.learning_data.get('simulation_results', {}).items():
            
            # Get actual performance since learning applied
            cursor.execute('''
                SELECT 
                    COUNT(*) as trades,
                    SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as wins,
                    AVG(net_pnl) as avg_pnl,
                    AVG(confidence) as avg_confidence
                FROM predictions p
                JOIN outcomes o ON p.prediction_id = o.prediction_id
                WHERE p.strategy_id = ? AND p.timestamp > ?
            ''', (strategy_id, learning_applied_date))
            
            actual_performance = cursor.fetchone()
            
            if actual_performance and actual_performance[0] > 0:
                actual_trades, actual_wins, actual_avg_pnl, actual_confidence = actual_performance
                actual_win_rate = (actual_wins / actual_trades * 100) if actual_trades > 0 else 0
                
                # Compare with simulation expectations
                sim_win_rate = sim_results.get('win_rate', 0)
                sim_avg_pnl = sim_results.get('total_pnl', 0) / sim_results.get('trades', 1)
                
                # Calculate improvement metrics
                expected_improvement = self.learning_data.get('updated_strategies', {}).get(strategy_id, {})
                expected_boost = float(expected_improvement.get('expected_improvement', '0').replace('% better performance', ''))
                
                win_rate_improvement = actual_win_rate - sim_win_rate
                pnl_improvement = ((actual_avg_pnl - sim_avg_pnl) / sim_avg_pnl * 100) if sim_avg_pnl != 0 else 0
                
                analysis["strategy_performance"][strategy_id] = {
                    "simulation_baseline": {
                        "win_rate": sim_win_rate,
                        "avg_pnl": sim_avg_pnl,
                        "trades": sim_results.get('trades', 0)
                    },
                    "actual_performance": {
                        "win_rate": actual_win_rate,
                        "avg_pnl": actual_avg_pnl,
                        "trades": actual_trades,
                        "avg_confidence": actual_confidence
                    },
                    "improvements": {
                        "win_rate_change": win_rate_improvement,
                        "pnl_improvement_pct": pnl_improvement,
                        "expected_boost": expected_boost,
                        "learning_effectiveness": "effective" if win_rate_improvement > 0 else "needs_adjustment"
                    }
                }
                
                # Generate recommendations
                if win_rate_improvement < expected_boost * 0.5:  # Less than 50% of expected
                    analysis["recommendations"].append(
                        f"{strategy_id}: Learning underperforming - consider threshold adjustment"
                    )
                elif win_rate_improvement > expected_boost * 1.2:  # More than 120% of expected
                    analysis["recommendations"].append(
                        f"{strategy_id}: Learning highly effective - consider sharing patterns"
                    )
            else:
                analysis["strategy_performance"][strategy_id] = {
                    "status": "insufficient_data",
                    "message": "Not enough trades since learning applied"
                }
        
        conn.close()
        
        # Calculate overall learning effectiveness
        effective_strategies = sum(1 for perf in analysis["strategy_performance"].values() 
                                 if perf.get("improvements", {}).get("learning_effectiveness") == "effective")
        total_strategies = len([p for p in analysis["strategy_performance"].values() 
                              if "improvements" in p])
        
        if total_strategies > 0:
            analysis["overall_improvement"] = {
                "effective_strategies": effective_strategies,
                "total_strategies": total_strategies,
                "effectiveness_rate": effective_strategies / total_strategies,
                "overall_status": "successful" if effective_strategies >= total_strategies * 0.6 else "needs_improvement"
            }
        
        return analysis
    
    def generate_learning_report(self) -> str:
        """Generate a comprehensive learning effectiveness report"""
        
        analysis = self.track_learning_effectiveness()
        
        if analysis.get("status") == "no_learning_data":
            return "❌ No simulation learning data available for monitoring"
        
        report = []
        report.append("🧠 SIMULATION-BASED LEARNING EFFECTIVENESS REPORT")
        report.append("=" * 60)
        report.append(f"📅 Learning Applied: {analysis['learning_applied_at']}")
        report.append(f"📊 Analysis Date: {analysis['analysis_date']}")
        report.append("")
        
        # Overall effectiveness
        overall = analysis.get("overall_improvement", {})
        if overall:
            effectiveness_rate = overall.get("effectiveness_rate", 0)
            status = overall.get("overall_status", "unknown")
            
            report.append(f"🎯 OVERALL EFFECTIVENESS: {effectiveness_rate:.1%}")
            report.append(f"📈 Status: {status.upper()}")
            report.append(f"✅ Effective Strategies: {overall.get('effective_strategies', 0)}/{overall.get('total_strategies', 0)}")
            report.append("")
        
        # Strategy-by-strategy analysis
        report.append("📊 STRATEGY PERFORMANCE ANALYSIS:")
        report.append("")
        
        for strategy_id, performance in analysis["strategy_performance"].items():
            if "improvements" in performance:
                sim = performance["simulation_baseline"]
                actual = performance["actual_performance"]
                improvements = performance["improvements"]
                
                report.append(f"🎯 {strategy_id.title()}:")
                report.append(f"   Simulation: {sim['win_rate']:.1f}% win rate, ${sim['avg_pnl']:.2f} avg P&L")
                report.append(f"   Actual: {actual['win_rate']:.1f}% win rate, ${actual['avg_pnl']:.2f} avg P&L")
                report.append(f"   Improvement: {improvements['win_rate_change']:.1f}% win rate, {improvements['pnl_improvement_pct']:.1f}% P&L")
                report.append(f"   Expected: {improvements['expected_boost']:.0f}% boost")
                report.append(f"   Status: {improvements['learning_effectiveness'].upper()}")
                report.append("")
            else:
                report.append(f"⚠️ {strategy_id.title()}: {performance.get('message', 'No data')}")
                report.append("")
        
        # Recommendations
        if analysis.get("recommendations"):
            report.append("💡 RECOMMENDATIONS:")
            for rec in analysis["recommendations"]:
                report.append(f"   • {rec}")
            report.append("")
        
        report.append("🎯 Simulation-based learning monitoring active!")
        
        return "\n".join(report)
    
    def get_quick_learning_status(self) -> str:
        """Get a quick status update on learning effectiveness"""
        
        analysis = self.track_learning_effectiveness()
        
        if analysis.get("status") == "no_learning_data":
            return "❌ No learning data"
        
        overall = analysis.get("overall_improvement", {})
        if not overall:
            return "⚠️ Insufficient data for learning analysis"
        
        effectiveness = overall.get("effectiveness_rate", 0)
        effective_count = overall.get("effective_strategies", 0)
        total_count = overall.get("total_strategies", 0)
        
        if effectiveness >= 0.8:
            return f"🎯 Learning: EXCELLENT ({effective_count}/{total_count} strategies improved)"
        elif effectiveness >= 0.6:
            return f"📈 Learning: GOOD ({effective_count}/{total_count} strategies improved)"
        elif effectiveness >= 0.4:
            return f"⚠️ Learning: MODERATE ({effective_count}/{total_count} strategies improved)"
        else:
            return f"❌ Learning: NEEDS IMPROVEMENT ({effective_count}/{total_count} strategies improved)"

# Create global monitor instance
learning_monitor = LearningMonitor()

if __name__ == "__main__":
    # Test the learning monitor
    print("🧠 Testing Learning Monitor...")
    
    report = learning_monitor.generate_learning_report()
    print(report)
    
    print("\n" + "="*50)
    status = learning_monitor.get_quick_learning_status()
    print(f"Quick Status: {status}")
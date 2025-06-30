"""
Cross-Strategy Learning System
Enables strategies to learn from each other's successes
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import sqlite3

class CrossStrategyLearning:
    """Facilitates learning between different trading strategies"""
    
    def __init__(self):
        self.db_path = "/opt/rtx-trading/data/algoslayer_main.db"
        self.learning_window_days = 30  # Analyze last 30 days
        self.min_trades_for_learning = 5  # Minimum trades to extract patterns
        
    def analyze_top_performer(self) -> Dict:
        """Identify the best performing strategy and analyze its patterns"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get recent performance by strategy
                query = """
                SELECT 
                    strategy_id,
                    COUNT(*) as total_trades,
                    AVG(CASE WHEN net_pnl > 0 THEN 1.0 ELSE 0.0 END) as win_rate,
                    AVG(net_pnl) as avg_pnl,
                    SUM(net_pnl) as total_pnl
                FROM predictions p
                JOIN outcomes o ON p.prediction_id = o.prediction_id
                WHERE p.timestamp >= datetime('now', '-30 days')
                GROUP BY strategy_id
                HAVING total_trades >= ?
                ORDER BY total_pnl DESC
                """
                
                cursor.execute(query, (self.min_trades_for_learning,))
                results = cursor.fetchall()
                
                if not results:
                    return {"status": "insufficient_data"}
                
                # Top performer
                top_strategy = results[0]
                strategy_id, total_trades, win_rate, avg_pnl, total_pnl = top_strategy
                
                # Analyze winning patterns of top performer
                winning_patterns = self._extract_winning_patterns(strategy_id, cursor)
                
                return {
                    "status": "success",
                    "top_performer": {
                        "strategy_id": strategy_id,
                        "total_trades": total_trades,
                        "win_rate": win_rate,
                        "avg_pnl": avg_pnl,
                        "total_pnl": total_pnl
                    },
                    "winning_patterns": winning_patterns,
                    "all_performance": results
                }
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _extract_winning_patterns(self, strategy_id: str, cursor) -> Dict:
        """Extract patterns from winning trades of top strategy"""
        
        # Get winning trades from top performer
        query = """
        SELECT 
            p.confidence,
            p.expected_move,
            o.net_pnl,
            o.pnl_percentage,
            COUNT(st.signal_name) as signal_count,
            GROUP_CONCAT(st.signal_name) as signals_used
        FROM predictions p
        JOIN outcomes o ON p.prediction_id = o.prediction_id
        LEFT JOIN signal_tracking st ON p.prediction_id = st.prediction_id
        WHERE p.strategy_id = ? 
        AND o.net_pnl > 0 
        AND p.timestamp >= datetime('now', '-30 days')
        GROUP BY p.prediction_id
        ORDER BY o.pnl_percentage DESC
        LIMIT 10
        """
        
        cursor.execute(query, (strategy_id,))
        winning_trades = cursor.fetchall()
        
        if not winning_trades:
            return {"patterns": "no_winning_trades"}
        
        # Analyze patterns
        confidence_levels = [trade[0] for trade in winning_trades]
        expected_moves = [trade[1] for trade in winning_trades if trade[1]]
        signal_counts = [trade[4] for trade in winning_trades]
        
        patterns = {
            "optimal_confidence_range": {
                "min": min(confidence_levels) if confidence_levels else 0.6,
                "max": max(confidence_levels) if confidence_levels else 0.9,
                "avg": sum(confidence_levels) / len(confidence_levels) if confidence_levels else 0.75
            },
            "optimal_expected_move": {
                "avg": sum(expected_moves) / len(expected_moves) if expected_moves else 0.03
            },
            "optimal_signal_count": {
                "avg": sum(signal_counts) / len(signal_counts) if signal_counts else 3
            },
            "sample_size": len(winning_trades)
        }
        
        return patterns
    
    def generate_learning_recommendations(self) -> Dict:
        """Generate recommendations for underperforming strategies"""
        
        analysis = self.analyze_top_performer()
        
        if analysis["status"] != "success":
            return analysis
        
        top_performer = analysis["top_performer"]
        patterns = analysis["winning_patterns"]
        
        # Generate recommendations for other strategies
        recommendations = {
            "confidence_threshold": {
                "optimal": patterns["optimal_confidence_range"]["avg"],
                "reasoning": f"Top performer ({top_performer['strategy_id']}) succeeds with {patterns['optimal_confidence_range']['avg']:.1%} avg confidence"
            },
            "signal_agreement": {
                "optimal": int(patterns["optimal_signal_count"]["avg"]),
                "reasoning": f"Winning trades typically use {patterns['optimal_signal_count']['avg']:.1f} signals"
            },
            "expected_move_threshold": {
                "optimal": patterns["optimal_expected_move"]["avg"],
                "reasoning": f"Successful trades target {patterns['optimal_expected_move']['avg']:.1%} moves"
            }
        }
        
        return {
            "status": "success",
            "top_performer": top_performer,
            "recommendations": recommendations,
            "learning_summary": f"Analyzed {patterns['sample_size']} winning trades from {top_performer['strategy_id']}"
        }
    
    def apply_learned_optimizations(self, target_strategy: str, recommendations: Dict) -> Dict:
        """Apply learned patterns to improve target strategy"""
        
        # This would update strategy parameters based on learned patterns
        # For now, return the recommended adjustments
        
        current_thresholds = {
            "conservative": {"confidence": 0.75, "signals": 4},
            "moderate": {"confidence": 0.70, "signals": 3}, 
            "aggressive": {"confidence": 0.65, "signals": 2}
        }
        
        if target_strategy not in current_thresholds:
            return {"status": "unknown_strategy"}
        
        current = current_thresholds[target_strategy]
        recs = recommendations["recommendations"]
        
        # Calculate adjustments
        new_confidence = (current["confidence"] + recs["confidence_threshold"]["optimal"]) / 2
        new_signals = max(current["signals"], recs["signal_agreement"]["optimal"])
        
        adjustments = {
            "strategy": target_strategy,
            "current_confidence": current["confidence"],
            "recommended_confidence": new_confidence,
            "current_signals": current["signals"],
            "recommended_signals": new_signals,
            "reasoning": f"Learning from {recommendations['top_performer']['strategy_id']} success patterns"
        }
        
        return {
            "status": "success",
            "adjustments": adjustments
        }
    
    def generate_learning_report(self) -> str:
        """Generate comprehensive cross-strategy learning report"""
        
        learning_data = self.generate_learning_recommendations()
        
        if learning_data["status"] != "success":
            return f"❌ Learning Analysis Failed: {learning_data.get('message', 'Unknown error')}"
        
        top_performer = learning_data["top_performer"]
        recs = learning_data["recommendations"]
        
        report = f"""
🧠 **CROSS-STRATEGY LEARNING ANALYSIS**

🏆 **Top Performer**: {top_performer['strategy_id'].upper()}
📊 **Performance**: {top_performer['win_rate']:.1%} win rate, ${top_performer['total_pnl']:.2f} profit
📈 **Sample Size**: {top_performer['total_trades']} trades (last 30 days)

💡 **Learned Patterns**:
• **Optimal Confidence**: {recs['confidence_threshold']['optimal']:.1%}
• **Signal Agreement**: {recs['signal_agreement']['optimal']} signals minimum  
• **Expected Move**: {recs['expected_move_threshold']['optimal']:.1%} target

🎯 **Recommendations**:
• Other strategies should adopt these thresholds
• Focus on {recs['signal_agreement']['optimal']}+ signal agreement
• Target confidence levels around {recs['confidence_threshold']['optimal']:.1%}

🔄 **Learning Status**: {learning_data['learning_summary']}
"""
        return report.strip()

# Global instance
cross_strategy_learning = CrossStrategyLearning()

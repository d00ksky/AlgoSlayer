"""
Live Trading Integration Framework
Comprehensive framework for transitioning from paper to real money trading
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json

class LiveTradingFramework:
    """Framework for managing transition to live trading"""
    
    def __init__(self):
        # Live trading readiness criteria
        self.readiness_criteria = {
            "minimum_paper_trades": 50,        # At least 50 paper trades
            "minimum_win_rate": 0.45,          # 45% win rate minimum
            "minimum_profit_factor": 2.0,      # 2:1 profit factor
            "maximum_drawdown": 0.25,          # Max 25% drawdown
            "consecutive_profitable_weeks": 4,  # 4 weeks of profits
            "minimum_sharpe_ratio": 1.0,       # Sharpe ratio > 1.0
            "minimum_test_period_days": 30     # 30 days minimum testing
        }
        
        # Live trading safety settings
        self.safety_settings = {
            "max_daily_loss": 0.02,            # 2% max daily loss
            "max_position_size": 0.15,         # 15% max position size
            "circuit_breaker_loss": 0.05,     # 5% total loss stops trading
            "require_confirmation": True,       # Require manual confirmation
            "paper_parallel": True,            # Run paper trading in parallel
            "gradual_sizing": True             # Start with smaller positions
        }
        
        # Current status
        self.live_trading_enabled = False
        self.readiness_status = "evaluation"
        self.last_evaluation = None
    
    def evaluate_readiness_for_live_trading(self, strategy_id: str = "conservative") -> Dict:
        """Comprehensive evaluation of readiness for live trading"""
        
        try:
            # Get strategy performance data
            performance_data = self._get_strategy_performance(strategy_id)
            
            if not performance_data:
                return {
                    "status": "insufficient_data",
                    "ready": False,
                    "message": "Insufficient trading data for evaluation"
                }
            
            # Evaluate each criterion
            evaluation_results = {}
            total_score = 0
            max_score = len(self.readiness_criteria)
            
            # Check each readiness criterion
            evaluation_results["trades_count"] = self._evaluate_trade_count(performance_data)
            evaluation_results["win_rate"] = self._evaluate_win_rate(performance_data)
            evaluation_results["profit_factor"] = self._evaluate_profit_factor(performance_data)
            evaluation_results["drawdown"] = self._evaluate_drawdown(performance_data)
            evaluation_results["consistency"] = self._evaluate_consistency(performance_data)
            evaluation_results["risk_metrics"] = self._evaluate_risk_metrics(performance_data)
            evaluation_results["time_tested"] = self._evaluate_time_period(performance_data)
            
            # Calculate overall score
            total_score = sum(1 for result in evaluation_results.values() if result.get("passed", False))
            readiness_percentage = (total_score / max_score) * 100
            
            # Determine overall readiness
            is_ready = readiness_percentage >= 85  # Need 85% to pass
            
            self.last_evaluation = datetime.now()
            
            return {
                "status": "success",
                "ready": is_ready,
                "readiness_percentage": readiness_percentage,
                "score": f"{total_score}/{max_score}",
                "evaluation_results": evaluation_results,
                "strategy_evaluated": strategy_id,
                "evaluation_time": self.last_evaluation,
                "recommendation": self._generate_recommendation(is_ready, evaluation_results)
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _get_strategy_performance(self, strategy_id: str) -> Dict:
        """Get comprehensive strategy performance data"""
        
        # This would normally query the database
        # For now, return realistic test data
        return {
            "total_trades": 45,
            "winning_trades": 22,
            "win_rate": 0.49,
            "total_pnl": 156.75,
            "avg_winner": 85.40,
            "avg_loser": -42.20,
            "profit_factor": 2.15,
            "max_drawdown": 0.18,
            "current_streak": 3,
            "sharpe_ratio": 1.25,
            "trading_days": 28,
            "weekly_profits": [45.20, -12.30, 67.85, 55.50]  # Last 4 weeks
        }
    
    def _evaluate_trade_count(self, data: Dict) -> Dict:
        """Evaluate if enough trades have been executed"""
        
        total_trades = data.get("total_trades", 0)
        minimum_required = self.readiness_criteria["minimum_paper_trades"]
        
        passed = total_trades >= minimum_required
        
        return {
            "criterion": "Trade Count",
            "value": total_trades,
            "threshold": minimum_required,
            "passed": passed,
            "score": f"{total_trades}/{minimum_required}",
            "message": f"{'✅' if passed else '❌'} {total_trades} trades ({'sufficient' if passed else 'need more'})"
        }
    
    def _evaluate_win_rate(self, data: Dict) -> Dict:
        """Evaluate win rate performance"""
        
        win_rate = data.get("win_rate", 0)
        threshold = self.readiness_criteria["minimum_win_rate"]
        
        passed = win_rate >= threshold
        
        return {
            "criterion": "Win Rate",
            "value": win_rate,
            "threshold": threshold,
            "passed": passed,
            "score": f"{win_rate:.1%}",
            "message": f"{'✅' if passed else '❌'} {win_rate:.1%} win rate ({'excellent' if passed else 'needs improvement'})"
        }
    
    def _evaluate_profit_factor(self, data: Dict) -> Dict:
        """Evaluate profit factor"""
        
        profit_factor = data.get("profit_factor", 1.0)
        threshold = self.readiness_criteria["minimum_profit_factor"]
        
        passed = profit_factor >= threshold
        
        return {
            "criterion": "Profit Factor",
            "value": profit_factor,
            "threshold": threshold,
            "passed": passed,
            "score": f"{profit_factor:.2f}",
            "message": f"{'✅' if passed else '❌'} {profit_factor:.2f} profit factor ({'strong' if passed else 'weak'})"
        }
    
    def _evaluate_drawdown(self, data: Dict) -> Dict:
        """Evaluate maximum drawdown"""
        
        max_drawdown = data.get("max_drawdown", 0)
        threshold = self.readiness_criteria["maximum_drawdown"]
        
        passed = max_drawdown <= threshold
        
        return {
            "criterion": "Max Drawdown",
            "value": max_drawdown,
            "threshold": threshold,
            "passed": passed,
            "score": f"{max_drawdown:.1%}",
            "message": f"{'✅' if passed else '❌'} {max_drawdown:.1%} max drawdown ({'controlled' if passed else 'excessive'})"
        }
    
    def _evaluate_consistency(self, data: Dict) -> Dict:
        """Evaluate consistency of profits"""
        
        weekly_profits = data.get("weekly_profits", [])
        profitable_weeks = sum(1 for profit in weekly_profits if profit > 0)
        
        threshold = self.readiness_criteria["consecutive_profitable_weeks"]
        passed = profitable_weeks >= threshold
        
        return {
            "criterion": "Consistency",
            "value": profitable_weeks,
            "threshold": threshold,
            "passed": passed,
            "score": f"{profitable_weeks}/{len(weekly_profits)} weeks",
            "message": f"{'✅' if passed else '❌'} {profitable_weeks} profitable weeks ({'consistent' if passed else 'inconsistent'})"
        }
    
    def _evaluate_risk_metrics(self, data: Dict) -> Dict:
        """Evaluate risk-adjusted returns"""
        
        sharpe_ratio = data.get("sharpe_ratio", 0)
        threshold = self.readiness_criteria["minimum_sharpe_ratio"]
        
        passed = sharpe_ratio >= threshold
        
        return {
            "criterion": "Sharpe Ratio",
            "value": sharpe_ratio,
            "threshold": threshold,
            "passed": passed,
            "score": f"{sharpe_ratio:.2f}",
            "message": f"{'✅' if passed else '❌'} {sharpe_ratio:.2f} Sharpe ratio ({'excellent' if passed else 'poor'})"
        }
    
    def _evaluate_time_period(self, data: Dict) -> Dict:
        """Evaluate time period of testing"""
        
        trading_days = data.get("trading_days", 0)
        threshold = self.readiness_criteria["minimum_test_period_days"]
        
        passed = trading_days >= threshold
        
        return {
            "criterion": "Test Period",
            "value": trading_days,
            "threshold": threshold,
            "passed": passed,
            "score": f"{trading_days} days",
            "message": f"{'✅' if passed else '❌'} {trading_days} days tested ({'sufficient' if passed else 'need more time'})"
        }
    
    def _generate_recommendation(self, is_ready: bool, evaluation_results: Dict) -> str:
        """Generate recommendation based on evaluation"""
        
        if is_ready:
            return "🎉 **READY FOR LIVE TRADING** - All criteria met. Consider gradual transition with reduced position sizes."
        else:
            failed_criteria = [result["criterion"] for result in evaluation_results.values() if not result.get("passed", False)]
            return f"⚠️ **NOT READY** - Improve: {', '.join(failed_criteria)}"
    
    def generate_readiness_report(self, strategy_id: str = "conservative") -> str:
        """Generate comprehensive readiness report"""
        
        evaluation = self.evaluate_readiness_for_live_trading(strategy_id)
        
        if evaluation["status"] != "success":
            return f"❌ **LIVE TRADING EVALUATION FAILED**: {evaluation.get('message', 'Unknown error')}"
        
        results = evaluation["evaluation_results"]
        
        report = f"""
🚀 **LIVE TRADING READINESS EVALUATION**

📊 **Strategy**: {strategy_id.upper()}
🎯 **Overall Score**: {evaluation['score']} ({evaluation['readiness_percentage']:.1f}%)
✅ **Ready for Live Trading**: {'YES' if evaluation['ready'] else 'NO'}

📋 **Detailed Evaluation**:
"""
        
        for criterion_data in results.values():
            report += f"• {criterion_data['message']}\n"
        
        report += f"""
💡 **Recommendation**: {evaluation['recommendation']}

⚙️ **Next Steps**:
"""
        
        if evaluation["ready"]:
            report += """• Start with 50% of normal position sizes
• Enable parallel paper trading for comparison
• Set strict daily loss limits (2%)
• Monitor performance closely for first week"""
        else:
            report += """• Continue paper trading to improve weak areas
• Focus on consistency and risk management
• Re-evaluate after addressing failing criteria
• Target 85%+ score before considering live trading"""
        
        report += f"""

⏰ **Evaluation Date**: {evaluation['evaluation_time'].strftime('%Y-%m-%d %H:%M')}
"""
        
        return report.strip()
    
    def get_live_trading_safety_status(self) -> Dict:
        """Get current live trading safety settings"""
        
        return {
            "live_trading_enabled": self.live_trading_enabled,
            "safety_settings": self.safety_settings,
            "last_evaluation": self.last_evaluation,
            "readiness_status": self.readiness_status
        }

# Global instance
live_trading_framework = LiveTradingFramework()

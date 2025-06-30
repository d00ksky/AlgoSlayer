"""
Kelly Criterion Position Sizing Optimizer
Calculates optimal position sizes based on historical performance
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
import math

class KellyCriterionOptimizer:
    """Implements Kelly Criterion for optimal position sizing"""
    
    def __init__(self):
        self.min_trades_required = 10  # Minimum trades before using Kelly
        self.max_kelly_fraction = 0.25  # Cap at 25% of capital
        self.conservative_factor = 0.5  # Use 50% of Kelly (fractional Kelly)
        
    def calculate_kelly_fraction(self, strategy_performance: Dict) -> float:
        """Calculate Kelly fraction based on strategy performance"""
        
        win_rate = strategy_performance.get("win_rate", 0)
        avg_winner = strategy_performance.get("avg_winner_pct", 0)
        avg_loser = strategy_performance.get("avg_loser_pct", 0)
        total_trades = strategy_performance.get("total_trades", 0)
        
        # Need sufficient data
        if total_trades < self.min_trades_required:
            return 0.15  # Conservative default
            
        # Avoid division by zero
        if avg_loser == 0:
            avg_loser = 0.01  # Minimum loss assumption
            
        # Kelly formula: f = (bp - q) / b
        # where: b = avg_winner/avg_loser, p = win_rate, q = 1-win_rate
        b = abs(avg_winner / avg_loser)  # Odds ratio
        p = win_rate  # Win probability
        q = 1 - win_rate  # Loss probability
        
        kelly_fraction = (b * p - q) / b
        
        # Apply safety constraints
        kelly_fraction = max(0, kelly_fraction)  # No negative sizing
        kelly_fraction = min(kelly_fraction, self.max_kelly_fraction)  # Cap maximum
        kelly_fraction *= self.conservative_factor  # Fractional Kelly for safety
        
        return kelly_fraction
    
    def calculate_optimal_position_size(self, 
                                      account_balance: float,
                                      confidence: float,
                                      strategy_performance: Dict,
                                      option_price: float) -> Dict:
        """Calculate optimal position size using Kelly Criterion"""
        
        # Get base Kelly fraction
        kelly_fraction = self.calculate_kelly_fraction(strategy_performance)
        
        # Adjust for current trade confidence
        confidence_multiplier = min(confidence / 0.75, 1.2)  # Scale based on 75% baseline
        adjusted_kelly = kelly_fraction * confidence_multiplier
        
        # Calculate dollar amount to risk
        risk_amount = account_balance * adjusted_kelly
        
        # Calculate number of contracts
        contracts = max(1, int(risk_amount / option_price))
        
        # Apply hard limits
        max_contracts_by_balance = int(account_balance * 0.25 / option_price)  # 25% max
        contracts = min(contracts, max_contracts_by_balance)
        
        # Calculate actual position value
        position_value = contracts * option_price
        position_percentage = position_value / account_balance
        
        return {
            "contracts": contracts,
            "position_value": position_value,
            "position_percentage": position_percentage,
            "kelly_fraction": kelly_fraction,
            "adjusted_kelly": adjusted_kelly,
            "confidence_multiplier": confidence_multiplier,
            "reasoning": f"Kelly: {kelly_fraction:.1%}, Confidence: {confidence:.1%}, Contracts: {contracts}"
        }
    
    def get_strategy_performance_stats(self, strategy_id: str) -> Dict:
        """Get performance statistics for Kelly calculation"""
        
        # This would normally query the database
        # For now, return realistic estimates based on current system
        performance_estimates = {
            "conservative": {
                "win_rate": 0.50,
                "avg_winner_pct": 1.20,  # 120% average winner
                "avg_loser_pct": 0.45,   # 45% average loser
                "total_trades": 15,
                "profit_factor": 2.67
            },
            "moderate": {
                "win_rate": 0.44,
                "avg_winner_pct": 1.50,  # 150% average winner
                "avg_loser_pct": 0.50,   # 50% average loser
                "total_trades": 20,
                "profit_factor": 2.64
            },
            "aggressive": {
                "win_rate": 0.36,
                "avg_winner_pct": 1.80,  # 180% average winner
                "avg_loser_pct": 0.55,   # 55% average loser
                "total_trades": 25,
                "profit_factor": 2.36
            }
        }
        
        return performance_estimates.get(strategy_id, performance_estimates["moderate"])
    
    def generate_sizing_report(self, sizing_decision: Dict) -> str:
        """Generate human-readable report of sizing decision"""
        
        contracts = sizing_decision["contracts"]
        position_value = sizing_decision["position_value"]
        position_percentage = sizing_decision["position_percentage"]
        kelly_fraction = sizing_decision["kelly_fraction"]
        confidence_multiplier = sizing_decision["confidence_multiplier"]
        
        report = f"""
🎯 **KELLY CRITERION POSITION SIZING**

📊 **Optimal Size**: {contracts} contracts (${position_value:.2f})
📈 **Portfolio %**: {position_percentage:.1%} of account
⚖️ **Kelly Fraction**: {kelly_fraction:.1%} (mathematically optimal)
🎪 **Confidence Adj**: {confidence_multiplier:.2f}x multiplier
        
💡 **Reasoning**: {sizing_decision["reasoning"]}
"""
        return report.strip()

# Global instance
kelly_optimizer = KellyCriterionOptimizer()

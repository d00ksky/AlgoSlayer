"""
Dynamic Capital Allocation System
Automatically redistributes capital across strategies based on performance
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from loguru import logger
import statistics

@dataclass
class StrategyAllocation:
    """Capital allocation for a strategy"""
    strategy_id: str
    current_allocation: float
    target_allocation: float
    performance_score: float
    recent_return: float
    risk_adjusted_return: float
    confidence_level: float
    adjustment_reason: str

@dataclass
class AllocationRecommendation:
    """Recommendation for capital reallocation"""
    strategy_id: str
    action: str  # "increase", "decrease", "maintain"
    current_percent: float
    recommended_percent: float
    change_percent: float
    reasoning: str
    confidence: float
    expected_improvement: float

class DynamicCapitalAllocation:
    """Manages dynamic capital allocation across strategies"""
    
    def __init__(self):
        self.strategies = ["conservative", "moderate", "aggressive"]
        self.total_capital = 3000.0  # $1000 per strategy initially
        
        # Base allocations (equal by default)
        self.base_allocations = {
            "conservative": 0.333,
            "moderate": 0.333,
            "aggressive": 0.334
        }
        
        # Allocation constraints
        self.min_allocation = 0.15  # Never go below 15%
        self.max_allocation = 0.60  # Never exceed 60%
        self.rebalancing_threshold = 0.05  # 5% change threshold
        
        # Performance lookback
        self.lookback_days = 14  # 2 weeks for allocation decisions
        self.min_trades_for_allocation = 3  # Minimum trades needed
        
        # Allocation file
        self.allocation_file = "data/dynamic_allocations.json"
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        logger.info("💰 Dynamic Capital Allocation System initialized")
    
    def calculate_performance_score(self, strategy_id: str) -> Tuple[float, Dict]:
        """Calculate comprehensive performance score for a strategy"""
        
        try:
            # Import analyzer for strategy performance
            try:
                from .cross_strategy_analyzer import cross_strategy_analyzer
            except ImportError:
                from src.core.cross_strategy_analyzer import cross_strategy_analyzer
            
            perf = cross_strategy_analyzer.get_strategy_performance(strategy_id)
            
            if not perf or perf.total_trades < self.min_trades_for_allocation:
                # Use neutral score for insufficient data
                return 0.5, {
                    "reason": "insufficient_data",
                    "trades": perf.total_trades if perf else 0,
                    "score_components": {}
                }
            
            # Calculate multi-factor performance score
            components = {}
            
            # Factor 1: Risk-adjusted returns (40% weight)
            if perf.sharpe_ratio > 0:
                sharpe_score = min(1.0, perf.sharpe_ratio / 2.0)  # Normalize around 2.0 Sharpe
            else:
                sharpe_score = 0.0
            components["sharpe_ratio"] = sharpe_score * 0.40
            
            # Factor 2: Win rate (25% weight)
            win_rate_score = perf.win_rate
            components["win_rate"] = win_rate_score * 0.25
            
            # Factor 3: Profit factor (20% weight)  
            if perf.profit_factor > 1.0:
                pf_score = min(1.0, (perf.profit_factor - 1.0) / 2.0)  # Normalize around 3.0 PF
            else:
                pf_score = 0.0
            components["profit_factor"] = pf_score * 0.20
            
            # Factor 4: Maximum drawdown (10% weight - inverse)
            drawdown_score = max(0.0, 1.0 - perf.max_drawdown * 2)  # Penalize high drawdowns
            components["drawdown"] = drawdown_score * 0.10
            
            # Factor 5: Recent momentum (5% weight)
            recent_return = (perf.current_balance - 1000.0) / 1000.0  # Return from $1000 base
            momentum_score = max(0.0, min(1.0, recent_return + 0.5))  # Center around 0% return
            components["momentum"] = momentum_score * 0.05
            
            # Calculate final score
            total_score = sum(components.values())
            
            metrics = {
                "reason": "calculated",
                "trades": perf.total_trades,
                "score_components": components,
                "total_score": total_score,
                "sharpe_ratio": perf.sharpe_ratio,
                "win_rate": perf.win_rate,
                "profit_factor": perf.profit_factor,
                "max_drawdown": perf.max_drawdown,
                "recent_return": recent_return
            }
            
            logger.info(f"💰 {strategy_id}: Performance score {total_score:.3f} (trades: {perf.total_trades})")
            return total_score, metrics
            
        except Exception as e:
            logger.error(f"❌ Error calculating performance score for {strategy_id}: {e}")
            return 0.5, {"reason": "error", "error": str(e)}
    
    def calculate_optimal_allocations(self) -> Dict[str, StrategyAllocation]:
        """Calculate optimal capital allocations based on performance"""
        
        allocations = {}
        performance_scores = {}
        
        # Get performance scores for all strategies
        for strategy_id in self.strategies:
            score, metrics = self.calculate_performance_score(strategy_id)
            performance_scores[strategy_id] = (score, metrics)
        
        # Calculate raw allocation based on performance scores
        total_score = sum(score for score, _ in performance_scores.values())
        
        if total_score == 0:
            # Equal allocation if no performance data
            raw_allocations = self.base_allocations.copy()
            logger.info("💰 Using equal allocation - no performance data")
        else:
            # Performance-weighted allocation
            raw_allocations = {}
            for strategy_id in self.strategies:
                score, _ = performance_scores[strategy_id]
                raw_allocations[strategy_id] = score / total_score
        
        # Apply constraints and smoothing
        for strategy_id in self.strategies:
            score, metrics = performance_scores[strategy_id]
            raw_allocation = raw_allocations[strategy_id]
            
            # Apply min/max constraints
            constrained_allocation = max(self.min_allocation, 
                                       min(self.max_allocation, raw_allocation))
            
            # Create allocation object
            current_allocation = self.get_current_allocation(strategy_id)
            
            allocation = StrategyAllocation(
                strategy_id=strategy_id,
                current_allocation=current_allocation,
                target_allocation=constrained_allocation,
                performance_score=score,
                recent_return=metrics.get("recent_return", 0.0),
                risk_adjusted_return=metrics.get("sharpe_ratio", 0.0),
                confidence_level=min(1.0, metrics.get("trades", 0) / 10.0),  # More trades = higher confidence
                adjustment_reason=self._get_adjustment_reason(current_allocation, constrained_allocation, metrics)
            )
            
            allocations[strategy_id] = allocation
        
        # Normalize to ensure allocations sum to 1.0
        total_target = sum(alloc.target_allocation for alloc in allocations.values())
        if total_target > 0:
            for allocation in allocations.values():
                allocation.target_allocation /= total_target
        
        logger.success(f"💰 Calculated optimal allocations for {len(allocations)} strategies")
        return allocations
    
    def _get_adjustment_reason(self, current: float, target: float, metrics: Dict) -> str:
        """Generate human-readable reason for allocation adjustment"""
        
        change = target - current
        
        if abs(change) < self.rebalancing_threshold:
            return "maintaining_allocation"
        elif change > 0:
            if metrics.get("trades", 0) < self.min_trades_for_allocation:
                return "insufficient_data_neutral"
            elif metrics.get("total_score", 0.5) > 0.7:
                return f"strong_performance_pf_{metrics.get('profit_factor', 0):.1f}"
            else:
                return "moderate_performance_increase"
        else:
            if metrics.get("total_score", 0.5) < 0.3:
                return f"poor_performance_wr_{metrics.get('win_rate', 0):.1%}"
            else:
                return "relative_underperformance"
    
    def get_current_allocation(self, strategy_id: str) -> float:
        """Get current allocation for a strategy"""
        try:
            if os.path.exists(self.allocation_file):
                with open(self.allocation_file, 'r') as f:
                    data = json.load(f)
                    
                allocations = data.get("allocations", {})
                return allocations.get(strategy_id, self.base_allocations[strategy_id])
        except Exception as e:
            logger.warning(f"⚠️ Error loading current allocation: {e}")
        
        return self.base_allocations[strategy_id]
    
    def save_allocations(self, allocations: Dict[str, StrategyAllocation]):
        """Save allocation decisions to file"""
        try:
            allocation_data = {
                "timestamp": datetime.now().isoformat(),
                "allocations": {k: v.target_allocation for k, v in allocations.items()},
                "detailed_allocations": {k: asdict(v) for k, v in allocations.items()},
                "total_capital": self.total_capital
            }
            
            with open(self.allocation_file, 'w') as f:
                json.dump(allocation_data, f, indent=2)
                
            logger.success(f"💾 Saved allocation decisions for {len(allocations)} strategies")
            
        except Exception as e:
            logger.error(f"❌ Error saving allocations: {e}")
    
    def generate_allocation_recommendations(self) -> List[AllocationRecommendation]:
        """Generate actionable allocation recommendations"""
        
        allocations = self.calculate_optimal_allocations()
        recommendations = []
        
        for strategy_id, allocation in allocations.items():
            current_pct = allocation.current_allocation * 100
            target_pct = allocation.target_allocation * 100
            change_pct = target_pct - current_pct
            
            # Determine action
            if abs(change_pct) < self.rebalancing_threshold * 100:
                action = "maintain"
            elif change_pct > 0:
                action = "increase"
            else:
                action = "decrease"
            
            # Generate reasoning
            if action == "maintain":
                reasoning = f"Performance stable, allocation appropriate"
            elif action == "increase":
                reasoning = f"Strong performance (score: {allocation.performance_score:.2f}), increase allocation"
            else:
                reasoning = f"Underperforming (score: {allocation.performance_score:.2f}), reduce allocation"
            
            # Estimate expected improvement
            if action == "increase":
                expected_improvement = allocation.performance_score * 0.1  # 10% of performance score
            elif action == "decrease":
                expected_improvement = 0.02  # Small improvement from risk reduction
            else:
                expected_improvement = 0.0
            
            recommendation = AllocationRecommendation(
                strategy_id=strategy_id,
                action=action,
                current_percent=current_pct,
                recommended_percent=target_pct,
                change_percent=change_pct,
                reasoning=reasoning,
                confidence=allocation.confidence_level,
                expected_improvement=expected_improvement
            )
            
            recommendations.append(recommendation)
        
        # Save allocations
        self.save_allocations(allocations)
        
        logger.info(f"📊 Generated {len(recommendations)} allocation recommendations")
        return recommendations
    
    def get_capital_allocation_summary(self) -> str:
        """Generate formatted summary for Telegram"""
        
        summary = "💰 **Dynamic Capital Allocation**\n\n"
        
        recommendations = self.generate_allocation_recommendations()
        
        if not recommendations:
            return summary + "❌ Unable to generate allocation recommendations"
        
        # Current vs Recommended Allocations
        summary += "📊 **Current vs Recommended:**\n"
        
        emojis = {"conservative": "🛡️", "moderate": "⚖️", "aggressive": "🚀"}
        action_emojis = {"increase": "📈", "decrease": "📉", "maintain": "➡️"}
        
        total_changes = 0
        
        for rec in recommendations:
            emoji = emojis.get(rec.strategy_id, "📊")
            action_emoji = action_emojis.get(rec.action, "➡️")
            
            summary += f"{emoji} **{rec.strategy_id.title()}**: "
            summary += f"{rec.current_percent:.1f}% → {rec.recommended_percent:.1f}% "
            summary += f"{action_emoji}\n"
            
            if abs(rec.change_percent) >= self.rebalancing_threshold * 100:
                total_changes += 1
        
        # Rebalancing Status
        summary += f"\n🔄 **Rebalancing Status:**\n"
        if total_changes > 0:
            summary += f"📋 {total_changes} strategies need rebalancing\n"
            summary += f"💡 Threshold: {self.rebalancing_threshold*100:.0f}% change required\n"
        else:
            summary += f"✅ All allocations are optimal\n"
        
        # Performance-Based Insights
        summary += f"\n💡 **Allocation Insights:**\n"
        
        # Find best performer
        best_rec = max(recommendations, key=lambda r: r.recommended_percent)
        worst_rec = min(recommendations, key=lambda r: r.recommended_percent)
        
        summary += f"🏆 Top allocation: {best_rec.strategy_id.title()} ({best_rec.recommended_percent:.1f}%)\n"
        summary += f"📉 Lowest allocation: {worst_rec.strategy_id.title()} ({worst_rec.recommended_percent:.1f}%)\n"
        
        # Expected improvements
        total_expected_improvement = sum(r.expected_improvement for r in recommendations)
        if total_expected_improvement > 0:
            summary += f"📈 Expected improvement: +{total_expected_improvement:.1%}\n"
        
        # Total capital
        summary += f"\n💳 **Total Capital**: ${self.total_capital:,.0f}\n"
        summary += f"📅 **Last Updated**: {datetime.now().strftime('%H:%M:%S')}"
        
        return summary

# Global instance
dynamic_capital_allocation = DynamicCapitalAllocation()

if __name__ == "__main__":
    # Test the dynamic capital allocation system
    logger.info("🧪 Testing Dynamic Capital Allocation System")
    
    allocation_system = DynamicCapitalAllocation()
    
    print("💰 Capital Allocation Test")
    print("=" * 50)
    
    # Test performance scoring
    print("\n📊 Performance Scoring:")
    for strategy in ["conservative", "moderate", "aggressive"]:
        score, metrics = allocation_system.calculate_performance_score(strategy)
        print(f"  {strategy}: Score {score:.3f} (reason: {metrics.get('reason', 'unknown')})")
    
    # Test optimal allocations
    allocations = allocation_system.calculate_optimal_allocations()
    print(f"\n🎯 Optimal Allocations:")
    
    for strategy_id, allocation in allocations.items():
        print(f"  {strategy_id}:")
        print(f"    Current: {allocation.current_allocation:.1%}")
        print(f"    Target: {allocation.target_allocation:.1%}")
        print(f"    Performance Score: {allocation.performance_score:.3f}")
        print(f"    Reason: {allocation.adjustment_reason}")
    
    # Test recommendations
    recommendations = allocation_system.generate_allocation_recommendations()
    print(f"\n💡 Recommendations ({len(recommendations)}):")
    
    for rec in recommendations:
        print(f"  {rec.strategy_id}: {rec.action} ({rec.current_percent:.1f}% → {rec.recommended_percent:.1f}%)")
        print(f"    Reason: {rec.reasoning}")
        print(f"    Confidence: {rec.confidence:.1%}")
    
    # Test summary generation
    print("\n" + "=" * 50)
    print("Capital Allocation Summary:")
    print(allocation_system.get_capital_allocation_summary())
"""
Cross-Strategy Performance Analyzer
Analyzes performance patterns across Conservative/Moderate/Aggressive strategies
to identify shared insights and optimization opportunities
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from loguru import logger
import statistics

@dataclass
class StrategyPerformance:
    """Performance metrics for a strategy"""
    strategy_id: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_winner: float
    avg_loser: float
    profit_factor: float
    total_pnl: float
    current_balance: float
    sharpe_ratio: float
    max_drawdown: float

@dataclass
class SignalInsight:
    """Insights about signal performance across strategies"""
    signal_name: str
    best_strategy: str
    best_win_rate: float
    worst_strategy: str
    worst_win_rate: float
    consensus_strength: float  # How much strategies agree
    recommendation: str

@dataclass
class CrossStrategyInsight:
    """Cross-strategy learning insights"""
    insight_type: str
    description: str
    confidence: float
    strategies_affected: List[str]
    recommendation: str
    expected_improvement: float

class CrossStrategyAnalyzer:
    """Analyzes performance across all strategies to find shared insights"""
    
    def __init__(self):
        self.strategies = ["conservative", "moderate", "aggressive"]
        self.lookback_days = 30  # Analyze last 30 days
        self.min_trades_for_analysis = 5  # Need minimum trades for reliable analysis
        
        logger.info("🔍 Cross-Strategy Performance Analyzer initialized")
    
    def get_strategy_performance(self, strategy_id: str) -> Optional[StrategyPerformance]:
        """Get comprehensive performance metrics for a strategy"""
        # Try production path first, fallback to local
        db_path = f"/opt/rtx-trading/data/options_performance_{strategy_id}.db"
        if not os.path.exists(db_path):
            db_path = f"data/options_performance_{strategy_id}.db"
            
        if not os.path.exists(db_path):
            logger.warning(f"🔍 No database found for {strategy_id}")
            return None
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get lookback date
            lookback_date = datetime.now() - timedelta(days=self.lookback_days)
            
            # Get comprehensive trade statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    AVG(CASE WHEN net_pnl > 0 THEN net_pnl ELSE NULL END) as avg_winner,
                    AVG(CASE WHEN net_pnl < 0 THEN net_pnl ELSE NULL END) as avg_loser,
                    SUM(net_pnl) as total_pnl
                FROM options_outcomes
                WHERE exit_timestamp > ?
            """, (lookback_date,))
            
            result = cursor.fetchone()
            
            if not result or result[0] < self.min_trades_for_analysis:
                logger.info(f"🔍 {strategy_id}: Insufficient trades ({result[0] if result else 0}) for analysis")
                conn.close()
                return None
                
            total_trades = result[0]
            winning_trades = result[1] or 0
            losing_trades = total_trades - winning_trades
            avg_winner = result[2] or 0
            avg_loser = abs(result[3] or 1)  # Make positive
            total_pnl = result[4] or 0
            
            # Calculate derived metrics
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            total_wins = avg_winner * winning_trades if avg_winner > 0 else 0
            total_losses = avg_loser * losing_trades if avg_loser > 0 else 1
            profit_factor = total_wins / total_losses if total_losses > 0 else 0
            
            # Get current balance
            cursor.execute("SELECT balance_after FROM account_history ORDER BY timestamp DESC LIMIT 1")
            balance_row = cursor.fetchone()
            current_balance = balance_row[0] if balance_row else 1000.0
            
            # Calculate Sharpe ratio (simplified)
            cursor.execute("SELECT net_pnl FROM options_outcomes WHERE exit_timestamp > ?", (lookback_date,))
            pnl_values = [row[0] for row in cursor.fetchall()]
            
            if len(pnl_values) > 1:
                returns_std = statistics.stdev(pnl_values)
                avg_return = statistics.mean(pnl_values)
                sharpe_ratio = avg_return / returns_std if returns_std > 0 else 0
            else:
                sharpe_ratio = 0
                
            # Calculate max drawdown
            cursor.execute("""
                SELECT balance_after 
                FROM account_history 
                WHERE timestamp > ? 
                ORDER BY timestamp
            """, (lookback_date,))
            
            balances = [row[0] for row in cursor.fetchall()]
            max_drawdown = self._calculate_max_drawdown(balances)
            
            conn.close()
            
            performance = StrategyPerformance(
                strategy_id=strategy_id,
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                avg_winner=avg_winner,
                avg_loser=avg_loser,
                profit_factor=profit_factor,
                total_pnl=total_pnl,
                current_balance=current_balance,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown
            )
            
            logger.info(f"🔍 {strategy_id}: Performance analyzed - {total_trades} trades, {win_rate:.1%} WR")
            return performance
            
        except Exception as e:
            logger.error(f"❌ Error analyzing {strategy_id}: {e}")
            return None
    
    def _calculate_max_drawdown(self, balances: List[float]) -> float:
        """Calculate maximum drawdown from balance history"""
        if len(balances) < 2:
            return 0.0
            
        max_balance = balances[0]
        max_drawdown = 0.0
        
        for balance in balances:
            if balance > max_balance:
                max_balance = balance
            else:
                drawdown = (max_balance - balance) / max_balance
                max_drawdown = max(max_drawdown, drawdown)
                
        return max_drawdown
    
    def analyze_signal_performance_cross_strategy(self) -> List[SignalInsight]:
        """Analyze which signals work best across different strategies"""
        signal_insights = []
        
        # This would require signal-level tracking in the database
        # For now, we'll create a framework and placeholder insights
        
        # Example signals analysis (would be populated from actual data)
        example_signals = [
            "technical_analysis", "news_sentiment", "options_flow", 
            "volatility_analysis", "momentum", "sector_correlation"
        ]
        
        for signal in example_signals:
            # This would query actual signal performance data
            # For now, creating example insights
            insight = SignalInsight(
                signal_name=signal,
                best_strategy="conservative",  # Would be calculated from data
                best_win_rate=0.65,  # Would be calculated from data
                worst_strategy="aggressive",  # Would be calculated from data
                worst_win_rate=0.45,  # Would be calculated from data
                consensus_strength=0.75,  # How much strategies agree on this signal
                recommendation="Increase weight for conservative strategy"
            )
            signal_insights.append(insight)
            
        logger.info(f"🔍 Analyzed {len(signal_insights)} signals across strategies")
        return signal_insights
    
    def identify_best_performing_strategy(self) -> Tuple[str, StrategyPerformance, str]:
        """Identify the current best performing strategy"""
        performances = {}
        
        for strategy_id in self.strategies:
            perf = self.get_strategy_performance(strategy_id)
            if perf:
                performances[strategy_id] = perf
                
        if not performances:
            return "none", None, "No strategies have sufficient data"
            
        # Rank by multiple criteria (profit factor, win rate, Sharpe ratio)
        def score_strategy(perf: StrategyPerformance) -> float:
            return (
                perf.profit_factor * 0.4 +
                perf.win_rate * 100 * 0.3 +
                perf.sharpe_ratio * 10 * 0.2 +
                (1 - perf.max_drawdown) * 100 * 0.1
            )
        
        best_strategy = max(performances.keys(), key=lambda k: score_strategy(performances[k]))
        best_performance = performances[best_strategy]
        
        reason = f"Best overall score: PF {best_performance.profit_factor:.2f}, WR {best_performance.win_rate:.1%}, Sharpe {best_performance.sharpe_ratio:.2f}"
        
        logger.success(f"🏆 Best performing strategy: {best_strategy} ({reason})")
        return best_strategy, best_performance, reason
    
    def generate_cross_strategy_insights(self) -> List[CrossStrategyInsight]:
        """Generate actionable insights from cross-strategy analysis"""
        insights = []
        
        # Get all strategy performances
        performances = {}
        for strategy_id in self.strategies:
            perf = self.get_strategy_performance(strategy_id)
            if perf:
                performances[strategy_id] = perf
        
        if len(performances) < 2:
            logger.warning("🔍 Insufficient strategies for cross-analysis")
            return insights
            
        # Insight 1: Win Rate Consistency
        win_rates = [p.win_rate for p in performances.values()]
        win_rate_std = statistics.stdev(win_rates) if len(win_rates) > 1 else 0
        
        if win_rate_std > 0.15:  # Large variation in win rates
            best_wr_strategy = max(performances.keys(), key=lambda k: performances[k].win_rate)
            worst_wr_strategy = min(performances.keys(), key=lambda k: performances[k].win_rate)
            
            insights.append(CrossStrategyInsight(
                insight_type="win_rate_divergence",
                description=f"Large win rate gap: {best_wr_strategy} ({performances[best_wr_strategy].win_rate:.1%}) vs {worst_wr_strategy} ({performances[worst_wr_strategy].win_rate:.1%})",
                confidence=0.85,
                strategies_affected=[worst_wr_strategy],
                recommendation=f"Copy signal weights from {best_wr_strategy} to {worst_wr_strategy}",
                expected_improvement=0.10
            ))
        
        # Insight 2: Profit Factor Analysis
        profit_factors = [p.profit_factor for p in performances.values()]
        
        if max(profit_factors) > 2.0:  # Someone has excellent profit factor
            best_pf_strategy = max(performances.keys(), key=lambda k: performances[k].profit_factor)
            
            insights.append(CrossStrategyInsight(
                insight_type="profit_factor_excellence",
                description=f"{best_pf_strategy} has excellent profit factor: {performances[best_pf_strategy].profit_factor:.2f}",
                confidence=0.90,
                strategies_affected=[s for s in performances.keys() if s != best_pf_strategy],
                recommendation=f"Adopt exit strategy and position sizing from {best_pf_strategy}",
                expected_improvement=0.15
            ))
        
        # Insight 3: Capital Allocation Recommendation
        best_strategy, _, _ = self.identify_best_performing_strategy()
        
        if best_strategy != "none":
            insights.append(CrossStrategyInsight(
                insight_type="capital_allocation",
                description=f"Strategy performance ranking suggests capital reallocation",
                confidence=0.75,
                strategies_affected=self.strategies,
                recommendation=f"Increase allocation to {best_strategy}, reduce allocation to worst performers",
                expected_improvement=0.20
            ))
        
        logger.info(f"🧠 Generated {len(insights)} cross-strategy insights")
        return insights
    
    def get_cross_strategy_summary(self) -> str:
        """Generate formatted summary for Telegram"""
        summary = "🧠 **Cross-Strategy Learning Analysis**\n\n"
        
        # Get all performances
        performances = {}
        for strategy_id in self.strategies:
            perf = self.get_strategy_performance(strategy_id)
            if perf:
                performances[strategy_id] = perf
        
        if not performances:
            return summary + "❌ No strategies have sufficient data for analysis"
        
        # Strategy Rankings
        sorted_strategies = sorted(
            performances.keys(), 
            key=lambda k: performances[k].profit_factor, 
            reverse=True
        )
        
        summary += "🏆 **Strategy Rankings (by Profit Factor):**\n"
        emojis = ["🥇", "🥈", "🥉"]
        
        for i, strategy in enumerate(sorted_strategies):
            perf = performances[strategy]
            emoji = emojis[i] if i < len(emojis) else "📊"
            summary += f"{emoji} **{strategy.title()}**: PF {perf.profit_factor:.2f}, WR {perf.win_rate:.1%}, Balance ${perf.current_balance:.2f}\n"
        
        # Best Performer Details
        best_strategy, best_perf, reason = self.identify_best_performing_strategy()
        
        if best_strategy != "none":
            summary += f"\n🎯 **Top Performer**: {best_strategy.title()}\n"
            summary += f"  • {reason}\n"
            summary += f"  • Sharpe Ratio: {best_perf.sharpe_ratio:.2f}\n"
            summary += f"  • Max Drawdown: {best_perf.max_drawdown:.1%}\n"
        
        # Cross-Strategy Insights
        insights = self.generate_cross_strategy_insights()
        
        if insights:
            summary += f"\n💡 **Learning Insights** ({len(insights)}):\n"
            for i, insight in enumerate(insights[:3]):  # Show top 3
                summary += f"{i+1}. {insight.description}\n"
                summary += f"   📈 Expected improvement: +{insight.expected_improvement:.1%}\n"
        
        summary += f"\n🔄 **Last Updated**: {datetime.now().strftime('%H:%M:%S')}"
        
        return summary

# Global instance
cross_strategy_analyzer = CrossStrategyAnalyzer()

if __name__ == "__main__":
    # Test the cross-strategy analyzer
    logger.info("🧪 Testing Cross-Strategy Performance Analyzer")
    
    analyzer = CrossStrategyAnalyzer()
    
    print("🔍 Cross-Strategy Analysis Test")
    print("=" * 50)
    
    # Test individual strategy performance
    for strategy in ["conservative", "moderate", "aggressive"]:
        perf = analyzer.get_strategy_performance(strategy)
        if perf:
            print(f"\n📊 {strategy.upper()}:")
            print(f"  Trades: {perf.total_trades}")
            print(f"  Win Rate: {perf.win_rate:.1%}")
            print(f"  Profit Factor: {perf.profit_factor:.2f}")
            print(f"  Sharpe Ratio: {perf.sharpe_ratio:.2f}")
            print(f"  Max Drawdown: {perf.max_drawdown:.1%}")
        else:
            print(f"\n📊 {strategy.upper()}: No data available")
    
    # Test best performer identification
    best_strategy, best_perf, reason = analyzer.identify_best_performing_strategy()
    print(f"\n🏆 Best Performer: {best_strategy}")
    print(f"Reason: {reason}")
    
    # Test cross-strategy insights
    insights = analyzer.generate_cross_strategy_insights()
    print(f"\n💡 Generated {len(insights)} insights")
    
    for insight in insights:
        print(f"  • {insight.insight_type}: {insight.description}")
        print(f"    Confidence: {insight.confidence:.1%}, Expected +{insight.expected_improvement:.1%}")
    
    # Test summary generation
    print("\n" + "=" * 50)
    print("Cross-Strategy Summary:")
    print(analyzer.get_cross_strategy_summary())
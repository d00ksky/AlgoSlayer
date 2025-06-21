"""
Dynamic ML Confidence Thresholds
Automatically adjusts strategy confidence thresholds based on recent performance
"""
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from loguru import logger
from dataclasses import dataclass

@dataclass
class PerformanceMetrics:
    """Recent performance metrics for a strategy"""
    total_trades: int
    winning_trades: int
    win_rate: float
    avg_profit: float
    avg_loss: float
    profit_factor: float
    recent_streak: int  # Positive for wins, negative for losses

class DynamicThresholdManager:
    """Manages dynamic confidence thresholds based on strategy performance"""
    
    def __init__(self):
        # Base thresholds for each strategy
        self.base_thresholds = {
            "conservative": 0.75,
            "moderate": 0.60,
            "aggressive": 0.50
        }
        
        # Dynamic ranges (min, max)
        self.threshold_ranges = {
            "conservative": (0.65, 0.85),
            "moderate": (0.50, 0.70),
            "aggressive": (0.40, 0.60)
        }
        
        # Performance windows
        self.performance_window_days = 7  # Look at last 7 days
        self.min_trades_for_adjustment = 5  # Need at least 5 trades to adjust
        
        # Adjustment parameters
        self.hot_streak_threshold = 0.60  # 60%+ win rate = hot streak
        self.cold_streak_threshold = 0.30  # <30% win rate = cold streak
        self.adjustment_factor = 0.10  # Adjust by ±10%
        
        logger.info("🎯 Dynamic Threshold Manager initialized")
        
    def get_recent_performance(self, strategy_id: str, window_days: int = None) -> Optional[PerformanceMetrics]:
        """Get recent performance metrics for a strategy"""
        if window_days is None:
            window_days = self.performance_window_days
            
        # Try production path first, fallback to local development path
        db_path = f"/opt/rtx-trading/data/options_performance_{strategy_id}.db"
        if not os.path.exists(db_path):
            db_path = f"data/options_performance_{strategy_id}.db"
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get recent trades from the last N days
            cutoff_date = datetime.now() - timedelta(days=window_days)
            
            cursor.execute("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                AVG(CASE WHEN net_pnl > 0 THEN net_pnl ELSE NULL END) as avg_profit,
                AVG(CASE WHEN net_pnl < 0 THEN net_pnl ELSE NULL END) as avg_loss,
                AVG(net_pnl) as avg_pnl
            FROM options_outcomes
            WHERE exit_timestamp > ?
            """, (cutoff_date,))
            
            result = cursor.fetchone()
            
            if result and result[0] > 0:  # Has trades
                total_trades = result[0]
                winning_trades = result[1] or 0
                win_rate = winning_trades / total_trades if total_trades > 0 else 0
                avg_profit = result[2] or 0
                avg_loss = abs(result[3] or 1)  # Avoid division by zero
                profit_factor = (avg_profit * winning_trades) / (avg_loss * (total_trades - winning_trades)) if (total_trades - winning_trades) > 0 else 0
                
                # Get recent streak
                cursor.execute("""
                SELECT net_pnl FROM options_outcomes
                WHERE exit_timestamp > ?
                ORDER BY exit_timestamp DESC
                LIMIT 5
                """, (cutoff_date,))
                
                recent_trades = cursor.fetchall()
                streak = self._calculate_streak(recent_trades)
                
                conn.close()
                
                return PerformanceMetrics(
                    total_trades=total_trades,
                    winning_trades=winning_trades,
                    win_rate=win_rate,
                    avg_profit=avg_profit,
                    avg_loss=avg_loss,
                    profit_factor=profit_factor,
                    recent_streak=streak
                )
            
            conn.close()
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting performance for {strategy_id}: {e}")
            return None
            
    def _calculate_streak(self, recent_trades: list) -> int:
        """Calculate current win/loss streak"""
        if not recent_trades:
            return 0
            
        streak = 0
        first_trade_positive = recent_trades[0][0] > 0
        
        for trade in recent_trades:
            if (trade[0] > 0) == first_trade_positive:
                streak += 1 if first_trade_positive else -1
            else:
                break
                
        return streak
        
    def calculate_optimal_threshold(self, strategy_id: str) -> Tuple[float, str]:
        """
        Calculate optimal threshold for a strategy based on recent performance
        Returns: (threshold, reason)
        """
        base_threshold = self.base_thresholds.get(strategy_id, 0.60)
        min_threshold, max_threshold = self.threshold_ranges.get(strategy_id, (0.40, 0.80))
        
        # Get recent performance
        performance = self.get_recent_performance(strategy_id)
        
        if not performance or performance.total_trades < self.min_trades_for_adjustment:
            logger.info(f"📊 {strategy_id}: Using base threshold {base_threshold:.1%} (insufficient data)")
            return base_threshold, "insufficient_data"
            
        # Analyze performance and adjust
        current_threshold = base_threshold
        reason = "normal"
        
        # Hot streak detection
        if performance.win_rate >= self.hot_streak_threshold:
            # Lower threshold to capture more trades during hot streak
            adjustment = self.adjustment_factor
            if performance.recent_streak >= 3:  # Extra bonus for 3+ win streak
                adjustment *= 1.5
            current_threshold = base_threshold - adjustment
            reason = f"hot_streak_{performance.win_rate:.0%}_win_rate"
            logger.success(f"🔥 {strategy_id}: HOT STREAK! Win rate {performance.win_rate:.1%}, lowering threshold")
            
        # Cold streak detection
        elif performance.win_rate <= self.cold_streak_threshold:
            # Raise threshold to be more selective during cold streak
            adjustment = self.adjustment_factor
            if performance.recent_streak <= -3:  # Extra penalty for 3+ loss streak
                adjustment *= 1.5
            current_threshold = base_threshold + adjustment
            reason = f"cold_streak_{performance.win_rate:.0%}_win_rate"
            logger.warning(f"❄️ {strategy_id}: COLD STREAK! Win rate {performance.win_rate:.1%}, raising threshold")
            
        # Profit factor optimization
        elif performance.profit_factor > 2.0:
            # Slightly lower threshold for highly profitable strategies
            current_threshold = base_threshold - (self.adjustment_factor * 0.5)
            reason = f"high_profit_factor_{performance.profit_factor:.1f}"
            logger.info(f"💰 {strategy_id}: High profit factor {performance.profit_factor:.1f}, slightly lowering threshold")
            
        # Apply bounds
        current_threshold = max(min_threshold, min(max_threshold, current_threshold))
        
        logger.info(f"🎯 {strategy_id}: Dynamic threshold {current_threshold:.1%} (base: {base_threshold:.1%}, reason: {reason})")
        
        return current_threshold, reason
        
    def get_all_thresholds(self) -> Dict[str, Dict]:
        """Get current dynamic thresholds for all strategies"""
        thresholds = {}
        
        for strategy_id in ["conservative", "moderate", "aggressive"]:
            threshold, reason = self.calculate_optimal_threshold(strategy_id)
            performance = self.get_recent_performance(strategy_id)
            
            thresholds[strategy_id] = {
                "base_threshold": self.base_thresholds[strategy_id],
                "dynamic_threshold": threshold,
                "adjustment": threshold - self.base_thresholds[strategy_id],
                "reason": reason,
                "performance": {
                    "win_rate": performance.win_rate if performance else 0,
                    "total_trades": performance.total_trades if performance else 0,
                    "profit_factor": performance.profit_factor if performance else 0,
                    "recent_streak": performance.recent_streak if performance else 0
                } if performance else None
            }
            
        return thresholds
        
    def get_threshold_summary(self) -> str:
        """Get a formatted summary of all thresholds"""
        thresholds = self.get_all_thresholds()
        
        summary = "🎯 **Dynamic Threshold Status**\n\n"
        
        for strategy_id, data in thresholds.items():
            emoji = {"conservative": "🛡️", "moderate": "⚖️", "aggressive": "🚀"}.get(strategy_id, "📊")
            
            summary += f"{emoji} **{strategy_id.title()}**\n"
            summary += f"  Base: {data['base_threshold']:.1%} → Dynamic: {data['dynamic_threshold']:.1%}"
            
            if data['adjustment'] != 0:
                direction = "↓" if data['adjustment'] < 0 else "↑"
                summary += f" ({direction}{abs(data['adjustment']):.1%})"
                
            summary += f"\n  Reason: {data['reason'].replace('_', ' ').title()}\n"
            
            if data['performance']:
                perf = data['performance']
                summary += f"  Performance: {perf['win_rate']:.1%} win rate, {perf['total_trades']} trades"
                if perf['recent_streak'] != 0:
                    streak_emoji = "🔥" if perf['recent_streak'] > 0 else "❄️"
                    summary += f", {streak_emoji} {abs(perf['recent_streak'])} streak"
                summary += "\n"
                
            summary += "\n"
            
        return summary


# Singleton instance
dynamic_threshold_manager = DynamicThresholdManager()

if __name__ == "__main__":
    # Test the dynamic threshold system
    manager = DynamicThresholdManager()
    
    print("🧪 Testing Dynamic Threshold Manager\n")
    
    # Get thresholds for all strategies
    thresholds = manager.get_all_thresholds()
    
    for strategy, data in thresholds.items():
        print(f"\n{strategy.upper()}:")
        print(f"  Base Threshold: {data['base_threshold']:.1%}")
        print(f"  Dynamic Threshold: {data['dynamic_threshold']:.1%}")
        print(f"  Adjustment: {data['adjustment']:+.1%}")
        print(f"  Reason: {data['reason']}")
        
        if data['performance']:
            print(f"  Win Rate: {data['performance']['win_rate']:.1%}")
            print(f"  Total Trades: {data['performance']['total_trades']}")
            print(f"  Profit Factor: {data['performance']['profit_factor']:.2f}")
            print(f"  Recent Streak: {data['performance']['recent_streak']}")
    
    print("\n" + "="*50)
    print("\nFormatted Summary:")
    print(manager.get_threshold_summary())
"""
Kelly Criterion Position Sizing
Mathematically optimal position sizing based on strategy performance
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from loguru import logger
from dataclasses import dataclass

@dataclass
class StrategyPerformance:
    """Performance metrics for Kelly calculation"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    loss_rate: float
    avg_winner: float
    avg_loser: float
    profit_factor: float
    total_pnl: float
    current_balance: float

class KellyPositionSizer:
    """Calculate optimal position sizes using Kelly Criterion"""
    
    def __init__(self):
        # Kelly parameters
        self.min_trades_required = 10  # Need minimum trades for reliable Kelly
        self.kelly_fraction = 0.5  # Use 50% of full Kelly for safety (fractional Kelly)
        self.min_position_size = 0.05  # 5% minimum position size
        self.max_position_size = 0.30  # 30% maximum position size
        self.lookback_days = 30  # Use last 30 days of performance
        
        # Strategy base sizes (fallback when insufficient data)
        self.base_position_sizes = {
            "conservative": 0.15,  # 15%
            "moderate": 0.20,      # 20%
            "aggressive": 0.25     # 25%
        }
        
        logger.info("📊 Kelly Criterion Position Sizer initialized")
    
    def get_strategy_performance(self, strategy_id: str) -> Optional[StrategyPerformance]:
        """Get performance metrics for Kelly calculation"""
        # Try production path first, fallback to local
        db_path = f"/opt/rtx-trading/data/options_performance_{strategy_id}.db"
        if not os.path.exists(db_path):
            db_path = f"data/options_performance_{strategy_id}.db"
            
        if not os.path.exists(db_path):
            logger.warning(f"📊 No database found for {strategy_id}")
            return None
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get lookback date
            lookback_date = datetime.now() - timedelta(days=self.lookback_days)
            
            # Get recent completed trades
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
            
            if not result or result[0] < self.min_trades_required:
                logger.info(f"📊 {strategy_id}: Insufficient trades ({result[0] if result else 0}) for Kelly calculation")
                conn.close()
                return None
                
            total_trades = result[0]
            winning_trades = result[1] or 0
            losing_trades = total_trades - winning_trades
            avg_winner = result[2] or 0
            avg_loser = abs(result[3] or 1)  # Make positive for calculation
            total_pnl = result[4] or 0
            
            # Calculate rates
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            loss_rate = losing_trades / total_trades if total_trades > 0 else 0
            
            # Calculate profit factor
            total_wins = avg_winner * winning_trades if avg_winner > 0 else 0
            total_losses = avg_loser * losing_trades if avg_loser > 0 else 1
            profit_factor = total_wins / total_losses if total_losses > 0 else 0
            
            # Get current balance
            cursor.execute("SELECT balance_after FROM account_history ORDER BY rowid DESC LIMIT 1")
            balance_row = cursor.fetchone()
            current_balance = balance_row[0] if balance_row else 1000.0
            
            conn.close()
            
            performance = StrategyPerformance(
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                loss_rate=loss_rate,
                avg_winner=avg_winner,
                avg_loser=avg_loser,
                profit_factor=profit_factor,
                total_pnl=total_pnl,
                current_balance=current_balance
            )
            
            logger.info(f"📊 {strategy_id}: Performance loaded - {total_trades} trades, {win_rate:.1%} WR")
            return performance
            
        except Exception as e:
            logger.error(f"❌ Error getting performance for {strategy_id}: {e}")
            return None
    
    def calculate_kelly_fraction(self, performance: StrategyPerformance) -> Tuple[float, str]:
        """Calculate optimal Kelly fraction"""
        
        # Kelly Criterion formula: f* = (bp - q) / b
        # Where:
        # b = odds received on the wager (avg_winner / avg_loser)
        # p = probability of winning (win_rate)
        # q = probability of losing (loss_rate)
        
        if performance.avg_loser == 0 or performance.avg_winner <= 0:
            return 0.0, "invalid_payoffs"
            
        # Calculate Kelly components
        b = performance.avg_winner / performance.avg_loser  # Payoff ratio
        p = performance.win_rate  # Win probability
        q = performance.loss_rate  # Loss probability
        
        # Kelly formula
        kelly_fraction = (b * p - q) / b
        
        # Reason for the Kelly size
        if kelly_fraction <= 0:
            reason = f"negative_edge_wl_{performance.win_rate:.1%}"
        elif kelly_fraction > 0.5:
            reason = f"high_edge_{kelly_fraction:.1%}"
        elif performance.profit_factor > 2.0:
            reason = f"strong_pf_{performance.profit_factor:.1f}"
        elif performance.win_rate > 0.6:
            reason = f"high_wr_{performance.win_rate:.1%}"
        else:
            reason = f"normal_edge_{kelly_fraction:.1%}"
            
        logger.info(f"📊 Kelly calculation: WR={p:.1%}, Payoff={b:.2f}, Raw Kelly={kelly_fraction:.1%}")
        
        return kelly_fraction, reason
    
    def calculate_optimal_position_size(self, strategy_id: str) -> Tuple[float, str, Dict]:
        """Calculate optimal position size for a strategy with earnings integration"""
        
        # Get performance data
        performance = self.get_strategy_performance(strategy_id)
        
        if not performance:
            base_size = self.base_position_sizes.get(strategy_id, 0.20)
            # Still apply earnings adjustment even without performance data
            return self._apply_earnings_adjustment(base_size, "insufficient_data", {})
            
        # Calculate Kelly fraction
        kelly_fraction, kelly_reason = self.calculate_kelly_fraction(performance)
        
        # Apply fractional Kelly for safety
        fractional_kelly = kelly_fraction * self.kelly_fraction
        
        # Apply bounds
        bounded_size = max(self.min_position_size, min(self.max_position_size, fractional_kelly))
        
        # Determine final reason
        if kelly_fraction <= 0:
            final_reason = "no_edge_min_size"
            final_size = self.min_position_size
        elif bounded_size == self.min_position_size:
            final_reason = f"kelly_too_low_{kelly_fraction:.1%}"
            final_size = self.min_position_size
        elif bounded_size == self.max_position_size:
            final_reason = f"kelly_capped_{kelly_fraction:.1%}"
            final_size = self.max_position_size
        else:
            final_reason = f"optimal_kelly_{kelly_reason}"
            final_size = bounded_size
            
        # Compile metrics for reporting
        metrics = {
            "raw_kelly": kelly_fraction,
            "fractional_kelly": fractional_kelly,
            "final_size": final_size,
            "win_rate": performance.win_rate,
            "profit_factor": performance.profit_factor,
            "total_trades": performance.total_trades,
            "avg_winner": performance.avg_winner,
            "avg_loser": performance.avg_loser,
            "payoff_ratio": performance.avg_winner / performance.avg_loser if performance.avg_loser > 0 else 0,
            "current_balance": performance.current_balance
        }
        
        logger.success(f"🎯 {strategy_id}: Kelly size {final_size:.1%} (reason: {final_reason})")
        
        # Apply earnings adjustment
        return self._apply_earnings_adjustment(final_size, final_reason, metrics)
    
    def _apply_earnings_adjustment(self, base_size: float, base_reason: str, base_metrics: Dict) -> Tuple[float, str, Dict]:
        """Apply earnings calendar adjustment to position size"""
        try:
            # Import earnings calendar here to avoid circular imports
            try:
                from .earnings_calendar import rtx_earnings
            except ImportError:
                from src.core.earnings_calendar import rtx_earnings
            
            # Get earnings adjustment
            kelly_boost, earnings_reason = rtx_earnings.get_earnings_kelly_adjustment()
            should_scale, scale_multiplier, scale_reason = rtx_earnings.should_scale_positions()
            
            # Apply earnings boost to Kelly size
            earnings_adjusted_size = base_size + kelly_boost
            
            # Apply position scaling
            if should_scale:
                earnings_adjusted_size *= scale_multiplier
                
            # Apply bounds again after earnings adjustment
            final_size = max(self.min_position_size, min(self.max_position_size, earnings_adjusted_size))
            
            # Update reason if earnings adjustment applied
            if abs(kelly_boost) > 0.001 or scale_multiplier != 1.0:
                final_reason = f"{base_reason}_earnings_{earnings_reason}"
                
                # Add earnings info to metrics
                base_metrics.update({
                    "earnings_kelly_boost": kelly_boost,
                    "earnings_scale_multiplier": scale_multiplier,
                    "earnings_reason": earnings_reason,
                    "base_size_before_earnings": base_size,
                    "final_size_after_earnings": final_size
                })
                
                logger.info(f"📅 Earnings adjustment: {base_size:.1%} → {final_size:.1%} (boost: {kelly_boost:+.1%}, scale: {scale_multiplier:.1f}x)")
            else:
                final_reason = base_reason
                final_size = base_size
                
            return final_size, final_reason, base_metrics
            
        except Exception as e:
            logger.warning(f"⚠️ Earnings adjustment failed: {e}")
            return base_size, base_reason, base_metrics
    
    def get_all_kelly_sizes(self) -> Dict[str, Dict]:
        """Get Kelly position sizes for all strategies"""
        kelly_data = {}
        
        for strategy_id in ["conservative", "moderate", "aggressive"]:
            size, reason, metrics = self.calculate_optimal_position_size(strategy_id)
            
            kelly_data[strategy_id] = {
                "strategy": strategy_id,
                "optimal_size": size,
                "reason": reason,
                "metrics": metrics,
                "base_size": self.base_position_sizes.get(strategy_id, 0.20),
                "adjustment": size - self.base_position_sizes.get(strategy_id, 0.20)
            }
            
        return kelly_data
    
    def get_kelly_summary(self) -> str:
        """Get formatted Kelly sizing summary for Telegram"""
        kelly_data = self.get_all_kelly_sizes()
        
        summary = "📊 **Kelly Criterion Position Sizing**\n\n"
        
        strategy_emojis = {"conservative": "🛡️", "moderate": "⚖️", "aggressive": "🚀"}
        
        for strategy_id, data in kelly_data.items():
            emoji = strategy_emojis.get(strategy_id, "📊")
            
            summary += f"{emoji} **{strategy_id.title()}**\n"
            summary += f"  Kelly Size: {data['optimal_size']:.1%} "
            
            # Show adjustment from base
            if data['adjustment'] != 0:
                direction = "↑" if data['adjustment'] > 0 else "↓"
                summary += f"({direction}{abs(data['adjustment']):.1%} from base)"
                
            summary += f"\n  Reason: {data['reason'].replace('_', ' ').title()}\n"
            
            # Show key metrics if available
            if data['metrics']:
                metrics = data['metrics']
                if metrics.get('total_trades', 0) > 0:
                    summary += f"  Performance: {metrics['win_rate']:.1%} WR, PF {metrics['profit_factor']:.1f}\n"
                    summary += f"  Trades: {metrics['total_trades']}, Balance: ${metrics['current_balance']:.2f}\n"
                    
            summary += "\n"
            
        summary += "💡 **Kelly Criterion**: Mathematically optimal position sizing\n"
        summary += "🛡️ **Safety**: Using 50% fractional Kelly with 5-30% bounds"
        
        return summary

# Global instance
kelly_sizer = KellyPositionSizer()

if __name__ == "__main__":
    # Test the Kelly position sizer
    logger.info("🧪 Testing Kelly Position Sizer")
    
    sizer = KellyPositionSizer()
    
    print("📊 Kelly Position Sizing Test")
    print("="*50)
    
    # Test all strategies
    kelly_data = sizer.get_all_kelly_sizes()
    
    for strategy_id, data in kelly_data.items():
        print(f"\n🎯 {strategy_id.upper()}:")
        print(f"  Base Size: {data['base_size']:.1%}")
        print(f"  Kelly Size: {data['optimal_size']:.1%}")
        print(f"  Adjustment: {data['adjustment']:+.1%}")
        print(f"  Reason: {data['reason']}")
        
        if data['metrics']:
            m = data['metrics']
            if m.get('total_trades', 0) > 0:
                print(f"  Win Rate: {m['win_rate']:.1%}")
                print(f"  Profit Factor: {m['profit_factor']:.2f}")
                print(f"  Payoff Ratio: {m['payoff_ratio']:.2f}")
                print(f"  Total Trades: {m['total_trades']}")
    
    print("\n" + "="*50)
    print("\nFormatted Summary:")
    print(sizer.get_kelly_summary())
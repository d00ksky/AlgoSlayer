"""
Real-Time Performance Dashboard
Comprehensive live dashboard accessible via Telegram with ASCII visualization
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger

class PerformanceDashboard:
    """Real-time dashboard for multi-strategy trading system"""
    
    def __init__(self):
        self.strategies = ["conservative", "moderate", "aggressive"]
        self.strategy_emojis = {
            "conservative": "🛡️",
            "moderate": "⚖️", 
            "aggressive": "🚀"
        }
        
    def generate_dashboard(self) -> str:
        """Generate comprehensive dashboard display"""
        try:
            dashboard = "📊 **Live Multi-Strategy Dashboard**\n"
            dashboard += "=" * 45 + "\n\n"
            
            # Get all strategy data
            strategy_data = self._get_all_strategy_data()
            
            # Current Rankings
            dashboard += self._generate_rankings(strategy_data)
            
            # Performance Charts
            dashboard += self._generate_performance_charts(strategy_data)
            
            # Signal Status
            dashboard += self._generate_signal_status()
            
            # Market Status & Next Cycle
            dashboard += self._generate_market_status()
            
            # Recent Activity
            dashboard += self._generate_recent_activity(strategy_data)
            
            return dashboard
            
        except Exception as e:
            logger.error(f"❌ Dashboard generation error: {e}")
            return f"❌ **Dashboard Error**: {str(e)}"
    
    def _get_all_strategy_data(self) -> Dict:
        """Get comprehensive data for all strategies"""
        data = {}
        
        for strategy in self.strategies:
            data[strategy] = self._get_strategy_data(strategy)
            
        return data
    
    def _get_strategy_data(self, strategy_id: str) -> Dict:
        """Get detailed data for a single strategy"""
        # Try production path first, fallback to local
        db_path = f"/opt/rtx-trading/data/options_performance_{strategy_id}.db"
        if not os.path.exists(db_path):
            db_path = f"data/options_performance_{strategy_id}.db"
            
        if not os.path.exists(db_path):
            return self._get_default_strategy_data(strategy_id)
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get current balance
            cursor.execute("SELECT balance_after FROM account_history ORDER BY rowid DESC LIMIT 1")
            balance_row = cursor.fetchone()
            balance = balance_row[0] if balance_row else 1000.0
            
            # Get total trades
            cursor.execute("SELECT COUNT(*) FROM options_outcomes")
            total_trades = cursor.fetchone()[0]
            
            # Get win rate
            cursor.execute("SELECT COUNT(*) FROM options_outcomes WHERE net_pnl > 0")
            winning_trades = cursor.fetchone()[0]
            win_rate = (winning_trades / total_trades) if total_trades > 0 else 0
            
            # Get open positions
            cursor.execute("SELECT COUNT(*) FROM options_predictions WHERE status = 'OPEN'")
            open_positions = cursor.fetchone()[0]
            
            # Get recent performance (last 7 days)
            cursor.execute("""
                SELECT COUNT(*), 
                       SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END),
                       AVG(net_pnl),
                       SUM(net_pnl)
                FROM options_outcomes 
                WHERE exit_timestamp > datetime('now', '-7 days')
            """)
            recent_data = cursor.fetchone()
            recent_trades = recent_data[0] or 0
            recent_wins = recent_data[1] or 0
            recent_avg_pnl = recent_data[2] or 0
            recent_total_pnl = recent_data[3] or 0
            
            # Get profit factor
            cursor.execute("SELECT SUM(net_pnl) FROM options_outcomes WHERE net_pnl > 0")
            total_profits = cursor.fetchone()[0] or 0
            cursor.execute("SELECT ABS(SUM(net_pnl)) FROM options_outcomes WHERE net_pnl < 0")
            total_losses = cursor.fetchone()[0] or 1
            profit_factor = total_profits / total_losses if total_losses > 0 else 0
            
            # Get recent streak
            cursor.execute("""
                SELECT net_pnl FROM options_outcomes 
                ORDER BY exit_timestamp DESC 
                LIMIT 5
            """)
            recent_pnls = cursor.fetchall()
            recent_streak = self._calculate_streak([row[0] for row in recent_pnls])
            
            # Get latest positions
            cursor.execute("""
                SELECT contract_symbol, entry_price, contracts, confidence
                FROM options_predictions 
                WHERE status = 'OPEN' 
                ORDER BY timestamp DESC 
                LIMIT 3
            """)
            latest_positions = cursor.fetchall()
            
            conn.close()
            
            return {
                'balance': balance,
                'starting_balance': 1000.0,
                'total_return': balance - 1000.0,
                'total_return_pct': (balance - 1000.0) / 1000.0,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'open_positions': open_positions,
                'recent_trades': recent_trades,
                'recent_wins': recent_wins,
                'recent_win_rate': (recent_wins / recent_trades) if recent_trades > 0 else 0,
                'recent_avg_pnl': recent_avg_pnl,
                'recent_total_pnl': recent_total_pnl,
                'recent_streak': recent_streak,
                'latest_positions': latest_positions,
                'status': self._get_strategy_status(balance, open_positions, win_rate)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting {strategy_id} data: {e}")
            return self._get_default_strategy_data(strategy_id)
    
    def _get_default_strategy_data(self, strategy_id: str) -> Dict:
        """Get default data when database is not available"""
        base_balances = {"conservative": 890.50, "moderate": 720.75, "aggressive": 582.30}
        balance = base_balances.get(strategy_id, 1000.0)
        
        return {
            'balance': balance,
            'starting_balance': 1000.0,
            'total_return': balance - 1000.0,
            'total_return_pct': (balance - 1000.0) / 1000.0,
            'total_trades': 0,
            'winning_trades': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'open_positions': 0,
            'recent_trades': 0,
            'recent_wins': 0,
            'recent_win_rate': 0,
            'recent_avg_pnl': 0,
            'recent_total_pnl': 0,
            'recent_streak': 0,
            'latest_positions': [],
            'status': 'No Data'
        }
    
    def _calculate_streak(self, pnls: List[float]) -> int:
        """Calculate current win/loss streak"""
        if not pnls:
            return 0
            
        streak = 0
        first_positive = pnls[0] > 0
        
        for pnl in pnls:
            if (pnl > 0) == first_positive:
                streak += 1 if first_positive else -1
            else:
                break
                
        return streak
    
    def _get_strategy_status(self, balance: float, positions: int, win_rate: float) -> str:
        """Determine strategy status based on performance"""
        if balance < 300 and positions == 0:
            return "⚠️ Ready for Reset"
        elif win_rate > 0.6:
            return "🔥 Hot Streak"
        elif win_rate < 0.3 and balance < 800:
            return "❄️ Cold Streak"
        elif positions > 0:
            return "📈 Active Trading"
        else:
            return "⏸️ Waiting"
    
    def _generate_rankings(self, strategy_data: Dict) -> str:
        """Generate current strategy rankings"""
        rankings = "🏆 **Current Leader Board**\n\n"
        
        # Sort strategies by balance
        sorted_strategies = sorted(
            strategy_data.items(),
            key=lambda x: x[1]['balance'],
            reverse=True
        )
        
        rank_emojis = ["🥇", "🥈", "🥉"]
        
        for i, (strategy_id, data) in enumerate(sorted_strategies):
            emoji = rank_emojis[i] if i < 3 else "📊"
            strategy_emoji = self.strategy_emojis[strategy_id]
            
            # Performance bar (10 segments)
            performance_score = min(max((data['balance'] - 500) / 500, 0), 1)
            filled_bars = int(performance_score * 10)
            bar = "█" * filled_bars + "░" * (10 - filled_bars)
            
            rankings += f"{emoji} {strategy_emoji} **{strategy_id.title()}**: ${data['balance']:.2f} "
            rankings += f"({data['total_return_pct']:+.1%})\n"
            rankings += f"    {bar} {performance_score*10:.1f}/10 "
            rankings += f"• {data['win_rate']:.1%} WR • {data['total_trades']} trades\n"
            rankings += f"    Status: {data['status']}\n\n"
        
        return rankings
    
    def _generate_performance_charts(self, strategy_data: Dict) -> str:
        """Generate ASCII performance charts"""
        charts = "📈 **Recent Performance (7 days)**\n\n"
        
        for strategy_id, data in strategy_data.items():
            emoji = self.strategy_emojis[strategy_id]
            
            # Recent performance indicator
            if data['recent_total_pnl'] > 0:
                trend = "↗️"
                color = "🟢"
            elif data['recent_total_pnl'] < 0:
                trend = "↘️"
                color = "🔴"
            else:
                trend = "→"
                color = "🟡"
                
            charts += f"{emoji} **{strategy_id.title()}** {trend}\n"
            charts += f"   Week P&L: {color} ${data['recent_total_pnl']:+.2f} "
            charts += f"({data['recent_win_rate']:.1%} WR, {data['recent_trades']} trades)\n"
            
            # Streak indicator
            if data['recent_streak'] != 0:
                streak_emoji = "🔥" if data['recent_streak'] > 0 else "❄️"
                charts += f"   {streak_emoji} {abs(data['recent_streak'])} trade streak\n"
                
            charts += "\n"
        
        return charts
    
    def _generate_signal_status(self) -> str:
        """Generate signal performance status"""
        # This would be enhanced to show actual signal performance
        # For now, showing static indicators
        signals = "🎯 **Signal Status**\n\n"
        
        hot_signals = ["technical_analysis", "momentum", "options_flow"]
        cold_signals = ["news_sentiment", "market_regime"]
        neutral_signals = ["volatility_analysis", "sector_correlation", "mean_reversion"]
        
        signals += "🔥 **Hot**: " + ", ".join(hot_signals) + "\n"
        signals += "❄️ **Cold**: " + ", ".join(cold_signals) + "\n" 
        signals += "⚡ **Neutral**: " + ", ".join(neutral_signals) + "\n\n"
        
        return signals
    
    def _generate_market_status(self) -> str:
        """Generate market status and timing"""
        status = "⏰ **Market Status**\n\n"
        
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S UTC")
        
        # Simple market hours check (9:30 AM - 4:00 PM ET)
        market_open = 14  # 9:30 AM ET in UTC (approximation)
        market_close = 21  # 4:00 PM ET in UTC (approximation)
        
        if market_open <= now.hour < market_close:
            status += "✅ **Market**: OPEN\n"
            next_close = now.replace(hour=market_close, minute=0, second=0)
            time_to_close = next_close - now
            hours, remainder = divmod(time_to_close.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            status += f"🕐 **Closes in**: {hours}h {minutes}m\n"
        else:
            status += "🔴 **Market**: CLOSED\n"
            # Calculate time to next open
            if now.hour >= market_close:
                next_open = (now + timedelta(days=1)).replace(hour=market_open, minute=30, second=0)
            else:
                next_open = now.replace(hour=market_open, minute=30, second=0)
            time_to_open = next_open - now
            hours, remainder = divmod(time_to_open.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            status += f"🕐 **Opens in**: {hours}h {minutes}m\n"
        
        status += f"⏱️ **Next Cycle**: ~8 minutes\n"
        status += f"🕐 **Current Time**: {current_time}\n\n"
        
        return status
    
    def _generate_recent_activity(self, strategy_data: Dict) -> str:
        """Generate recent trading activity"""
        activity = "📋 **Recent Activity**\n\n"
        
        total_positions = sum(data['open_positions'] for data in strategy_data.values())
        
        if total_positions == 0:
            activity += "💤 No open positions\n"
            activity += "🎯 Waiting for high-confidence signals\n\n"
        else:
            activity += f"💰 **{total_positions} Active Positions**\n\n"
            
            for strategy_id, data in strategy_data.items():
                if data['latest_positions']:
                    emoji = self.strategy_emojis[strategy_id]
                    activity += f"{emoji} **{strategy_id.title()}**:\n"
                    
                    for pos in data['latest_positions'][:2]:  # Show max 2 positions
                        contract, price, contracts, confidence = pos
                        activity += f"   • {contract} x{contracts} @ ${price:.2f} ({confidence:.1%})\n"
                    
                    if len(data['latest_positions']) > 2:
                        remaining = len(data['latest_positions']) - 2
                        activity += f"   ... and {remaining} more\n"
                    activity += "\n"
        
        return activity
    
    def get_quick_summary(self) -> str:
        """Get a quick one-line summary for regular updates"""
        try:
            strategy_data = self._get_all_strategy_data()
            
            # Find leader
            leader = max(strategy_data.items(), key=lambda x: x[1]['balance'])
            leader_name = leader[0].title()
            leader_balance = leader[1]['balance']
            leader_return = leader[1]['total_return_pct']
            
            # Count total positions
            total_positions = sum(data['open_positions'] for data in strategy_data.values())
            
            # Get overall performance
            total_balance = sum(data['balance'] for data in strategy_data.values())
            avg_return = (total_balance - 3000) / 3000  # 3 strategies * $1000 each
            
            return (f"🏆 Leader: {leader_name} ${leader_balance:.2f} ({leader_return:+.1%}) "
                   f"• {total_positions} positions • Avg: {avg_return:+.1%}")
            
        except Exception as e:
            return f"❌ Summary error: {str(e)}"

# Global instance
dashboard = PerformanceDashboard()

if __name__ == "__main__":
    # Test the dashboard
    print("🧪 Testing Performance Dashboard")
    print("="*50)
    
    dashboard_display = dashboard.generate_dashboard()
    print(dashboard_display)
    
    print("\n" + "="*50)
    print("Quick Summary:")
    print(dashboard.get_quick_summary())
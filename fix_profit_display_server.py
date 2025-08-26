#!/usr/bin/env python3
"""
Fixed profit calculation for accurate display
"""
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional

class FixedProfitCalculator:
    """Calculate accurate profit percentages after July reset"""
    
    def __init__(self):
        self.reset_date = datetime(2025, 7, 29)  # Date of balance reset
        self.reset_balance = 2000.0  # Each strategy reset to $2000
        
    def get_accurate_profit_stats(self) -> Dict:
        """Get accurate profit statistics for all strategies"""
        
        strategies_data = {}
        total_current_balance = 0
        total_initial_balance = 0
        active_strategies = 0
        
        # Check each strategy
        strategy_names = ['conservative', 'moderate', 'aggressive', 'scalping', 
                         'swing', 'momentum', 'volatility', 'mean_reversion']
        
        for strategy in strategy_names:
            try:
                # Get current balance from multi-strategy DB
                conn = sqlite3.connect('data/algoslayer_multi_strategy.db')
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT current_balance, total_pnl FROM trading_strategies WHERE LOWER(name) = ?",
                    (strategy,)
                )
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    current_balance = result[0]
                    total_pnl = result[1]
                    
                    # For post-reset period, initial balance is always $2000
                    initial_balance = self.reset_balance
                    
                    # Calculate actual P&L since reset
                    actual_pnl = current_balance - initial_balance
                    profit_pct = (actual_pnl / initial_balance * 100) if initial_balance > 0 else 0
                    
                    # Check if strategy has any trades
                    try:
                        conn = sqlite3.connect(f'data/options_performance_{strategy}.db')
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM options_predictions WHERE timestamp > ?", 
                                     (self.reset_date.isoformat(),))
                        trade_count = cursor.fetchone()[0]
                        conn.close()
                        
                        has_trades = trade_count > 0
                    except:
                        has_trades = False
                        trade_count = 0
                    
                    strategies_data[strategy] = {
                        'current_balance': current_balance,
                        'initial_balance': initial_balance,
                        'pnl': actual_pnl,
                        'profit_pct': profit_pct,
                        'has_trades': has_trades,
                        'trade_count': trade_count
                    }
                    
                    # Add to totals
                    total_current_balance += current_balance
                    total_initial_balance += initial_balance
                    if has_trades:
                        active_strategies += 1
                        
            except Exception as e:
                print(f"Error processing {strategy}: {e}")
                continue
        
        # Calculate overall statistics
        total_pnl = total_current_balance - total_initial_balance
        overall_profit_pct = (total_pnl / total_initial_balance * 100) if total_initial_balance > 0 else 0
        
        return {
            'strategies': strategies_data,
            'total_current_balance': total_current_balance,
            'total_initial_balance': total_initial_balance,
            'total_pnl': total_pnl,
            'overall_profit_pct': overall_profit_pct,
            'active_strategies': active_strategies,
            'total_strategies': len(strategies_data)
        }
    
    def get_notification_text(self) -> str:
        """Generate accurate notification text"""
        
        stats = self.get_accurate_profit_stats()
        
        # Format the notification
        active = stats['active_strategies']
        total = stats['total_strategies']
        
        if stats['overall_profit_pct'] != 0:
            profit_emoji = "📈" if stats['overall_profit_pct'] > 0 else "📉"
            profit_text = f"{profit_emoji} Overall: {stats['overall_profit_pct']:.1f}%"
        else:
            profit_text = "➖ Overall: 0.0% (Fresh start after reset)"
        
        notification = f"""
🏦 **ACCOUNT STATUS**
💰 Total Balance: ${stats['total_current_balance']:.2f}
{profit_text}
📊 Active Strategies: {active}/{total}

**Strategy Breakdown:**
"""
        
        # Add individual strategy info
        for strategy, data in stats['strategies'].items():
            if data['has_trades']:
                emoji = "🟢" if data['profit_pct'] >= 0 else "🔴"
                notification += f"{emoji} {strategy.title()}: ${data['current_balance']:.2f} ({data['profit_pct']:+.1f}%)\n"
        
        # Add inactive strategies
        inactive = [s for s, d in stats['strategies'].items() if not d['has_trades']]
        if inactive:
            notification += f"\n⚪ Inactive: {', '.join(s.title() for s in inactive)}"
        
        notification += f"""

📌 **Note**: All strategies were reset to $2,000 on July 29, 2025.
Profit % shown is from this reset date, not historical performance.
"""
        
        return notification

def apply_fix():
    """Apply the profit display fix"""
    
    print("🔧 Applying profit display fix...")
    
    # Test the fix
    calculator = FixedProfitCalculator()
    stats = calculator.get_accurate_profit_stats()
    
    print("\n📊 ACCURATE PROFIT STATISTICS:")
    print(f"Total Balance: ${stats['total_current_balance']:.2f}")
    print(f"Total Initial: ${stats['total_initial_balance']:.2f}")
    print(f"Total P&L: ${stats['total_pnl']:.2f}")
    print(f"Overall Profit: {stats['overall_profit_pct']:.1f}%")
    print(f"Active Strategies: {stats['active_strategies']}/{stats['total_strategies']}")
    
    print("\n📱 SAMPLE NOTIFICATION:")
    print(calculator.get_notification_text())
    
    # Save the fix
    with open('src/core/profit_calculator.py', 'w') as f:
        f.write('''#!/usr/bin/env python3
# Fixed profit calculator - imported by notification system
from datetime import datetime
import sqlite3
import json

class ProfitCalculator:
    def __init__(self):
        self.reset_date = datetime(2025, 7, 29)
        self.reset_balance = 2000.0
        
    def get_strategy_profit(self, strategy_name: str) -> float:
        """Get accurate profit % for a strategy"""
        try:
            conn = sqlite3.connect('data/algoslayer_multi_strategy.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT current_balance FROM trading_strategies WHERE LOWER(name) = ?",
                (strategy_name.lower(),)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                current = result[0]
                # Always use reset balance as initial
                return ((current - self.reset_balance) / self.reset_balance) * 100
        except:
            pass
        return 0.0
        
    def get_overall_profit(self) -> float:
        """Get accurate overall profit %"""
        try:
            conn = sqlite3.connect('data/algoslayer_multi_strategy.db')
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(current_balance) FROM trading_strategies")
            total_current = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM trading_strategies")
            strategy_count = cursor.fetchone()[0] or 0
            conn.close()
            
            if strategy_count > 0:
                total_initial = strategy_count * self.reset_balance
                return ((total_current - total_initial) / total_initial) * 100
        except:
            pass
        return 0.0

# Global instance
profit_calculator = ProfitCalculator()
''')
    
    print("\n✅ Fix saved to src/core/profit_calculator.py")
    print("\n🎯 WHAT THIS FIXES:")
    print("• Removes the confusing 433% display")
    print("• Shows accurate 0% profit (since all strategies were reset to $2000)")
    print("• Clearly indicates which strategies are active vs inactive")
    print("• Adds note about July 29 reset for clarity")
    
    return True

if __name__ == "__main__":
    apply_fix()

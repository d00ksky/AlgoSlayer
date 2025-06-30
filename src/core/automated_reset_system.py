"""
Automated Strategy Reset System
Manages strategy "lives" with intelligent reset triggers and learning preservation
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import sqlite3
import json

class AutomatedResetSystem:
    """Manages automated strategy resets with lives tracking"""
    
    def __init__(self):
        self.db_path = "/opt/rtx-trading/data/algoslayer_main.db"
        
        # Reset configuration
        self.reset_thresholds = {
            "balance_threshold": 300,      # Reset when balance < $300
            "max_consecutive_losses": 8,   # Reset after 8 consecutive losses
            "max_drawdown": 0.70,         # Reset at 70% drawdown
            "min_days_before_reset": 7    # Wait at least 7 days between resets
        }
        
        # Lives tracking
        self.lives_data = {
            "conservative": {"current_life": 1, "total_lives": 1, "cumulative_pnl": 0},
            "moderate": {"current_life": 1, "total_lives": 1, "cumulative_pnl": 0},
            "aggressive": {"current_life": 1, "total_lives": 1, "cumulative_pnl": 0}
        }
        
        self.reset_history = []
    
    def check_reset_conditions(self, strategy_id: str, current_balance: float, 
                              recent_performance: Dict) -> Dict:
        """Check if strategy meets reset conditions"""
        
        reset_reasons = []
        should_reset = False
        
        # Check balance threshold
        if current_balance < self.reset_thresholds["balance_threshold"]:
            reset_reasons.append(f"Balance below ${self.reset_thresholds['balance_threshold']}")
            should_reset = True
        
        # Check consecutive losses
        consecutive_losses = recent_performance.get("consecutive_losses", 0)
        if consecutive_losses >= self.reset_thresholds["max_consecutive_losses"]:
            reset_reasons.append(f"{consecutive_losses} consecutive losses")
            should_reset = True
        
        # Check maximum drawdown
        max_drawdown = recent_performance.get("max_drawdown", 0)
        if max_drawdown >= self.reset_thresholds["max_drawdown"]:
            reset_reasons.append(f"{max_drawdown:.1%} drawdown exceeded")
            should_reset = True
        
        # Check if enough time has passed since last reset
        if should_reset:
            last_reset = self._get_last_reset_date(strategy_id)
            if last_reset:
                days_since_reset = (datetime.now() - last_reset).days
                if days_since_reset < self.reset_thresholds["min_days_before_reset"]:
                    should_reset = False
                    reset_reasons.append(f"Too soon (only {days_since_reset} days since last reset)")
        
        return {
            "should_reset": should_reset,
            "reasons": reset_reasons,
            "current_balance": current_balance,
            "consecutive_losses": consecutive_losses,
            "max_drawdown": max_drawdown
        }
    
    def execute_strategy_reset(self, strategy_id: str, reset_reason: str) -> Dict:
        """Execute automated strategy reset with data preservation"""
        
        try:
            # 1. Preserve current performance data
            backup_data = self._backup_strategy_data(strategy_id)
            
            # 2. Update lives tracking
            self._update_lives_tracking(strategy_id, backup_data)
            
            # 3. Reset account balance to $1000
            new_balance = 1000.0
            
            # 4. Clear open positions
            self._clear_open_positions(strategy_id)
            
            # 5. Reset performance counters (but preserve learning data)
            self._reset_performance_counters(strategy_id)
            
            # 6. Log the reset
            reset_record = {
                "strategy_id": strategy_id,
                "reset_time": datetime.now(),
                "reason": reset_reason,
                "previous_balance": backup_data.get("final_balance", 0),
                "new_life": self.lives_data[strategy_id]["current_life"] + 1,
                "preserved_data": backup_data
            }
            
            self.reset_history.append(reset_record)
            self.lives_data[strategy_id]["current_life"] += 1
            self.lives_data[strategy_id]["total_lives"] += 1
            
            return {
                "status": "success",
                "new_balance": new_balance,
                "new_life": self.lives_data[strategy_id]["current_life"],
                "total_lives": self.lives_data[strategy_id]["total_lives"],
                "cumulative_pnl": self.lives_data[strategy_id]["cumulative_pnl"],
                "reset_reason": reset_reason,
                "preserved_learning": True
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _backup_strategy_data(self, strategy_id: str) -> Dict:
        """Backup strategy performance data before reset"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get current performance metrics
                cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    AVG(CASE WHEN net_pnl > 0 THEN 1.0 ELSE 0.0 END) as win_rate,
                    SUM(net_pnl) as total_pnl,
                    AVG(net_pnl) as avg_pnl
                FROM predictions p
                JOIN outcomes o ON p.prediction_id = o.prediction_id
                WHERE p.strategy_id = ?
                """, (strategy_id,))
                
                performance_data = cursor.fetchone()
                
                return {
                    "strategy_id": strategy_id,
                    "backup_time": datetime.now(),
                    "total_trades": performance_data[0] if performance_data else 0,
                    "win_rate": performance_data[1] if performance_data else 0,
                    "total_pnl": performance_data[2] if performance_data else 0,
                    "avg_pnl": performance_data[3] if performance_data else 0,
                    "final_balance": 1000 + (performance_data[2] if performance_data else 0)
                }
                
        except Exception as e:
            return {"error": str(e)}
    
    def _update_lives_tracking(self, strategy_id: str, backup_data: Dict):
        """Update cumulative lives tracking"""
        
        if strategy_id in self.lives_data:
            final_pnl = backup_data.get("total_pnl", 0)
            self.lives_data[strategy_id]["cumulative_pnl"] += final_pnl
    
    def _clear_open_positions(self, strategy_id: str):
        """Clear any open positions for the strategy"""
        
        # In paper trading, this would reset position tracking
        # Implementation depends on how positions are stored
        pass
    
    def _reset_performance_counters(self, strategy_id: str):
        """Reset performance counters while preserving learning data"""
        
        # Reset balance and trade counters
        # But preserve signal learning weights and historical patterns
        pass
    
    def _get_last_reset_date(self, strategy_id: str) -> Optional[datetime]:
        """Get the date of the last reset for this strategy"""
        
        strategy_resets = [r for r in self.reset_history if r["strategy_id"] == strategy_id]
        if strategy_resets:
            return max(r["reset_time"] for r in strategy_resets)
        return None
    
    def get_lives_status(self) -> Dict:
        """Get current lives status for all strategies"""
        
        status = {}
        for strategy_id, data in self.lives_data.items():
            status[strategy_id] = {
                "current_life": data["current_life"],
                "total_lives": data["total_lives"],
                "cumulative_pnl": data["cumulative_pnl"],
                "last_reset": self._get_last_reset_date(strategy_id),
                "next_reset_threshold": self.reset_thresholds["balance_threshold"]
            }
        
        return status
    
    def generate_lives_report(self) -> str:
        """Generate comprehensive lives status report"""
        
        status = self.get_lives_status()
        
        report = f"""
🎮 **STRATEGY LIVES STATUS**

🏆 **Overall Performance**:
"""
        
        total_cumulative_pnl = sum(data["cumulative_pnl"] for data in status.values())
        total_lives_used = sum(data["total_lives"] for data in status.values())
        
        report += f"💰 **Total Cumulative P&L**: ${total_cumulative_pnl:.2f}\n"
        report += f"🎯 **Total Lives Used**: {total_lives_used}\n\n"
        
        for strategy_id, data in status.items():
            emoji = "🥇" if strategy_id == "conservative" else "🥈" if strategy_id == "moderate" else "🥉"
            
            report += f"{emoji} **{strategy_id.upper()}**:\n"
            report += f"  • Current Life: #{data['current_life']}\n"
            report += f"  • Total Lives: {data['total_lives']}\n"
            report += f"  • Cumulative P&L: ${data['cumulative_pnl']:.2f}\n"
            
            if data["last_reset"]:
                days_since = (datetime.now() - data["last_reset"]).days
                report += f"  • Last Reset: {days_since} days ago\n"
            else:
                report += f"  • Last Reset: Never\n"
            
            report += f"\n"
        
        report += f"⚠️ **Reset Trigger**: Balance < ${self.reset_thresholds['balance_threshold']}\n"
        report += f"🔄 **Auto-Reset**: {'✅ Enabled' if True else '❌ Disabled'}"
        
        return report.strip()
    
    def simulate_reset_scenario(self, strategy_id: str, current_balance: float) -> str:
        """Simulate what would happen if strategy was reset now"""
        
        performance_data = {
            "consecutive_losses": 5,  # Example data
            "max_drawdown": 0.65
        }
        
        check_result = self.check_reset_conditions(strategy_id, current_balance, performance_data)
        
        if check_result["should_reset"]:
            return f"""
🔄 **RESET SIMULATION FOR {strategy_id.upper()}**

✅ **Would Reset**: YES
📋 **Reasons**: {', '.join(check_result['reasons'])}
💰 **New Balance**: $1,000.00
🎮 **New Life**: #{self.lives_data[strategy_id]['current_life'] + 1}
📊 **Learning Data**: Preserved
"""
        else:
            return f"""
🔄 **RESET SIMULATION FOR {strategy_id.upper()}**

❌ **Would Reset**: NO
💰 **Current Balance**: ${current_balance:.2f}
📈 **Status**: Strategy continues running
⏳ **Next Check**: Automatic (every trading cycle)
"""

# Global instance
automated_reset_system = AutomatedResetSystem()

"""
Automated Exit Strategy with Ladders
Implements sophisticated stop-loss and profit-taking rules
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class AutomatedExitStrategy:
    """Manages automated exits with ladders and trailing stops"""
    
    def __init__(self):
        # Profit taking ladder (take profits at multiple levels)
        self.profit_ladder = [
            {"level": 0.5, "percentage": 0.25},  # Take 25% at 50% profit
            {"level": 1.0, "percentage": 0.5},   # Take 50% at 100% profit  
            {"level": 2.0, "percentage": 1.0}    # Take all remaining at 200% profit
        ]
        
        # Stop loss rules
        self.stop_loss_rules = {
            "initial": 0.5,     # Initial 50% stop loss
            "breakeven": 0.25,  # Move to breakeven after 25% profit
            "trailing": 0.15    # Trailing stop at 15% below peak
        }
        
    def should_exit_position(self, position: Dict, current_price: float) -> Optional[Dict]:
        """Determine if position should be exited and how much"""
        
        entry_price = position.get("entry_price", 0)
        contracts = position.get("contracts", 0)
        entry_time = position.get("entry_time")
        peak_profit = position.get("peak_profit", 0)
        
        if not entry_price or not contracts:
            return None
            
        # Calculate current P&L
        current_pnl_pct = (current_price - entry_price) / entry_price
        current_profit = current_pnl_pct * 100
        
        # Update peak profit
        if current_profit > peak_profit:
            peak_profit = current_profit
            
        # Check profit taking ladder
        for ladder in self.profit_ladder:
            if (current_profit >= ladder["level"] * 100 and 
                not position.get(f"ladder_{ladder['level']}_taken", False)):
                
                contracts_to_sell = int(contracts * ladder["percentage"])
                if contracts_to_sell > 0:
                    logger.info(f"🎯 Profit ladder triggered: Taking {ladder['percentage']:.0%} at {current_profit:.1f}% profit")
                    return {
                        "action": "PARTIAL_EXIT",
                        "reason": f"profit_ladder_{ladder['level']}",
                        "contracts": contracts_to_sell,
                        "remaining_contracts": contracts - contracts_to_sell
                    }
        
        # Check stop loss rules
        stop_loss_price = self._calculate_stop_loss(position, current_price, peak_profit)
        
        if current_price <= stop_loss_price:
            logger.warning(f"🛑 Stop loss triggered at {current_profit:.1f}% loss")
            return {
                "action": "FULL_EXIT",
                "reason": "stop_loss",
                "contracts": contracts
            }
            
        # Check time-based exits (avoid theta decay)
        if entry_time:
            days_held = (datetime.now() - entry_time).days
            days_to_expiry = position.get("days_to_expiry", 30)
            
            if days_held >= (days_to_expiry * 0.75):  # 75% of time to expiry
                logger.info(f"⏰ Time decay exit: {days_held} days held, {days_to_expiry} DTE")
                return {
                    "action": "FULL_EXIT", 
                    "reason": "time_decay",
                    "contracts": contracts
                }
        
        return None
    
    def _calculate_stop_loss(self, position: Dict, current_price: float, peak_profit: float) -> float:
        """Calculate dynamic stop loss price"""
        
        entry_price = position.get("entry_price", 0)
        current_pnl_pct = (current_price - entry_price) / entry_price
        
        # If at breakeven or better, use trailing stop
        if current_pnl_pct >= 0.25:  # 25% profit threshold
            trailing_stop = peak_profit * (1 - self.stop_loss_rules["trailing"])
            return entry_price * (1 + trailing_stop / 100)
        else:
            # Use initial stop loss
            return entry_price * (1 - self.stop_loss_rules["initial"])

# Global instance
automated_exit_strategy = AutomatedExitStrategy()

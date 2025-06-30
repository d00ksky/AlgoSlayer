"""
Real-time Performance Monitoring and Alert System
Monitors system health and trading performance with automatic alerts
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import asyncio

class PerformanceMonitor:
    """Monitors system performance and sends alerts"""
    
    def __init__(self):
        self.alert_thresholds = {
            "drawdown_warning": 0.15,      # 15% drawdown warning
            "drawdown_critical": 0.25,     # 25% drawdown critical
            "win_rate_low": 0.30,          # Win rate below 30%
            "consecutive_losses": 5,        # 5 consecutive losses
            "system_error_count": 3        # 3 system errors in 1 hour
        }
        
        self.performance_history = []
        self.error_log = []
        
    async def check_strategy_health(self, strategy_id: str, strategy_data: Dict) -> Optional[Dict]:
        """Check individual strategy health and generate alerts"""
        
        balance = strategy_data.get("balance", 1000)
        total_trades = strategy_data.get("total_trades", 0)
        win_rate = strategy_data.get("win_rate", 0)
        consecutive_losses = strategy_data.get("consecutive_losses", 0)
        
        alerts = []
        
        # Check drawdown
        initial_balance = 1000  # Starting balance
        drawdown = (initial_balance - balance) / initial_balance
        
        if drawdown >= self.alert_thresholds["drawdown_critical"]:
            alerts.append({
                "level": "CRITICAL",
                "message": f"🚨 {strategy_id.upper()}: Critical drawdown {drawdown:.1%} (${balance:.2f})",
                "action": "Consider stopping strategy"
            })
        elif drawdown >= self.alert_thresholds["drawdown_warning"]:
            alerts.append({
                "level": "WARNING", 
                "message": f"⚠️ {strategy_id.upper()}: High drawdown {drawdown:.1%} (${balance:.2f})",
                "action": "Monitor closely"
            })
            
        # Check win rate (only if sufficient trades)
        if total_trades >= 10 and win_rate < self.alert_thresholds["win_rate_low"]:
            alerts.append({
                "level": "WARNING",
                "message": f"📉 {strategy_id.upper()}: Low win rate {win_rate:.1%} over {total_trades} trades",
                "action": "Review strategy parameters"
            })
            
        # Check consecutive losses
        if consecutive_losses >= self.alert_thresholds["consecutive_losses"]:
            alerts.append({
                "level": "WARNING",
                "message": f"📉 {strategy_id.upper()}: {consecutive_losses} consecutive losses",
                "action": "Consider reducing position size"
            })
            
        return alerts if alerts else None
    
    async def check_system_health(self) -> Optional[List[Dict]]:
        """Check overall system health"""
        
        alerts = []
        
        # Check recent errors
        recent_errors = [e for e in self.error_log 
                        if (datetime.now() - e["timestamp"]).seconds < 3600]
        
        if len(recent_errors) >= self.alert_thresholds["system_error_count"]:
            alerts.append({
                "level": "WARNING",
                "message": f"🔧 System: {len(recent_errors)} errors in last hour",
                "action": "Check system logs"
            })
            
        return alerts if alerts else None
    
    def log_error(self, error_message: str, component: str):
        """Log system error for monitoring"""
        self.error_log.append({
            "timestamp": datetime.now(),
            "message": error_message,
            "component": component
        })
        
        # Keep only last 24 hours of errors
        cutoff = datetime.now() - timedelta(hours=24)
        self.error_log = [e for e in self.error_log if e["timestamp"] > cutoff]
    
    async def generate_daily_summary(self) -> str:
        """Generate daily performance summary"""
        
        summary = f"""
📊 **DAILY PERFORMANCE SUMMARY**
🕐 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

🎯 **System Status**: Operational
📈 **Market Hours**: {'Active' if datetime.now().hour in range(9, 16) else 'Closed'}
🔧 **Errors Today**: {len([e for e in self.error_log if e['timestamp'].date() == datetime.now().date()])}

💡 **Performance Alerts**: Check /dashboard for detailed metrics
🎮 **Strategy Health**: All strategies monitored continuously

⚡ **Next Check**: Automated in 1 hour
"""
        
        return summary.strip()

# Global instance
performance_monitor = PerformanceMonitor()

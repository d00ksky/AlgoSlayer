"""
IV Rank Percentile Alert System
Monitors RTX volatility patterns and sends optimal timing alerts
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class IVPercentileAlerts:
    """Monitors IV percentiles and generates timing alerts"""
    
    def __init__(self):
        self.symbol = "RTX"
        self.alert_thresholds = {
            "extremely_cheap": 10,    # IV rank < 10th percentile - STRONG BUY
            "cheap": 25,              # IV rank < 25th percentile - BUY  
            "expensive": 75,          # IV rank > 75th percentile - CAUTION
            "extremely_expensive": 90 # IV rank > 90th percentile - AVOID
        }
        
        self.last_alert_time = {}
        self.alert_cooldown_minutes = 60  # Don't spam alerts
        
    def check_iv_alerts(self) -> List[Dict]:
        """Check current IV rank and generate alerts if needed"""
        
        # Get current IV data (using existing IV optimizer)
        try:
            from src.core.iv_rank_optimizer import iv_rank_optimizer
            iv_data = iv_rank_optimizer.get_current_iv_rank()
            
            if iv_data.get("status") != "success":
                return []
            
            iv_rank = iv_data.get("iv_rank", 50)
            current_iv = iv_data.get("current_iv", 25)
            
            alerts = []
            
            # Check for alert conditions
            if iv_rank <= self.alert_thresholds["extremely_cheap"]:
                alert = self._create_alert(
                    "EXTREMELY_CHEAP",
                    f"🔥 **PRIME BUYING OPPORTUNITY** 🔥\n\nRTX IV Rank: {iv_rank:.1f}% (EXTREMELY LOW)\nCurrent IV: {current_iv:.1f}%\n\n✅ **STRONG BUY SIGNAL** - Options are severely underpriced!\n💰 **Strategy**: Buy calls/puts aggressively",
                    "success",
                    iv_rank,
                    current_iv
                )
                alerts.append(alert)
                
            elif iv_rank <= self.alert_thresholds["cheap"]:
                alert = self._create_alert(
                    "CHEAP",
                    f"📈 **GOOD BUYING OPPORTUNITY**\n\nRTX IV Rank: {iv_rank:.1f}% (LOW)\nCurrent IV: {current_iv:.1f}%\n\n✅ **BUY SIGNAL** - Favorable options pricing\n💡 **Strategy**: Consider long options positions",
                    "info",
                    iv_rank,
                    current_iv
                )
                alerts.append(alert)
                
            elif iv_rank >= self.alert_thresholds["extremely_expensive"]:
                alert = self._create_alert(
                    "EXTREMELY_EXPENSIVE",
                    f"🚨 **DANGER ZONE** 🚨\n\nRTX IV Rank: {iv_rank:.1f}% (EXTREMELY HIGH)\nCurrent IV: {current_iv:.1f}%\n\n❌ **AVOID BUYING** - Options severely overpriced!\n⚠️ **Strategy**: Avoid long positions, wait for IV crush",
                    "warning",
                    iv_rank,
                    current_iv
                )
                alerts.append(alert)
                
            elif iv_rank >= self.alert_thresholds["expensive"]:
                alert = self._create_alert(
                    "EXPENSIVE",
                    f"⚠️ **CAUTION ADVISED**\n\nRTX IV Rank: {iv_rank:.1f}% (HIGH)\nCurrent IV: {current_iv:.1f}%\n\n⚠️ **PROCEED CAREFULLY** - Options pricing elevated\n💡 **Strategy**: Wait for better entry or smaller positions",
                    "caution",
                    iv_rank,
                    current_iv
                )
                alerts.append(alert)
            
            # Filter alerts based on cooldown
            filtered_alerts = self._filter_alerts_by_cooldown(alerts)
            
            return filtered_alerts
            
        except Exception as e:
            return [self._create_error_alert(str(e))]
    
    def _create_alert(self, alert_type: str, message: str, severity: str, iv_rank: float, current_iv: float) -> Dict:
        """Create formatted alert dictionary"""
        
        return {
            "type": alert_type,
            "message": message,
            "severity": severity,
            "iv_rank": iv_rank,
            "current_iv": current_iv,
            "timestamp": datetime.now(),
            "symbol": self.symbol,
            "should_send": True
        }
    
    def _create_error_alert(self, error_message: str) -> Dict:
        """Create error alert"""
        
        return {
            "type": "ERROR",
            "message": f"❌ **IV ALERT SYSTEM ERROR**\n\n{error_message}",
            "severity": "error",
            "timestamp": datetime.now(),
            "should_send": True
        }
    
    def _filter_alerts_by_cooldown(self, alerts: List[Dict]) -> List[Dict]:
        """Filter alerts to prevent spam based on cooldown period"""
        
        filtered_alerts = []
        current_time = datetime.now()
        
        for alert in alerts:
            alert_type = alert["type"]
            
            # Check if we sent this type recently
            if alert_type in self.last_alert_time:
                time_since_last = (current_time - self.last_alert_time[alert_type]).total_seconds() / 60
                
                if time_since_last < self.alert_cooldown_minutes:
                    alert["should_send"] = False
                    continue
            
            # Update last alert time
            self.last_alert_time[alert_type] = current_time
            filtered_alerts.append(alert)
        
        return filtered_alerts
    
    def get_current_iv_status(self) -> Dict:
        """Get current IV status for dashboard display"""
        
        try:
            from src.core.iv_rank_optimizer import iv_rank_optimizer
            iv_data = iv_rank_optimizer.get_current_iv_rank()
            
            if iv_data.get("status") != "success":
                return {"status": "error", "message": "IV data unavailable"}
            
            iv_rank = iv_data.get("iv_rank", 50)
            current_iv = iv_data.get("current_iv", 25)
            
            # Determine status
            if iv_rank <= self.alert_thresholds["extremely_cheap"]:
                status = "EXTREMELY_CHEAP"
                emoji = "🔥"
                recommendation = "STRONG BUY"
            elif iv_rank <= self.alert_thresholds["cheap"]:
                status = "CHEAP"
                emoji = "📈"
                recommendation = "BUY"
            elif iv_rank >= self.alert_thresholds["extremely_expensive"]:
                status = "EXTREMELY_EXPENSIVE"
                emoji = "🚨"
                recommendation = "AVOID"
            elif iv_rank >= self.alert_thresholds["expensive"]:
                status = "EXPENSIVE"
                emoji = "⚠️"
                recommendation = "CAUTION"
            else:
                status = "NORMAL"
                emoji = "📊"
                recommendation = "NEUTRAL"
            
            return {
                "status": "success",
                "iv_rank": iv_rank,
                "current_iv": current_iv,
                "category": status,
                "emoji": emoji,
                "recommendation": recommendation,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def generate_iv_dashboard(self) -> str:
        """Generate IV monitoring dashboard"""
        
        status = self.get_current_iv_status()
        
        if status["status"] != "success":
            return f"❌ **IV MONITORING**: {status.get('message', 'Unknown error')}"
        
        dashboard = f"""
{status['emoji']} **RTX IV RANK MONITOR** {status['emoji']}

📊 **Current Status**: {status['category']}
📈 **IV Rank**: {status['iv_rank']:.1f}% (vs 1-year range)
📊 **Current IV**: {status['current_iv']:.1f}%
🎯 **Recommendation**: {status['recommendation']}

📋 **Alert Thresholds**:
🔥 Extremely Cheap: <{self.alert_thresholds['extremely_cheap']}% (STRONG BUY)
📈 Cheap: <{self.alert_thresholds['cheap']}% (BUY)
⚠️ Expensive: >{self.alert_thresholds['expensive']}% (CAUTION)
🚨 Extremely Expensive: >{self.alert_thresholds['extremely_expensive']}% (AVOID)

⏰ **Last Updated**: {status['timestamp'].strftime('%H:%M:%S')}
"""
        return dashboard.strip()
    
    def run_periodic_check(self) -> List[Dict]:
        """Run periodic IV check and return any alerts"""
        
        alerts = self.check_iv_alerts()
        return [alert for alert in alerts if alert.get("should_send", False)]

# Global instance
iv_percentile_alerts = IVPercentileAlerts()

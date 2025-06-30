"""
RTX Earnings Calendar Integration
Predicts and captures volatility around RTX earnings announcements
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import yfinance as yf
import requests

class RTXEarningsCalendar:
    """Manages RTX earnings calendar and volatility predictions"""
    
    def __init__(self):
        self.symbol = "RTX"
        self.earnings_cache = {}
        self.cache_expiry_hours = 24  # Cache for 24 hours
        
        # Typical RTX earnings pattern (quarterly)
        self.typical_earnings_months = [1, 4, 7, 10]  # Jan, Apr, Jul, Oct
        self.typical_earnings_day_range = (20, 28)  # Usually 3rd/4th week
        
        # Volatility patterns around earnings
        self.volatility_patterns = {
            "pre_earnings": {
                "days_before": 5,
                "iv_increase": 1.3,  # 30% IV increase typical
                "confidence_boost": 1.2
            },
            "post_earnings": {
                "days_after": 2,
                "iv_crush": 0.6,  # 40% IV crush typical
                "confidence_reduction": 0.8
            }
        }
    
    def get_next_earnings_date(self) -> Optional[datetime]:
        """Predict next RTX earnings date based on historical patterns"""
        
        # Check cache first
        cache_key = "next_earnings_date"
        if (cache_key in self.earnings_cache and 
            (datetime.now() - self.earnings_cache[cache_key]["timestamp"]).total_seconds() < self.cache_expiry_hours * 3600):
            return self.earnings_cache[cache_key]["date"]
        
        try:
            # Try to get earnings from yfinance
            ticker = yf.Ticker(self.symbol)
            calendar = ticker.calendar
            
            if calendar is not None and not calendar.empty:
                # Get next earnings date from calendar
                next_earnings = calendar.index[0]
                if isinstance(next_earnings, str):
                    next_earnings = datetime.strptime(next_earnings, "%Y-%m-%d")
                
                # Cache result
                self.earnings_cache[cache_key] = {
                    "date": next_earnings,
                    "timestamp": datetime.now(),
                    "source": "yfinance"
                }
                
                return next_earnings
            
        except Exception as e:
            print(f"Yfinance earnings fetch failed: {e}")
        
        # Fallback: Predict based on quarterly pattern
        predicted_date = self._predict_earnings_date()
        
        self.earnings_cache[cache_key] = {
            "date": predicted_date,
            "timestamp": datetime.now(),
            "source": "predicted"
        }
        
        return predicted_date
    
    def _predict_earnings_date(self) -> datetime:
        """Predict next earnings date based on quarterly pattern"""
        
        now = datetime.now()
        current_month = now.month
        current_year = now.year
        
        # Find next earnings month
        next_earnings_month = None
        for month in self.typical_earnings_months:
            if month > current_month:
                next_earnings_month = month
                break
        
        # If no month found this year, use first month of next year
        if next_earnings_month is None:
            next_earnings_month = self.typical_earnings_months[0]
            current_year += 1
        
        # Estimate earnings day (typically 3rd week)
        estimated_day = 21  # Conservative estimate
        
        predicted_date = datetime(current_year, next_earnings_month, estimated_day)
        
        return predicted_date
    
    def get_earnings_proximity_analysis(self) -> Dict:
        """Analyze current proximity to earnings and implications"""
        
        next_earnings = self.get_next_earnings_date()
        
        if not next_earnings:
            return {
                "status": "unknown",
                "days_to_earnings": None,
                "phase": "unknown",
                "volatility_impact": "neutral"
            }
        
        now = datetime.now()
        days_to_earnings = (next_earnings - now).days
        
        # Determine earnings phase
        if days_to_earnings <= 0:
            if days_to_earnings >= -2:
                phase = "post_earnings"
                volatility_impact = "iv_crush"
                confidence_multiplier = self.volatility_patterns["post_earnings"]["confidence_reduction"]
            else:
                phase = "normal"
                volatility_impact = "neutral"
                confidence_multiplier = 1.0
        elif days_to_earnings <= 5:
            phase = "pre_earnings"
            volatility_impact = "iv_expansion"
            confidence_multiplier = self.volatility_patterns["pre_earnings"]["confidence_boost"]
        elif days_to_earnings <= 14:
            phase = "approaching_earnings"
            volatility_impact = "slight_increase"
            confidence_multiplier = 1.1
        else:
            phase = "normal"
            volatility_impact = "neutral"
            confidence_multiplier = 1.0
        
        return {
            "status": "success",
            "next_earnings_date": next_earnings.strftime("%Y-%m-%d"),
            "days_to_earnings": days_to_earnings,
            "phase": phase,
            "volatility_impact": volatility_impact,
            "confidence_multiplier": confidence_multiplier,
            "source": self.earnings_cache.get("next_earnings_date", {}).get("source", "unknown")
        }
    
    def get_earnings_trading_signal(self, direction: str) -> Dict:
        """Get earnings-adjusted trading signal"""
        
        analysis = self.get_earnings_proximity_analysis()
        
        if analysis["status"] != "success":
            return {
                "earnings_signal": "neutral",
                "confidence_multiplier": 1.0,
                "reasoning": "Earnings data unavailable"
            }
        
        phase = analysis["phase"]
        days_to_earnings = analysis["days_to_earnings"]
        confidence_multiplier = analysis["confidence_multiplier"]
        
        # Generate earnings-specific recommendations
        if phase == "pre_earnings":
            if direction in ["CALL", "PUT"]:
                signal = "STRONG_BUY"
                reasoning = f"Pre-earnings volatility expansion in {days_to_earnings} days - excellent for long options"
            else:
                signal = "NEUTRAL"
                reasoning = "Pre-earnings period - volatility increasing"
                
        elif phase == "post_earnings":
            if direction in ["CALL", "PUT"]:
                signal = "AVOID"
                confidence_multiplier = 0.5  # Strongly reduce confidence
                reasoning = f"Post-earnings IV crush expected - avoid long options"
            else:
                signal = "NEUTRAL"
                reasoning = "Post-earnings period - volatility declining"
                
        elif phase == "approaching_earnings":
            signal = "BUY"
            reasoning = f"Approaching earnings in {days_to_earnings} days - building volatility"
            
        else:
            signal = "NEUTRAL"
            reasoning = f"Normal period - {days_to_earnings} days to earnings"
        
        return {
            "earnings_signal": signal,
            "confidence_multiplier": confidence_multiplier,
            "reasoning": reasoning,
            "phase": phase,
            "days_to_earnings": days_to_earnings,
            "next_earnings": analysis["next_earnings_date"]
        }
    
    def generate_earnings_report(self) -> str:
        """Generate detailed earnings calendar report"""
        
        analysis = self.get_earnings_proximity_analysis()
        
        if analysis["status"] != "success":
            return "❌ **EARNINGS CALENDAR**: Data unavailable"
        
        signal = self.get_earnings_trading_signal("CALL")  # Use CALL as example
        
        report = f"""
📅 **RTX EARNINGS CALENDAR ANALYSIS**

📊 **Next Earnings**: {analysis['next_earnings_date']}
⏰ **Days Away**: {analysis['days_to_earnings']} days
🎯 **Current Phase**: {analysis['phase'].replace('_', ' ').title()}

📈 **Volatility Impact**: {analysis['volatility_impact'].replace('_', ' ').title()}
⚡ **Confidence Multiplier**: {analysis['confidence_multiplier']:.1%}
💡 **Trading Signal**: {signal['earnings_signal']}

🧠 **Strategy**: {signal['reasoning']}
📍 **Data Source**: {analysis['source'].title()}
"""
        return report.strip()

# Global instance
rtx_earnings_calendar = RTXEarningsCalendar()

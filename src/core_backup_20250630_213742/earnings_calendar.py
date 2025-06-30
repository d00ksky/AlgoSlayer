"""
RTX Earnings Calendar Integration
Automatically detects RTX earnings dates and adjusts trading strategy
"""

import os
import json
import requests
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from loguru import logger
import yfinance as yf

class RTXEarningsCalendar:
    """Manages RTX earnings calendar and strategy adjustments"""
    
    def __init__(self):
        self.symbol = "RTX"
        self.earnings_cache_file = "data/rtx_earnings_cache.json"
        self.cache_duration_days = 7  # Refresh earnings data weekly
        
        # Earnings strategy parameters
        self.pre_earnings_days = 2  # Start scaling positions 2 days before
        self.pre_earnings_multiplier = 1.5  # 50% larger positions
        self.pre_earnings_iv_threshold = 30  # Only if IV < 30th percentile
        
        # Post-earnings parameters  
        self.post_earnings_exit_hours = 4  # Exit within 4 hours after earnings
        self.iv_crush_threshold = 0.20  # Exit if IV drops >20%
        
        # Kelly integration
        self.earnings_kelly_boost = 0.05  # Add 5% to Kelly size during earnings
        
        logger.info("📅 RTX Earnings Calendar initialized")
    
    def get_next_earnings_date(self) -> Optional[date]:
        """Get the next RTX earnings date"""
        try:
            # Try to get from cache first
            cached_earnings = self._load_earnings_cache()
            if cached_earnings and cached_earnings.get('next_earnings'):
                next_earnings_str = cached_earnings['next_earnings']
                next_earnings = datetime.strptime(next_earnings_str, '%Y-%m-%d').date()
                
                # If earnings date is in the future and cache is recent, use it
                if next_earnings > date.today():
                    cache_age = (datetime.now() - datetime.fromisoformat(cached_earnings['last_updated'])).days
                    if cache_age < self.cache_duration_days:
                        logger.info(f"📅 Using cached earnings date: {next_earnings}")
                        return next_earnings
            
            # Fetch fresh earnings data
            logger.info("📅 Fetching fresh RTX earnings data...")
            return self._fetch_earnings_date()
            
        except Exception as e:
            logger.error(f"❌ Error getting earnings date: {e}")
            return None
    
    def _fetch_earnings_date(self) -> Optional[date]:
        """Fetch RTX earnings date from multiple sources"""
        
        # Method 1: Try yfinance calendar
        earnings_date = self._fetch_from_yfinance()
        if earnings_date:
            self._save_earnings_cache(earnings_date)
            return earnings_date
            
        # Method 2: Try estimated quarterly dates
        earnings_date = self._estimate_quarterly_earnings()
        if earnings_date:
            logger.warning("📅 Using estimated earnings date (no official date found)")
            self._save_earnings_cache(earnings_date, estimated=True)
            return earnings_date
            
        return None
    
    def _fetch_from_yfinance(self) -> Optional[date]:
        """Fetch earnings date from yfinance"""
        try:
            rtx = yf.Ticker("RTX")
            
            # Get earnings calendar
            calendar = rtx.calendar
            if calendar is not None and not calendar.empty:
                # Get the next earnings date
                earnings_dates = calendar.index.tolist()
                if earnings_dates:
                    next_earnings = earnings_dates[0].date()
                    logger.success(f"📅 Found RTX earnings date: {next_earnings}")
                    return next_earnings
                    
        except Exception as e:
            logger.warning(f"⚠️ yfinance earnings fetch failed: {e}")
            
        return None
    
    def _estimate_quarterly_earnings(self) -> Optional[date]:
        """Estimate next earnings based on typical quarterly schedule"""
        
        # RTX typically reports in late January, April, July, October
        # Around the 25th of each month
        today = date.today()
        year = today.year
        
        # Quarterly months
        earnings_months = [1, 4, 7, 10]  # Jan, Apr, Jul, Oct
        
        # Find next earnings month
        for month in earnings_months:
            # Estimate around the 25th of the month
            estimated_date = date(year, month, 25)
            
            # If this date is in the future, use it
            if estimated_date > today:
                logger.info(f"📅 Estimated RTX earnings: {estimated_date}")
                return estimated_date
                
        # If no dates this year, try next year
        estimated_date = date(year + 1, 1, 25)
        logger.info(f"📅 Estimated RTX earnings (next year): {estimated_date}")
        return estimated_date
    
    def _load_earnings_cache(self) -> Optional[Dict]:
        """Load earnings data from cache"""
        try:
            if os.path.exists(self.earnings_cache_file):
                with open(self.earnings_cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ Error loading earnings cache: {e}")
        return None
    
    def _save_earnings_cache(self, earnings_date: date, estimated: bool = False):
        """Save earnings data to cache"""
        try:
            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            
            cache_data = {
                'next_earnings': earnings_date.strftime('%Y-%m-%d'),
                'last_updated': datetime.now().isoformat(),
                'estimated': estimated,
                'symbol': self.symbol
            }
            
            with open(self.earnings_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.info(f"📅 Saved earnings cache: {earnings_date}")
            
        except Exception as e:
            logger.error(f"❌ Error saving earnings cache: {e}")
    
    def get_earnings_proximity(self) -> Tuple[int, str]:
        """Get days until earnings and proximity status"""
        
        next_earnings = self.get_next_earnings_date()
        if not next_earnings:
            return -1, "unknown"
            
        days_until = (next_earnings - date.today()).days
        
        if days_until < 0:
            return days_until, "post_earnings"
        elif days_until == 0:
            return 0, "earnings_day"
        elif days_until <= 1:
            return days_until, "pre_earnings_24h"
        elif days_until <= self.pre_earnings_days:
            return days_until, "pre_earnings"
        elif days_until <= 7:
            return days_until, "earnings_week"
        else:
            return days_until, "normal"
    
    def should_scale_positions(self) -> Tuple[bool, float, str]:
        """Determine if positions should be scaled for earnings"""
        
        days_until, proximity = self.get_earnings_proximity()
        
        if proximity in ["pre_earnings_24h", "pre_earnings"]:
            # Scale up positions before earnings
            multiplier = self.pre_earnings_multiplier
            reason = f"pre_earnings_{days_until}d"
            return True, multiplier, reason
            
        elif proximity == "earnings_day":
            # Be more aggressive on earnings day
            multiplier = self.pre_earnings_multiplier * 1.2  # Extra 20%
            reason = "earnings_day"
            return True, multiplier, reason
            
        elif proximity == "post_earnings":
            # Reduce positions after earnings (IV crush)
            multiplier = 0.5  # 50% smaller positions
            reason = "post_earnings_iv_crush"
            return True, multiplier, reason
            
        else:
            # Normal trading
            return False, 1.0, "normal_period"
    
    def get_earnings_kelly_adjustment(self) -> Tuple[float, str]:
        """Get Kelly position size adjustment for earnings"""
        
        days_until, proximity = self.get_earnings_proximity()
        
        if proximity in ["pre_earnings_24h", "pre_earnings"]:
            # Boost Kelly size for earnings opportunity
            boost = self.earnings_kelly_boost
            reason = f"earnings_opportunity_{days_until}d"
            return boost, reason
            
        elif proximity == "earnings_day":
            # Maximum boost on earnings day
            boost = self.earnings_kelly_boost * 1.5
            reason = "earnings_day_boost"
            return boost, reason
            
        elif proximity == "post_earnings":
            # Reduce Kelly after earnings
            boost = -self.earnings_kelly_boost
            reason = "post_earnings_reduction"
            return boost, reason
            
        else:
            return 0.0, "no_adjustment"
    
    def get_earnings_summary(self) -> str:
        """Get formatted earnings summary for Telegram"""
        
        next_earnings = self.get_next_earnings_date()
        days_until, proximity = self.get_earnings_proximity()
        should_scale, multiplier, scale_reason = self.should_scale_positions()
        kelly_boost, kelly_reason = self.get_earnings_kelly_adjustment()
        
        summary = "📅 **RTX Earnings Calendar**\n\n"
        
        if next_earnings:
            summary += f"🗓️ **Next Earnings**: {next_earnings.strftime('%B %d, %Y')}\n"
            summary += f"⏰ **Days Until**: {days_until} days\n"
            summary += f"📍 **Status**: {proximity.replace('_', ' ').title()}\n\n"
            
            # Position scaling
            if should_scale:
                if multiplier > 1.0:
                    emoji = "📈"
                    action = f"Scale UP {multiplier:.1f}x"
                elif multiplier < 1.0:
                    emoji = "📉"  
                    action = f"Scale DOWN {multiplier:.1f}x"
                else:
                    emoji = "➡️"
                    action = "Normal sizing"
                    
                summary += f"{emoji} **Position Scaling**: {action}\n"
                summary += f"📊 **Reason**: {scale_reason.replace('_', ' ').title()}\n\n"
            
            # Kelly adjustment
            if abs(kelly_boost) > 0.001:
                boost_emoji = "⬆️" if kelly_boost > 0 else "⬇️"
                summary += f"{boost_emoji} **Kelly Boost**: {kelly_boost:+.1%}\n"
                summary += f"🎯 **Kelly Reason**: {kelly_reason.replace('_', ' ').title()}\n\n"
            
            # Strategy recommendations
            if proximity in ["pre_earnings", "pre_earnings_24h"]:
                summary += "💡 **Strategy**: Target low IV options for earnings play\n"
                summary += "⚡ **Focus**: ATM/OTM calls for maximum leverage\n"
                summary += "⏰ **Exit Plan**: Quick exit 2-4h post-earnings\n"
                
            elif proximity == "earnings_day":
                summary += "🚨 **Strategy**: Maximum conviction trades only\n"
                summary += "⚡ **Focus**: High volume, tight spreads\n"
                summary += "⏰ **Exit Plan**: Exit within hours after announcement\n"
                
            elif proximity == "post_earnings":
                summary += "🛡️ **Strategy**: Reduced exposure due to IV crush\n"
                summary += "📉 **Focus**: Avoid new positions until IV normalizes\n"
                
        else:
            summary += "❓ **Next Earnings**: Date unknown\n"
            summary += "📊 **Status**: Normal trading period\n"
            summary += "💡 **Strategy**: Standard position sizing\n"
        
        summary += f"\n🔄 **Last Updated**: {datetime.now().strftime('%H:%M:%S')}"
        
        return summary
    
    def get_earnings_alert(self) -> Optional[str]:
        """Get earnings alert if action is needed"""
        
        days_until, proximity = self.get_earnings_proximity()
        
        alerts = {
            "pre_earnings": f"🚨 RTX earnings in {days_until} days! Consider scaling positions UP",
            "pre_earnings_24h": f"🔥 RTX earnings TOMORROW! Scale positions for volatility",
            "earnings_day": "⚡ RTX earnings TODAY! Maximum conviction trades only",
            "post_earnings": "📉 RTX earnings passed - watch for IV crush, consider exits"
        }
        
        return alerts.get(proximity)

# Global instance
rtx_earnings = RTXEarningsCalendar()

if __name__ == "__main__":
    # Test the earnings calendar
    logger.info("🧪 Testing RTX Earnings Calendar")
    
    earnings = RTXEarningsCalendar()
    
    print("📅 RTX Earnings Calendar Test")
    print("="*50)
    
    # Test earnings date detection
    next_earnings = earnings.get_next_earnings_date()
    print(f"Next Earnings: {next_earnings}")
    
    # Test proximity
    days_until, proximity = earnings.get_earnings_proximity()
    print(f"Days Until: {days_until}, Status: {proximity}")
    
    # Test position scaling
    should_scale, multiplier, reason = earnings.should_scale_positions()
    print(f"Scale Positions: {should_scale}, Multiplier: {multiplier:.1f}x, Reason: {reason}")
    
    # Test Kelly adjustment
    kelly_boost, kelly_reason = earnings.get_earnings_kelly_adjustment()
    print(f"Kelly Boost: {kelly_boost:+.1%}, Reason: {kelly_reason}")
    
    # Test summary
    print("\n" + "="*50)
    print("Earnings Summary:")
    print(earnings.get_earnings_summary())
    
    # Test alert
    alert = earnings.get_earnings_alert()
    if alert:
        print(f"\nAlert: {alert}")
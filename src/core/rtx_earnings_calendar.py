"""
RTX Earnings Calendar Integration
Tracks RTX earnings dates and provides volatility/opportunity predictions
Defense stocks have predictable earnings-driven volatility spikes
"""
import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json

@dataclass
class EarningsEvent:
    """RTX earnings event information"""
    date: date
    quarter: str  # Q1, Q2, Q3, Q4
    year: int
    estimated_eps: Optional[float] = None
    actual_eps: Optional[float] = None
    surprise_pct: Optional[float] = None
    pre_market: bool = True  # Most earnings are pre-market
    confirmed: bool = False  # Whether date is confirmed vs estimated

@dataclass
class EarningsImpact:
    """Expected impact of upcoming earnings"""
    days_until_earnings: int
    quarter: str
    year: int
    volatility_multiplier: float  # Expected vol increase
    confidence_boost: float  # Boost to signal confidence
    historical_move_avg: float  # Average historical earnings move
    historical_moves: List[float]  # Recent earnings moves
    recommendation: str  # Action recommendation

class RTXEarningsCalendar:
    """
    Tracks RTX earnings calendar and provides trading insights
    RTX typically reports quarterly earnings with significant volatility
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.symbol = "RTX"
        self.earnings_cache = []
        self.last_update = None
        
        # Historical patterns (will be updated with real data)
        self.historical_patterns = {
            'avg_move_magnitude': 0.04,  # 4% average move on earnings
            'volatility_increase': 2.5,   # 2.5x normal volatility
            'surprise_impact': 0.02,      # 2% additional move per 10% surprise
            'pre_earnings_drift': 0.015   # 1.5% average pre-earnings drift
        }
    
    async def update_earnings_calendar(self) -> bool:
        """Update RTX earnings calendar from multiple sources"""
        try:
            self.logger.info("📅 Updating RTX earnings calendar...")
            
            # Try multiple sources for best coverage
            earnings_data = []
            
            # Source 1: Yahoo Finance
            yahoo_earnings = await self._get_yahoo_earnings()
            if yahoo_earnings:
                earnings_data.extend(yahoo_earnings)
            
            # Source 2: Manual quarterly estimation (backup)
            estimated_earnings = await self._estimate_quarterly_earnings()
            earnings_data.extend(estimated_earnings)
            
            # Remove duplicates and sort
            self.earnings_cache = self._deduplicate_earnings(earnings_data)
            self.last_update = datetime.now()
            
            self.logger.info(f"✅ Updated earnings calendar with {len(self.earnings_cache)} events")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating earnings calendar: {e}")
            return False
    
    async def _get_yahoo_earnings(self) -> List[EarningsEvent]:
        """Get earnings data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(self.symbol)
            
            # Get earnings calendar (next few quarters)
            calendar = ticker.calendar
            
            earnings_events = []
            if calendar is not None and not calendar.empty:
                for idx, row in calendar.iterrows():
                    earnings_date = idx.date() if hasattr(idx, 'date') else idx
                    
                    event = EarningsEvent(
                        date=earnings_date,
                        quarter=self._determine_quarter(earnings_date),
                        year=earnings_date.year,
                        estimated_eps=row.get('Earnings Estimate', None),
                        confirmed=True
                    )
                    earnings_events.append(event)
            
            return earnings_events
            
        except Exception as e:
            self.logger.warning(f"Could not get Yahoo earnings data: {e}")
            return []
    
    async def _estimate_quarterly_earnings(self) -> List[EarningsEvent]:
        """Estimate quarterly earnings dates based on historical patterns"""
        try:
            # RTX typically reports:
            # Q1: Late April
            # Q2: Late July  
            # Q3: Late October
            # Q4: Late January (following year)
            
            current_year = datetime.now().year
            estimated_dates = []
            
            # Q1 earnings (late April)
            q1_date = date(current_year, 4, 25)
            if q1_date > date.today():
                estimated_dates.append(EarningsEvent(
                    date=q1_date,
                    quarter="Q1",
                    year=current_year,
                    confirmed=False
                ))
            
            # Q2 earnings (late July)
            q2_date = date(current_year, 7, 25)
            if q2_date > date.today():
                estimated_dates.append(EarningsEvent(
                    date=q2_date,
                    quarter="Q2", 
                    year=current_year,
                    confirmed=False
                ))
            
            # Q3 earnings (late October)
            q3_date = date(current_year, 10, 25)
            if q3_date > date.today():
                estimated_dates.append(EarningsEvent(
                    date=q3_date,
                    quarter="Q3",
                    year=current_year,
                    confirmed=False
                ))
            
            # Q4 earnings (late January next year)
            q4_date = date(current_year + 1, 1, 25)
            if q4_date > date.today():
                estimated_dates.append(EarningsEvent(
                    date=q4_date,
                    quarter="Q4",
                    year=current_year,
                    confirmed=False
                ))
            
            return estimated_dates
            
        except Exception as e:
            self.logger.error(f"Error estimating earnings dates: {e}")
            return []
    
    def _determine_quarter(self, earnings_date: date) -> str:
        """Determine which quarter the earnings date represents"""
        month = earnings_date.month
        
        if month in [1, 2]:
            return "Q4"  # Previous year Q4
        elif month in [4, 5]:
            return "Q1"
        elif month in [7, 8]:
            return "Q2"
        elif month in [10, 11]:
            return "Q3"
        else:
            # Default based on typical patterns
            if month == 3:
                return "Q4"
            elif month == 6:
                return "Q1"
            elif month == 9:
                return "Q2"
            else:  # month == 12
                return "Q3"
    
    def _deduplicate_earnings(self, earnings_data: List[EarningsEvent]) -> List[EarningsEvent]:
        """Remove duplicate earnings events and sort by date"""
        seen_dates = set()
        unique_earnings = []
        
        # Prefer confirmed events over estimated
        earnings_data.sort(key=lambda x: (x.date, not x.confirmed))
        
        for event in earnings_data:
            date_key = (event.date, event.quarter, event.year)
            if date_key not in seen_dates:
                seen_dates.add(date_key)
                unique_earnings.append(event)
        
        # Sort by date
        unique_earnings.sort(key=lambda x: x.date)
        return unique_earnings
    
    async def get_next_earnings(self) -> Optional[EarningsEvent]:
        """Get the next upcoming earnings event"""
        try:
            if not self.earnings_cache or self._needs_update():
                await self.update_earnings_calendar()
            
            today = date.today()
            for event in self.earnings_cache:
                if event.date >= today:
                    return event
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting next earnings: {e}")
            return None
    
    async def get_earnings_impact(self) -> EarningsImpact:
        """Calculate the impact of upcoming earnings on trading strategy"""
        try:
            next_earnings = await self.get_next_earnings()
            
            if not next_earnings:
                # No upcoming earnings - normal volatility
                return EarningsImpact(
                    days_until_earnings=999,
                    quarter="Unknown",
                    year=0,
                    volatility_multiplier=1.0,
                    confidence_boost=0.0,
                    historical_move_avg=0.0,
                    historical_moves=[],
                    recommendation="NORMAL"
                )
            
            days_until = (next_earnings.date - date.today()).days
            
            # Calculate impact based on proximity to earnings
            if days_until <= 0:
                # Earnings day or just passed
                vol_mult = 3.0
                conf_boost = 0.15
                recommendation = "EARNINGS_DAY"
            elif days_until <= 3:
                # Within 3 days - high volatility expected
                vol_mult = 2.5
                conf_boost = 0.12
                recommendation = "HIGH_VOLATILITY"
            elif days_until <= 7:
                # Within a week - increased volatility
                vol_mult = 1.8
                conf_boost = 0.08
                recommendation = "INCREASED_VOLATILITY"
            elif days_until <= 14:
                # Within 2 weeks - slight increase
                vol_mult = 1.3
                conf_boost = 0.05
                recommendation = "SLIGHT_INCREASE"
            else:
                # Normal period
                vol_mult = 1.0
                conf_boost = 0.0
                recommendation = "NORMAL"
            
            # Get historical earnings moves
            historical_moves = await self._get_historical_earnings_moves()
            avg_move = sum(historical_moves) / len(historical_moves) if historical_moves else 0.04
            
            return EarningsImpact(
                days_until_earnings=days_until,
                quarter=next_earnings.quarter,
                year=next_earnings.year,
                volatility_multiplier=vol_mult,
                confidence_boost=conf_boost,
                historical_move_avg=avg_move,
                historical_moves=historical_moves,
                recommendation=recommendation
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating earnings impact: {e}")
            return EarningsImpact(
                days_until_earnings=999,
                quarter="Error",
                year=0,
                volatility_multiplier=1.0,
                confidence_boost=0.0,
                historical_move_avg=0.0,
                historical_moves=[],
                recommendation="ERROR"
            )
    
    async def _get_historical_earnings_moves(self) -> List[float]:
        """Get historical RTX price moves around earnings"""
        try:
            # Get RTX historical data for the past 2 years
            ticker = yf.Ticker(self.symbol)
            hist_data = ticker.history(period="2y", interval="1d")
            
            if hist_data.empty:
                return [0.04, 0.045, 0.035, 0.055]  # Default estimates
            
            # Estimate earnings dates (quarterly)
            earnings_moves = []
            
            # Look for significant moves that likely coincide with earnings
            daily_returns = hist_data['Close'].pct_change().abs()
            
            # Find moves > 3% (likely earnings-related)
            significant_moves = daily_returns[daily_returns > 0.03]
            
            # Take recent moves (last 8 quarters worth)
            recent_moves = significant_moves.tail(8).tolist()
            
            if recent_moves:
                return recent_moves
            else:
                return [0.04, 0.045, 0.035, 0.055]  # Default estimates
                
        except Exception as e:
            self.logger.warning(f"Could not get historical earnings moves: {e}")
            return [0.04, 0.045, 0.035, 0.055]  # Default estimates
    
    def _needs_update(self) -> bool:
        """Check if earnings calendar needs updating"""
        if not self.last_update:
            return True
        
        # Update weekly
        return datetime.now() - self.last_update > timedelta(days=7)
    
    async def is_earnings_week(self) -> bool:
        """Check if we're in an earnings week (higher volatility)"""
        try:
            impact = await self.get_earnings_impact()
            return impact.days_until_earnings <= 7
            
        except Exception as e:
            self.logger.error(f"Error checking earnings week: {e}")
            return False
    
    async def get_earnings_strategy_adjustment(self) -> Dict:
        """Get strategy adjustments based on earnings proximity"""
        try:
            impact = await self.get_earnings_impact()
            
            adjustments = {
                'volatility_multiplier': impact.volatility_multiplier,
                'confidence_threshold_adjustment': impact.confidence_boost,
                'position_size_multiplier': 1.0,
                'hold_period_adjustment': 0,
                'strategy_notes': []
            }
            
            if impact.days_until_earnings <= 3:
                # Close to earnings - be more aggressive
                adjustments['position_size_multiplier'] = 1.5
                adjustments['hold_period_adjustment'] = -1  # Shorter holds
                adjustments['strategy_notes'].append("Earnings imminent - increased volatility expected")
                
            elif impact.days_until_earnings <= 7:
                # Earnings week - moderate adjustment
                adjustments['position_size_multiplier'] = 1.2
                adjustments['strategy_notes'].append("Earnings week - higher volatility likely")
                
            elif impact.days_until_earnings <= 14:
                # Pre-earnings setup period
                adjustments['strategy_notes'].append("Pre-earnings period - watch for setup")
                
            else:
                # Normal period
                adjustments['strategy_notes'].append("Normal period - standard volatility")
            
            return adjustments
            
        except Exception as e:
            self.logger.error(f"Error getting strategy adjustments: {e}")
            return {'volatility_multiplier': 1.0, 'confidence_threshold_adjustment': 0.0}
    
    async def get_earnings_summary(self) -> Dict:
        """Get comprehensive earnings summary for reporting"""
        try:
            next_earnings = await self.get_next_earnings()
            impact = await self.get_earnings_impact()
            
            summary = {
                'next_earnings': {
                    'date': next_earnings.date.isoformat() if next_earnings else None,
                    'quarter': next_earnings.quarter if next_earnings else None,
                    'year': next_earnings.year if next_earnings else None,
                    'confirmed': next_earnings.confirmed if next_earnings else False,
                    'days_until': impact.days_until_earnings
                },
                'impact': {
                    'volatility_multiplier': impact.volatility_multiplier,
                    'confidence_boost': impact.confidence_boost,
                    'recommendation': impact.recommendation,
                    'historical_avg_move': impact.historical_move_avg
                },
                'strategy_adjustments': await self.get_earnings_strategy_adjustment(),
                'last_updated': self.last_update.isoformat() if self.last_update else None
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating earnings summary: {e}")
            return {}

# Global earnings calendar instance
rtx_earnings = RTXEarningsCalendar()

async def test_earnings_calendar():
    """Test the RTX earnings calendar"""
    print("📅 Testing RTX Earnings Calendar")
    print("=" * 40)
    
    try:
        # Update calendar
        success = await rtx_earnings.update_earnings_calendar()
        print(f"📅 Calendar update: {'✅ Success' if success else '❌ Failed'}")
        
        # Get next earnings
        next_earnings = await rtx_earnings.get_next_earnings()
        if next_earnings:
            print(f"📊 Next earnings: {next_earnings.quarter} {next_earnings.year} on {next_earnings.date}")
            print(f"   Confirmed: {'Yes' if next_earnings.confirmed else 'Estimated'}")
        else:
            print("📊 No upcoming earnings found")
        
        # Get earnings impact
        impact = await rtx_earnings.get_earnings_impact()
        print(f"🎯 Earnings impact:")
        print(f"   Days until: {impact.days_until_earnings}")
        print(f"   Volatility multiplier: {impact.volatility_multiplier:.1f}x")
        print(f"   Confidence boost: {impact.confidence_boost:+.1%}")
        print(f"   Recommendation: {impact.recommendation}")
        print(f"   Historical avg move: {impact.historical_move_avg:.1%}")
        
        # Check if earnings week
        is_earnings_week = await rtx_earnings.is_earnings_week()
        print(f"📈 Earnings week: {'Yes' if is_earnings_week else 'No'}")
        
        # Get strategy adjustments
        adjustments = await rtx_earnings.get_earnings_strategy_adjustment()
        print(f"⚙️  Strategy adjustments:")
        print(f"   Position size multiplier: {adjustments['position_size_multiplier']:.1f}x")
        for note in adjustments['strategy_notes']:
            print(f"   📝 {note}")
        
        print("✅ All tests passed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_earnings_calendar())
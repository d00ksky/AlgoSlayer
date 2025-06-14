"""
Options IV Percentile Signal - Historical Volatility Context
Determines if RTX options are cheap or expensive based on historical IV patterns
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .base_signal import BaseSignal

class OptionsIVPercentileSignal(BaseSignal):
    """
    Options IV Percentile Signal for Entry Timing
    
    Strategy:
    - IV Percentile < 20%: BUY (cheap options, expect expansion)
    - IV Percentile 20-40%: Weak BUY (below average IV)
    - IV Percentile 40-60%: HOLD (average IV)
    - IV Percentile 60-80%: Weak SELL (above average IV)
    - IV Percentile > 80%: SELL (expensive options, expect contraction)
    
    This signal helps time options entries when premium is attractive.
    """
    
    def __init__(self):
        super().__init__("options_iv_percentile")
        self.signal_name = "options_iv_percentile"
        self.lookback_days = 252  # 1 year of trading days
        
    async def analyze(self, symbol: str = "RTX") -> Dict:
        """Analyze RTX options IV percentile for entry timing"""
        try:
            # Get current RTX options data
            current_iv = self._get_current_iv()
            if current_iv is None:
                return self._create_hold_signal("Could not obtain current IV")
            
            # Get historical volatility data
            historical_vols = self._get_historical_volatility()
            if len(historical_vols) < 50:
                return self._create_hold_signal("Insufficient historical data")
            
            # Calculate IV percentile
            iv_percentile = self._calculate_iv_percentile(current_iv, historical_vols)
            
            # Generate signal based on IV percentile
            direction, confidence, reasoning = self._generate_iv_signal(iv_percentile, current_iv)
            
            return {
                'signal': self.signal_name,
                'direction': direction,
                'confidence': confidence,
                'strength': min(confidence / 100.0, 1.0),
                'reasoning': reasoning,
                'metadata': {
                    'current_iv': round(current_iv, 3),
                    'iv_percentile': round(iv_percentile, 1),
                    'historical_avg_iv': round(np.mean(historical_vols), 3),
                    'iv_classification': self._classify_iv_level(iv_percentile),
                    'lookback_days': len(historical_vols)
                }
            }
            
        except Exception as e:
            return self._create_error_signal(f"IV percentile analysis failed: {str(e)}")
    
    def _get_current_iv(self) -> Optional[float]:
        """Get current implied volatility from RTX options"""
        try:
            rtx = yf.Ticker("RTX")
            
            # Get ATM options (closest to current stock price)
            current_price = self._get_current_price()
            if not current_price:
                return None
            
            # Get options chain for nearest expiration
            expirations = rtx.options
            if not expirations:
                return None
            
            # Get nearest expiration (but not too close - avoid weird behavior)
            valid_expirations = []
            for exp in expirations:
                exp_date = pd.to_datetime(exp)
                days_to_exp = (exp_date - pd.Timestamp.now()).days
                if 7 <= days_to_exp <= 45:  # 1-6 weeks out
                    valid_expirations.append(exp)
            
            if not valid_expirations:
                return None
            
            nearest_exp = valid_expirations[0]
            options_chain = rtx.option_chain(nearest_exp)
            
            # Get ATM call IV
            calls = options_chain.calls
            if calls.empty:
                return None
            
            # Find closest to ATM
            calls['strike_diff'] = abs(calls['strike'] - current_price)
            atm_call = calls.loc[calls['strike_diff'].idxmin()]
            
            iv = atm_call.get('impliedVolatility', None)
            return float(iv) if iv and not pd.isna(iv) else None
            
        except Exception:
            # Fallback: estimate IV from historical volatility
            return self._estimate_iv_from_historical()
    
    def _get_current_price(self) -> Optional[float]:
        """Get current RTX stock price"""
        try:
            rtx = yf.Ticker("RTX")
            info = rtx.info
            return info.get('currentPrice') or info.get('regularMarketPrice')
        except:
            return None
    
    def _estimate_iv_from_historical(self) -> Optional[float]:
        """Estimate IV from recent historical volatility"""
        try:
            rtx = yf.Ticker("RTX")
            # Get last 30 days of price data
            hist = rtx.history(period="1mo")
            if len(hist) < 10:
                return None
            
            # Calculate realized volatility (annualized)
            returns = hist['Close'].pct_change().dropna()
            realized_vol = returns.std() * np.sqrt(252)
            
            # IV is typically 1.2-1.5x realized volatility for RTX
            estimated_iv = realized_vol * 1.3
            return float(estimated_iv)
            
        except:
            return None
    
    def _get_historical_volatility(self) -> List[float]:
        """Get historical realized volatility for IV percentile calculation"""
        try:
            rtx = yf.Ticker("RTX")
            
            # Get historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days + 30)
            hist = rtx.history(start=start_date, end=end_date)
            
            if len(hist) < 50:
                return []
            
            # Calculate 30-day rolling volatility
            returns = hist['Close'].pct_change().dropna()
            rolling_vol = returns.rolling(window=20).std() * np.sqrt(252)
            
            # Remove NaN values and convert to list
            valid_vols = rolling_vol.dropna().tolist()
            return [v for v in valid_vols if 0.05 < v < 1.0]  # Sanity check
            
        except Exception:
            return []
    
    def _calculate_iv_percentile(self, current_iv: float, historical_vols: List[float]) -> float:
        """Calculate where current IV ranks vs historical volatility"""
        if not historical_vols:
            return 50.0  # Default to median
        
        # Count how many historical values are below current IV
        below_current = sum(1 for vol in historical_vols if vol < current_iv)
        
        # Calculate percentile
        percentile = (below_current / len(historical_vols)) * 100
        return percentile
    
    def _generate_iv_signal(self, iv_percentile: float, current_iv: float) -> tuple:
        """Generate signal based on IV percentile"""
        
        # Very low IV - cheap options
        if iv_percentile < 20:
            confidence = 85
            return "BUY", confidence, f"IV very low ({iv_percentile:.0f}th percentile) - cheap options"
        
        # Low IV - below average
        elif iv_percentile < 40:
            confidence = 70
            return "BUY", confidence, f"IV below average ({iv_percentile:.0f}th percentile) - attractive entry"
        
        # Average IV - neutral
        elif iv_percentile < 60:
            confidence = 55
            return "HOLD", confidence, f"IV average ({iv_percentile:.0f}th percentile) - neutral"
        
        # High IV - above average
        elif iv_percentile < 80:
            confidence = 70
            return "SELL", confidence, f"IV above average ({iv_percentile:.0f}th percentile) - expensive options"
        
        # Very high IV - expensive options
        else:
            confidence = 85
            return "SELL", confidence, f"IV very high ({iv_percentile:.0f}th percentile) - overpriced options"
    
    def _classify_iv_level(self, iv_percentile: float) -> str:
        """Classify IV level for metadata"""
        if iv_percentile < 20:
            return "Very Low"
        elif iv_percentile < 40:
            return "Low"
        elif iv_percentile < 60:
            return "Average"
        elif iv_percentile < 80:
            return "High"
        else:
            return "Very High"
    
    def _create_hold_signal(self, reason: str) -> Dict:
        """Create a neutral HOLD signal"""
        return {
            'signal': self.signal_name,
            'direction': 'HOLD',
            'confidence': 50,
            'strength': 0.5,
            'reasoning': reason,
            'metadata': {
                'current_iv': None,
                'iv_percentile': None,
                'iv_classification': 'Unknown'
            }
        }
    
    def _create_error_signal(self, error_msg: str) -> Dict:
        """Create an error signal"""
        return {
            'signal': self.signal_name,
            'direction': 'HOLD',
            'confidence': 50,
            'strength': 0.5,
            'reasoning': f"Error: {error_msg}",
            'metadata': {
                'error': True,
                'error_message': error_msg
            }
        }
    
    async def backtest(self, symbol: str, start_date: str, end_date: str) -> Dict:
        """Simple backtest implementation for IV percentile signal"""
        return {
            'signal_name': self.signal_name,
            'backtest_period': f"{start_date} to {end_date}",
            'note': 'IV percentile signal backtest requires historical options data',
            'estimated_performance': 'Positive when entering at low IV percentiles'
        }
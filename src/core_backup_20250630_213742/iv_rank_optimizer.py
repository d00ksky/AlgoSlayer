"""
Real-time IV Rank Optimization
Analyzes RTX implied volatility patterns for optimal options timing
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import yfinance as yf
import numpy as np

class IVRankOptimizer:
    """Optimizes options entry timing based on IV rank analysis"""
    
    def __init__(self):
        self.symbol = "RTX"
        self.iv_history_days = 252  # 1 year of IV data
        self.iv_cache = {}
        self.cache_expiry = 300  # 5 minutes cache
        
        # IV timing preferences
        self.optimal_iv_ranges = {
            "CALL": {"min": 15, "max": 35},   # Buy calls when IV is low-medium
            "PUT": {"min": 20, "max": 40}     # Buy puts when IV is medium
        }
        
    def get_current_iv_rank(self) -> Dict:
        """Calculate current IV rank for RTX"""
        
        # Check cache first
        cache_key = f"{self.symbol}_iv_rank"
        if (cache_key in self.iv_cache and 
            (datetime.now() - self.iv_cache[cache_key]["timestamp"]).seconds < self.cache_expiry):
            return self.iv_cache[cache_key]["data"]
        
        try:
            # Get RTX options data
            ticker = yf.Ticker(self.symbol)
            
            # Get near-term expiration options
            expirations = ticker.options
            if not expirations:
                return {"iv_rank": 50, "current_iv": 25, "status": "unknown"}
            
            # Use first available expiration
            exp_date = expirations[0]
            options_chain = ticker.option_chain(exp_date)
            
            # Calculate average IV from ATM options
            current_price = ticker.history(period="1d")["Close"].iloc[-1]
            
            # Get ATM call and put IVs
            calls = options_chain.calls
            puts = options_chain.puts
            
            # Find ATM strikes
            atm_call = calls.iloc[(calls['strike'] - current_price).abs().argsort()[:1]]
            atm_put = puts.iloc[(puts['strike'] - current_price).abs().argsort()[:1]]
            
            current_iv = 0
            if not atm_call.empty and not atm_put.empty:
                call_iv = atm_call['impliedVolatility'].iloc[0] * 100
                put_iv = atm_put['impliedVolatility'].iloc[0] * 100
                current_iv = (call_iv + put_iv) / 2
            
            # Get historical IV data (approximate from price volatility)
            historical_data = ticker.history(period="1y")
            returns = historical_data['Close'].pct_change().dropna()
            historical_vol = returns.rolling(window=21).std() * np.sqrt(252) * 100
            
            # Calculate IV rank (current IV vs historical range)
            if len(historical_vol) > 50:
                min_iv = historical_vol.min()
                max_iv = historical_vol.max()
                iv_rank = ((current_iv - min_iv) / (max_iv - min_iv)) * 100
            else:
                iv_rank = 50  # Default middle rank
            
            result = {
                "iv_rank": round(iv_rank, 1),
                "current_iv": round(current_iv, 1),
                "iv_percentile": round(iv_rank, 1),
                "status": "success",
                "expiration": exp_date,
                "timestamp": datetime.now()
            }
            
            # Cache result
            self.iv_cache[cache_key] = {
                "data": result,
                "timestamp": datetime.now()
            }
            
            return result
            
        except Exception as e:
            # Fallback to reasonable defaults
            return {
                "iv_rank": 50,
                "current_iv": 25,
                "iv_percentile": 50,
                "status": f"error: {e}",
                "timestamp": datetime.now()
            }
    
    def calculate_iv_timing_score(self, direction: str, iv_data: Dict) -> float:
        """Calculate timing score based on IV rank (0-1 scale)"""
        
        iv_rank = iv_data.get("iv_rank", 50)
        current_iv = iv_data.get("current_iv", 25)
        
        if direction == "CALL":
            # Prefer lower IV for buying calls
            if iv_rank < 25:  # Low IV - excellent timing
                score = 1.0
            elif iv_rank < 40:  # Medium-low IV - good timing
                score = 0.8
            elif iv_rank < 60:  # Medium IV - acceptable timing
                score = 0.6
            else:  # High IV - poor timing for calls
                score = 0.3
                
        elif direction == "PUT":
            # Slightly prefer higher IV for puts (more time premium)
            if iv_rank > 60:  # High IV - good for puts
                score = 0.9
            elif iv_rank > 40:  # Medium-high IV - good timing
                score = 0.8
            elif iv_rank > 25:  # Medium IV - acceptable
                score = 0.7
            else:  # Low IV - still ok for puts
                score = 0.6
        else:
            score = 0.5  # Neutral for HOLD
            
        return score
    
    def get_iv_optimization_signal(self, direction: str) -> Dict:
        """Get IV-based timing signal for options trading"""
        
        iv_data = self.get_current_iv_rank()
        timing_score = self.calculate_iv_timing_score(direction, iv_data)
        
        # Determine timing recommendation
        if timing_score >= 0.8:
            timing = "EXCELLENT"
            recommendation = "Strong Buy Signal"
        elif timing_score >= 0.6:
            timing = "GOOD"
            recommendation = "Buy Signal"
        elif timing_score >= 0.4:
            timing = "FAIR"
            recommendation = "Caution - Consider Waiting"
        else:
            timing = "POOR"
            recommendation = "Wait for Better IV"
        
        return {
            "iv_rank": iv_data.get("iv_rank"),
            "current_iv": iv_data.get("current_iv"),
            "timing_score": timing_score,
            "timing_rating": timing,
            "recommendation": recommendation,
            "direction": direction,
            "confidence_multiplier": timing_score,  # Use as confidence multiplier
            "reasoning": f"IV Rank {iv_data.get('iv_rank', 0):.1f}% - {timing} timing for {direction}"
        }
    
    def generate_iv_report(self, direction: str) -> str:
        """Generate detailed IV timing report"""
        
        signal = self.get_iv_optimization_signal(direction)
        
        report = f"""
📊 **IV RANK OPTIMIZATION ANALYSIS**

🎯 **Current IV Rank**: {signal['iv_rank']:.1f}% (vs 1-year range)
📈 **Current IV**: {signal['current_iv']:.1f}%
⏰ **Timing Rating**: {signal['timing_rating']} ({signal['timing_score']:.1%})
💡 **Recommendation**: {signal['recommendation']}

🧠 **Strategy**: {signal['reasoning']}
📊 **Confidence Boost**: {signal['confidence_multiplier']:.1%}
"""
        return report.strip()

# Global instance
iv_rank_optimizer = IVRankOptimizer()

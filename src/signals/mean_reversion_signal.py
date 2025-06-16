"""
Mean Reversion Analysis Signal
Identify mean reversion opportunities in RTX price action
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
from loguru import logger

from config.trading_config import config

class MeanReversionSignal:
    """Analyze mean reversion patterns for RTX"""
    
    def __init__(self):
        self.signal_name = "mean_reversion"
        self.weight = config.SIGNAL_WEIGHTS.get(self.signal_name, 0.10)
        self.last_analysis = None
        
    async def analyze(self, symbol: str = "RTX") -> Dict:
        """Analyze mean reversion patterns for trading signals"""
        
        try:
            # Get price data
            data = await self._get_price_data(symbol)
            
            if data.empty:
                return self._create_neutral_signal("No price data available")
            
            # Calculate mean reversion indicators
            reversion_data = self._calculate_mean_reversion_indicators(data)
            
            # Analyze reversion patterns
            pattern_analysis = self._analyze_reversion_patterns(reversion_data)
            
            # Generate signal
            signal = self._generate_signal(pattern_analysis)
            
            self.last_analysis = signal
            return signal
            
        except Exception as e:
            logger.error(f"📊 Mean reversion error: {e}")
            return self._create_neutral_signal(f"Analysis error: {str(e)}")
    
    async def _get_price_data(self, symbol: str, period: str = "60d") -> pd.DataFrame:
        """Get price data for mean reversion analysis"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            logger.info(f"📊 Loaded {len(data)} days for mean reversion analysis")
            return data
            
        except Exception as e:
            logger.error(f"📊 Price data error: {e}")
            return pd.DataFrame()
    
    def _calculate_mean_reversion_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate mean reversion indicators"""
        
        # Moving averages for mean calculation
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['EMA_20'] = data['Close'].ewm(span=20).mean()
        
        # Standard deviation bands
        data['StdDev_20'] = data['Close'].rolling(window=20).std()
        data['Upper_Band'] = data['SMA_20'] + (2 * data['StdDev_20'])
        data['Lower_Band'] = data['SMA_20'] - (2 * data['StdDev_20'])
        
        # Price position relative to mean
        data['Price_Distance_SMA20'] = (data['Close'] - data['SMA_20']) / data['SMA_20'] * 100
        data['Price_Distance_SMA50'] = (data['Close'] - data['SMA_50']) / data['SMA_50'] * 100
        
        # Z-Score (standardized distance from mean)
        data['Z_Score_20'] = (data['Close'] - data['SMA_20']) / data['StdDev_20']
        
        # Bollinger Band position
        data['BB_Position'] = (data['Close'] - data['Lower_Band']) / (data['Upper_Band'] - data['Lower_Band'])
        
        # Mean reversion momentum
        data['Returns'] = data['Close'].pct_change()
        data['Mean_Reversion_Momentum'] = data['Returns'].rolling(window=5).sum()
        
        # RSI for overbought/oversold
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # Williams %R
        high_14 = data['High'].rolling(window=14).max()
        low_14 = data['Low'].rolling(window=14).min()
        data['Williams_R'] = -100 * (high_14 - data['Close']) / (high_14 - low_14)
        
        # Stochastic Oscillator
        data['Stoch_K'] = 100 * (data['Close'] - low_14) / (high_14 - low_14)
        
        # Price reversion velocity (how fast price moves back to mean)
        data['Reversion_Velocity'] = data['Price_Distance_SMA20'].diff()
        
        # Get current values
        latest = data.iloc[-1]
        
        return {
            'current_price': latest['Close'],
            'sma_20': latest['SMA_20'],
            'sma_50': latest['SMA_50'],
            'ema_20': latest['EMA_20'],
            'upper_band': latest['Upper_Band'],
            'lower_band': latest['Lower_Band'],
            'price_distance_sma20': latest['Price_Distance_SMA20'],
            'price_distance_sma50': latest['Price_Distance_SMA50'],
            'z_score': latest['Z_Score_20'],
            'bb_position': latest['BB_Position'],
            'rsi': latest['RSI'],
            'williams_r': latest['Williams_R'],
            'stoch_k': latest['Stoch_K'],
            'reversion_velocity': latest['Reversion_Velocity'],
            'mean_reversion_momentum': latest['Mean_Reversion_Momentum'],
            'data': data  # Keep for pattern analysis
        }
    
    def _analyze_reversion_patterns(self, reversion_data: Dict) -> Dict:
        """Analyze mean reversion patterns"""
        
        analysis = {
            'reversion_signal': 'neutral',
            'extremeness_level': 'normal',
            'reversion_probability': 0.5,
            'time_horizon': 'medium',
            'patterns': []
        }
        
        # Current indicators
        z_score = reversion_data.get('z_score', 0)
        bb_position = reversion_data.get('bb_position', 0.5)
        rsi = reversion_data.get('rsi', 50)
        williams_r = reversion_data.get('williams_r', -50)
        price_distance_sma20 = reversion_data.get('price_distance_sma20', 0)
        reversion_velocity = reversion_data.get('reversion_velocity', 0)
        
        # Extreme price levels (strong reversion candidates)
        if abs(z_score) > 2.0:
            analysis['extremeness_level'] = 'extreme'
            analysis['patterns'].append(f"Extreme Z-score: {z_score:.2f}")
            analysis['reversion_probability'] += 0.3
        elif abs(z_score) > 1.5:
            analysis['extremeness_level'] = 'high'
            analysis['patterns'].append(f"High Z-score: {z_score:.2f}")
            analysis['reversion_probability'] += 0.2
        
        # Bollinger Band analysis
        if bb_position > 0.95:  # Near upper band
            analysis['patterns'].append("Price near upper Bollinger Band")
            analysis['reversion_probability'] += 0.25
            if z_score > 0:
                analysis['reversion_signal'] = 'bearish_reversion'
        elif bb_position < 0.05:  # Near lower band
            analysis['patterns'].append("Price near lower Bollinger Band")
            analysis['reversion_probability'] += 0.25
            if z_score < 0:
                analysis['reversion_signal'] = 'bullish_reversion'
        
        # RSI extremes
        if rsi > 80:
            analysis['patterns'].append(f"RSI overbought: {rsi:.1f}")
            analysis['reversion_probability'] += 0.2
            if analysis['reversion_signal'] == 'neutral':
                analysis['reversion_signal'] = 'bearish_reversion'
        elif rsi < 20:
            analysis['patterns'].append(f"RSI oversold: {rsi:.1f}")
            analysis['reversion_probability'] += 0.2
            if analysis['reversion_signal'] == 'neutral':
                analysis['reversion_signal'] = 'bullish_reversion'
        
        # Williams %R extremes
        if williams_r > -10:  # Overbought
            analysis['patterns'].append("Williams %R overbought")
            analysis['reversion_probability'] += 0.15
        elif williams_r < -90:  # Oversold
            analysis['patterns'].append("Williams %R oversold")
            analysis['reversion_probability'] += 0.15
        
        # Price distance from moving averages
        if abs(price_distance_sma20) > 5:  # >5% from 20-day MA
            analysis['patterns'].append(f"Price {price_distance_sma20:+.1f}% from 20-day MA")
            analysis['reversion_probability'] += 0.15
        
        # Reversion velocity (momentum toward mean)
        if reversion_velocity > 0 and z_score < 0:  # Moving toward mean from below
            analysis['patterns'].append("Positive reversion velocity from oversold")
            analysis['reversion_probability'] += 0.1
        elif reversion_velocity < 0 and z_score > 0:  # Moving toward mean from above
            analysis['patterns'].append("Negative reversion velocity from overbought")
            analysis['reversion_probability'] += 0.1
        
        # Historical reversion analysis
        data = reversion_data.get('data')
        if data is not None:
            historical_patterns = self._analyze_historical_reversions(data)
            analysis['patterns'].extend(historical_patterns)
        
        # Determine time horizon based on extremeness
        if analysis['extremeness_level'] == 'extreme':
            analysis['time_horizon'] = 'short'  # Extreme levels revert quickly
        elif analysis['extremeness_level'] == 'high':
            analysis['time_horizon'] = 'medium'
        else:
            analysis['time_horizon'] = 'long'
        
        # Cap probability
        analysis['reversion_probability'] = min(0.9, analysis['reversion_probability'])
        
        return analysis
    
    def _analyze_historical_reversions(self, data: pd.DataFrame) -> List[str]:
        """Analyze historical mean reversion patterns"""
        
        patterns = []
        
        try:
            # Look for recent reversion patterns
            recent_data = data.tail(20)
            
            # Count times price touched extreme levels and reverted
            extreme_touches = 0
            successful_reversions = 0
            
            for i in range(5, len(recent_data)):
                z_score = recent_data['Z_Score_20'].iloc[i]
                future_z_scores = recent_data['Z_Score_20'].iloc[i+1:i+6]  # Next 5 days
                
                if abs(z_score) > 1.5:  # Extreme level
                    extreme_touches += 1
                    
                    # Check if it reverted (moved toward mean)
                    if z_score > 0 and any(future_z_scores < z_score * 0.7):
                        successful_reversions += 1
                    elif z_score < 0 and any(future_z_scores > z_score * 0.7):
                        successful_reversions += 1
            
            if extreme_touches > 0:
                reversion_rate = successful_reversions / extreme_touches
                patterns.append(f"Recent reversion success rate: {reversion_rate:.1f}%")
            
            # Check for recent failed reversions (trend continuation)
            recent_failures = self._check_recent_failures(recent_data)
            if recent_failures:
                patterns.append("Recent trend continuation signals")
                
        except Exception as e:
            logger.warning(f"Historical analysis error: {e}")
        
        return patterns
    
    def _check_recent_failures(self, data: pd.DataFrame) -> bool:
        """Check for recent failed mean reversions (trend continuation)"""
        
        try:
            # Look for cases where price stayed extreme
            extreme_persistence = 0
            
            for i in range(len(data) - 5):
                z_score = data['Z_Score_20'].iloc[i]
                if abs(z_score) > 1.5:
                    # Check if it stayed extreme for next few days
                    future_scores = data['Z_Score_20'].iloc[i+1:i+4]
                    if all(score * z_score > 0 and abs(score) > 1.0 for score in future_scores):
                        extreme_persistence += 1
            
            return extreme_persistence > 2  # More than 2 recent failures
            
        except Exception:
            return False
    
    def _generate_signal(self, pattern_analysis: Dict) -> Dict:
        """Generate trading signal from mean reversion analysis"""
        
        reversion_signal = pattern_analysis.get('reversion_signal', 'neutral')
        reversion_probability = pattern_analysis.get('reversion_probability', 0.5)
        extremeness_level = pattern_analysis.get('extremeness_level', 'normal')
        time_horizon = pattern_analysis.get('time_horizon', 'medium')
        
        # Signal direction and confidence
        direction = "HOLD"
        confidence = 0.5
        
        if reversion_signal == 'bullish_reversion' and reversion_probability > 0.65:
            direction = "BUY"
            confidence = min(0.85, reversion_probability)
        elif reversion_signal == 'bearish_reversion' and reversion_probability > 0.65:
            direction = "SELL"
            confidence = min(0.85, reversion_probability)
        
        # Adjust confidence based on extremeness
        if extremeness_level == 'extreme':
            confidence *= 1.1  # Higher confidence for extreme levels
        elif extremeness_level == 'normal':
            confidence *= 0.8  # Lower confidence for normal levels
        
        confidence = min(0.90, confidence)  # Cap confidence
        
        signal_strength = confidence * self.weight if direction != "HOLD" else 0.1
        
        # Create reasoning
        patterns = pattern_analysis.get('patterns', [])
        reasoning = f"Mean reversion: {reversion_signal}, {extremeness_level} level"
        if patterns:
            reasoning += f". Key patterns: {', '.join(patterns[:2])}"
        
        return {
            "signal_name": self.signal_name,
            "direction": direction,
            "strength": signal_strength,
            "confidence": confidence,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat(),
            "reversion_data": {
                "signal": reversion_signal,
                "probability": reversion_probability,
                "extremeness": extremeness_level,
                "time_horizon": time_horizon
            }
        }
    
    def _create_neutral_signal(self, reason: str) -> Dict:
        """Create neutral signal with reason"""
        return {
            "signal_name": self.signal_name,
            "direction": "HOLD",
            "strength": 0.1,
            "confidence": 0.5,
            "reasoning": reason,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_signal_status(self) -> Dict:
        """Get current signal status"""
        return {
            "signal_name": self.signal_name,
            "weight": self.weight,
            "last_analysis": self.last_analysis,
            "status": "operational"
        } 
"""
Momentum Analysis Signal
Multi-timeframe momentum detection for RTX
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict
from loguru import logger

from config.trading_config import config

class MomentumSignal:
    """Analyze momentum across multiple timeframes"""
    
    def __init__(self):
        self.signal_name = "momentum"
        self.weight = config.SIGNAL_WEIGHTS.get(self.signal_name, 0.10)
        self.last_analysis = None
        
    async def analyze(self, symbol: str = "RTX") -> Dict:
        """Analyze momentum patterns for trading signals"""
        
        try:
            # Get price data
            data = await self._get_price_data(symbol)
            
            if data.empty:
                return self._create_neutral_signal("No price data available")
            
            # Calculate momentum indicators
            momentum_data = self._calculate_momentum_indicators(data)
            
            # Analyze momentum patterns
            momentum_analysis = self._analyze_momentum_patterns(momentum_data)
            
            # Generate signal
            signal = self._generate_signal(momentum_analysis)
            
            self.last_analysis = signal
            return signal
            
        except Exception as e:
            logger.error(f"📊 Momentum analysis error: {e}")
            return self._create_neutral_signal(f"Analysis error: {str(e)}")
    
    async def _get_price_data(self, symbol: str, period: str = "60d") -> pd.DataFrame:
        """Get price data for momentum analysis"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval="1d")
            
            logger.info(f"📊 Loaded {len(data)} days for momentum analysis")
            return data
            
        except Exception as e:
            logger.error(f"📊 Price data error: {e}")
            return pd.DataFrame()
    
    def _calculate_momentum_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate various momentum indicators"""
        
        # Price-based momentum
        data['Returns_1d'] = data['Close'].pct_change(1)
        data['Returns_5d'] = data['Close'].pct_change(5)
        data['Returns_10d'] = data['Close'].pct_change(10)
        data['Returns_20d'] = data['Close'].pct_change(20)
        
        # Rate of Change (ROC)
        data['ROC_10'] = ((data['Close'] - data['Close'].shift(10)) / data['Close'].shift(10)) * 100
        data['ROC_20'] = ((data['Close'] - data['Close'].shift(20)) / data['Close'].shift(20)) * 100
        
        # Momentum oscillator
        data['Momentum_10'] = data['Close'] / data['Close'].shift(10)
        data['Momentum_20'] = data['Close'] / data['Close'].shift(20)
        
        # Williams %R
        high_14 = data['High'].rolling(window=14).max()
        low_14 = data['Low'].rolling(window=14).min()
        data['Williams_R'] = -100 * (high_14 - data['Close']) / (high_14 - low_14)
        
        # Stochastic oscillator
        low_14_stoch = data['Low'].rolling(window=14).min()
        high_14_stoch = data['High'].rolling(window=14).max()
        data['Stoch_K'] = 100 * (data['Close'] - low_14_stoch) / (high_14_stoch - low_14_stoch)
        data['Stoch_D'] = data['Stoch_K'].rolling(window=3).mean()
        
        # Volume-weighted momentum
        data['Volume_MA'] = data['Volume'].rolling(window=20).mean()
        data['Volume_Ratio'] = data['Volume'] / data['Volume_MA']
        data['Volume_Weighted_Return'] = data['Returns_1d'] * data['Volume_Ratio']
        
        # Acceleration (second derivative of price)
        data['Price_Velocity'] = data['Close'].diff()
        data['Price_Acceleration'] = data['Price_Velocity'].diff()
        
        # Get current values
        latest = data.iloc[-1]
        
        return {
            'current_price': latest['Close'],
            'returns_1d': latest['Returns_1d'],
            'returns_5d': latest['Returns_5d'],
            'returns_10d': latest['Returns_10d'],
            'returns_20d': latest['Returns_20d'],
            'roc_10': latest['ROC_10'],
            'roc_20': latest['ROC_20'],
            'momentum_10': latest['Momentum_10'],
            'momentum_20': latest['Momentum_20'],
            'williams_r': latest['Williams_R'],
            'stoch_k': latest['Stoch_K'],
            'stoch_d': latest['Stoch_D'],
            'volume_ratio': latest['Volume_Ratio'],
            'volume_weighted_return': latest['Volume_Weighted_Return'],
            'price_acceleration': latest['Price_Acceleration'],
            'data': data  # Keep for further analysis
        }
    
    def _analyze_momentum_patterns(self, momentum_data: Dict) -> Dict:
        """Analyze momentum patterns and trends"""
        
        analysis = {
            'short_term_momentum': 'neutral',
            'medium_term_momentum': 'neutral',
            'long_term_momentum': 'neutral',
            'momentum_divergence': False,
            'momentum_acceleration': 'stable',
            'volume_confirmation': False,
            'signals': []
        }
        
        # Short-term momentum (1-5 days)
        returns_1d = momentum_data.get('returns_1d', 0)
        returns_5d = momentum_data.get('returns_5d', 0)
        
        if returns_1d > 0.01 and returns_5d > 0.02:
            analysis['short_term_momentum'] = 'bullish'
            analysis['signals'].append("Strong short-term upward momentum")
        elif returns_1d < -0.01 and returns_5d < -0.02:
            analysis['short_term_momentum'] = 'bearish'
            analysis['signals'].append("Strong short-term downward momentum")
        
        # Medium-term momentum (5-20 days)
        returns_10d = momentum_data.get('returns_10d', 0)
        returns_20d = momentum_data.get('returns_20d', 0)
        
        if returns_10d > 0.03 and returns_20d > 0.05:
            analysis['medium_term_momentum'] = 'bullish'
            analysis['signals'].append("Sustained medium-term momentum")
        elif returns_10d < -0.03 and returns_20d < -0.05:
            analysis['medium_term_momentum'] = 'bearish'
            analysis['signals'].append("Sustained medium-term decline")
        
        # Momentum consistency
        roc_10 = momentum_data.get('roc_10', 0)
        roc_20 = momentum_data.get('roc_20', 0)
        
        if roc_10 > 0 and roc_20 > 0 and roc_10 > roc_20:
            analysis['long_term_momentum'] = 'accelerating_bullish'
            analysis['signals'].append("Accelerating bullish momentum")
        elif roc_10 < 0 and roc_20 < 0 and roc_10 < roc_20:
            analysis['long_term_momentum'] = 'accelerating_bearish'
            analysis['signals'].append("Accelerating bearish momentum")
        
        # Stochastic analysis
        stoch_k = momentum_data.get('stoch_k', 50)
        stoch_d = momentum_data.get('stoch_d', 50)
        
        if stoch_k > 80 and stoch_d > 80:
            analysis['signals'].append("Overbought stochastic levels")
        elif stoch_k < 20 and stoch_d < 20:
            analysis['signals'].append("Oversold stochastic levels")
        
        # Williams %R analysis
        williams_r = momentum_data.get('williams_r', -50)
        if williams_r > -20:
            analysis['signals'].append("Williams %R overbought")
        elif williams_r < -80:
            analysis['signals'].append("Williams %R oversold")
        
        # Volume confirmation
        volume_ratio = momentum_data.get('volume_ratio', 1.0)
        volume_weighted_return = momentum_data.get('volume_weighted_return', 0)
        
        if volume_ratio > 1.5 and abs(volume_weighted_return) > 0.01:
            analysis['volume_confirmation'] = True
            analysis['signals'].append("Volume confirming price momentum")
        
        # Price acceleration
        price_acceleration = momentum_data.get('price_acceleration', 0)
        if abs(price_acceleration) > 0.5:
            if price_acceleration > 0:
                analysis['momentum_acceleration'] = 'accelerating_up'
                analysis['signals'].append("Price acceleration to upside")
            else:
                analysis['momentum_acceleration'] = 'accelerating_down'
                analysis['signals'].append("Price acceleration to downside")
        
        # Momentum divergence check
        data = momentum_data.get('data')
        if data is not None and len(data) > 20:
            analysis['momentum_divergence'] = self._check_momentum_divergence(data)
            if analysis['momentum_divergence']:
                analysis['signals'].append("Momentum divergence detected")
        
        return analysis
    
    def _check_momentum_divergence(self, data: pd.DataFrame) -> bool:
        """Check for momentum divergence patterns"""
        
        try:
            # Look at last 20 days
            recent_data = data.tail(20)
            
            # Compare price trend vs momentum trend
            price_trend = (recent_data['Close'].iloc[-1] - recent_data['Close'].iloc[0]) / recent_data['Close'].iloc[0]
            roc_trend = recent_data['ROC_10'].iloc[-5:].mean() - recent_data['ROC_10'].iloc[:5].mean()
            
            # Divergence if price and momentum move in opposite directions
            if price_trend > 0.02 and roc_trend < -2:  # Price up, momentum down
                return True
            elif price_trend < -0.02 and roc_trend > 2:  # Price down, momentum up
                return True
                
            return False
            
        except Exception:
            return False
    
    def _generate_signal(self, momentum_analysis: Dict) -> Dict:
        """Generate trading signal from momentum analysis"""
        
        short_momentum = momentum_analysis.get('short_term_momentum', 'neutral')
        medium_momentum = momentum_analysis.get('medium_term_momentum', 'neutral')
        long_momentum = momentum_analysis.get('long_term_momentum', 'neutral')
        volume_confirmation = momentum_analysis.get('volume_confirmation', False)
        divergence = momentum_analysis.get('momentum_divergence', False)
        
        # Count bullish/bearish signals
        bullish_signals = 0
        bearish_signals = 0
        
        if 'bullish' in short_momentum:
            bullish_signals += 1
        elif 'bearish' in short_momentum:
            bearish_signals += 1
        
        if 'bullish' in medium_momentum:
            bullish_signals += 1
        elif 'bearish' in medium_momentum:
            bearish_signals += 1
        
        if 'accelerating_bullish' in long_momentum:
            bullish_signals += 2  # Weight long-term more
        elif 'accelerating_bearish' in long_momentum:
            bearish_signals += 2
        
        # Volume confirmation bonus
        if volume_confirmation:
            if bullish_signals > bearish_signals:
                bullish_signals += 1
            elif bearish_signals > bullish_signals:
                bearish_signals += 1
        
        # Divergence penalty
        if divergence:
            confidence_penalty = 0.2
        else:
            confidence_penalty = 0
        
        # Determine signal
        total_signals = bullish_signals + bearish_signals
        if total_signals == 0:
            direction = "HOLD"
            confidence = 0.5
        else:
            bullish_ratio = bullish_signals / total_signals
            
            if bullish_ratio > 0.65:
                direction = "BUY"
                confidence = min(0.85, bullish_ratio - confidence_penalty)
            elif bullish_ratio < 0.35:
                direction = "SELL"
                confidence = min(0.85, (1 - bullish_ratio) - confidence_penalty)
            else:
                direction = "HOLD"
                confidence = 0.5
        
        signal_strength = confidence * self.weight if direction != "HOLD" else 0.1
        
        # Create reasoning
        signals = momentum_analysis.get('signals', [])
        reasoning = f"Momentum: {bullish_signals} bullish, {bearish_signals} bearish signals"
        if signals:
            reasoning += f". Key: {signals[0][:50]}..."
        
        return {
            "signal_name": self.signal_name,
            "direction": direction,
            "strength": signal_strength,
            "confidence": confidence,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat(),
            "momentum_data": {
                "short_term": short_momentum,
                "medium_term": medium_momentum,
                "long_term": long_momentum,
                "volume_confirmation": volume_confirmation,
                "divergence": divergence
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
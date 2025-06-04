"""
Technical Analysis Signal
Comprehensive technical indicators for RTX trading
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict
from loguru import logger

from config.trading_config import config

class TechnicalAnalysisSignal:
    """Advanced technical analysis for RTX"""
    
    def __init__(self):
        self.signal_name = "technical_analysis"
        self.weight = config.SIGNAL_WEIGHTS.get(self.signal_name, 0.15)
        self.last_analysis = None
        
    async def analyze(self, symbol: str = "RTX") -> Dict:
        """Perform comprehensive technical analysis"""
        
        try:
            # Get price data
            data = await self._get_price_data(symbol)
            
            if data.empty:
                return self._create_neutral_signal("No price data available")
            
            # Calculate technical indicators
            indicators = self._calculate_indicators(data)
            
            # Generate signal
            signal = self._generate_signal(indicators)
            
            self.last_analysis = signal
            return signal
            
        except Exception as e:
            logger.error(f"📊 Technical analysis error: {e}")
            return self._create_neutral_signal(f"Analysis error: {str(e)}")
    
    async def _get_price_data(self, symbol: str, period: str = "60d") -> pd.DataFrame:
        """Get historical price data"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            logger.info(f"📊 Loaded {len(data)} days of {symbol} price data")
            return data
            
        except Exception as e:
            logger.error(f"📊 Price data error: {e}")
            return pd.DataFrame()
    
    def _calculate_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate multiple technical indicators"""
        
        indicators = {}
        
        # Current price
        current_price = data['Close'].iloc[-1]
        indicators['current_price'] = current_price
        
        # Moving averages
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['EMA_12'] = data['Close'].ewm(span=12).mean()
        data['EMA_26'] = data['Close'].ewm(span=26).mean()
        
        # RSI (Relative Strength Index)
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        data['MACD'] = data['EMA_12'] - data['EMA_26']
        data['MACD_Signal'] = data['MACD'].ewm(span=9).mean()
        data['MACD_Histogram'] = data['MACD'] - data['MACD_Signal']
        
        # Bollinger Bands
        data['BB_Middle'] = data['Close'].rolling(window=20).mean()
        bb_std = data['Close'].rolling(window=20).std()
        data['BB_Upper'] = data['BB_Middle'] + (bb_std * 2)
        data['BB_Lower'] = data['BB_Middle'] - (bb_std * 2)
        
        # Volume indicators
        data['Volume_SMA'] = data['Volume'].rolling(window=20).mean()
        
        # Get latest values
        latest = data.iloc[-1]
        
        indicators.update({
            'sma_20': latest['SMA_20'],
            'sma_50': latest['SMA_50'],
            'ema_12': latest['EMA_12'],
            'ema_26': latest['EMA_26'],
            'rsi': latest['RSI'],
            'macd': latest['MACD'],
            'macd_signal': latest['MACD_Signal'],
            'macd_histogram': latest['MACD_Histogram'],
            'bb_upper': latest['BB_Upper'],
            'bb_middle': latest['BB_Middle'],
            'bb_lower': latest['BB_Lower'],
            'volume': latest['Volume'],
            'volume_sma': latest['Volume_SMA']
        })
        
        # Calculate signals
        indicators.update(self._analyze_signals(data, indicators))
        
        return indicators
    
    def _analyze_signals(self, data: pd.DataFrame, indicators: Dict) -> Dict:
        """Analyze indicators for trading signals"""
        
        signals = {}
        current_price = indicators['current_price']
        
        # Moving Average signals
        sma_20_signal = "bullish" if current_price > indicators['sma_20'] else "bearish"
        sma_50_signal = "bullish" if current_price > indicators['sma_50'] else "bearish"
        ma_cross_signal = "bullish" if indicators['sma_20'] > indicators['sma_50'] else "bearish"
        
        # RSI signals
        rsi = indicators['rsi']
        if rsi > 70:
            rsi_signal = "overbought"
        elif rsi < 30:
            rsi_signal = "oversold"
        else:
            rsi_signal = "neutral"
        
        # MACD signals
        macd_signal = "bullish" if indicators['macd'] > indicators['macd_signal'] else "bearish"
        macd_momentum = "bullish" if indicators['macd_histogram'] > 0 else "bearish"
        
        # Bollinger Bands signals
        if current_price > indicators['bb_upper']:
            bb_signal = "overbought"
        elif current_price < indicators['bb_lower']:
            bb_signal = "oversold"
        else:
            bb_signal = "normal"
        
        # Volume analysis
        volume_signal = "high" if indicators['volume'] > indicators['volume_sma'] * 1.5 else "normal"
        
        # Support/Resistance levels
        recent_high = data['High'].tail(20).max()
        recent_low = data['Low'].tail(20).min()
        
        resistance_distance = (recent_high - current_price) / current_price
        support_distance = (current_price - recent_low) / current_price
        
        signals.update({
            'sma_20_signal': sma_20_signal,
            'sma_50_signal': sma_50_signal,
            'ma_cross_signal': ma_cross_signal,
            'rsi_signal': rsi_signal,
            'macd_signal': macd_signal,
            'macd_momentum': macd_momentum,
            'bb_signal': bb_signal,
            'volume_signal': volume_signal,
            'resistance_distance': resistance_distance,
            'support_distance': support_distance,
            'recent_high': recent_high,
            'recent_low': recent_low
        })
        
        return signals
    
    def _generate_signal(self, indicators: Dict) -> Dict:
        """Generate overall trading signal from technical indicators"""
        
        bullish_signals = 0
        bearish_signals = 0
        confidence_factors = []
        
        # Count bullish/bearish signals
        if indicators.get('sma_20_signal') == 'bullish':
            bullish_signals += 1
        else:
            bearish_signals += 1
            
        if indicators.get('ma_cross_signal') == 'bullish':
            bullish_signals += 1
        else:
            bearish_signals += 1
            
        if indicators.get('macd_signal') == 'bullish':
            bullish_signals += 1
        else:
            bearish_signals += 1
            
        if indicators.get('macd_momentum') == 'bullish':
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        # RSI considerations
        rsi_signal = indicators.get('rsi_signal')
        if rsi_signal == 'oversold':
            bullish_signals += 1
            confidence_factors.append("RSI oversold")
        elif rsi_signal == 'overbought':
            bearish_signals += 1
            confidence_factors.append("RSI overbought")
        
        # Bollinger Bands
        bb_signal = indicators.get('bb_signal')
        if bb_signal == 'oversold':
            bullish_signals += 1
            confidence_factors.append("Price near lower BB")
        elif bb_signal == 'overbought':
            bearish_signals += 1
            confidence_factors.append("Price near upper BB")
        
        # Volume confirmation
        if indicators.get('volume_signal') == 'high':
            confidence_factors.append("High volume")
        
        # Determine overall signal
        total_signals = bullish_signals + bearish_signals
        bullish_ratio = bullish_signals / total_signals if total_signals > 0 else 0.5
        
        if bullish_ratio > 0.65:
            direction = "BUY"
            confidence = bullish_ratio
        elif bullish_ratio < 0.35:
            direction = "SELL"
            confidence = 1 - bullish_ratio
        else:
            direction = "HOLD"
            confidence = 0.5
        
        signal_strength = confidence * self.weight
        
        # Create reasoning
        reasoning = f"Technical analysis: {bullish_signals} bullish, {bearish_signals} bearish signals"
        if confidence_factors:
            reasoning += f". Key factors: {', '.join(confidence_factors[:3])}"
        
        return {
            "signal_name": self.signal_name,
            "direction": direction,
            "strength": signal_strength,
            "confidence": confidence,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat(),
            "indicators": {
                "current_price": indicators['current_price'],
                "rsi": indicators['rsi'],
                "macd": indicators['macd'],
                "sma_20": indicators['sma_20'],
                "sma_50": indicators['sma_50'],
                "bullish_signals": bullish_signals,
                "bearish_signals": bearish_signals
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
"""
Volatility Analysis Signal
Advanced volatility pattern recognition for RTX trading
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
from loguru import logger

from config.trading_config import config

class VolatilityAnalysisSignal:
    """Analyze volatility patterns for trading opportunities"""
    
    def __init__(self):
        self.signal_name = "volatility_analysis"
        self.weight = config.SIGNAL_WEIGHTS.get(self.signal_name, 0.15)
        self.last_analysis = None
        
    async def analyze(self, symbol: str = "RTX") -> Dict:
        """Analyze volatility patterns for trading signals"""
        
        try:
            # Get price data
            data = await self._get_price_data(symbol)
            
            if data.empty:
                return self._create_neutral_signal("No price data available")
            
            # Calculate volatility metrics
            volatility_metrics = self._calculate_volatility_metrics(data)
            
            # Analyze volatility patterns
            pattern_analysis = self._analyze_volatility_patterns(volatility_metrics)
            
            # Generate signal
            signal = self._generate_signal(pattern_analysis)
            
            self.last_analysis = signal
            return signal
            
        except Exception as e:
            logger.error(f"📊 Volatility analysis error: {e}")
            return self._create_neutral_signal(f"Analysis error: {str(e)}")
    
    async def _get_price_data(self, symbol: str, period: str = "90d") -> pd.DataFrame:
        """Get historical price data for volatility analysis"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            logger.info(f"📊 Loaded {len(data)} days of {symbol} data for volatility analysis")
            return data
            
        except Exception as e:
            logger.error(f"📊 Price data error: {e}")
            return pd.DataFrame()
    
    def _calculate_volatility_metrics(self, data: pd.DataFrame) -> Dict:
        """Calculate comprehensive volatility metrics"""
        
        # Calculate returns
        data['Returns'] = data['Close'].pct_change()
        data['Log_Returns'] = np.log(data['Close'] / data['Close'].shift(1))
        
        # True Range calculation
        data['High_Low'] = data['High'] - data['Low']
        data['High_Close'] = np.abs(data['High'] - data['Close'].shift(1))
        data['Low_Close'] = np.abs(data['Low'] - data['Close'].shift(1))
        data['True_Range'] = data[['High_Low', 'High_Close', 'Low_Close']].max(axis=1)
        
        # Average True Range (ATR)
        data['ATR_14'] = data['True_Range'].rolling(window=14).mean()
        data['ATR_21'] = data['True_Range'].rolling(window=21).mean()
        
        # Historical volatility (different windows)
        data['HV_10'] = data['Returns'].rolling(window=10).std() * np.sqrt(252)
        data['HV_20'] = data['Returns'].rolling(window=20).std() * np.sqrt(252)
        data['HV_30'] = data['Returns'].rolling(window=30).std() * np.sqrt(252)
        
        # Parkinson volatility (high-low estimator)
        data['Parkinson_Vol'] = np.sqrt((1 / (4 * np.log(2))) * 
                                       (np.log(data['High'] / data['Low'])) ** 2)
        data['Parkinson_20'] = data['Parkinson_Vol'].rolling(window=20).mean() * np.sqrt(252)
        
        # Garman-Klass volatility estimator
        ln_hl = np.log(data['High'] / data['Low'])
        ln_co = np.log(data['Close'] / data['Open'])
        data['GK_Vol'] = 0.5 * ln_hl**2 - (2 * np.log(2) - 1) * ln_co**2
        data['GK_20'] = data['GK_Vol'].rolling(window=20).mean() * np.sqrt(252)
        
        # GARCH-like volatility clustering
        data['Vol_Clustering'] = data['Returns'].rolling(window=5).std()
        
        # Current values
        latest = data.iloc[-1]
        
        metrics = {
            'current_price': latest['Close'],
            'current_return': latest['Returns'],
            'atr_14': latest['ATR_14'],
            'atr_21': latest['ATR_21'],
            'hv_10': latest['HV_10'],
            'hv_20': latest['HV_20'],
            'hv_30': latest['HV_30'],
            'parkinson_20': latest['Parkinson_20'],
            'gk_20': latest['GK_20'],
            'vol_clustering': latest['Vol_Clustering']
        }
        
        # Add percentile rankings
        metrics.update(self._calculate_volatility_percentiles(data))
        
        return metrics
    
    def _calculate_volatility_percentiles(self, data: pd.DataFrame) -> Dict:
        """Calculate where current volatility ranks historically"""
        
        percentiles = {}
        
        # ATR percentiles
        if len(data) > 50:
            current_atr = data['ATR_14'].iloc[-1]
            atr_percentile = (data['ATR_14'].dropna() <= current_atr).mean()
            percentiles['atr_percentile'] = atr_percentile
        
        # Historical volatility percentiles
        if len(data) > 50:
            current_hv = data['HV_20'].iloc[-1]
            hv_percentile = (data['HV_20'].dropna() <= current_hv).mean()
            percentiles['hv_percentile'] = hv_percentile
        
        # Parkinson volatility percentiles
        if len(data) > 50:
            current_park = data['Parkinson_20'].iloc[-1]
            park_percentile = (data['Parkinson_20'].dropna() <= current_park).mean()
            percentiles['parkinson_percentile'] = park_percentile
        
        return percentiles
    
    def _analyze_volatility_patterns(self, metrics: Dict) -> Dict:
        """Analyze volatility patterns for trading opportunities"""
        
        analysis = {
            'volatility_regime': 'normal',
            'vol_trend': 'stable',
            'mean_reversion_signal': 'neutral',
            'breakout_probability': 0.5,
            'patterns': []
        }
        
        # Determine volatility regime
        hv_percentile = metrics.get('hv_percentile', 0.5)
        atr_percentile = metrics.get('atr_percentile', 0.5)
        
        if hv_percentile > 0.8 or atr_percentile > 0.8:
            analysis['volatility_regime'] = 'high'
            analysis['patterns'].append("High volatility regime")
        elif hv_percentile < 0.2 or atr_percentile < 0.2:
            analysis['volatility_regime'] = 'low'
            analysis['patterns'].append("Low volatility regime")
        
        # Volatility trend analysis
        hv_10 = metrics.get('hv_10', 0)
        hv_20 = metrics.get('hv_20', 0)
        hv_30 = metrics.get('hv_30', 0)
        
        if hv_10 > hv_20 > hv_30:
            analysis['vol_trend'] = 'increasing'
            analysis['patterns'].append("Volatility expanding")
        elif hv_10 < hv_20 < hv_30:
            analysis['vol_trend'] = 'decreasing'
            analysis['patterns'].append("Volatility contracting")
        
        # Mean reversion signals
        if analysis['volatility_regime'] == 'high':
            analysis['mean_reversion_signal'] = 'bearish'  # High vol tends to revert
            analysis['patterns'].append("High vol mean reversion setup")
        elif analysis['volatility_regime'] == 'low':
            analysis['mean_reversion_signal'] = 'bullish'  # Low vol may precede moves
            analysis['patterns'].append("Low vol expansion setup")
        
        # Breakout probability
        atr_14 = metrics.get('atr_14', 0)
        atr_21 = metrics.get('atr_21', 0)
        
        if atr_14 > atr_21 * 1.2:
            analysis['breakout_probability'] = 0.7
            analysis['patterns'].append("Recent volatility spike")
        elif atr_14 < atr_21 * 0.8:
            analysis['breakout_probability'] = 0.3
            analysis['patterns'].append("Volatility compression")
        
        # Volatility clustering detection
        vol_clustering = metrics.get('vol_clustering', 0)
        if vol_clustering > 0.02:  # 2% daily clustering
            analysis['patterns'].append("Volatility clustering detected")
        
        # Trading implications
        analysis['trading_implications'] = self._get_trading_implications(analysis)
        
        return analysis
    
    def _get_trading_implications(self, analysis: Dict) -> List[str]:
        """Get trading implications from volatility analysis"""
        
        implications = []
        
        regime = analysis['volatility_regime']
        trend = analysis['vol_trend']
        
        if regime == 'low' and trend == 'stable':
            implications.append("Low vol environment - expect range trading")
            implications.append("Consider selling premium strategies")
        elif regime == 'low' and trend == 'increasing':
            implications.append("Vol expansion likely - prepare for directional moves")
            implications.append("Good for momentum strategies")
        elif regime == 'high' and trend == 'decreasing':
            implications.append("Vol mean reversion underway")
            implications.append("Favor mean reversion strategies")
        elif regime == 'high' and trend == 'increasing':
            implications.append("High vol persistence - trend continuation")
            implications.append("Risk management critical")
        
        # Breakout implications
        breakout_prob = analysis['breakout_probability']
        if breakout_prob > 0.7:
            implications.append("High breakout probability - prepare for moves")
        elif breakout_prob < 0.3:
            implications.append("Low breakout probability - range likely")
        
        return implications
    
    def _generate_signal(self, pattern_analysis: Dict) -> Dict:
        """Generate trading signal from volatility analysis"""
        
        regime = pattern_analysis.get('volatility_regime', 'normal')
        trend = pattern_analysis.get('vol_trend', 'stable')
        mean_reversion = pattern_analysis.get('mean_reversion_signal', 'neutral')
        breakout_prob = pattern_analysis.get('breakout_probability', 0.5)
        
        # Determine signal direction and confidence
        direction = "HOLD"
        confidence = 0.5
        signal_strength = 0.1
        
        # Low volatility expansion setup
        if regime == 'low' and trend == 'increasing':
            direction = "BUY"  # Expecting upward movement
            confidence = 0.65
            signal_strength = confidence * self.weight
        
        # High volatility mean reversion
        elif regime == 'high' and mean_reversion == 'bearish':
            direction = "SELL"  # Expecting volatility to decrease
            confidence = 0.60
            signal_strength = confidence * self.weight
        
        # Breakout preparation
        elif breakout_prob > 0.7:
            direction = "BUY"  # Position for potential breakout
            confidence = 0.55
            signal_strength = confidence * self.weight
        
        # Create reasoning
        patterns = pattern_analysis.get('patterns', [])
        reasoning = f"Volatility analysis: {regime} vol regime, {trend} trend"
        if patterns:
            reasoning += f". Key patterns: {', '.join(patterns[:2])}"
        
        return {
            "signal_name": self.signal_name,
            "direction": direction,
            "strength": signal_strength,
            "confidence": confidence,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat(),
            "volatility_data": {
                "regime": regime,
                "trend": trend,
                "breakout_probability": breakout_prob,
                "mean_reversion_signal": mean_reversion
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
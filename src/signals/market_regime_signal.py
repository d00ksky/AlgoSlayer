"""
Market Regime Analysis Signal
Detect market regimes and adapt trading strategy accordingly
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
from loguru import logger

from config.trading_config import config

class MarketRegimeSignal:
    """Analyze market regime and adapt trading strategy"""
    
    def __init__(self):
        self.signal_name = "market_regime"
        self.weight = config.SIGNAL_WEIGHTS.get(self.signal_name, 0.10)
        self.last_analysis = None
        
        # Market indices for regime analysis
        self.market_indices = ['SPY', 'QQQ', 'VIX', 'DXY']  # S&P 500, NASDAQ, VIX, Dollar
        
    async def analyze(self, symbol: str = "RTX") -> Dict:
        """Analyze current market regime for trading signals"""
        
        try:
            # Get market data
            market_data = await self._get_market_data()
            
            if not market_data:
                return self._create_neutral_signal("No market data available")
            
            # Analyze market regime
            regime_analysis = self._analyze_market_regime(market_data)
            
            # Analyze RTX behavior in current regime
            rtx_analysis = await self._analyze_rtx_in_regime(symbol, regime_analysis)
            
            # Generate signal
            signal = self._generate_signal(regime_analysis, rtx_analysis)
            
            self.last_analysis = signal
            return signal
            
        except Exception as e:
            logger.error(f"📊 Market regime error: {e}")
            return self._create_neutral_signal(f"Analysis error: {str(e)}")
    
    async def _get_market_data(self, period: str = "60d") -> Dict:
        """Get market data for regime analysis"""
        
        market_data = {}
        
        for ticker in self.market_indices:
            try:
                yf_ticker = yf.Ticker(ticker)
                data = yf_ticker.history(period=period)
                
                if not data.empty:
                    # Calculate returns and volatility
                    data['Returns'] = data['Close'].pct_change()
                    data['Volatility'] = data['Returns'].rolling(window=20).std() * np.sqrt(252)
                    market_data[ticker] = data
                    
            except Exception as e:
                logger.warning(f"📊 Failed to get {ticker} data: {e}")
                continue
        
        logger.info(f"📊 Loaded market data for {len(market_data)} indices")
        return market_data
    
    def _analyze_market_regime(self, market_data: Dict) -> Dict:
        """Analyze current market regime"""
        
        regime = {
            'overall_regime': 'neutral',
            'trend_direction': 'sideways',
            'volatility_regime': 'normal',
            'risk_sentiment': 'neutral',
            'regime_strength': 0.5,
            'regime_indicators': {}
        }
        
        # Analyze S&P 500 (SPY) for overall market trend
        if 'SPY' in market_data:
            spy_regime = self._analyze_spy_regime(market_data['SPY'])
            regime.update(spy_regime)
        
        # Analyze VIX for volatility regime
        if 'VIX' in market_data:
            vix_regime = self._analyze_vix_regime(market_data['VIX'])
            regime['volatility_regime'] = vix_regime['volatility_regime']
            regime['risk_sentiment'] = vix_regime['risk_sentiment']
        
        # Analyze NASDAQ (QQQ) for tech sentiment
        if 'QQQ' in market_data:
            qqq_regime = self._analyze_qqq_regime(market_data['QQQ'])
            regime['tech_sentiment'] = qqq_regime['tech_sentiment']
        
        # Analyze Dollar (DXY) for macro environment
        if 'DXY' in market_data:
            dxy_regime = self._analyze_dxy_regime(market_data['DXY'])
            regime['dollar_regime'] = dxy_regime['dollar_regime']
        
        # Determine overall regime strength
        regime['regime_strength'] = self._calculate_regime_strength(regime)
        
        return regime
    
    def _analyze_spy_regime(self, spy_data: pd.DataFrame) -> Dict:
        """Analyze S&P 500 regime"""
        
        # Calculate moving averages
        spy_data['SMA_20'] = spy_data['Close'].rolling(window=20).mean()
        spy_data['SMA_50'] = spy_data['Close'].rolling(window=50).mean()
        spy_data['SMA_200'] = spy_data['Close'].rolling(window=200).mean()
        
        current_price = spy_data['Close'].iloc[-1]
        sma_20 = spy_data['SMA_20'].iloc[-1]
        sma_50 = spy_data['SMA_50'].iloc[-1]
        sma_200 = spy_data['SMA_200'].iloc[-1] if len(spy_data) >= 200 else sma_50
        
        # Determine trend
        if current_price > sma_20 > sma_50 > sma_200:
            trend = 'strong_bullish'
            overall_regime = 'bullish'
        elif current_price > sma_20 > sma_50:
            trend = 'bullish'
            overall_regime = 'bullish'
        elif current_price < sma_20 < sma_50 < sma_200:
            trend = 'strong_bearish'
            overall_regime = 'bearish'
        elif current_price < sma_20 < sma_50:
            trend = 'bearish'
            overall_regime = 'bearish'
        else:
            trend = 'sideways'
            overall_regime = 'neutral'
        
        return {
            'overall_regime': overall_regime,
            'trend_direction': trend,
            'spy_price': current_price,
            'spy_vs_sma20': (current_price - sma_20) / sma_20 * 100,
            'spy_vs_sma50': (current_price - sma_50) / sma_50 * 100
        }
    
    def _analyze_vix_regime(self, vix_data: pd.DataFrame) -> Dict:
        """Analyze VIX volatility regime"""
        
        current_vix = vix_data['Close'].iloc[-1]
        vix_20_avg = vix_data['Close'].rolling(window=20).mean().iloc[-1]
        
        # VIX regime classification
        if current_vix > 30:
            volatility_regime = 'high'
            risk_sentiment = 'fear'
        elif current_vix > 20:
            volatility_regime = 'elevated'
            risk_sentiment = 'caution'
        elif current_vix < 12:
            volatility_regime = 'low'
            risk_sentiment = 'complacency'
        else:
            volatility_regime = 'normal'
            risk_sentiment = 'neutral'
        
        return {
            'volatility_regime': volatility_regime,
            'risk_sentiment': risk_sentiment,
            'current_vix': current_vix,
            'vix_vs_avg': (current_vix - vix_20_avg) / vix_20_avg * 100
        }
    
    def _analyze_qqq_regime(self, qqq_data: pd.DataFrame) -> Dict:
        """Analyze NASDAQ tech sentiment"""
        
        qqq_data['Returns_5d'] = qqq_data['Close'].pct_change(5)
        recent_return = qqq_data['Returns_5d'].iloc[-1]
        
        if recent_return > 0.03:  # >3% in 5 days
            tech_sentiment = 'bullish'
        elif recent_return < -0.03:  # <-3% in 5 days
            tech_sentiment = 'bearish'
        else:
            tech_sentiment = 'neutral'
        
        return {
            'tech_sentiment': tech_sentiment,
            'qqq_5d_return': recent_return * 100
        }
    
    def _analyze_dxy_regime(self, dxy_data: pd.DataFrame) -> Dict:
        """Analyze Dollar strength regime"""
        
        dxy_data['SMA_20'] = dxy_data['Close'].rolling(window=20).mean()
        current_dxy = dxy_data['Close'].iloc[-1]
        dxy_sma = dxy_data['SMA_20'].iloc[-1]
        
        if current_dxy > dxy_sma * 1.02:  # >2% above average
            dollar_regime = 'strong'
        elif current_dxy < dxy_sma * 0.98:  # <2% below average
            dollar_regime = 'weak'
        else:
            dollar_regime = 'neutral'
        
        return {
            'dollar_regime': dollar_regime,
            'dxy_vs_avg': (current_dxy - dxy_sma) / dxy_sma * 100
        }
    
    def _calculate_regime_strength(self, regime: Dict) -> float:
        """Calculate overall regime strength"""
        
        strength = 0.5  # Base strength
        
        # Add strength based on trend clarity
        if regime['trend_direction'] in ['strong_bullish', 'strong_bearish']:
            strength += 0.3
        elif regime['trend_direction'] in ['bullish', 'bearish']:
            strength += 0.2
        
        # Add strength based on volatility regime
        if regime['volatility_regime'] in ['high', 'low']:
            strength += 0.1
        
        # Add strength based on risk sentiment alignment
        if (regime['overall_regime'] == 'bullish' and regime['risk_sentiment'] in ['neutral', 'complacency']) or \
           (regime['overall_regime'] == 'bearish' and regime['risk_sentiment'] in ['fear', 'caution']):
            strength += 0.1
        
        return min(1.0, strength)
    
    async def _analyze_rtx_in_regime(self, symbol: str, regime: Dict) -> Dict:
        """Analyze how RTX performs in current market regime"""
        
        try:
            # Get RTX data
            ticker = yf.Ticker(symbol)
            rtx_data = ticker.history(period="60d")
            
            if rtx_data.empty:
                return {'regime_fit': 'unknown'}
            
            # Calculate RTX characteristics
            rtx_data['Returns'] = rtx_data['Close'].pct_change()
            rtx_data['Volatility'] = rtx_data['Returns'].rolling(window=20).std() * np.sqrt(252)
            
            current_price = rtx_data['Close'].iloc[-1]
            recent_volatility = rtx_data['Volatility'].iloc[-1]
            recent_return = rtx_data['Returns'].tail(5).mean()  # 5-day average return
            
            # Analyze RTX fit with current regime
            regime_fit = self._determine_rtx_regime_fit(regime, recent_return, recent_volatility)
            
            return {
                'regime_fit': regime_fit,
                'rtx_price': current_price,
                'rtx_volatility': recent_volatility,
                'rtx_recent_return': recent_return * 100
            }
            
        except Exception as e:
            logger.error(f"📊 RTX regime analysis error: {e}")
            return {'regime_fit': 'unknown'}
    
    def _determine_rtx_regime_fit(self, regime: Dict, rtx_return: float, rtx_volatility: float) -> str:
        """Determine how well RTX fits current market regime"""
        
        overall_regime = regime.get('overall_regime', 'neutral')
        volatility_regime = regime.get('volatility_regime', 'normal')
        
        # RTX as defense stock characteristics
        if overall_regime == 'bearish' and volatility_regime == 'high':
            # High volatility bearish markets often favor defense stocks
            if rtx_return > 0:
                return 'outperforming'  # RTX doing well in difficult market
            else:
                return 'underperforming'
        
        elif overall_regime == 'bullish' and volatility_regime == 'low':
            # Low volatility bull markets may not favor defense as much
            if rtx_return < 0:
                return 'lagging'  # RTX lagging in good times
            else:
                return 'participating'
        
        elif volatility_regime == 'high':
            # High volatility generally favors defensive stocks
            return 'favored'
        
        else:
            return 'neutral'
    
    def _generate_signal(self, regime_analysis: Dict, rtx_analysis: Dict) -> Dict:
        """Generate trading signal based on market regime analysis"""
        
        overall_regime = regime_analysis.get('overall_regime', 'neutral')
        volatility_regime = regime_analysis.get('volatility_regime', 'normal')
        risk_sentiment = regime_analysis.get('risk_sentiment', 'neutral')
        regime_strength = regime_analysis.get('regime_strength', 0.5)
        regime_fit = rtx_analysis.get('regime_fit', 'neutral')
        
        # Signal logic based on regime
        direction = "HOLD"
        confidence = 0.5
        
        # Defense stock logic in different regimes
        if overall_regime == 'bearish' and volatility_regime in ['high', 'elevated']:
            # Bearish high-vol environment favors defense stocks
            direction = "BUY"
            confidence = 0.70
        
        elif risk_sentiment == 'fear' and regime_fit == 'outperforming':
            # Fear environment where RTX is outperforming
            direction = "BUY"
            confidence = 0.75
        
        elif overall_regime == 'bullish' and volatility_regime == 'low' and regime_fit == 'lagging':
            # Bull market where RTX is lagging - might avoid
            direction = "SELL"
            confidence = 0.60
        
        elif volatility_regime == 'high' and regime_fit in ['favored', 'outperforming']:
            # High volatility favoring defensive positions
            direction = "BUY"
            confidence = 0.65
        
        # Adjust confidence by regime strength
        confidence *= regime_strength
        confidence = min(0.85, confidence)  # Cap confidence
        
        signal_strength = confidence * self.weight if direction != "HOLD" else 0.1
        
        # Create reasoning
        reasoning = f"Market regime: {overall_regime} trend, {volatility_regime} volatility"
        if regime_fit != 'neutral':
            reasoning += f", RTX {regime_fit} in regime"
        
        return {
            "signal_name": self.signal_name,
            "direction": direction,
            "strength": signal_strength,
            "confidence": confidence,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat(),
            "regime_data": {
                "overall_regime": overall_regime,
                "volatility_regime": volatility_regime,
                "risk_sentiment": risk_sentiment,
                "regime_strength": regime_strength,
                "rtx_regime_fit": regime_fit
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
            "status": "operational",
            "tracked_indices": self.market_indices
        } 
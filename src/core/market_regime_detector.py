"""
Market Regime Detection for RTX Options Strategy
Detects bull/bear/sideways markets to adapt strategy accordingly
Different market regimes require different approaches for options trading
"""
import asyncio
import logging
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    """Market regime classifications"""
    STRONG_BULL = "strong_bull"
    BULL = "bull"
    SIDEWAYS = "sideways"
    BEAR = "bear"
    STRONG_BEAR = "strong_bear"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"

@dataclass
class RegimeAnalysis:
    """Market regime analysis result"""
    current_regime: MarketRegime
    regime_strength: float  # 0-1, how strong the regime signal is
    regime_duration: int  # Days in current regime
    volatility_regime: MarketRegime  # Separate volatility classification
    trend_direction: float  # -1 to 1, overall trend
    confidence: float  # 0-1, confidence in regime classification
    supporting_indicators: Dict[str, float]
    regime_change_probability: float  # 0-1, likelihood of regime change soon
    optimal_strategy: str  # Strategy recommendation for current regime
    analysis_timestamp: datetime

class MarketRegimeDetector:
    """
    Detects market regimes for adaptive RTX options strategy
    
    Uses multiple indicators:
    - Price trends (moving averages)
    - Volatility patterns (VIX, historical vol)
    - Market breadth (sector performance)
    - Technical momentum
    
    Regime-Specific Strategy Adaptations:
    - Bull markets: Focus on call options, momentum plays
    - Bear markets: Focus on put options, mean reversion
    - Sideways: Iron condors, theta strategies
    - High vol: Sell premium, wait for vol collapse
    - Low vol: Buy options before vol expansion
    """
    
    def __init__(self):
        self.lookback_periods = [20, 50, 200]  # Days for trend analysis
        self.volatility_window = 20
        self.regime_cache = {}
        self.cache_duration = timedelta(hours=2)
        
        # Market indicators
        self.market_etfs = {
            'SPY': 'S&P 500',
            'QQQ': 'NASDAQ', 
            'IWM': 'Russell 2000',
            'VIX': 'Volatility Index'
        }
        
        self.sector_etfs = {
            'XLF': 'Financials',
            'XLK': 'Technology', 
            'XLE': 'Energy',
            'XLI': 'Industrials',
            'ITA': 'Aerospace & Defense'
        }
    
    async def get_market_data(self, symbols: List[str], period: str = "6mo") -> Dict[str, pd.DataFrame]:
        """Get market data for regime analysis"""
        try:
            data = {}
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period=period)
                    if not hist.empty:
                        data[symbol] = hist
                        logger.debug(f"Retrieved data for {symbol}: {len(hist)} days")
                    else:
                        logger.warning(f"No data for {symbol}")
                except Exception as e:
                    logger.warning(f"Error fetching {symbol}: {e}")
                    continue
            
            return data
        except Exception as e:
            logger.error(f"Error in get_market_data: {e}")
            return {}
    
    def calculate_trend_indicators(self, price_data: pd.Series) -> Dict[str, float]:
        """Calculate trend strength indicators"""
        indicators = {}
        
        try:
            # Moving average trends
            for period in self.lookback_periods:
                if len(price_data) >= period:
                    ma = price_data.rolling(window=period).mean()
                    current_price = price_data.iloc[-1]
                    ma_current = ma.iloc[-1]
                    
                    # Price vs MA
                    price_vs_ma = (current_price - ma_current) / ma_current
                    indicators[f'price_vs_ma_{period}'] = price_vs_ma
                    
                    # MA slope (trend direction)
                    if len(ma) >= 10:
                        ma_slope = (ma.iloc[-1] - ma.iloc[-10]) / ma.iloc[-10] / 10
                        indicators[f'ma_slope_{period}'] = ma_slope
            
            # Price momentum
            for period in [5, 10, 20]:
                if len(price_data) >= period:
                    momentum = (price_data.iloc[-1] - price_data.iloc[-period]) / price_data.iloc[-period]
                    indicators[f'momentum_{period}d'] = momentum
            
            # Trend consistency (how often price is above/below MA)
            if len(price_data) >= 20:
                ma20 = price_data.rolling(window=20).mean()
                above_ma = (price_data > ma20).astype(int)
                trend_consistency = above_ma.rolling(window=20).mean().iloc[-1]
                indicators['trend_consistency'] = trend_consistency * 2 - 1  # Scale to -1 to 1
            
            return indicators
            
        except Exception as e:
            logger.warning(f"Error calculating trend indicators: {e}")
            return {}
    
    def calculate_volatility_indicators(self, price_data: pd.Series, vix_data: Optional[pd.Series] = None) -> Dict[str, float]:
        """Calculate volatility regime indicators"""
        indicators = {}
        
        try:
            # Historical volatility
            returns = price_data.pct_change().dropna()
            
            if len(returns) >= self.volatility_window:
                # Current volatility
                current_vol = returns.tail(self.volatility_window).std() * np.sqrt(252)
                indicators['historical_vol'] = current_vol
                
                # Volatility percentile (vs last 6 months)
                if len(returns) >= 120:
                    vol_series = returns.rolling(window=self.volatility_window).std() * np.sqrt(252)
                    vol_percentile = (vol_series.iloc[-1] > vol_series.tail(120)).mean()
                    indicators['vol_percentile'] = vol_percentile
                
                # Volatility trend
                if len(returns) >= 40:
                    vol_recent = returns.tail(20).std() * np.sqrt(252)
                    vol_prior = returns.iloc[-40:-20].std() * np.sqrt(252)
                    vol_trend = (vol_recent - vol_prior) / vol_prior
                    indicators['vol_trend'] = vol_trend
            
            # VIX indicators
            if vix_data is not None and len(vix_data) > 0:
                current_vix = vix_data.iloc[-1]
                indicators['vix_level'] = current_vix
                
                # VIX percentile
                if len(vix_data) >= 120:
                    vix_percentile = (current_vix > vix_data.tail(120)).mean()
                    indicators['vix_percentile'] = vix_percentile
                
                # VIX vs historical average
                if len(vix_data) >= 50:
                    vix_avg = vix_data.tail(50).mean()
                    vix_vs_avg = (current_vix - vix_avg) / vix_avg
                    indicators['vix_vs_avg'] = vix_vs_avg
            
            return indicators
            
        except Exception as e:
            logger.warning(f"Error calculating volatility indicators: {e}")
            return {}
    
    def calculate_breadth_indicators(self, sector_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """Calculate market breadth indicators"""
        indicators = {}
        
        try:
            if not sector_data:
                return indicators
            
            # Sector momentum
            sector_momenta = []
            for symbol, data in sector_data.items():
                if len(data) >= 20:
                    momentum_20d = (data['Close'].iloc[-1] - data['Close'].iloc[-20]) / data['Close'].iloc[-20]
                    sector_momenta.append(momentum_20d)
            
            if sector_momenta:
                # Average sector momentum
                avg_sector_momentum = np.mean(sector_momenta)
                indicators['avg_sector_momentum'] = avg_sector_momentum
                
                # Sector breadth (% positive)
                positive_sectors = sum(1 for m in sector_momenta if m > 0) / len(sector_momenta)
                indicators['sector_breadth'] = positive_sectors
                
                # Sector dispersion
                sector_dispersion = np.std(sector_momenta)
                indicators['sector_dispersion'] = sector_dispersion
            
            return indicators
            
        except Exception as e:
            logger.warning(f"Error calculating breadth indicators: {e}")
            return {}
    
    def classify_trend_regime(self, trend_indicators: Dict[str, float]) -> Tuple[MarketRegime, float]:
        """Classify trend-based market regime"""
        
        # Aggregate trend signals
        bullish_signals = 0
        bearish_signals = 0
        signal_count = 0
        
        # Price vs moving averages
        for period in self.lookback_periods:
            key = f'price_vs_ma_{period}'
            if key in trend_indicators:
                value = trend_indicators[key]
                if value > 0.02:  # 2% above MA
                    bullish_signals += 1
                elif value < -0.02:  # 2% below MA
                    bearish_signals += 1
                signal_count += 1
        
        # Moving average slopes
        for period in self.lookback_periods:
            key = f'ma_slope_{period}'
            if key in trend_indicators:
                value = trend_indicators[key]
                if value > 0.001:  # Positive slope
                    bullish_signals += 1
                elif value < -0.001:  # Negative slope
                    bearish_signals += 1
                signal_count += 1
        
        # Momentum signals
        momentum_signals = []
        for period in [5, 10, 20]:
            key = f'momentum_{period}d'
            if key in trend_indicators:
                momentum_signals.append(trend_indicators[key])
        
        if momentum_signals:
            avg_momentum = np.mean(momentum_signals)
            if avg_momentum > 0.05:  # Strong positive momentum
                bullish_signals += 2
            elif avg_momentum > 0.02:  # Moderate positive
                bullish_signals += 1
            elif avg_momentum < -0.05:  # Strong negative
                bearish_signals += 2
            elif avg_momentum < -0.02:  # Moderate negative
                bearish_signals += 1
            signal_count += 2
        
        # Trend consistency
        if 'trend_consistency' in trend_indicators:
            consistency = trend_indicators['trend_consistency']
            if consistency > 0.6:  # Consistently above MA
                bullish_signals += 1
            elif consistency < -0.6:  # Consistently below MA
                bearish_signals += 1
            signal_count += 1
        
        # Determine regime
        if signal_count == 0:
            return MarketRegime.SIDEWAYS, 0.3
        
        bullish_ratio = bullish_signals / signal_count
        bearish_ratio = bearish_signals / signal_count
        
        confidence = max(bullish_ratio, bearish_ratio) - 0.5  # Convert to 0-0.5 range
        confidence = min(confidence * 2, 1.0)  # Scale to 0-1
        
        if bullish_ratio > 0.7:
            return MarketRegime.STRONG_BULL, confidence
        elif bullish_ratio > 0.55:
            return MarketRegime.BULL, confidence
        elif bearish_ratio > 0.7:
            return MarketRegime.STRONG_BEAR, confidence
        elif bearish_ratio > 0.55:
            return MarketRegime.BEAR, confidence
        else:
            return MarketRegime.SIDEWAYS, confidence
    
    def classify_volatility_regime(self, vol_indicators: Dict[str, float]) -> Tuple[MarketRegime, float]:
        """Classify volatility-based regime"""
        
        high_vol_signals = 0
        low_vol_signals = 0
        signal_count = 0
        
        # Historical volatility percentile
        if 'vol_percentile' in vol_indicators:
            vol_pct = vol_indicators['vol_percentile']
            if vol_pct > 0.8:  # 80th percentile
                high_vol_signals += 2
            elif vol_pct > 0.6:
                high_vol_signals += 1
            elif vol_pct < 0.2:  # 20th percentile
                low_vol_signals += 2
            elif vol_pct < 0.4:
                low_vol_signals += 1
            signal_count += 2
        
        # VIX level
        if 'vix_level' in vol_indicators:
            vix = vol_indicators['vix_level']
            if vix > 30:  # High fear
                high_vol_signals += 2
            elif vix > 20:
                high_vol_signals += 1
            elif vix < 15:  # Low fear
                low_vol_signals += 2
            elif vix < 18:
                low_vol_signals += 1
            signal_count += 2
        
        # VIX percentile
        if 'vix_percentile' in vol_indicators:
            vix_pct = vol_indicators['vix_percentile']
            if vix_pct > 0.8:
                high_vol_signals += 1
            elif vix_pct < 0.2:
                low_vol_signals += 1
            signal_count += 1
        
        # Volatility trend
        if 'vol_trend' in vol_indicators:
            vol_trend = vol_indicators['vol_trend']
            if vol_trend > 0.2:  # Rising volatility
                high_vol_signals += 1
            elif vol_trend < -0.2:  # Falling volatility
                low_vol_signals += 1
            signal_count += 1
        
        # Determine regime
        if signal_count == 0:
            return MarketRegime.SIDEWAYS, 0.3
        
        high_vol_ratio = high_vol_signals / signal_count
        low_vol_ratio = low_vol_signals / signal_count
        
        confidence = max(high_vol_ratio, low_vol_ratio) - 0.5
        confidence = min(confidence * 2, 1.0)
        
        if high_vol_ratio > 0.6:
            return MarketRegime.HIGH_VOLATILITY, confidence
        elif low_vol_ratio > 0.6:
            return MarketRegime.LOW_VOLATILITY, confidence
        else:
            return MarketRegime.SIDEWAYS, confidence
    
    def estimate_regime_duration(self, price_data: pd.Series, current_regime: MarketRegime) -> int:
        """Estimate how long current regime has been in place"""
        
        try:
            if len(price_data) < 20:
                return 1
            
            # Simple regime detection based on MA20
            ma20 = price_data.rolling(window=20).mean()
            price_above_ma = price_data > ma20
            
            # Count consecutive days in current state
            if current_regime in [MarketRegime.BULL, MarketRegime.STRONG_BULL]:
                # Count days above MA
                consecutive_days = 0
                for i in range(len(price_above_ma) - 1, -1, -1):
                    if price_above_ma.iloc[i]:
                        consecutive_days += 1
                    else:
                        break
            elif current_regime in [MarketRegime.BEAR, MarketRegime.STRONG_BEAR]:
                # Count days below MA
                consecutive_days = 0
                for i in range(len(price_above_ma) - 1, -1, -1):
                    if not price_above_ma.iloc[i]:
                        consecutive_days += 1
                    else:
                        break
            else:
                # Sideways - look for volatility patterns
                consecutive_days = 10  # Default assumption
            
            return max(1, consecutive_days)
            
        except Exception as e:
            logger.warning(f"Error estimating regime duration: {e}")
            return 1
    
    def calculate_regime_change_probability(self, trend_indicators: Dict[str, float], 
                                         vol_indicators: Dict[str, float],
                                         regime_duration: int) -> float:
        """Estimate probability of regime change"""
        
        change_probability = 0.1  # Base probability
        
        try:
            # Momentum divergence
            if 'momentum_5d' in trend_indicators and 'momentum_20d' in trend_indicators:
                short_momentum = trend_indicators['momentum_5d']
                long_momentum = trend_indicators['momentum_20d']
                
                # If short and long momentum diverge, change is more likely
                momentum_divergence = abs(short_momentum - long_momentum)
                change_probability += momentum_divergence * 0.5
            
            # Volatility spikes often signal regime changes
            if 'vol_trend' in vol_indicators:
                vol_trend = abs(vol_indicators['vol_trend'])
                change_probability += vol_trend * 0.3
            
            # Regime duration (longer regimes more likely to change)
            if regime_duration > 30:  # More than a month
                duration_factor = min((regime_duration - 30) / 60, 0.3)  # Cap at 30%
                change_probability += duration_factor
            
            # VIX spikes
            if 'vix_vs_avg' in vol_indicators:
                vix_spike = max(0, vol_indicators['vix_vs_avg'])
                change_probability += vix_spike * 0.2
            
            # Cap probability
            change_probability = min(change_probability, 0.8)
            
            return change_probability
            
        except Exception as e:
            logger.warning(f"Error calculating regime change probability: {e}")
            return 0.1
    
    def get_optimal_strategy(self, regime: MarketRegime, vol_regime: MarketRegime) -> str:
        """Get optimal trading strategy for current regime"""
        
        # Trend-based strategies
        if regime == MarketRegime.STRONG_BULL:
            if vol_regime == MarketRegime.LOW_VOLATILITY:
                return "Buy calls on dips, hold longer"
            else:
                return "Buy ATM calls, quick scalps"
        
        elif regime == MarketRegime.BULL:
            if vol_regime == MarketRegime.LOW_VOLATILITY:
                return "Buy slightly OTM calls"
            else:
                return "Sell puts, buy call spreads"
        
        elif regime == MarketRegime.STRONG_BEAR:
            if vol_regime == MarketRegime.LOW_VOLATILITY:
                return "Buy puts on bounces"
            else:
                return "Buy ATM puts, quick scalps"
        
        elif regime == MarketRegime.BEAR:
            if vol_regime == MarketRegime.LOW_VOLATILITY:
                return "Buy slightly OTM puts"
            else:
                return "Sell calls, buy put spreads"
        
        elif regime == MarketRegime.SIDEWAYS:
            if vol_regime == MarketRegime.HIGH_VOLATILITY:
                return "Sell strangles, iron condors"
            elif vol_regime == MarketRegime.LOW_VOLATILITY:
                return "Buy straddles before vol expansion"
            else:
                return "Range trading, theta strategies"
        
        # Volatility-specific overrides
        if vol_regime == MarketRegime.HIGH_VOLATILITY:
            return "Sell premium, avoid long options"
        elif vol_regime == MarketRegime.LOW_VOLATILITY:
            return "Buy options before vol expansion"
        
        return "Wait for clearer signals"
    
    async def detect_regime(self, symbol: str = "RTX") -> Optional[RegimeAnalysis]:
        """Main regime detection method"""
        
        try:
            logger.info(f"Detecting market regime for {symbol}")
            
            # Get market data
            all_symbols = [symbol] + list(self.market_etfs.keys()) + list(self.sector_etfs.keys())
            data = await self.get_market_data(all_symbols)
            
            if symbol not in data or len(data[symbol]) < 50:
                logger.error(f"Insufficient data for {symbol}")
                return None
            
            # Primary asset data
            primary_data = data[symbol]['Close']
            
            # Calculate indicators
            trend_indicators = self.calculate_trend_indicators(primary_data)
            
            # VIX data for volatility analysis
            vix_data = data.get('VIX', {}).get('Close') if 'VIX' in data else None
            vol_indicators = self.calculate_volatility_indicators(primary_data, vix_data)
            
            # Sector data for breadth
            sector_data = {k: v for k, v in data.items() if k in self.sector_etfs}
            breadth_indicators = self.calculate_breadth_indicators(sector_data)
            
            # Classify regimes
            trend_regime, trend_confidence = self.classify_trend_regime(trend_indicators)
            vol_regime, vol_confidence = self.classify_volatility_regime(vol_indicators)
            
            # Overall confidence (weighted average)
            overall_confidence = (trend_confidence * 0.7 + vol_confidence * 0.3)
            
            # Regime duration
            regime_duration = self.estimate_regime_duration(primary_data, trend_regime)
            
            # Regime change probability
            change_probability = self.calculate_regime_change_probability(
                trend_indicators, vol_indicators, regime_duration
            )
            
            # Trend direction
            trend_direction = 0
            if 'momentum_20d' in trend_indicators:
                trend_direction = np.tanh(trend_indicators['momentum_20d'] * 10)  # Scale to -1,1
            
            # Optimal strategy
            optimal_strategy = self.get_optimal_strategy(trend_regime, vol_regime)
            
            # Combine all indicators
            supporting_indicators = {**trend_indicators, **vol_indicators, **breadth_indicators}
            
            analysis = RegimeAnalysis(
                current_regime=trend_regime,
                regime_strength=trend_confidence,
                regime_duration=regime_duration,
                volatility_regime=vol_regime,
                trend_direction=trend_direction,
                confidence=overall_confidence,
                supporting_indicators=supporting_indicators,
                regime_change_probability=change_probability,
                optimal_strategy=optimal_strategy,
                analysis_timestamp=datetime.now()
            )
            
            logger.info(f"Regime detected: {trend_regime.value} (confidence: {overall_confidence:.2f}), "
                       f"Vol: {vol_regime.value}, Strategy: {optimal_strategy}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in regime detection: {e}")
            return None

# Example usage
async def main():
    """Test the market regime detector"""
    detector = MarketRegimeDetector()
    
    analysis = await detector.detect_regime("RTX")
    
    if analysis:
        print("=== Market Regime Analysis ===")
        print(f"Primary Regime: {analysis.current_regime.value}")
        print(f"Regime Strength: {analysis.regime_strength:.2f}")
        print(f"Regime Duration: {analysis.regime_duration} days")
        print(f"Volatility Regime: {analysis.volatility_regime.value}")
        print(f"Trend Direction: {analysis.trend_direction:.2f}")
        print(f"Overall Confidence: {analysis.confidence:.2f}")
        print(f"Change Probability: {analysis.regime_change_probability:.2f}")
        print(f"Optimal Strategy: {analysis.optimal_strategy}")
        
        print("\n=== Key Indicators ===")
        for key, value in analysis.supporting_indicators.items():
            print(f"{key}: {value:.4f}")
    else:
        print("Failed to detect market regime")

if __name__ == "__main__":
    asyncio.run(main())
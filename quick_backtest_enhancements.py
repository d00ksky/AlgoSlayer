#!/usr/bin/env python3
"""
Quick Backtest Enhancements - Immediate Improvements
Can be implemented in 1-2 hours for instant benefits
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import ta  # Technical Analysis library

class EnhancedSignalGenerator:
    """Enhanced signals with more sophisticated indicators"""
    
    def __init__(self):
        self.signal_weights = {
            'technical_analysis': 0.12,
            'momentum': 0.10,
            'volatility': 0.08,
            'news_sentiment': 0.05,
            'options_flow': 0.09,
            'market_regime': 0.08,
            'sector_correlation': 0.06,
            'mean_reversion': 0.07,
            'iv_percentile': 0.11,
            'earnings': 0.05,
            # New signals
            'smart_money': 0.08,
            'dark_pool': 0.06,
            'put_call_ratio': 0.05
        }
    
    def generate_enhanced_signals(self, data: pd.DataFrame, current_date: datetime) -> Dict:
        """Generate more sophisticated trading signals"""
        recent_data = data[data.index <= current_date].tail(50)
        
        if len(recent_data) < 20:
            return {}
        
        signals = {}
        current_price = recent_data['Close'].iloc[-1]
        
        # Enhanced Technical Analysis
        signals['technical_analysis'] = self._enhanced_technical_signal(recent_data)
        
        # Smart Money Flow
        signals['smart_money'] = self._smart_money_signal(recent_data)
        
        # Options Flow Analysis
        signals['put_call_ratio'] = self._put_call_ratio_signal(recent_data)
        
        # Dark Pool Activity
        signals['dark_pool'] = self._dark_pool_signal(recent_data)
        
        # Enhanced Volatility
        signals['volatility'] = self._enhanced_volatility_signal(recent_data)
        
        # Market Microstructure
        signals['microstructure'] = self._microstructure_signal(recent_data)
        
        return signals
    
    def _enhanced_technical_signal(self, data: pd.DataFrame) -> Dict:
        """Enhanced technical analysis with multiple indicators"""
        close = data['Close']
        high = data['High']
        low = data['Low']
        volume = data['Volume']
        
        # Calculate indicators
        rsi = ta.momentum.RSIIndicator(close).rsi().iloc[-1]
        macd = ta.trend.MACD(close)
        macd_signal = macd.macd_signal().iloc[-1]
        macd_diff = macd.macd_diff().iloc[-1]
        
        bb = ta.volatility.BollingerBands(close)
        bb_high = bb.bollinger_hband().iloc[-1]
        bb_low = bb.bollinger_lband().iloc[-1]
        bb_width = (bb_high - bb_low) / close.iloc[-1]
        
        # Stochastic
        stoch = ta.momentum.StochasticOscillator(high, low, close)
        stoch_k = stoch.stoch().iloc[-1]
        
        # ADX for trend strength
        adx = ta.trend.ADXIndicator(high, low, close)
        adx_value = adx.adx().iloc[-1] if not adx.adx().empty else 25
        
        # Combine signals
        score = 0
        
        # RSI signals
        if rsi < 30:
            score += 0.2  # Oversold
        elif rsi > 70:
            score -= 0.2  # Overbought
        else:
            score += 0.1  # Neutral is good
            
        # MACD signals
        if macd_diff > 0:
            score += 0.15
            
        # Bollinger Bands
        price_position = (close.iloc[-1] - bb_low) / (bb_high - bb_low)
        if 0.2 < price_position < 0.8:
            score += 0.1  # Price in middle of bands
            
        # Trend strength
        if adx_value > 25:
            score += 0.15  # Strong trend
            
        # Volume confirmation
        vol_sma = volume.rolling(20).mean().iloc[-1]
        if volume.iloc[-1] > vol_sma * 1.2:
            score += 0.1  # Volume spike
            
        confidence = min(0.9, max(0.1, score + 0.5))
        
        return {
            'confidence': confidence,
            'direction': 'bullish' if score > 0 else 'bearish',
            'indicators': {
                'rsi': rsi,
                'macd_diff': macd_diff,
                'bb_width': bb_width,
                'adx': adx_value,
                'stoch_k': stoch_k
            }
        }
    
    def _smart_money_signal(self, data: pd.DataFrame) -> Dict:
        """Detect smart money movements"""
        close = data['Close']
        volume = data['Volume']
        
        # Large volume with small price movement = accumulation
        price_change = close.pct_change().iloc[-5:].mean()
        volume_spike = volume.iloc[-1] / volume.rolling(20).mean().iloc[-1]
        
        # On-Balance Volume divergence
        obv = ta.volume.OnBalanceVolumeIndicator(close, volume).on_balance_volume()
        obv_slope = np.polyfit(range(10), obv.iloc[-10:].values, 1)[0]
        price_slope = np.polyfit(range(10), close.iloc[-10:].values, 1)[0]
        
        divergence = (obv_slope > 0 and price_slope < 0) or (obv_slope < 0 and price_slope > 0)
        
        confidence = 0.5
        if volume_spike > 2 and abs(price_change) < 0.01:
            confidence += 0.3  # Accumulation
        if divergence:
            confidence += 0.2  # OBV divergence
            
        return {
            'confidence': min(0.9, confidence),
            'direction': 'bullish' if obv_slope > 0 else 'bearish',
            'volume_spike': volume_spike,
            'divergence': divergence
        }
    
    def _put_call_ratio_signal(self, data: pd.DataFrame) -> Dict:
        """Simulate put/call ratio (in real implementation, use actual options data)"""
        # Simulate based on price action and volatility
        close = data['Close']
        returns = close.pct_change()
        
        # Falling prices typically increase put/call ratio
        recent_return = returns.iloc[-5:].mean()
        volatility = returns.iloc[-20:].std()
        
        # Simulate P/C ratio (normally 0.7-1.3)
        simulated_pc_ratio = 1.0 - recent_return * 10
        simulated_pc_ratio = max(0.5, min(1.5, simulated_pc_ratio))
        
        # Extreme readings are contrarian indicators
        confidence = 0.5
        if simulated_pc_ratio > 1.2:  # High fear
            confidence = 0.7
            direction = 'bullish'  # Contrarian
        elif simulated_pc_ratio < 0.8:  # High greed
            confidence = 0.7
            direction = 'bearish'  # Contrarian
        else:
            direction = 'neutral'
            
        return {
            'confidence': confidence,
            'direction': direction,
            'pc_ratio': simulated_pc_ratio
        }
    
    def _dark_pool_signal(self, data: pd.DataFrame) -> Dict:
        """Simulate dark pool activity"""
        volume = data['Volume']
        close = data['Close']
        
        # Large trades with minimal price impact suggest dark pool
        volume_blocks = volume.iloc[-1] // 10000  # Block trades
        price_stability = close.iloc[-5:].std() / close.iloc[-1]
        
        # High volume + low volatility = potential dark pool accumulation
        if volume_blocks > volume.rolling(20).mean().iloc[-1] // 10000:
            if price_stability < 0.01:
                confidence = 0.8
                direction = 'bullish'
            else:
                confidence = 0.6
                direction = 'neutral'
        else:
            confidence = 0.5
            direction = 'neutral'
            
        return {
            'confidence': confidence,
            'direction': direction,
            'block_trades': volume_blocks
        }
    
    def _enhanced_volatility_signal(self, data: pd.DataFrame) -> Dict:
        """Enhanced volatility analysis"""
        close = data['Close']
        high = data['High']
        low = data['Low']
        
        # ATR
        atr = ta.volatility.AverageTrueRange(high, low, close).average_true_range()
        current_atr = atr.iloc[-1]
        atr_percentile = (atr.iloc[-20:] < current_atr).sum() / 20
        
        # Keltner Channels
        kc = ta.volatility.KeltnerChannel(high, low, close)
        kc_high = kc.keltner_channel_hband().iloc[-1]
        kc_low = kc.keltner_channel_lband().iloc[-1]
        
        # Price position in channel
        price_position = (close.iloc[-1] - kc_low) / (kc_high - kc_low)
        
        # Historical Volatility
        returns = close.pct_change()
        hv_20 = returns.iloc[-20:].std() * np.sqrt(252)
        hv_60 = returns.iloc[-60:].std() * np.sqrt(252)
        vol_trend = hv_20 / hv_60 if hv_60 > 0 else 1
        
        confidence = 0.5
        if atr_percentile > 0.8:  # High volatility
            confidence = 0.7
            if vol_trend > 1.2:  # Expanding volatility
                confidence = 0.8
                
        return {
            'confidence': confidence,
            'direction': 'high_vol' if atr_percentile > 0.7 else 'low_vol',
            'atr_percentile': atr_percentile,
            'vol_trend': vol_trend,
            'kc_position': price_position
        }
    
    def _microstructure_signal(self, data: pd.DataFrame) -> Dict:
        """Market microstructure analysis"""
        close = data['Close']
        high = data['High'] 
        low = data['Low']
        volume = data['Volume']
        
        # Spread proxy (high-low as % of close)
        spread = ((high - low) / close).iloc[-5:].mean()
        
        # Volume-weighted average price
        vwap = (close * volume).rolling(20).sum() / volume.rolling(20).sum()
        vwap_deviation = (close.iloc[-1] - vwap.iloc[-1]) / vwap.iloc[-1]
        
        # Efficiency ratio (directional movement / total movement)
        net_change = abs(close.iloc[-1] - close.iloc[-10])
        total_movement = (close.diff().abs()).iloc[-10:].sum()
        efficiency = net_change / total_movement if total_movement > 0 else 0
        
        confidence = 0.5
        if efficiency > 0.6:  # Strong directional movement
            confidence += 0.2
        if abs(vwap_deviation) < 0.01:  # Near VWAP
            confidence += 0.1
        if spread < 0.002:  # Tight spread
            confidence += 0.1
            
        direction = 'bullish' if vwap_deviation > 0 else 'bearish'
        
        return {
            'confidence': min(0.9, confidence),
            'direction': direction,
            'efficiency': efficiency,
            'vwap_deviation': vwap_deviation,
            'spread': spread
        }

class EnhancedExitStrategies:
    """More sophisticated exit strategies"""
    
    @staticmethod
    def trailing_stop_loss(entry_price: float, current_price: float, 
                          high_water_mark: float, strategy: str) -> Tuple[bool, str]:
        """Dynamic trailing stop based on profit level"""
        profit_pct = (current_price - entry_price) / entry_price
        
        # Strategy-specific trailing stops
        trailing_pcts = {
            'aggressive': {10: 0.05, 25: 0.10, 50: 0.15, 100: 0.20},
            'conservative': {25: 0.10, 50: 0.15, 100: 0.20, 200: 0.25},
            'scalping': {5: 0.02, 10: 0.05, 25: 0.10, 50: 0.15}
        }
        
        strategy_trails = trailing_pcts.get(strategy, trailing_pcts['conservative'])
        
        # Find appropriate trailing stop
        trailing_pct = 0
        for profit_threshold, trail_pct in sorted(strategy_trails.items()):
            if profit_pct * 100 >= profit_threshold:
                trailing_pct = trail_pct
                
        if trailing_pct > 0:
            stop_price = high_water_mark * (1 - trailing_pct)
            if current_price <= stop_price:
                return True, f"trailing_stop_{int(trailing_pct*100)}pct"
                
        return False, None
    
    @staticmethod
    def volatility_exit(entry_iv: float, current_iv: float, 
                       days_held: int) -> Tuple[bool, str]:
        """Exit based on volatility changes"""
        iv_change = (current_iv - entry_iv) / entry_iv
        
        # IV expansion exit
        if iv_change > 0.5 and days_held > 2:
            return True, "iv_expansion_exit"
            
        # IV crush exit (for long volatility strategies)
        if iv_change < -0.3 and days_held > 1:
            return True, "iv_crush_exit"
            
        return False, None
    
    @staticmethod
    def time_decay_exit(days_to_expiry: int, profit_pct: float, 
                       strategy: str) -> Tuple[bool, str]:
        """Exit based on time decay considerations"""
        # Strategy-specific time decay thresholds
        if strategy in ['scalping', 'aggressive']:
            if days_to_expiry <= 3 and profit_pct < 0.2:
                return True, "gamma_risk_exit"
                
        if days_to_expiry <= 7:
            if profit_pct < 0:
                return True, "theta_decay_exit"
            elif profit_pct < 0.1:
                return True, "insufficient_profit_exit"
                
        return False, None
    
    @staticmethod
    def pattern_based_exit(price_history: pd.Series, 
                          entry_price: float) -> Tuple[bool, str]:
        """Exit based on price patterns"""
        if len(price_history) < 10:
            return False, None
            
        recent_prices = price_history.iloc[-10:]
        
        # Double top detection
        peaks = recent_prices[recent_prices == recent_prices.rolling(3, center=True).max()]
        if len(peaks) >= 2:
            if abs(peaks.iloc[-1] - peaks.iloc[-2]) / peaks.iloc[-1] < 0.02:
                if recent_prices.iloc[-1] < peaks.iloc[-1] * 0.98:
                    return True, "double_top_exit"
                    
        # Support break
        support = recent_prices.rolling(20).min().iloc[-1]
        if recent_prices.iloc[-1] < support * 0.98:
            return True, "support_break_exit"
            
        return False, None

class EnhancedMLFeatures:
    """Generate more sophisticated features for ML"""
    
    @staticmethod
    def create_advanced_features(trade_data: pd.DataFrame) -> pd.DataFrame:
        """Create advanced features for ML training"""
        features = trade_data.copy()
        
        # Interaction features
        features['confidence_x_moneyness'] = features['confidence'] * features['moneyness']
        features['iv_x_dte'] = features['implied_volatility'] * features['days_to_expiry']
        features['moneyness_x_dte'] = features['moneyness'] * features['days_to_expiry']
        
        # Polynomial features
        features['confidence_squared'] = features['confidence'] ** 2
        features['moneyness_squared'] = features['moneyness'] ** 2
        
        # Categorical encodings
        features['deep_otm'] = (features['moneyness'] < 0.95).astype(int)
        features['near_atm'] = ((features['moneyness'] > 0.97) & 
                               (features['moneyness'] < 1.03)).astype(int)
        features['deep_itm'] = (features['moneyness'] > 1.05).astype(int)
        
        # Time-based features
        features['dte_bins'] = pd.cut(features['days_to_expiry'], 
                                     bins=[0, 7, 21, 45, 100], 
                                     labels=['very_short', 'short', 'medium', 'long'])
        
        # Signal quality features
        features['signal_strength'] = features[
            ['technical_confidence', 'momentum_confidence', 
             'volatility_confidence', 'mean_reversion_confidence']
        ].mean(axis=1)
        
        features['signal_agreement_ratio'] = features['signal_agreement'] / 10
        
        # Historical performance features (would need historical data)
        # features['strategy_recent_winrate'] = ...
        # features['strategy_recent_sharpe'] = ...
        
        return features

# Example usage
if __name__ == "__main__":
    print("Enhanced Backtest Components Ready!")
    print("\nNew Features:")
    print("1. Enhanced Signal Generator with 13 signals")
    print("2. Sophisticated exit strategies")
    print("3. Advanced ML feature engineering")
    print("\nTo integrate these enhancements:")
    print("1. Import classes into historical_backtester.py")
    print("2. Replace signal generation with EnhancedSignalGenerator")
    print("3. Add new exit strategies to _simulate_trade_exit")
    print("4. Use EnhancedMLFeatures in BacktestMLIntegrator")
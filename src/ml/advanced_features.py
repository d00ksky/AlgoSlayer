#!/usr/bin/env python3
"""
Advanced Feature Engineering for AlgoSlayer Trading System
Phase 1: Enhanced features for better ML performance

This module creates sophisticated features from basic trading data
to improve model accuracy from 90% to 92%+
"""
import numpy as np
import pandas as pd
from datetime import datetime, time
import json
import yfinance as yf
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

class AdvancedFeatureEngineer:
    """
    Advanced feature engineering for RTX options predictions
    Transforms basic signals into rich feature set for ML training
    """
    
    def __init__(self):
        self.spy_data = None
        self.vix_data = None
        self.ita_data = None  # Defense ETF
        self.dxy_data = None  # Dollar index
        self.cache_external_data()
    
    def cache_external_data(self):
        """Cache external market data for feature generation"""
        try:
            logger.info("📊 Caching external market data...")
            
            # Download market data (last 30 days for features)
            tickers = ['SPY', '^VIX', 'ITA', 'DX-Y.NYB']
            for ticker in tickers:
                try:
                    data = yf.download(ticker, period='30d', interval='1d', progress=False)
                    if not data.empty:
                        if ticker == 'SPY':
                            self.spy_data = data
                        elif ticker == '^VIX':
                            self.vix_data = data
                        elif ticker == 'ITA':
                            self.ita_data = data
                        elif ticker == 'DX-Y.NYB':
                            self.dxy_data = data
                except Exception as e:
                    logger.warning(f"⚠️ Could not fetch {ticker}: {e}")
            
            logger.success("✅ External data cached successfully")
        except Exception as e:
            logger.error(f"❌ Failed to cache external data: {e}")
    
    def engineer_features(self, df):
        """
        Main feature engineering pipeline
        Input: DataFrame with basic prediction data
        Output: DataFrame with advanced features
        """
        logger.info("🔧 Engineering advanced features...")
        
        features = []
        
        for idx, row in df.iterrows():
            try:
                feature_dict = self.create_base_features(row)
                
                # Add time-based features
                feature_dict.update(self.create_time_features(row))
                
                # Add market structure features
                feature_dict.update(self.create_market_features(row))
                
                # Add technical features
                feature_dict.update(self.create_technical_features(row, df, idx))
                
                # Add signal interaction features
                feature_dict.update(self.create_signal_interactions(row))
                
                # Add volatility features
                feature_dict.update(self.create_volatility_features(row))
                
                # Add cross-asset features
                feature_dict.update(self.create_cross_asset_features(row))
                
                features.append(feature_dict)
                
            except Exception as e:
                logger.warning(f"⚠️ Error processing row {idx}: {e}")
                # Create minimal feature dict on error
                features.append(self.create_base_features(row))
        
        result_df = pd.DataFrame(features).fillna(0)
        logger.success(f"✅ Created {len(result_df.columns)} advanced features")
        return result_df
    
    def create_base_features(self, row):
        """Create basic features from original data"""
        return {
            'confidence': row.get('confidence', 0),
            'expected_move': row.get('expected_move', 0),
            'prediction_id': row.get('prediction_id', 0)
        }
    
    def create_time_features(self, row):
        """Create time-based features"""
        try:
            timestamp = pd.to_datetime(row['timestamp'])
            
            # Market timing features
            market_open = time(9, 30)  # 9:30 AM ET
            market_close = time(16, 0)  # 4:00 PM ET
            current_time = timestamp.time()
            
            # Calculate minutes from market open/close
            minutes_from_open = self._minutes_between_times(market_open, current_time)
            minutes_to_close = self._minutes_between_times(current_time, market_close)
            
            return {
                'hour': timestamp.hour,
                'minute': timestamp.minute,
                'day_of_week': timestamp.dayofweek,
                'day_of_month': timestamp.day,
                'week_of_year': timestamp.isocalendar()[1],
                'month': timestamp.month,
                'quarter': timestamp.quarter,
                
                # Market session features
                'minutes_from_open': max(0, minutes_from_open),
                'minutes_to_close': max(0, minutes_to_close),
                'is_market_open': 1 if market_open <= current_time <= market_close else 0,
                'is_opening_hour': 1 if 9 <= timestamp.hour <= 10 else 0,
                'is_closing_hour': 1 if 15 <= timestamp.hour <= 16 else 0,
                'is_lunch_time': 1 if 12 <= timestamp.hour <= 13 else 0,
                
                # Day patterns
                'is_monday': 1 if timestamp.dayofweek == 0 else 0,
                'is_tuesday': 1 if timestamp.dayofweek == 1 else 0,
                'is_wednesday': 1 if timestamp.dayofweek == 2 else 0,
                'is_thursday': 1 if timestamp.dayofweek == 3 else 0,
                'is_friday': 1 if timestamp.dayofweek == 4 else 0,
                'is_weekend': 1 if timestamp.dayofweek >= 5 else 0,
                
                # End of month/quarter effects
                'is_month_end': 1 if timestamp.day >= 28 else 0,
                'is_quarter_end': 1 if (timestamp.month % 3 == 0 and timestamp.day >= 28) else 0,
            }
        except Exception as e:
            logger.warning(f"⚠️ Error creating time features: {e}")
            return {'hour': 12, 'day_of_week': 2}  # Default values
    
    def create_market_features(self, row):
        """Create market microstructure features"""
        try:
            # Market regime features
            vix_level = self._get_current_vix()
            
            return {
                # Volatility regime
                'vix_level': vix_level,
                'vix_regime_low': 1 if vix_level < 15 else 0,
                'vix_regime_normal': 1 if 15 <= vix_level <= 25 else 0,
                'vix_regime_high': 1 if vix_level > 25 else 0,
                'vix_regime_crisis': 1 if vix_level > 40 else 0,
                
                # Market structure
                'confidence_squared': row.get('confidence', 0) ** 2,
                'confidence_cubed': row.get('confidence', 0) ** 3,
                'expected_move_squared': row.get('expected_move', 0) ** 2,
                
                # Risk-on/Risk-off proxy
                'risk_on_regime': 1 if vix_level < 20 else 0,
                'risk_off_regime': 1 if vix_level > 30 else 0,
            }
        except Exception as e:
            logger.warning(f"⚠️ Error creating market features: {e}")
            return {'vix_level': 20, 'vix_regime_normal': 1}
    
    def create_technical_features(self, row, df, current_idx):
        """Create technical analysis features"""
        try:
            # Get historical context (last 20 predictions)
            start_idx = max(0, current_idx - 20)
            historical_data = df.iloc[start_idx:current_idx + 1]
            
            if len(historical_data) < 2:
                return {'recent_confidence_mean': row.get('confidence', 0)}
            
            # Rolling statistics on confidence
            confidences = historical_data['confidence'].values
            expected_moves = historical_data['expected_move'].values
            
            return {
                # Rolling confidence features
                'recent_confidence_mean': np.mean(confidences[-5:]) if len(confidences) >= 5 else np.mean(confidences),
                'recent_confidence_std': np.std(confidences[-5:]) if len(confidences) >= 5 else 0,
                'confidence_trend': self._calculate_trend(confidences[-5:]) if len(confidences) >= 5 else 0,
                'confidence_momentum': confidences[-1] - np.mean(confidences[:-1]) if len(confidences) > 1 else 0,
                
                # Rolling expected move features
                'recent_expected_move_mean': np.mean(expected_moves[-5:]) if len(expected_moves) >= 5 else np.mean(expected_moves),
                'recent_expected_move_std': np.std(expected_moves[-5:]) if len(expected_moves) >= 5 else 0,
                'expected_move_trend': self._calculate_trend(expected_moves[-5:]) if len(expected_moves) >= 5 else 0,
                
                # Pattern recognition
                'confidence_above_recent_mean': 1 if row.get('confidence', 0) > np.mean(confidences[-10:]) else 0,
                'confidence_in_top_quartile': 1 if row.get('confidence', 0) > np.percentile(confidences, 75) else 0,
                'confidence_in_bottom_quartile': 1 if row.get('confidence', 0) < np.percentile(confidences, 25) else 0,
                
                # Momentum indicators
                'confidence_acceleration': self._calculate_acceleration(confidences[-3:]) if len(confidences) >= 3 else 0,
                'expected_move_acceleration': self._calculate_acceleration(expected_moves[-3:]) if len(expected_moves) >= 3 else 0,
            }
        except Exception as e:
            logger.warning(f"⚠️ Error creating technical features: {e}")
            return {'recent_confidence_mean': row.get('confidence', 0)}
    
    def create_signal_interactions(self, row):
        """Create features from signal interactions"""
        try:
            signal_data = json.loads(row['signal_data']) if row.get('signal_data') else {}
            
            # Extract signal confidences and directions
            signals = {}
            for signal_name, signal_info in signal_data.items():
                if isinstance(signal_info, dict):
                    signals[signal_name] = {
                        'confidence': signal_info.get('confidence', 0),
                        'direction': signal_info.get('direction', 'HOLD'),
                        'strength': signal_info.get('strength', 0)
                    }
            
            # Signal agreement features
            buy_signals = sum(1 for s in signals.values() if s['direction'] == 'BUY')
            sell_signals = sum(1 for s in signals.values() if s['direction'] == 'SELL')
            total_signals = len(signals)
            
            # Signal strength combinations
            technical_conf = signals.get('technical_analysis', {}).get('confidence', 0)
            momentum_conf = signals.get('momentum', {}).get('confidence', 0)
            news_conf = signals.get('news_sentiment', {}).get('confidence', 0)
            
            return {
                # Signal consensus
                'signal_agreement_ratio': (max(buy_signals, sell_signals) / max(total_signals, 1)),
                'buy_signal_count': buy_signals,
                'sell_signal_count': sell_signals,
                'neutral_signal_count': total_signals - buy_signals - sell_signals,
                'total_active_signals': total_signals,
                
                # Signal strength interactions
                'tech_momentum_product': technical_conf * momentum_conf,
                'tech_news_product': technical_conf * news_conf,
                'momentum_news_product': momentum_conf * news_conf,
                'top3_signals_avg': np.mean(sorted([technical_conf, momentum_conf, news_conf], reverse=True)),
                
                # Signal divergence detection
                'signal_divergence': np.std([s['confidence'] for s in signals.values()]) if signals else 0,
                'max_signal_confidence': max([s['confidence'] for s in signals.values()]) if signals else 0,
                'min_signal_confidence': min([s['confidence'] for s in signals.values()]) if signals else 0,
                
                # Specific signal combinations
                'bullish_momentum_tech': 1 if (technical_conf > 0.7 and momentum_conf > 0.7 and 
                                               signals.get('technical_analysis', {}).get('direction') == 'BUY' and
                                               signals.get('momentum', {}).get('direction') == 'BUY') else 0,
                
                'bearish_momentum_tech': 1 if (technical_conf > 0.7 and momentum_conf > 0.7 and 
                                               signals.get('technical_analysis', {}).get('direction') == 'SELL' and
                                               signals.get('momentum', {}).get('direction') == 'SELL') else 0,
            }
        except Exception as e:
            logger.warning(f"⚠️ Error creating signal interaction features: {e}")
            return {'signal_agreement_ratio': 0.5, 'total_active_signals': 0}
    
    def create_volatility_features(self, row):
        """Create volatility-based features"""
        try:
            expected_move = row.get('expected_move', 0)
            confidence = row.get('confidence', 0)
            
            return {
                # Volatility metrics
                'expected_move_normalized': min(expected_move / 0.05, 5),  # Normalize to 5% max
                'volatility_confidence_ratio': expected_move * confidence if expected_move > 0 else 0,
                'low_volatility_high_confidence': 1 if (expected_move < 0.02 and confidence > 0.8) else 0,
                'high_volatility_low_confidence': 1 if (expected_move > 0.04 and confidence < 0.6) else 0,
                
                # Expected move categories
                'expected_move_tiny': 1 if expected_move < 0.01 else 0,
                'expected_move_small': 1 if 0.01 <= expected_move < 0.02 else 0,
                'expected_move_medium': 1 if 0.02 <= expected_move < 0.04 else 0,
                'expected_move_large': 1 if expected_move >= 0.04 else 0,
                
                # Volatility regime features
                'vol_regime_expansion': 1 if expected_move > 0.03 else 0,
                'vol_regime_contraction': 1 if expected_move < 0.015 else 0,
            }
        except Exception as e:
            logger.warning(f"⚠️ Error creating volatility features: {e}")
            return {'expected_move_normalized': 0}
    
    def create_cross_asset_features(self, row):
        """Create features from other assets"""
        try:
            # Get current market data
            spy_return = self._get_recent_return('SPY')
            ita_return = self._get_recent_return('ITA')  # Defense ETF
            vix_change = self._get_recent_vix_change()
            dxy_return = self._get_recent_return('DXY')
            
            return {
                # Market correlation features
                'spy_return_1d': spy_return,
                'ita_return_1d': ita_return,  # Defense sector
                'vix_change_1d': vix_change,
                'dxy_return_1d': dxy_return,
                
                # Market regime from cross-assets
                'market_bullish': 1 if (spy_return > 0.01 and vix_change < -0.05) else 0,
                'market_bearish': 1 if (spy_return < -0.01 and vix_change > 0.1) else 0,
                'defense_outperforming': 1 if ita_return > spy_return else 0,
                'risk_on_environment': 1 if (spy_return > 0 and vix_change < 0) else 0,
                
                # Dollar strength impact (defense stocks can be affected)
                'dollar_strengthening': 1 if dxy_return > 0.005 else 0,
                'dollar_weakening': 1 if dxy_return < -0.005 else 0,
                
                # Combined market signals
                'favorable_market_conditions': 1 if (spy_return > 0 and ita_return > spy_return and vix_change < 0) else 0,
                'unfavorable_market_conditions': 1 if (spy_return < -0.01 and vix_change > 0.1) else 0,
            }
        except Exception as e:
            logger.warning(f"⚠️ Error creating cross-asset features: {e}")
            return {'spy_return_1d': 0, 'market_bullish': 0}
    
    # Helper methods
    def _minutes_between_times(self, time1, time2):
        """Calculate minutes between two time objects"""
        try:
            dt1 = datetime.combine(datetime.today(), time1)
            dt2 = datetime.combine(datetime.today(), time2)
            return int((dt2 - dt1).total_seconds() / 60)
        except:
            return 0
    
    def _calculate_trend(self, values):
        """Calculate simple linear trend"""
        if len(values) < 2:
            return 0
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        return slope
    
    def _calculate_acceleration(self, values):
        """Calculate acceleration (second derivative)"""
        if len(values) < 3:
            return 0
        return values[-1] - 2 * values[-2] + values[-3]
    
    def _get_current_vix(self):
        """Get current VIX level"""
        try:
            if self.vix_data is not None and not self.vix_data.empty:
                return float(self.vix_data['Close'].iloc[-1])
            return 20.0  # Default VIX level
        except:
            return 20.0
    
    def _get_recent_return(self, symbol):
        """Get recent 1-day return for symbol"""
        try:
            data_map = {'SPY': self.spy_data, 'ITA': self.ita_data, 'DXY': self.dxy_data}
            data = data_map.get(symbol)
            
            if data is not None and not data.empty and len(data) >= 2:
                recent_price = float(data['Close'].iloc[-1])
                previous_price = float(data['Close'].iloc[-2])
                return (recent_price - previous_price) / previous_price
            return 0.0
        except:
            return 0.0
    
    def _get_recent_vix_change(self):
        """Get recent VIX change"""
        try:
            if self.vix_data is not None and not self.vix_data.empty and len(self.vix_data) >= 2:
                current_vix = float(self.vix_data['Close'].iloc[-1])
                previous_vix = float(self.vix_data['Close'].iloc[-2])
                return (current_vix - previous_vix) / previous_vix
            return 0.0
        except:
            return 0.0

def test_feature_engineering():
    """Quick test of feature engineering"""
    logger.info("🧪 Testing advanced feature engineering...")
    
    # Create sample data
    sample_data = pd.DataFrame({
        'prediction_id': [1, 2, 3],
        'timestamp': ['2025-07-24 14:30:00', '2025-07-24 14:45:00', '2025-07-24 15:00:00'],
        'confidence': [0.75, 0.82, 0.68],
        'expected_move': [0.025, 0.031, 0.019],
        'signal_data': [
            '{"technical_analysis": {"confidence": 0.8, "direction": "BUY", "strength": 0.7}}',
            '{"technical_analysis": {"confidence": 0.85, "direction": "BUY", "strength": 0.8}, "momentum": {"confidence": 0.7, "direction": "BUY", "strength": 0.6}}',
            '{"technical_analysis": {"confidence": 0.6, "direction": "SELL", "strength": 0.5}}'
        ]
    })
    
    # Test feature engineering
    feature_engineer = AdvancedFeatureEngineer()
    features = feature_engineer.engineer_features(sample_data)
    
    logger.info(f"✅ Generated {len(features.columns)} features:")
    for col in sorted(features.columns):
        logger.info(f"   - {col}")
    
    logger.success("🎉 Feature engineering test completed successfully!")
    return features

if __name__ == "__main__":
    test_feature_engineering()
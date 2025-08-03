#!/usr/bin/env python3
"""
Enhanced ML Predictor using Ultimate Historical Training Models
Integrates with real-time trading system for maximum sophistication
"""
import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

# Technical analysis
import yfinance as yf
import ta

class UltimateMLPredictor:
    """
    Ultra-sophisticated ML predictor using ultimate historical training models
    """
    
    def __init__(self, models_file: str = None):
        self.models = {}
        self.scalers = {}
        self.feature_selectors = {}
        self.feature_names = []
        
        # Load ultimate models
        if models_file:
            self.load_ultimate_models(models_file)
            
    def load_ultimate_models(self, models_file: str):
        """Load the ultimate trained models"""
        try:
            logger.info(f"🧠 Loading ultimate models from {models_file}")
            
            model_data = joblib.load(models_file)
            
            for target, data in model_data.items():
                self.models[target] = data['models']
                self.scalers[target] = data['scaler']
                self.feature_selectors[target] = data['feature_selector']
                
            logger.info(f"✅ Loaded {len(self.models)} prediction targets")
            
            # Extract feature names from first model
            if self.models:
                first_target = list(self.models.keys())[0]
                first_model = list(self.models[first_target].values())[0]
                if hasattr(first_model, 'feature_names_in_'):
                    self.feature_names = list(first_model.feature_names_in_)
                    
        except Exception as e:
            logger.error(f"❌ Error loading models: {e}")
            
    def generate_features(self, symbol: str = 'RTX', lookback_days: int = 200) -> Optional[Dict]:
        """Generate features for current market conditions"""
        try:
            # Fetch recent data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days)
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if len(data) < 50:
                logger.warning(f"Insufficient data for {symbol}")
                return None
                
            # Use latest data point
            index = len(data) - 1
            
            features = {}
            
            # Basic features
            features['symbol'] = symbol
            features['price'] = data['Close'].iloc[-1]
            features['timestamp'] = datetime.now()
            
            # Technical features (simplified version of ultimate generator)
            features.update(self._calculate_technical_features(data, index))
            features.update(self._calculate_volatility_features(data, index))
            features.update(self._calculate_time_features(datetime.now()))
            features.update(self._calculate_microstructure_features(data, index))
            
            # Cross-asset features (load other symbols)
            cross_assets = ['BA', 'GD', 'NOC', 'LMT', 'SPY', 'QQQ']
            features.update(self._calculate_cross_asset_features(symbol, cross_assets, lookback_days))
            
            return features
            
        except Exception as e:
            logger.error(f"Error generating features: {e}")
            return None
            
    def _calculate_technical_features(self, data: pd.DataFrame, index: int) -> Dict:
        """Calculate technical indicators"""
        features = {}
        
        try:
            c = data['Close']
            h = data['High']
            l = data['Low']
            v = data['Volume']
            
            # Price changes
            features['price_change_1d'] = c.pct_change(1).iloc[-1] if len(c) > 1 else 0
            features['price_change_5d'] = c.pct_change(5).iloc[-1] if len(c) > 5 else 0
            features['price_change_20d'] = c.pct_change(20).iloc[-1] if len(c) > 20 else 0
            
            # Moving averages
            for period in [5, 10, 20, 50, 100, 200]:
                if len(c) > period:
                    sma = c.rolling(period).mean().iloc[-1]
                    features[f'sma_{period}_ratio'] = c.iloc[-1] / sma if sma > 0 else 1
                    
            # RSI
            for period in [14, 21, 50]:
                if len(c) > period:
                    rsi = ta.momentum.RSIIndicator(c, window=period).rsi().iloc[-1]
                    features[f'rsi_{period}'] = rsi / 100 if not pd.isna(rsi) else 0.5
                    
            # MACD
            macd = ta.trend.MACD(c)
            features['macd_signal'] = macd.macd_signal().iloc[-1] if not macd.macd_signal().empty else 0
            features['macd_diff'] = macd.macd_diff().iloc[-1] if not macd.macd_diff().empty else 0
            
            # ATR
            atr = ta.volatility.AverageTrueRange(h, l, c, window=14)
            if not atr.average_true_range().empty:
                features['atr_ratio'] = atr.average_true_range().iloc[-1] / c.iloc[-1]
            
            # Volume
            features['volume_ratio'] = v.iloc[-1] / v.rolling(20).mean().iloc[-1] if len(v) > 20 else 1
            
            # Momentum
            for period in [1, 3, 5, 10, 20]:
                if len(c) > period:
                    features[f'momentum_{period}d'] = (c.iloc[-1] / c.iloc[-period-1] - 1) if period < len(c) else 0
                    
        except Exception as e:
            logger.debug(f"Error in technical features: {e}")
            
        return features
        
    def _calculate_volatility_features(self, data: pd.DataFrame, index: int) -> Dict:
        """Calculate volatility features"""
        features = {}
        
        try:
            returns = data['Close'].pct_change().dropna()
            
            if len(returns) > 20:
                # Volatility regimes
                vol_20d = returns.rolling(20).std().iloc[-1]
                vol_60d = returns.rolling(60).std().iloc[-1] if len(returns) > 60 else vol_20d
                
                features['vol_regime_short'] = vol_20d / returns.std() if returns.std() > 0 else 1
                features['vol_regime_long'] = vol_60d / returns.std() if returns.std() > 0 else 1
                features['vol_term_structure'] = vol_20d / vol_60d if vol_60d > 0 else 1
                
                # Recent volatility spike
                squared_returns = returns ** 2
                features['recent_vol_spike'] = squared_returns.rolling(5).mean().iloc[-1] / squared_returns.mean()
                
        except Exception as e:
            logger.debug(f"Error in volatility features: {e}")
            
        return features
        
    def _calculate_time_features(self, date: datetime) -> Dict:
        """Calculate time-based features"""
        return {
            'day_of_week': date.weekday() / 6,
            'day_of_month': date.day / 31,
            'month': date.month / 12,
            'quarter': ((date.month - 1) // 3) / 3,
            'is_month_end': 1 if date.day > 25 else 0,
            'is_quarter_end': 1 if date.month in [3, 6, 9, 12] and date.day > 25 else 0,
        }
        
    def _calculate_microstructure_features(self, data: pd.DataFrame, index: int) -> Dict:
        """Calculate microstructure features"""
        features = {}
        
        try:
            recent_data = data.iloc[-min(20, len(data)):]
            
            if len(recent_data) > 1:
                # Spread proxy
                features['spread_proxy'] = ((recent_data['High'] - recent_data['Low']) / recent_data['Close']).mean()
                
                # Volume-price correlation
                volume_changes = recent_data['Volume'].pct_change().dropna()
                price_changes = recent_data['Close'].pct_change().dropna()
                
                if len(volume_changes) > 1 and len(price_changes) > 1:
                    min_len = min(len(volume_changes), len(price_changes))
                    if min_len > 1:
                        corr = np.corrcoef(volume_changes.iloc[-min_len:], price_changes.iloc[-min_len:])[0,1]
                        features['volume_price_corr'] = corr if not pd.isna(corr) else 0
                        
                # Intraday patterns
                features['high_low_ratio'] = (recent_data['High'].iloc[-1] / recent_data['Low'].iloc[-1]) - 1
                        
        except Exception as e:
            logger.debug(f"Error in microstructure features: {e}")
            
        return features
        
    def _calculate_cross_asset_features(self, symbol: str, cross_assets: List[str], 
                                      lookback_days: int) -> Dict:
        """Calculate cross-asset features"""
        features = {}
        
        try:
            # Get RTX data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days)
            
            rtx_ticker = yf.Ticker(symbol)
            rtx_data = rtx_ticker.history(start=start_date, end=end_date)
            
            if len(rtx_data) < 20:
                return features
                
            rtx_returns = rtx_data['Close'].pct_change().dropna()
            
            # Calculate correlations with other assets
            for asset in cross_assets:
                try:
                    asset_ticker = yf.Ticker(asset)
                    asset_data = asset_ticker.history(start=start_date, end=end_date)
                    
                    if len(asset_data) > 20:
                        asset_returns = asset_data['Close'].pct_change().dropna()
                        
                        # Rolling correlations
                        for period in [20, 50]:
                            if len(rtx_returns) > period and len(asset_returns) > period:
                                # Align the series
                                aligned_rtx, aligned_asset = rtx_returns.align(asset_returns, join='inner')
                                
                                if len(aligned_rtx) > period:
                                    corr = aligned_rtx.rolling(period).corr(aligned_asset).iloc[-1]
                                    if not pd.isna(corr):
                                        features[f'corr_{asset.lower()}_{period}d'] = corr
                                        
                except Exception as e:
                    logger.debug(f"Error with {asset}: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Error in cross-asset features: {e}")
            
        return features
        
    def predict_all_targets(self, features: Dict) -> Dict:
        """Generate predictions for all targets using ultimate models"""
        predictions = {}
        
        for target in self.models.keys():
            pred = self.predict_target(features, target)
            if pred is not None:
                predictions[target] = pred
                
        return predictions
        
    def predict_target(self, features: Dict, target: str) -> Optional[Dict]:
        """Generate prediction for specific target"""
        try:
            if target not in self.models:
                return None
                
            # Prepare features
            feature_df = pd.DataFrame([features])
            
            # Remove non-numeric columns
            numeric_cols = feature_df.select_dtypes(include=[np.number]).columns
            X = feature_df[numeric_cols].fillna(0)
            
            # Apply feature selection if available
            if self.feature_selectors[target] is not None:
                try:
                    X_selected = pd.DataFrame(
                        self.feature_selectors[target].transform(X),
                        columns=X.columns[self.feature_selectors[target].get_support()]
                    )
                except:
                    X_selected = X  # Fallback if feature selection fails
            else:
                X_selected = X
                
            # Apply scaling
            try:
                X_scaled = pd.DataFrame(
                    self.scalers[target].transform(X_selected),
                    columns=X_selected.columns
                )
            except:
                X_scaled = X_selected  # Fallback if scaling fails
                
            # Generate predictions from all models
            model_predictions = {}
            model_probabilities = {}
            
            for model_name, model in self.models[target].items():
                try:
                    if hasattr(model, 'predict_proba'):
                        proba = model.predict_proba(X_scaled)[0]
                        pred = model.predict(X_scaled)[0]
                        
                        if len(proba) > 1:
                            model_probabilities[model_name] = proba[1]  # Probability of positive class
                        else:
                            model_probabilities[model_name] = proba[0]
                            
                        model_predictions[model_name] = pred
                    else:
                        pred = model.predict(X_scaled)[0]
                        model_predictions[model_name] = pred
                        model_probabilities[model_name] = pred
                        
                except Exception as e:
                    logger.debug(f"Error with {model_name}: {e}")
                    continue
                    
            if not model_predictions:
                return None
                
            # Ensemble prediction
            ensemble_pred = np.mean(list(model_predictions.values()))
            ensemble_proba = np.mean(list(model_probabilities.values()))
            
            # Find best individual model
            best_model = max(model_probabilities.items(), key=lambda x: x[1])
            
            return {
                'ensemble_prediction': ensemble_pred,
                'ensemble_probability': ensemble_proba,
                'best_model': best_model[0],
                'best_probability': best_model[1],
                'individual_predictions': model_predictions,
                'individual_probabilities': model_probabilities,
                'confidence': ensemble_proba
            }
            
        except Exception as e:
            logger.error(f"Error predicting {target}: {e}")
            return None
            
    def generate_trading_signal(self, symbol: str = 'RTX') -> Dict:
        """Generate comprehensive trading signal using ultimate models"""
        logger.info(f"🧠 Generating ultimate ML signal for {symbol}")
        
        try:
            # Generate features
            features = self.generate_features(symbol)
            if not features:
                return {'error': 'Could not generate features'}
                
            # Get predictions
            predictions = self.predict_all_targets(features)
            if not predictions:
                return {'error': 'Could not generate predictions'}
                
            # Analyze predictions
            signal_strength = 0
            confidence_scores = []
            
            for target, pred in predictions.items():
                if pred and 'confidence' in pred:
                    confidence_scores.append(pred['confidence'])
                    
                    # Weight different targets
                    if 'profitable_5d' in target:
                        signal_strength += pred['confidence'] * 0.4
                    elif 'profitable_10d' in target:
                        signal_strength += pred['confidence'] * 0.3  
                    elif 'big_move' in target:
                        signal_strength += pred['confidence'] * 0.3
                        
            # Overall assessment
            avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
            
            # Generate signal
            if avg_confidence > 0.7:
                signal = 'STRONG_BUY'
            elif avg_confidence > 0.6:
                signal = 'BUY'
            elif avg_confidence > 0.4:
                signal = 'HOLD'
            elif avg_confidence > 0.3:
                signal = 'SELL'
            else:
                signal = 'STRONG_SELL'
                
            return {
                'symbol': symbol,
                'signal': signal,
                'confidence': avg_confidence,
                'signal_strength': signal_strength,
                'predictions': predictions,
                'features_used': len(features),
                'timestamp': datetime.now(),
                'model_type': 'ultimate_ensemble'
            }
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return {'error': str(e)}

def test_ultimate_predictor():
    """Test the ultimate predictor"""
    logger.info("🧪 Testing Ultimate ML Predictor")
    
    # Use the models we just created
    models_file = "trained_models/ultimate_models_20250803_183343.pkl"
    
    predictor = UltimateMLPredictor(models_file)
    
    # Test prediction
    signal = predictor.generate_trading_signal('RTX')
    
    logger.info("📊 Ultimate ML Signal:")
    logger.info(f"Signal: {signal.get('signal', 'N/A')}")
    logger.info(f"Confidence: {signal.get('confidence', 0):.3f}")
    logger.info(f"Features: {signal.get('features_used', 0)}")
    
    if 'predictions' in signal:
        for target, pred in signal['predictions'].items():
            if pred:
                logger.info(f"{target}: {pred.get('confidence', 0):.3f} (best: {pred.get('best_model', 'N/A')})")
                
    return signal

if __name__ == "__main__":
    test_ultimate_predictor()
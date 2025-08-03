#!/usr/bin/env python3
"""
ULTIMATE Historical Training System for AlgoSlayer
Maximum sophistication - training can take hours for maximum accuracy
"""
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

# Advanced ML libraries
from sklearn.model_selection import train_test_split, TimeSeriesSplit, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.feature_selection import SelectKBest, f_classif, RFE
import xgboost as xgb
import lightgbm as lgb

# Deep Learning
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, LSTM, Dropout, BatchNormalization
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

# Advanced technical analysis
import ta
from scipy import stats
from scipy.optimize import minimize
import concurrent.futures
from itertools import combinations
import joblib
import json

class UltimateHistoricalDataGenerator:
    """Generate massive, comprehensive historical dataset"""
    
    def __init__(self):
        self.symbols = [
            'RTX',   # Primary focus
            'BA',    # Boeing (aerospace)
            'GD',    # General Dynamics (defense)
            'NOC',   # Northrop Grumman (defense)
            'LMT',   # Lockheed Martin (defense)
            'SPY',   # Market benchmark
            'QQQ',   # Tech benchmark
            'VIX',   # Volatility
        ]
        self.lookback_periods = [5, 10, 20, 50, 100, 200]
        
    def generate_comprehensive_dataset(self, start_date: str = '2015-01-01', 
                                     end_date: str = '2024-07-31') -> pd.DataFrame:
        """Generate the most comprehensive dataset possible"""
        logger.info(f"🚀 Generating ULTIMATE dataset from {start_date} to {end_date}")
        
        all_data = []
        
        # 1. Multi-Asset Data Collection
        logger.info("📊 Fetching multi-asset data...")
        asset_data = {}
        
        for symbol in self.symbols:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date, interval='1d')
                if not data.empty:
                    asset_data[symbol] = data
                    logger.info(f"✅ {symbol}: {len(data)} days")
                else:
                    logger.warning(f"❌ No data for {symbol}")
            except Exception as e:
                logger.warning(f"❌ Error fetching {symbol}: {e}")
                
        # 2. Generate Trading Opportunities for Each Asset
        logger.info("🎯 Generating trading opportunities...")
        
        for primary_symbol in ['RTX']:  # Focus on RTX but can expand
            if primary_symbol not in asset_data:
                continue
                
            primary_data = asset_data[primary_symbol]
            
            # Generate opportunities for each trading day
            for i in range(50, len(primary_data) - 30):  # Need lookback and lookahead
                current_date = primary_data.index[i]
                
                # Skip weekends
                if current_date.weekday() >= 5:
                    continue
                    
                try:
                    opportunity = self._generate_trading_opportunity(
                        primary_symbol, current_date, asset_data, i
                    )
                    
                    if opportunity:
                        all_data.append(opportunity)
                        
                except Exception as e:
                    logger.debug(f"Error generating opportunity for {current_date}: {e}")
                    continue
                    
        logger.info(f"✅ Generated {len(all_data)} trading opportunities")
        return pd.DataFrame(all_data)
    
    def _generate_trading_opportunity(self, symbol: str, date: datetime, 
                                    all_data: Dict, index: int) -> Optional[Dict]:
        """Generate a single ultra-sophisticated trading opportunity"""
        
        primary_data = all_data[symbol]
        current_price = primary_data['Close'].iloc[index]
        
        # 1. Technical Features (50+ indicators)
        features = self._calculate_technical_features(primary_data, index)
        
        # 2. Cross-Asset Features
        features.update(self._calculate_cross_asset_features(all_data, index))
        
        # 3. Market Microstructure Features
        features.update(self._calculate_microstructure_features(primary_data, index))
        
        # 4. Time-Based Features
        features.update(self._calculate_time_features(date))
        
        # 5. Volatility Regime Features
        features.update(self._calculate_volatility_features(primary_data, index))
        
        # 6. Options-Specific Features
        features.update(self._calculate_options_features(primary_data, index, current_price))
        
        # 7. Generate Multiple Targets (1d, 3d, 5d, 10d returns)
        targets = self._calculate_future_returns(primary_data, index)
        
        if targets is None:
            return None
            
        # Combine everything
        opportunity = {
            'timestamp': date,
            'symbol': symbol,
            'price': current_price,
            **features,
            **targets
        }
        
        return opportunity
    
    def _calculate_technical_features(self, data: pd.DataFrame, index: int) -> Dict:
        """Calculate 50+ technical indicators"""
        close = data['Close']
        high = data['High']
        low = data['Low']
        volume = data['Volume']
        
        # Get recent data up to current index
        recent_data = data.iloc[:index+1]
        c = recent_data['Close']
        h = recent_data['High']
        l = recent_data['Low']
        v = recent_data['Volume']
        
        features = {}
        
        try:
            # Basic price features
            features['price_change_1d'] = c.pct_change(1).iloc[-1]
            features['price_change_5d'] = c.pct_change(5).iloc[-1]
            features['price_change_20d'] = c.pct_change(20).iloc[-1]
            
            # Moving averages
            for period in [5, 10, 20, 50, 100, 200]:
                if len(c) > period:
                    sma = c.rolling(period).mean().iloc[-1]
                    features[f'sma_{period}_ratio'] = c.iloc[-1] / sma if sma > 0 else 1
                    
            # RSI family
            for period in [14, 21, 50]:
                if len(c) > period:
                    rsi = ta.momentum.RSIIndicator(c, window=period).rsi().iloc[-1]
                    features[f'rsi_{period}'] = rsi / 100
                    
            # MACD
            macd = ta.trend.MACD(c)
            features['macd_signal'] = macd.macd_signal().iloc[-1] if not macd.macd_signal().empty else 0
            features['macd_diff'] = macd.macd_diff().iloc[-1] if not macd.macd_diff().empty else 0
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(c)
            bb_high = bb.bollinger_hband()
            bb_low = bb.bollinger_lband()
            if not bb_high.empty and not bb_low.empty:
                features['bb_position'] = (c.iloc[-1] - bb_low.iloc[-1]) / (bb_high.iloc[-1] - bb_low.iloc[-1])
                features['bb_width'] = (bb_high.iloc[-1] - bb_low.iloc[-1]) / c.iloc[-1]
            
            # ATR and volatility
            atr = ta.volatility.AverageTrueRange(h, l, c, window=14)
            if not atr.average_true_range().empty:
                features['atr_ratio'] = atr.average_true_range().iloc[-1] / c.iloc[-1]
                
            # Stochastic
            stoch = ta.momentum.StochasticOscillator(h, l, c)
            if not stoch.stoch().empty:
                features['stoch_k'] = stoch.stoch().iloc[-1] / 100
                features['stoch_d'] = stoch.stoch_signal().iloc[-1] / 100
                
            # Williams %R
            williams = ta.momentum.WilliamsRIndicator(h, l, c)
            if not williams.williams_r().empty:
                features['williams_r'] = (williams.williams_r().iloc[-1] + 100) / 100
                
            # Commodity Channel Index
            cci = ta.trend.CCIIndicator(h, l, c)
            if not cci.cci().empty:
                features['cci'] = np.tanh(cci.cci().iloc[-1] / 200)  # Normalize
                
            # Volume indicators
            features['volume_ratio'] = v.iloc[-1] / v.rolling(20).mean().iloc[-1] if len(v) > 20 else 1
            
            # On-Balance Volume
            obv = ta.volume.OnBalanceVolumeIndicator(c, v)
            if not obv.on_balance_volume().empty:
                obv_values = obv.on_balance_volume()
                features['obv_trend'] = np.polyfit(range(min(10, len(obv_values))), 
                                                 obv_values.iloc[-min(10, len(obv_values)):].values, 1)[0]
                
            # Price momentum
            for period in [1, 3, 5, 10, 20]:
                if len(c) > period:
                    features[f'momentum_{period}d'] = (c.iloc[-1] / c.iloc[-period-1] - 1) if period < len(c) else 0
                    
            # Volatility features
            returns = c.pct_change()
            for period in [5, 10, 20]:
                if len(returns) > period:
                    features[f'volatility_{period}d'] = returns.rolling(period).std().iloc[-1]
                    
        except Exception as e:
            logger.debug(f"Error calculating technical features: {e}")
            
        return features
    
    def _calculate_cross_asset_features(self, all_data: Dict, index: int) -> Dict:
        """Calculate cross-asset correlation and relative performance"""
        features = {}
        
        try:
            # Get RTX data
            rtx_data = all_data.get('RTX')
            if rtx_data is None or index >= len(rtx_data):
                return features
                
            rtx_returns = rtx_data['Close'].pct_change()
            
            # Compare with other assets
            for symbol, data in all_data.items():
                if symbol == 'RTX' or index >= len(data):
                    continue
                    
                asset_returns = data['Close'].pct_change()
                
                # Calculate rolling correlation
                for period in [20, 50]:
                    if len(rtx_returns) > period and len(asset_returns) > period:
                        corr = rtx_returns.rolling(period).corr(asset_returns).iloc[min(index, len(rtx_returns)-1)]
                        if not pd.isna(corr):
                            features[f'corr_{symbol.lower()}_{period}d'] = corr
                            
                # Relative performance
                if len(data['Close']) > index:
                    rtx_change = rtx_returns.iloc[min(index, len(rtx_returns)-1)]
                    asset_change = asset_returns.iloc[min(index, len(asset_returns)-1)]
                    if not pd.isna(rtx_change) and not pd.isna(asset_change):
                        features[f'rel_perf_{symbol.lower()}'] = rtx_change - asset_change
                        
        except Exception as e:
            logger.debug(f"Error calculating cross-asset features: {e}")
            
        return features
    
    def _calculate_microstructure_features(self, data: pd.DataFrame, index: int) -> Dict:
        """Calculate market microstructure features"""
        features = {}
        
        try:
            recent_data = data.iloc[max(0, index-20):index+1]
            
            if len(recent_data) < 5:
                return features
                
            # Spread proxy
            features['spread_proxy'] = ((recent_data['High'] - recent_data['Low']) / recent_data['Close']).mean()
            
            # Price efficiency
            returns = recent_data['Close'].pct_change().dropna()
            if len(returns) > 1:
                features['price_efficiency'] = abs(returns.sum()) / returns.abs().sum()
                
            # Volume-price relationship
            volume_changes = recent_data['Volume'].pct_change().dropna()
            price_changes = recent_data['Close'].pct_change().dropna()
            
            if len(volume_changes) > 1 and len(price_changes) > 1:
                min_len = min(len(volume_changes), len(price_changes))
                if min_len > 1:
                    vol_price_corr = np.corrcoef(volume_changes.iloc[-min_len:], 
                                               price_changes.iloc[-min_len:])[0,1]
                    features['volume_price_corr'] = vol_price_corr if not pd.isna(vol_price_corr) else 0
                    
            # Intraday patterns
            features['high_low_ratio'] = (recent_data['High'].iloc[-1] / recent_data['Low'].iloc[-1]) - 1
            features['close_position'] = ((recent_data['Close'].iloc[-1] - recent_data['Low'].iloc[-1]) / 
                                        (recent_data['High'].iloc[-1] - recent_data['Low'].iloc[-1]))
                                        
        except Exception as e:
            logger.debug(f"Error calculating microstructure features: {e}")
            
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
    
    def _calculate_volatility_features(self, data: pd.DataFrame, index: int) -> Dict:
        """Calculate advanced volatility regime features"""
        features = {}
        
        try:
            recent_data = data.iloc[max(0, index-100):index+1]
            returns = recent_data['Close'].pct_change().dropna()
            
            if len(returns) < 20:
                return features
                
            # Volatility regimes
            vol_20d = returns.rolling(20).std()
            vol_60d = returns.rolling(60).std()
            
            if not vol_20d.empty and not vol_60d.empty:
                current_vol_20 = vol_20d.iloc[-1]
                current_vol_60 = vol_60d.iloc[-1]
                
                features['vol_regime_short'] = current_vol_20 / returns.std() if returns.std() > 0 else 1
                features['vol_regime_long'] = current_vol_60 / returns.std() if returns.std() > 0 else 1
                features['vol_term_structure'] = current_vol_20 / current_vol_60 if current_vol_60 > 0 else 1
                
            # GARCH-like features
            squared_returns = returns ** 2
            features['recent_vol_spike'] = squared_returns.rolling(5).mean().iloc[-1] / squared_returns.mean()
            
            # Volatility percentile
            if len(vol_20d) > 50:
                vol_percentile = stats.percentileofscore(vol_20d.dropna(), current_vol_20) / 100
                features['vol_percentile'] = vol_percentile
                
        except Exception as e:
            logger.debug(f"Error calculating volatility features: {e}")
            
        return features
    
    def _calculate_options_features(self, data: pd.DataFrame, index: int, current_price: float) -> Dict:
        """Calculate options-specific features"""
        features = {}
        
        try:
            # Simulated options features (in real implementation, use actual options data)
            recent_returns = data['Close'].pct_change().iloc[max(0, index-20):index+1]
            
            if len(recent_returns) > 1:
                # Implied volatility proxy
                historical_vol = recent_returns.std() * np.sqrt(252)
                features['historical_vol'] = historical_vol
                
                # Moneyness for common strikes
                for strike_pct in [0.95, 0.97, 1.0, 1.03, 1.05]:
                    strike = current_price * strike_pct
                    features[f'moneyness_{int(strike_pct*100)}'] = current_price / strike
                    
                # Time decay features
                for days in [7, 14, 21, 30, 45]:
                    # Simplified time value
                    time_value = historical_vol * np.sqrt(days / 365) * current_price * 0.4
                    features[f'time_value_{days}d'] = time_value / current_price
                    
                # Greeks proxies
                features['delta_proxy'] = min(0.9, max(0.1, 0.5 + recent_returns.iloc[-1] * 10))
                features['gamma_proxy'] = 0.02 * (1 - abs(recent_returns.iloc[-1]) * 20)
                features['theta_proxy'] = -time_value / 30  # Rough theta
                
        except Exception as e:
            logger.debug(f"Error calculating options features: {e}")
            
        return features
    
    def _calculate_future_returns(self, data: pd.DataFrame, index: int) -> Optional[Dict]:
        """Calculate future returns for multiple horizons"""
        targets = {}
        
        try:
            current_price = data['Close'].iloc[index]
            
            # Calculate returns for different horizons
            for days in [1, 3, 5, 10, 20]:
                future_index = index + days
                if future_index < len(data):
                    future_price = data['Close'].iloc[future_index]
                    return_pct = (future_price / current_price) - 1
                    
                    targets[f'return_{days}d'] = return_pct
                    targets[f'profitable_{days}d'] = 1 if return_pct > 0.02 else 0  # 2% threshold
                    targets[f'big_move_{days}d'] = 1 if abs(return_pct) > 0.05 else 0  # 5% threshold
                else:
                    return None
                    
            # Maximum return achieved in next 30 days
            max_future_index = min(index + 30, len(data) - 1)
            if max_future_index > index:
                future_prices = data['Close'].iloc[index+1:max_future_index+1]
                max_return = (future_prices.max() / current_price) - 1
                min_return = (future_prices.min() / current_price) - 1
                
                targets['max_return_30d'] = max_return
                targets['min_return_30d'] = min_return
                targets['max_drawdown_30d'] = min_return
                
        except Exception as e:
            logger.debug(f"Error calculating future returns: {e}")
            return None
            
        return targets

class UltimateMLTrainer:
    """Ultimate ML training with every advanced technique"""
    
    def __init__(self):
        self.models = {}
        self.ensemble = None
        self.feature_selector = None
        self.scaler = RobustScaler()
        
    def train_ultimate_ensemble(self, df: pd.DataFrame) -> Dict:
        """Train the most sophisticated ensemble possible"""
        logger.info("🧠 Starting ULTIMATE ML training...")
        
        # Prepare features and targets
        feature_cols = [col for col in df.columns if not col.startswith(('return_', 'profitable_', 'big_move_', 'max_', 'min_', 'timestamp', 'symbol', 'price'))]
        
        X = df[feature_cols].fillna(0)
        
        # Multiple target training
        results = {}
        
        for target in ['profitable_5d', 'profitable_10d', 'big_move_5d']:
            if target in df.columns:
                logger.info(f"🎯 Training models for {target}")
                
                y = df[target].fillna(0).astype(int)
                
                # Feature selection and scaling
                X_processed = self._preprocess_features(X, y)
                
                # Train multiple model types
                model_results = self._train_model_ensemble(X_processed, y, target)
                results[target] = model_results
                
        return results
    
    def _preprocess_features(self, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        """Advanced feature preprocessing"""
        logger.info("🔧 Advanced feature preprocessing...")
        
        # 1. Remove highly correlated features
        correlation_matrix = X.corr().abs()
        upper_triangle = correlation_matrix.where(
            np.triu(np.ones(correlation_matrix.shape), k=1).astype(bool)
        )
        
        high_corr_features = [column for column in upper_triangle.columns 
                            if any(upper_triangle[column] > 0.95)]
        X_reduced = X.drop(columns=high_corr_features)
        
        logger.info(f"📉 Removed {len(high_corr_features)} highly correlated features")
        
        # 2. Feature selection
        if len(X_reduced.columns) > 50:
            selector = SelectKBest(score_func=f_classif, k=min(50, len(X_reduced.columns)))
            X_selected = pd.DataFrame(
                selector.fit_transform(X_reduced, y),
                columns=X_reduced.columns[selector.get_support()],
                index=X_reduced.index
            )
            self.feature_selector = selector
        else:
            X_selected = X_reduced
            
        logger.info(f"✅ Selected {len(X_selected.columns)} best features")
        
        # 3. Scaling
        X_scaled = pd.DataFrame(
            self.scaler.fit_transform(X_selected),
            columns=X_selected.columns,
            index=X_selected.index
        )
        
        return X_scaled
    
    def _train_model_ensemble(self, X: pd.DataFrame, y: pd.Series, target: str) -> Dict:
        """Train comprehensive model ensemble"""
        
        # Time series split for financial data
        tscv = TimeSeriesSplit(n_splits=5)
        
        models = {
            'random_forest': RandomForestClassifier(
                n_estimators=500,
                max_depth=15,
                min_samples_split=10,
                min_samples_leaf=5,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            ),
            'xgboost': xgb.XGBClassifier(
                n_estimators=500,
                max_depth=8,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                scale_pos_weight=len(y[y==0]) / len(y[y==1]) if len(y[y==1]) > 0 else 1,
                random_state=42,
                n_jobs=-1
            ),
            'lightgbm': lgb.LGBMClassifier(
                n_estimators=500,
                max_depth=8,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1,
                verbose=-1
            ),
            'gradient_boost': GradientBoostingClassifier(
                n_estimators=300,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                random_state=42
            ),
            'neural_net': MLPClassifier(
                hidden_layer_sizes=(100, 50, 25),
                max_iter=1000,
                alpha=0.001,
                random_state=42,
                early_stopping=True
            )
        }
        
        # Add deep learning if available
        if TENSORFLOW_AVAILABLE:
            models['deep_learning'] = self._create_deep_model(X.shape[1])
            
        # Train each model with cross-validation
        cv_results = {}
        trained_models = {}
        
        for name, model in models.items():
            logger.info(f"🤖 Training {name}...")
            
            cv_scores = []
            
            for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
                X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                
                if name == 'deep_learning' and TENSORFLOW_AVAILABLE:
                    score = self._train_deep_model(model, X_train, y_train, X_val, y_val)
                else:
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_val)
                    score = f1_score(y_val, y_pred, zero_division=0)
                    
                cv_scores.append(score)
                
            avg_score = np.mean(cv_scores)
            cv_results[name] = {
                'cv_scores': cv_scores,
                'mean_score': avg_score,
                'std_score': np.std(cv_scores)
            }
            
            # Train on full dataset
            if name != 'deep_learning':
                model.fit(X, y)
                trained_models[name] = model
                
            logger.info(f"✅ {name}: {avg_score:.4f} ± {np.std(cv_scores):.4f}")
            
        # Create voting ensemble
        if len(trained_models) > 1:
            voting_models = [(name, model) for name, model in trained_models.items()]
            ensemble = VotingClassifier(
                estimators=voting_models,
                voting='soft'
            )
            ensemble.fit(X, y)
            
            # Test ensemble
            ensemble_scores = []
            for train_idx, val_idx in tscv.split(X):
                X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                
                ensemble.fit(X_train, y_train)
                y_pred = ensemble.predict(X_val)
                score = f1_score(y_val, y_pred, zero_division=0)
                ensemble_scores.append(score)
                
            cv_results['ensemble'] = {
                'cv_scores': ensemble_scores,
                'mean_score': np.mean(ensemble_scores),
                'std_score': np.std(ensemble_scores)
            }
            
            trained_models['ensemble'] = ensemble
            
        # Feature importance analysis
        feature_importance = self._analyze_feature_importance(trained_models, X.columns)
        
        return {
            'cv_results': cv_results,
            'trained_models': trained_models,
            'feature_importance': feature_importance,
            'best_model': max(cv_results.items(), key=lambda x: x[1]['mean_score'])
        }
    
    def _create_deep_model(self, input_dim: int):
        """Create deep learning model"""
        model = Sequential([
            Dense(256, activation='relu', input_shape=(input_dim,)),
            BatchNormalization(),
            Dropout(0.3),
            
            Dense(128, activation='relu'),
            BatchNormalization(),
            Dropout(0.3),
            
            Dense(64, activation='relu'),
            BatchNormalization(),
            Dropout(0.2),
            
            Dense(32, activation='relu'),
            Dropout(0.2),
            
            Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def _train_deep_model(self, model, X_train, y_train, X_val, y_val):
        """Train deep learning model"""
        callbacks = [
            EarlyStopping(patience=10, restore_best_weights=True),
            ReduceLROnPlateau(patience=5, factor=0.5, min_lr=0.0001)
        ]
        
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=100,
            batch_size=32,
            callbacks=callbacks,
            verbose=0
        )
        
        y_pred = (model.predict(X_val) > 0.5).astype(int)
        return f1_score(y_val, y_pred, zero_division=0)
    
    def _analyze_feature_importance(self, models: Dict, feature_names: List) -> Dict:
        """Analyze feature importance across models"""
        importance_data = {}
        
        for name, model in models.items():
            if hasattr(model, 'feature_importances_'):
                importance_data[name] = dict(zip(feature_names, model.feature_importances_))
                
        # Aggregate importance
        if importance_data:
            aggregated = {}
            for feature in feature_names:
                scores = [data.get(feature, 0) for data in importance_data.values()]
                aggregated[feature] = np.mean(scores)
                
            # Sort by importance
            sorted_features = sorted(aggregated.items(), key=lambda x: x[1], reverse=True)
            
            return {
                'individual': importance_data,
                'aggregated': dict(sorted_features),
                'top_10': dict(sorted_features[:10])
            }
            
        return {}

def run_ultimate_training():
    """Run the ultimate training pipeline"""
    logger.info("🚀 STARTING ULTIMATE HISTORICAL TRAINING")
    logger.info("⏰ This may take several hours - maximum sophistication mode!")
    
    # 1. Generate comprehensive dataset
    logger.info("\n" + "="*80)
    logger.info("PHASE 1: ULTIMATE DATA GENERATION")
    logger.info("="*80)
    
    data_generator = UltimateHistoricalDataGenerator()
    
    # Generate dataset from 2015 (more history = better learning)
    df = data_generator.generate_comprehensive_dataset(
        start_date='2015-01-01',
        end_date='2024-07-31'
    )
    
    if df.empty:
        logger.error("❌ No data generated!")
        return
        
    logger.info(f"✅ Generated dataset: {len(df)} samples, {len(df.columns)} features")
    
    # Save raw dataset
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    raw_file = f'data/ultimate_historical_dataset_{timestamp}.csv'
    df.to_csv(raw_file, index=False)
    logger.info(f"💾 Raw dataset saved: {raw_file}")
    
    # 2. Ultimate ML training
    logger.info("\n" + "="*80)
    logger.info("PHASE 2: ULTIMATE ML TRAINING")
    logger.info("="*80)
    
    trainer = UltimateMLTrainer()
    training_results = trainer.train_ultimate_ensemble(df)
    
    # 3. Save results
    logger.info("\n" + "="*80)
    logger.info("PHASE 3: SAVING ULTIMATE MODELS")
    logger.info("="*80)
    
    results_file = f'data/ultimate_training_results_{timestamp}.json'
    models_file = f'trained_models/ultimate_models_{timestamp}.pkl'
    
    # Save training results (JSON serializable)
    json_results = {}
    for target, results in training_results.items():
        json_results[target] = {
            'cv_results': {
                name: {
                    'mean_score': float(data['mean_score']),
                    'std_score': float(data['std_score'])
                }
                for name, data in results['cv_results'].items()
            },
            'feature_importance': results.get('feature_importance', {}),
            'best_model': results['best_model'][0] if results['best_model'] else None
        }
    
    with open(results_file, 'w') as f:
        json.dump(json_results, f, indent=2, default=str)
        
    # Save models
    model_data = {}
    for target, results in training_results.items():
        model_data[target] = {
            'models': results['trained_models'],
            'scaler': trainer.scaler,
            'feature_selector': trainer.feature_selector
        }
        
    joblib.dump(model_data, models_file)
    
    logger.info(f"💾 Results saved: {results_file}")
    logger.info(f"💾 Models saved: {models_file}")
    
    # 4. Generate ultimate report
    logger.info("\n" + "="*80)
    logger.info("ULTIMATE TRAINING COMPLETE!")
    logger.info("="*80)
    
    for target, results in training_results.items():
        logger.info(f"\n🎯 {target.upper()} RESULTS:")
        
        cv_results = results['cv_results']
        best_name, best_score = results['best_model']
        
        logger.info(f"🏆 Best Model: {best_name} ({best_score['mean_score']:.4f})")
        
        for name, scores in cv_results.items():
            logger.info(f"  {name:15}: {scores['mean_score']:.4f} ± {scores['std_score']:.4f}")
            
        # Top features
        if 'feature_importance' in results:
            top_features = results['feature_importance'].get('top_10', {})
            if top_features:
                logger.info(f"\n🔝 Top Features for {target}:")
                for feature, importance in list(top_features.items())[:5]:
                    logger.info(f"  {feature:30}: {importance:.4f}")
    
    logger.info(f"\n🎉 ULTIMATE TRAINING COMPLETE!")
    logger.info(f"📊 Dataset: {len(df)} samples with {len(df.columns)} features")
    logger.info(f"🤖 Models trained for multiple prediction horizons")
    logger.info(f"💾 Everything saved with timestamp: {timestamp}")
    
    return training_results, df

if __name__ == "__main__":
    # Install additional dependencies if needed
    try:
        import lightgbm
    except ImportError:
        logger.info("Installing LightGBM...")
        import subprocess
        subprocess.check_call(["pip3", "install", "lightgbm"])
        
    # Run ultimate training
    results, dataset = run_ultimate_training()
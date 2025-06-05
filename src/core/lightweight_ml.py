"""
Lightweight ML System for 1GB RAM Droplet
Real machine learning that works with limited resources
Uses scikit-learn with memory-efficient algorithms
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import joblib
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Lightweight ML imports
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score
import yfinance as yf

@dataclass
class MLPrediction:
    timestamp: datetime
    symbol: str
    direction: str  # BUY, SELL, HOLD
    confidence: float
    expected_move: float
    features_used: List[str]
    model_name: str

@dataclass
class ModelPerformance:
    model_name: str
    accuracy: float
    precision: float
    recall: float
    total_predictions: int
    last_updated: datetime

class LightweightML:
    """
    Memory-efficient ML system for small droplets
    """
    
    def __init__(self, model_dir: str = "data/models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Multiple lightweight models
        self.models = {
            'direction_classifier': LogisticRegression(max_iter=500, random_state=42),
            'magnitude_regressor': GradientBoostingClassifier(n_estimators=50, max_depth=3, random_state=42),
            'volatility_predictor': RandomForestClassifier(n_estimators=30, max_depth=4, random_state=42)
        }
        
        self.scalers = {
            'features': RobustScaler(),
            'returns': StandardScaler()
        }
        
        # Performance tracking
        self.model_performance = {}
        self.last_training = None
        self.min_data_points = 100  # Minimum data for training
        
    async def prepare_features(self, symbol: str = "RTX", lookback_days: int = 90) -> pd.DataFrame:
        """
        Prepare feature matrix for ML models
        Memory-efficient feature engineering
        """
        try:
            # Get data efficiently
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=f"{lookback_days}d", interval="1h")
            
            if len(data) < 50:  # Not enough data
                return pd.DataFrame()
            
            # Memory-efficient feature engineering
            features = pd.DataFrame(index=data.index)
            
            # Price features (efficient calculation)
            features['price'] = data['Close']
            features['volume'] = data['Volume']
            features['high_low_ratio'] = data['High'] / data['Low']
            features['close_open_ratio'] = data['Close'] / data['Open']
            
            # Returns (various timeframes)
            features['return_1h'] = data['Close'].pct_change(1)
            features['return_4h'] = data['Close'].pct_change(4)
            features['return_24h'] = data['Close'].pct_change(24)
            
            # Volatility features
            features['volatility_24h'] = features['return_1h'].rolling(24).std()
            features['volatility_7d'] = features['return_1h'].rolling(168).std()  # 7 days * 24 hours
            
            # Volume features
            features['volume_ratio'] = data['Volume'] / data['Volume'].rolling(24).mean()
            features['volume_trend'] = data['Volume'].rolling(12).mean() / data['Volume'].rolling(24).mean()
            
            # Technical indicators (lightweight)
            features['sma_ratio'] = data['Close'] / data['Close'].rolling(24).mean()
            features['price_position'] = (data['Close'] - data['Close'].rolling(24).min()) / (data['Close'].rolling(24).max() - data['Close'].rolling(24).min())
            
            # Momentum features
            features['momentum_12h'] = data['Close'] / data['Close'].shift(12) - 1
            features['momentum_24h'] = data['Close'] / data['Close'].shift(24) - 1
            
            # Time features (important for patterns)
            features['hour'] = data.index.hour
            features['day_of_week'] = data.index.dayofweek
            features['is_market_hours'] = ((data.index.hour >= 9) & (data.index.hour <= 16)).astype(int)
            
            # Target variables for training
            features['future_return_4h'] = data['Close'].shift(-4) / data['Close'] - 1
            features['future_return_24h'] = data['Close'].shift(-24) / data['Close'] - 1
            
            # Clean data
            features = features.dropna()
            
            # Memory optimization
            for col in features.select_dtypes(include=[np.float64]).columns:
                features[col] = features[col].astype(np.float32)
            
            return features
            
        except Exception as e:
            print(f"Error preparing features: {e}")
            return pd.DataFrame()
    
    async def train_models(self, features: pd.DataFrame) -> bool:
        """
        Train all models efficiently
        """
        if len(features) < self.min_data_points:
            print(f"Not enough data for training: {len(features)} < {self.min_data_points}")
            return False
        
        try:
            print(f"🧠 Training ML models with {len(features)} data points...")
            
            # Prepare training data
            feature_cols = [col for col in features.columns if not col.startswith('future_')]
            X = features[feature_cols].fillna(0)
            
            # Scale features
            X_scaled = self.scalers['features'].fit_transform(X)
            
            # Train direction classifier (up/down/sideways)
            y_direction = self._create_direction_labels(features['future_return_4h'])
            if len(np.unique(y_direction)) > 1:  # Check if we have multiple classes
                self.models['direction_classifier'].fit(X_scaled, y_direction)
                
                # Evaluate direction classifier
                tscv = TimeSeriesSplit(n_splits=3)
                dir_scores = []
                for train_idx, test_idx in tscv.split(X_scaled):
                    X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
                    y_train, y_test = y_direction[train_idx], y_direction[test_idx]
                    
                    self.models['direction_classifier'].fit(X_train, y_train)
                    y_pred = self.models['direction_classifier'].predict(X_test)
                    dir_scores.append(accuracy_score(y_test, y_pred))
                
                self.model_performance['direction_classifier'] = ModelPerformance(
                    model_name='direction_classifier',
                    accuracy=np.mean(dir_scores),
                    precision=np.mean(dir_scores),  # Simplified
                    recall=np.mean(dir_scores),
                    total_predictions=len(features),
                    last_updated=datetime.now()
                )
            
            # Train magnitude predictor (how big the move)
            y_magnitude = self._create_magnitude_labels(features['future_return_4h'])
            if len(np.unique(y_magnitude)) > 1:
                self.models['magnitude_regressor'].fit(X_scaled, y_magnitude)
            
            # Train volatility predictor
            y_volatility = self._create_volatility_labels(features['volatility_24h'])
            if len(np.unique(y_volatility)) > 1:
                self.models['volatility_predictor'].fit(X_scaled, y_volatility)
            
            # Save models
            await self._save_models()
            
            self.last_training = datetime.now()
            print(f"✅ Models trained successfully")
            print(f"   Direction accuracy: {self.model_performance.get('direction_classifier', ModelPerformance('', 0, 0, 0, 0, datetime.now())).accuracy:.2%}")
            
            return True
            
        except Exception as e:
            print(f"Error training models: {e}")
            return False
    
    def _create_direction_labels(self, returns: pd.Series) -> np.ndarray:
        """Create direction labels: 0=down, 1=sideways, 2=up"""
        labels = np.zeros(len(returns))
        labels[returns > 0.01] = 2  # Up (>1%)
        labels[returns < -0.01] = 0  # Down (<-1%)
        labels[(returns >= -0.01) & (returns <= 0.01)] = 1  # Sideways
        return labels.astype(int)
    
    def _create_magnitude_labels(self, returns: pd.Series) -> np.ndarray:
        """Create magnitude labels: 0=small, 1=medium, 2=large move"""
        labels = np.zeros(len(returns))
        abs_returns = np.abs(returns)
        labels[abs_returns > 0.03] = 2  # Large move (>3%)
        labels[(abs_returns > 0.015) & (abs_returns <= 0.03)] = 1  # Medium move
        labels[abs_returns <= 0.015] = 0  # Small move
        return labels.astype(int)
    
    def _create_volatility_labels(self, volatility: pd.Series) -> np.ndarray:
        """Create volatility regime labels"""
        labels = np.zeros(len(volatility))
        vol_75 = volatility.quantile(0.75)
        vol_25 = volatility.quantile(0.25)
        
        labels[volatility > vol_75] = 2  # High volatility
        labels[volatility < vol_25] = 0  # Low volatility
        labels[(volatility >= vol_25) & (volatility <= vol_75)] = 1  # Normal volatility
        return labels.astype(int)
    
    async def predict(self, current_features: pd.DataFrame) -> MLPrediction:
        """
        Make prediction using trained models
        """
        try:
            if current_features.empty:
                return MLPrediction(
                    timestamp=datetime.now(),
                    symbol="RTX",
                    direction="HOLD",
                    confidence=0.5,
                    expected_move=0.0,
                    features_used=[],
                    model_name="no_data"
                )
            
            # Prepare features
            feature_cols = [col for col in current_features.columns if not col.startswith('future_')]
            X = current_features[feature_cols].fillna(0).iloc[-1:]  # Latest data point
            
            # Scale features
            X_scaled = self.scalers['features'].transform(X)
            
            # Get predictions from all models
            direction_pred = self.models['direction_classifier'].predict(X_scaled)[0]
            direction_proba = self.models['direction_classifier'].predict_proba(X_scaled)[0]
            
            magnitude_pred = self.models['magnitude_regressor'].predict(X_scaled)[0]
            volatility_pred = self.models['volatility_predictor'].predict(X_scaled)[0]
            
            # Convert predictions to human readable
            direction_map = {0: "SELL", 1: "HOLD", 2: "BUY"}
            direction = direction_map[direction_pred]
            
            # Calculate confidence (max probability)
            confidence = np.max(direction_proba)
            
            # Estimate expected move based on magnitude and volatility
            magnitude_map = {0: 0.01, 1: 0.02, 2: 0.04}  # 1%, 2%, 4%
            volatility_multiplier = {0: 0.5, 1: 1.0, 2: 1.5}  # Low, normal, high vol
            
            base_move = magnitude_map[magnitude_pred]
            vol_adjustment = volatility_multiplier[volatility_pred]
            expected_move = base_move * vol_adjustment
            
            if direction == "SELL":
                expected_move = -expected_move
            elif direction == "HOLD":
                expected_move = 0.0
            
            return MLPrediction(
                timestamp=datetime.now(),
                symbol="RTX",
                direction=direction,
                confidence=confidence,
                expected_move=expected_move,
                features_used=feature_cols,
                model_name="ensemble"
            )
            
        except Exception as e:
            print(f"Error making prediction: {e}")
            return MLPrediction(
                timestamp=datetime.now(),
                symbol="RTX",
                direction="HOLD",
                confidence=0.5,
                expected_move=0.0,
                features_used=[],
                model_name="error"
            )
    
    async def _save_models(self):
        """Save trained models to disk"""
        try:
            for name, model in self.models.items():
                joblib.dump(model, self.model_dir / f"{name}.pkl")
            
            for name, scaler in self.scalers.items():
                joblib.dump(scaler, self.model_dir / f"scaler_{name}.pkl")
                
        except Exception as e:
            print(f"Error saving models: {e}")
    
    async def load_models(self) -> bool:
        """Load trained models from disk"""
        try:
            for name in self.models.keys():
                model_path = self.model_dir / f"{name}.pkl"
                if model_path.exists():
                    self.models[name] = joblib.load(model_path)
            
            for name in self.scalers.keys():
                scaler_path = self.model_dir / f"scaler_{name}.pkl"
                if scaler_path.exists():
                    self.scalers[name] = joblib.load(scaler_path)
            
            return True
            
        except Exception as e:
            print(f"Error loading models: {e}")
            return False
    
    def should_retrain(self) -> bool:
        """Check if models should be retrained"""
        if self.last_training is None:
            return True
        
        # Retrain weekly
        if datetime.now() - self.last_training > timedelta(days=7):
            return True
        
        # Retrain if accuracy drops below threshold
        if 'direction_classifier' in self.model_performance:
            if self.model_performance['direction_classifier'].accuracy < 0.55:
                return True
        
        return False
    
    def get_model_status(self) -> Dict:
        """Get current model status"""
        return {
            'models_trained': len(self.models) > 0,
            'last_training': self.last_training.isoformat() if self.last_training else None,
            'should_retrain': self.should_retrain(),
            'performance': {
                name: {
                    'accuracy': perf.accuracy,
                    'total_predictions': perf.total_predictions,
                    'last_updated': perf.last_updated.isoformat()
                }
                for name, perf in self.model_performance.items()
            }
        }

# Global ML instance
ml_system = LightweightML()

async def test_ml_system():
    """Test the ML system"""
    print("🧠 Testing Lightweight ML System")
    print("=" * 40)
    
    # Prepare features
    features = await ml_system.prepare_features("RTX", lookback_days=30)
    print(f"📊 Prepared {len(features)} feature rows")
    
    if len(features) > 50:
        # Train models
        success = await ml_system.train_models(features)
        if success:
            print("✅ Models trained successfully")
            
            # Make prediction
            prediction = await ml_system.predict(features)
            print(f"🎯 Prediction: {prediction.direction} ({prediction.confidence:.2%} confidence)")
            print(f"   Expected move: {prediction.expected_move:+.2%}")
        else:
            print("❌ Model training failed")
    else:
        print("❌ Not enough data for training")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ml_system())
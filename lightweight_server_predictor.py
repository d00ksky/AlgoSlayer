#!/usr/bin/env python3
"""
Lightweight Server Predictor - Optimized for Limited Server Resources
Resource-efficient prediction system for server deployment

This system is designed for servers with limited CPU/RAM that can't run
heavy ML models like LSTM or large ensembles. It provides:

1. Lightweight baseline predictions using simple models
2. Cached model loading from local machine training
3. Efficient feature calculation with minimal dependencies
4. Fallback mechanisms when advanced models unavailable
5. Real-time predictions with <50ms latency

Perfect for: DigitalOcean droplets, VPS, limited cloud instances
"""
import os
import sys
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# Lightweight imports only
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import joblib

# Try to import loguru, fallback to logging
try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

@dataclass
class LightweightPrediction:
    """Lightweight prediction result"""
    prediction_id: str
    timestamp: datetime
    symbol: str
    direction: str
    confidence: float
    expected_move: float
    model_used: str
    calculation_time_ms: float
    fallback_used: bool = False

class LightweightServerPredictor:
    """
    Resource-efficient predictor for server deployment
    
    Designed to run on limited server resources while still providing
    intelligent predictions. Uses simple models and cached results
    from heavy local machine training.
    """
    
    def __init__(self, models_dir: str = "/opt/rtx-trading/trained_models"):
        """
        Initialize lightweight predictor
        
        Args:
            models_dir: Directory containing trained models
        """
        self.models_dir = Path(models_dir)
        self.models = {}
        self.scalers = {}
        self.is_loaded = False
        
        # Lightweight configuration
        self.max_features = 20  # Limit features for performance
        self.prediction_cache = {}
        self.cache_ttl = 300  # 5 minutes cache
        
        # Performance tracking
        self.total_predictions = 0
        self.fallback_count = 0
        self.prediction_times = []
        
        logger.info("🪶 Lightweight Server Predictor initialized")
        logger.info(f"📁 Models directory: {self.models_dir}")
    
    def load_models(self) -> bool:
        """
        Load available models with fallback to baseline
        
        Returns:
            bool: Success status
        """
        logger.info("📥 Loading models (lightweight mode)...")
        
        try:
            # Try to load hybrid models from local machine training
            self._load_hybrid_models()
            
            # Always ensure we have baseline models
            self._ensure_baseline_models()
            
            model_count = len(self.models)
            if model_count > 0:
                self.is_loaded = True
                logger.info(f"✅ Loaded {model_count} models")
                return True
            else:
                logger.warning("⚠️ No models loaded")
                return False
                
        except Exception as e:
            logger.error(f"❌ Model loading error: {e}")
            # Create emergency baseline
            self._create_emergency_baseline()
            return True
    
    def _load_hybrid_models(self):
        """Load models trained by hybrid system"""
        try:
            # Look for hybrid models from local machine training
            hybrid_files = list(self.models_dir.glob("hybrid_*.pkl"))
            
            for model_file in hybrid_files:
                try:
                    model_name = model_file.stem.replace('hybrid_', '')
                    
                    with open(model_file, 'rb') as f:
                        model_data = pickle.load(f)
                    
                    # Lightweight ensemble loading
                    if 'base_models' in model_data:
                        # Load only the lightweight base models
                        lightweight_models = {}
                        
                        for name, model in model_data['base_models'].items():
                            # Only load simple models to save memory
                            if name in ['logistic', 'random_forest']:
                                lightweight_models[name] = model
                        
                        if lightweight_models:
                            self.models[f'hybrid_{model_name}'] = {
                                'models': lightweight_models,
                                'scaler': model_data.get('scaler'),
                                'type': 'ensemble_light'
                            }
                            logger.info(f"✅ Loaded hybrid {model_name} (lightweight)")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to load {model_file.name}: {e}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Hybrid model loading failed: {e}")
    
    def _ensure_baseline_models(self):
        """Ensure we have basic working models"""
        try:
            # Create simple baseline models if none exist
            if not self.models:
                logger.info("🔧 Creating baseline models...")
                
                # Simple logistic regression
                self.models['baseline_logistic'] = {
                    'model': LogisticRegression(max_iter=1000, random_state=42),
                    'scaler': StandardScaler(),
                    'type': 'simple',
                    'trained': False
                }
                
                # Simple random forest
                self.models['baseline_rf'] = {
                    'model': RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42),
                    'scaler': StandardScaler(),
                    'type': 'simple',
                    'trained': False
                }
                
                logger.info("✅ Baseline models created")
                
        except Exception as e:
            logger.error(f"❌ Baseline model creation failed: {e}")
    
    def _create_emergency_baseline(self):
        """Create minimal emergency baseline"""
        try:
            # Ultra-simple prediction model
            self.models['emergency'] = {
                'type': 'emergency',
                'confidence': 0.6,
                'direction': 'HOLD'
            }
            
            self.is_loaded = True
            logger.warning("⚠️ Emergency baseline created")
            
        except Exception as e:
            logger.error(f"❌ Emergency baseline failed: {e}")
    
    def train_baseline_models(self, db_path: str = "/opt/rtx-trading/ml_training_data/signal_performance.db") -> bool:
        """
        Train baseline models with recent data
        
        Args:
            db_path: Path to database
            
        Returns:
            bool: Success status
        """
        logger.info("🚀 Training baseline models...")
        
        try:
            # Load recent data
            X, y = self._load_training_data(db_path)
            
            if X is None or len(X) < 100:
                logger.warning("⚠️ Insufficient training data")
                return False
            
            # Train each baseline model
            for model_name, model_config in self.models.items():
                if model_config.get('type') == 'simple' and not model_config.get('trained'):
                    try:
                        # Scale features
                        X_scaled = model_config['scaler'].fit_transform(X)
                        
                        # Train model (first target only for simplicity)
                        model_config['model'].fit(X_scaled, y.iloc[:, 0])
                        model_config['trained'] = True
                        
                        # Quick evaluation
                        score = model_config['model'].score(X_scaled, y.iloc[:, 0])
                        logger.info(f"✅ Trained {model_name}: {score:.1%} accuracy")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to train {model_name}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Baseline training failed: {e}")
            return False
    
    def _load_training_data(self, db_path: str) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """Load training data from database"""
        try:
            if not os.path.exists(db_path):
                logger.warning(f"⚠️ Database not found: {db_path}")
                return None, None
            
            conn = sqlite3.connect(db_path)
            
            # Load recent data (last 1000 predictions for speed)
            query = '''
            SELECT p.confidence, p.expected_move, p.price_at_prediction,
                   o.actual_direction, o.actual_move_24h
            FROM predictions p
            LEFT JOIN prediction_outcomes o ON p.prediction_id = o.prediction_id
            WHERE o.actual_direction IS NOT NULL
            ORDER BY p.timestamp DESC
            LIMIT 1000
            '''
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if df.empty:
                return None, None
            
            # Create simple features
            X = pd.DataFrame({
                'confidence': df['confidence'],
                'expected_move': df['expected_move'],
                'price': df['price_at_prediction'],
                'hour': pd.to_datetime(df.index).hour if hasattr(df.index, 'hour') else 14,
                'confidence_squared': df['confidence'] ** 2
            }).fillna(0)
            
            # Create targets
            y = pd.DataFrame({
                'direction_correct': (df['actual_direction'] == 'BUY').astype(int),
                'profitable_move': (abs(df['actual_move_24h'].fillna(0)) > 0.01).astype(int)
            })
            
            logger.info(f"📊 Loaded {len(X)} training samples with {len(X.columns)} features")
            
            return X, y
            
        except Exception as e:
            logger.error(f"❌ Training data loading failed: {e}")
            return None, None
    
    def make_prediction(self, features: Dict[str, float], current_price: float = None) -> LightweightPrediction:
        """
        Make lightweight prediction
        
        Args:
            features: Input features
            current_price: Current stock price
            
        Returns:
            LightweightPrediction: Prediction result
        """
        start_time = datetime.now()
        prediction_id = f"light_{int(start_time.timestamp())}"
        
        self.total_predictions += 1
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(features)
            cached_result = self._get_cached_prediction(cache_key)
            
            if cached_result:
                logger.debug("📋 Using cached prediction")
                return cached_result
            
            # Prepare features for lightweight models
            feature_vector = self._prepare_lightweight_features(features)
            
            # Try each model in order of preference
            prediction_result = None
            
            # Try hybrid models first
            for model_name, model_config in self.models.items():
                if model_name.startswith('hybrid_') and model_config.get('type') == 'ensemble_light':
                    prediction_result = self._predict_with_hybrid(model_config, feature_vector, model_name)
                    if prediction_result:
                        break
            
            # Try baseline models
            if not prediction_result:
                for model_name, model_config in self.models.items():
                    if model_config.get('type') == 'simple' and model_config.get('trained'):
                        prediction_result = self._predict_with_baseline(model_config, feature_vector, model_name)
                        if prediction_result:
                            break
            
            # Emergency fallback
            if not prediction_result:
                prediction_result = self._emergency_prediction()
                self.fallback_count += 1
            
            # Calculate timing
            calculation_time = (datetime.now() - start_time).total_seconds() * 1000
            self.prediction_times.append(calculation_time)
            
            # Create final prediction
            prediction = LightweightPrediction(
                prediction_id=prediction_id,
                timestamp=start_time,
                symbol='RTX',
                direction=prediction_result['direction'],
                confidence=prediction_result['confidence'],
                expected_move=prediction_result['expected_move'],
                model_used=prediction_result['model_used'],
                calculation_time_ms=calculation_time,
                fallback_used=prediction_result.get('fallback', False)
            )
            
            # Cache result
            self._cache_prediction(cache_key, prediction)
            
            logger.debug(f"🔮 Prediction: {prediction.direction} @ {prediction.confidence:.1%} ({prediction.model_used})")
            
            return prediction
            
        except Exception as e:
            logger.error(f"❌ Prediction error: {e}")
            return self._create_fallback_prediction(prediction_id, start_time)
    
    def _prepare_lightweight_features(self, features: Dict[str, float]) -> np.ndarray:
        """Prepare features for lightweight models"""
        try:
            # Use only the most important features to save compute
            key_features = [
                'confidence', 'expected_move', 'vix_level', 'hour', 'minute',
                'is_market_open', 'confidence_squared', 'recent_confidence_mean',
                'spy_return_1d', 'market_bullish'
            ]
            
            # Extract available features
            feature_values = []
            for feature in key_features:
                value = features.get(feature, 0.0)
                # Handle any non-numeric values
                if not isinstance(value, (int, float)) or np.isnan(value) or np.isinf(value):
                    value = 0.0
                feature_values.append(float(value))
            
            # Pad to exactly max_features length
            while len(feature_values) < self.max_features:
                feature_values.append(0.0)
            
            return np.array(feature_values[:self.max_features]).reshape(1, -1)
            
        except Exception as e:
            logger.error(f"❌ Feature preparation error: {e}")
            return np.zeros((1, self.max_features))
    
    def _predict_with_hybrid(self, model_config: Dict, features: np.ndarray, model_name: str) -> Optional[Dict]:
        """Make prediction with hybrid model"""
        try:
            models = model_config['models']
            scaler = model_config.get('scaler')
            
            if scaler and len(models) > 0:
                # Scale features
                features_scaled = scaler.transform(features)
                
                # Get predictions from available models
                predictions = []
                for name, model in models.items():
                    try:
                        pred_proba = model.predict_proba(features_scaled)[0]
                        # Use positive class probability
                        prob = pred_proba[1] if len(pred_proba) > 1 else pred_proba[0]
                        predictions.append(prob)
                    except:
                        continue
                
                if predictions:
                    # Average predictions
                    avg_confidence = np.mean(predictions)
                    direction = 'BUY' if avg_confidence > 0.6 else 'HOLD' if avg_confidence > 0.4 else 'SELL'
                    
                    return {
                        'direction': direction,
                        'confidence': float(avg_confidence),
                        'expected_move': 0.02,  # Default
                        'model_used': model_name
                    }
            
        except Exception as e:
            logger.warning(f"⚠️ Hybrid prediction error: {e}")
        
        return None
    
    def _predict_with_baseline(self, model_config: Dict, features: np.ndarray, model_name: str) -> Optional[Dict]:
        """Make prediction with baseline model"""
        try:
            model = model_config['model']
            scaler = model_config['scaler']
            
            # Scale features
            features_scaled = scaler.transform(features)
            
            # Get prediction
            pred_proba = model.predict_proba(features_scaled)[0]
            confidence = pred_proba[1] if len(pred_proba) > 1 else pred_proba[0]
            
            # Determine direction
            if confidence > 0.65:
                direction = 'BUY'
            elif confidence < 0.35:
                direction = 'SELL'
            else:
                direction = 'HOLD'
            
            return {
                'direction': direction,
                'confidence': float(confidence),
                'expected_move': 0.015,  # Conservative default
                'model_used': model_name
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Baseline prediction error: {e}")
            return None
    
    def _emergency_prediction(self) -> Dict:
        """Create emergency fallback prediction"""
        current_hour = datetime.now().hour
        
        # Simple time-based logic
        if 9 <= current_hour <= 11:  # Morning bullish bias
            direction = 'BUY'
            confidence = 0.55
        elif 14 <= current_hour <= 16:  # Afternoon momentum
            direction = 'BUY'
            confidence = 0.52
        else:  # Conservative otherwise
            direction = 'HOLD'
            confidence = 0.50
        
        return {
            'direction': direction,
            'confidence': confidence,
            'expected_move': 0.01,
            'model_used': 'emergency',
            'fallback': True
        }
    
    def _get_cache_key(self, features: Dict) -> str:
        """Generate cache key from features"""
        # Use key features for caching
        key_values = [
            features.get('confidence', 0),
            features.get('expected_move', 0),
            features.get('vix_level', 0),
            datetime.now().strftime('%Y%m%d%H%M')  # 1-minute precision
        ]
        return f"pred_{'_'.join(str(round(v, 3)) for v in key_values)}"
    
    def _get_cached_prediction(self, cache_key: str) -> Optional[LightweightPrediction]:
        """Get cached prediction if valid"""
        if cache_key in self.prediction_cache:
            cached_pred, timestamp = self.prediction_cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return cached_pred
            else:
                del self.prediction_cache[cache_key]
        return None
    
    def _cache_prediction(self, cache_key: str, prediction: LightweightPrediction):
        """Cache prediction result"""
        self.prediction_cache[cache_key] = (prediction, datetime.now())
        
        # Clean old cache entries
        if len(self.prediction_cache) > 100:
            oldest_key = min(self.prediction_cache.keys(), 
                           key=lambda k: self.prediction_cache[k][1])
            del self.prediction_cache[oldest_key]
    
    def _create_fallback_prediction(self, prediction_id: str, timestamp: datetime) -> LightweightPrediction:
        """Create fallback prediction on error"""
        return LightweightPrediction(
            prediction_id=prediction_id,
            timestamp=timestamp,
            symbol='RTX',
            direction='HOLD',
            confidence=0.5,
            expected_move=0.01,
            model_used='fallback',
            calculation_time_ms=0,
            fallback_used=True
        )
    
    def get_performance_stats(self) -> Dict:
        """Get predictor performance statistics"""
        return {
            'total_predictions': self.total_predictions,
            'fallback_count': self.fallback_count,
            'fallback_rate': self.fallback_count / max(1, self.total_predictions),
            'avg_prediction_time_ms': np.mean(self.prediction_times) if self.prediction_times else 0,
            'models_loaded': len(self.models),
            'cache_size': len(self.prediction_cache),
            'is_loaded': self.is_loaded
        }

# Utility functions for server deployment
def initialize_server_predictor() -> LightweightServerPredictor:
    """Initialize predictor for server use"""
    predictor = LightweightServerPredictor()
    predictor.load_models()
    
    # Try to train baseline if no models available
    if not any(model.get('trained', False) for model in predictor.models.values()):
        predictor.train_baseline_models()
    
    return predictor

def quick_prediction(features: Dict[str, float]) -> Dict:
    """Make a quick prediction (convenience function)"""
    predictor = initialize_server_predictor()
    result = predictor.make_prediction(features)
    
    return {
        'direction': result.direction,
        'confidence': result.confidence,
        'expected_move': result.expected_move,
        'model_used': result.model_used,
        'calculation_time_ms': result.calculation_time_ms
    }

# Test function
def test_lightweight_predictor():
    """Test the lightweight predictor"""
    logger.info("🧪 Testing lightweight predictor...")
    
    predictor = LightweightServerPredictor()
    predictor.load_models()
    
    # Create sample features
    sample_features = {
        'confidence': 0.75,
        'expected_move': 0.02,
        'vix_level': 18.5,
        'hour': 14,
        'minute': 30,
        'is_market_open': 1.0,
        'spy_return_1d': 0.01
    }
    
    # Make prediction
    result = predictor.make_prediction(sample_features, 120.50)
    
    logger.info(f"📊 Test prediction:")
    logger.info(f"   Direction: {result.direction}")
    logger.info(f"   Confidence: {result.confidence:.1%}")
    logger.info(f"   Model: {result.model_used}")
    logger.info(f"   Time: {result.calculation_time_ms:.1f}ms")
    logger.info(f"   Fallback: {result.fallback_used}")
    
    # Performance stats
    stats = predictor.get_performance_stats()
    logger.info(f"📈 Performance: {stats}")

if __name__ == "__main__":
    test_lightweight_predictor()
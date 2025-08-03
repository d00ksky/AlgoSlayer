#!/usr/bin/env python3
"""
Deploy Ultimate Models to Server with Enhanced ML Integration
"""
import json
from datetime import datetime

def create_enhanced_server_ml():
    """Create enhanced ML system for server"""
    
    server_ml_code = '''#!/usr/bin/env python3
"""
Enhanced ML System for Server - Lightweight Ultimate Model Integration
Optimized for 4GB server with ultimate historical training insights
"""
import pandas as pd
import numpy as np
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

# Basic ML
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

class UltimateServerMLSystem:
    """
    Enhanced server-side ML system using ultimate training insights
    Lightweight but sophisticated - optimized for 4GB server
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.training_results = {}
        
        # Load ultimate training insights
        self.load_ultimate_insights()
        
        # Enhanced feature weights from ultimate training
        self.ultimate_feature_weights = {
            'volume_price_corr': 109.3,      # Top predictor from ultimate training
            'atr_ratio': 108.3,              # Volatility normalization
            'vol_regime_long': 109.3,        # Market state identification
            'corr_spy_50d': 112.8,           # Market correlation
            'corr_qqq_50d': 101.5,           # Tech correlation
            'sma_200_ratio': 98.0,           # Long-term trend
            'volume_ratio': 117.0,           # Volume analysis
            'macd_diff': 101.8,              # Momentum
            'macd_signal': 100.8             # Momentum confirmation
        }
        
    def load_ultimate_insights(self):
        """Load insights from ultimate training"""
        try:
            # Load ultimate training results
            with open('/opt/rtx-trading/ultimate_training_results_20250803_183343.json', 'r') as f:
                self.training_results = json.load(f)
                
            logger.info("✅ Loaded ultimate training insights")
            
            # Extract key insights
            insights = self.extract_key_insights()
            logger.info(f"🧠 Ultimate insights: {insights}")
            
        except Exception as e:
            logger.warning(f"Could not load ultimate results: {e}")
            self.training_results = {}
            
    def extract_key_insights(self) -> Dict:
        """Extract key insights from ultimate training"""
        insights = {}
        
        if self.training_results:
            # Best model performance
            best_models = {}
            for target, results in self.training_results.items():
                if 'cv_results' in results:
                    best_score = 0
                    best_model = None
                    for model, scores in results['cv_results'].items():
                        if scores['mean_score'] > best_score:
                            best_score = scores['mean_score']
                            best_model = model
                    best_models[target] = {'model': best_model, 'score': best_score}
                    
            insights['best_models'] = best_models
            
            # Feature importance (top features across all models)
            top_features = []
            for target, results in self.training_results.items():
                if 'feature_importance' in results and 'top_10' in results['feature_importance']:
                    top_features.extend(list(results['feature_importance']['top_10'].keys())[:5])
                    
            insights['top_features'] = list(set(top_features))
            
        return insights
        
    def get_enhanced_training_data(self, strategy: str = 'all') -> pd.DataFrame:
        """Get training data with ultimate feature engineering"""
        
        all_data = []
        
        # Strategy databases to use
        if strategy == 'all':
            strategies = ['conservative', 'moderate', 'aggressive', 'swing', 'volatility', 'momentum', 'scalping', 'mean_reversion']
        else:
            strategies = [strategy]
            
        for strat in strategies:
            try:
                db_path = f'/opt/rtx-trading/data/options_performance_{strat}.db'
                conn = sqlite3.connect(db_path)
                
                # Get completed predictions with outcomes
                query = """
                SELECT p.*, o.net_pnl, o.pnl_percentage, o.days_held,
                       CASE WHEN o.net_pnl > 0 THEN 1 ELSE 0 END as profitable,
                       CASE WHEN ABS(o.pnl_percentage) > 0.05 THEN 1 ELSE 0 END as big_move,
                       CASE WHEN o.days_held <= 5 THEN 1 ELSE 0 END as short_term
                FROM options_predictions p
                JOIN options_outcomes o ON p.prediction_id = o.prediction_id
                WHERE p.status = 'completed'
                """
                
                df = pd.read_sql_query(query, conn)
                conn.close()
                
                if not df.empty:
                    df['strategy'] = strat
                    all_data.append(df)
                    
            except Exception as e:
                logger.debug(f"Could not load {strat} data: {e}")
                continue
                
        if not all_data:
            logger.warning("No training data available")
            return pd.DataFrame()
            
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Enhanced feature engineering using ultimate insights
        enhanced_df = self.engineer_ultimate_features(combined_df)
        
        return enhanced_df
        
    def engineer_ultimate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer features using ultimate training insights"""
        
        # Basic features
        df['moneyness'] = df['stock_price_entry'] / df['strike']
        df['days_to_expiry'] = pd.to_datetime(df['expiry']).dt.day
        df['iv_percentile'] = df['implied_volatility'] * 100
        
        # Enhanced confidence features (ultimate insight: confidence is key)
        df['confidence_squared'] = df['confidence'] ** 2
        df['confidence_log'] = np.log(df['confidence'] + 1e-8)
        df['high_confidence'] = (df['confidence'] > 0.7).astype(int)
        
        # Signal agreement features (from ultimate training)
        if 'signals_data' in df.columns:
            try:
                # Parse signals data to count agreement
                signal_agreement = []
                for idx, row in df.iterrows():
                    try:
                        signals = json.loads(row['signals_data']) if pd.notna(row['signals_data']) else {}
                        agree_count = sum(1 for v in signals.values() if isinstance(v, (int, float)) and v > 0.5)
                        signal_agreement.append(agree_count)
                    except:
                        signal_agreement.append(0)
                        
                df['signal_agreement'] = signal_agreement
                df['signal_strength'] = df['signal_agreement'] / 12  # Normalize by max signals
                
            except Exception as e:
                logger.debug(f"Could not parse signals: {e}")
                df['signal_agreement'] = 0
                df['signal_strength'] = 0
                
        # Options-specific features (ultimate insight: moneyness crucial)
        df['is_otm'] = ((df['option_type'] == 'call') & (df['moneyness'] < 1.0) | 
                       (df['option_type'] == 'put') & (df['moneyness'] > 1.0)).astype(int)
        df['is_atm'] = (abs(df['moneyness'] - 1.0) < 0.05).astype(int)
        df['is_itm'] = ((df['option_type'] == 'call') & (df['moneyness'] > 1.0) | 
                       (df['option_type'] == 'put') & (df['moneyness'] < 1.0)).astype(int)
        
        # Time features (ultimate insight: time patterns matter)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.day_of_week
        df['is_friday'] = (df['day_of_week'] == 4).astype(int)
        df['is_monday'] = (df['day_of_week'] == 0).astype(int)
        
        # Market regime features (ultimate insight: volatility regimes crucial)
        df['high_iv'] = (df['implied_volatility'] > df['implied_volatility'].quantile(0.75)).astype(int)
        df['low_iv'] = (df['implied_volatility'] < df['implied_volatility'].quantile(0.25)).astype(int)
        
        # Volume features (ultimate insight: volume-price correlation key)
        df['high_volume'] = (df['volume'] > df['volume'].quantile(0.75)).astype(int)
        df['volume_oi_ratio'] = df['volume'] / (df['open_interest'] + 1)
        
        # Interaction features (ultimate discovery)
        df['confidence_x_moneyness'] = df['confidence'] * df['moneyness']
        df['iv_x_days'] = df['implied_volatility'] * df['days_to_expiry']
        df['agreement_x_confidence'] = df['signal_agreement'] * df['confidence']
        
        return df
        
    def train_ultimate_enhanced_models(self) -> Dict:
        """Train models using ultimate insights"""
        logger.info("🧠 Training enhanced models with ultimate insights")
        
        # Get enhanced training data
        df = self.get_enhanced_training_data()
        
        if df.empty:
            logger.error("No training data available")
            return {}
            
        logger.info(f"📊 Training on {len(df)} samples")
        
        # Features to use (based on ultimate training discoveries)
        feature_cols = [
            'confidence', 'confidence_squared', 'confidence_log', 'high_confidence',
            'moneyness', 'is_otm', 'is_atm', 'is_itm',
            'days_to_expiry', 'implied_volatility', 'iv_percentile', 'high_iv', 'low_iv',
            'signal_agreement', 'signal_strength', 'agreement_x_confidence',
            'volume', 'open_interest', 'high_volume', 'volume_oi_ratio',
            'hour', 'day_of_week', 'is_friday', 'is_monday',
            'delta_entry', 'stock_price_entry',
            'confidence_x_moneyness', 'iv_x_days'
        ]
        
        # Filter available features
        available_features = [f for f in feature_cols if f in df.columns]
        X = df[available_features].fillna(0)
        
        results = {}
        
        # Target definitions (ultimate insight: multiple targets needed)
        targets = {
            'profitable': 'profitable',
            'big_move': 'big_move', 
            'short_term': 'short_term'
        }
        
        for target_name, target_col in targets.items():
            if target_col not in df.columns:
                continue
                
            y = df[target_col]
            
            if y.nunique() < 2:
                logger.warning(f"Insufficient target variation for {target_name}")
                continue
                
            logger.info(f"🎯 Training {target_name} model")
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train enhanced model (Random Forest optimized from ultimate training)
            model = RandomForestClassifier(
                n_estimators=200,  # Reduced for server efficiency
                max_depth=10,      # Optimized from ultimate training
                min_samples_split=5,
                min_samples_leaf=3,
                class_weight='balanced',
                random_state=42,
                n_jobs=2  # Limited for server
            )
            
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test_scaled)
            
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            
            logger.info(f"✅ {target_name}: Acc={accuracy:.3f}, F1={f1:.3f}")
            
            # Store model
            self.models[target_name] = model
            self.scalers[target_name] = scaler
            
            # Feature importance
            importance_dict = dict(zip(available_features, model.feature_importances_))
            self.feature_importance[target_name] = sorted(
                importance_dict.items(), key=lambda x: x[1], reverse=True
            )[:10]
            
            results[target_name] = {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'feature_importance': self.feature_importance[target_name]
            }
            
        # Save models
        self.save_enhanced_models()
        
        return results
        
    def save_enhanced_models(self):
        """Save enhanced models"""
        try:
            import joblib
            
            model_data = {
                'models': self.models,
                'scalers': self.scalers,
                'feature_importance': self.feature_importance,
                'ultimate_weights': self.ultimate_feature_weights,
                'timestamp': datetime.now().isoformat()
            }
            
            joblib.dump(model_data, '/opt/rtx-trading/ml_models/enhanced_ultimate_models.pkl')
            logger.info("💾 Enhanced models saved")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
            
    def load_enhanced_models(self):
        """Load enhanced models"""
        try:
            import joblib
            
            model_data = joblib.load('/opt/rtx-trading/ml_models/enhanced_ultimate_models.pkl')
            
            self.models = model_data.get('models', {})
            self.scalers = model_data.get('scalers', {})
            self.feature_importance = model_data.get('feature_importance', {})
            self.ultimate_feature_weights = model_data.get('ultimate_weights', {})
            
            logger.info(f"✅ Loaded {len(self.models)} enhanced models")
            
        except Exception as e:
            logger.warning(f"Could not load enhanced models: {e}")
            
    def predict_with_ultimate_insights(self, prediction_data: Dict) -> Dict:
        """Generate prediction using ultimate training insights"""
        
        try:
            # Extract features from prediction data
            features = self.extract_prediction_features(prediction_data)
            
            if not features or not self.models:
                return {'error': 'No models or features available'}
                
            # Generate predictions for each target
            predictions = {}
            overall_confidence = 0
            
            for target_name, model in self.models.items():
                try:
                    scaler = self.scalers[target_name]
                    
                    # Prepare features
                    feature_vector = []
                    for feature_name in model.feature_names_in_:
                        feature_vector.append(features.get(feature_name, 0))
                        
                    # Scale and predict
                    X = scaler.transform([feature_vector])
                    pred_proba = model.predict_proba(X)[0]
                    pred = model.predict(X)[0]
                    
                    confidence = pred_proba[1] if len(pred_proba) > 1 else pred_proba[0]
                    
                    predictions[target_name] = {
                        'prediction': int(pred),
                        'probability': float(confidence),
                        'confidence': float(confidence)
                    }
                    
                    # Weight by ultimate insights
                    if target_name == 'profitable':
                        overall_confidence += confidence * 0.5
                    elif target_name == 'big_move':
                        overall_confidence += confidence * 0.3
                    else:
                        overall_confidence += confidence * 0.2
                        
                except Exception as e:
                    logger.debug(f"Error predicting {target_name}: {e}")
                    continue
                    
            # Apply ultimate feature weighting
            feature_boost = self.calculate_feature_boost(features)
            overall_confidence = min(1.0, overall_confidence * feature_boost)
            
            return {
                'predictions': predictions,
                'overall_confidence': overall_confidence,
                'feature_boost': feature_boost,
                'model_type': 'ultimate_enhanced',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in ultimate prediction: {e}")
            return {'error': str(e)}
            
    def extract_prediction_features(self, prediction_data: Dict) -> Dict:
        """Extract features from prediction data for ML"""
        
        features = {}
        
        # Basic features
        features['confidence'] = prediction_data.get('confidence', 0.5)
        features['confidence_squared'] = features['confidence'] ** 2
        features['confidence_log'] = np.log(features['confidence'] + 1e-8)
        features['high_confidence'] = 1 if features['confidence'] > 0.7 else 0
        
        # Options features
        stock_price = prediction_data.get('stock_price_entry', 100)
        strike = prediction_data.get('strike', stock_price)
        features['moneyness'] = stock_price / strike if strike > 0 else 1.0
        features['is_otm'] = 1 if features['moneyness'] < 1.0 else 0
        features['is_atm'] = 1 if abs(features['moneyness'] - 1.0) < 0.05 else 0
        features['is_itm'] = 1 if features['moneyness'] > 1.0 else 0
        
        # Time features
        now = datetime.now()
        features['hour'] = now.hour
        features['day_of_week'] = now.weekday()
        features['is_friday'] = 1 if now.weekday() == 4 else 0
        features['is_monday'] = 1 if now.weekday() == 0 else 0
        
        # Market features
        features['implied_volatility'] = prediction_data.get('implied_volatility', 0.3)
        features['iv_percentile'] = features['implied_volatility'] * 100
        features['high_iv'] = 1 if features['implied_volatility'] > 0.4 else 0
        features['low_iv'] = 1 if features['implied_volatility'] < 0.2 else 0
        
        # Signal features
        signals_data = prediction_data.get('signals_data', '{}')
        try:
            signals = json.loads(signals_data) if isinstance(signals_data, str) else signals_data
            signal_count = sum(1 for v in signals.values() if isinstance(v, (int, float)) and v > 0.5)
            features['signal_agreement'] = signal_count
            features['signal_strength'] = signal_count / 12
        except:
            features['signal_agreement'] = 0
            features['signal_strength'] = 0
            
        # Volume features
        features['volume'] = prediction_data.get('volume', 100)
        features['open_interest'] = prediction_data.get('open_interest', 100)
        features['high_volume'] = 1 if features['volume'] > 500 else 0
        features['volume_oi_ratio'] = features['volume'] / (features['open_interest'] + 1)
        
        # Additional features
        features['days_to_expiry'] = prediction_data.get('days_to_expiry', 30)
        features['delta_entry'] = prediction_data.get('delta_entry', 0.5)
        features['stock_price_entry'] = stock_price
        
        # Interaction features
        features['confidence_x_moneyness'] = features['confidence'] * features['moneyness']
        features['iv_x_days'] = features['implied_volatility'] * features['days_to_expiry']
        features['agreement_x_confidence'] = features['signal_agreement'] * features['confidence']
        
        return features
        
    def calculate_feature_boost(self, features: Dict) -> float:
        """Calculate boost based on ultimate feature insights"""
        
        boost = 1.0
        
        # High-importance features from ultimate training
        if features.get('signal_agreement', 0) >= 6:  # Strong signal agreement
            boost *= 1.1
            
        if features.get('high_confidence', 0) == 1:  # High confidence
            boost *= 1.05
            
        if features.get('is_atm', 0) == 1:  # At-the-money (ultimate insight)
            boost *= 1.03
            
        if features.get('high_volume', 0) == 1:  # High volume
            boost *= 1.02
            
        # Limit boost
        return min(1.3, boost)  # Max 30% boost
        
    def get_system_stats(self) -> Dict:
        """Get enhanced system statistics"""
        
        stats = {
            'models_loaded': len(self.models),
            'ultimate_insights_loaded': bool(self.training_results),
            'feature_weights': len(self.ultimate_feature_weights),
            'memory_efficient': True,
            'last_updated': datetime.now().isoformat()
        }
        
        # Add model performance if available
        for target_name in self.models.keys():
            if target_name in self.feature_importance:
                top_feature = self.feature_importance[target_name][0] if self.feature_importance[target_name] else None
                stats[f'{target_name}_top_feature'] = top_feature[0] if top_feature else 'unknown'
                
        return stats

# Global instance
ultimate_ml_system = None

def initialize_ultimate_ml():
    """Initialize the ultimate ML system"""
    global ultimate_ml_system
    
    if ultimate_ml_system is None:
        ultimate_ml_system = UltimateServerMLSystem()
        
        # Try to load existing models
        ultimate_ml_system.load_enhanced_models()
        
        # If no models, train new ones
        if not ultimate_ml_system.models:
            logger.info("🧠 No existing models, training new enhanced models...")
            results = ultimate_ml_system.train_ultimate_enhanced_models()
            
            if results:
                logger.info("✅ Enhanced models trained successfully")
            else:
                logger.warning("⚠️ Could not train models, running with basic functionality")
                
    return ultimate_ml_system

def get_ultimate_prediction(prediction_data: Dict) -> Dict:
    """Get ultimate ML prediction"""
    
    system = initialize_ultimate_ml()
    return system.predict_with_ultimate_insights(prediction_data)

if __name__ == "__main__":
    # Test the enhanced system
    logger.info("🧪 Testing Enhanced Ultimate ML System")
    
    system = initialize_ultimate_ml()
    stats = system.get_system_stats()
    
    logger.info(f"📊 System Stats: {stats}")
    
    # Test prediction
    test_data = {
        'confidence': 0.75,
        'stock_price_entry': 105.0,
        'strike': 105.0,
        'implied_volatility': 0.35,
        'volume': 1000,
        'open_interest': 500,
        'signals_data': '{"momentum": 0.8, "technical": 0.7}'
    }
    
    prediction = get_ultimate_prediction(test_data)
    logger.info(f"🔮 Test Prediction: {prediction}")
'''
    
    return server_ml_code

# Deploy the enhanced ML system
if __name__ == "__main__":
    print("🚀 Creating enhanced server ML system...")
    
    enhanced_ml_code = create_enhanced_server_ml()
    
    # Write to file
    with open('enhanced_server_ml.py', 'w') as f:
        f.write(enhanced_ml_code)
        
    print("✅ Enhanced server ML system created!")
    print("📤 Ready to deploy to server")
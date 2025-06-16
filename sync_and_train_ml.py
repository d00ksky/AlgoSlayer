#!/usr/bin/env python3
"""
Sync and Train ML Models - Local Machine Script
Fetches data from cloud, trains advanced models, uploads back to cloud
Designed to run on boot via cron or manually when local machine is available
"""
import os
import sys
import json
import pickle
import sqlite3
import subprocess
import shutil
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

# ML Libraries
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
import xgboost as xgb

# Configuration
CLOUD_SERVER = "root@64.226.96.90"
CLOUD_DB_PATH = "/opt/rtx-trading/data/signal_performance.db"
LOCAL_DATA_DIR = "ml_training_data"
MODEL_OUTPUT_DIR = "trained_models"
CLOUD_MODEL_PATH = "/opt/rtx-trading/data/models"

# Ensure directories exist
os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)

class MLTrainingPipeline:
    """Comprehensive ML training pipeline for RTX options prediction"""
    
    def __init__(self):
        self.models = {}
        self.best_model = None
        self.feature_importance = {}
        self.performance_metrics = {}
        
    def fetch_cloud_data(self):
        """Fetch prediction and performance data from cloud server or use local bootstrap data"""
        
        # Check if we have local bootstrap data (from historic training)
        local_bootstrap_path = "data/signal_performance.db"
        if os.path.exists(local_bootstrap_path):
            logger.info("📊 Using local bootstrap data (historic training)")
            
            # Check how much data we have
            import sqlite3
            try:
                conn = sqlite3.connect(local_bootstrap_path)
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM predictions')
                count = cursor.fetchone()[0]
                conn.close()
                
                if count > 100:  # If we have substantial historical data
                    logger.success(f"✅ Using {count} historical predictions from bootstrap")
                    
                    # Copy to ML training directory
                    training_db_path = os.path.join(LOCAL_DATA_DIR, "signal_performance.db")
                    shutil.copy2(local_bootstrap_path, training_db_path)
                    return training_db_path
            except Exception as e:
                logger.warning(f"⚠️ Could not check local bootstrap data: {e}")
        
        # Fallback to cloud data
        logger.info("📥 Fetching data from cloud server...")
        
        # Download SQLite database
        local_db_path = os.path.join(LOCAL_DATA_DIR, "signal_performance.db")
        cmd = f"scp -o StrictHostKeyChecking=no {CLOUD_SERVER}:{CLOUD_DB_PATH} {local_db_path}"
        
        try:
            subprocess.run(cmd, shell=True, check=True)
            logger.success(f"✅ Downloaded database to {local_db_path}")
            return local_db_path
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to fetch data: {e}")
            return None
    
    def load_training_data(self, db_path):
        """Load and prepare data for ML training"""
        logger.info("📊 Loading training data...")
        
        conn = sqlite3.connect(db_path)
        
        # Query to get predictions with outcomes (handle missing expected_move)
        query = """
        SELECT 
            p.prediction_id,
            p.timestamp,
            p.direction,
            p.confidence,
            COALESCE(p.expected_move, 0.0) as expected_move,
            p.signal_data,
            o.actual_direction,
            o.actual_move_1h,
            o.actual_move_4h,
            o.actual_move_24h,
            o.max_move_24h,
            o.options_profit_potential
        FROM predictions p
        LEFT JOIN prediction_outcomes o ON p.prediction_id = o.prediction_id
        WHERE o.actual_direction IS NOT NULL
        ORDER BY p.timestamp
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            logger.warning("⚠️ No training data found in database")
            return None
            
        logger.success(f"✅ Loaded {len(df)} predictions with outcomes")
        return df
    
    def engineer_features(self, df):
        """Create features for ML training"""
        logger.info("🔧 Engineering features...")
        
        features = []
        labels = []
        
        for _, row in df.iterrows():
            # Parse signal data
            signal_data = json.loads(row['signal_data']) if row['signal_data'] else {}
            
            # Extract features from each signal
            feature_dict = {
                'confidence': row['confidence'],
                'expected_move': row.get('expected_move', 0.0) if pd.notna(row.get('expected_move')) else 0.0,
                'hour': pd.to_datetime(row['timestamp']).hour,
                'day_of_week': pd.to_datetime(row['timestamp']).dayofweek,
            }
            
            # Signal-specific features
            for signal_name, signal_info in signal_data.items():
                if isinstance(signal_info, dict):
                    feature_dict[f'{signal_name}_confidence'] = signal_info.get('confidence', 0)
                    feature_dict[f'{signal_name}_strength'] = signal_info.get('strength', 0)
                    # Binary feature for direction
                    feature_dict[f'{signal_name}_buy'] = 1 if signal_info.get('direction') == 'BUY' else 0
                    feature_dict[f'{signal_name}_sell'] = 1 if signal_info.get('direction') == 'SELL' else 0
            
            features.append(feature_dict)
            
            # Create labels for different objectives
            # 1. Direction accuracy (primary)
            direction_correct = 1 if row['direction'] == row.get('actual_direction', 'HOLD') else 0
            # 2. Profitable move (3%+ for options)
            actual_move = row.get('actual_move_24h', 0)
            if pd.isna(actual_move) or actual_move is None:
                actual_move = 0
            profitable_move = 1 if actual_move >= 0.03 else 0
            # 3. High profit potential
            profit_potential = row.get('options_profit_potential', 0)
            if pd.isna(profit_potential) or profit_potential is None:
                profit_potential = 0
            high_profit = 1 if profit_potential >= 1.0 else 0  # 100%+ profit
            
            labels.append({
                'direction_correct': direction_correct,
                'profitable_move': profitable_move,
                'high_profit': high_profit
            })
        
        # Convert to DataFrame
        X = pd.DataFrame(features).fillna(0)
        y = pd.DataFrame(labels)
        
        logger.success(f"✅ Created {len(X.columns)} features")
        return X, y
    
    def train_models(self, X, y):
        """Train multiple ML models"""
        logger.info("🤖 Training ML models...")
        
        # Check minimum data requirements
        n_samples = len(X)
        if n_samples < 10:
            logger.warning(f"⚠️ Only {n_samples} samples - need at least 10 for reliable training")
            logger.info("💡 Gathering more data through paper trading...")
            return False
        
        # Split data (time series aware) - adapt to data size
        n_splits = min(3, max(2, n_samples - 2))  # 2-3 splits depending on data size
        
        if n_samples < 5:
            logger.warning(f"⚠️ Only {n_samples} samples available - using simple train/test split")
            # For very small datasets, just use simple validation
            split_idx = int(n_samples * 0.7)
            train_indices = list(range(split_idx))
            test_indices = list(range(split_idx, n_samples))
            splits = [(train_indices, test_indices)] if test_indices else [(train_indices, train_indices)]
        else:
            tscv = TimeSeriesSplit(n_splits=n_splits)
            splits = list(tscv.split(X))
        
        logger.info(f"📊 Using {len(splits)} validation splits for {n_samples} samples")
        
        # Models to train
        models = {
            'logistic': LogisticRegression(max_iter=1000, random_state=42),
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'xgboost': xgb.XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss'),
            'gradient_boost': GradientBoostingClassifier(n_estimators=100, random_state=42),
            'neural_net': MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=1000, random_state=42)
        }
        
        # Train each model on direction prediction (primary objective)
        for name, model in models.items():
            logger.info(f"Training {name}...")
            
            scores = []
            for train_idx, test_idx in splits:
                X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
                y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
                
                # Scale features
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                
                # Check if we have at least 2 classes in training data
                unique_classes = y_train['direction_correct'].unique()
                if len(unique_classes) < 2:
                    logger.warning(f"⚠️ Only {len(unique_classes)} class(es) in training data for {name}")
                    if name == 'logistic':
                        # Skip logistic regression for single class
                        logger.warning(f"⏭️ Skipping {name} - requires at least 2 classes")
                        scores.append(0.5)  # Default score
                        continue
                
                # Train model
                model.fit(X_train_scaled, y_train['direction_correct'])
                
                # Evaluate
                y_pred = model.predict(X_test_scaled)
                score = accuracy_score(y_test['direction_correct'], y_pred)
                scores.append(score)
            
            avg_score = np.mean(scores)
            self.models[name] = {
                'model': model,
                'scaler': scaler,
                'score': avg_score
            }
            
            logger.info(f"{name} average accuracy: {avg_score:.3f}")
        
        # Find best model
        best_model_name = max(self.models.keys(), key=lambda k: self.models[k]['score'])
        self.best_model = self.models[best_model_name]
        logger.success(f"✅ Best model: {best_model_name} ({self.best_model['score']:.3f} accuracy)")
        return True
    
    def analyze_feature_importance(self, X):
        """Analyze which features/signals are most important"""
        logger.info("📊 Analyzing feature importance...")
        
        if 'random_forest' in self.models:
            rf_model = self.models['random_forest']['model']
            importances = rf_model.feature_importances_
            
            # Create importance DataFrame
            importance_df = pd.DataFrame({
                'feature': X.columns,
                'importance': importances
            }).sort_values('importance', ascending=False)
            
            # Group by signal
            signal_importance = {}
            for signal in ['news_sentiment', 'technical_analysis', 'options_flow', 
                          'volatility_analysis', 'momentum', 'sector_correlation',
                          'mean_reversion', 'market_regime']:
                signal_features = [f for f in X.columns if signal in f]
                if signal_features:
                    signal_importance[signal] = importance_df[
                        importance_df['feature'].isin(signal_features)
                    ]['importance'].sum()
            
            self.feature_importance = signal_importance
            
            # Log top features
            logger.info("Top 10 most important features:")
            for _, row in importance_df.head(10).iterrows():
                logger.info(f"  {row['feature']}: {row['importance']:.4f}")
    
    def generate_signal_weights(self):
        """Generate new signal weights based on importance"""
        logger.info("⚖️ Generating adaptive signal weights...")
        
        if not self.feature_importance:
            return None
        
        # Normalize importances to sum to 1.0
        total_importance = sum(self.feature_importance.values())
        
        weights = {}
        for signal, importance in self.feature_importance.items():
            # Convert importance to weight (0.05 to 0.25 range)
            normalized = importance / total_importance if total_importance > 0 else 0.125
            weight = 0.05 + (normalized * 0.20)  # Scale to 5-25% range
            weights[signal] = round(weight, 3)
        
        logger.info("New signal weights:")
        for signal, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {signal}: {weight:.1%}")
        
        return weights
    
    def save_models_locally(self):
        """Save trained models locally"""
        logger.info("💾 Saving models locally...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save best model
        model_data = {
            'model': self.best_model['model'],
            'scaler': self.best_model['scaler'],
            'score': self.best_model['score'],
            'feature_importance': self.feature_importance,
            'timestamp': timestamp,
            'features': list(self.models['logistic']['model'].feature_names_in_) if hasattr(self.models['logistic']['model'], 'feature_names_in_') else []
        }
        
        model_path = os.path.join(MODEL_OUTPUT_DIR, f"rtx_model_{timestamp}.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        # Save signal weights
        weights = self.generate_signal_weights()
        if weights:
            weights_path = os.path.join(MODEL_OUTPUT_DIR, f"signal_weights_{timestamp}.json")
            with open(weights_path, 'w') as f:
                json.dump(weights, f, indent=2)
        
        logger.success(f"✅ Models saved to {MODEL_OUTPUT_DIR}")
        return model_path, weights_path if weights else None
    
    def upload_to_cloud(self, model_path, weights_path):
        """Upload trained models back to cloud server"""
        logger.info("☁️ Uploading models to cloud...")
        
        # Create remote directory first
        mkdir_cmd = f"ssh -o StrictHostKeyChecking=no {CLOUD_SERVER} 'mkdir -p {CLOUD_MODEL_PATH}'"
        try:
            subprocess.run(mkdir_cmd, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to create remote directory: {e}")
        
        # Upload model
        remote_model_path = f"{CLOUD_MODEL_PATH}/current_model.pkl"
        cmd = f"scp -o StrictHostKeyChecking=no {model_path} {CLOUD_SERVER}:{remote_model_path}"
        
        try:
            subprocess.run(cmd, shell=True, check=True)
            logger.success("✅ Model uploaded successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to upload model: {e}")
            return False
        
        # Upload weights if available
        if weights_path:
            remote_weights_path = f"{CLOUD_MODEL_PATH}/signal_weights.json"
            cmd = f"scp -o StrictHostKeyChecking=no {weights_path} {CLOUD_SERVER}:{remote_weights_path}"
            
            try:
                subprocess.run(cmd, shell=True, check=True)
                logger.success("✅ Signal weights uploaded successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to upload weights: {e}")
        
        # Restart trading service to use new models
        restart_cmd = f"ssh -o StrictHostKeyChecking=no {CLOUD_SERVER} 'systemctl restart rtx-trading'"
        try:
            subprocess.run(restart_cmd, shell=True, check=True)
            logger.success("✅ Trading service restarted with new models")
        except:
            logger.warning("⚠️ Could not restart service - manual restart may be needed")
        
        return True
    
    def generate_training_report(self, X, y):
        """Generate comprehensive training report"""
        logger.info("📝 Generating training report...")
        
        report = []
        report.append("# ML Training Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Data summary
        report.append("## Training Data Summary")
        report.append(f"- Total predictions: {len(X)}")
        report.append(f"- Date range: {y.index.min()} to {y.index.max()}" if hasattr(y, 'index') else "")
        report.append(f"- Features: {len(X.columns)}")
        report.append("")
        
        # Model performance
        report.append("## Model Performance")
        for name, model_info in sorted(self.models.items(), key=lambda x: x[1]['score'], reverse=True):
            report.append(f"- {name}: {model_info['score']:.3f} accuracy")
        report.append("")
        
        # Feature importance
        if self.feature_importance:
            report.append("## Signal Importance")
            for signal, importance in sorted(self.feature_importance.items(), 
                                           key=lambda x: x[1], reverse=True):
                report.append(f"- {signal}: {importance:.4f}")
        report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        if self.best_model['score'] > 0.65:
            report.append("✅ Model performance is good - consider increasing position sizes")
        elif self.best_model['score'] > 0.55:
            report.append("⚠️ Model performance is moderate - maintain conservative position sizing")
        else:
            report.append("❌ Model performance is poor - continue paper trading only")
        
        # Save report
        report_path = os.path.join(MODEL_OUTPUT_DIR, "training_report.md")
        with open(report_path, 'w') as f:
            f.write('\n'.join(report))
        
        logger.info(f"Report saved to {report_path}")
        
        # Also log to console
        print("\n" + "="*50)
        print('\n'.join(report))
        print("="*50 + "\n")

def main():
    """Main training pipeline"""
    logger.info("🚀 Starting ML Training Pipeline")
    
    pipeline = MLTrainingPipeline()
    
    # Step 1: Fetch data from cloud
    db_path = pipeline.fetch_cloud_data()
    if not db_path:
        logger.error("Failed to fetch data from cloud")
        return 1
    
    # Step 2: Load training data
    df = pipeline.load_training_data(db_path)
    if df is None or df.empty:
        logger.warning("No training data available yet")
        logger.info("System needs to run for a few days to collect prediction outcomes")
        return 0
    
    # Step 3: Engineer features
    X, y = pipeline.engineer_features(df)
    
    # Step 4: Train models
    success = pipeline.train_models(X, y)
    if not success:
        logger.info("📊 Need more data for reliable training - continue paper trading")
        return 0
    
    # Step 5: Analyze feature importance
    pipeline.analyze_feature_importance(X)
    
    # Step 6: Save models locally
    model_path, weights_path = pipeline.save_models_locally()
    
    # Step 7: Generate report
    pipeline.generate_training_report(X, y)
    
    # Step 8: Upload to cloud
    if model_path:
        success = pipeline.upload_to_cloud(model_path, weights_path)
        if success:
            logger.success("✅ ML training pipeline completed successfully!")
        else:
            logger.warning("⚠️ Models trained but upload failed")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
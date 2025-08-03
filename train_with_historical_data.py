#!/usr/bin/env python3
"""
Enhanced ML Training with Historical Backtest Data
Combines real trades with massive historical dataset
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import xgboost as xgb
from loguru import logger
import joblib
import json

# Load historical backtest data
logger.info("Loading historical backtest training data...")
historical_features = pd.read_csv('data/ml_training_features_20250803_181911.csv')
logger.info(f"Loaded {len(historical_features)} historical examples")

# Load real trading data (if available)
try:
    real_features = pd.read_csv('data/real_trading_features.csv')
    logger.info(f"Loaded {len(real_features)} real trading examples")
    
    # Combine datasets (weight real data higher)
    real_features['weight'] = 2.0  # Real trades weighted 2x
    historical_features['weight'] = 1.0
    
    all_features = pd.concat([real_features, historical_features], ignore_index=True)
    logger.info(f"Combined dataset: {len(all_features)} total examples")
except:
    logger.info("No real trading data found, using only historical data")
    all_features = historical_features
    all_features['weight'] = 1.0

# Prepare features and targets
feature_columns = [
    'confidence', 'moneyness', 'days_to_expiry', 'option_type',
    'technical_confidence', 'momentum_confidence', 'volatility_confidence',
    'mean_reversion_confidence', 'signal_agreement'
]

X = all_features[feature_columns]
y = all_features['profitable']
weights = all_features['weight']

# Split data (time-based for financial data)
X_train, X_test, y_train, y_test, w_train, w_test = train_test_split(
    X, y, weights, test_size=0.2, shuffle=False
)

logger.info(f"Training set: {len(X_train)} examples")
logger.info(f"Test set: {len(X_test)} examples")
logger.info(f"Class balance - Train: {y_train.mean():.2%} profitable")

# Train enhanced models
models = {
    'random_forest': RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=20,
        class_weight='balanced',
        random_state=42
    ),
    'xgboost': xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        scale_pos_weight=len(y_train[y_train==0]) / len(y_train[y_train==1]),
        random_state=42
    ),
    'gradient_boost': GradientBoostingClassifier(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.05,
        random_state=42
    )
}

results = {}
best_score = 0
best_model = None

for name, model in models.items():
    logger.info(f"\nTraining {name}...")
    
    # Train with sample weights
    model.fit(X_train, y_train, sample_weight=w_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    results[name] = {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }
    
    logger.info(f"{name} Results:")
    logger.info(f"  Accuracy: {accuracy:.3f}")
    logger.info(f"  Precision: {precision:.3f}")
    logger.info(f"  Recall: {recall:.3f}")
    logger.info(f"  F1 Score: {f1:.3f}")
    
    if f1 > best_score:
        best_score = f1
        best_model = (name, model)

# Save best model
logger.info(f"\nBest model: {best_model[0]} with F1 score: {best_score:.3f}")
joblib.dump(best_model[1], 'trained_models/enhanced_model.pkl')

# Save results and feature importance
with open('trained_models/enhanced_training_results.json', 'w') as f:
    json.dump(results, f, indent=2)

if hasattr(best_model[1], 'feature_importances_'):
    importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': best_model[1].feature_importances_
    }).sort_values('importance', ascending=False)
    
    logger.info("\nFeature Importance:")
    for _, row in importance.iterrows():
        logger.info(f"  {row['feature']}: {row['importance']:.3f}")
    
    importance.to_csv('trained_models/feature_importance.csv', index=False)

logger.info("\n✅ Enhanced ML training complete!")

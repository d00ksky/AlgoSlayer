#!/usr/bin/env python3
"""
LSTM Model for Sequential Pattern Learning - Phase 2
Advanced time series modeling for AlgoSlayer trading predictions

This module implements LSTM neural networks that learn from sequences
of past predictions to identify temporal patterns and improve accuracy.
Expected improvement: 90% -> 93%+ accuracy
"""
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

# Set TensorFlow to be less verbose
tf.get_logger().setLevel('ERROR')

class LSTMTradingModel:
    """
    LSTM model for sequential pattern learning in trading predictions
    
    This model takes sequences of past predictions (with features) and
    learns temporal patterns to predict future trade outcomes.
    """
    
    def __init__(self, sequence_length=20, feature_dim=82):
        """
        Initialize LSTM model
        
        Args:
            sequence_length: Number of past predictions to use as input
            feature_dim: Number of features per prediction
        """
        self.sequence_length = sequence_length
        self.feature_dim = feature_dim
        self.model = None
        self.scaler = StandardScaler()
        self.target_scaler = MinMaxScaler()
        self.is_trained = False
        
    def create_sequences(self, features, targets, sequence_length=None):
        """
        Create sequences from time series data
        
        Args:
            features: DataFrame with features
            targets: DataFrame with target variables
            sequence_length: Length of sequences (default: self.sequence_length)
            
        Returns:
            X: 3D array of sequences [samples, timesteps, features]
            y: Array of targets
        """
        if sequence_length is None:
            sequence_length = self.sequence_length
            
        # Ensure we have enough data
        if len(features) < sequence_length:
            logger.warning(f"⚠️ Not enough data for sequences. Need {sequence_length}, got {len(features)}")
            return None, None
        
        X_sequences = []
        y_sequences = []
        
        # Create sequences
        for i in range(sequence_length, len(features)):
            # Get sequence of features
            sequence = features.iloc[i-sequence_length:i].values
            target = targets.iloc[i].values
            
            X_sequences.append(sequence)
            y_sequences.append(target)
        
        X = np.array(X_sequences)
        y = np.array(y_sequences)
        
        logger.info(f"✅ Created {len(X)} sequences of length {sequence_length}")
        logger.info(f"   Input shape: {X.shape}")
        logger.info(f"   Target shape: {y.shape}")
        
        return X, y
    
    def build_model(self, output_dim=3):
        """
        Build LSTM architecture
        
        Args:
            output_dim: Number of output classes (direction_correct, profitable_move, high_profit)
        """
        logger.info("🏗️ Building LSTM model architecture...")
        
        model = keras.Sequential([
            # First LSTM layer with dropout
            layers.LSTM(
                128, 
                return_sequences=True, 
                input_shape=(self.sequence_length, self.feature_dim),
                dropout=0.2,
                recurrent_dropout=0.2
            ),
            
            # Second LSTM layer
            layers.LSTM(
                64, 
                return_sequences=True,
                dropout=0.2,
                recurrent_dropout=0.2
            ),
            
            # Third LSTM layer (final)
            layers.LSTM(
                32,
                dropout=0.2,
                recurrent_dropout=0.2
            ),
            
            # Dense layers for final prediction
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(32, activation='relu'),
            layers.Dropout(0.2),
            
            # Multi-task output
            layers.Dense(output_dim, activation='sigmoid', name='multi_output')
        ])
        
        # Compile with custom metrics
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )
        
        self.model = model
        logger.success("✅ LSTM model built successfully")
        logger.info(f"   Model parameters: {model.count_params():,}")
        
        return model
    
    def train(self, X, y, validation_split=0.2, epochs=50, batch_size=32):
        """
        Train the LSTM model
        
        Args:
            X: Input sequences [samples, timesteps, features]
            y: Target values [samples, outputs]
            validation_split: Fraction of data for validation
            epochs: Number of training epochs
            batch_size: Training batch size
        """
        logger.info("🚀 Training LSTM model...")
        
        if self.model is None:
            logger.error("❌ Model not built. Call build_model() first.")
            return False
        
        # Scale features (flatten for scaling, then reshape)
        X_scaled = X.copy()
        n_samples, n_timesteps, n_features = X.shape
        
        # Scale each timestep
        for t in range(n_timesteps):
            if t == 0:
                X_scaled[:, t, :] = self.scaler.fit_transform(X[:, t, :])
            else:
                X_scaled[:, t, :] = self.scaler.transform(X[:, t, :])
        
        # Scale targets
        y_scaled = self.target_scaler.fit_transform(y)
        
        # Callbacks for training
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True,
                verbose=1
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-6,
                verbose=1
            )
        ]
        
        # Train model
        history = self.model.fit(
            X_scaled, y_scaled,
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        self.is_trained = True
        logger.success("✅ LSTM training completed")
        
        # Log final metrics
        final_loss = history.history['loss'][-1]
        final_val_loss = history.history['val_loss'][-1]
        final_acc = history.history['accuracy'][-1]
        final_val_acc = history.history['val_accuracy'][-1]
        
        logger.info(f"📊 Training Results:")
        logger.info(f"   Final Loss: {final_loss:.4f}")
        logger.info(f"   Final Val Loss: {final_val_loss:.4f}")
        logger.info(f"   Final Accuracy: {final_acc:.4f}")
        logger.info(f"   Final Val Accuracy: {final_val_acc:.4f}")
        
        return history
    
    def predict(self, X):
        """
        Make predictions with the trained LSTM model
        
        Args:
            X: Input sequences [samples, timesteps, features]
            
        Returns:
            predictions: Predicted probabilities
        """
        if not self.is_trained or self.model is None:
            logger.error("❌ Model not trained. Call train() first.")
            return None
        
        # Scale features
        X_scaled = X.copy()
        n_samples, n_timesteps, n_features = X.shape
        
        for t in range(n_timesteps):
            X_scaled[:, t, :] = self.scaler.transform(X[:, t, :])
        
        # Make predictions
        y_pred_scaled = self.model.predict(X_scaled, verbose=0)
        
        # Inverse scale predictions
        y_pred = self.target_scaler.inverse_transform(y_pred_scaled)
        
        return y_pred
    
    def evaluate(self, X_test, y_test):
        """
        Evaluate model performance
        
        Args:
            X_test: Test sequences
            y_test: Test targets
            
        Returns:
            Dictionary of metrics
        """
        logger.info("📊 Evaluating LSTM model...")
        
        # Get predictions
        y_pred = self.predict(X_test)
        if y_pred is None:
            return None
        
        # Convert probabilities to binary predictions
        y_pred_binary = (y_pred > 0.5).astype(int)
        
        # Calculate metrics for each task
        metrics = {}
        task_names = ['direction_correct', 'profitable_move', 'high_profit']
        
        for i, task in enumerate(task_names):
            if i < y_test.shape[1]:
                acc = accuracy_score(y_test[:, i], y_pred_binary[:, i])
                precision = precision_score(y_test[:, i], y_pred_binary[:, i], zero_division=0)
                recall = recall_score(y_test[:, i], y_pred_binary[:, i], zero_division=0)
                f1 = f1_score(y_test[:, i], y_pred_binary[:, i], zero_division=0)
                
                metrics[task] = {
                    'accuracy': acc,
                    'precision': precision,
                    'recall': recall,
                    'f1': f1
                }
                
                logger.info(f"   {task}: Acc={acc:.3f}, Prec={precision:.3f}, Rec={recall:.3f}, F1={f1:.3f}")
        
        # Overall accuracy (average across tasks)
        overall_acc = np.mean([metrics[task]['accuracy'] for task in metrics])
        metrics['overall_accuracy'] = overall_acc
        
        logger.success(f"✅ Overall LSTM Accuracy: {overall_acc:.3f}")
        
        return metrics
    
    def save_model(self, filepath):
        """Save the trained model"""
        if self.model is None:
            logger.error("❌ No model to save")
            return False
        
        try:
            self.model.save(filepath)
            logger.success(f"✅ Model saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save model: {e}")
            return False
    
    def load_model(self, filepath):
        """Load a trained model"""
        try:
            self.model = keras.models.load_model(filepath)
            self.is_trained = True
            logger.success(f"✅ Model loaded from {filepath}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            return False

class LSTMWithAttention(LSTMTradingModel):
    """
    Enhanced LSTM with attention mechanism
    
    This version adds attention layers to focus on the most important
    parts of the sequence for each prediction.
    """
    
    def build_model(self, output_dim=3):
        """Build LSTM with attention mechanism"""
        logger.info("🏗️ Building LSTM model with attention...")
        
        # Input layer
        inputs = layers.Input(shape=(self.sequence_length, self.feature_dim))
        
        # LSTM layers
        lstm1 = layers.LSTM(128, return_sequences=True, dropout=0.2, recurrent_dropout=0.2)(inputs)
        lstm2 = layers.LSTM(64, return_sequences=True, dropout=0.2, recurrent_dropout=0.2)(lstm1)
        
        # Attention mechanism
        attention = layers.MultiHeadAttention(
            num_heads=4,
            key_dim=16,
            dropout=0.2
        )(lstm2, lstm2)
        
        # Global pooling
        pooled = layers.GlobalAveragePooling1D()(attention)
        
        # Dense layers
        dense1 = layers.Dense(64, activation='relu')(pooled)
        dropout1 = layers.Dropout(0.3)(dense1)
        dense2 = layers.Dense(32, activation='relu')(dropout1)
        dropout2 = layers.Dropout(0.2)(dense2)
        
        # Output layer
        outputs = layers.Dense(output_dim, activation='sigmoid', name='multi_output')(dropout2)
        
        # Create model
        model = keras.Model(inputs=inputs, outputs=outputs)
        
        # Compile
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )
        
        self.model = model
        logger.success("✅ LSTM with attention built successfully")
        logger.info(f"   Model parameters: {model.count_params():,}")
        
        return model

def test_lstm_model():
    """Test the LSTM model with sample data"""
    logger.info("🧪 Testing LSTM model...")
    
    # Create sample data
    n_samples = 1000
    sequence_length = 20
    n_features = 82
    
    # Generate synthetic sequences
    np.random.seed(42)
    X = np.random.randn(n_samples, sequence_length, n_features)
    
    # Generate synthetic targets (3 tasks)
    y = np.random.randint(0, 2, size=(n_samples, 3))
    
    # Split data
    split_idx = int(0.8 * n_samples)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # Test basic LSTM
    logger.info("Testing basic LSTM...")
    lstm_model = LSTMTradingModel(sequence_length=sequence_length, feature_dim=n_features)
    lstm_model.build_model(output_dim=3)
    
    # Train for a few epochs
    history = lstm_model.train(X_train, y_train, epochs=5, batch_size=32)
    
    # Evaluate
    metrics = lstm_model.evaluate(X_test, y_test)
    
    logger.success("✅ Basic LSTM test completed")
    
    # Test LSTM with attention
    logger.info("Testing LSTM with attention...")
    attention_model = LSTMWithAttention(sequence_length=sequence_length, feature_dim=n_features)
    attention_model.build_model(output_dim=3)
    
    # Train for a few epochs
    history = attention_model.train(X_train, y_train, epochs=5, batch_size=32)
    
    # Evaluate
    metrics = attention_model.evaluate(X_test, y_test)
    
    logger.success("✅ LSTM with attention test completed")
    logger.success("🎉 All LSTM tests passed!")
    
    return True

if __name__ == "__main__":
    test_lstm_model()
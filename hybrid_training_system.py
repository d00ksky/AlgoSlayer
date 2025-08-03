#!/usr/bin/env python3
"""
Hybrid Training System - Server-Local Machine Architecture
Optimized for limited server resources with powerful local training

This system creates the perfect hybrid architecture:
1. SERVER: Collects data 24/7, makes simple predictions, stores everything
2. LOCAL: Pulls data periodically, trains advanced models, uploads results
3. SYNC: Seamless data flow between server and local machine

Architecture:
- Server runs lightweight predictions with cached models
- Local machine pulls data, trains heavy models (LSTM, Ensemble, etc.)
- Models uploaded back to server for improved predictions
- Continuous improvement cycle without overloading server
"""
import asyncio
import sys
import os
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import pickle
import paramiko
from typing import Dict, List, Optional, Tuple
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
sys.path.append(os.path.dirname(__file__))

# Import our components
from src.ml.advanced_features import AdvancedFeatureEngineer
from src.ml.lstm_model import LSTMTradingModel, LSTMWithAttention
from src.ml.ensemble_stacker import EnsembleStacker
from src.ml.multitask_model import MultiTaskTradingModel

class HybridTrainingSystem:
    """
    Hybrid training system optimized for server-local architecture
    
    Server Responsibilities:
    - Collect market data 24/7
    - Store predictions and outcomes
    - Run lightweight baseline predictions
    - Serve trained model results
    
    Local Machine Responsibilities:
    - Pull accumulated data from server
    - Train heavy ML models (LSTM, Ensemble, Multi-Task)
    - Upload trained models back to server
    - Generate comprehensive reports
    """
    
    def __init__(self, server_config: Dict = None):
        """
        Initialize hybrid training system
        
        Args:
            server_config: SSH configuration for server connection
        """
        self.server_config = server_config or {
            'hostname': '64.226.96.90',  # Your DigitalOcean server
            'username': 'root',
            'key_filename': '~/.ssh/id_rsa'  # SSH key path
        }
        
        # Local paths
        self.local_data_dir = Path('data_sync')
        self.local_models_dir = Path('trained_models')
        self.local_reports_dir = Path('training_reports')
        
        # Server paths
        self.server_data_path = '/opt/rtx-trading/ml_training_data/signal_performance.db'
        self.server_models_path = '/opt/rtx-trading/trained_models/'
        
        # Create local directories
        for dir_path in [self.local_data_dir, self.local_models_dir, self.local_reports_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Training components
        self.feature_engineer = AdvancedFeatureEngineer()
        self.trained_models = {}
        
        logger.info("🔄 Hybrid Training System initialized")
        logger.info(f"🖥️  Server: {self.server_config['hostname']}")
        logger.info(f"💻 Local: {os.getcwd()}")
    
    async def sync_data_from_server(self) -> bool:
        """
        Pull latest data from server for training
        
        Returns:
            bool: Success status
        """
        logger.info("📥 Syncing data from server...")
        
        try:
            # Connect to server via SSH
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            logger.info(f"🔌 Connecting to {self.server_config['hostname']}...")
            ssh.connect(**self.server_config)
            
            # Use SCP to download database
            sftp = ssh.open_sftp()
            
            local_db_path = self.local_data_dir / 'server_data.db'
            
            logger.info("📊 Downloading database...")
            sftp.get(self.server_data_path, str(local_db_path))
            
            # Get file stats
            db_size = local_db_path.stat().st_size / (1024 * 1024)  # MB
            
            # Quick data check
            conn = sqlite3.connect(local_db_path)
            cursor = conn.cursor()
            
            # Count predictions
            cursor.execute("SELECT COUNT(*) FROM predictions")
            prediction_count = cursor.fetchone()[0]
            
            # Count outcomes
            cursor.execute("SELECT COUNT(*) FROM prediction_outcomes WHERE actual_direction IS NOT NULL")
            outcome_count = cursor.fetchone()[0]
            
            # Get date range
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM predictions")
            date_range = cursor.fetchone()
            
            conn.close()
            sftp.close()
            ssh.close()
            
            logger.success(f"✅ Data sync complete!")
            logger.info(f"📊 Database size: {db_size:.1f} MB")
            logger.info(f"🎯 Predictions: {prediction_count:,}")
            logger.info(f"✅ Outcomes: {outcome_count:,}")
            logger.info(f"📅 Date range: {date_range[0]} → {date_range[1]}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Data sync failed: {e}")
            return False
    
    async def train_advanced_models(self) -> Dict:
        """
        Train all advanced models on local machine
        
        Returns:
            Dict: Training results and performance metrics
        """
        logger.info("🧠 Training advanced models locally...")
        
        # Load synced data
        local_db_path = self.local_data_dir / 'server_data.db'
        
        if not local_db_path.exists():
            logger.error("❌ No synced data found. Run sync_data_from_server() first.")
            return {}
        
        # Load and prepare data
        data_info = await self._load_and_prepare_data(local_db_path)
        
        if not data_info:
            logger.error("❌ Data preparation failed")
            return {}
        
        X, y, data_stats = data_info
        
        training_results = {
            'timestamp': datetime.now(),
            'data_stats': data_stats,
            'model_results': {},
            'best_model': None,
            'deployment_ready': False
        }
        
        # Train each model type
        model_configs = [
            {'name': 'ensemble', 'class': EnsembleStacker, 'config': {'use_lstm': False, 'use_attention': False}},
            {'name': 'lstm', 'class': LSTMTradingModel, 'config': {}},
            {'name': 'lstm_attention', 'class': LSTMWithAttention, 'config': {}},
            {'name': 'multitask', 'class': MultiTaskTradingModel, 'config': {}}
        ]
        
        best_score = 0
        best_model_name = None
        
        for model_config in model_configs:
            try:
                logger.info(f"🚀 Training {model_config['name']} model...")
                
                # Train model
                model_result = await self._train_single_model(
                    model_config, X, y
                )
                
                if model_result:
                    training_results['model_results'][model_config['name']] = model_result
                    
                    # Track best model
                    score = model_result.get('accuracy', 0)
                    if score > best_score:
                        best_score = score
                        best_model_name = model_config['name']
                
            except Exception as e:
                logger.error(f"❌ Failed to train {model_config['name']}: {e}")
        
        # Set best model
        if best_model_name:
            training_results['best_model'] = best_model_name
            training_results['deployment_ready'] = best_score > 0.7  # 70% threshold
        
        # Generate comprehensive report
        await self._generate_training_report(training_results)
        
        logger.success(f"✅ Training complete! Best model: {best_model_name} ({best_score:.1%})")
        
        return training_results
    
    async def _load_and_prepare_data(self, db_path: Path) -> Optional[Tuple]:
        """Load and prepare data for training"""
        try:
            conn = sqlite3.connect(db_path)
            
            # Load predictions with outcomes
            query = '''
            SELECT p.*, o.actual_direction, o.actual_move_1h, o.actual_move_4h, 
                   o.actual_move_24h, o.max_move_24h, o.options_profit_potential
            FROM predictions p
            LEFT JOIN prediction_outcomes o ON p.prediction_id = o.prediction_id
            WHERE o.actual_direction IS NOT NULL
            ORDER BY p.timestamp
            '''
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            logger.info(f"📊 Loaded {len(df)} training samples")
            
            # Create target variables
            df['outcome_correct'] = (df['direction'] == df['actual_direction']).astype(int)
            df['profitable_move'] = (abs(df['actual_move_24h'].fillna(0)) > 0.01).astype(int)
            df['high_profit'] = (abs(df['actual_move_24h'].fillna(0)) > 0.02).astype(int)
            
            # Engineer features
            logger.info("🔧 Engineering advanced features...")
            df_enhanced = self.feature_engineer.engineer_features(df)
            
            # Prepare features and targets
            exclude_columns = {
                'prediction_id', 'timestamp', 'symbol', 'direction', 
                'signal_data', 'price_at_prediction', 'reasoning',
                'actual_direction', 'actual_move_1h', 'actual_move_4h', 
                'actual_move_24h', 'max_move_24h', 'options_profit_potential'
            }
            
            feature_columns = [col for col in df_enhanced.columns if col not in exclude_columns]
            X = df_enhanced[feature_columns].fillna(0)
            y = df[['outcome_correct', 'profitable_move', 'high_profit']].fillna(0)
            
            # Data statistics
            data_stats = {
                'total_samples': len(df),
                'feature_count': len(feature_columns),
                'date_range': (df['timestamp'].min(), df['timestamp'].max()),
                'target_distribution': {
                    'outcome_correct': float(y['outcome_correct'].mean()),
                    'profitable_move': float(y['profitable_move'].mean()),
                    'high_profit': float(y['high_profit'].mean())
                }
            }
            
            logger.success(f"✅ Data prepared: {X.shape[1]} features, {len(X)} samples")
            
            return X, y, data_stats
            
        except Exception as e:
            logger.error(f"❌ Data preparation error: {e}")
            return None
    
    async def _train_single_model(self, model_config: Dict, X: pd.DataFrame, y: pd.DataFrame) -> Optional[Dict]:
        """Train a single model and return results"""
        try:
            model_name = model_config['name']
            model_class = model_config['class']
            config = model_config['config']
            
            # Split data
            split_idx = int(0.8 * len(X))
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Create and train model
            if model_name == 'ensemble':
                model = model_class(**config)
                model.train(X_train, y_train.values, cv_folds=3)
                
                # Evaluate
                metrics = model.evaluate(X_test, y_test.values)
                accuracy = metrics['overall']['accuracy']
                
                # Save model
                model_path = self.local_models_dir / f'hybrid_{model_name}_model.pkl'
                model.save_ensemble(str(model_path))
                
            elif model_name in ['lstm', 'lstm_attention']:
                model = model_class(sequence_length=20, feature_dim=X.shape[1])
                
                # Create sequences for LSTM
                X_seq, y_seq = model.create_sequences(X_train, y_train)
                if X_seq is None:
                    logger.warning(f"⚠️ Not enough data for {model_name} sequences")
                    return None
                
                # Build and train
                model.build_model(output_dim=y_train.shape[1])
                model.train(X_seq, y_seq, epochs=20, batch_size=32)
                
                # Evaluate
                X_test_seq, y_test_seq = model.create_sequences(X_test, y_test)
                if X_test_seq is not None:
                    metrics = model.evaluate(X_test_seq, y_test_seq)
                    accuracy = metrics['overall_accuracy']
                else:
                    accuracy = 0.5
                
                # Save model
                model_path = self.local_models_dir / f'hybrid_{model_name}_model.h5'
                model.save_model(str(model_path))
                
            elif model_name == 'multitask':
                model = model_class(feature_dim=X.shape[1])
                
                # Create synthetic targets
                targets = model.create_synthetic_targets(X_train.values, y_train.values)
                
                # Build and train
                model.build_model()
                model.train(X_train.values, targets, epochs=30, batch_size=64)
                
                # Evaluate
                test_targets = model.create_synthetic_targets(X_test.values, y_test.values)
                metrics = model.evaluate(X_test.values, test_targets)
                accuracy = metrics['overall']['classification_accuracy']
                
                # Save model
                model_path = self.local_models_dir / f'hybrid_{model_name}_model.h5'
                model.save_model(str(model_path))
            
            # Store trained model
            self.trained_models[model_name] = model
            
            result = {
                'accuracy': accuracy,
                'model_path': str(model_path),
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'features': X.shape[1]
            }
            
            logger.success(f"✅ {model_name}: {accuracy:.1%} accuracy")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Model training error for {model_name}: {e}")
            return None
    
    async def upload_models_to_server(self) -> bool:
        """
        Upload trained models to server for deployment
        
        Returns:
            bool: Success status
        """
        logger.info("📤 Uploading trained models to server...")
        
        try:
            # Connect to server
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(**self.server_config)
            sftp = ssh.open_sftp()
            
            # Upload all model files
            model_files = list(self.local_models_dir.glob('hybrid_*'))
            uploaded_count = 0
            
            for model_file in model_files:
                try:
                    remote_path = f"{self.server_models_path}{model_file.name}"
                    sftp.put(str(model_file), remote_path)
                    uploaded_count += 1
                    logger.info(f"📤 Uploaded: {model_file.name}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to upload {model_file.name}: {e}")
            
            # Upload training report
            report_files = list(self.local_reports_dir.glob('*.md'))
            for report_file in report_files[-1:]:  # Upload latest report
                try:
                    remote_path = f"{self.server_models_path}{report_file.name}"
                    sftp.put(str(report_file), remote_path)
                    logger.info(f"📄 Uploaded report: {report_file.name}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to upload report: {e}")
            
            sftp.close()
            ssh.close()
            
            logger.success(f"✅ Upload complete! {uploaded_count} models uploaded")
            
            return uploaded_count > 0
            
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            return False
    
    async def _generate_training_report(self, results: Dict):
        """Generate comprehensive training report"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            report_path = self.local_reports_dir / f'hybrid_training_report_{timestamp}.md'
            
            report_lines = [
                "# Hybrid Training Report - Server-Local Architecture",
                f"Generated: {results['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "## 🏗️ Hybrid Architecture Summary",
                "- **Server**: Collects data 24/7, lightweight predictions",
                "- **Local**: Heavy ML training, model optimization",
                "- **Sync**: Seamless data flow and model deployment",
                "",
                "## 📊 Training Data Statistics",
                f"- **Total Samples**: {results['data_stats']['total_samples']:,}",
                f"- **Feature Count**: {results['data_stats']['feature_count']}",
                f"- **Date Range**: {results['data_stats']['date_range'][0]} → {results['data_stats']['date_range'][1]}",
                "",
                "## 🎯 Target Distribution",
            ]
            
            for target, rate in results['data_stats']['target_distribution'].items():
                report_lines.append(f"- **{target}**: {rate:.1%}")
            
            report_lines.extend([
                "",
                "## 🧠 Model Performance Results",
            ])
            
            for model_name, model_result in results['model_results'].items():
                accuracy = model_result['accuracy']
                report_lines.extend([
                    f"### {model_name.title()} Model",
                    f"- **Accuracy**: {accuracy:.1%}",
                    f"- **Training Samples**: {model_result['training_samples']:,}",
                    f"- **Test Samples**: {model_result['test_samples']:,}",
                    f"- **Features**: {model_result['features']}",
                    f"- **Model Path**: `{model_result['model_path']}`",
                    ""
                ])
            
            report_lines.extend([
                "## 🏆 Best Model",
                f"- **Winner**: {results['best_model'] or 'None'}",
                f"- **Deployment Ready**: {'✅ Yes' if results['deployment_ready'] else '❌ No (accuracy < 70%)'}",
                "",
                "## 🚀 Next Steps",
                "1. Upload models to server with `upload_models_to_server()`",
                "2. Update server to use new models",
                "3. Monitor performance in production",
                "4. Schedule next training cycle",
                "",
                "## 🔄 Hybrid Workflow",
                "```",
                "Server (24/7) → Collect Data → Store in DB",
                "Local (Weekly) → Sync Data → Train Models → Upload Results",
                "Server → Load New Models → Improved Predictions",
                "```",
                "",
                f"*Generated by Hybrid Training System - {timestamp}*"
            ])
            
            # Write report
            with open(report_path, 'w') as f:
                f.write('\n'.join(report_lines))
            
            logger.success(f"📄 Training report saved: {report_path}")
            
        except Exception as e:
            logger.error(f"❌ Report generation failed: {e}")
    
    async def run_complete_training_cycle(self) -> bool:
        """
        Run complete training cycle: sync → train → upload
        
        Returns:
            bool: Success status
        """
        logger.info("🔄 Starting complete hybrid training cycle...")
        
        try:
            # Step 1: Sync data from server
            if not await self.sync_data_from_server():
                return False
            
            # Step 2: Train models locally
            results = await self.train_advanced_models()
            if not results or not results['deployment_ready']:
                logger.warning("⚠️ No deployment-ready models produced")
                return False
            
            # Step 3: Upload to server
            if not await self.upload_models_to_server():
                return False
            
            logger.success("🎉 Complete training cycle successful!")
            logger.info(f"🏆 Best model: {results['best_model']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Training cycle failed: {e}")
            return False

# Convenience functions for easy usage
async def quick_sync_and_train():
    """Quick sync and train cycle"""
    system = HybridTrainingSystem()
    return await system.run_complete_training_cycle()

async def sync_data_only():
    """Just sync data from server"""
    system = HybridTrainingSystem()
    return await system.sync_data_from_server()

async def train_models_only():
    """Just train models (assumes data already synced)"""
    system = HybridTrainingSystem()
    return await system.train_advanced_models()

async def upload_models_only():
    """Just upload models to server"""
    system = HybridTrainingSystem()
    return await system.upload_models_to_server()

# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Hybrid Training System')
    parser.add_argument('--sync', action='store_true', help='Sync data from server')
    parser.add_argument('--train', action='store_true', help='Train models locally')
    parser.add_argument('--upload', action='store_true', help='Upload models to server')
    parser.add_argument('--full', action='store_true', help='Run complete cycle')
    
    args = parser.parse_args()
    
    if args.sync:
        asyncio.run(sync_data_only())
    elif args.train:
        asyncio.run(train_models_only())
    elif args.upload:
        asyncio.run(upload_models_only())
    elif args.full:
        asyncio.run(quick_sync_and_train())
    else:
        logger.info("🔄 Running complete hybrid training cycle...")
        asyncio.run(quick_sync_and_train())
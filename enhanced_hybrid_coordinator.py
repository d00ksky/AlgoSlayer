#!/usr/bin/env python3
"""
Enhanced Hybrid Coordinator - Works with Claude Code's Server Learning
Coordinates between server-side continuous learning and local heavy training

This system is designed to work WITH Claude Code's continuous learning system:
- Server: 4-hour lightweight learning (signal weights, linear models)
- Local: Weekly heavy training (LSTM, Ensemble, Multi-Task)
- Coordination: Seamless integration between both approaches

Architecture:
Server (Claude Code) → Continuous learning every 4 hours
Local (This system) → Heavy training weekly + model deployment
Result → Best of both: Immediate improvements + Advanced models
"""
import asyncio
import sys
import os
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from importlib import import_module
from pathlib import Path
import pickle
import paramiko
from typing import Dict, List, Optional, Tuple
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
sys.path.append(os.path.dirname(__file__))

# Import our Phase 2 feature engineering (lightweight dependency)
from src.ml.advanced_features import AdvancedFeatureEngineer

class HybridCoordinator:
    """
    Enhanced coordinator that works with Claude Code's server-side learning
    
    Responsibilities:
    1. Monitor server's continuous learning performance
    2. Determine when heavy training is needed
    3. Execute local heavy training with latest data
    4. Deploy advanced models back to server
    5. Coordinate between lightweight and heavy learning systems
    """
    
    def __init__(self, server_config: Dict = None):
        """Initialize hybrid coordinator"""
        self.server_config = server_config or {
            'hostname': '64.226.96.90',
            'username': 'root',
            'key_filename': os.path.expanduser('~/.ssh/id_ed25519')
        }
        
        # Paths
        self.local_work_dir = Path('hybrid_work')
        self.local_models_dir = Path('trained_models')
        self.server_learning_path = '/opt/rtx-trading/continuous_learning.py'
        self.server_models_path = '/opt/rtx-trading/trained_models/'
        self.server_data_path = '/opt/rtx-trading/ml_training_data/signal_performance.db'
        self.server_export_path = '/opt/rtx-trading/data_export/'
        
        # Create local directories
        self.local_work_dir.mkdir(exist_ok=True)
        self.local_models_dir.mkdir(exist_ok=True)
        
        # Training components
        self.feature_engineer = AdvancedFeatureEngineer()
        self.last_training_time = None
        self.training_threshold_days = 7  # Train weekly
        
        logger.info("🤝 Enhanced Hybrid Coordinator initialized")
        logger.info(f"🖥️  Server: {self.server_config['hostname']}")
        logger.info(f"⚡ Will coordinate with Claude Code's continuous learning")

    def _resolve_model_class(self, dotted_path: str):
        """Return class object for optional advanced models or None if unavailable."""
        module_path, _, class_name = dotted_path.partition(":")
        if not module_path or not class_name:
            logger.error(f"❌ Invalid class path: {dotted_path}")
            return None

        try:
            module = import_module(module_path)
            return getattr(module, class_name)
        except ImportError as exc:
            logger.warning(f"⚠️ Skipping {class_name}: missing dependency ({exc})")
        except AttributeError as exc:
            logger.warning(f"⚠️ Skipping {class_name}: attribute not found ({exc})")

        return None

    async def check_server_learning_status(self) -> Dict:
        """
        Check status of Claude Code's continuous learning system
        
        Returns:
            Dict: Server learning status and performance
        """
        logger.info("📊 Checking server continuous learning status...")
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(**self.server_config)
            
            # Check if continuous learning is running
            stdin, stdout, stderr = ssh.exec_command(
                "ps aux | grep continuous_learning | grep -v grep"
            )
            processes = stdout.read().decode().strip()
            
            # Get recent performance data
            stdin, stdout, stderr = ssh.exec_command(
                f"tail -n 100 /opt/rtx-trading/logs/continuous_learning.log 2>/dev/null || echo 'No log file'"
            )
            recent_logs = stdout.read().decode().strip()
            
            # Check database for recent updates
            sftp = ssh.open_sftp()
            try:
                # Download small sample to check update frequency
                temp_db = self.local_work_dir / 'status_check.db'
                sftp.get(self.server_data_path, str(temp_db))
                
                # Quick analysis
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                
                # Get recent prediction count
                cursor.execute("""
                    SELECT COUNT(*) FROM predictions 
                    WHERE timestamp > datetime('now', '-24 hours')
                """)
                recent_predictions = cursor.fetchone()[0]
                
                # Get recent training updates (if Claude Code adds a training log table)
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name LIKE '%training%'
                """)
                training_tables = cursor.fetchall()
                
                conn.close()
                temp_db.unlink()  # Clean up
                
            except Exception as e:
                logger.warning(f"⚠️ Database check failed: {e}")
                recent_predictions = 0
                training_tables = []
            
            sftp.close()
            ssh.close()
            
            status = {
                'continuous_learning_running': bool(processes),
                'recent_predictions': recent_predictions,
                'has_training_logs': bool(training_tables),
                'log_sample': recent_logs[-500:] if recent_logs else "No logs",
                'needs_local_training': self._should_run_heavy_training(recent_predictions)
            }
            
            logger.info(f"📊 Server status: {recent_predictions} recent predictions")
            if status['continuous_learning_running']:
                logger.success("✅ Continuous learning is running")
            else:
                logger.warning("⚠️ Continuous learning not detected")
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Server status check failed: {e}")
            return {'error': str(e), 'needs_local_training': True}
    
    def _should_run_heavy_training(self, recent_predictions: int) -> bool:
        """Determine if we should run heavy training"""
        # Run if:
        # 1. Haven't trained in the last week
        # 2. Server has accumulated significant new data
        # 3. It's been requested manually
        
        if self.last_training_time is None:
            return True
        
        days_since_training = (datetime.now() - self.last_training_time).days
        if days_since_training >= self.training_threshold_days:
            return True
        
        # If server has lots of new predictions, consider training
        if recent_predictions > 500:  # Threshold for heavy training
            return True
        
        return False
    
    async def download_claude_code_export(self) -> bool:
        """
        Download Claude Code's exported training data
        
        Returns:
            bool: Success status
        """
        logger.info("📥 Downloading Claude Code's exported data...")
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(**self.server_config)
            sftp = ssh.open_sftp()
            
            # Create local export directory
            export_dir = self.local_work_dir / 'data_export'
            export_dir.mkdir(exist_ok=True)
            
            # List files in export directory
            try:
                export_files = sftp.listdir(self.server_export_path)
                logger.info(f"📊 Found {len(export_files)} export files")
                
                downloaded_count = 0
                for filename in export_files:
                    try:
                        remote_path = f"{self.server_export_path}{filename}"
                        local_path = export_dir / filename
                        
                        sftp.get(remote_path, str(local_path))
                        downloaded_count += 1
                        logger.info(f"📥 Downloaded: {filename}")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to download {filename}: {e}")
                
                sftp.close()
                ssh.close()
                
                if downloaded_count > 0:
                    logger.success(f"✅ Downloaded {downloaded_count} export files")
                    return True
                else:
                    logger.warning("⚠️ No files downloaded")
                    return False
                
            except Exception as e:
                logger.warning(f"⚠️ Export directory access failed: {e}")
                # Fallback to database download
                sftp.close()
                ssh.close()
                return await self.sync_and_analyze_server_data() is not None
                
        except Exception as e:
            logger.error(f"❌ Export download failed: {e}")
            return False

    async def sync_and_analyze_server_data(self) -> Optional[Dict]:
        """
        Sync data from server and analyze training needs
        
        Returns:
            Dict: Data analysis and training recommendations
        """
        logger.info("🔄 Syncing and analyzing server data...")
        
        try:
            # Download database
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(**self.server_config)
            sftp = ssh.open_sftp()
            
            local_db = self.local_work_dir / 'server_data_latest.db'
            sftp.get(self.server_data_path, str(local_db))
            
            sftp.close()
            ssh.close()
            
            # Analyze data
            conn = sqlite3.connect(local_db)
            
            # Data statistics
            cursor = conn.cursor()
            
            # Total predictions
            cursor.execute("SELECT COUNT(*) FROM predictions")
            total_predictions = cursor.fetchone()[0]
            
            # Recent predictions (last 7 days)
            cursor.execute("""
                SELECT COUNT(*) FROM predictions 
                WHERE timestamp > datetime('now', '-7 days')
            """)
            recent_predictions = cursor.fetchone()[0]
            
            # Predictions with outcomes
            cursor.execute("""
                SELECT COUNT(*) FROM predictions p
                JOIN prediction_outcomes o ON p.prediction_id = o.prediction_id
                WHERE o.actual_direction IS NOT NULL
            """)
            training_samples = cursor.fetchone()[0]
            
            # Recent accuracy (if we can calculate it)
            cursor.execute("""
                SELECT 
                    AVG(CASE WHEN p.direction = o.actual_direction THEN 1.0 ELSE 0.0 END) as accuracy
                FROM predictions p
                JOIN prediction_outcomes o ON p.prediction_id = o.prediction_id
                WHERE o.actual_direction IS NOT NULL 
                AND p.timestamp > datetime('now', '-7 days')
            """)
            recent_accuracy_result = cursor.fetchone()
            recent_accuracy = recent_accuracy_result[0] if recent_accuracy_result[0] else 0.5
            
            # Date range
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM predictions")
            date_range = cursor.fetchone()
            
            conn.close()
            
            analysis = {
                'total_predictions': total_predictions,
                'recent_predictions': recent_predictions,
                'training_samples': training_samples,
                'recent_accuracy': float(recent_accuracy),
                'date_range': date_range,
                'data_quality': training_samples / max(1, total_predictions),
                'training_recommended': training_samples > 1000 and recent_predictions > 100
            }
            
            logger.success("✅ Data analysis complete")
            logger.info(f"📊 Total predictions: {total_predictions:,}")
            logger.info(f"📊 Training samples: {training_samples:,}")
            logger.info(f"📊 Recent accuracy: {recent_accuracy:.1%}")
            logger.info(f"🎯 Training recommended: {analysis['training_recommended']}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Data sync/analysis failed: {e}")
            return None
    
    async def run_heavy_training_cycle(self) -> bool:
        """
        Run heavy training cycle with advanced models
        
        Returns:
            bool: Success status
        """
        logger.info("🧠 Starting heavy training cycle...")
        
        try:
            # Load and prepare data
            local_db = self.local_work_dir / 'server_data_latest.db'
            if not local_db.exists():
                logger.error("❌ No synced data found")
                return False
            
            # Load training data
            training_data = await self._prepare_training_data(local_db)
            if not training_data:
                return False
            
            X, y, data_stats = training_data
            
            # Train advanced models
            training_results = await self._train_advanced_models(X, y, data_stats)
            
            if not training_results or not training_results.get('models_trained'):
                logger.error("❌ No models successfully trained")
                return False
            
            # Generate comprehensive report
            await self._generate_coordination_report(training_results, data_stats)
            
            # Mark training time
            self.last_training_time = datetime.now()
            
            logger.success("✅ Heavy training cycle completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Heavy training cycle failed: {e}")
            return False
    
    async def _prepare_training_data(self, db_path: Path) -> Optional[Tuple]:
        """Prepare training data with advanced features"""
        try:
            conn = sqlite3.connect(db_path)
            
            # Load all available data
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
            
            if len(df) < 500:
                logger.warning("⚠️ Insufficient training data")
                return None
            
            logger.info(f"📊 Loaded {len(df)} training samples")
            
            # Create targets
            df['outcome_correct'] = (df['direction'] == df['actual_direction']).astype(int)
            df['profitable_move'] = (abs(df['actual_move_24h'].fillna(0)) > 0.01).astype(int)
            df['high_profit'] = (abs(df['actual_move_24h'].fillna(0)) > 0.02).astype(int)
            
            # Engineer advanced features
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
            logger.error(f"❌ Data preparation failed: {e}")
            return None
    
    async def _train_advanced_models(self, X: pd.DataFrame, y: pd.DataFrame, data_stats: Dict) -> Dict:
        """Train advanced models"""
        logger.info("🚀 Training advanced models...")
        
        results = {
            'timestamp': datetime.now(),
            'data_stats': data_stats,
            'models': {},
            'models_trained': 0,
            'best_model': None,
            'best_accuracy': 0
        }
        
        # Model configurations
        model_configs = [
            {
                'name': 'ensemble_advanced',
                'class_path': 'src.ml.ensemble_stacker:EnsembleStacker',
                'config': {'use_lstm': False, 'use_attention': False},
                'priority': 'high'
            },
            {
                'name': 'lstm_standard',
                'class_path': 'src.ml.lstm_model:LSTMTradingModel',
                'config': {'sequence_length': 20, 'feature_dim': X.shape[1]},
                'priority': 'medium'
            },
            {
                'name': 'multitask_neural',
                'class_path': 'src.ml.multitask_model:MultiTaskTradingModel',
                'config': {'feature_dim': X.shape[1]},
                'priority': 'medium'
            }
        ]
        
        # Train each model
        for config in model_configs:
            try:
                model_class = self._resolve_model_class(config['class_path'])
                if model_class is None:
                    logger.info(f"⏭️  Skipping {config['name']} due to unavailable dependencies")
                    continue

                logger.info(f"🧠 Training {config['name']}...")

                model_result = await self._train_single_advanced_model(
                    config['name'],
                    model_class,
                    config['config'],
                    X,
                    y
                )

                if model_result:
                    results['models'][config['name']] = model_result
                    results['models_trained'] += 1
                    
                    # Track best model
                    accuracy = model_result.get('accuracy', 0)
                    if accuracy > results['best_accuracy']:
                        results['best_accuracy'] = accuracy
                        results['best_model'] = config['name']
                        
                    logger.success(f"✅ {config['name']}: {accuracy:.1%} accuracy")
                
            except Exception as e:
                logger.error(f"❌ Failed to train {config['name']}: {e}")
        
        return results
    
    async def _train_single_advanced_model(
        self,
        model_name: str,
        model_class,
        model_config: Dict,
        X: pd.DataFrame,
        y: pd.DataFrame,
    ) -> Optional[Dict]:
        """Train a single advanced model"""
        try:
            # Split data
            split_idx = int(0.8 * len(X))
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Create and train model
            if 'ensemble' in model_name:
                model = model_class(**model_config)
                model.train(X_train, y_train.values, cv_folds=3)
                
                # Evaluate
                metrics = model.evaluate(X_test, y_test.values)
                accuracy = metrics['overall']['accuracy']
                
                # Save model
                model_path = self.local_models_dir / f'coord_{model_name}.pkl'
                model.save_ensemble(str(model_path))
                
            elif 'lstm' in model_name:
                model = model_class(**model_config)
                
                # Create sequences
                X_seq, y_seq = model.create_sequences(X_train, y_train)
                if X_seq is None:
                    return None
                
                # Build and train
                model.build_model(output_dim=y_train.shape[1])
                model.train(X_seq, y_seq, epochs=25, batch_size=32)
                
                # Evaluate
                X_test_seq, y_test_seq = model.create_sequences(X_test, y_test)
                if X_test_seq is not None:
                    metrics = model.evaluate(X_test_seq, y_test_seq)
                    accuracy = metrics['overall_accuracy']
                else:
                    accuracy = 0.5
                
                # Save model
                model_path = self.local_models_dir / f'coord_{model_name}.h5'
                model.save_model(str(model_path))
                
            elif 'multitask' in model_name:
                model = model_class(**model_config)
                
                # Create targets
                targets = model.create_synthetic_targets(X_train.values, y_train.values)
                
                # Build and train
                model.build_model()
                model.train(X_train.values, targets, epochs=35, batch_size=64)
                
                # Evaluate
                test_targets = model.create_synthetic_targets(X_test.values, y_test.values)
                metrics = model.evaluate(X_test.values, test_targets)
                accuracy = metrics['overall']['classification_accuracy']
                
                # Save model
                model_path = self.local_models_dir / f'coord_{model_name}.h5'
                model.save_model(str(model_path))
            
            return {
                'accuracy': accuracy,
                'model_path': str(model_path),
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'features': X.shape[1],
                'model_type': model_name
            }
            
        except Exception as e:
            logger.error(f"❌ Advanced model training error: {e}")
            return None
    
    async def deploy_models_to_server(self) -> bool:
        """Deploy trained models to server"""
        logger.info("📤 Deploying advanced models to server...")
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(**self.server_config)
            sftp = ssh.open_sftp()
            
            # Upload model files
            model_files = list(self.local_models_dir.glob('coord_*'))
            deployed_count = 0
            
            for model_file in model_files:
                try:
                    remote_path = f"{self.server_models_path}{model_file.name}"
                    sftp.put(str(model_file), remote_path)
                    deployed_count += 1
                    logger.info(f"📤 Deployed: {model_file.name}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to deploy {model_file.name}: {e}")
            
            # Upload training report
            report_files = list(self.local_work_dir.glob('*coordination_report*'))
            for report_file in report_files[-1:]:
                try:
                    remote_path = f"{self.server_models_path}{report_file.name}"
                    sftp.put(str(report_file), remote_path)
                    logger.info(f"📄 Deployed report: {report_file.name}")
                except:
                    pass
            
            sftp.close()
            ssh.close()
            
            logger.success(f"✅ Deployment complete: {deployed_count} models deployed")
            return deployed_count > 0
            
        except Exception as e:
            logger.error(f"❌ Model deployment failed: {e}")
            return False
    
    async def _generate_coordination_report(self, training_results: Dict, data_stats: Dict):
        """Generate coordination report"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            report_path = self.local_work_dir / f'coordination_report_{timestamp}.md'
            
            report_lines = [
                "# Hybrid Coordination Report - Local Heavy Training",
                f"Generated: {training_results['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "## 🤝 Coordination with Server Continuous Learning",
                "This report covers heavy training that complements Claude Code's server-side continuous learning.",
                "",
                "### 🖥️ Server Responsibilities (Claude Code)",
                "- ⚡ 4-hour signal weight updates",
                "- 📊 Linear model retraining",
                "- 🎯 Real-time performance monitoring",
                "- 📈 Feature importance tracking",
                "",
                "### 💻 Local Responsibilities (This System)",
                "- 🧠 Weekly advanced model training",
                "- 🔬 Deep learning (LSTM, Ensemble, Multi-Task)",
                "- 📊 Comprehensive model evaluation",
                "- 🚀 Model deployment back to server",
                "",
                "## 📊 Training Data Analysis",
                f"- **Total Samples**: {data_stats['total_samples']:,}",
                f"- **Feature Count**: {data_stats['feature_count']}",
                f"- **Date Range**: {data_stats['date_range'][0]} → {data_stats['date_range'][1]}",
                "",
                "### 🎯 Target Distribution",
            ]
            
            for target, rate in data_stats['target_distribution'].items():
                report_lines.append(f"- **{target}**: {rate:.1%}")
            
            report_lines.extend([
                "",
                "## 🧠 Advanced Model Results",
                f"- **Models Trained**: {training_results['models_trained']}",
                f"- **Best Model**: {training_results['best_model']}",
                f"- **Best Accuracy**: {training_results['best_accuracy']:.1%}",
                ""
            ])
            
            for model_name, result in training_results['models'].items():
                report_lines.extend([
                    f"### {model_name}",
                    f"- Accuracy: {result['accuracy']:.1%}",
                    f"- Training Samples: {result['training_samples']:,}",
                    f"- Features: {result['features']}",
                    f"- Model Path: {result['model_path']}",
                    ""
                ])
            
            report_lines.extend([
                "## 🚀 Next Steps",
                "1. ✅ Deploy models to server",
                "2. 🤝 Coordinate with Claude Code's continuous learning",
                "3. 📊 Monitor combined performance (continuous + heavy)",
                "4. 🔄 Schedule next heavy training cycle",
                "",
                "## 🎯 Expected Benefits",
                "- **Immediate**: Server continuous learning provides 4-hour improvements",
                "- **Deep**: Local heavy training provides weekly advanced model updates",
                "- **Combined**: Best of both worlds for optimal performance",
                "",
                f"*Generated by Hybrid Coordinator - {timestamp}*"
            ])
            
            with open(report_path, 'w') as f:
                f.write('\n'.join(report_lines))
            
            logger.success(f"📄 Coordination report saved: {report_path}")
            
        except Exception as e:
            logger.error(f"❌ Report generation failed: {e}")
    
    async def run_full_coordination_cycle(self) -> bool:
        """Run complete coordination cycle"""
        logger.info("🤝 Starting full coordination cycle...")
        
        try:
            # Step 1: Check server continuous learning status
            server_status = await self.check_server_learning_status()
            if server_status.get('error'):
                logger.warning("⚠️ Server status check failed, proceeding anyway")
            
            # Step 2: Sync and analyze data
            analysis = await self.sync_and_analyze_server_data()
            if not analysis:
                return False
            
            # Step 3: Decide if heavy training is needed
            if not analysis['training_recommended']:
                logger.info("ℹ️ Heavy training not needed at this time")
                return True
            
            # Step 4: Run heavy training
            if not await self.run_heavy_training_cycle():
                return False
            
            # Step 5: Deploy models to server
            if not await self.deploy_models_to_server():
                return False
            
            logger.success("🎉 Full coordination cycle completed successfully!")
            logger.info("🤝 Server continuous learning + Local heavy training active")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Coordination cycle failed: {e}")
            return False

# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Hybrid Coordinator')
    parser.add_argument('--status', action='store_true', help='Check server status')
    parser.add_argument('--analyze', action='store_true', help='Analyze server data')
    parser.add_argument('--train', action='store_true', help='Run heavy training')
    parser.add_argument('--deploy', action='store_true', help='Deploy models')
    parser.add_argument('--full', action='store_true', help='Run full cycle')
    
    args = parser.parse_args()
    
    coordinator = HybridCoordinator()
    
    if args.status:
        result = asyncio.run(coordinator.check_server_learning_status())
        print(json.dumps(result, indent=2, default=str))
    elif args.analyze:
        result = asyncio.run(coordinator.sync_and_analyze_server_data())
        print(json.dumps(result, indent=2, default=str))
    elif args.train:
        success = asyncio.run(coordinator.run_heavy_training_cycle())
        print(f"Training successful: {success}")
    elif args.deploy:
        success = asyncio.run(coordinator.deploy_models_to_server())
        print(f"Deployment successful: {success}")
    elif args.full:
        success = asyncio.run(coordinator.run_full_coordination_cycle())
        print(f"Full cycle successful: {success}")
    else:
        logger.info("🤝 Running full coordination cycle...")
        success = asyncio.run(coordinator.run_full_coordination_cycle())
        print(f"Coordination successful: {success}")

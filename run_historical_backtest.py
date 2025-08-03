#!/usr/bin/env python3
"""
Run Historical Backtest for AlgoSlayer
Generates massive training data from historical market data
"""
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger
import json
import sqlite3
from src.core.historical_backtester import (
    HistoricalDataFetcher, 
    HistoricalSignalSimulator, 
    HistoricalBacktestEngine
)

# Configure logging
logger.remove()
logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
logger.add("logs/historical_backtest_{time:YYYY-MM-DD}.log", rotation="1 day")

class BacktestMLIntegrator:
    """Integrates backtest results with ML training pipeline"""
    
    def __init__(self):
        self.feature_columns = [
            'confidence', 'rsi', 'sma_ratio', 'volume_ratio', 
            'atr_ratio', 'momentum_5d', 'days_to_expiry',
            'moneyness', 'iv_estimate', 'signal_agreement'
        ]
        
    def prepare_ml_features(self, trades_df: pd.DataFrame) -> pd.DataFrame:
        """Convert backtest trades to ML training features"""
        logger.info(f"Preparing ML features from {len(trades_df)} historical trades")
        
        features_list = []
        
        for idx, trade in trades_df.iterrows():
            # Parse signals JSON
            signals = json.loads(trade['signals'])
            
            # Calculate features
            features = {
                'timestamp': trade['timestamp'],
                'strategy': trade['strategy'],
                'confidence': trade['confidence'],
                'moneyness': trade['entry_stock_price'] / trade['strike'],
                'days_to_expiry': (trade['expiry'] - trade['timestamp']).days,
                'option_type': 1 if trade['option_type'] == 'CALL' else 0,
                
                # Extract signal features
                'technical_confidence': signals.get('technical_analysis', {}).get('confidence', 0),
                'momentum_confidence': signals.get('momentum', {}).get('confidence', 0),
                'volatility_confidence': signals.get('volatility', {}).get('confidence', 0),
                'mean_reversion_confidence': signals.get('mean_reversion', {}).get('confidence', 0),
                
                # Count agreeing signals
                'signal_agreement': sum(1 for s in signals.values() 
                                      if s.get('direction') in ['bullish', 'trending']),
                
                # Target variables
                'profitable': 1 if trade['pnl'] > 0 else 0,
                'pnl_percentage': trade['pnl_percentage'],
                'exit_reason': trade['exit_reason']
            }
            
            features_list.append(features)
        
        features_df = pd.DataFrame(features_list)
        logger.info(f"Created {len(features_df)} ML training examples")
        
        return features_df
    
    def save_training_data(self, features_df: pd.DataFrame, output_file: str):
        """Save prepared training data for ML pipeline"""
        features_df.to_csv(output_file, index=False)
        logger.info(f"Saved ML training data to {output_file}")
        
        # Also save to SQLite for compatibility
        conn = sqlite3.connect('data/historical_backtest.db')
        features_df.to_sql('backtest_features', conn, if_exists='replace', index=False)
        
        # Save summary statistics
        summary = {
            'total_examples': len(features_df),
            'profitable_rate': features_df['profitable'].mean(),
            'strategies': features_df['strategy'].value_counts().to_dict(),
            'avg_pnl': features_df['pnl_percentage'].mean(),
            'feature_stats': features_df.describe().to_dict()
        }
        
        with open('data/backtest_summary.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
            
        conn.close()
        logger.info("Saved backtest summary and database")

def run_multi_period_backtest():
    """Run backtests across multiple time periods for robust training data"""
    
    # Initialize components
    data_fetcher = HistoricalDataFetcher()
    signal_simulator = HistoricalSignalSimulator()
    backtest_engine = HistoricalBacktestEngine(data_fetcher, signal_simulator)
    ml_integrator = BacktestMLIntegrator()
    
    # Define test periods (different market conditions)
    test_periods = [
        {
            'name': 'COVID_Crash_Recovery',
            'start': '2020-01-01',
            'end': '2020-12-31',
            'description': 'Extreme volatility, crash and recovery'
        },
        {
            'name': 'Bull_Market_2021',
            'start': '2021-01-01',
            'end': '2021-12-31',
            'description': 'Strong bull market conditions'
        },
        {
            'name': 'Bear_Market_2022',
            'start': '2022-01-01',
            'end': '2022-12-31',
            'description': 'Rising rates, bear market'
        },
        {
            'name': 'Recovery_2023',
            'start': '2023-01-01',
            'end': '2023-12-31',
            'description': 'Market recovery and AI boom'
        },
        {
            'name': 'Recent_2024',
            'start': '2024-01-01',
            'end': '2024-07-31',
            'description': 'Most recent market conditions'
        }
    ]
    
    all_trades = []
    period_results = {}
    
    logger.info("Starting multi-period historical backtest for RTX")
    
    for period in test_periods:
        logger.info(f"\n{'='*60}")
        logger.info(f"Backtesting period: {period['name']}")
        logger.info(f"Description: {period['description']}")
        logger.info(f"Date range: {period['start']} to {period['end']}")
        logger.info(f"{'='*60}")
        
        try:
            # Run backtest for this period
            trades_df = backtest_engine.backtest_period(
                symbol='RTX',
                start_date=period['start'],
                end_date=period['end']
            )
            
            if not trades_df.empty:
                # Analyze results
                analysis = backtest_engine.analyze_results(trades_df)
                period_results[period['name']] = analysis
                
                # Add period identifier
                trades_df['period'] = period['name']
                all_trades.append(trades_df)
                
                # Print summary
                logger.info(f"\nPeriod Summary for {period['name']}:")
                logger.info(f"Total trades: {analysis['total_trades']}")
                logger.info(f"Overall win rate: {analysis['overall_metrics']['win_rate']:.1f}%")
                logger.info(f"Total P&L: ${analysis['overall_metrics']['total_pnl']:.2f}")
                logger.info(f"Sharpe ratio: {analysis['overall_metrics']['sharpe_ratio']:.2f}")
                
                # Best performing strategy
                best_strategy = max(analysis['by_strategy'].items(), 
                                  key=lambda x: x[1]['total_pnl'])
                logger.info(f"Best strategy: {best_strategy[0]} "
                          f"(${best_strategy[1]['total_pnl']:.2f} P&L)")
                
        except Exception as e:
            logger.error(f"Error backtesting {period['name']}: {str(e)}")
            continue
    
    # Combine all trades
    if all_trades:
        combined_trades = pd.concat(all_trades, ignore_index=True)
        logger.info(f"\n{'='*60}")
        logger.info(f"COMBINED RESULTS")
        logger.info(f"{'='*60}")
        logger.info(f"Total historical trades generated: {len(combined_trades)}")
        
        # Overall analysis
        combined_analysis = backtest_engine.analyze_results(combined_trades)
        
        logger.info(f"\nCombined Performance Metrics:")
        logger.info(f"Overall win rate: {combined_analysis['overall_metrics']['win_rate']:.1f}%")
        logger.info(f"Average win: {combined_analysis['overall_metrics']['average_win']:.1f}%")
        logger.info(f"Average loss: {combined_analysis['overall_metrics']['average_loss']:.1f}%")
        logger.info(f"Total P&L: ${combined_analysis['overall_metrics']['total_pnl']:.2f}")
        logger.info(f"Sharpe ratio: {combined_analysis['overall_metrics']['sharpe_ratio']:.2f}")
        logger.info(f"Max drawdown: {combined_analysis['overall_metrics']['max_drawdown']:.1f}%")
        
        # Strategy ranking
        logger.info(f"\nStrategy Performance Ranking:")
        strategy_ranking = sorted(
            combined_analysis['by_strategy'].items(),
            key=lambda x: x[1]['total_pnl'],
            reverse=True
        )
        
        for rank, (strategy, metrics) in enumerate(strategy_ranking, 1):
            logger.info(f"{rank}. {strategy:15} - "
                      f"Trades: {metrics['total_trades']:4d}, "
                      f"Win Rate: {metrics['win_rate']:5.1f}%, "
                      f"Total P&L: ${metrics['total_pnl']:8.2f}")
        
        # Prepare ML training data
        logger.info(f"\n{'='*60}")
        logger.info("Preparing ML training data...")
        ml_features = ml_integrator.prepare_ml_features(combined_trades)
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save raw trades
        combined_trades.to_csv(f'data/historical_trades_{timestamp}.csv', index=False)
        
        # Save ML features
        ml_integrator.save_training_data(
            ml_features, 
            f'data/ml_training_features_{timestamp}.csv'
        )
        
        # Save detailed analysis
        with open(f'data/backtest_analysis_{timestamp}.json', 'w') as f:
            json.dump({
                'period_results': period_results,
                'combined_analysis': combined_analysis,
                'configuration': {
                    'symbol': 'RTX',
                    'periods_tested': len(test_periods),
                    'total_years': 4.5,
                    'strategies': list(backtest_engine.strategy_configs.keys())
                }
            }, f, indent=2, default=str)
        
        logger.info(f"\n✅ Backtest complete! Generated {len(combined_trades)} historical trades")
        logger.info(f"📊 ML training data saved with {len(ml_features)} examples")
        logger.info(f"📁 Results saved to data/ directory with timestamp {timestamp}")
        
        # Print actionable insights
        logger.info(f"\n{'='*60}")
        logger.info("📌 KEY INSIGHTS FOR ML TRAINING:")
        logger.info(f"{'='*60}")
        
        # Find most predictive features
        profitable_trades = ml_features[ml_features['profitable'] == 1]
        unprofitable_trades = ml_features[ml_features['profitable'] == 0]
        
        logger.info("\n🎯 Most predictive signals (correlation with profitability):")
        for signal in ['technical_confidence', 'momentum_confidence', 'volatility_confidence']:
            if signal in ml_features.columns:
                profitable_avg = profitable_trades[signal].mean()
                unprofitable_avg = unprofitable_trades[signal].mean()
                diff = profitable_avg - unprofitable_avg
                logger.info(f"  {signal}: {diff:+.3f} difference "
                          f"(Prof: {profitable_avg:.3f}, Unprof: {unprofitable_avg:.3f})")
        
        # Optimal confidence thresholds
        logger.info("\n📊 Optimal confidence thresholds by strategy:")
        for strategy in combined_trades['strategy'].unique():
            strategy_trades = combined_trades[combined_trades['strategy'] == strategy]
            profitable_threshold = strategy_trades[strategy_trades['pnl'] > 0]['confidence'].quantile(0.25)
            logger.info(f"  {strategy}: {profitable_threshold:.3f} "
                      f"(25th percentile of profitable trades)")
        
        # Market condition insights
        logger.info("\n🌍 Performance by market condition:")
        for period_name, results in period_results.items():
            win_rate = results['overall_metrics']['win_rate']
            total_pnl = results['overall_metrics']['total_pnl']
            logger.info(f"  {period_name}: {win_rate:.1f}% win rate, ${total_pnl:.2f} P&L")
        
        return combined_trades, ml_features
    else:
        logger.error("No trades generated across any period!")
        return None, None

def generate_enhanced_training_script():
    """Generate an enhanced ML training script that uses historical data"""
    
    enhanced_script = '''#!/usr/bin/env python3
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
historical_features = pd.read_csv('data/ml_training_features_latest.csv')
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
    logger.info(f"\\nTraining {name}...")
    
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
logger.info(f"\\nBest model: {best_model[0]} with F1 score: {best_score:.3f}")
joblib.dump(best_model[1], 'trained_models/enhanced_model.pkl')

# Save results and feature importance
with open('trained_models/enhanced_training_results.json', 'w') as f:
    json.dump(results, f, indent=2)

if hasattr(best_model[1], 'feature_importances_'):
    importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': best_model[1].feature_importances_
    }).sort_values('importance', ascending=False)
    
    logger.info("\\nFeature Importance:")
    for _, row in importance.iterrows():
        logger.info(f"  {row['feature']}: {row['importance']:.3f}")
    
    importance.to_csv('trained_models/feature_importance.csv', index=False)

logger.info("\\n✅ Enhanced ML training complete!")
'''
    
    with open('train_with_historical_data.py', 'w') as f:
        f.write(enhanced_script)
    
    logger.info("Created enhanced training script: train_with_historical_data.py")

if __name__ == "__main__":
    logger.info("="*60)
    logger.info("ALGOSLAYER HISTORICAL BACKTEST SYSTEM")
    logger.info("="*60)
    logger.info("Generating massive training dataset from historical market data")
    logger.info("")
    
    # Run the multi-period backtest
    trades_df, features_df = run_multi_period_backtest()
    
    if trades_df is not None:
        # Generate enhanced training script
        generate_enhanced_training_script()
        
        logger.info("\n🎯 NEXT STEPS:")
        logger.info("1. Review the backtest results in data/backtest_analysis_*.json")
        logger.info("2. Run the enhanced ML training: python train_with_historical_data.py")
        logger.info("3. Deploy the improved models to your server")
        logger.info("4. Monitor live performance vs backtest predictions")
        
        logger.info("\n💡 PRO TIPS:")
        logger.info("- The historical data assumes simplified option pricing")
        logger.info("- For production, consider getting real historical options data from IBKR")
        logger.info("- Backtest results are indicative - real trading may differ")
        logger.info("- Use walk-forward analysis to avoid overfitting")
    else:
        logger.error("Backtest failed - please check the logs")
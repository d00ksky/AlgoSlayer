"""
Options ML Integration
Integrates options trading results into the ML learning system
Learns from real options P&L, not just stock direction
"""
import sqlite3
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger

class OptionsMLIntegration:
    """Integrates options performance data into ML training"""
    
    def __init__(self, options_db_path: str = "data/options_performance.db"):
        self.options_db_path = options_db_path
        self.feature_importance = {}
        self.signal_performance = {}
    
    def extract_options_training_data(self) -> pd.DataFrame:
        """Extract options trading data for ML training"""
        
        logger.info("📊 Extracting options training data...")
        
        conn = sqlite3.connect(self.options_db_path)
        
        query = """
        SELECT 
            p.prediction_id,
            p.timestamp as entry_timestamp,
            p.symbol,
            p.action,
            p.option_type,
            p.strike,
            p.days_to_expiry,
            p.entry_price,
            p.contracts,
            p.direction,
            p.confidence,
            p.expected_move,
            p.expected_profit_pct,
            p.implied_volatility as iv_entry,
            p.delta_entry,
            p.gamma_entry,
            p.theta_entry,
            p.vega_entry,
            p.stock_price_entry,
            p.signals_data,
            
            o.exit_timestamp,
            o.exit_price,
            o.exit_reason,
            o.days_held,
            o.net_pnl,
            o.pnl_percentage,
            o.stock_price_exit,
            o.stock_move_pct,
            o.prediction_accuracy
            
        FROM options_predictions p
        LEFT JOIN options_outcomes o ON p.prediction_id = o.prediction_id
        WHERE o.net_pnl IS NOT NULL
        ORDER BY p.timestamp
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            logger.warning("⚠️ No options trading data found")
            return pd.DataFrame()
        
        logger.success(f"✅ Extracted {len(df)} options trades for training")
        return df
    
    def engineer_options_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Engineer features specifically for options trading"""
        
        logger.info("🔧 Engineering options features...")
        
        features = []
        labels = []
        
        for _, row in df.iterrows():
            try:
                # Parse signals data
                signals_data = json.loads(row['signals_data']) if row['signals_data'] else {}
                
                # Time-based features
                entry_time = pd.to_datetime(row['entry_timestamp'])
                
                # Basic features
                feature_dict = {
                    # Prediction features
                    'confidence': row['confidence'],
                    'expected_move': row['expected_move'],
                    'expected_profit_pct': row['expected_profit_pct'],
                    
                    # Options characteristics
                    'days_to_expiry': row['days_to_expiry'],
                    'option_type_call': 1 if row['option_type'] == 'call' else 0,
                    'strike_to_stock_ratio': row['strike'] / row['stock_price_entry'] if row['stock_price_entry'] > 0 else 1,
                    'iv_entry': row['iv_entry'],
                    'delta_entry': row['delta_entry'],
                    'gamma_entry': row['gamma_entry'],
                    'theta_entry': abs(row['theta_entry']),  # Absolute value for theta
                    'vega_entry': row['vega_entry'],
                    
                    # Market timing
                    'hour': entry_time.hour,
                    'day_of_week': entry_time.dayofweek,
                    'month': entry_time.month,
                    
                    # Position sizing
                    'contracts': row['contracts'],
                    'entry_price': row['entry_price'],
                }
                
                # Signal-specific features
                for signal_name, signal_info in signals_data.items():
                    if isinstance(signal_info, dict):
                        signal_direction = signal_info.get('direction', 'HOLD')
                        signal_confidence = signal_info.get('confidence', 0.5)
                        signal_strength = signal_info.get('strength', 0.1)
                        
                        # Binary direction features
                        feature_dict[f'{signal_name}_buy'] = 1 if signal_direction == 'BUY' else 0
                        feature_dict[f'{signal_name}_sell'] = 1 if signal_direction == 'SELL' else 0
                        feature_dict[f'{signal_name}_confidence'] = signal_confidence
                        feature_dict[f'{signal_name}_strength'] = signal_strength
                
                # Fill missing signal features with defaults
                signal_names = ['news_sentiment', 'technical_analysis', 'options_flow', 'volatility_analysis', 
                               'momentum', 'sector_correlation', 'mean_reversion', 'market_regime']
                
                for signal_name in signal_names:
                    for suffix in ['_buy', '_sell', '_confidence', '_strength']:
                        key = f'{signal_name}{suffix}'
                        if key not in feature_dict:
                            if suffix in ['_buy', '_sell']:
                                feature_dict[key] = 0
                            elif suffix == '_confidence':
                                feature_dict[key] = 0.5
                            else:  # strength
                                feature_dict[key] = 0.1
                
                features.append(feature_dict)
                
                # Options-specific labels
                # Primary label: Was it profitable?
                profit_label = 1 if row['net_pnl'] > 0 else 0
                
                # Additional learning targets
                pnl_category = self._categorize_pnl(row['pnl_percentage'])
                
                labels.append({
                    'profitable': profit_label,
                    'pnl_percentage': row['pnl_percentage'],
                    'pnl_category': pnl_category,
                    'days_held': row['days_held'],
                    'exit_reason': row['exit_reason']
                })
                
            except Exception as e:
                logger.warning(f"⚠️ Error processing trade {row.get('prediction_id', 'unknown')}: {e}")
                continue
        
        if not features:
            logger.error("❌ No features engineered")
            return pd.DataFrame(), pd.Series()
        
        features_df = pd.DataFrame(features)
        labels_df = pd.DataFrame(labels)
        
        logger.success(f"✅ Engineered {len(features_df.columns)} features from {len(features_df)} trades")
        
        return features_df, labels_df['profitable']  # Return profitability as main target
    
    def _categorize_pnl(self, pnl_pct: float) -> int:
        """Categorize P&L into buckets for classification"""
        if pnl_pct >= 1.0:  # 100%+ gain
            return 3  # Excellent
        elif pnl_pct >= 0.5:  # 50-100% gain
            return 2  # Good
        elif pnl_pct > 0:  # 0-50% gain
            return 1  # Small profit
        else:  # Loss
            return 0  # Loss
    
    def analyze_signal_performance(self, df: pd.DataFrame) -> Dict:
        """Analyze which signals performed best for options trading"""
        
        logger.info("📊 Analyzing signal performance for options...")
        
        signal_performance = {}
        
        signal_names = ['news_sentiment', 'technical_analysis', 'options_flow', 'volatility_analysis',
                       'momentum', 'sector_correlation', 'mean_reversion', 'market_regime']
        
        for signal_name in signal_names:
            # Extract trades where this signal was bullish/bearish
            bullish_mask = df[f'{signal_name}_buy'] == 1
            bearish_mask = df[f'{signal_name}_sell'] == 1
            
            if bullish_mask.sum() > 5:  # Need at least 5 trades
                bullish_trades = df[bullish_mask]
                bullish_avg_pnl = bullish_trades['pnl_percentage'].mean()
                bullish_win_rate = (bullish_trades['net_pnl'] > 0).mean()
                bullish_avg_confidence = bullish_trades[f'{signal_name}_confidence'].mean()
            else:
                bullish_avg_pnl = bullish_win_rate = bullish_avg_confidence = 0
            
            if bearish_mask.sum() > 5:
                bearish_trades = df[bearish_mask]
                bearish_avg_pnl = bearish_trades['pnl_percentage'].mean()
                bearish_win_rate = (bearish_trades['net_pnl'] > 0).mean()
                bearish_avg_confidence = bearish_trades[f'{signal_name}_confidence'].mean()
            else:
                bearish_avg_pnl = bearish_win_rate = bearish_avg_confidence = 0
            
            signal_performance[signal_name] = {
                'bullish_avg_pnl': bullish_avg_pnl,
                'bullish_win_rate': bullish_win_rate,
                'bullish_confidence': bullish_avg_confidence,
                'bearish_avg_pnl': bearish_avg_pnl,
                'bearish_win_rate': bearish_win_rate,
                'bearish_confidence': bearish_avg_confidence,
                'total_trades': bullish_mask.sum() + bearish_mask.sum(),
                'overall_performance': (bullish_avg_pnl + bearish_avg_pnl) / 2
            }
        
        # Sort by overall performance
        sorted_signals = sorted(signal_performance.items(), 
                               key=lambda x: x[1]['overall_performance'], reverse=True)
        
        logger.info("📊 Signal Performance Ranking:")
        for i, (signal_name, perf) in enumerate(sorted_signals[:5]):
            logger.info(f"{i+1}. {signal_name}: {perf['overall_performance']:.1f}% avg P&L, {perf['total_trades']} trades")
        
        self.signal_performance = dict(sorted_signals)
        return self.signal_performance
    
    def generate_adaptive_weights(self, signal_performance: Dict) -> Dict:
        """Generate new signal weights based on options performance"""
        
        logger.info("⚖️ Generating adaptive signal weights...")
        
        # Base weights
        base_weight = 0.05
        total_weight = 0.8  # Leave 20% for base weights
        
        # Calculate performance scores
        performance_scores = {}
        min_trades = 10  # Minimum trades to be considered
        
        for signal_name, perf in signal_performance.items():
            if perf['total_trades'] >= min_trades:
                # Combine win rate and average P&L
                bullish_score = perf['bullish_win_rate'] * (1 + perf['bullish_avg_pnl'])
                bearish_score = perf['bearish_win_rate'] * (1 + perf['bearish_avg_pnl'])
                combined_score = (bullish_score + bearish_score) / 2
                performance_scores[signal_name] = max(0, combined_score)  # Ensure non-negative
            else:
                performance_scores[signal_name] = 0.1  # Default for insufficient data
        
        # Normalize to sum to total_weight
        total_score = sum(performance_scores.values())
        
        if total_score > 0:
            adaptive_weights = {
                signal_name: base_weight + (score / total_score * total_weight)
                for signal_name, score in performance_scores.items()
            }
        else:
            # Fallback to equal weights
            adaptive_weights = {signal_name: 1.0 / len(performance_scores) 
                               for signal_name in performance_scores.keys()}
        
        logger.info("🎯 New adaptive weights:")
        for signal_name, weight in sorted(adaptive_weights.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {signal_name}: {weight:.1f}%")
        
        return adaptive_weights
    
    def update_scheduler_weights(self, new_weights: Dict):
        """Update the scheduler with new signal weights"""
        
        # Import here to avoid circular imports
        from src.core.options_scheduler import options_scheduler
        
        # Update weights
        options_scheduler.signal_weights.update(new_weights)
        
        logger.success("✅ Updated scheduler with new signal weights")
    
    def analyze_options_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze patterns specific to successful options trades"""
        
        logger.info("🔍 Analyzing options trading patterns...")
        
        profitable_trades = df[df['net_pnl'] > 0]
        losing_trades = df[df['net_pnl'] <= 0]
        
        patterns = {}
        
        if len(profitable_trades) > 5 and len(losing_trades) > 5:
            # Time to expiry analysis
            profitable_dte = profitable_trades['days_to_expiry'].mean()
            losing_dte = losing_trades['days_to_expiry'].mean()
            
            # IV analysis
            profitable_iv = profitable_trades['iv_entry'].mean()
            losing_iv = losing_trades['iv_entry'].mean()
            
            # Delta analysis
            profitable_delta = profitable_trades['delta_entry'].mean()
            losing_delta = losing_trades['delta_entry'].mean()
            
            # Confidence analysis
            profitable_confidence = profitable_trades['confidence'].mean()
            losing_confidence = losing_trades['confidence'].mean()
            
            patterns = {
                'optimal_dte': profitable_dte,
                'optimal_iv': profitable_iv,
                'optimal_delta': profitable_delta,
                'optimal_confidence': profitable_confidence,
                'dte_diff': profitable_dte - losing_dte,
                'iv_diff': profitable_iv - losing_iv,
                'delta_diff': profitable_delta - losing_delta,
                'confidence_diff': profitable_confidence - losing_confidence
            }
            
            logger.info("📊 Options Trading Patterns:")
            logger.info(f"  Optimal DTE: {profitable_dte:.1f} days")
            logger.info(f"  Optimal IV: {profitable_iv:.1f}%")
            logger.info(f"  Optimal Delta: {profitable_delta:.2f}")
            logger.info(f"  Optimal Confidence: {profitable_confidence:.1f}%")
        
        return patterns
    
    def generate_options_insights(self) -> Dict:
        """Generate comprehensive insights for options trading"""
        
        logger.info("🧠 Generating options trading insights...")
        
        # Extract data
        df = self.extract_options_training_data()
        
        if df.empty:
            return {'error': 'No trading data available'}
        
        # Analyze signal performance
        signal_perf = self.analyze_signal_performance(df)
        
        # Generate adaptive weights
        adaptive_weights = self.generate_adaptive_weights(signal_perf)
        
        # Analyze patterns
        patterns = self.analyze_options_patterns(df)
        
        # Overall performance
        total_trades = len(df)
        profitable_trades = (df['net_pnl'] > 0).sum()
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        avg_pnl = df['pnl_percentage'].mean() if total_trades > 0 else 0
        
        insights = {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_pnl_percentage': avg_pnl,
            'signal_performance': signal_perf,
            'adaptive_weights': adaptive_weights,
            'trading_patterns': patterns,
            'generated_at': datetime.now().isoformat()
        }
        
        logger.success(f"✅ Generated insights from {total_trades} trades ({win_rate:.1f}% win rate)")
        
        return insights

# Create global instance
options_ml_integration = OptionsMLIntegration()

if __name__ == "__main__":
    # Test the ML integration
    logger.info("🧪 Testing Options ML Integration...")
    
    integration = OptionsMLIntegration()
    
    # Generate insights
    insights = integration.generate_options_insights()
    
    if 'error' in insights:
        print(f"❌ {insights['error']}")
    else:
        print(f"✅ Analyzed {insights['total_trades']} trades")
        print(f"Win Rate: {insights['win_rate']:.1f}%")
        print(f"Avg P&L: {insights['avg_pnl_percentage']:.1f}%")
        
        if insights['adaptive_weights']:
            print("\\nTop performing signals:")
            for signal, weight in list(insights['adaptive_weights'].items())[:3]:
                print(f"  {signal}: {weight:.1f}%")
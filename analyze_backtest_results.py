#!/usr/bin/env python3
"""
Analyze and Visualize Historical Backtest Results
Provides insights into strategy performance across different market conditions
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json
import sqlite3
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class BacktestAnalyzer:
    """Comprehensive analysis of backtest results"""
    
    def __init__(self, results_dir: str = "data"):
        self.results_dir = Path(results_dir)
        self.trades_df = None
        self.features_df = None
        self.analysis = None
        
    def load_latest_results(self):
        """Load the most recent backtest results"""
        # Find latest files
        trade_files = list(self.results_dir.glob("historical_trades_*.csv"))
        feature_files = list(self.results_dir.glob("ml_training_features_*.csv"))
        analysis_files = list(self.results_dir.glob("backtest_analysis_*.json"))
        
        if not trade_files:
            print("No backtest results found. Run 'python run_historical_backtest.py' first.")
            return False
            
        # Load most recent files
        latest_trades = max(trade_files, key=lambda p: p.stat().st_mtime)
        self.trades_df = pd.read_csv(latest_trades)
        print(f"Loaded {len(self.trades_df)} trades from {latest_trades.name}")
        
        if feature_files:
            latest_features = max(feature_files, key=lambda p: p.stat().st_mtime)
            self.features_df = pd.read_csv(latest_features)
            print(f"Loaded {len(self.features_df)} ML features from {latest_features.name}")
            
        if analysis_files:
            latest_analysis = max(analysis_files, key=lambda p: p.stat().st_mtime)
            with open(latest_analysis, 'r') as f:
                self.analysis = json.load(f)
            print(f"Loaded analysis from {latest_analysis.name}")
            
        # Convert timestamps
        self.trades_df['timestamp'] = pd.to_datetime(self.trades_df['timestamp'])
        self.trades_df['exit_timestamp'] = pd.to_datetime(self.trades_df['exit_timestamp'])
        
        return True
        
    def print_summary_report(self):
        """Print comprehensive summary report"""
        print("\n" + "="*80)
        print("HISTORICAL BACKTEST SUMMARY REPORT")
        print("="*80)
        
        if self.analysis:
            config = self.analysis.get('configuration', {})
            print(f"\nBacktest Configuration:")
            print(f"  Symbol: {config.get('symbol', 'RTX')}")
            print(f"  Periods Tested: {config.get('periods_tested', 'N/A')}")
            print(f"  Total Years: {config.get('total_years', 'N/A')}")
            print(f"  Strategies: {', '.join(config.get('strategies', []))}")
            
        print(f"\nOverall Performance:")
        print(f"  Total Trades: {len(self.trades_df):,}")
        print(f"  Profitable Trades: {len(self.trades_df[self.trades_df['pnl'] > 0]):,}")
        print(f"  Win Rate: {(self.trades_df['pnl'] > 0).mean()*100:.1f}%")
        print(f"  Total P&L: ${self.trades_df['pnl'].sum():,.2f}")
        print(f"  Average P&L per Trade: ${self.trades_df['pnl'].mean():.2f}")
        print(f"  Average Win: {self.trades_df[self.trades_df['pnl'] > 0]['pnl_percentage'].mean():.1f}%")
        print(f"  Average Loss: {self.trades_df[self.trades_df['pnl'] < 0]['pnl_percentage'].mean():.1f}%")
        
        # Strategy Performance
        print("\n" + "-"*50)
        print("STRATEGY PERFORMANCE RANKING")
        print("-"*50)
        
        strategy_stats = []
        for strategy in self.trades_df['strategy'].unique():
            s_df = self.trades_df[self.trades_df['strategy'] == strategy]
            win_rate = (s_df['pnl'] > 0).mean() * 100
            total_pnl = s_df['pnl'].sum()
            avg_pnl = s_df['pnl_percentage'].mean()
            trades = len(s_df)
            
            strategy_stats.append({
                'Strategy': strategy,
                'Trades': trades,
                'Win Rate': win_rate,
                'Total P&L': total_pnl,
                'Avg P&L %': avg_pnl
            })
            
        strategy_df = pd.DataFrame(strategy_stats).sort_values('Total P&L', ascending=False)
        
        for idx, row in strategy_df.iterrows():
            print(f"{row['Strategy']:15} | Trades: {row['Trades']:4d} | "
                  f"Win: {row['Win Rate']:5.1f}% | P&L: ${row['Total P&L']:8.2f} | "
                  f"Avg: {row['Avg P&L %']:+6.1f}%")
                  
        # Market Condition Analysis
        if 'period' in self.trades_df.columns:
            print("\n" + "-"*50)
            print("PERFORMANCE BY MARKET CONDITION")
            print("-"*50)
            
            for period in self.trades_df['period'].unique():
                p_df = self.trades_df[self.trades_df['period'] == period]
                win_rate = (p_df['pnl'] > 0).mean() * 100
                total_pnl = p_df['pnl'].sum()
                
                print(f"{period:25} | Trades: {len(p_df):4d} | "
                      f"Win: {win_rate:5.1f}% | P&L: ${total_pnl:8.2f}")
                      
        # Exit Reason Analysis
        print("\n" + "-"*50)
        print("EXIT REASON ANALYSIS")
        print("-"*50)
        
        exit_stats = self.trades_df.groupby('exit_reason').agg({
            'pnl': ['count', 'sum', 'mean'],
            'pnl_percentage': 'mean'
        }).round(2)
        
        exit_stats.columns = ['Count', 'Total P&L', 'Avg P&L', 'Avg %']
        print(exit_stats.sort_values('Count', ascending=False))
        
    def generate_visualizations(self):
        """Generate comprehensive visualizations"""
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
        fig = plt.figure(figsize=(20, 16))
        
        # 1. Cumulative P&L Chart
        ax1 = plt.subplot(3, 3, 1)
        self.trades_df['cumulative_pnl'] = self.trades_df.sort_values('timestamp')['pnl'].cumsum()
        self.trades_df.plot(x='timestamp', y='cumulative_pnl', ax=ax1, legend=False)
        ax1.set_title('Cumulative P&L Over Time', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Cumulative P&L ($)')
        ax1.axhline(y=0, color='r', linestyle='--', alpha=0.5)
        
        # 2. Win Rate by Strategy
        ax2 = plt.subplot(3, 3, 2)
        strategy_winrates = self.trades_df.groupby('strategy').apply(
            lambda x: (x['pnl'] > 0).mean() * 100
        ).sort_values(ascending=True)
        strategy_winrates.plot(kind='barh', ax=ax2, color='skyblue')
        ax2.set_title('Win Rate by Strategy', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Win Rate (%)')
        ax2.axvline(x=50, color='r', linestyle='--', alpha=0.5)
        
        # 3. P&L Distribution
        ax3 = plt.subplot(3, 3, 3)
        self.trades_df['pnl_percentage'].hist(bins=50, ax=ax3, alpha=0.7, color='green')
        ax3.set_title('P&L Distribution', fontsize=14, fontweight='bold')
        ax3.set_xlabel('P&L %')
        ax3.set_ylabel('Frequency')
        ax3.axvline(x=0, color='r', linestyle='--', alpha=0.5)
        
        # 4. Average Trade Duration by Strategy
        ax4 = plt.subplot(3, 3, 4)
        avg_duration = self.trades_df.groupby('strategy')['days_held'].mean().sort_values()
        avg_duration.plot(kind='bar', ax=ax4, color='coral')
        ax4.set_title('Average Days Held by Strategy', fontsize=14, fontweight='bold')
        ax4.set_ylabel('Days')
        ax4.set_xticklabels(ax4.get_xticklabels(), rotation=45)
        
        # 5. Monthly Performance
        ax5 = plt.subplot(3, 3, 5)
        self.trades_df['month'] = self.trades_df['timestamp'].dt.to_period('M')
        monthly_pnl = self.trades_df.groupby('month')['pnl'].sum()
        monthly_pnl.plot(kind='bar', ax=ax5, color='purple')
        ax5.set_title('Monthly P&L', fontsize=14, fontweight='bold')
        ax5.set_xlabel('Month')
        ax5.set_ylabel('P&L ($)')
        ax5.axhline(y=0, color='r', linestyle='--', alpha=0.5)
        
        # 6. Strategy Correlation Heatmap
        ax6 = plt.subplot(3, 3, 6)
        if len(self.trades_df['strategy'].unique()) > 1:
            pivot_df = self.trades_df.pivot_table(
                values='pnl_percentage', 
                index=self.trades_df['timestamp'].dt.date,
                columns='strategy',
                aggfunc='mean'
            )
            corr_matrix = pivot_df.corr()
            sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', ax=ax6)
            ax6.set_title('Strategy Correlation', fontsize=14, fontweight='bold')
        
        # 7. Exit Reason Performance
        ax7 = plt.subplot(3, 3, 7)
        exit_performance = self.trades_df.groupby('exit_reason')['pnl_percentage'].mean().sort_values()
        exit_performance.plot(kind='barh', ax=ax7, color='lightgreen')
        ax7.set_title('Average P&L by Exit Reason', fontsize=14, fontweight='bold')
        ax7.set_xlabel('Average P&L %')
        ax7.axvline(x=0, color='r', linestyle='--', alpha=0.5)
        
        # 8. Confidence vs Outcome
        ax8 = plt.subplot(3, 3, 8)
        profitable = self.trades_df[self.trades_df['pnl'] > 0]
        unprofitable = self.trades_df[self.trades_df['pnl'] <= 0]
        ax8.hist([profitable['confidence'], unprofitable['confidence']], 
                label=['Profitable', 'Unprofitable'], bins=20, alpha=0.7)
        ax8.set_title('Confidence Distribution by Outcome', fontsize=14, fontweight='bold')
        ax8.set_xlabel('Confidence')
        ax8.set_ylabel('Frequency')
        ax8.legend()
        
        # 9. Market Condition Performance
        ax9 = plt.subplot(3, 3, 9)
        if 'period' in self.trades_df.columns:
            period_stats = self.trades_df.groupby('period').agg({
                'pnl': 'sum'
            }).sort_values('pnl')
            period_stats.plot(kind='bar', ax=ax9, color='orange', legend=False)
            ax9.set_title('P&L by Market Period', fontsize=14, fontweight='bold')
            ax9.set_ylabel('Total P&L ($)')
            ax9.set_xticklabels(ax9.get_xticklabels(), rotation=45)
            ax9.axhline(y=0, color='r', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        
        # Save the figure
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'backtest_analysis_{timestamp}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"\nVisualization saved as: {filename}")
        
        plt.show()
        
    def generate_ml_insights(self):
        """Generate insights specifically for ML training"""
        if self.features_df is None:
            print("\nNo ML features found. Run backtest first.")
            return
            
        print("\n" + "="*80)
        print("MACHINE LEARNING INSIGHTS")
        print("="*80)
        
        # Feature importance based on correlation with profitability
        feature_cols = [col for col in self.features_df.columns 
                       if col.endswith('_confidence') or col in ['moneyness', 'days_to_expiry', 'signal_agreement']]
        
        correlations = {}
        for col in feature_cols:
            if col in self.features_df.columns:
                corr = self.features_df[col].corr(self.features_df['profitable'])
                correlations[col] = corr
                
        # Sort by absolute correlation
        sorted_corr = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
        
        print("\nFeature Correlations with Profitability:")
        print("-" * 40)
        for feature, corr in sorted_corr:
            print(f"{feature:30} {corr:+.3f}")
            
        # Optimal thresholds
        print("\nOptimal Confidence Thresholds:")
        print("-" * 40)
        
        for strategy in self.features_df['strategy'].unique():
            strategy_df = self.features_df[self.features_df['strategy'] == strategy]
            profitable_df = strategy_df[strategy_df['profitable'] == 1]
            
            if len(profitable_df) > 0:
                # Find confidence threshold that maximizes profit
                thresholds = np.arange(0.5, 0.9, 0.05)
                best_threshold = 0.5
                best_profit = -float('inf')
                
                for threshold in thresholds:
                    trades_above = strategy_df[strategy_df['confidence'] >= threshold]
                    if len(trades_above) > 0:
                        total_profit = trades_above['pnl_percentage'].sum()
                        if total_profit > best_profit:
                            best_profit = total_profit
                            best_threshold = threshold
                            
                print(f"{strategy:15} {best_threshold:.2f} "
                      f"({len(strategy_df[strategy_df['confidence'] >= best_threshold])} trades, "
                      f"{best_profit:.1f}% total return)")
                      
        # Signal combination insights
        print("\nBest Signal Combinations:")
        print("-" * 40)
        
        # Group by signal agreement count
        agreement_stats = self.features_df.groupby('signal_agreement').agg({
            'profitable': 'mean',
            'pnl_percentage': 'mean'
        }).round(3)
        
        print("Signals Agreeing | Win Rate | Avg P&L %")
        for idx, row in agreement_stats.iterrows():
            print(f"      {idx}         |  {row['profitable']*100:5.1f}%  | {row['pnl_percentage']:+6.1f}%")
            
    def export_enhanced_training_data(self):
        """Export enhanced training data with additional features"""
        if self.features_df is None:
            print("\nNo features to export.")
            return
            
        # Add additional engineered features
        enhanced_df = self.features_df.copy()
        
        # Add time-based features
        enhanced_df['timestamp'] = pd.to_datetime(enhanced_df['timestamp'])
        enhanced_df['day_of_week'] = enhanced_df['timestamp'].dt.dayofweek
        enhanced_df['month'] = enhanced_df['timestamp'].dt.month
        enhanced_df['quarter'] = enhanced_df['timestamp'].dt.quarter
        
        # Add derived features
        enhanced_df['confidence_squared'] = enhanced_df['confidence'] ** 2
        enhanced_df['moneyness_category'] = pd.cut(
            enhanced_df['moneyness'], 
            bins=[0, 0.95, 1.05, 2.0],
            labels=['OTM', 'ATM', 'ITM']
        )
        
        # Add rolling statistics (if we have enough data)
        if len(enhanced_df) > 100:
            enhanced_df = enhanced_df.sort_values('timestamp')
            
            # Calculate rolling win rate for each strategy
            for strategy in enhanced_df['strategy'].unique():
                mask = enhanced_df['strategy'] == strategy
                enhanced_df.loc[mask, 'rolling_win_rate'] = (
                    enhanced_df.loc[mask, 'profitable']
                    .rolling(window=20, min_periods=5)
                    .mean()
                )
                
        # Save enhanced dataset
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'data/enhanced_ml_training_{timestamp}.csv'
        enhanced_df.to_csv(filename, index=False)
        
        print(f"\n✅ Enhanced training data exported to: {filename}")
        print(f"   Total examples: {len(enhanced_df):,}")
        print(f"   Features: {len(enhanced_df.columns)}")
        print(f"   Date range: {enhanced_df['timestamp'].min()} to {enhanced_df['timestamp'].max()}")
        
        # Also create a lightweight version for the server
        lightweight_cols = [
            'strategy', 'confidence', 'moneyness', 'days_to_expiry',
            'signal_agreement', 'profitable', 'pnl_percentage'
        ]
        
        lightweight_df = enhanced_df[lightweight_cols]
        lightweight_file = f'data/lightweight_ml_training_{timestamp}.csv'
        lightweight_df.to_csv(lightweight_file, index=False)
        
        print(f"   Lightweight version: {lightweight_file} ({len(lightweight_cols)} features)")

def main():
    """Main analysis workflow"""
    print("AlgoSlayer Historical Backtest Analysis")
    print("="*80)
    
    analyzer = BacktestAnalyzer()
    
    # Load results
    if not analyzer.load_latest_results():
        return
        
    # Generate reports
    analyzer.print_summary_report()
    
    # Generate ML insights
    analyzer.generate_ml_insights()
    
    # Export enhanced training data
    analyzer.export_enhanced_training_data()
    
    # Generate visualizations
    print("\nGenerating visualizations...")
    analyzer.generate_visualizations()
    
    print("\n✅ Analysis complete!")
    print("\nNext steps:")
    print("1. Review the visualizations and insights")
    print("2. Use the enhanced training data for ML model updates")
    print("3. Deploy improved models to your trading system")
    print("4. Monitor live performance vs backtest predictions")

if __name__ == "__main__":
    main()
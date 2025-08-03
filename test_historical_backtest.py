#!/usr/bin/env python3
"""
Quick test of the historical backtesting system
Tests with a shorter time period to verify everything works
"""
import sys
from datetime import datetime, timedelta
from loguru import logger
from src.core.historical_backtester import (
    HistoricalDataFetcher, 
    HistoricalSignalSimulator, 
    HistoricalBacktestEngine
)

# Configure logging
logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}")

def test_backtest_system():
    """Test the backtesting system with a short period"""
    
    print("="*60)
    print("TESTING HISTORICAL BACKTEST SYSTEM")
    print("="*60)
    
    # Initialize components
    print("\n1. Initializing components...")
    data_fetcher = HistoricalDataFetcher()
    signal_simulator = HistoricalSignalSimulator()
    backtest_engine = HistoricalBacktestEngine(data_fetcher, signal_simulator)
    print("✅ Components initialized")
    
    # Test with 3 months of recent data
    end_date = '2024-07-31'
    start_date = '2024-05-01'
    
    print(f"\n2. Testing backtest from {start_date} to {end_date}...")
    
    try:
        # Run backtest
        trades_df = backtest_engine.backtest_period(
            symbol='RTX',
            start_date=start_date,
            end_date=end_date,
            initial_capital=10000
        )
        
        if trades_df.empty:
            print("❌ No trades generated")
            return False
            
        print(f"✅ Generated {len(trades_df)} trades")
        
        # Analyze results
        print("\n3. Analyzing results...")
        analysis = backtest_engine.analyze_results(trades_df)
        
        print("\nQuick Summary:")
        print(f"  Total trades: {analysis['total_trades']}")
        print(f"  Win rate: {analysis['overall_metrics']['win_rate']:.1f}%")
        print(f"  Total P&L: ${analysis['overall_metrics']['total_pnl']:.2f}")
        
        # Show sample trades
        print("\nSample Trades:")
        print("-" * 60)
        sample_trades = trades_df.head(5)
        for idx, trade in sample_trades.iterrows():
            print(f"{trade['strategy']:12} | {trade['timestamp'].date()} | "
                  f"{trade['option_type']} ${trade['strike']} | "
                  f"Conf: {trade['confidence']:.2f} | "
                  f"P&L: {trade['pnl_percentage']:+.1f}%")
                  
        # Test ML feature generation
        print("\n4. Testing ML feature generation...")
        from run_historical_backtest import BacktestMLIntegrator
        
        ml_integrator = BacktestMLIntegrator()
        features_df = ml_integrator.prepare_ml_features(trades_df)
        
        print(f"✅ Generated {len(features_df)} ML training examples")
        print(f"   Features: {list(features_df.columns)[:5]}... ({len(features_df.columns)} total)")
        
        # Save test results
        trades_df.to_csv('data/test_backtest_trades.csv', index=False)
        features_df.to_csv('data/test_ml_features.csv', index=False)
        
        print("\n✅ TEST PASSED! Backtesting system is working correctly.")
        print("\nTest files saved:")
        print("  - data/test_backtest_trades.csv")
        print("  - data/test_ml_features.csv")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        logger.exception("Detailed error:")
        return False

def test_data_fetching():
    """Test just the data fetching component"""
    print("\n" + "="*60)
    print("TESTING DATA FETCHING")
    print("="*60)
    
    data_fetcher = HistoricalDataFetcher()
    
    try:
        # Test stock data fetching
        print("\nFetching RTX stock data...")
        stock_data = data_fetcher.fetch_stock_history('RTX', '2024-05-01', '2024-07-31')
        
        if stock_data.empty:
            print("❌ No stock data fetched")
            return False
            
        print(f"✅ Fetched {len(stock_data)} days of stock data")
        print(f"   Columns: {list(stock_data.columns)}")
        print(f"   Date range: {stock_data.index[0]} to {stock_data.index[-1]}")
        print(f"   Latest close: ${stock_data['Close'].iloc[-1]:.2f}")
        
        # Test option pricing
        print("\nTesting option price estimation...")
        option_prices = data_fetcher.estimate_option_prices(
            stock_price=100,
            strike=105,
            days_to_expiry=30,
            volatility=0.3
        )
        
        print(f"✅ Option prices estimated:")
        print(f"   Call: ${option_prices['call']}")
        print(f"   Put: ${option_prices['put']}")
        print(f"   IV: {option_prices['iv']}")
        print(f"   Delta: {option_prices['delta']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data fetching failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("AlgoSlayer Historical Backtest System Test")
    print("="*60)
    
    # Create data directory if it doesn't exist
    import os
    os.makedirs('data', exist_ok=True)
    os.makedirs('historical_data_cache', exist_ok=True)
    
    # Run tests
    data_test = test_data_fetching()
    backtest_test = test_backtest_system()
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Data Fetching: {'✅ PASSED' if data_test else '❌ FAILED'}")
    print(f"Backtesting: {'✅ PASSED' if backtest_test else '❌ FAILED'}")
    
    if data_test and backtest_test:
        print("\n🎉 All tests passed! The backtesting system is ready to use.")
        print("\nNext steps:")
        print("1. Run full historical backtest: python run_historical_backtest.py")
        print("2. Analyze results: python analyze_backtest_results.py")
        print("3. Train ML with historical data: python train_with_historical_data.py")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()
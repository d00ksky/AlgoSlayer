#!/usr/bin/env python3
"""
Real-Time Feature Engineering Pipeline - Phase 3
Live calculation of advanced features for streaming ML predictions

This module extends our Phase 1 advanced features to work in real-time:
1. Streams market data continuously
2. Calculates all 82 advanced features in real-time
3. Maintains rolling windows for technical indicators
4. Triggers ML predictions when features are ready

Expected enhancement: Real-time decision making capability
"""
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sqlite3
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import threading
from collections import deque
from loguru import logger
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

# Import our existing feature engineer
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.ml.advanced_features import AdvancedFeatureEngineer

@dataclass
class RealTimeFeatures:
    """Container for real-time calculated features"""
    timestamp: datetime
    features: Dict[str, float]
    confidence: float
    data_completeness: float
    calculation_time_ms: float

class RealTimeFeatureEngine:
    """
    Real-time feature engineering pipeline
    
    Maintains rolling windows of market data and calculates
    all 82 advanced features in real-time for immediate ML predictions
    """
    
    def __init__(self, window_size: int = 1000):
        """
        Initialize real-time feature engine
        
        Args:
            window_size: Number of data points to maintain in rolling windows
        """
        self.window_size = window_size
        self.feature_engineer = AdvancedFeatureEngineer()
        
        # Rolling data windows
        self.price_windows: Dict[str, deque] = {}
        self.feature_cache: Dict[str, RealTimeFeatures] = {}
        self.last_calculation: Optional[datetime] = None
        
        # Symbols we track
        self.symbols = ['RTX', 'SPY', '^VIX', 'DX-Y.NYB', 'ITA']
        
        # Initialize rolling windows
        for symbol in self.symbols:
            self.price_windows[symbol] = deque(maxlen=window_size)
        
        # Thread safety
        self.data_lock = threading.Lock()
        
        # Performance tracking
        self.calculation_times: deque = deque(maxlen=100)
        self.feature_update_count = 0
        
        logger.info("⚡ Real-time feature engine initialized")
        logger.info(f"🔧 Window size: {window_size}, Symbols: {len(self.symbols)}")
    
    async def update_market_data(self, symbol: str, price: float, volume: int, 
                               timestamp: datetime, **kwargs):
        """
        Update market data for a symbol
        
        Args:
            symbol: Stock symbol
            price: Current price
            volume: Trading volume
            timestamp: Data timestamp
            **kwargs: Additional data (bid, ask, etc.)
        """
        data_point = {
            'symbol': symbol,
            'price': price,
            'volume': volume,
            'timestamp': timestamp,
            **kwargs
        }
        
        with self.data_lock:
            self.price_windows[symbol].append(data_point)
        
        # Trigger feature calculation if we have enough data
        if self.should_calculate_features():
            await self.calculate_features_async()
    
    def should_calculate_features(self) -> bool:
        """Determine if we should recalculate features"""
        # Check if we have recent data for all key symbols
        required_symbols = ['RTX', 'SPY', '^VIX']
        
        for symbol in required_symbols:
            if not self.price_windows[symbol]:
                return False
            
            # Check if data is recent (within last minute)
            latest_data = self.price_windows[symbol][-1]
            age = datetime.now() - latest_data['timestamp']
            if age > timedelta(minutes=1):
                return False
        
        # Don't calculate too frequently
        if self.last_calculation:
            time_since_last = datetime.now() - self.last_calculation
            if time_since_last < timedelta(seconds=10):  # Max every 10 seconds
                return False
        
        return True
    
    async def calculate_features_async(self):
        """Calculate features asynchronously"""
        start_time = datetime.now()
        
        try:
            # Prepare data in the format expected by AdvancedFeatureEngineer
            current_data = self.prepare_current_data()
            
            if current_data is None:
                logger.warning("⚠️ Insufficient data for feature calculation")
                return None
            
            # Calculate features
            features = await self.calculate_advanced_features(current_data)
            
            # Calculate performance metrics
            calculation_time = (datetime.now() - start_time).total_seconds() * 1000
            self.calculation_times.append(calculation_time)
            
            # Create feature container
            rt_features = RealTimeFeatures(
                timestamp=datetime.now(),
                features=features,
                confidence=self.calculate_confidence_score(features),
                data_completeness=self.calculate_data_completeness(),
                calculation_time_ms=calculation_time
            )
            
            # Cache results
            with self.data_lock:
                self.feature_cache['latest'] = rt_features
                self.last_calculation = datetime.now()
                self.feature_update_count += 1
            
            logger.info(f"⚡ Features calculated: {len(features)} features in {calculation_time:.1f}ms")
            
            return rt_features
            
        except Exception as e:
            logger.error(f"❌ Feature calculation error: {e}")
            return None
    
    def prepare_current_data(self) -> Optional[pd.DataFrame]:
        """Prepare current market data for feature engineering"""
        try:
            # Get the latest data point from each symbol
            latest_data = {}
            
            with self.data_lock:
                for symbol in self.symbols:
                    if self.price_windows[symbol]:
                        latest_data[symbol] = self.price_windows[symbol][-1]
            
            if 'RTX' not in latest_data:
                return None
            
            # Create a DataFrame row similar to our training data
            rtx_data = latest_data['RTX']
            
            # Create the data structure expected by AdvancedFeatureEngineer
            data_row = {
                'prediction_id': f"rt_{int(datetime.now().timestamp())}",
                'timestamp': rtx_data['timestamp'],
                'symbol': 'RTX',
                'direction': 'UNKNOWN',  # We don't know the direction yet
                'confidence': 0.7,  # Default confidence
                'expected_move': 0.02,  # Default expected move
                'signal_data': json.dumps({
                    'technical_analysis': 0.5,
                    'momentum': 0.5,
                    'news_sentiment': 0.5,
                    'volatility_analysis': 0.5,
                    'options_flow': 0.5,
                    'sector_correlation': 0.5,
                    'mean_reversion': 0.5,
                    'market_regime': 0.5
                }),
                'price_at_prediction': rtx_data['price'],
                'reasoning': 'Real-time prediction'
            }
            
            # Add current market data to the row
            if 'SPY' in latest_data:
                data_row['spy_price'] = latest_data['SPY']['price']
            if '^VIX' in latest_data:
                data_row['vix_price'] = latest_data['^VIX']['price']
            if 'DX-Y.NYB' in latest_data:
                data_row['dxy_price'] = latest_data['DX-Y.NYB']['price']
            if 'ITA' in latest_data:
                data_row['ita_price'] = latest_data['ITA']['price']
            
            # Convert to DataFrame
            df = pd.DataFrame([data_row])
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Data preparation error: {e}")
            return None
    
    async def calculate_advanced_features(self, current_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate advanced features using our existing engine"""
        try:
            # Use our existing feature engineer with some adaptations for real-time
            enhanced_df = self.feature_engineer.engineer_features(current_data)
            
            if enhanced_df.empty:
                return {}
            
            # Extract features (exclude metadata columns)
            exclude_columns = {
                'prediction_id', 'timestamp', 'symbol', 'direction', 
                'signal_data', 'price_at_prediction', 'reasoning'
            }
            
            features = {}
            for col in enhanced_df.columns:
                if col not in exclude_columns:
                    value = enhanced_df[col].iloc[0]
                    # Ensure numeric values
                    if pd.isna(value):
                        value = 0.0
                    features[col] = float(value)
            
            # Add real-time specific features
            features.update(self.calculate_realtime_specific_features())
            
            return features
            
        except Exception as e:
            logger.error(f"❌ Advanced feature calculation error: {e}")
            return {}
    
    def calculate_realtime_specific_features(self) -> Dict[str, float]:
        """Calculate features specific to real-time operation"""
        features = {}
        
        try:
            with self.data_lock:
                # Price momentum features
                if len(self.price_windows['RTX']) > 5:
                    rtx_prices = [dp['price'] for dp in list(self.price_windows['RTX'])[-5:]]
                    features['rtx_momentum_1min'] = (rtx_prices[-1] - rtx_prices[0]) / rtx_prices[0]
                    features['rtx_volatility_1min'] = np.std(rtx_prices) / np.mean(rtx_prices)
                
                # Cross-asset momentum
                for symbol in ['SPY', '^VIX', 'DX-Y.NYB']:
                    if len(self.price_windows[symbol]) > 3:
                        prices = [dp['price'] for dp in list(self.price_windows[symbol])[-3:]]
                        features[f'{symbol.lower()}_momentum_30s'] = (prices[-1] - prices[0]) / prices[0]
                
                # Volume features
                if len(self.price_windows['RTX']) > 5:
                    volumes = [dp.get('volume', 0) for dp in list(self.price_windows['RTX'])[-5:]]
                    avg_volume = np.mean(volumes)
                    current_volume = volumes[-1]
                    features['volume_surge'] = current_volume / avg_volume if avg_volume > 0 else 1.0
                
                # Time-based features
                now = datetime.now()
                features['seconds_in_minute'] = now.second
                features['minutes_since_open'] = self.get_minutes_since_market_open(now)
                features['is_power_hour'] = 1.0 if 15 <= now.hour <= 16 else 0.0
                
        except Exception as e:
            logger.error(f"❌ Real-time specific features error: {e}")
        
        return features
    
    def get_minutes_since_market_open(self, timestamp: datetime) -> float:
        """Calculate minutes since market open"""
        # Market opens at 9:30 AM
        market_open = timestamp.replace(hour=9, minute=30, second=0, microsecond=0)
        
        if timestamp < market_open:
            return 0.0  # Before market open
        
        delta = timestamp - market_open
        return delta.total_seconds() / 60.0
    
    def calculate_confidence_score(self, features: Dict[str, float]) -> float:
        """Calculate confidence score for the features"""
        try:
            # Base confidence on data completeness and freshness
            base_confidence = 0.7
            
            # Boost confidence if we have all key features
            key_features = ['confidence', 'expected_move', 'vix_level', 'spy_return_1d']
            available_key_features = sum(1 for feat in key_features if feat in features)
            feature_completeness = available_key_features / len(key_features)
            
            # Adjust for data freshness
            if self.last_calculation:
                age_minutes = (datetime.now() - self.last_calculation).total_seconds() / 60
                freshness_factor = max(0.5, 1.0 - age_minutes / 60)  # Decay over 1 hour
            else:
                freshness_factor = 1.0
            
            confidence = base_confidence * feature_completeness * freshness_factor
            return min(1.0, max(0.1, confidence))  # Clamp between 0.1 and 1.0
            
        except Exception as e:
            logger.error(f"❌ Confidence calculation error: {e}")
            return 0.5
    
    def calculate_data_completeness(self) -> float:
        """Calculate how complete our data is"""
        try:
            total_symbols = len(self.symbols)
            symbols_with_data = sum(1 for symbol in self.symbols if self.price_windows[symbol])
            
            return symbols_with_data / total_symbols
            
        except Exception as e:
            logger.error(f"❌ Data completeness calculation error: {e}")
            return 0.0
    
    def get_latest_features(self) -> Optional[RealTimeFeatures]:
        """Get the most recent feature calculation"""
        with self.data_lock:
            return self.feature_cache.get('latest')
    
    def get_feature_performance_stats(self) -> Dict:
        """Get performance statistics for feature calculation"""
        with self.data_lock:
            stats = {
                'total_updates': self.feature_update_count,
                'avg_calculation_time_ms': np.mean(self.calculation_times) if self.calculation_times else 0,
                'max_calculation_time_ms': max(self.calculation_times) if self.calculation_times else 0,
                'min_calculation_time_ms': min(self.calculation_times) if self.calculation_times else 0,
                'data_points_cached': sum(len(window) for window in self.price_windows.values()),
                'last_update': self.last_calculation
            }
        
        return stats
    
    async def simulate_market_data_stream(self, duration_minutes: int = 2):
        """Simulate real-time market data for testing"""
        logger.info(f"🎮 Simulating market data stream for {duration_minutes} minutes...")
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        while datetime.now() < end_time:
            try:
                # Fetch real market data
                tickers = yf.Tickers(' '.join(self.symbols))
                
                for symbol in self.symbols:
                    try:
                        ticker = tickers.tickers[symbol]
                        hist = ticker.history(period='1d', interval='1m')
                        
                        if not hist.empty:
                            latest = hist.iloc[-1]
                            
                            await self.update_market_data(
                                symbol=symbol,
                                price=float(latest['Close']),
                                volume=int(latest['Volume']),
                                timestamp=datetime.now(),
                                high=float(latest['High']),
                                low=float(latest['Low']),
                                open=float(latest['Open'])
                            )
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error updating {symbol}: {e}")
                
                # Wait before next update
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"❌ Simulation error: {e}")
                await asyncio.sleep(10)
        
        logger.success("✅ Market data simulation completed")

def test_realtime_feature_engine():
    """Test the real-time feature engine"""
    logger.info("🧪 Testing real-time feature engine...")
    
    async def run_test():
        engine = RealTimeFeatureEngine()
        
        # Simulate market data stream
        await engine.simulate_market_data_stream(duration_minutes=1)
        
        # Get final results
        latest_features = engine.get_latest_features()
        performance_stats = engine.get_feature_performance_stats()
        
        if latest_features:
            logger.success(f"✅ Generated {len(latest_features.features)} features")
            logger.info(f"📊 Confidence: {latest_features.confidence:.3f}")
            logger.info(f"📊 Data completeness: {latest_features.data_completeness:.3f}")
            logger.info(f"⚡ Calculation time: {latest_features.calculation_time_ms:.1f}ms")
        else:
            logger.warning("⚠️ No features generated")
        
        logger.info(f"📈 Performance stats: {performance_stats}")
    
    # Run test
    asyncio.run(run_test())

if __name__ == "__main__":
    test_realtime_feature_engine()
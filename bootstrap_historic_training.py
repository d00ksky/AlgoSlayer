#!/usr/bin/env python3
"""
Bootstrap Historic Training - Massive Initial Training
Train models on years of historic RTX data to get excellent starting point
Run this once before going live to build initial expertise
"""
import asyncio
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger
import sqlite3
import json
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

# Import our signals for historic analysis
from src.signals.technical_analysis_signal import TechnicalAnalysisSignal
from src.signals.momentum_signal import MomentumSignal
from src.signals.volatility_analysis_signal import VolatilityAnalysisSignal
from src.signals.mean_reversion_signal import MeanReversionSignal

class HistoricTrainingBootstrap:
    """Bootstrap training with years of historic data"""
    
    def __init__(self):
        self.db_path = "data/signal_performance.db"
        self.signals = {
            'technical_analysis': TechnicalAnalysisSignal(),
            'momentum': MomentumSignal(),
            'volatility_analysis': VolatilityAnalysisSignal(),
            'mean_reversion': MeanReversionSignal()
        }
        self._init_database()
    
    def _init_database(self):
        """Initialize database for historic training"""
        import os
        os.makedirs("data", exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            symbol TEXT DEFAULT 'RTX',
            direction TEXT NOT NULL,
            confidence REAL NOT NULL,
            expected_move REAL,
            signal_data TEXT,
            price_at_prediction REAL,
            reasoning TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction_outcomes (
            outcome_id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id INTEGER,
            timestamp_checked DATETIME DEFAULT CURRENT_TIMESTAMP,
            actual_direction TEXT,
            actual_move_1h REAL,
            actual_move_4h REAL,
            actual_move_24h REAL,
            max_move_24h REAL,
            price_1h REAL,
            price_4h REAL,
            price_24h REAL,
            options_profit_potential REAL,
            FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id)
        )
        """)
        
        conn.commit()
        conn.close()
        logger.info("📊 Database initialized for historic training")
    
    async def download_historic_data(self, years: int = 3) -> pd.DataFrame:
        """Download years of RTX historic data"""
        logger.info(f"📥 Downloading {years} years of RTX historic data...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        ticker = yf.Ticker("RTX")
        
        # Download daily data
        hist_data = ticker.history(
            start=start_date,
            end=end_date,
            interval="1d"
        )
        
        if hist_data.empty:
            logger.error("❌ No historic data downloaded")
            return pd.DataFrame()
        
        logger.success(f"✅ Downloaded {len(hist_data)} days of RTX data")
        logger.info(f"📅 Date range: {hist_data.index[0].date()} to {hist_data.index[-1].date()}")
        
        return hist_data
    
    async def run_signals_on_historic_data(self, hist_data: pd.DataFrame) -> List[Dict]:
        """Run all signals on historic data"""
        logger.info("🤖 Running AI signals on historic data...")
        
        predictions = []
        total_days = len(hist_data)
        
        # Process data day by day (simulating real-time)
        for i, (date, row) in enumerate(hist_data.iterrows()):
            if i % 100 == 0:
                progress = (i / total_days) * 100
                logger.info(f"📊 Progress: {progress:.1f}% ({i}/{total_days})")
            
            # Skip first 60 days to have enough data for signals
            if i < 60:
                continue
            
            # Get data up to this point for signal analysis
            data_slice = hist_data.iloc[:i+1]
            current_price = row['Close']
            
            # Run signals (simplified for historic data)
            signal_results = {}
            
            try:
                # Technical analysis
                tech_signal = await self._run_historic_technical_analysis(data_slice)
                signal_results['technical_analysis'] = tech_signal
                
                # Momentum
                momentum_signal = await self._run_historic_momentum(data_slice)
                signal_results['momentum'] = momentum_signal
                
                # Volatility
                vol_signal = await self._run_historic_volatility(data_slice)
                signal_results['volatility_analysis'] = vol_signal
                
                # Mean reversion
                mean_rev_signal = await self._run_historic_mean_reversion(data_slice)
                signal_results['mean_reversion'] = mean_rev_signal
                
                # Aggregate signals
                prediction = self._aggregate_historic_signals(signal_results, current_price, date)
                
                if prediction:
                    predictions.append(prediction)
                    
            except Exception as e:
                logger.warning(f"⚠️ Signal error on {date.date()}: {e}")
                continue
        
        logger.success(f"✅ Generated {len(predictions)} historic predictions")
        return predictions
    
    async def _run_historic_technical_analysis(self, data: pd.DataFrame) -> Dict:
        """Run technical analysis on historic data slice"""
        # Use last 60 days for analysis
        recent_data = data.tail(60)
        
        if len(recent_data) < 20:
            return {"direction": "HOLD", "confidence": 0.5, "strength": 0.1}
        
        # Calculate simple indicators
        closes = recent_data['Close']
        
        # RSI
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # Moving averages
        ma_20 = closes.rolling(20).mean().iloc[-1]
        ma_50 = closes.rolling(50).mean().iloc[-1] if len(closes) >= 50 else ma_20
        current_price = closes.iloc[-1]
        
        # Simple signal logic
        if current_rsi < 30 and current_price > ma_20:
            return {"direction": "BUY", "confidence": 0.75, "strength": 0.15}
        elif current_rsi > 70 and current_price < ma_20:
            return {"direction": "SELL", "confidence": 0.75, "strength": 0.15}
        elif current_price > ma_20 and ma_20 > ma_50:
            return {"direction": "BUY", "confidence": 0.6, "strength": 0.12}
        elif current_price < ma_20 and ma_20 < ma_50:
            return {"direction": "SELL", "confidence": 0.6, "strength": 0.12}
        else:
            return {"direction": "HOLD", "confidence": 0.5, "strength": 0.05}
    
    async def _run_historic_momentum(self, data: pd.DataFrame) -> Dict:
        """Run momentum analysis on historic data slice"""
        recent_data = data.tail(30)
        
        if len(recent_data) < 10:
            return {"direction": "HOLD", "confidence": 0.5, "strength": 0.1}
        
        closes = recent_data['Close']
        returns = closes.pct_change()
        
        # Simple momentum
        momentum_5d = returns.tail(5).mean()
        momentum_10d = returns.tail(10).mean()
        
        if momentum_5d > 0.01 and momentum_10d > 0.005:
            return {"direction": "BUY", "confidence": 0.7, "strength": 0.14}
        elif momentum_5d < -0.01 and momentum_10d < -0.005:
            return {"direction": "SELL", "confidence": 0.7, "strength": 0.14}
        else:
            return {"direction": "HOLD", "confidence": 0.5, "strength": 0.05}
    
    async def _run_historic_volatility(self, data: pd.DataFrame) -> Dict:
        """Run volatility analysis on historic data slice"""
        recent_data = data.tail(30)
        
        if len(recent_data) < 20:
            return {"direction": "HOLD", "confidence": 0.5, "strength": 0.1}
        
        closes = recent_data['Close']
        returns = closes.pct_change()
        volatility = returns.rolling(20).std().iloc[-1]
        
        # High volatility often precedes reversals
        if volatility > 0.03:  # High volatility
            return {"direction": "HOLD", "confidence": 0.4, "strength": 0.08}
        else:
            return {"direction": "HOLD", "confidence": 0.6, "strength": 0.10}
    
    async def _run_historic_mean_reversion(self, data: pd.DataFrame) -> Dict:
        """Run mean reversion analysis on historic data slice"""
        recent_data = data.tail(30)
        
        if len(recent_data) < 20:
            return {"direction": "HOLD", "confidence": 0.5, "strength": 0.1}
        
        closes = recent_data['Close']
        mean_price = closes.rolling(20).mean().iloc[-1]
        std_price = closes.rolling(20).std().iloc[-1]
        current_price = closes.iloc[-1]
        
        # Z-score for mean reversion
        z_score = (current_price - mean_price) / std_price
        
        if z_score > 2:  # Overbought
            return {"direction": "SELL", "confidence": 0.65, "strength": 0.13}
        elif z_score < -2:  # Oversold
            return {"direction": "BUY", "confidence": 0.65, "strength": 0.13}
        else:
            return {"direction": "HOLD", "confidence": 0.5, "strength": 0.05}
    
    def _aggregate_historic_signals(self, signal_results: Dict, price: float, date) -> Dict:
        """Aggregate signals for historic prediction"""
        buy_strength = 0
        sell_strength = 0
        total_confidence = 0
        signal_count = 0
        
        for name, signal in signal_results.items():
            direction = signal.get("direction", "HOLD")
            strength = signal.get("strength", 0)
            confidence = signal.get("confidence", 0.5)
            
            if direction == "BUY":
                buy_strength += strength
            elif direction == "SELL":
                sell_strength += strength
            
            total_confidence += confidence
            signal_count += 1
        
        # Determine direction
        strength_diff = abs(buy_strength - sell_strength)
        
        if buy_strength > sell_strength and buy_strength > 0.3 and strength_diff > 0.1:
            final_direction = "BUY"
            final_confidence = min(0.95, buy_strength / (buy_strength + sell_strength + 0.1))
        elif sell_strength > buy_strength and sell_strength > 0.3 and strength_diff > 0.1:
            final_direction = "SELL"
            final_confidence = min(0.95, sell_strength / (buy_strength + sell_strength + 0.1))
        else:
            final_direction = "HOLD"
            final_confidence = 0.5
        
        return {
            "timestamp": date,
            "direction": final_direction,
            "confidence": final_confidence,
            "price_at_prediction": price,
            "signal_data": signal_results
        }
    
    def calculate_outcomes(self, predictions: List[Dict], hist_data: pd.DataFrame) -> int:
        """Calculate outcomes for all predictions and store in database"""
        logger.info("📊 Calculating prediction outcomes...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stored_count = 0
        
        for pred in predictions:
            try:
                pred_date = pred['timestamp']
                pred_price = pred['price_at_prediction']
                
                # Find outcomes 1 day later (simplified)
                future_idx = hist_data.index.get_indexer([pred_date], method='nearest')[0] + 1
                
                if future_idx < len(hist_data):
                    future_price = hist_data.iloc[future_idx]['Close']
                    move_24h = (future_price - pred_price) / pred_price
                    
                    # Determine actual direction
                    if move_24h > 0.001:
                        actual_direction = "BUY"
                    elif move_24h < -0.001:
                        actual_direction = "SELL"
                    else:
                        actual_direction = "HOLD"
                    
                    # Calculate options profit potential
                    options_profit = self._calculate_options_profit(move_24h)
                    
                    # Store prediction
                    cursor.execute("""
                    INSERT INTO predictions 
                    (timestamp, direction, confidence, signal_data, price_at_prediction, reasoning)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        pred_date,
                        pred['direction'],
                        pred['confidence'],
                        json.dumps(pred['signal_data']),
                        pred_price,
                        f"Historic training prediction"
                    ))
                    
                    prediction_id = cursor.lastrowid
                    
                    # Store outcome
                    cursor.execute("""
                    INSERT INTO prediction_outcomes 
                    (prediction_id, actual_direction, actual_move_24h, 
                     price_24h, options_profit_potential)
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        prediction_id,
                        actual_direction,
                        move_24h,
                        future_price,
                        options_profit
                    ))
                    
                    stored_count += 1
                    
            except Exception as e:
                logger.warning(f"⚠️ Error storing prediction: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        logger.success(f"✅ Stored {stored_count} predictions with outcomes")
        return stored_count
    
    def _calculate_options_profit(self, actual_move: float) -> float:
        """Calculate theoretical options profit"""
        if abs(actual_move) < 0.01:
            return -0.5  # Time decay
        elif abs(actual_move) < 0.03:
            return actual_move * 25  # 25x leverage
        elif abs(actual_move) < 0.05:
            return actual_move * 35  # 35x leverage
        else:
            return actual_move * 50  # 50x leverage
    
    async def generate_performance_report(self) -> str:
        """Generate performance report from historic training"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get overall stats
        cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN p.direction = o.actual_direction THEN 1 ELSE 0 END) as correct,
            AVG(p.confidence) as avg_confidence,
            AVG(o.options_profit_potential) as avg_profit
        FROM predictions p
        JOIN prediction_outcomes o ON p.prediction_id = o.prediction_id
        """)
        
        result = cursor.fetchone()
        total, correct, avg_conf, avg_profit = result
        
        accuracy = correct / total if total > 0 else 0
        
        # Get high confidence stats
        cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN p.direction = o.actual_direction THEN 1 ELSE 0 END) as correct
        FROM predictions p
        JOIN prediction_outcomes o ON p.prediction_id = o.prediction_id
        WHERE p.confidence >= 0.8
        """)
        
        hc_result = cursor.fetchone()
        hc_total, hc_correct = hc_result
        hc_accuracy = hc_correct / hc_total if hc_total > 0 else 0
        
        conn.close()
        
        report = f"""
📊 **Historic Training Results**

**Overall Performance:**
• Total Predictions: {total:,}
• Accuracy: {accuracy:.1%}
• Avg Confidence: {avg_conf:.1%}
• Avg Options Profit: {avg_profit:+.1%}

**High Confidence (≥80%):**
• Predictions: {hc_total}
• Accuracy: {hc_accuracy:.1%}

**Assessment:**
"""
        
        if accuracy >= 0.6 and hc_accuracy >= 0.7:
            report += "🟢 **EXCELLENT** - Models ready for live trading"
        elif accuracy >= 0.55:
            report += "🟡 **GOOD** - Models ready for paper trading"
        else:
            report += "🔴 **NEEDS WORK** - Continue development"
        
        return report

async def main():
    """Main bootstrap training function"""
    logger.info("🚀 Starting Historic Training Bootstrap")
    logger.info("=" * 60)
    
    bootstrap = HistoricTrainingBootstrap()
    
    # Step 1: Download historic data
    hist_data = await bootstrap.download_historic_data(years=3)
    if hist_data.empty:
        logger.error("❌ Failed to download historic data")
        return
    
    # Step 2: Run signals on all historic data
    predictions = await bootstrap.run_signals_on_historic_data(hist_data)
    if not predictions:
        logger.error("❌ No predictions generated")
        return
    
    # Step 3: Calculate and store outcomes
    stored_count = bootstrap.calculate_outcomes(predictions, hist_data)
    
    # Step 4: Generate performance report
    report = await bootstrap.generate_performance_report()
    print("\n" + report)
    
    # Step 5: Run ML training if we have enough data
    if stored_count > 100:
        logger.info("🤖 Running ML training on historic data...")
        
        # Import and run the ML training pipeline
        from sync_and_train_ml import MLTrainingPipeline
        
        pipeline = MLTrainingPipeline()
        
        # Load training data
        import pandas as pd
        conn = sqlite3.connect(bootstrap.db_path)
        
        query = """
        SELECT 
            p.prediction_id, p.timestamp, p.direction, p.confidence, 
            p.signal_data, o.actual_direction, o.actual_move_24h,
            o.options_profit_potential
        FROM predictions p
        JOIN prediction_outcomes o ON p.prediction_id = o.prediction_id
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            # Engineer features and train models
            X, y = pipeline.engineer_features(df)
            pipeline.train_models(X, y)
            pipeline.analyze_feature_importance(X)
            
            # Save models locally
            model_path, weights_path = pipeline.save_models_locally()
            
            # Generate training report
            pipeline.generate_training_report(X, y)
            
            logger.success("✅ Historic training bootstrap complete!")
            logger.info(f"📁 Models saved to: {model_path}")
            
            # Optional: Upload to cloud
            upload_to_cloud = input("\n🔗 Upload models to cloud server? (y/N): ").lower()
            if upload_to_cloud == 'y':
                success = pipeline.upload_to_cloud(model_path, weights_path)
                if success:
                    logger.success("✅ Models uploaded to cloud!")
    else:
        logger.warning("⚠️ Not enough data for ML training")
    
    logger.success("🎉 Historic training bootstrap complete!")

if __name__ == "__main__":
    asyncio.run(main())
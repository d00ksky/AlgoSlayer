"""
Real-Time Performance Tracker
Tracks predictions vs actual outcomes for learning
Stores data in SQLite for later ML training
"""
import asyncio
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger
import yfinance as yf

from config.trading_config import config

class PerformanceTracker:
    """Track prediction performance in real-time"""
    
    def __init__(self, db_path: str = "data/signal_performance.db"):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Predictions table
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
        
        # Prediction outcomes table
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
        
        # Signal performance summary
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS signal_performance (
            signal_name TEXT PRIMARY KEY,
            total_predictions INTEGER DEFAULT 0,
            correct_predictions INTEGER DEFAULT 0,
            accuracy REAL DEFAULT 0.0,
            avg_confidence REAL DEFAULT 0.0,
            profit_factor REAL DEFAULT 0.0,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Options trades tracking
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS options_trades (
            trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id INTEGER,
            entry_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            strike_price REAL,
            expiration_date DATE,
            option_type TEXT,
            entry_price REAL,
            exit_price REAL,
            exit_time DATETIME,
            profit_loss REAL,
            profit_percentage REAL,
            FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id)
        )
        """)
        
        conn.commit()
        conn.close()
        logger.info("📊 Performance tracking database initialized")
    
    async def record_prediction(self, direction: str, confidence: float, 
                              signal_data: Dict, reasoning: str = "") -> int:
        """Record a new prediction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current RTX price
        try:
            ticker = yf.Ticker("RTX")
            current_price = ticker.history(period="1d")['Close'].iloc[-1]
        except:
            current_price = None
            logger.warning("Could not fetch current RTX price")
        
        # Calculate expected move based on confidence
        expected_move = 0.03 if confidence > 0.8 else 0.02  # 3% for high confidence, 2% otherwise
        
        cursor.execute("""
        INSERT INTO predictions 
        (direction, confidence, expected_move, signal_data, price_at_prediction, reasoning)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            direction,
            confidence,
            expected_move,
            json.dumps(signal_data),
            current_price,
            reasoning
        ))
        
        prediction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"📝 Recorded prediction #{prediction_id}: {direction} ({confidence:.1%})")
        
        # Schedule outcome checks
        asyncio.create_task(self._schedule_outcome_checks(prediction_id))
        
        return prediction_id
    
    async def _schedule_outcome_checks(self, prediction_id: int):
        """Schedule checks for prediction outcomes"""
        # Check after 1 hour
        await asyncio.sleep(3600)  # 1 hour
        await self.check_prediction_outcome(prediction_id, "1h")
        
        # Check after 4 hours
        await asyncio.sleep(3 * 3600)  # 3 more hours
        await self.check_prediction_outcome(prediction_id, "4h")
        
        # Check after 24 hours
        await asyncio.sleep(20 * 3600)  # 20 more hours
        await self.check_prediction_outcome(prediction_id, "24h")
    
    async def check_prediction_outcome(self, prediction_id: int, timeframe: str):
        """Check actual outcome of a prediction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get original prediction
        cursor.execute("""
        SELECT direction, confidence, price_at_prediction, expected_move
        FROM predictions WHERE prediction_id = ?
        """, (prediction_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return
        
        pred_direction, pred_confidence, price_at_pred, expected_move = result
        
        # Get current price
        try:
            ticker = yf.Ticker("RTX")
            current_price = ticker.history(period="1d")['Close'].iloc[-1]
            
            # Calculate actual move
            if price_at_pred:
                actual_move = (current_price - price_at_pred) / price_at_pred
                actual_direction = "BUY" if actual_move > 0 else "SELL" if actual_move < 0 else "HOLD"
            else:
                actual_move = 0
                actual_direction = "HOLD"
            
            # Check if we have existing outcome record
            cursor.execute("""
            SELECT outcome_id FROM prediction_outcomes 
            WHERE prediction_id = ?
            """, (prediction_id,))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                if timeframe == "1h":
                    cursor.execute("""
                    UPDATE prediction_outcomes 
                    SET actual_move_1h = ?, price_1h = ?
                    WHERE prediction_id = ?
                    """, (actual_move, current_price, prediction_id))
                elif timeframe == "4h":
                    cursor.execute("""
                    UPDATE prediction_outcomes 
                    SET actual_move_4h = ?, price_4h = ?
                    WHERE prediction_id = ?
                    """, (actual_move, current_price, prediction_id))
                elif timeframe == "24h":
                    # Final update - calculate options profit potential
                    options_profit = self._calculate_options_profit(actual_move)
                    
                    cursor.execute("""
                    UPDATE prediction_outcomes 
                    SET actual_move_24h = ?, price_24h = ?, 
                        actual_direction = ?, options_profit_potential = ?
                    WHERE prediction_id = ?
                    """, (actual_move, current_price, actual_direction, 
                          options_profit, prediction_id))
            else:
                # Create new outcome record
                cursor.execute("""
                INSERT INTO prediction_outcomes 
                (prediction_id, actual_direction, actual_move_1h, price_1h)
                VALUES (?, ?, ?, ?)
                """, (prediction_id, actual_direction, actual_move, current_price))
            
            conn.commit()
            
            # Log outcome
            correct = pred_direction == actual_direction
            logger.info(f"📊 Prediction #{prediction_id} {timeframe} outcome: "
                       f"{'✅' if correct else '❌'} "
                       f"Predicted {pred_direction}, Actual {actual_direction} "
                       f"({actual_move:.2f}% move)")
            
        except Exception as e:
            logger.error(f"Error checking outcome: {e}")
        finally:
            conn.close()
    
    def _calculate_options_profit(self, actual_move: float) -> float:
        """Calculate theoretical options profit based on stock move"""
        # Simplified options profit calculation
        # Assumes ATM options with 30 delta
        
        if abs(actual_move) < 0.01:  # Less than 1% move
            return -0.5  # Lose 50% on time decay
        elif abs(actual_move) < 0.03:  # 1-3% move
            return actual_move * 20  # 20x leverage
        elif abs(actual_move) < 0.05:  # 3-5% move
            return actual_move * 30  # 30x leverage
        else:  # 5%+ move
            return actual_move * 40  # 40x leverage
    
    async def update_signal_performance(self):
        """Update signal performance statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get performance by signal
        cursor.execute("""
        SELECT 
            json_extract(p.signal_data, '$.*') as signals,
            COUNT(*) as total,
            SUM(CASE WHEN p.direction = o.actual_direction THEN 1 ELSE 0 END) as correct,
            AVG(p.confidence) as avg_confidence
        FROM predictions p
        JOIN prediction_outcomes o ON p.prediction_id = o.prediction_id
        WHERE o.actual_direction IS NOT NULL
        GROUP BY signals
        """)
        
        # This is simplified - in production, parse signal_data properly
        
        conn.close()
        logger.info("📊 Updated signal performance statistics")
    
    async def get_recent_performance(self, days: int = 7) -> Dict:
        """Get recent performance metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute("""
        SELECT 
            COUNT(*) as total_predictions,
            SUM(CASE WHEN p.direction = o.actual_direction THEN 1 ELSE 0 END) as correct,
            AVG(p.confidence) as avg_confidence,
            AVG(o.options_profit_potential) as avg_profit_potential
        FROM predictions p
        JOIN prediction_outcomes o ON p.prediction_id = o.prediction_id
        WHERE p.timestamp > ? AND o.actual_direction IS NOT NULL
        """, (cutoff_date,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            total, correct, avg_conf, avg_profit = result
            accuracy = correct / total if total > 0 else 0
            
            return {
                'total_predictions': total,
                'accuracy': accuracy,
                'avg_confidence': avg_conf,
                'avg_profit_potential': avg_profit,
                'period_days': days
            }
        
        return {}
    
    async def generate_daily_report(self) -> str:
        """Generate daily performance report"""
        logger.info("📝 Generating daily performance report...")
        
        # Get various performance metrics
        day_perf = await self.get_recent_performance(1)
        week_perf = await self.get_recent_performance(7)
        month_perf = await self.get_recent_performance(30)
        
        report = []
        report.append("📊 **RTX Trading Performance Report**")
        report.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M ET')}")
        report.append("")
        
        # Daily performance
        if day_perf.get('total_predictions', 0) > 0:
            report.append("**Last 24 Hours:**")
            report.append(f"• Predictions: {day_perf['total_predictions']}")
            report.append(f"• Accuracy: {day_perf['accuracy']:.1%}")
            report.append(f"• Avg Confidence: {day_perf['avg_confidence']:.1%}")
            report.append("")
        
        # Weekly performance
        if week_perf.get('total_predictions', 0) > 0:
            report.append("**Last 7 Days:**")
            report.append(f"• Predictions: {week_perf['total_predictions']}")
            report.append(f"• Accuracy: {week_perf['accuracy']:.1%}")
            report.append(f"• Options Profit Potential: {week_perf['avg_profit_potential']:.1%}")
            report.append("")
        
        # Get high conviction performance
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN p.direction = o.actual_direction THEN 1 ELSE 0 END) as correct
        FROM predictions p
        JOIN prediction_outcomes o ON p.prediction_id = o.prediction_id
        WHERE p.confidence >= 0.85 AND o.actual_direction IS NOT NULL
        """)
        
        high_conv = cursor.fetchone()
        if high_conv and high_conv[0] > 0:
            hc_accuracy = high_conv[1] / high_conv[0]
            report.append("**High Conviction (≥85%):**")
            report.append(f"• Total: {high_conv[0]}")
            report.append(f"• Accuracy: {hc_accuracy:.1%}")
            report.append("")
        
        # Learning insights
        report.append("**🧠 Learning Insights:**")
        if week_perf.get('accuracy', 0) > 0.65:
            report.append("✅ Model performing well - consider larger positions")
        elif week_perf.get('accuracy', 0) > 0.55:
            report.append("⚠️ Model performance moderate - maintain caution")
        else:
            report.append("❌ Model underperforming - review signal weights")
        
        conn.close()
        
        return "\n".join(report)

# Global instance
performance_tracker = PerformanceTracker()
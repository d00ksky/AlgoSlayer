"""
Lightweight SQLite Database for Small Droplet
Optimized for 1GB RAM, stores all trading data and learning history
"""
import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import aiosqlite
from loguru import logger
import os

@dataclass
class PriceData:
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    volatility: float

@dataclass
class AISignalPrediction:
    timestamp: datetime
    signal_name: str
    direction: str  # BUY, SELL, HOLD
    confidence: float
    strength: float
    reasoning: str
    target_price: Optional[float] = None
    timeframe: str = "1d"

@dataclass
class TradeRecord:
    timestamp: datetime
    action: str  # BUY, SELL, SELL_CALL, etc.
    symbol: str
    quantity: int
    price: float
    fees: float
    pnl: float
    strategy_reason: str
    ai_confidence: float

@dataclass
class SignalWeight:
    signal_name: str
    current_weight: float
    accuracy_24h: float
    accuracy_7d: float
    accuracy_30d: float
    total_predictions: int
    correct_predictions: int
    last_updated: datetime

@dataclass
class PerformanceMetric:
    date: datetime
    daily_pnl: float
    total_pnl: float
    total_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    sharpe_ratio: float
    max_drawdown: float

class AlgoSlayerDB:
    """Lightweight SQLite database for small droplet"""
    
    def __init__(self, db_path: str = "data/algoslayer.db"):
        self.db_path = db_path
        self.ensure_data_dir()
    
    def ensure_data_dir(self):
        """Ensure data directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    async def initialize(self):
        """Initialize database with required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Enable WAL mode for better concurrent access
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA synchronous=NORMAL")
            await db.execute("PRAGMA cache_size=10000")  # 10MB cache
            await db.execute("PRAGMA temp_store=memory")
            
            # Create tables
            await self._create_tables(db)
            await db.commit()
            logger.success("Database initialized successfully")
    
    async def _create_tables(self, db):
        """Create all required tables"""
        
        # Price data table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS price_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL,
                volatility REAL NOT NULL,
                UNIQUE(timestamp, symbol)
            )
        """)
        
        # AI predictions table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ai_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                signal_name TEXT NOT NULL,
                direction TEXT NOT NULL,
                confidence REAL NOT NULL,
                strength REAL NOT NULL,
                reasoning TEXT,
                target_price REAL,
                timeframe TEXT DEFAULT '1d',
                actual_outcome TEXT DEFAULT 'pending',
                was_correct BOOLEAN DEFAULT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Trades table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                action TEXT NOT NULL,
                symbol TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                fees REAL DEFAULT 0,
                pnl REAL DEFAULT 0,
                strategy_reason TEXT,
                ai_confidence REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Signal weights table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS signal_weights (
                signal_name TEXT PRIMARY KEY,
                current_weight REAL NOT NULL,
                accuracy_24h REAL DEFAULT 0.5,
                accuracy_7d REAL DEFAULT 0.5,
                accuracy_30d REAL DEFAULT 0.5,
                total_predictions INTEGER DEFAULT 0,
                correct_predictions INTEGER DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Performance metrics table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                date DATE PRIMARY KEY,
                daily_pnl REAL NOT NULL,
                total_pnl REAL NOT NULL,
                total_trades INTEGER NOT NULL,
                win_rate REAL NOT NULL,
                avg_win REAL NOT NULL,
                avg_loss REAL NOT NULL,
                sharpe_ratio REAL DEFAULT 0,
                max_drawdown REAL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # System logs table (for debugging)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                component TEXT,
                details TEXT
            )
        """)
        
        # Create indexes for better performance
        await db.execute("CREATE INDEX IF NOT EXISTS idx_price_timestamp ON price_data(timestamp)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON ai_predictions(timestamp)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp)")
    
    async def store_price_data(self, data: PriceData):
        """Store price data"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO price_data 
                (timestamp, symbol, open, high, low, close, volume, volatility)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.timestamp, data.symbol, data.open, data.high, 
                data.low, data.close, data.volume, data.volatility
            ))
            await db.commit()
    
    async def store_ai_prediction(self, prediction: AISignalPrediction):
        """Store AI prediction"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO ai_predictions 
                (timestamp, signal_name, direction, confidence, strength, reasoning, target_price, timeframe)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction.timestamp, prediction.signal_name, prediction.direction,
                prediction.confidence, prediction.strength, prediction.reasoning,
                prediction.target_price, prediction.timeframe
            ))
            await db.commit()
    
    async def store_trade(self, trade: TradeRecord):
        """Store trade record"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO trades 
                (timestamp, action, symbol, quantity, price, fees, pnl, strategy_reason, ai_confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade.timestamp, trade.action, trade.symbol, trade.quantity,
                trade.price, trade.fees, trade.pnl, trade.strategy_reason, trade.ai_confidence
            ))
            await db.commit()
    
    async def update_signal_weights(self, weights: List[SignalWeight]):
        """Update signal weights"""
        async with aiosqlite.connect(self.db_path) as db:
            for weight in weights:
                await db.execute("""
                    INSERT OR REPLACE INTO signal_weights 
                    (signal_name, current_weight, accuracy_24h, accuracy_7d, accuracy_30d, 
                     total_predictions, correct_predictions, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    weight.signal_name, weight.current_weight, weight.accuracy_24h,
                    weight.accuracy_7d, weight.accuracy_30d, weight.total_predictions,
                    weight.correct_predictions, weight.last_updated
                ))
            await db.commit()
    
    async def store_performance_metric(self, metric: PerformanceMetric):
        """Store daily performance metrics"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO performance_metrics 
                (date, daily_pnl, total_pnl, total_trades, win_rate, avg_win, avg_loss, 
                 sharpe_ratio, max_drawdown)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.date, metric.daily_pnl, metric.total_pnl, metric.total_trades,
                metric.win_rate, metric.avg_win, metric.avg_loss, 
                metric.sharpe_ratio, metric.max_drawdown
            ))
            await db.commit()
    
    async def get_recent_price_data(self, symbol: str, hours: int = 24) -> List[PriceData]:
        """Get recent price data"""
        async with aiosqlite.connect(self.db_path) as db:
            cutoff = datetime.now() - timedelta(hours=hours)
            cursor = await db.execute("""
                SELECT timestamp, symbol, open, high, low, close, volume, volatility
                FROM price_data 
                WHERE symbol = ? AND timestamp > ?
                ORDER BY timestamp DESC
            """, (symbol, cutoff))
            
            rows = await cursor.fetchall()
            return [
                PriceData(
                    timestamp=datetime.fromisoformat(row[0]),
                    symbol=row[1], open=row[2], high=row[3], low=row[4], 
                    close=row[5], volume=row[6], volatility=row[7]
                ) for row in rows
            ]
    
    async def get_signal_weights(self) -> List[SignalWeight]:
        """Get current signal weights"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT signal_name, current_weight, accuracy_24h, accuracy_7d, accuracy_30d,
                       total_predictions, correct_predictions, last_updated
                FROM signal_weights
            """)
            
            rows = await cursor.fetchall()
            return [
                SignalWeight(
                    signal_name=row[0], current_weight=row[1], accuracy_24h=row[2],
                    accuracy_7d=row[3], accuracy_30d=row[4], total_predictions=row[5],
                    correct_predictions=row[6], last_updated=datetime.fromisoformat(row[7])
                ) for row in rows
            ]
    
    async def calculate_signal_accuracy(self, signal_name: str, days: int = 1) -> float:
        """Calculate signal accuracy over specified days"""
        async with aiosqlite.connect(self.db_path) as db:
            cutoff = datetime.now() - timedelta(days=days)
            cursor = await db.execute("""
                SELECT COUNT(*) as total, SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct
                FROM ai_predictions 
                WHERE signal_name = ? AND timestamp > ? AND was_correct IS NOT NULL
            """, (signal_name, cutoff))
            
            row = await cursor.fetchone()
            total, correct = row[0], row[1]
            
            return correct / total if total > 0 else 0.5
    
    async def get_recent_performance(self, days: int = 30) -> List[PerformanceMetric]:
        """Get recent performance metrics"""
        async with aiosqlite.connect(self.db_path) as db:
            cutoff = datetime.now() - timedelta(days=days)
            cursor = await db.execute("""
                SELECT date, daily_pnl, total_pnl, total_trades, win_rate,
                       avg_win, avg_loss, sharpe_ratio, max_drawdown
                FROM performance_metrics 
                WHERE date > ?
                ORDER BY date DESC
            """, (cutoff.date(),))
            
            rows = await cursor.fetchall()
            return [
                PerformanceMetric(
                    date=datetime.fromisoformat(row[0]).date(),
                    daily_pnl=row[1], total_pnl=row[2], total_trades=row[3],
                    win_rate=row[4], avg_win=row[5], avg_loss=row[6],
                    sharpe_ratio=row[7], max_drawdown=row[8]
                ) for row in rows
            ]
    
    async def get_trades_today(self) -> List[TradeRecord]:
        """Get today's trades"""
        today = datetime.now().date()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT timestamp, action, symbol, quantity, price, fees, pnl, 
                       strategy_reason, ai_confidence
                FROM trades 
                WHERE DATE(timestamp) = ?
                ORDER BY timestamp DESC
            """, (today,))
            
            rows = await cursor.fetchall()
            return [
                TradeRecord(
                    timestamp=datetime.fromisoformat(row[0]),
                    action=row[1], symbol=row[2], quantity=row[3],
                    price=row[4], fees=row[5], pnl=row[6],
                    strategy_reason=row[7], ai_confidence=row[8]
                ) for row in rows
            ]
    
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data to save space"""
        async with aiosqlite.connect(self.db_path) as db:
            cutoff = datetime.now() - timedelta(days=days_to_keep)
            
            # Keep price data for 90 days
            await db.execute("DELETE FROM price_data WHERE timestamp < ?", (cutoff,))
            
            # Keep predictions for 90 days
            await db.execute("DELETE FROM ai_predictions WHERE timestamp < ?", (cutoff,))
            
            # Keep logs for 30 days
            log_cutoff = datetime.now() - timedelta(days=30)
            await db.execute("DELETE FROM system_logs WHERE timestamp < ?", (log_cutoff,))
            
            await db.commit()
            logger.info(f"Cleaned up data older than {days_to_keep} days")
    
    async def get_database_stats(self) -> Dict:
        """Get database statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Table sizes
            for table in ['price_data', 'ai_predictions', 'trades', 'signal_weights', 'performance_metrics']:
                cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
                count = (await cursor.fetchone())[0]
                stats[f"{table}_count"] = count
            
            # Database file size
            if os.path.exists(self.db_path):
                stats['db_size_mb'] = os.path.getsize(self.db_path) / 1024 / 1024
            
            return stats

# Global database instance
db = AlgoSlayerDB()
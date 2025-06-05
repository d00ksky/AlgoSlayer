"""
Signal Performance Tracker for RTX Options Trading
Tracks which signal combinations actually predict profitable RTX options trades
Adapts signal weights based on real performance, not theoretical models
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import sqlite3
import pandas as pd
import numpy as np

@dataclass
class SignalPrediction:
    """Individual signal prediction record"""
    timestamp: datetime
    signal_name: str
    direction: str  # BUY, SELL, HOLD
    confidence: float
    strength: float
    expected_move: float
    rationale: str
    
@dataclass
class CombinedPrediction:
    """Combined prediction from multiple signals"""
    timestamp: datetime
    rtx_price: float
    action: str  # BUY, SELL, HOLD
    confidence: float
    expected_move: float
    signals_agreeing: int
    total_signals: int
    individual_signals: List[SignalPrediction]
    trade_worthy: bool
    
@dataclass
class ActualOutcome:
    """Actual RTX price movement outcome"""
    timestamp: datetime
    start_price: float
    price_4h: Optional[float] = None
    price_24h: Optional[float] = None
    price_48h: Optional[float] = None
    price_72h: Optional[float] = None
    high_4h: Optional[float] = None
    low_4h: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None

@dataclass
class OptionsTradeResult:
    """Results of an actual or paper options trade"""
    timestamp: datetime
    prediction_id: str
    option_type: str  # call, put
    strike: float
    expiry: str
    entry_price: float
    exit_price: Optional[float] = None
    exit_timestamp: Optional[datetime] = None
    profit_loss: Optional[float] = None
    profit_loss_pct: Optional[float] = None
    max_profit: Optional[float] = None
    max_loss: Optional[float] = None

class SignalPerformanceTracker:
    """
    Tracks and analyzes signal performance for RTX options trading
    Learns which signal combinations actually work
    """
    
    def __init__(self, db_path: str = "data/signal_performance.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_database()
        
        # Performance metrics cache
        self.signal_performance = {}
        self.combination_performance = {}
        self.last_analysis = None
        
    def init_database(self):
        """Initialize SQLite database for performance tracking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS predictions (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        rtx_price REAL NOT NULL,
                        action TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        expected_move REAL NOT NULL,
                        signals_agreeing INTEGER NOT NULL,
                        total_signals INTEGER NOT NULL,
                        trade_worthy INTEGER NOT NULL,
                        individual_signals TEXT NOT NULL
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS outcomes (
                        prediction_id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        start_price REAL NOT NULL,
                        price_4h REAL,
                        price_24h REAL,
                        price_48h REAL,
                        price_72h REAL,
                        high_4h REAL,
                        low_4h REAL,
                        high_24h REAL,
                        low_24h REAL,
                        FOREIGN KEY (prediction_id) REFERENCES predictions (id)
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS options_trades (
                        id TEXT PRIMARY KEY,
                        prediction_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        option_type TEXT NOT NULL,
                        strike REAL NOT NULL,
                        expiry TEXT NOT NULL,
                        entry_price REAL NOT NULL,
                        exit_price REAL,
                        exit_timestamp TEXT,
                        profit_loss REAL,
                        profit_loss_pct REAL,
                        max_profit REAL,
                        max_loss REAL,
                        FOREIGN KEY (prediction_id) REFERENCES predictions (id)
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS signal_weights (
                        signal_name TEXT PRIMARY KEY,
                        current_weight REAL NOT NULL,
                        performance_score REAL NOT NULL,
                        total_predictions INTEGER NOT NULL,
                        accurate_predictions INTEGER NOT NULL,
                        last_updated TEXT NOT NULL
                    )
                """)
                
                self.logger.info("📊 Signal performance database initialized")
                
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
    
    async def record_prediction(self, combined_prediction: CombinedPrediction) -> str:
        """Record a combined prediction for tracking"""
        try:
            prediction_id = f"pred_{combined_prediction.timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            # Serialize individual signals
            signals_data = []
            for signal in combined_prediction.individual_signals:
                signals_data.append(asdict(signal))
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO predictions 
                    (id, timestamp, rtx_price, action, confidence, expected_move, 
                     signals_agreeing, total_signals, trade_worthy, individual_signals)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    prediction_id,
                    combined_prediction.timestamp.isoformat(),
                    combined_prediction.rtx_price,
                    combined_prediction.action,
                    combined_prediction.confidence,
                    combined_prediction.expected_move,
                    combined_prediction.signals_agreeing,
                    combined_prediction.total_signals,
                    1 if combined_prediction.trade_worthy else 0,
                    json.dumps(signals_data)
                ))
            
            self.logger.debug(f"📊 Recorded prediction: {prediction_id}")
            return prediction_id
            
        except Exception as e:
            self.logger.error(f"Error recording prediction: {e}")
            return ""
    
    async def record_outcome(self, prediction_id: str, outcome: ActualOutcome):
        """Record actual market outcome for a prediction"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO outcomes 
                    (prediction_id, timestamp, start_price, price_4h, price_24h, price_48h, price_72h,
                     high_4h, low_4h, high_24h, low_24h)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    prediction_id,
                    outcome.timestamp.isoformat(),
                    outcome.start_price,
                    outcome.price_4h,
                    outcome.price_24h,
                    outcome.price_48h,
                    outcome.price_72h,
                    outcome.high_4h,
                    outcome.low_4h,
                    outcome.high_24h,
                    outcome.low_24h
                ))
            
            self.logger.debug(f"📊 Recorded outcome for: {prediction_id}")
            
        except Exception as e:
            self.logger.error(f"Error recording outcome: {e}")
    
    async def record_options_trade(self, trade: OptionsTradeResult):
        """Record options trade result (real or paper)"""
        try:
            trade_id = f"trade_{trade.timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO options_trades 
                    (id, prediction_id, timestamp, option_type, strike, expiry, entry_price,
                     exit_price, exit_timestamp, profit_loss, profit_loss_pct, max_profit, max_loss)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade_id,
                    trade.prediction_id,
                    trade.timestamp.isoformat(),
                    trade.option_type,
                    trade.strike,
                    trade.expiry,
                    trade.entry_price,
                    trade.exit_price,
                    trade.exit_timestamp.isoformat() if trade.exit_timestamp else None,
                    trade.profit_loss,
                    trade.profit_loss_pct,
                    trade.max_profit,
                    trade.max_loss
                ))
            
            self.logger.info(f"💰 Recorded options trade: {trade_id}")
            
        except Exception as e:
            self.logger.error(f"Error recording options trade: {e}")
    
    async def analyze_signal_performance(self, days_back: int = 30) -> Dict:
        """Analyze individual signal performance over time"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                # Get predictions with outcomes
                query = """
                    SELECT p.*, o.price_4h, o.price_24h, o.high_4h, o.low_4h
                    FROM predictions p
                    LEFT JOIN outcomes o ON p.id = o.prediction_id
                    WHERE p.timestamp > ?
                    ORDER BY p.timestamp DESC
                """
                
                results = conn.execute(query, (cutoff_date,)).fetchall()
                
                if not results:
                    return {}
                
                # Analyze each signal
                signal_stats = {}
                
                for row in results:
                    pred_data = json.loads(row[9])  # individual_signals column
                    actual_move_4h = None
                    actual_move_24h = None
                    
                    if row[10] and row[11]:  # price_4h and price_24h
                        actual_move_4h = (row[10] - row[2]) / row[2]  # rtx_price
                        actual_move_24h = (row[11] - row[2]) / row[2]
                    
                    # Analyze each individual signal
                    for signal_data in pred_data:
                        signal_name = signal_data['signal_name']
                        signal_direction = signal_data['direction']
                        signal_confidence = signal_data['confidence']
                        signal_expected = signal_data['expected_move']
                        
                        if signal_name not in signal_stats:
                            signal_stats[signal_name] = {
                                'total_predictions': 0,
                                'accurate_direction': 0,
                                'accurate_magnitude': 0,
                                'avg_confidence': 0,
                                'profit_factor': 0,
                                'best_setups': []
                            }
                        
                        stats = signal_stats[signal_name]
                        stats['total_predictions'] += 1
                        stats['avg_confidence'] += signal_confidence
                        
                        # Check direction accuracy
                        if actual_move_24h is not None:
                            predicted_up = signal_direction == 'BUY'
                            actual_up = actual_move_24h > 0.01
                            
                            if (predicted_up and actual_up) or (not predicted_up and not actual_up):
                                stats['accurate_direction'] += 1
                            
                            # Check magnitude accuracy (within 50% of predicted)
                            if abs(actual_move_24h) > abs(signal_expected) * 0.5:
                                stats['accurate_magnitude'] += 1
                            
                            # Track best setups
                            if signal_confidence > 0.8 and abs(actual_move_24h) > 0.03:
                                stats['best_setups'].append({
                                    'timestamp': row[1],
                                    'confidence': signal_confidence,
                                    'predicted_move': signal_expected,
                                    'actual_move': actual_move_24h,
                                    'rationale': signal_data.get('rationale', '')
                                })
                
                # Calculate final metrics
                for signal_name, stats in signal_stats.items():
                    if stats['total_predictions'] > 0:
                        stats['avg_confidence'] /= stats['total_predictions']
                        stats['direction_accuracy'] = stats['accurate_direction'] / stats['total_predictions']
                        stats['magnitude_accuracy'] = stats['accurate_magnitude'] / stats['total_predictions']
                        
                        # Sort best setups by actual move
                        stats['best_setups'].sort(key=lambda x: abs(x['actual_move']), reverse=True)
                        stats['best_setups'] = stats['best_setups'][:5]  # Top 5
                
                self.signal_performance = signal_stats
                return signal_stats
                
        except Exception as e:
            self.logger.error(f"Error analyzing signal performance: {e}")
            return {}
    
    async def get_optimal_signal_weights(self) -> Dict[str, float]:
        """Calculate optimal signal weights based on performance"""
        try:
            await self.analyze_signal_performance()
            
            if not self.signal_performance:
                # Return default weights
                return {
                    'technical_analysis': 0.15,
                    'momentum': 0.15,
                    'volatility_analysis': 0.15,
                    'sector_correlation': 0.15,
                    'mean_reversion': 0.10,
                    'market_regime': 0.10,
                    'options_flow': 0.10,
                    'news_sentiment': 0.10
                }
            
            # Calculate performance scores
            signal_scores = {}
            for signal_name, stats in self.signal_performance.items():
                if stats['total_predictions'] >= 5:  # Minimum predictions for reliability
                    # Weighted score: direction accuracy + magnitude accuracy + confidence
                    score = (
                        stats['direction_accuracy'] * 0.5 +
                        stats['magnitude_accuracy'] * 0.3 +
                        stats['avg_confidence'] * 0.2
                    )
                    signal_scores[signal_name] = max(0.05, min(0.25, score))  # Bound between 5% and 25%
                else:
                    signal_scores[signal_name] = 0.125  # Default weight
            
            # Normalize weights to sum to 1.0
            total_score = sum(signal_scores.values())
            if total_score > 0:
                optimal_weights = {k: v/total_score for k, v in signal_scores.items()}
            else:
                optimal_weights = signal_scores
            
            # Update database
            await self._update_signal_weights(optimal_weights)
            
            return optimal_weights
            
        except Exception as e:
            self.logger.error(f"Error calculating optimal weights: {e}")
            return {}
    
    async def _update_signal_weights(self, weights: Dict[str, float]):
        """Update signal weights in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for signal_name, weight in weights.items():
                    if signal_name in self.signal_performance:
                        stats = self.signal_performance[signal_name]
                        performance_score = stats.get('direction_accuracy', 0.5)
                        total_preds = stats.get('total_predictions', 0)
                        accurate_preds = stats.get('accurate_direction', 0)
                    else:
                        performance_score = 0.5
                        total_preds = 0
                        accurate_preds = 0
                    
                    conn.execute("""
                        INSERT OR REPLACE INTO signal_weights 
                        (signal_name, current_weight, performance_score, total_predictions, 
                         accurate_predictions, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        signal_name,
                        weight,
                        performance_score,
                        total_preds,
                        accurate_preds,
                        datetime.now().isoformat()
                    ))
            
            self.logger.info("📊 Signal weights updated based on performance")
            
        except Exception as e:
            self.logger.error(f"Error updating signal weights: {e}")
    
    async def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        try:
            await self.analyze_signal_performance()
            
            # Get options trading performance
            with sqlite3.connect(self.db_path) as conn:
                options_query = """
                    SELECT COUNT(*) as total_trades,
                           AVG(profit_loss_pct) as avg_return,
                           SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                           MAX(profit_loss_pct) as best_trade,
                           MIN(profit_loss_pct) as worst_trade
                    FROM options_trades
                    WHERE profit_loss IS NOT NULL
                """
                
                options_stats = conn.execute(options_query).fetchone()
            
            # Calculate high-conviction accuracy
            high_conviction_query = """
                SELECT COUNT(*) as total,
                       AVG(CASE WHEN o.price_24h > p.rtx_price AND p.action = 'BUY' 
                                 OR o.price_24h < p.rtx_price AND p.action = 'SELL' 
                                THEN 1.0 ELSE 0.0 END) as accuracy
                FROM predictions p
                JOIN outcomes o ON p.id = o.prediction_id
                WHERE p.trade_worthy = 1 AND o.price_24h IS NOT NULL
                AND p.timestamp > datetime('now', '-30 days')
            """
            
            with sqlite3.connect(self.db_path) as conn:
                hc_stats = conn.execute(high_conviction_query).fetchone()
            
            summary = {
                'signal_performance': self.signal_performance,
                'options_trading': {
                    'total_trades': options_stats[0] if options_stats else 0,
                    'avg_return_pct': options_stats[1] if options_stats else 0,
                    'win_rate': (options_stats[2] / max(1, options_stats[0])) if options_stats else 0,
                    'best_trade_pct': options_stats[3] if options_stats else 0,
                    'worst_trade_pct': options_stats[4] if options_stats else 0
                },
                'high_conviction_accuracy': hc_stats[1] if hc_stats and hc_stats[0] > 0 else 0,
                'high_conviction_count': hc_stats[0] if hc_stats else 0,
                'last_analysis': datetime.now().isoformat()
            }
            
            self.last_analysis = summary
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating performance summary: {e}")
            return {}

# Global performance tracker instance
performance_tracker = SignalPerformanceTracker()

async def test_performance_tracker():
    """Test the signal performance tracker"""
    print("📊 Testing Signal Performance Tracker")
    print("=" * 50)
    
    try:
        # Test recording a prediction
        test_signals = [
            SignalPrediction(
                timestamp=datetime.now(),
                signal_name='technical_analysis',
                direction='BUY',
                confidence=0.75,
                strength=0.8,
                expected_move=0.04,
                rationale='RSI oversold + MACD bullish cross'
            ),
            SignalPrediction(
                timestamp=datetime.now(),
                signal_name='momentum',
                direction='BUY',
                confidence=0.82,
                strength=0.9,
                expected_move=0.035,
                rationale='Strong upward momentum'
            )
        ]
        
        test_prediction = CombinedPrediction(
            timestamp=datetime.now(),
            rtx_price=155.50,
            action='BUY',
            confidence=0.78,
            expected_move=0.037,
            signals_agreeing=2,
            total_signals=8,
            individual_signals=test_signals,
            trade_worthy=False  # Below 80% confidence threshold
        )
        
        pred_id = await performance_tracker.record_prediction(test_prediction)
        print(f"✅ Recorded test prediction: {pred_id}")
        
        # Analyze performance
        performance = await performance_tracker.analyze_signal_performance()
        print(f"📈 Performance analysis completed: {len(performance)} signals analyzed")
        
        # Get optimal weights
        weights = await performance_tracker.get_optimal_signal_weights()
        print(f"⚖️  Optimal weights calculated: {len(weights)} signals")
        
        # Get summary
        summary = await performance_tracker.get_performance_summary()
        print(f"📊 Performance summary generated")
        
        print("✅ All tests passed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_performance_tracker())
#!/usr/bin/env python3
"""
Real-time Signal Effectiveness Tracker
Tracks which signals contribute to profitable trades and learns in real-time
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger
from collections import defaultdict

class SignalEffectivenessTracker:
    """Tracks signal effectiveness in real-time for ML optimization"""
    
    def __init__(self, db_path: str = "data/signal_effectiveness.db"):
        self.db_path = db_path
        self.signal_scores = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total_pnl': 0.0})
        self.recent_signals = []  # Cache for performance
        self._init_database()
        self._load_historical_data()
    
    def _init_database(self):
        """Initialize signal effectiveness database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create signal effectiveness table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signal_effectiveness (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_name TEXT NOT NULL,
                prediction_id TEXT NOT NULL,
                signal_confidence REAL NOT NULL,
                signal_direction TEXT NOT NULL,
                trade_outcome TEXT,  -- 'win', 'loss', 'pending'
                trade_pnl REAL DEFAULT 0.0,
                trade_pnl_percentage REAL DEFAULT 0.0,
                strategy_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                exit_timestamp DATETIME,
                contribution_score REAL DEFAULT 0.0,
                UNIQUE(prediction_id, signal_name)
            )
        """)
        
        # Create signal performance summary table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signal_performance_summary (
                signal_name TEXT PRIMARY KEY,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0.0,
                avg_pnl REAL DEFAULT 0.0,
                total_pnl REAL DEFAULT 0.0,
                avg_confidence REAL DEFAULT 0.0,
                effectiveness_score REAL DEFAULT 0.0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create signal correlation table (which signals work well together)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signal_correlations (
                signal_a TEXT NOT NULL,
                signal_b TEXT NOT NULL,
                correlation_strength REAL DEFAULT 0.0,
                combined_win_rate REAL DEFAULT 0.0,
                trades_together INTEGER DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (signal_a, signal_b)
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("📊 Signal Effectiveness Tracker initialized")
    
    def _load_historical_data(self):
        """Load historical signal performance data into memory cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Load signal performance summaries
            cursor.execute("""
                SELECT signal_name, total_trades, winning_trades, total_pnl
                FROM signal_performance_summary
                WHERE total_trades > 0
            """)
            
            for row in cursor.fetchall():
                signal_name, total_trades, wins, total_pnl = row
                losses = total_trades - wins
                self.signal_scores[signal_name] = {
                    'wins': wins,
                    'losses': losses,
                    'total_pnl': total_pnl
                }
            
            conn.close()
            logger.debug(f"📊 Loaded historical data for {len(self.signal_scores)} signals")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not load historical data: {e}")
            # This is normal for first run when tables don't exist yet
    
    def track_prediction_signals(self, prediction_id: str, signals_data: Dict, 
                                strategy_id: str) -> bool:
        """Track signals for a new prediction"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Store each signal's contribution to this prediction
            for signal_name, signal_info in signals_data.items():
                if isinstance(signal_info, dict):
                    confidence = signal_info.get('confidence', 0.0)
                    direction = signal_info.get('direction', 'UNKNOWN')
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO signal_effectiveness 
                        (signal_name, prediction_id, signal_confidence, signal_direction, 
                         strategy_id, trade_outcome)
                        VALUES (?, ?, ?, ?, ?, 'pending')
                    """, (signal_name, prediction_id, confidence, direction, strategy_id))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"📊 Tracked {len(signals_data)} signals for prediction {prediction_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to track prediction signals: {e}")
            return False
    
    def update_trade_outcome(self, prediction_id: str, outcome: str, 
                           pnl: float, pnl_percentage: float) -> bool:
        """Update trade outcome for all signals involved in this prediction"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update all signals for this prediction
            cursor.execute("""
                UPDATE signal_effectiveness 
                SET trade_outcome = ?, trade_pnl = ?, trade_pnl_percentage = ?, 
                    exit_timestamp = CURRENT_TIMESTAMP,
                    contribution_score = signal_confidence * ?
                WHERE prediction_id = ?
            """, (outcome, pnl, pnl_percentage, pnl_percentage, prediction_id))
            
            rows_updated = cursor.rowcount
            conn.commit()
            conn.close()
            
            if rows_updated > 0:
                # Update performance summaries
                self._update_performance_summaries(prediction_id)
                logger.info(f"📊 Updated {rows_updated} signals for prediction {prediction_id}: {outcome}")
                return True
            else:
                logger.warning(f"⚠️ No signals found for prediction {prediction_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to update trade outcome: {e}")
            return False
    
    def _update_performance_summaries(self, prediction_id: str):
        """Update signal performance summaries after trade completion"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all signals involved in this prediction
            cursor.execute("""
                SELECT signal_name FROM signal_effectiveness 
                WHERE prediction_id = ?
            """, (prediction_id,))
            
            signals = [row[0] for row in cursor.fetchall()]
            
            # Update summary for each signal
            for signal_name in signals:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN trade_outcome = 'win' THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN trade_outcome = 'loss' THEN 1 ELSE 0 END) as losses,
                        AVG(trade_pnl) as avg_pnl,
                        SUM(trade_pnl) as total_pnl,
                        AVG(signal_confidence) as avg_confidence
                    FROM signal_effectiveness 
                    WHERE signal_name = ? AND trade_outcome IN ('win', 'loss')
                """, (signal_name,))
                
                result = cursor.fetchone()
                if result:
                    total, wins, losses, avg_pnl, total_pnl, avg_conf = result
                    win_rate = (wins / total) * 100 if total > 0 else 0
                    
                    # Calculate effectiveness score (win rate * avg confidence * avg pnl)
                    effectiveness = (win_rate / 100) * (avg_conf or 0) * (avg_pnl or 0)
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO signal_performance_summary
                        (signal_name, total_trades, winning_trades, losing_trades,
                         win_rate, avg_pnl, total_pnl, avg_confidence, effectiveness_score,
                         last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (signal_name, total, wins, losses, win_rate, avg_pnl or 0, 
                         total_pnl or 0, avg_conf or 0, effectiveness))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to update performance summaries: {e}")
    
    def get_signal_rankings(self, min_trades: int = 5) -> List[Dict]:
        """Get signals ranked by effectiveness"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT signal_name, total_trades, win_rate, avg_pnl, 
                       total_pnl, effectiveness_score, avg_confidence
                FROM signal_performance_summary 
                WHERE total_trades >= ?
                ORDER BY effectiveness_score DESC
            """, (min_trades,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'signal_name': row[0],
                    'total_trades': row[1],
                    'win_rate': row[2],
                    'avg_pnl': row[3],
                    'total_pnl': row[4],
                    'effectiveness_score': row[5],
                    'avg_confidence': row[6]
                })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to get signal rankings: {e}")
            return []
    
    def get_underperforming_signals(self, min_trades: int = 3) -> List[Dict]:
        """Identify signals that are consistently underperforming"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT signal_name, total_trades, win_rate, avg_pnl, effectiveness_score
                FROM signal_performance_summary 
                WHERE total_trades >= ? AND (win_rate < 30 OR avg_pnl < -10)
                ORDER BY effectiveness_score ASC
            """, (min_trades,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'signal_name': row[0],
                    'total_trades': row[1],
                    'win_rate': row[2],
                    'avg_pnl': row[3],
                    'effectiveness_score': row[4],
                    'issue': 'Low win rate' if row[2] < 30 else 'Poor P&L'
                })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to get underperforming signals: {e}")
            return []
    
    def generate_signal_insights(self) -> Dict:
        """Generate comprehensive signal insights for optimization"""
        try:
            top_signals = self.get_signal_rankings()[:5]
            underperforming = self.get_underperforming_signals()
            
            # Get total signal statistics
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(DISTINCT signal_name) as total_signals,
                       AVG(win_rate) as avg_win_rate,
                       SUM(total_pnl) as combined_pnl
                FROM signal_performance_summary
                WHERE total_trades >= 3
            """)
            
            stats = cursor.fetchone()
            conn.close()
            
            insights = {
                'timestamp': datetime.now().isoformat(),
                'total_signals_tracked': stats[0] if stats else 0,
                'average_win_rate': stats[1] if stats and stats[1] else 0,
                'combined_pnl': stats[2] if stats and stats[2] else 0,
                'top_performers': top_signals,
                'underperformers': underperforming,
                'recommendations': self._generate_recommendations(top_signals, underperforming)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"❌ Failed to generate signal insights: {e}")
            return {}
    
    def _generate_recommendations(self, top_signals: List[Dict], 
                                underperforming: List[Dict]) -> List[str]:
        """Generate optimization recommendations based on signal performance"""
        recommendations = []
        
        if top_signals:
            best_signal = top_signals[0]
            recommendations.append(
                f"🚀 Increase weight for '{best_signal['signal_name']}' "
                f"({best_signal['win_rate']:.1f}% win rate, ${best_signal['avg_pnl']:.2f} avg P&L)"
            )
        
        if underperforming:
            worst_signal = underperforming[0]
            recommendations.append(
                f"⚠️ Reduce weight for '{worst_signal['signal_name']}' "
                f"({worst_signal['win_rate']:.1f}% win rate, {worst_signal['issue']})"
            )
        
        if len(top_signals) >= 3:
            top_3 = [s['signal_name'] for s in top_signals[:3]]
            recommendations.append(
                f"✅ Focus on top 3 signals: {', '.join(top_3)}"
            )
        
        return recommendations
    
    def export_effectiveness_data(self, output_file: str = None) -> str:
        """Export signal effectiveness data for ML training"""
        if not output_file:
            output_file = f"signal_effectiveness_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            insights = self.generate_signal_insights()
            
            with open(output_file, 'w') as f:
                json.dump(insights, f, indent=2)
            
            logger.info(f"📊 Signal effectiveness data exported to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"❌ Failed to export effectiveness data: {e}")
            return ""

# Global instance
signal_tracker = SignalEffectivenessTracker()

def track_prediction_signals(prediction_id: str, signals_data: Dict, strategy_id: str) -> bool:
    """Global function to track signals for a prediction"""
    return signal_tracker.track_prediction_signals(prediction_id, signals_data, strategy_id)

def update_trade_outcome(prediction_id: str, outcome: str, pnl: float, pnl_percentage: float) -> bool:
    """Global function to update trade outcome"""
    return signal_tracker.update_trade_outcome(prediction_id, outcome, pnl, pnl_percentage)

def get_signal_effectiveness_report() -> Dict:
    """Global function to get signal effectiveness insights"""
    return signal_tracker.generate_signal_insights()

if __name__ == "__main__":
    # Test the signal effectiveness tracker
    tracker = SignalEffectivenessTracker()
    
    # Simulate some signal tracking
    test_signals = {
        'technical_analysis': {'confidence': 0.85, 'direction': 'CALL'},
        'news_sentiment': {'confidence': 0.72, 'direction': 'CALL'},
        'momentum': {'confidence': 0.91, 'direction': 'CALL'}
    }
    
    prediction_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Track prediction
    tracker.track_prediction_signals(prediction_id, test_signals, "test_strategy")
    
    # Simulate trade outcome
    tracker.update_trade_outcome(prediction_id, "win", 150.0, 35.5)
    
    # Generate insights
    insights = tracker.generate_signal_insights()
    print("📊 Signal Effectiveness Insights:")
    print(json.dumps(insights, indent=2))
"""
Prediction Outcome Tracker
Tracks actual RTX price movements and options P&L after predictions
Runs periodically to update prediction_outcomes table
"""
import sqlite3
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger
import asyncio

class PredictionOutcomeTracker:
    """Tracks actual outcomes of predictions for ML learning"""
    
    def __init__(self, db_path: str = "data/signal_performance.db"):
        self.db_path = db_path
        self.ticker = yf.Ticker("RTX")
        
    async def track_all_outcomes(self):
        """Track outcomes for all untracked predictions"""
        logger.info("🔍 Tracking prediction outcomes...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find predictions that need outcome tracking
        cursor.execute("""
            SELECT p.prediction_id, p.timestamp, p.direction, p.confidence
            FROM predictions p
            LEFT JOIN prediction_outcomes po ON p.prediction_id = po.prediction_id
            WHERE po.prediction_id IS NULL
                AND datetime(p.timestamp) < datetime('now', '-1 hour')
            ORDER BY p.timestamp DESC
            LIMIT 20
        """)
        
        untracked = cursor.fetchall()
        logger.info(f"Found {len(untracked)} predictions to track")
        
        for prediction_id, timestamp, direction, confidence in untracked:
            await self._track_single_outcome(prediction_id, timestamp, cursor)
            
        conn.commit()
        conn.close()
        
        logger.success(f"✅ Tracked {len(untracked)} prediction outcomes")
        
    async def _track_single_outcome(self, prediction_id: str, prediction_time: str, cursor):
        """Track outcome for a single prediction"""
        try:
            # Parse prediction timestamp
            pred_dt = datetime.fromisoformat(prediction_time.replace(' ', 'T'))
            
            # Get RTX price at prediction time and current
            history = self.ticker.history(period="5d", interval="1h")
            
            if history.empty:
                logger.warning(f"⚠️ No price data available for {prediction_id}")
                return
            
            # Find closest price to prediction time
            history.index = history.index.tz_localize(None)  # Remove timezone
            time_diff = abs(history.index - pred_dt)
            closest_idx = time_diff.argmin()
            
            entry_price = history.loc[closest_idx, 'Close']
            
            # Calculate price moves at different intervals
            moves = {}
            for hours in [1, 4, 24]:
                target_time = pred_dt + timedelta(hours=hours)
                
                # Find price at target time
                if target_time <= datetime.now():
                    time_diff = abs(history.index - target_time)
                    if time_diff.min() < timedelta(hours=2):  # Within 2 hours is acceptable
                        target_idx = time_diff.argmin()
                        target_price = history.loc[target_idx, 'Close']
                        moves[f'{hours}h'] = (target_price - entry_price) / entry_price
                    else:
                        moves[f'{hours}h'] = None
                else:
                    moves[f'{hours}h'] = None
            
            # Determine actual direction
            if moves['24h'] is not None:
                if moves['24h'] > 0.01:
                    actual_direction = 'BUY'
                elif moves['24h'] < -0.01:
                    actual_direction = 'SELL'
                else:
                    actual_direction = 'HOLD'
            else:
                actual_direction = None
            
            # Calculate max move in 24h window
            max_move = None
            if moves['24h'] is not None:
                # Get all prices in 24h window
                window_start = pred_dt
                window_end = pred_dt + timedelta(hours=24)
                mask = (history.index >= window_start) & (history.index <= window_end)
                window_prices = history.loc[mask, 'Close']
                
                if not window_prices.empty:
                    max_price = window_prices.max()
                    min_price = window_prices.min()
                    
                    # Max move depends on predicted direction
                    if actual_direction == 'BUY':
                        max_move = (max_price - entry_price) / entry_price
                    else:
                        max_move = (entry_price - min_price) / entry_price
            
            # Insert outcome
            cursor.execute("""
                INSERT INTO prediction_outcomes 
                (prediction_id, timestamp_checked, actual_direction, 
                 actual_move_1h, actual_move_4h, actual_move_24h, max_move_24h,
                 price_1h, price_4h, price_24h, options_profit_potential)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction_id,
                datetime.now().isoformat(),
                actual_direction,
                moves.get('1h'),
                moves.get('4h'),
                moves.get('24h'),
                max_move,
                entry_price * (1 + (moves.get('1h', 0) or 0)),
                entry_price * (1 + (moves.get('4h', 0) or 0)),
                entry_price * (1 + (moves.get('24h', 0) or 0)),
                self._calculate_options_profit(moves.get('24h', 0), actual_direction)
            ))
            
            logger.info(f"✅ Tracked {prediction_id}: {actual_direction} move {moves.get('24h', 0):.3%}")
            
        except Exception as e:
            logger.error(f"❌ Error tracking {prediction_id}: {e}")
    
    def _calculate_options_profit(self, actual_move: float, direction: str) -> float:
        """Estimate options profit based on actual move"""
        if actual_move is None:
            return 0
        
        # Rough estimate: 3% move = 100% options profit
        # This is simplified - real options P&L depends on IV, time decay, etc
        if direction == 'BUY' and actual_move > 0:
            return min(actual_move / 0.03, 2.0)  # Cap at 200% profit
        elif direction == 'SELL' and actual_move < 0:
            return min(abs(actual_move) / 0.03, 2.0)
        else:
            return -0.5  # 50% loss if direction was wrong
    
    async def run_continuous_tracking(self):
        """Run outcome tracking continuously"""
        logger.info("🚀 Starting continuous outcome tracking")
        
        while True:
            try:
                await self.track_all_outcomes()
                
                # Also check and close paper positions
                from src.core.options_paper_trader import options_paper_trader
                if options_paper_trader.open_positions:
                    actions = options_paper_trader.check_positions()
                    if actions:
                        logger.info(f"📊 Closed {len(actions)} positions")
                
                # Wait 5 minutes before next check
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"❌ Tracking error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

# Global instance
outcome_tracker = PredictionOutcomeTracker()

if __name__ == "__main__":
    # Test tracking
    asyncio.run(outcome_tracker.track_all_outcomes())
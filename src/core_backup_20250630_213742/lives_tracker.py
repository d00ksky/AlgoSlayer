#!/usr/bin/env python3
"""
Lives Tracking System for Options Trading
Each "life" is $1000 of capital. When depleted, start a new life.
Track performance across all lives for comprehensive learning.
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger

class LivesTracker:
    """Track trading performance across multiple 'lives' of $1000 each"""
    
    def __init__(self, db_path: str = "data/options_performance.db"):
        self.db_path = db_path
        self.lives_file = "data/trading_lives.json"
        self.starting_capital = 1000.0
        self.minimum_balance = 100.0  # Below this, consider life "lost"
        self._init_database()
        self.current_life = self._load_or_create_lives()
        
    def _init_database(self):
        """Initialize lives tracking table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_lives (
                life_number INTEGER PRIMARY KEY,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ended_at DATETIME,
                starting_balance REAL DEFAULT 1000.0,
                ending_balance REAL,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0.0,
                status TEXT DEFAULT 'ACTIVE',
                death_reason TEXT,
                lessons_learned TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def _load_or_create_lives(self) -> Dict:
        """Load current life status or create first life"""
        try:
            with open(self.lives_file, 'r') as f:
                lives_data = json.load(f)
                return lives_data
        except (FileNotFoundError, json.JSONDecodeError):
            # Create first life
            return self._start_new_life(1)
            
    def _save_lives_data(self):
        """Save lives data to file"""
        with open(self.lives_file, 'w') as f:
            json.dump(self.current_life, f, indent=2)
            
    def _start_new_life(self, life_number: int) -> Dict:
        """Start a new trading life with fresh capital"""
        logger.info(f"🎮 Starting Life #{life_number} with ${self.starting_capital}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert new life record
        cursor.execute('''
            INSERT INTO trading_lives (life_number, starting_balance)
            VALUES (?, ?)
        ''', (life_number, self.starting_capital))
        
        conn.commit()
        conn.close()
        
        new_life = {
            "current_life_number": life_number,
            "started_at": datetime.now().isoformat(),
            "current_balance": self.starting_capital,
            "total_lives_used": life_number,
            "all_time_pnl": self._calculate_all_time_pnl(),
            "status": "ACTIVE"
        }
        
        self.current_life = new_life  # Set before saving
        self._save_lives_data()
        return new_life
        
    def check_life_status(self, current_balance: float, open_positions_count: int = 0) -> Dict:
        """Check if current life is still active or needs respawn"""
        life_status = {
            "life_number": self.current_life["current_life_number"],
            "balance": current_balance,
            "health_percentage": (current_balance / self.starting_capital) * 100,
            "status": "ACTIVE",
            "action_needed": None
        }
        
        # Only reset if balance is low AND no open positions
        if current_balance < self.minimum_balance and open_positions_count == 0:
            life_status["status"] = "DEPLETED"
            life_status["action_needed"] = "RESPAWN"
            logger.warning(f"💀 Life #{self.current_life['current_life_number']} depleted! Balance: ${current_balance:.2f}, No positions")
            
            # End current life
            self._end_current_life(current_balance, "INSUFFICIENT_FUNDS_NO_POSITIONS")
            
            # Start new life
            new_life_number = self.current_life["current_life_number"] + 1
            self.current_life = self._start_new_life(new_life_number)
            life_status["new_life_number"] = new_life_number
            life_status["message"] = f"Starting fresh with Life #{new_life_number}!"
            
        elif current_balance < self.minimum_balance and open_positions_count > 0:
            life_status["status"] = "CRITICAL_WITH_POSITIONS"
            life_status["message"] = f"⏳ Low funds (${current_balance:.2f}) but {open_positions_count} positions may recover"
            
        elif current_balance < self.starting_capital * 0.3:
            life_status["status"] = "CRITICAL"
            life_status["message"] = f"⚠️ Critical health! Only {life_status['health_percentage']:.1f}% remaining"
            
        elif current_balance < self.starting_capital * 0.5:
            life_status["status"] = "DAMAGED"
            life_status["message"] = f"🩹 Taking damage! {life_status['health_percentage']:.1f}% health"
            
        else:
            life_status["message"] = f"💚 Healthy! {life_status['health_percentage']:.1f}% health"
            
        return life_status
        
    def _end_current_life(self, ending_balance: float, death_reason: str):
        """Record the end of a trading life"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get trading statistics for this life
        cursor.execute('''
            SELECT COUNT(*) as total_trades,
                   SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as wins
            FROM options_outcomes
            WHERE datetime(closed_at) >= ?
        ''', (self.current_life["started_at"],))
        
        stats = cursor.fetchone()
        
        # Calculate lessons learned
        lessons = self._analyze_life_performance(stats[0], stats[1], ending_balance)
        
        # Update life record
        cursor.execute('''
            UPDATE trading_lives
            SET ended_at = CURRENT_TIMESTAMP,
                ending_balance = ?,
                total_trades = ?,
                winning_trades = ?,
                total_pnl = ?,
                status = 'ENDED',
                death_reason = ?,
                lessons_learned = ?
            WHERE life_number = ?
        ''', (ending_balance, stats[0], stats[1], 
              ending_balance - self.starting_capital,
              death_reason, json.dumps(lessons),
              self.current_life["current_life_number"]))
        
        conn.commit()
        conn.close()
        
    def _analyze_life_performance(self, total_trades: int, wins: int, ending_balance: float) -> Dict:
        """Analyze what went wrong/right in this life"""
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        pnl_pct = ((ending_balance - self.starting_capital) / self.starting_capital) * 100
        
        lessons = {
            "win_rate": win_rate,
            "total_return": pnl_pct,
            "trades_executed": total_trades,
            "insights": []
        }
        
        if win_rate < 30:
            lessons["insights"].append("Win rate too low - need better signal filtering")
        if total_trades < 5:
            lessons["insights"].append("Too few trades - might be too conservative")
        if pnl_pct < -50:
            lessons["insights"].append("Large losses - position sizing or stop losses need work")
            
        return lessons
        
    def _calculate_all_time_pnl(self) -> float:
        """Calculate total P&L across all lives"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT SUM(total_pnl) 
            FROM trading_lives 
            WHERE status = 'ENDED'
        ''')
        
        result = cursor.fetchone()[0]
        conn.close()
        
        return result or 0.0
        
    def get_lives_summary(self) -> Dict:
        """Get comprehensive summary of all trading lives"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all lives data
        cursor.execute('''
            SELECT life_number, starting_balance, ending_balance, 
                   total_trades, winning_trades, total_pnl, status,
                   death_reason, lessons_learned,
                   datetime(started_at) as started,
                   datetime(ended_at) as ended
            FROM trading_lives
            ORDER BY life_number DESC
        ''')
        
        lives = cursor.fetchall()
        conn.close()
        
        summary = {
            "current_life": self.current_life["current_life_number"],
            "total_lives_used": len(lives),
            "all_time_investment": len([l for l in lives if l[6] == 'ENDED']) * self.starting_capital,
            "all_time_pnl": self._calculate_all_time_pnl(),
            "lives_history": []
        }
        
        for life in lives:
            life_data = {
                "life_number": life[0],
                "duration": self._calculate_duration(life[9], life[10]),
                "trades": life[3],
                "win_rate": (life[4] / life[3] * 100) if life[3] > 0 else 0,
                "pnl": life[5],
                "status": life[6],
                "death_reason": life[7],
                "lessons": json.loads(life[8]) if life[8] else {}
            }
            summary["lives_history"].append(life_data)
            
        # Learning insights across all lives
        summary["meta_insights"] = self._generate_meta_insights(summary["lives_history"])
        
        return summary
        
    def _calculate_duration(self, started: str, ended: Optional[str]) -> str:
        """Calculate how long a life lasted"""
        if not ended:
            return "Active"
            
        try:
            start = datetime.fromisoformat(started.replace(' ', 'T'))
            end = datetime.fromisoformat(ended.replace(' ', 'T'))
            duration = end - start
            
            if duration.days > 0:
                return f"{duration.days} days"
            else:
                return f"{duration.seconds // 3600} hours"
        except:
            return "Unknown"
            
    def _generate_meta_insights(self, lives_history: List[Dict]) -> List[str]:
        """Generate insights from patterns across multiple lives"""
        insights = []
        
        if len(lives_history) >= 3:
            avg_duration = sum(1 for l in lives_history if l["status"] == "ENDED") / len(lives_history)
            if avg_duration < 7:
                insights.append("Lives ending too quickly - risk management critical")
                
            avg_win_rate = sum(l["win_rate"] for l in lives_history) / len(lives_history)
            if avg_win_rate < 40:
                insights.append("Consistent low win rate - strategy needs fundamental change")
                
            if all(l["pnl"] < 0 for l in lives_history[:3]):
                insights.append("Losing streak detected - consider paper trading only")
                
        return insights
        
    def respawn_with_new_life(self) -> Dict:
        """Manually trigger a new life (for testing or manual intervention)"""
        current_balance = 0  # Force new life
        return self.check_life_status(current_balance)

if __name__ == "__main__":
    # Test the lives system
    tracker = LivesTracker()
    
    # Check current status
    status = tracker.check_life_status(359.50)  # Current balance
    print(f"🎮 Life Status: {status}")
    
    # Get summary
    summary = tracker.get_lives_summary()
    print(f"\n📊 Lives Summary:")
    print(f"Current Life: #{summary['current_life']}")
    print(f"Total Lives Used: {summary['total_lives_used']}")
    print(f"All-Time P&L: ${summary['all_time_pnl']:.2f}")
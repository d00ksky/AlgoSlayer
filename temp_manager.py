#!/usr/bin/env python3
"""
Multi-Strategy Trading Manager
Manages multiple parallel trading strategies with independent accounts,
each with its own ML optimization and performance tracking.
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from loguru import logger
import asyncio
from dataclasses import dataclass

@dataclass
class StrategyConfig:
    """Configuration for each trading strategy"""
    name: str
    confidence_threshold: float
    min_signals_required: int
    position_size_pct: float
    description: str
    signal_weights: Optional[Dict[str, float]] = None

class MultiStrategyManager:
    """Manage multiple parallel trading strategies with independent learning"""
    
    def __init__(self, db_path: str = "data/options_performance.db"):
        self.db_path = db_path
        self.strategies_file = "data/active_strategies.json"
        self.starting_capital = 1000.0
        
        # Define the three strategies
        self.strategy_configs = {
            "conservative": StrategyConfig(
                name="Conservative",
                confidence_threshold=0.75,
                min_signals_required=4,
                position_size_pct=0.15,
                description="High confidence, multiple signal agreement, small positions"
            ),
            "moderate": StrategyConfig(
                name="Moderate",
                confidence_threshold=0.60,
                min_signals_required=3,
                position_size_pct=0.20,
                description="Balanced approach with moderate risk"
            ),
            "aggressive": StrategyConfig(
                name="Aggressive",
                confidence_threshold=0.50,
                description=Lower threshold, larger positions, more trades
            ),
            scalping: StrategyConfig(
                name=Scalping,
                confidence_threshold=0.75,
                min_signals_required=3,
                position_size_pct=0.10,
                description=Fast 15min-2hr trades, high confidence, small positions
            ),
            swing: StrategyConfig(
                name=Swing,
                confidence_threshold=0.70,
                min_signals_required=3,
                position_size_pct=0.30,
                description=2-5 day holds, moderate confidence, larger positions
            ),
            momentum: StrategyConfig(
                name=Momentum,
                confidence_threshold=0.68,
                min_signals_required=2,
                position_size_pct=0.20,
                description=Trend following, momentum-based entries
            ),
            volatility: StrategyConfig(
                name=Volatility,
                confidence_threshold=0.73,
                min_signals_required=3,
                position_size_pct=0.25,
                description=IV expansion plays, volatility timing
            ),
            mean_reversion: StrategyConfig(
                name=Mean Reversion,
                confidence_threshold=0.72,
                min_signals_required=3,
                position_size_pct=0.22,
                description=Counter-trend, oversold/overbought plays
            )
        }
                position_size_pct=0.25,
                description="Lower threshold, larger positions, more trades"
            )
        }
        
        self._init_database()
        self.active_strategies = self._load_or_create_strategies()
        
    def _init_database(self):
        """Initialize multi-strategy tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Strategies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_strategies (
                strategy_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                config TEXT NOT NULL,
                status TEXT DEFAULT 'ACTIVE',
                current_balance REAL DEFAULT 1000.0,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0.0,
                last_ml_update DATETIME,
                signal_weights TEXT,
                performance_score REAL DEFAULT 0.0
            )
        ''')
        
        # Strategy predictions table (links predictions to strategies)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_predictions (
                prediction_id TEXT,
                strategy_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (prediction_id, strategy_id),
                FOREIGN KEY (strategy_id) REFERENCES trading_strategies(strategy_id)
            )
        ''')
        
        # Strategy performance tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_performance (
                strategy_id TEXT,
                date DATE,
                trades_made INTEGER DEFAULT 0,
                successful_trades INTEGER DEFAULT 0,
                daily_pnl REAL DEFAULT 0.0,
                balance_end_of_day REAL,
                win_rate REAL,
                ml_adjustments TEXT,
                PRIMARY KEY (strategy_id, date),
                FOREIGN KEY (strategy_id) REFERENCES trading_strategies(strategy_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def _load_or_create_strategies(self) -> Dict[str, Dict]:
        """Load existing strategies or create new ones"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        strategies = {}
        
        for strategy_id, config in self.strategy_configs.items():
            # Check if strategy exists
            cursor.execute('''
                SELECT current_balance, total_trades, winning_trades, 
                       total_pnl, signal_weights, performance_score
                FROM trading_strategies
                WHERE strategy_id = ? AND status = 'ACTIVE'
            ''', (strategy_id,))
            
            existing = cursor.fetchone()
            
            if existing:
                # Load existing strategy
                strategies[strategy_id] = {
                    "config": config,
                    "balance": existing[0],
                    "total_trades": existing[1],
                    "winning_trades": existing[2],
                    "total_pnl": existing[3],
                    "signal_weights": json.loads(existing[4]) if existing[4] else None,
                    "performance_score": existing[5]
                }
                logger.info(f"📊 Loaded strategy '{config.name}': Balance ${existing[0]:.2f}, Score: {existing[5]:.2f}")
            else:
                # Create new strategy
                cursor.execute('''
                    INSERT INTO trading_strategies 
                    (strategy_id, name, config, current_balance)
                    VALUES (?, ?, ?, ?)
                ''', (strategy_id, config.name, json.dumps(config.__dict__), self.starting_capital))
                
                strategies[strategy_id] = {
                    "config": config,
                    "balance": self.starting_capital,
                    "total_trades": 0,
                    "winning_trades": 0,
                    "total_pnl": 0.0,
                    "signal_weights": None,
                    "performance_score": 0.0
                }
                logger.info(f"🆕 Created strategy '{config.name}' with ${self.starting_capital}")
                
        conn.commit()
        conn.close()
        
        return strategies
        
    def get_strategy_config(self, strategy_id: str) -> Tuple[StrategyConfig, Dict[str, float]]:
        """Get configuration and current state for a strategy"""
        if strategy_id not in self.active_strategies:
            raise ValueError(f"Unknown strategy: {strategy_id}")
            
        strategy = self.active_strategies[strategy_id]
        config = strategy["config"]
        
        # Override with ML-optimized weights if available
        if strategy["signal_weights"]:
            config.signal_weights = strategy["signal_weights"]
            
        return config, {
            "balance": strategy["balance"],
            "performance_score": strategy["performance_score"],
            "win_rate": (strategy["winning_trades"] / strategy["total_trades"] * 100) 
                        if strategy["total_trades"] > 0 else 0
        }
        
    def record_prediction(self, strategy_id: str, prediction_id: str):
        """Record that a strategy made a prediction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO strategy_predictions 
            (prediction_id, strategy_id)
            VALUES (?, ?)
        ''', (prediction_id, strategy_id))
        
        conn.commit()
        conn.close()
        
    def update_strategy_balance(self, strategy_id: str, new_balance: float, trade_result: Optional[Dict] = None):
        """Update strategy balance and performance metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        strategy = self.active_strategies[strategy_id]
        old_balance = strategy["balance"]
        pnl = new_balance - old_balance
        
        # Update in-memory state
        strategy["balance"] = new_balance
        strategy["total_pnl"] += pnl
        
        if trade_result:
            strategy["total_trades"] += 1
            if trade_result.get("profitable", False):
                strategy["winning_trades"] += 1
                
        # Calculate performance score (weighted by multiple factors)
        strategy["performance_score"] = self._calculate_performance_score(strategy)
        
        # Update database
        cursor.execute('''
            UPDATE trading_strategies
            SET current_balance = ?,
                total_trades = ?,
                winning_trades = ?,
                total_pnl = ?,
                performance_score = ?
            WHERE strategy_id = ?
        ''', (new_balance, strategy["total_trades"], strategy["winning_trades"],
              strategy["total_pnl"], strategy["performance_score"], strategy_id))
        
        # Update daily performance
        today = datetime.now().date()
        cursor.execute('''
            INSERT OR REPLACE INTO strategy_performance
            (strategy_id, date, balance_end_of_day, daily_pnl)
            VALUES (?, ?, ?, ?)
        ''', (strategy_id, today, new_balance, pnl))
        
        conn.commit()
        conn.close()
        
        logger.info(f"💰 {strategy['config'].name} strategy: ${old_balance:.2f} → ${new_balance:.2f} (P&L: ${pnl:.2f})")
        
    def _calculate_performance_score(self, strategy: Dict) -> float:
        """Calculate overall performance score for ranking strategies"""
        if strategy["total_trades"] == 0:
            return 0.0
            
        # Factors for scoring
        win_rate = strategy["winning_trades"] / strategy["total_trades"]
        avg_pnl_per_trade = strategy["total_pnl"] / strategy["total_trades"]
        total_return = strategy["total_pnl"] / self.starting_capital
        
        # Weighted score (win rate + profitability + consistency)
        score = (
            win_rate * 40 +                    # 40% weight on win rate
            min(avg_pnl_per_trade, 100) * 0.3 + # 30% weight on avg profit
            total_return * 30                   # 30% weight on total return
        )
        
        return round(score, 2)
        
    def apply_ml_optimization(self, strategy_id: str, new_signal_weights: Dict[str, float]):
        """Apply ML-learned signal weights to a strategy"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update in-memory
        self.active_strategies[strategy_id]["signal_weights"] = new_signal_weights
        
        # Update database
        cursor.execute('''
            UPDATE trading_strategies
            SET signal_weights = ?,
                last_ml_update = CURRENT_TIMESTAMP
            WHERE strategy_id = ?
        ''', (json.dumps(new_signal_weights), strategy_id))
        
        # Record ML adjustment
        cursor.execute('''
            UPDATE strategy_performance
            SET ml_adjustments = ?
            WHERE strategy_id = ? AND date = ?
        ''', (json.dumps(new_signal_weights), strategy_id, datetime.now().date()))
        
        conn.commit()
        conn.close()
        
        logger.info(f"🧠 Applied ML optimization to {self.active_strategies[strategy_id]['config'].name} strategy")
        
    def get_leaderboard(self) -> List[Dict]:
        """Get current strategy rankings"""
        leaderboard = []
        
        for strategy_id, strategy in self.active_strategies.items():
            config = strategy["config"]
            win_rate = (strategy["winning_trades"] / strategy["total_trades"] * 100) if strategy["total_trades"] > 0 else 0
            
            leaderboard.append({
                "rank": 0,  # Will be set after sorting
                "strategy": config.name,
                "balance": strategy["balance"],
                "total_pnl": strategy["total_pnl"],
                "trades": strategy["total_trades"],
                "win_rate": win_rate,
                "score": strategy["performance_score"],
                "status": self._get_strategy_status(strategy)
            })
            
        # Sort by performance score
        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        
        # Add ranks
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1
            
        return leaderboard
        
    def _get_strategy_status(self, strategy: Dict) -> str:
        """Get emoji status for strategy health"""
        balance_pct = (strategy["balance"] / self.starting_capital) * 100
        
        if balance_pct >= 120:
            return "🚀 Excellent"
        elif balance_pct >= 100:
            return "✅ Profitable"
        elif balance_pct >= 80:
            return "⚠️ Struggling"
        elif balance_pct >= 50:
            return "🩹 Damaged"
        else:
            return "💀 Critical"
            
    def get_comparison_report(self) -> Dict:
        """Generate comprehensive comparison report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "strategies": {},
            "winner": None,
            "insights": []
        }
        
        # Get detailed stats for each strategy
        for strategy_id, strategy in self.active_strategies.items():
            # Get recent performance
            cursor.execute('''
                SELECT date, daily_pnl, win_rate
                FROM strategy_performance
                WHERE strategy_id = ?
                ORDER BY date DESC
                LIMIT 7
            ''', (strategy_id,))
            
            recent_performance = cursor.fetchall()
            
            config = strategy["config"]
            report["strategies"][strategy_id] = {
                "name": config.name,
                "config": {
                    "confidence": config.confidence_threshold,
                    "min_signals": config.min_signals_required,
                    "position_size": config.position_size_pct
                },
                "performance": {
                    "balance": strategy["balance"],
                    "total_pnl": strategy["total_pnl"],
                    "trades": strategy["total_trades"],
                    "win_rate": (strategy["winning_trades"] / strategy["total_trades"] * 100) 
                                if strategy["total_trades"] > 0 else 0,
                    "score": strategy["performance_score"]
                },
                "recent_7_days": [
                    {"date": str(p[0]), "pnl": p[1], "win_rate": p[2]}
                    for p in recent_performance
                ]
            }
            
        # Determine winner
        if all(s["total_trades"] >= 10 for s in self.active_strategies.values()):
            winner = max(self.active_strategies.items(), key=lambda x: x[1]["performance_score"])
            report["winner"] = winner[0]
            report["winner_name"] = winner[1]["config"].name
            
        # Generate insights
        report["insights"] = self._generate_insights()
        
        conn.close()
        return report
        
    def _generate_insights(self) -> List[str]:
        """Generate insights from strategy comparison"""
        insights = []
        
        # Compare win rates
        win_rates = {
            k: (v["winning_trades"] / v["total_trades"] * 100) if v["total_trades"] > 0 else 0
            for k, v in self.active_strategies.items()
        }
        
        best_win_rate = max(win_rates.items(), key=lambda x: x[1])
        if best_win_rate[1] > 0:
            insights.append(f"{self.active_strategies[best_win_rate[0]]['config'].name} has best win rate: {best_win_rate[1]:.1f}%")
            
        # Compare profitability
        best_pnl = max(self.active_strategies.items(), key=lambda x: x[1]["total_pnl"])
        if best_pnl[1]["total_pnl"] > 0:
            insights.append(f"{best_pnl[1]['config'].name} is most profitable: ${best_pnl[1]['total_pnl']:.2f}")
            
        # Check if conservative is actually conservative
        if self.active_strategies["conservative"]["total_trades"] > 0:
            cons_trades = self.active_strategies["conservative"]["total_trades"]
            agg_trades = self.active_strategies["aggressive"]["total_trades"]
            if agg_trades > cons_trades * 1.5:
                insights.append("Aggressive strategy making 50%+ more trades as expected")
                
        return insights

if __name__ == "__main__":
    # Test the multi-strategy system
    manager = MultiStrategyManager()
    
    # Get strategy configurations
    for strategy_id in ["conservative", "moderate", "aggressive"]:
        config, state = manager.get_strategy_config(strategy_id)
        print(f"\n{config.name} Strategy:")
        print(f"  Confidence: {config.confidence_threshold:.0%}")
        print(f"  Min Signals: {config.min_signals_required}")
        print(f"  Balance: ${state['balance']:.2f}")
        print(f"  Win Rate: {state['win_rate']:.1f}%")
    
    # Show leaderboard
    print("\n📊 Strategy Leaderboard:")
    for entry in manager.get_leaderboard():
        print(f"{entry['rank']}. {entry['strategy']}: ${entry['balance']:.2f} (Score: {entry['score']})")
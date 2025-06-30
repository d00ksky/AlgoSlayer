#!/usr/bin/env python3
"""
Multi-Strategy Coordinator - Manages 8 trading strategies with cross-learning
Coordinates between: Conservative, Moderate, Aggressive, Scalping, Swing, Momentum, Mean Reversion, Volatility
"""

import sys
import os
sys.path.append('/opt/rtx-trading')

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3

class MultiStrategyCoordinator:
    def __init__(self):
        self.strategies = {
            'conservative': {'threshold': 0.60, 'max_position': 400, 'style': 'safe'},
            'moderate': {'threshold': 0.55, 'max_position': 450, 'style': 'balanced'},
            'aggressive': {'threshold': 0.50, 'max_position': 500, 'style': 'frequent'},
            'scalping': {'threshold': 0.65, 'max_position': 300, 'style': 'quick'},
            'swing': {'threshold': 0.70, 'max_position': 500, 'style': 'patient'},
            'momentum': {'threshold': 0.58, 'max_position': 400, 'style': 'trending'},
            'mean_reversion': {'threshold': 0.62, 'max_position': 350, 'style': 'contrarian'},
            'volatility': {'threshold': 0.68, 'max_position': 450, 'style': 'explosive'}
        }
        
        self.cross_learning_patterns = {}
        self.performance_rankings = {}
        
    def get_all_strategies(self):
        return list(self.strategies.keys())
    
    def get_strategy_config(self, strategy_name: str):
        if strategy_name not in self.strategies:
            return None
        return self.strategies[strategy_name]
    
    def update_cross_learning_patterns(self):
        """Extract successful patterns from best-performing strategies"""
        
        try:
            conn = sqlite3.connect('/opt/rtx-trading/data/algoslayer_main.db')
            cursor = conn.cursor()
            
            # Get performance by strategy
            cursor.execute('''
                SELECT strategy_id, 
                       COUNT(*) as total_trades,
                       SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as wins,
                       AVG(net_pnl) as avg_pnl
                FROM outcomes o
                JOIN predictions p ON o.prediction_id = p.prediction_id
                WHERE p.timestamp > datetime('now', '-7 days')
                GROUP BY strategy_id
                HAVING total_trades >= 3
                ORDER BY avg_pnl DESC
            ''')
            
            performance_data = cursor.fetchall()
            
            if performance_data:
                best_strategy = performance_data[0][0]
                best_avg_pnl = performance_data[0][3]
                
                print(f'🏆 Best performing strategy: {best_strategy} (${best_avg_pnl:.2f} avg P&L)')
                
                # Extract patterns from best strategy
                cursor.execute('''
                    SELECT confidence, expected_move, entry_price, net_pnl
                    FROM predictions p
                    JOIN outcomes o ON p.prediction_id = o.prediction_id
                    WHERE p.strategy_id = ? AND o.net_pnl > 0
                    ORDER BY o.net_pnl DESC
                    LIMIT 10
                ''', (best_strategy,))
                
                winning_patterns = cursor.fetchall()
                
                if winning_patterns:
                    self.cross_learning_patterns[best_strategy] = {
                        'avg_confidence': sum(p[0] for p in winning_patterns) / len(winning_patterns),
                        'avg_expected_move': sum(p[1] for p in winning_patterns) / len(winning_patterns),
                        'successful_trades': len(winning_patterns)
                    }
                    
                    print(f'📚 Extracted {len(winning_patterns)} winning patterns from {best_strategy}')
            
            conn.close()
            
        except Exception as e:
            print(f'❌ Cross-learning update error: {e}')
    
    def apply_cross_learning(self, target_strategy: str, base_signals: List[Dict]) -> List[Dict]:
        """Apply learning patterns from successful strategies"""
        
        if not self.cross_learning_patterns:
            return base_signals
            
        enhanced_signals = base_signals.copy()
        
        # Apply patterns from best performing strategies
        for source_strategy, patterns in self.cross_learning_patterns.items():
            if source_strategy != target_strategy:
                # Boost confidence for signals that match successful patterns
                confidence_boost = patterns.get('avg_confidence', 0) * 0.1  # 10% boost
                
                for signal in enhanced_signals:
                    if signal.get('confidence', 0) >= 0.6:  # Only boost already good signals
                        signal['confidence'] = min(1.0, signal['confidence'] + confidence_boost)
                        signal['cross_learning'] = f'boosted_by_{source_strategy}'
        
        return enhanced_signals
    
    def generate_strategy_recommendation(self, current_signals: List[Dict]) -> Optional[str]:
        """Recommend which strategy should trade based on current conditions"""
        
        if not current_signals:
            return None
            
        # Calculate confidence for each strategy
        strategy_scores = {}
        
        for strategy_name in self.strategies:
            config = self.strategies[strategy_name]
            
            # Apply cross-learning enhancements
            enhanced_signals = self.apply_cross_learning(strategy_name, current_signals)
            
            # Calculate strategy-specific confidence
            confidences = [s.get('confidence', 0) for s in enhanced_signals]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Check if meets threshold
            if avg_confidence >= config['threshold']:
                strategy_scores[strategy_name] = avg_confidence
        
        # Return highest scoring strategy
        if strategy_scores:
            best_strategy = max(strategy_scores.items(), key=lambda x: x[1])
            return best_strategy[0]
        
        return None

# Create global coordinator instance
multi_strategy_coordinator = MultiStrategyCoordinator()

if __name__ == '__main__':
    print('🎯 Multi-Strategy Coordinator Started')
    print(f'📊 Managing {len(multi_strategy_coordinator.get_all_strategies())} strategies:')
    
    for strategy in multi_strategy_coordinator.get_all_strategies():
        config = multi_strategy_coordinator.get_strategy_config(strategy)
        print(f'  • {strategy}: {config["threshold"]:.0%} threshold, ${config["max_position"]} max, {config["style"]} style')
    
    print('\n🧠 Cross-learning system initialized')
    multi_strategy_coordinator.update_cross_learning_patterns()
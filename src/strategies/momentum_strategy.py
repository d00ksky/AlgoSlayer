#!/usr/bin/env python3
"""
Momentum Strategy - Trend following with quick entries
Optimized for capturing trending moves with momentum signals
"""

import sys
import os
sys.path.append('/opt/rtx-trading')

from datetime import datetime, timedelta
from typing import Dict, List, Optional

class MomentumTradingEngine:
    def __init__(self):
        self.name = 'momentum'
        self.confidence_threshold = 0.58
        self.max_position_size = 400
        self.max_daily_loss = 60
        self.target_profit_1 = 0.30  # 30% - take 40% of position
        self.target_profit_2 = 0.60  # 60% - take 40% of position
        self.target_profit_3 = 1.20  # 120% - take remaining 20%
        self.stop_loss = 0.18        # 18% max loss
        self.max_hold_time = 2880    # 2 days max (48 hours)
        self.min_hold_time = 60      # 1 hour min
        
        self.active_positions = {}
        self.daily_pnl = 0
        self.trades_today = 0
        
    def get_strategy_config(self):
        return {
            'strategy_id': self.name,
            'confidence_threshold': self.confidence_threshold,
            'max_position_size': self.max_position_size,
            'max_daily_loss': self.max_daily_loss,
            'profit_targets': [self.target_profit_1, self.target_profit_2, self.target_profit_3],
            'stop_loss': self.stop_loss,
            'time_limits': {
                'max_hold_minutes': self.max_hold_time,
                'min_hold_minutes': self.min_hold_time
            },
            'signal_weights': {
                'momentum': 1.4,               # Primary signal for momentum
                'technical_analysis': 1.2,     # TA confirms momentum
                'market_regime': 1.1,          # Market state important
                'options_flow': 1.0,           # Flow shows momentum
                'sector_correlation': 0.9,     # Secondary importance
                'news_sentiment': 0.8          # Less relevant for momentum
            }
        }
    
    def should_enter_trade(self, signals: List[Dict]) -> bool:
        """Determine if momentum trading conditions are met"""
        
        if not signals:
            return False
        
        # Apply momentum-specific signal weights
        config = self.get_strategy_config()
        weighted_confidences = []
        
        for signal in signals:
            signal_name = signal.get('name', '')
            confidence = signal.get('confidence', 0)
            weight = config['signal_weights'].get(signal_name, 1.0)
            
            weighted_confidences.append(confidence * weight)
        
        # Calculate overall confidence
        avg_confidence = sum(weighted_confidences) / len(weighted_confidences)
        
        # Momentum allows lower threshold for trend following
        return avg_confidence >= self.confidence_threshold
    
    def calculate_position_size(self, option_price: float, confidence: float) -> int:
        """Calculate optimal position size for momentum trading"""
        
        # Momentum uses moderate positions with scaling based on strength
        position_value = self.max_position_size * confidence * 0.85  # 85% of max
        
        contracts = int(position_value // (option_price * 100))
        return max(1, min(contracts, 25))  # 1-25 contracts for momentum

# Create global momentum engine instance
momentum_engine = MomentumTradingEngine()

if __name__ == '__main__':
    print('🚀 Momentum Strategy Engine Started')
    config = momentum_engine.get_strategy_config()
    print(f'📊 Config: {config["strategy_id"]} - {config["confidence_threshold"]:.0%} threshold')
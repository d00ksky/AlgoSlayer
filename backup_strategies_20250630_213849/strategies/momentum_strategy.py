#\!/usr/bin/env python3
"""
Momentum Strategy - Trend following strategy that rides momentum
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
        self.profit_targets = [0.75, 1.5]
        self.stop_loss = 0.2
        self.min_hold_time = 60  # minutes
        self.max_hold_time = 480  # minutes
        
    def get_strategy_config(self):
        return {
            'strategy_id': self.name,
            'confidence_threshold': self.confidence_threshold,
            'max_position_size': self.max_position_size,
            'profit_targets': self.profit_targets,
            'stop_loss': self.stop_loss,
            'time_limits': {
                'max_hold_minutes': self.max_hold_time,
                'min_hold_minutes': self.min_hold_time
            },
            'signal_weights': {'momentum': 1.4, 'technical_analysis': 1.2, 'market_regime': 1.1, 'options_flow': 1.0}
        }
    
    def should_enter_trade(self, signals: List[Dict]) -> bool:
        """Determine if trading conditions are met"""
        
        if not signals:
            return False
        
        config = self.get_strategy_config()
        weighted_confidences = []
        
        for signal in signals:
            signal_name = signal.get('name', '')
            confidence = signal.get('confidence', 0)
            weight = config['signal_weights'].get(signal_name, 1.0)
            weighted_confidences.append(confidence * weight)
        
        avg_confidence = sum(weighted_confidences) / len(weighted_confidences)
        return avg_confidence >= self.confidence_threshold

# Create global engine instance
momentum_engine = MomentumTradingEngine()

if __name__ == '__main__':
    print('🚀 Momentum Strategy Engine Started')
    config = momentum_engine.get_strategy_config()
    print(f'📊 Strategy: {config["strategy_id"]} - {config["confidence_threshold"]:.0%} threshold')
    print(f'🎯 Targets: {[f"{p:.0%}" for p in config["profit_targets"]]}')

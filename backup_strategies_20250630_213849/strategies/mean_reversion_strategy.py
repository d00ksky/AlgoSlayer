#\!/usr/bin/env python3
"""
Mean_Reversion Strategy - Counter-trend strategy on oversold/overbought conditions
"""

import sys
import os
sys.path.append('/opt/rtx-trading')

from datetime import datetime, timedelta
from typing import Dict, List, Optional

class Mean_ReversionTradingEngine:
    def __init__(self):
        self.name = 'mean_reversion'
        self.confidence_threshold = 0.62
        self.max_position_size = 350
        self.max_daily_loss = 60
        self.profit_targets = [0.5, 1.0]
        self.stop_loss = 0.25
        self.min_hold_time = 30  # minutes
        self.max_hold_time = 360  # minutes
        
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
            'signal_weights': {'mean_reversion': 1.3, 'technical_analysis': 1.2, 'volatility_analysis': 1.1, 'options_iv_percentile': 1.0}
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
mean_reversion_engine = Mean_ReversionTradingEngine()

if __name__ == '__main__':
    print('🚀 Mean_Reversion Strategy Engine Started')
    config = mean_reversion_engine.get_strategy_config()
    print(f'📊 Strategy: {config["strategy_id"]} - {config["confidence_threshold"]:.0%} threshold')
    print(f'🎯 Targets: {[f"{p:.0%}" for p in config["profit_targets"]]}')

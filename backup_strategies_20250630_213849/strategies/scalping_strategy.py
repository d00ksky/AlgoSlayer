#\!/usr/bin/env python3
"""
Scalping Strategy - Quick profit capture on high-confidence signals
Optimized for 15-minute to 2-hour holding periods
"""

import sys
import os
sys.path.append('/opt/rtx-trading')

from datetime import datetime, timedelta
from typing import Dict, List, Optional

class ScalpingTradingEngine:
    def __init__(self):
        self.name = 'scalping'
        self.confidence_threshold = 0.65
        self.max_position_size = 300
        self.max_daily_loss = 50
        self.target_profit_1 = 0.25  # 25% profit target
        self.target_profit_2 = 0.50  # 50% profit target
        self.stop_loss = 0.15        # 15% max loss
        self.max_hold_time = 120     # 2 hours max
        self.min_hold_time = 15      # 15 minutes min
        
    def get_strategy_config(self):
        return {
            'strategy_id': self.name,
            'confidence_threshold': self.confidence_threshold,
            'max_position_size': self.max_position_size,
            'max_daily_loss': self.max_daily_loss,
            'profit_targets': [self.target_profit_1, self.target_profit_2],
            'stop_loss': self.stop_loss,
            'time_limits': {
                'max_hold_minutes': self.max_hold_time,
                'min_hold_minutes': self.min_hold_time
            }
        }

# Create global scalping engine instance
scalping_engine = ScalpingTradingEngine()

if __name__ == '__main__':
    print('🏃 Scalping Strategy Engine Started')
    config = scalping_engine.get_strategy_config()
    print(f'📊 Strategy: {config["strategy_id"]} - {config["confidence_threshold"]:.0%} threshold')

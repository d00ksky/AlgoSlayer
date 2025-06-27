#!/usr/bin/env python3
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
        self.target_profit_1 = 0.25  # 25% - take 50% of position
        self.target_profit_2 = 0.50  # 50% - take remaining 50%
        self.stop_loss = 0.15        # 15% max loss
        self.max_hold_time = 120     # 2 hours max
        self.min_hold_time = 15      # 15 minutes min
        
        self.active_positions = {}
        self.daily_pnl = 0
        self.trades_today = 0
        
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
            },
            'signal_weights': {
                'options_iv_percentile': 1.2,  # Favor IV timing for scalping
                'momentum': 1.1,               # Quick momentum moves
                'technical_analysis': 1.0,     # Standard TA weight
                'options_flow': 0.9,           # Less important for quick moves
                'news_sentiment': 0.8          # News less relevant for scalping
            }
        }
    
    def should_enter_trade(self, signals: List[Dict]) -> bool:
        """Determine if scalping conditions are met"""
        
        if not signals:
            return False
        
        # Apply scalping-specific signal weights
        config = self.get_strategy_config()
        weighted_confidences = []
        
        for signal in signals:
            signal_name = signal.get('name', '')
            confidence = signal.get('confidence', 0)
            weight = config['signal_weights'].get(signal_name, 1.0)
            
            weighted_confidences.append(confidence * weight)
        
        # Calculate overall confidence
        avg_confidence = sum(weighted_confidences) / len(weighted_confidences)
        
        # Scalping requires higher confidence due to short timeframe
        return avg_confidence >= self.confidence_threshold
    
    def calculate_position_size(self, option_price: float, confidence: float) -> int:
        """Calculate optimal position size for scalping"""
        
        # Scalping uses smaller positions due to higher frequency
        position_value = self.max_position_size * confidence * 0.8  # 80% of max for safety
        
        contracts = int(position_value // (option_price * 100))
        return max(1, min(contracts, 20))  # 1-20 contracts for scalping

# Create global scalping engine instance
scalping_engine = ScalpingTradingEngine()

if __name__ == '__main__':
    print('🏃 Scalping Strategy Engine Started')
    config = scalping_engine.get_strategy_config()
    print(f'📊 Config: {config["strategy_id"]} - {config["confidence_threshold"]:.0%} threshold')
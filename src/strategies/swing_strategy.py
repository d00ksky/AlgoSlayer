#!/usr/bin/env python3
"""
Swing Strategy - Multi-day trend capture strategy
Optimized for 2-5 day holding periods with higher position sizes
"""

import sys
import os
sys.path.append('/opt/rtx-trading')

from datetime import datetime, timedelta
from typing import Dict, List, Optional

class SwingTradingEngine:
    def __init__(self):
        self.name = 'swing'
        self.confidence_threshold = 0.70
        self.max_position_size = 500
        self.max_daily_loss = 75
        self.target_profit_1 = 0.40  # 40% - take 25% of position
        self.target_profit_2 = 0.80  # 80% - take 50% of position  
        self.target_profit_3 = 1.50  # 150% - take remaining 25%
        self.stop_loss = 0.20        # 20% max loss (wider for swing)
        self.max_hold_time = 7200    # 5 days max (120 hours)
        self.min_hold_time = 1440    # 1 day min (24 hours)
        
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
                'technical_analysis': 1.3,     # Strong TA for swing trades
                'momentum': 1.2,               # Multi-day momentum
                'sector_correlation': 1.1,     # Sector trends matter
                'news_sentiment': 1.0,         # News impact over days
                'options_flow': 0.9,           # Less relevant for swing
                'options_iv_percentile': 0.8   # IV less critical for swing
            }
        }
    
    def should_enter_trade(self, signals: List[Dict]) -> bool:
        """Determine if swing trading conditions are met"""
        
        if not signals:
            return False
        
        # Apply swing-specific signal weights
        config = self.get_strategy_config()
        weighted_confidences = []
        
        for signal in signals:
            signal_name = signal.get('name', '')
            confidence = signal.get('confidence', 0)
            weight = config['signal_weights'].get(signal_name, 1.0)
            
            weighted_confidences.append(confidence * weight)
        
        # Calculate overall confidence
        avg_confidence = sum(weighted_confidences) / len(weighted_confidences)
        
        # Swing requires very high confidence for multi-day holds
        return avg_confidence >= self.confidence_threshold
    
    def calculate_position_size(self, option_price: float, confidence: float) -> int:
        """Calculate optimal position size for swing trading"""
        
        # Swing uses larger positions for fewer, higher-conviction trades
        position_value = self.max_position_size * confidence * 0.9  # 90% of max
        
        contracts = int(position_value // (option_price * 100))
        return max(1, min(contracts, 30))  # 1-30 contracts for swing

# Create global swing engine instance
swing_engine = SwingTradingEngine()

if __name__ == '__main__':
    print('📈 Swing Strategy Engine Started')
    config = swing_engine.get_strategy_config()
    print(f'📊 Config: {config["strategy_id"]} - {config["confidence_threshold"]:.0%} threshold')
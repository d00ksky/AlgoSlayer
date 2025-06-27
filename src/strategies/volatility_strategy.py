#!/usr/bin/env python3
"""
Volatility Strategy - IV expansion plays and high-impact events
Optimized for capturing volatility spikes and earnings plays
"""

import sys
import os
sys.path.append('/opt/rtx-trading')

from datetime import datetime, timedelta
from typing import Dict, List, Optional

class VolatilityTradingEngine:
    def __init__(self):
        self.name = 'volatility'
        self.confidence_threshold = 0.68
        self.max_position_size = 450
        self.max_daily_loss = 70
        self.target_profit_1 = 0.50  # 50% - take 30% of position
        self.target_profit_2 = 1.00  # 100% - take 40% of position
        self.target_profit_3 = 2.00  # 200% - take remaining 30%
        self.stop_loss = 0.25        # 25% max loss (wider for vol plays)
        self.max_hold_time = 4320    # 3 days max (72 hours)
        self.min_hold_time = 120     # 2 hours min
        
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
                'volatility_analysis': 1.4,    # Primary signal for vol strategy
                'options_iv_percentile': 1.3,  # IV timing crucial
                'rtx_earnings': 1.2,           # Earnings drive volatility
                'news_sentiment': 1.1,         # News creates vol spikes
                'trump_geopolitical': 1.0,     # Geopolitical volatility
                'technical_analysis': 0.9,     # Less important for vol plays
                'momentum': 0.8                # Not momentum-based
            }
        }
    
    def should_enter_trade(self, signals: List[Dict]) -> bool:
        """Determine if volatility expansion conditions are met"""
        
        if not signals:
            return False
        
        # Apply volatility-specific signal weights
        config = self.get_strategy_config()
        weighted_confidences = []
        
        for signal in signals:
            signal_name = signal.get('name', '')
            confidence = signal.get('confidence', 0)
            weight = config['signal_weights'].get(signal_name, 1.0)
            
            weighted_confidences.append(confidence * weight)
        
        # Calculate overall confidence
        avg_confidence = sum(weighted_confidences) / len(weighted_confidences)
        
        # Volatility requires high confidence for explosive moves
        return avg_confidence >= self.confidence_threshold
    
    def calculate_position_size(self, option_price: float, confidence: float) -> int:
        """Calculate optimal position size for volatility trading"""
        
        # Volatility uses larger positions for explosive potential
        position_value = self.max_position_size * confidence * 0.9  # 90% of max
        
        contracts = int(position_value // (option_price * 100))
        return max(1, min(contracts, 28))  # 1-28 contracts for volatility

# Create global volatility engine instance
volatility_engine = VolatilityTradingEngine()

if __name__ == '__main__':
    print('💥 Volatility Strategy Engine Started')
    config = volatility_engine.get_strategy_config()
    print(f'📊 Config: {config["strategy_id"]} - {config["confidence_threshold"]:.0%} threshold')
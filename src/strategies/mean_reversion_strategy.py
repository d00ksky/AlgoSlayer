#!/usr/bin/env python3
"""
Mean Reversion Strategy - Counter-trend plays on oversold/overbought conditions
Optimized for capturing reversals at extreme levels
"""

import sys
import os
sys.path.append('/opt/rtx-trading')

from datetime import datetime, timedelta
from typing import Dict, List, Optional

class MeanReversionTradingEngine:
    def __init__(self):
        self.name = 'mean_reversion'
        self.confidence_threshold = 0.62
        self.max_position_size = 350
        self.max_daily_loss = 55
        self.target_profit_1 = 0.35  # 35% - take 50% of position
        self.target_profit_2 = 0.70  # 70% - take 30% of position
        self.target_profit_3 = 1.10  # 110% - take remaining 20%
        self.stop_loss = 0.22        # 22% max loss (wider for reversions)
        self.max_hold_time = 1440    # 1 day max (24 hours)
        self.min_hold_time = 30      # 30 minutes min
        
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
                'mean_reversion': 1.3,         # Primary signal
                'technical_analysis': 1.2,     # RSI/oversold conditions
                'volatility_analysis': 1.1,    # High vol often precedes reversions
                'options_iv_percentile': 1.0,  # IV extremes signal reversions
                'momentum': 0.7,               # Counter-momentum strategy
                'market_regime': 0.8           # Market state less important
            }
        }
    
    def should_enter_trade(self, signals: List[Dict]) -> bool:
        """Determine if mean reversion conditions are met"""
        
        if not signals:
            return False
        
        # Apply mean reversion-specific signal weights
        config = self.get_strategy_config()
        weighted_confidences = []
        
        for signal in signals:
            signal_name = signal.get('name', '')
            confidence = signal.get('confidence', 0)
            weight = config['signal_weights'].get(signal_name, 1.0)
            
            weighted_confidences.append(confidence * weight)
        
        # Calculate overall confidence
        avg_confidence = sum(weighted_confidences) / len(weighted_confidences)
        
        # Mean reversion requires moderate confidence for counter-trend trades
        return avg_confidence >= self.confidence_threshold
    
    def calculate_position_size(self, option_price: float, confidence: float) -> int:
        """Calculate optimal position size for mean reversion trading"""
        
        # Mean reversion uses conservative positions due to counter-trend risk
        position_value = self.max_position_size * confidence * 0.75  # 75% of max for safety
        
        contracts = int(position_value // (option_price * 100))
        return max(1, min(contracts, 18))  # 1-18 contracts for mean reversion

# Create global mean reversion engine instance
mean_reversion_engine = MeanReversionTradingEngine()

if __name__ == '__main__':
    print('🔄 Mean Reversion Strategy Engine Started')
    config = mean_reversion_engine.get_strategy_config()
    print(f'📊 Config: {config["strategy_id"]} - {config["confidence_threshold"]:.0%} threshold')
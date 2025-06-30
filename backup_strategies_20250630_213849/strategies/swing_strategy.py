#\!/usr/bin/env python3
"""
Swing Strategy - Multi-day trend capture on strong directional moves
Optimized for 2-5 day holding periods with 100-300% profit targets
"""

import sys
import os
sys.path.append('/opt/rtx-trading')

from datetime import datetime, timedelta
from typing import Dict, List, Optional

class SwingTradingEngine:
    def __init__(self):
        self.name = 'swing'
        self.confidence_threshold = 0.70  # Higher threshold for multi-day holds
        self.max_position_size = 500      # Larger positions for swing trades
        self.max_daily_loss = 75          # Higher loss limit for longer timeframe
        self.target_profit_1 = 1.00       # 100% profit - take 30% of position
        self.target_profit_2 = 2.00       # 200% profit - take 50% of position  
        self.target_profit_3 = 3.00       # 300% profit - take remaining 20%
        self.stop_loss = 0.30             # 30% max loss for swing trades
        self.max_hold_time = 7200          # 5 days max (in minutes)
        self.min_hold_time = 2880          # 2 days min (in minutes)
        
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
                'technical_analysis': 1.3,      # Strong TA for trend identification
                'momentum': 1.2,                # Momentum for trend continuation
                'options_flow': 1.1,            # Large flow indicates institutional interest
                'market_regime': 1.1,           # Market regime important for multi-day
                'news_sentiment': 1.0,          # News can drive multi-day trends
                'options_iv_percentile': 0.9    # IV less critical for swing trades
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
        
        # Swing trading requires very high confidence for multi-day commitment
        return avg_confidence >= self.confidence_threshold
    
    def calculate_position_size(self, option_price: float, confidence: float) -> int:
        """Calculate optimal position size for swing trading"""
        
        # Swing trades use larger positions due to higher conviction
        position_value = self.max_position_size * confidence  # Full allocation based on confidence
        
        contracts = int(position_value // (option_price * 100))
        return max(1, min(contracts, 50))  # 1-50 contracts for swing trades

# Create global swing engine instance
swing_engine = SwingTradingEngine()

if __name__ == '__main__':
    print('📈 Swing Strategy Engine Started')
    config = swing_engine.get_strategy_config()
    print(f'📊 Strategy: {config["strategy_id"]} - {config["confidence_threshold"]:.0%} threshold')
    print(f'🎯 Hold time: {config["time_limits"]["min_hold_minutes"]/1440:.0f}-{config["time_limits"]["max_hold_minutes"]/1440:.0f} days')
    print(f'💰 Profit targets: {[f"{p:.0%}" for p in config["profit_targets"]]}')

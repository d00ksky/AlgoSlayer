# Scalping Strategy Configuration
class ScalpingStrategy:
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

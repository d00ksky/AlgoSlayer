"""
RTX Trading Configuration
Centralized configuration for the entire trading system
"""
import os
from datetime import time
from typing import Dict, Any

class RTXTradingConfig:
    """Main configuration class for RTX trading system"""
    
    # === TRADING SYMBOL ===
    SYMBOL = "RTX"
    
    # === CAPITAL MANAGEMENT ===
    STARTING_CAPITAL = 1000
    MAX_POSITION_SIZE = 200  # Maximum per trade
    MAX_DAILY_LOSS = 50
    COMMISSION_PER_CONTRACT = 0.65
    
    # === SIGNAL WEIGHTS ===
    SIGNAL_WEIGHTS = {
        "news_sentiment": 0.15,
        "technical_analysis": 0.15,
        "options_flow": 0.15,
        "volatility_analysis": 0.15,
        "sector_correlation": 0.10,
        "momentum": 0.10,
        "market_regime": 0.10,
        "mean_reversion": 0.10
    }
    
    # === TRADING THRESHOLDS ===
    CONFIDENCE_THRESHOLD = 0.35  # Minimum confidence to trade
    HIGH_CONFIDENCE_THRESHOLD = 0.75  # High confidence alerts
    MIN_SIGNALS_REQUIRED = 3  # Minimum signals that must agree
    
    # === RISK MANAGEMENT ===
    STOP_LOSS_PERCENTAGE = 0.15  # 15% stop loss
    TAKE_PROFIT_PERCENTAGE = 0.25  # 25% take profit
    MAX_CONSECUTIVE_LOSSES = 3
    
    # === MARKET HOURS ===
    MARKET_OPEN = time(9, 30)  # 9:30 AM EST
    MARKET_CLOSE = time(16, 0)  # 4:00 PM EST
    
    # === PREDICTION SETTINGS ===
    PREDICTION_INTERVAL_MINUTES = 15
    LEARNING_LOOKBACK_DAYS = 180
    
    # === PERFORMANCE THRESHOLDS ===
    good_accuracy = 0.70
    fair_accuracy = 0.55
    poor_accuracy = 0.40

# === TRADING MODE CONTROLS ===
class TradingModeConfig:
    """Master trading controls - the kill switches"""
    
    # MASTER TRADING SWITCH
    TRADING_ENABLED = False  # Master switch - overrides everything
    
    # TRADING MODES
    PAPER_TRADING = True     # True = paper money, False = real money
    PREDICTION_ONLY = False  # True = predictions only, no orders
    
    # IBKR CONNECTION
    IBKR_REQUIRED = False    # True = fail if no IBKR, False = continue without
    AUTO_CONNECT_IBKR = True # Try to connect to IBKR automatically
    
    # ENVIRONMENT OVERRIDES (can be set in .env)
    @classmethod
    def load_from_env(cls):
        """Load settings from environment variables"""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        # Override from environment
        cls.TRADING_ENABLED = os.getenv("TRADING_ENABLED", "false").lower() == "true"
        cls.PAPER_TRADING = os.getenv("PAPER_TRADING", "true").lower() == "true" 
        cls.PREDICTION_ONLY = os.getenv("PREDICTION_ONLY", "false").lower() == "true"
        cls.IBKR_REQUIRED = os.getenv("IBKR_REQUIRED", "false").lower() == "true"
        cls.AUTO_CONNECT_IBKR = os.getenv("AUTO_CONNECT_IBKR", "true").lower() == "true"
        
        # Validation
        if cls.PREDICTION_ONLY:
            cls.TRADING_ENABLED = False  # Prediction-only mode disables trading
            
        return cls
    
    @classmethod 
    def get_mode_description(cls):
        """Get human-readable description of current mode"""
        if cls.PREDICTION_ONLY:
            return "PREDICTION ONLY - No trading, notifications only"
        elif not cls.TRADING_ENABLED:
            return "TRADING DISABLED - Predictions only"
        elif cls.PAPER_TRADING:
            return "PAPER TRADING - Fake money, real orders"
        else:
            return "LIVE TRADING - Real money, real orders"
    
    @classmethod
    def is_safe_to_trade(cls):
        """Check if it's safe to place orders"""
        return cls.TRADING_ENABLED and not cls.PREDICTION_ONLY
    
    @classmethod
    def should_connect_ibkr(cls):
        """Check if we should try to connect to IBKR"""
        return cls.AUTO_CONNECT_IBKR and (cls.TRADING_ENABLED or cls.IBKR_REQUIRED)

# === IBKR CONNECTION SETTINGS ===
class IBKRConfig:
    """Interactive Brokers connection settings"""
    
    # Connection parameters
    HOST = "127.0.0.1"
    PAPER_PORT = 7497  # Paper trading port
    LIVE_PORT = 7496   # Live trading port  
    CLIENT_ID = 1
    TIMEOUT = 10
    
    # Retry settings
    MAX_RECONNECT_ATTEMPTS = 5
    RECONNECT_DELAY = 30  # seconds
    
    # Order settings
    ORDER_TYPE = "MKT"  # Market orders by default
    TIME_IN_FORCE = "DAY"
    
    @classmethod
    def get_port(cls):
        """Get correct port based on trading mode"""
        trading_mode = TradingModeConfig.load_from_env()
        return cls.PAPER_PORT if trading_mode.PAPER_TRADING else cls.LIVE_PORT
    
    @classmethod
    def get_connection_string(cls):
        """Get connection description"""
        port = cls.get_port()
        mode = "Paper" if port == cls.PAPER_PORT else "Live"
        return f"{cls.HOST}:{port} ({mode})"

# === TELEGRAM CONFIGURATION ===
class TelegramConfig:
    """Telegram bot settings"""
    
    # Bot credentials (from environment)
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # Notification settings
    SEND_PREDICTIONS = True
    SEND_TRADE_ALERTS = True
    SEND_DAILY_SUMMARY = True
    SEND_SYSTEM_STATUS = True
    
    # Timing
    DAILY_SUMMARY_TIME = time(8, 0)  # 8:00 AM
    STATUS_UPDATE_INTERVAL = 6  # hours

# === ACCELERATED LEARNING CONFIG ===
class AcceleratedLearningConfig:
    """Accelerated learning system settings"""
    
    # Learning parameters
    LEARNING_SPEED_MULTIPLIER = 180  # 180x real-time
    HISTORICAL_DATA_MONTHS = 6
    LEARNING_SCENARIOS = [90, 180, 365]  # days
    
    # Performance tracking
    TRACK_ACCURACY = True
    SAVE_PREDICTIONS = True
    LEARNING_LOG_LEVEL = "INFO"

# Global config instance with trading controls
config = RTXTradingConfig()

# Add trading mode as module-level for easier access
trading_mode = TradingModeConfig.load_from_env()
ibkr_config = IBKRConfig()
telegram_config = TelegramConfig()
learning_config = AcceleratedLearningConfig()

# Also attach to config object
config.trading_mode = trading_mode
config.ibkr = ibkr_config
config.telegram = telegram_config
config.learning = learning_config 
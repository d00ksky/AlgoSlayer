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
    POSITION_SIZE_PCT = 0.20  # 20% of capital per position
    MAX_DAILY_LOSS = 50
    COMMISSION_PER_CONTRACT = 0.65
    
    # === SIGNAL WEIGHTS ===
    SIGNAL_WEIGHTS = {
        # Core signals (rebalanced)
        "news_sentiment": 0.12,
        "technical_analysis": 0.12,
        "options_flow": 0.12,
        "volatility_analysis": 0.12,
        "sector_correlation": 0.08,
        "momentum": 0.08,
        "market_regime": 0.08,
        "mean_reversion": 0.08,
        
        # NEW HIGH-VALUE OPTIONS SIGNALS
        "rtx_earnings": 0.10,           # RTX earnings calendar for IV timing
        "options_iv_percentile": 0.10,  # IV percentile for entry timing
        "defense_contract": 0.08,       # Defense contract news/catalysts
        "trump_geopolitical": 0.05      # Political/geopolitical impact
    }
    
    # === TRADING THRESHOLDS ===
    CONFIDENCE_THRESHOLD = 0.75  # ML Optimized: Increased from 0.35 for higher selectivity
    HIGH_CONFIDENCE_THRESHOLD = 0.75  # High confidence alerts
    MIN_SIGNALS_REQUIRED = 4  # ML Optimized: Increased from 3 for higher conviction
    
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
        
        # Helper function to parse boolean env vars
        def parse_bool(value: str, default: bool) -> bool:
            if value is None:
                return default
            return value.lower() in ['true', '1', 'yes', 'on']
        
        # Override from environment
        cls.TRADING_ENABLED = parse_bool(os.getenv("TRADING_ENABLED"), False)
        cls.PAPER_TRADING = parse_bool(os.getenv("PAPER_TRADING"), True)
        cls.PREDICTION_ONLY = parse_bool(os.getenv("PREDICTION_ONLY"), False)
        cls.IBKR_REQUIRED = parse_bool(os.getenv("IBKR_REQUIRED"), False)
        cls.AUTO_CONNECT_IBKR = parse_bool(os.getenv("AUTO_CONNECT_IBKR"), True)
        
        # Validation
        if cls.PREDICTION_ONLY:
            cls.TRADING_ENABLED = False  # Prediction-only mode disables trading
            
        # Log loaded configuration
        from loguru import logger
        logger.info(f"Trading Mode: {cls.get_mode_description()}")
        logger.info(f"IBKR Required: {cls.IBKR_REQUIRED}")
        logger.info(f"Auto Connect IBKR: {cls.AUTO_CONNECT_IBKR}")
            
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
    
    # Bot credentials (loaded dynamically from environment)
    @property
    def BOT_TOKEN(self):
        from dotenv import load_dotenv
        load_dotenv()
        return os.getenv("TELEGRAM_BOT_TOKEN")
    
    @property 
    def CHAT_ID(self):
        from dotenv import load_dotenv
        load_dotenv()
        return os.getenv("TELEGRAM_CHAT_ID")
    
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
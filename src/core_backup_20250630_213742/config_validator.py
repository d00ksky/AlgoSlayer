"""
Configuration validator to ensure all required settings are present and valid
"""
import os
import sys
from typing import Dict, List, Tuple
from loguru import logger
from dotenv import load_dotenv

class ConfigValidator:
    """Validates configuration and environment variables"""
    
    # Required environment variables
    REQUIRED_VARS = {
        "OPENAI_API_KEY": "OpenAI API key for news sentiment analysis"
    }
    
    # Optional but recommended variables
    RECOMMENDED_VARS = {
        "TELEGRAM_BOT_TOKEN": "Telegram bot token for notifications",
        "TELEGRAM_CHAT_ID": "Telegram chat ID for notifications",
        "STARTING_CAPITAL": "Starting capital amount (default: 1000)",
        "MAX_POSITION_SIZE": "Maximum position size (default: 200)",
        "MAX_DAILY_LOSS": "Maximum daily loss (default: 50)",
        "CONFIDENCE_THRESHOLD": "Minimum confidence to trade (default: 0.35)",
        "PREDICTION_INTERVAL_MINUTES": "How often to run predictions (default: 15)"
    }
    
    # Trading mode variables
    TRADING_VARS = {
        "TRADING_ENABLED": "Master trading switch (default: false)",
        "PAPER_TRADING": "Paper vs live trading (default: true)",
        "PREDICTION_ONLY": "Prediction-only mode (default: false)",
        "IBKR_REQUIRED": "Whether IBKR is required (default: false)",
        "AUTO_CONNECT_IBKR": "Auto-connect to IBKR (default: true)"
    }
    
    @classmethod
    def validate(cls) -> Tuple[bool, List[str]]:
        """
        Validate configuration
        Returns: (is_valid, error_messages)
        """
        load_dotenv()
        errors = []
        warnings = []
        
        # Check required variables
        for var, description in cls.REQUIRED_VARS.items():
            value = os.getenv(var)
            if not value:
                errors.append(f"Missing required: {var} - {description}")
            elif var == "OPENAI_API_KEY" and not value.startswith("sk-"):
                warnings.append(f"Invalid format for {var} - should start with 'sk-'")
        
        # Check recommended variables
        for var, description in cls.RECOMMENDED_VARS.items():
            value = os.getenv(var)
            if not value:
                warnings.append(f"Missing recommended: {var} - {description}")
        
        # Validate numeric values
        numeric_vars = {
            "STARTING_CAPITAL": (100, 1000000),
            "MAX_POSITION_SIZE": (10, 100000),
            "MAX_DAILY_LOSS": (10, 10000),
            "CONFIDENCE_THRESHOLD": (0.0, 1.0),
            "PREDICTION_INTERVAL_MINUTES": (1, 60)
        }
        
        for var, (min_val, max_val) in numeric_vars.items():
            value = os.getenv(var)
            if value:
                try:
                    num_val = float(value)
                    if not min_val <= num_val <= max_val:
                        errors.append(f"{var} must be between {min_val} and {max_val}")
                except ValueError:
                    errors.append(f"{var} must be a valid number")
        
        # Validate trading mode consistency
        trading_enabled = os.getenv("TRADING_ENABLED", "false").lower() == "true"
        prediction_only = os.getenv("PREDICTION_ONLY", "false").lower() == "true"
        ibkr_required = os.getenv("IBKR_REQUIRED", "false").lower() == "true"
        
        if trading_enabled and prediction_only:
            warnings.append("TRADING_ENABLED=true but PREDICTION_ONLY=true - trading will be disabled")
        
        if ibkr_required and not trading_enabled:
            errors.append("IBKR_REQUIRED=true but TRADING_ENABLED=false - inconsistent configuration")
        
        # Check Telegram configuration
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if bot_token and not chat_id:
            errors.append("TELEGRAM_BOT_TOKEN provided but TELEGRAM_CHAT_ID missing")
        elif chat_id and not bot_token:
            errors.append("TELEGRAM_CHAT_ID provided but TELEGRAM_BOT_TOKEN missing")
        
        # Log results
        if errors:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  ❌ {error}")
        
        if warnings:
            logger.warning("Configuration warnings:")
            for warning in warnings:
                logger.warning(f"  ⚠️  {warning}")
        
        if not errors and not warnings:
            logger.success("✅ Configuration validation passed")
        
        return len(errors) == 0, errors
    
    @classmethod
    def print_config_summary(cls):
        """Print current configuration summary"""
        from config.trading_config import TradingModeConfig
        
        logger.info("=" * 50)
        logger.info("CONFIGURATION SUMMARY")
        logger.info("=" * 50)
        
        # Trading mode
        trading_mode = TradingModeConfig.load_from_env()
        logger.info(f"Trading Mode: {trading_mode.get_mode_description()}")
        
        # API Keys
        openai_key = os.getenv("OPENAI_API_KEY", "")
        logger.info(f"OpenAI API: {'✅ Configured' if openai_key else '❌ Missing'}")
        
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        logger.info(f"Telegram Bot: {'✅ Configured' if telegram_token else '⚠️  Not configured'}")
        
        # Risk settings
        logger.info(f"Starting Capital: ${os.getenv('STARTING_CAPITAL', '1000')}")
        logger.info(f"Max Position Size: ${os.getenv('MAX_POSITION_SIZE', '200')}")
        logger.info(f"Max Daily Loss: ${os.getenv('MAX_DAILY_LOSS', '50')}")
        logger.info(f"Confidence Threshold: {os.getenv('CONFIDENCE_THRESHOLD', '0.35')}")
        
        logger.info("=" * 50)
    
    @classmethod
    def create_env_template(cls):
        """Create a template .env file"""
        template = """# AlgoSlayer Environment Configuration
# Generated template - fill in your values

# === REQUIRED ===
OPENAI_API_KEY=your_openai_api_key_here

# === RECOMMENDED ===
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# === TRADING MODE ===
TRADING_ENABLED=false
PAPER_TRADING=true
PREDICTION_ONLY=false
IBKR_REQUIRED=false
AUTO_CONNECT_IBKR=true

# === RISK MANAGEMENT ===
STARTING_CAPITAL=1000
MAX_POSITION_SIZE=200
MAX_DAILY_LOSS=50
CONFIDENCE_THRESHOLD=0.35

# === SYSTEM ===
LOG_LEVEL=INFO
PREDICTION_INTERVAL_MINUTES=15
"""
        
        with open(".env.template", "w") as f:
            f.write(template)
        
        logger.info("Created .env.template file")
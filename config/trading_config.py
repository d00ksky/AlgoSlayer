"""
RTX Trading Configuration
Modular configuration for all trading parameters
"""
from pydantic import BaseModel
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class RTXTradingConfig(BaseModel):
    # Trading Parameters
    TARGET_SYMBOL: str = "RTX"
    STARTING_CAPITAL: float = 1000.0
    MAX_POSITION_SIZE: float = 200.0  # Max $ per trade
    STOP_LOSS_PCT: float = 0.25  # 25% stop loss
    TARGET_WIN_RATE: float = 0.85  # 85% target win rate
    
    # Interactive Brokers
    IB_HOST: str = "127.0.0.1"
    IB_PORT: int = 7497  # Paper trading port
    IB_CLIENT_ID: int = 1
    
    # AI Signal Weights (0.0 to 1.0)
    SIGNAL_WEIGHTS: Dict[str, float] = {
        "news_sentiment": 0.3,
        "options_flow": 0.25,
        "technical_analysis": 0.2,
        "volatility_analysis": 0.15,
        "sector_correlation": 0.1
    }
    
    # Minimum signals required for trade
    MIN_SIGNALS_REQUIRED: int = 3
    MIN_CONFIDENCE_THRESHOLD: float = 0.75
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    # Risk Management
    MAX_DAILY_LOSS: float = 50.0
    MAX_WEEKLY_LOSS: float = 150.0
    POSITION_SIZE_PCT: float = 0.15  # 15% of capital per trade
    
    # Paper Trading
    PAPER_TRADING: bool = True  # Start with paper trading
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/rtx_trading.log"

# Global config instance
config = RTXTradingConfig() 
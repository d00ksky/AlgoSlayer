"""
Options Trading Configuration
Configurable settings for RTX options trading strategy
"""
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OptionsConfig:
    """Configurable options trading parameters"""
    
    # Strategy Settings (User Configurable)
    EXPIRATION_PREFERENCE = os.getenv("EXPIRATION_PREFERENCE", "weekly")  # "weekly", "monthly", "both"
    STRIKE_SELECTION = os.getenv("STRIKE_SELECTION", "atm")  # "atm", "otm", "itm", "adaptive"
    
    # Risk Management
    MAX_DAYS_TO_EXPIRY = int(os.getenv("MAX_DTE", 45))
    MIN_DAYS_TO_EXPIRY = int(os.getenv("MIN_DTE", 7))
    MAX_POSITION_SIZE_PCT = float(os.getenv("MAX_POSITION_SIZE_PCT", 0.20))  # 20% of capital
    STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", 0.50))  # 50% loss
    PROFIT_TARGET_PCT = float(os.getenv("PROFIT_TARGET_PCT", 1.00))  # 100% gain
    
    # Options Quality Filters
    MIN_VOLUME = int(os.getenv("MIN_OPTION_VOLUME", 50))
    MIN_OPEN_INTEREST = int(os.getenv("MIN_OPEN_INTEREST", 100))
    MAX_BID_ASK_SPREAD_PCT = float(os.getenv("MAX_SPREAD_PCT", 0.20))  # 20% max spread
    MIN_OPTION_PRICE = float(os.getenv("MIN_OPTION_PRICE", 0.10))  # $0.10 minimum
    
    # IV Preferences
    IV_PREFERENCE = os.getenv("IV_PREFERENCE", "low")  # "low", "high", "any"
    MAX_IV_PERCENTILE = int(os.getenv("MAX_IV_PERCENTILE", 50))  # Buy when IV < 50th percentile
    MIN_IV_PERCENTILE = int(os.getenv("MIN_IV_PERCENTILE", 10))   # Don't buy if IV < 10th percentile
    
    # Trading Hours (ET)
    MARKET_OPEN_HOUR = 9
    MARKET_OPEN_MINUTE = 30
    MARKET_CLOSE_HOUR = 16
    MARKET_CLOSE_MINUTE = 0
    
    # IBKR Commission Structure
    COMMISSION_PER_CONTRACT = 0.65
    COMMISSION_PER_TRADE = 0.50
    MIN_COMMISSION = 1.00
    
    # Data Quality Settings
    MAX_DATA_AGE_MINUTES = 5  # Data must be fresh
    PRICE_VALIDATION_TOLERANCE = 0.05  # 5% price difference tolerance
    
    # Learning Parameters
    MIN_TRADES_FOR_LEARNING = 10  # Need 10 trades before adjusting weights
    LEARNING_RATE = 0.1  # How fast to adjust signal weights
    
    @classmethod
    def get_position_size(cls, account_balance: float) -> float:
        """Calculate maximum position size based on account balance"""
        max_per_trade = account_balance * cls.MAX_POSITION_SIZE_PCT
        
        # Adaptive sizing based on account growth
        if account_balance <= 1500:
            return min(200, max_per_trade)
        elif account_balance <= 3000:
            return min(400, max_per_trade * 0.75)  # More conservative as we grow
        else:
            return min(600, max_per_trade * 0.60)  # Even more conservative
    
    @classmethod
    def get_contracts_for_trade(cls, option_price: float, account_balance: float) -> int:
        """Calculate number of contracts to trade"""
        max_investment = cls.get_position_size(account_balance)
        
        # Cost per contract (include commission estimate)
        cost_per_contract = (option_price * 100) + (cls.COMMISSION_PER_CONTRACT * 2)  # Round trip
        
        # Maximum contracts we can afford
        max_contracts = int(max_investment / cost_per_contract)
        
        # Conservative: Start with 1-2 contracts max
        return min(max_contracts, 2) if max_contracts > 0 else 0
    
    @classmethod
    def calculate_commission(cls, action: str, contracts: int) -> float:
        """Calculate IBKR commission for options trade"""
        base_commission = (cls.COMMISSION_PER_CONTRACT * contracts) + cls.COMMISSION_PER_TRADE
        return max(base_commission, cls.MIN_COMMISSION)
    
    @classmethod
    def is_market_hours(cls) -> bool:
        """Check if market is currently open"""
        from datetime import datetime
        import pytz
        
        # Get current ET time
        et = pytz.timezone('US/Eastern')
        now = datetime.now(et)
        
        # Check if weekday (Monday=0, Sunday=6)
        if now.weekday() >= 5:  # Weekend
            return False
        
        # Check market hours
        market_open = now.replace(hour=cls.MARKET_OPEN_HOUR, minute=cls.MARKET_OPEN_MINUTE, second=0, microsecond=0)
        market_close = now.replace(hour=cls.MARKET_CLOSE_HOUR, minute=cls.MARKET_CLOSE_MINUTE, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    
    @classmethod
    def update_settings(cls, **kwargs):
        """Update settings dynamically for testing different strategies"""
        for key, value in kwargs.items():
            if hasattr(cls, key.upper()):
                setattr(cls, key.upper(), value)
                print(f"✅ Updated {key.upper()} = {value}")
            else:
                print(f"❌ Unknown setting: {key}")

# Create global config instance
options_config = OptionsConfig()

# Example usage:
if __name__ == "__main__":
    print("🎯 Options Configuration")
    print(f"Expiration Preference: {options_config.EXPIRATION_PREFERENCE}")
    print(f"Strike Selection: {options_config.STRIKE_SELECTION}")
    print(f"Max Position Size: {options_config.MAX_POSITION_SIZE_PCT:.0%}")
    print(f"Market Hours: {options_config.is_market_hours()}")
    
    # Test position sizing
    print(f"\nPosition sizing for $1000 account: ${options_config.get_position_size(1000)}")
    print(f"Position sizing for $3000 account: ${options_config.get_position_size(3000)}")
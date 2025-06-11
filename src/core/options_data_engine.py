"""
Real Options Data Engine
Fetches, validates, and manages real RTX options data
Ensures 100% accuracy for learning system
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

from config.options_config import options_config

class OptionsDataEngine:
    """Real-time options data with validation and quality checks"""
    
    def __init__(self, symbol: str = "RTX"):
        self.symbol = symbol
        self.ticker = yf.Ticker(symbol)
        self.last_update = None
        self.cached_chain = {}
        
    def get_real_options_chain(self, force_refresh: bool = False) -> Dict:
        """Get validated, real options chain data"""
        
        # Check if we need fresh data
        if (not force_refresh and 
            self.last_update and 
            datetime.now() - self.last_update < timedelta(minutes=options_config.MAX_DATA_AGE_MINUTES)):
            logger.info("📊 Using cached options data")
            return self.cached_chain
        
        if not options_config.is_market_hours():
            logger.warning("⏰ Market closed - options data may be stale")
        
        logger.info(f"📥 Fetching real {self.symbol} options chain...")
        
        try:
            # Get all available expiration dates
            options_dates = self.ticker.options
            
            if not options_dates:
                logger.error(f"❌ No options available for {self.symbol}")
                return {}
            
            validated_chain = {}
            total_contracts = 0
            
            for exp_date in options_dates:
                # Skip if expiration doesn't meet our criteria
                if not self._is_valid_expiration(exp_date):
                    continue
                
                try:
                    # Get options chain for this expiration
                    chain = self.ticker.option_chain(exp_date)
                    
                    # Process calls
                    for _, option in chain.calls.iterrows():
                        if self._validate_option_data(option, "call"):
                            contract_symbol = self._generate_contract_symbol(option, exp_date, "C")
                            validated_chain[contract_symbol] = self._format_option_data(option, exp_date, "call")
                            total_contracts += 1
                    
                    # Process puts
                    for _, option in chain.puts.iterrows():
                        if self._validate_option_data(option, "put"):
                            contract_symbol = self._generate_contract_symbol(option, exp_date, "P")
                            validated_chain[contract_symbol] = self._format_option_data(option, exp_date, "put")
                            total_contracts += 1
                            
                except Exception as e:
                    logger.warning(f"⚠️ Error processing {exp_date}: {e}")
                    continue
            
            self.cached_chain = validated_chain
            self.last_update = datetime.now()
            
            logger.success(f"✅ Loaded {total_contracts} validated options contracts")
            return validated_chain
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch options data: {e}")
            return {}
    
    def _is_valid_expiration(self, exp_date: str) -> bool:
        """Check if expiration date meets our criteria"""
        try:
            exp_datetime = datetime.strptime(exp_date, "%Y-%m-%d")
            days_to_expiry = (exp_datetime - datetime.now()).days
            
            # Check DTE limits
            if days_to_expiry < options_config.MIN_DAYS_TO_EXPIRY:
                return False
            if days_to_expiry > options_config.MAX_DAYS_TO_EXPIRY:
                return False
            
            # Check expiration preference
            if options_config.EXPIRATION_PREFERENCE == "weekly":
                # Weekly options typically expire on Fridays
                return days_to_expiry <= 7
            elif options_config.EXPIRATION_PREFERENCE == "monthly":
                # Monthly options typically expire on 3rd Friday
                return days_to_expiry > 7
            # "both" allows all valid DTEs
            
            return True
            
        except Exception:
            return False
    
    def _validate_option_data(self, option: pd.Series, option_type: str) -> bool:
        """Rigorous validation to ensure option data is real and tradeable"""
        
        try:
            # Basic price validation
            if pd.isna(option['bid']) or option['bid'] <= 0:
                return False
            
            if pd.isna(option['ask']) or option['ask'] <= option['bid']:
                return False
            
            if pd.isna(option['lastPrice']) or option['lastPrice'] <= 0:
                return False
            
            # Minimum price check
            if option['lastPrice'] < options_config.MIN_OPTION_PRICE:
                return False
            
            # Liquidity checks
            volume = option.get('volume', 0) or 0
            open_interest = option.get('openInterest', 0) or 0
            
            if volume < options_config.MIN_VOLUME and open_interest < options_config.MIN_OPEN_INTEREST:
                return False
            
            # Spread check
            mid_price = (option['bid'] + option['ask']) / 2
            spread = option['ask'] - option['bid']
            spread_pct = spread / mid_price if mid_price > 0 else 1
            
            if spread_pct > options_config.MAX_BID_ASK_SPREAD_PCT:
                return False
            
            # IV validation
            if pd.isna(option['impliedVolatility']) or option['impliedVolatility'] <= 0:
                return False
            
            # Reasonable IV check (0.5% to 200%)
            if option['impliedVolatility'] < 0.005 or option['impliedVolatility'] > 2.0:
                return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Validation error: {e}")
            return False
    
    def _generate_contract_symbol(self, option: pd.Series, exp_date: str, call_put: str) -> str:
        """Generate standard option contract symbol"""
        # Format: RTX240615C125000 (RTX Jun 15 2024 $125 Call)
        try:
            exp_datetime = datetime.strptime(exp_date, "%Y-%m-%d")
            exp_str = exp_datetime.strftime("%y%m%d")
            strike_str = f"{int(option['strike'] * 1000):08d}"
            
            return f"{self.symbol}{exp_str}{call_put}{strike_str}"
        except:
            return f"{self.symbol}_{exp_date}_{call_put}_{option['strike']}"
    
    def _format_option_data(self, option: pd.Series, exp_date: str, option_type: str) -> Dict:
        """Format option data for our system"""
        return {
            'type': option_type,
            'strike': float(option['strike']),
            'expiry': exp_date,
            'bid': float(option['bid']),
            'ask': float(option['ask']),
            'last': float(option['lastPrice']),
            'volume': int(option.get('volume', 0) or 0),
            'openInterest': int(option.get('openInterest', 0) or 0),
            'impliedVolatility': float(option['impliedVolatility']),
            'delta': float(option.get('delta', 0) or 0),
            'gamma': float(option.get('gamma', 0) or 0),
            'theta': float(option.get('theta', 0) or 0),
            'vega': float(option.get('vega', 0) or 0),
            'timestamp': datetime.now().isoformat(),
            'mid_price': (float(option['bid']) + float(option['ask'])) / 2,
            'spread_pct': ((float(option['ask']) - float(option['bid'])) / 
                          ((float(option['ask']) + float(option['bid'])) / 2)) if option['bid'] > 0 else 0
        }
    
    def get_best_options_for_direction(self, direction: str, confidence: float, account_balance: float) -> List[Dict]:
        """Find the best options for predicted direction"""
        
        options_chain = self.get_real_options_chain()
        if not options_chain:
            return []
        
        # Get current stock price for strike selection
        stock_price = self.get_current_stock_price()
        if not stock_price:
            return []
        
        # Filter options by direction
        filtered_options = []
        
        for contract_symbol, option_data in options_chain.items():
            # Direction filtering
            if direction == "BUY" and option_data['type'] != 'call':
                continue
            if direction == "SELL" and option_data['type'] != 'put':
                continue
            if direction == "HOLD":
                continue
            
            # Strike selection logic
            if not self._is_suitable_strike(option_data['strike'], stock_price, direction, confidence):
                continue
            
            # Affordability check
            max_investment = options_config.get_position_size(account_balance)
            option_cost = option_data['ask'] * 100  # Cost for 1 contract
            
            if option_cost > max_investment:
                continue
            
            # Add to candidates
            option_data['contract_symbol'] = contract_symbol
            option_data['cost_per_contract'] = option_cost
            option_data['max_contracts'] = options_config.get_contracts_for_trade(option_data['ask'], account_balance)
            
            filtered_options.append(option_data)
        
        # Sort by attractiveness (combination of liquidity, pricing, Greeks)
        filtered_options.sort(key=self._calculate_option_score, reverse=True)
        
        return filtered_options[:5]  # Return top 5 candidates
    
    def _is_suitable_strike(self, strike: float, stock_price: float, direction: str, confidence: float) -> bool:
        """Determine if strike price is suitable for our strategy"""
        
        strike_selection = options_config.STRIKE_SELECTION
        
        if strike_selection == "atm":
            # At-the-money: within 2% of current price
            return abs(strike - stock_price) / stock_price <= 0.02
        
        elif strike_selection == "otm":
            if direction == "BUY":  # OTM calls
                return strike > stock_price * 1.01  # At least 1% OTM
            else:  # OTM puts
                return strike < stock_price * 0.99
        
        elif strike_selection == "itm":
            if direction == "BUY":  # ITM calls
                return strike < stock_price * 0.99
            else:  # ITM puts
                return strike > stock_price * 1.01
        
        elif strike_selection == "adaptive":
            # Higher confidence = more aggressive strikes
            if confidence >= 0.8:
                # High confidence: can go OTM for more leverage
                if direction == "BUY":
                    return stock_price * 1.01 <= strike <= stock_price * 1.05
                else:
                    return stock_price * 0.95 <= strike <= stock_price * 0.99
            else:
                # Lower confidence: stick to ATM/ITM
                return abs(strike - stock_price) / stock_price <= 0.02
        
        return True
    
    def _calculate_option_score(self, option: Dict) -> float:
        """Calculate attractiveness score for option selection"""
        score = 0
        
        # Liquidity score (30% weight)
        volume_score = min(option['volume'] / 1000, 1) * 0.3
        oi_score = min(option['openInterest'] / 5000, 1) * 0.3
        
        # Spread score (20% weight) - lower spread is better
        spread_score = max(0, (0.2 - option['spread_pct']) / 0.2) * 0.2
        
        # Greeks score (30% weight)
        delta_score = abs(option.get('delta', 0)) * 0.15  # Higher delta for directional bets
        gamma_score = option.get('gamma', 0) * 100 * 0.15  # Positive gamma
        
        # Price score (20% weight) - not too cheap, not too expensive
        price = option['mid_price']
        if 0.5 <= price <= 5.0:  # Sweet spot for options pricing
            price_score = 0.2
        else:
            price_score = 0.1
        
        return volume_score + oi_score + spread_score + delta_score + gamma_score + price_score
    
    def get_current_stock_price(self) -> Optional[float]:
        """Get current RTX stock price"""
        try:
            data = self.ticker.history(period="1d", interval="1m")
            if not data.empty:
                return float(data['Close'].iloc[-1])
        except Exception as e:
            logger.error(f"❌ Failed to get stock price: {e}")
        return None
    
    def get_option_price_realtime(self, contract_symbol: str) -> Optional[Dict]:
        """Get real-time price for specific option contract"""
        options_chain = self.get_real_options_chain(force_refresh=True)
        return options_chain.get(contract_symbol)

# Create global instance
options_data_engine = OptionsDataEngine("RTX")

if __name__ == "__main__":
    # Test the options data engine
    logger.info("🧪 Testing Options Data Engine...")
    
    engine = OptionsDataEngine("RTX")
    
    # Test options chain fetch
    chain = engine.get_real_options_chain()
    print(f"📊 Found {len(chain)} tradeable options")
    
    # Test best options selection
    best_calls = engine.get_best_options_for_direction("BUY", 0.8, 1000)
    print(f"🎯 Top call options: {len(best_calls)}")
    
    if best_calls:
        best_option = best_calls[0]
        print(f"Best option: {best_option['contract_symbol']}")
        print(f"Strike: ${best_option['strike']}")
        print(f"Cost: ${best_option['cost_per_contract']:.2f}")
        print(f"IV: {best_option['impliedVolatility']:.1%}")
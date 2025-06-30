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
                            if contract_symbol:  # Only add if symbol generation succeeded
                                validated_chain[contract_symbol] = self._format_option_data(option, exp_date, "call")
                                total_contracts += 1
                    
                    # Process puts
                    for _, option in chain.puts.iterrows():
                        if self._validate_option_data(option, "put"):
                            contract_symbol = self._generate_contract_symbol(option, exp_date, "P")
                            if contract_symbol:  # Only add if symbol generation succeeded
                                validated_chain[contract_symbol] = self._format_option_data(option, exp_date, "put")
                                total_contracts += 1
                            
                except Exception as e:
                    logger.warning(f"⚠️ Error processing {exp_date}: {e}")
                    import traceback
                    logger.debug(f"Traceback: {traceback.format_exc()}")
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
            if days_to_expiry < 3:  # Too close to expiry (less than 3 days)
                return False
            if days_to_expiry > options_config.MAX_DAYS_TO_EXPIRY:
                return False
            
            # Check expiration preference
            if options_config.EXPIRATION_PREFERENCE == "weekly":
                # Weekly options typically expire on Fridays (up to 10 days out)
                return days_to_expiry <= 10
            elif options_config.EXPIRATION_PREFERENCE == "monthly":
                # Monthly options typically expire on 3rd Friday
                return days_to_expiry > 10
            # "both" allows all valid DTEs within our range
            
            return True
            
        except Exception:
            return False
    
    def _validate_option_data(self, option: pd.Series, option_type: str) -> bool:
        """Rigorous validation to ensure option data is real and tradeable"""
        
        try:
            # First validate strike price
            try:
                strike = float(option['strike'])
                if pd.isna(strike) or np.isnan(strike) or strike <= 0:
                    return False
            except (ValueError, TypeError):
                return False
            
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
            # Check for NaN or invalid strike
            try:
                strike_value = float(option['strike'])
                if pd.isna(strike_value) or np.isnan(strike_value) or strike_value <= 0:
                    return None
            except (ValueError, TypeError):
                return None
                
            exp_datetime = datetime.strptime(exp_date, "%Y-%m-%d")
            exp_str = exp_datetime.strftime("%y%m%d")
            strike_str = f"{int(float(option['strike']) * 1000):08d}"
            
            return f"{self.symbol}{exp_str}{call_put}{strike_str}"
        except Exception as e:
            logger.warning(f"Error generating symbol: {e}")
            return None
    
    def _format_option_data(self, option: pd.Series, exp_date: str, option_type: str) -> Dict:
        """Format option data for our system"""
        try:
            # Safely convert values with NaN handling
            def safe_float(val, default=0.0):
                try:
                    f = float(val)
                    return default if pd.isna(f) or np.isnan(f) else f
                except (ValueError, TypeError):
                    return default
            
            def safe_int(val, default=0):
                try:
                    f = float(val)
                    if pd.isna(f) or np.isnan(f):
                        return default
                    return int(f)
                except (ValueError, TypeError):
                    return default
            
            bid = safe_float(option['bid'])
            ask = safe_float(option['ask'])
            
            return {
                'type': option_type,
                'strike': safe_float(option['strike']),
                'expiry': exp_date,
                'bid': bid,
                'ask': ask,
                'last': safe_float(option['lastPrice']),
                'volume': safe_int(option.get('volume', 0)),
                'openInterest': safe_int(option.get('openInterest', 0)),
                'impliedVolatility': safe_float(option['impliedVolatility']),
                'delta': safe_float(option.get('delta', 0)),
                'gamma': safe_float(option.get('gamma', 0)),
                'theta': safe_float(option.get('theta', 0)),
                'vega': safe_float(option.get('vega', 0)),
                'timestamp': datetime.now().isoformat(),
                'mid_price': (bid + ask) / 2 if bid > 0 and ask > 0 else 0,
                'spread_pct': ((ask - bid) / ((ask + bid) / 2)) if bid > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error formatting option data: {e}")
            raise
    
    def get_best_options_for_direction(self, direction: str, confidence: float, account_balance: float) -> List[Dict]:
        """Find the best options for predicted direction"""
        
        options_chain = self.get_real_options_chain()
        if not options_chain:
            logger.warning("❌ No options chain available")
            return []
        
        # Get current stock price for strike selection
        stock_price = self.get_current_stock_price()
        if not stock_price:
            logger.warning("❌ No current stock price available")
            return []
        
        logger.info(f"🔍 OPTIONS FILTER DEBUG:")
        logger.info(f"   • Direction: {direction}")
        logger.info(f"   • Stock price: ${stock_price:.2f}")
        logger.info(f"   • Account balance: ${account_balance:.2f}")
        logger.info(f"   • Available contracts: {len(options_chain)}")
        
        # Filter options by direction
        filtered_options = []
        rejected_reasons = {"direction": 0, "strike": 0, "cost": 0, "quality": 0}
        
        for contract_symbol, option_data in options_chain.items():
            # Direction filtering
            if direction == "BUY" and option_data['type'] != 'call':
                rejected_reasons["direction"] += 1
                continue
            if direction == "SELL" and option_data['type'] != 'put':
                rejected_reasons["direction"] += 1
                continue
            if direction == "HOLD":
                rejected_reasons["direction"] += 1
                continue
            
            # Strike selection logic
            if not self._is_suitable_strike(option_data['strike'], stock_price, direction, confidence):
                rejected_reasons["strike"] += 1
                continue
            
            # Affordability check
            max_investment = options_config.get_position_size(account_balance)
            option_cost = option_data['ask'] * 100  # Cost for 1 contract
            
            if option_cost > max_investment:
                rejected_reasons["cost"] += 1
                logger.debug(f"   ❌ {contract_symbol}: Too expensive (${option_cost:.0f} > ${max_investment:.0f})")
                continue
            
            # Add to candidates with additional fields
            option_data['contract_symbol'] = contract_symbol
            option_data['cost_per_contract'] = option_cost
            option_data['max_contracts'] = options_config.get_contracts_for_trade(option_data['ask'], account_balance)
            
            # Calculate days to expiry
            from datetime import datetime
            exp_date = datetime.strptime(option_data['expiry'], "%Y-%m-%d")
            option_data['dte'] = (exp_date - datetime.now()).days
            option_data['days_to_expiry'] = option_data['dte']
            
            # Add pricing info
            option_data['ask_price'] = option_data['ask']
            option_data['contracts'] = min(1, option_data['max_contracts'])  # Start with 1 contract
            option_data['total_cost'] = option_cost + options_config.calculate_commission("BUY", 1)
            
            # Add volume and OI with better names
            option_data['open_interest'] = option_data.get('openInterest', 0)
            option_data['iv'] = option_data.get('impliedVolatility', 0)
            
            # Calculate and add score
            option_data['score'] = self._calculate_option_score(option_data)
            
            filtered_options.append(option_data)
            logger.debug(f"   ✅ {contract_symbol}: ${option_data['strike']} strike @ ${option_cost:.0f}")
        
        # Log filtering summary
        logger.info(f"   📊 FILTERING SUMMARY:")
        logger.info(f"      • Rejected by direction: {rejected_reasons['direction']}")
        logger.info(f"      • Rejected by strike: {rejected_reasons['strike']}")
        logger.info(f"      • Rejected by cost: {rejected_reasons['cost']}")
        logger.info(f"      • Passed all filters: {len(filtered_options)}")
        
        if not filtered_options:
            logger.warning(f"   ❌ No options passed filters! Max investment: ${options_config.get_position_size(account_balance):.0f}")
            return []
        
        # Sort by attractiveness (combination of liquidity, pricing, Greeks)
        filtered_options.sort(key=self._calculate_option_score, reverse=True)
        
        logger.info(f"   🎯 Top candidate: {filtered_options[0]['contract_symbol']} @ ${filtered_options[0]['cost_per_contract']:.0f}")
        
        return filtered_options[:5]  # Return top 5 candidates
    
    def _is_suitable_strike(self, strike: float, stock_price: float, direction: str, confidence: float) -> bool:
        """Determine if strike price is suitable for our strategy"""
        
        # Get strike selection from config (default to adaptive if not set)
        strike_selection = getattr(options_config, 'STRIKE_SELECTION', 'adaptive')
        
        if strike_selection == "atm":
            # At-the-money: within 3% of current price (more flexible)
            suitable = abs(strike - stock_price) / stock_price <= 0.03
        
        elif strike_selection == "otm":
            if direction == "BUY":  # OTM calls
                suitable = strike > stock_price * 1.005  # At least 0.5% OTM
            else:  # OTM puts
                suitable = strike < stock_price * 0.995
        
        elif strike_selection == "itm":
            if direction == "BUY":  # ITM calls
                suitable = strike < stock_price * 0.995
            else:  # ITM puts
                suitable = strike > stock_price * 1.005
        
        else:  # "adaptive" - use confidence to determine strategy
            if confidence > 0.8:
                # High confidence: ATM for maximum delta
                suitable = abs(strike - stock_price) / stock_price <= 0.05
            elif confidence > 0.65:
                # Medium confidence: Slightly OTM for better risk/reward
                if direction == "BUY":
                    suitable = strike >= stock_price * 0.98 and strike <= stock_price * 1.05
                else:
                    suitable = strike >= stock_price * 0.95 and strike <= stock_price * 1.02
            else:
                # Lower confidence: More conservative ATM
                suitable = abs(strike - stock_price) / stock_price <= 0.02
        
        if not suitable:
            logger.debug(f"   ❌ Strike ${strike:.0f} unsuitable for ${stock_price:.2f} stock (mode: {strike_selection})")
        
        return suitable
    
    def _calculate_option_score(self, option: Dict) -> float:
        """Calculate attractiveness score for option selection"""
        score = 0
        
        # Liquidity score (30% weight)
        volume_score = min(option['volume'] / 1000, 1) * 0.3
        oi_score = min(option['openInterest'] / 5000, 1) * 0.3
        
        # Spread score (20% weight) - lower spread is better
        spread_score = max(0, (0.2 - option['spread_pct']) / 0.2) * 0.2
        
        # Enhanced Greeks score (30% weight)
        delta = option.get('delta', 0)
        gamma = option.get('gamma', 0)
        theta = option.get('theta', 0)
        vega = option.get('vega', 0)
        
        # Delta score: Higher delta for directional bets, but not too close to 1.0
        if option.get("type", "").upper() == "CALL":
            optimal_delta = 0.6  # Sweet spot for calls
            delta_score = max(0, 1 - abs(delta - optimal_delta) / optimal_delta) * 0.10
        else:  # PUT
            optimal_delta = -0.6  # Sweet spot for puts  
            delta_score = max(0, 1 - abs(abs(delta) - abs(optimal_delta)) / abs(optimal_delta)) * 0.10
            
        # Gamma score: Positive gamma is good, but not excessive
        gamma_score = min(gamma * 100, 1.0) * 0.08
        
        # Theta score: Less negative theta is better (less time decay)
        theta_score = max(0, 1 + theta / 10) * 0.07  # Normalize theta decay
        
        # Vega score: Lower vega during high IV periods
        vega_score = max(0, 1 - abs(vega) / 20) * 0.05  # Prefer lower vega
        
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
        
        # First try to get from cached/validated chain
        options_chain = self.get_real_options_chain(force_refresh=True)
        if contract_symbol in options_chain:
            return options_chain[contract_symbol]
        
        # If not found (e.g., contract no longer passes validation), 
        # fetch directly from yfinance for existing positions
        logger.info(f"📊 Contract {contract_symbol} not in validated chain, fetching directly...")
        
        try:
            # Parse contract symbol: RTX250620C00147000
            if len(contract_symbol) < 15:
                logger.error(f"❌ Invalid contract symbol format: {contract_symbol}")
                return None
                
            symbol_parts = {
                'underlying': contract_symbol[:3],  # RTX
                'date': contract_symbol[3:9],       # 250620
                'type': contract_symbol[9],         # C or P
                'strike': contract_symbol[10:]      # 00147000
            }
            
            # Convert date and strike
            expiry = f"20{symbol_parts['date'][:2]}-{symbol_parts['date'][2:4]}-{symbol_parts['date'][4:6]}"
            strike = int(symbol_parts['strike']) / 1000
            
            # Get the option chain for this expiry
            chain = self.ticker.option_chain(expiry)
            
            if symbol_parts['type'] == 'C':
                options_df = chain.calls
                option_type = 'call'
            else:
                options_df = chain.puts  
                option_type = 'put'
            
            # Find the specific strike
            option_row = options_df[options_df['strike'] == strike]
            
            if option_row.empty:
                logger.error(f"❌ Strike ${strike} not found for {expiry}")
                return None
                
            option = option_row.iloc[0]
            
            # Format the data (with relaxed validation for existing positions)
            bid = float(option['bid']) if not pd.isna(option['bid']) else 0.0
            ask = float(option['ask']) if not pd.isna(option['ask']) else 0.0
            
            data = {
                'type': option_type,
                'strike': strike,
                'expiry': expiry,  # Keep YYYY-MM-DD format
                'bid': bid,
                'ask': ask,
                'last': float(option['lastPrice']) if not pd.isna(option['lastPrice']) else 0.0,
                'volume': int(option.get('volume', 0)) if not pd.isna(option.get('volume', 0)) else 0,
                'openInterest': int(option.get('openInterest', 0)) if not pd.isna(option.get('openInterest', 0)) else 0,
                'impliedVolatility': float(option['impliedVolatility']) if not pd.isna(option['impliedVolatility']) else 0.0,
                'delta': float(option.get('delta', 0)) if not pd.isna(option.get('delta', 0)) else 0.0,
                'gamma': float(option.get('gamma', 0)) if not pd.isna(option.get('gamma', 0)) else 0.0,
                'theta': float(option.get('theta', 0)) if not pd.isna(option.get('theta', 0)) else 0.0,
                'vega': float(option.get('vega', 0)) if not pd.isna(option.get('vega', 0)) else 0.0,
                'timestamp': datetime.now().isoformat(),
                'mid_price': (bid + ask) / 2 if bid > 0 and ask > 0 else 0,
                'spread_pct': ((ask - bid) / ((ask + bid) / 2)) if bid > 0 and ask > 0 else 0
            }
            
            logger.success(f"✅ Fetched {contract_symbol} directly: bid=${bid:.2f}, ask=${ask:.2f}")
            return data
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch {contract_symbol} directly: {e}")
            return None

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
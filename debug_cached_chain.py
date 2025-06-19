#!/usr/bin/env python3
"""Debug cached options chain"""

from loguru import logger
from src.core.options_data_engine import options_data_engine
from datetime import datetime

def debug_cached_chain():
    """Debug what's in the cached options chain"""
    
    logger.info("🔍 Debugging cached options chain...")
    
    # Force refresh
    chain = options_data_engine.get_real_options_chain(force_refresh=True)
    
    logger.info(f"📊 Total contracts: {len(chain)}")
    
    # Find contracts expiring on June 20
    target_date = "2025-06-20"
    june20_contracts = []
    
    for symbol, data in chain.items():
        if data['expiry'] == target_date:
            june20_contracts.append((symbol, data))
    
    logger.info(f"📅 Contracts expiring {target_date}: {len(june20_contracts)}")
    
    if june20_contracts:
        for symbol, data in june20_contracts:
            logger.info(f"   {symbol}: ${data['strike']} {data['type']}")
    
    # Check if our specific contract passes validation
    test_contract = "RTX250620C00147000"
    logger.info(f"\n🎯 Testing validation for {test_contract}...")
    
    # Get the raw data directly
    import yfinance as yf
    ticker = yf.Ticker("RTX")
    
    try:
        chain_data = ticker.option_chain("2025-06-20")
        calls = chain_data.calls
        
        # Find $147 call
        call_147 = calls[calls['strike'] == 147.0]
        
        if not call_147.empty:
            option = call_147.iloc[0]
            logger.info(f"📊 Raw data for $147 call:")
            logger.info(f"   Bid: ${option['bid']:.2f}")
            logger.info(f"   Ask: ${option['ask']:.2f}")
            logger.info(f"   Last: ${option['lastPrice']:.2f}")
            logger.info(f"   Volume: {option['volume']}")
            logger.info(f"   OI: {option['openInterest']}")
            logger.info(f"   IV: {option['impliedVolatility']:.3f}")
            
            # Test validation manually
            from src.core.options_data_engine import OptionsDataEngine
            engine = OptionsDataEngine()
            
            is_valid = engine._validate_option_data(option, "call")
            logger.info(f"   Validation result: {'✅ PASS' if is_valid else '❌ FAIL'}")
            
            # Check specific validation points
            logger.info(f"\n🔍 Validation details:")
            logger.info(f"   Strike valid: {not pd.isna(option['strike']) and option['strike'] > 0}")
            logger.info(f"   Bid valid: {not pd.isna(option['bid']) and option['bid'] > 0}")
            logger.info(f"   Ask valid: {not pd.isna(option['ask']) and option['ask'] > option['bid']}")
            logger.info(f"   Last valid: {not pd.isna(option['lastPrice']) and option['lastPrice'] > 0}")
            
            # Check price minimum
            from config.options_config import options_config
            min_price = getattr(options_config, 'MIN_OPTION_PRICE', 0.05)
            logger.info(f"   Min price (${min_price}): {'✅' if option['lastPrice'] >= min_price else '❌'}")
            
            # Check liquidity
            volume = option.get('volume', 0) or 0
            oi = option.get('openInterest', 0) or 0
            min_vol = getattr(options_config, 'MIN_VOLUME', 50)
            min_oi = getattr(options_config, 'MIN_OPEN_INTEREST', 100)
            
            logger.info(f"   Volume ({volume}) >= {min_vol}: {'✅' if volume >= min_vol else '❌'}")
            logger.info(f"   OI ({oi}) >= {min_oi}: {'✅' if oi >= min_oi else '❌'}")
            logger.info(f"   Combined liquidity: {'✅' if volume >= min_vol or oi >= min_oi else '❌'}")
            
            # Check spread
            if option['bid'] > 0 and option['ask'] > option['bid']:
                mid_price = (option['bid'] + option['ask']) / 2
                spread = option['ask'] - option['bid']
                spread_pct = spread / mid_price
                max_spread = getattr(options_config, 'MAX_BID_ASK_SPREAD_PCT', 0.20)
                logger.info(f"   Spread {spread_pct:.2%} <= {max_spread:.0%}: {'✅' if spread_pct <= max_spread else '❌'}")
            
            # Check expiry validation
            from datetime import datetime, timedelta
            exp_datetime = datetime.strptime("2025-06-20", "%Y-%m-%d")
            days_to_expiry = (exp_datetime - datetime.now()).days
            logger.info(f"   Days to expiry: {days_to_expiry}")
            logger.info(f"   DTE >= 3: {'✅' if days_to_expiry >= 3 else '❌'}")
            
        else:
            logger.error(f"❌ Could not find $147 call for 2025-06-20")
            
    except Exception as e:
        logger.error(f"❌ Error getting raw data: {e}")

if __name__ == "__main__":
    import pandas as pd
    debug_cached_chain()
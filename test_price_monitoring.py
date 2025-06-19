#!/usr/bin/env python3
"""Test price monitoring for options"""

from loguru import logger
from src.core.options_data_engine import options_data_engine
from src.core.options_paper_trader import options_paper_trader
import time

def test_price_monitoring():
    """Test getting real-time prices for open positions"""
    
    logger.info("🧪 Testing price monitoring for open positions...")
    
    # Get open positions
    open_positions = options_paper_trader.open_positions
    logger.info(f"📊 Found {len(open_positions)} open positions")
    
    if not open_positions:
        logger.warning("No open positions to test")
        return
    
    # Test each position
    for prediction_id, position in open_positions.items():
        prediction = position['prediction']
        contract_symbol = prediction['contract_symbol']
        
        logger.info(f"\n🔍 Testing position: {contract_symbol}")
        logger.info(f"   Entry price: ${position['execution']['execution_price']:.2f}")
        
        # Method 1: Direct API call with force refresh
        logger.info("   Method 1: Force refresh entire chain...")
        start_time = time.time()
        current_data = options_data_engine.get_option_price_realtime(contract_symbol)
        elapsed = time.time() - start_time
        
        if current_data:
            logger.success(f"   ✅ Got price via force refresh in {elapsed:.2f}s")
            logger.info(f"   Current bid: ${current_data['bid']:.2f}")
            logger.info(f"   Current ask: ${current_data['ask']:.2f}")
            logger.info(f"   Current mid: ${current_data['mid_price']:.2f}")
        else:
            logger.error(f"   ❌ Failed to get price via force refresh")
            
        # Method 2: Try to get specific contract data
        logger.info("\n   Method 2: Direct yfinance lookup...")
        try:
            import yfinance as yf
            
            # Parse contract symbol: RTX250620C00147000
            # Format: RTX 250620 C 00147000
            symbol_parts = {
                'underlying': contract_symbol[:3],  # RTX
                'date': contract_symbol[3:9],       # 250620
                'type': contract_symbol[9],         # C
                'strike': contract_symbol[10:]      # 00147000
            }
            
            # Convert date and strike
            expiry = f"20{symbol_parts['date'][:2]}-{symbol_parts['date'][2:4]}-{symbol_parts['date'][4:6]}"
            strike = int(symbol_parts['strike']) / 1000
            
            logger.info(f"   Parsed: {symbol_parts['underlying']} {expiry} ${strike} {symbol_parts['type']}")
            
            # Get the ticker
            ticker = yf.Ticker(symbol_parts['underlying'])
            
            # Get option chain for that expiry
            try:
                chain = ticker.option_chain(expiry)
                
                if symbol_parts['type'] == 'C':
                    options_df = chain.calls
                else:
                    options_df = chain.puts
                
                # Find the specific strike
                option_row = options_df[options_df['strike'] == strike]
                
                if not option_row.empty:
                    option_data = option_row.iloc[0]
                    logger.success(f"   ✅ Found via direct lookup!")
                    logger.info(f"   Bid: ${option_data['bid']:.2f}")
                    logger.info(f"   Ask: ${option_data['ask']:.2f}")
                    logger.info(f"   Last: ${option_data['lastPrice']:.2f}")
                    logger.info(f"   Volume: {option_data['volume']}")
                else:
                    logger.error(f"   ❌ Strike ${strike} not found in chain")
                    
            except Exception as e:
                logger.error(f"   ❌ Failed to get chain for {expiry}: {e}")
                
        except Exception as e:
            logger.error(f"   ❌ Direct lookup failed: {e}")
            
        # Method 3: Check if contract is still in cached chain
        logger.info("\n   Method 3: Check cached chain...")
        cached_chain = options_data_engine.cached_chain
        
        if contract_symbol in cached_chain:
            logger.success(f"   ✅ Found in cached chain")
            cached_data = cached_chain[contract_symbol]
            logger.info(f"   Cached bid: ${cached_data['bid']:.2f}")
            logger.info(f"   Cached ask: ${cached_data['ask']:.2f}")
            logger.info(f"   Last update: {cached_data['timestamp']}")
        else:
            logger.error(f"   ❌ Not in cached chain")
            logger.info(f"   Cached contracts: {len(cached_chain)}")
            
            # Check if similar contracts exist
            similar = [c for c in cached_chain.keys() if c.startswith(contract_symbol[:9])]
            if similar:
                logger.info(f"   Similar contracts found: {similar[:3]}")

if __name__ == "__main__":
    test_price_monitoring()
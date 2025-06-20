print("🔍 DEBUGGING OPTIONS DATA ISSUE")
print("=" * 50)

import yfinance as yf
from datetime import datetime, timedelta

# Test if we can get RTX options
ticker = yf.Ticker("RTX")
print("\n📊 Testing RTX options data:")

try:
    # Get expiration dates
    expirations = ticker.options
    print(f"Available expirations: {len(expirations)}")
    if expirations:
        print(f"Next 3 expirations: {expirations[:3]}")
        
        # Try to get options chain for next expiration
        opt = ticker.option_chain(expirations[0])
        print(f"\nOptions for {expirations[0]}:")
        print(f"  Calls: {len(opt.calls)}")
        print(f"  Puts: {len(opt.puts)}")
        
        # Check current stock price
        hist = ticker.history(period="1d")
        current_price = hist['Close'].iloc[-1] if not hist.empty else None
        print(f"\nCurrent RTX price: ${current_price:.2f}" if current_price else "Price unavailable")
    else:
        print("❌ No expiration dates available\!")
        
except Exception as e:
    print(f"❌ Error getting options: {e}")

# Check if today is a special case
today = datetime.now()
print(f"\n📅 Today: {today.strftime('%Y-%m-%d %A')}")
if today.weekday() == 4:  # Friday
    print("⚠️ Friday - Options expiration day, limited availability")

# Check our options config
import sys
sys.path.append('.')
from config.options_config import options_config

print(f"\n⚙️ Options Configuration:")
print(f"  MIN_DTE: {options_config.MIN_DAYS_TO_EXPIRY}")
print(f"  MAX_DTE: {options_config.MAX_DAYS_TO_EXPIRY}")
print(f"  MIN_VOLUME: {options_config.MIN_VOLUME}")
print(f"  MAX_SPREAD: {options_config.MAX_BID_ASK_SPREAD_PCT:.0%}")

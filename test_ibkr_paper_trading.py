#!/usr/bin/env python3
"""
IBKR Paper Trading Test Script
Run this when you have TWS/Gateway running to test paper trading integration
"""
import asyncio
import socket
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.ibkr_manager import IBKRManager
from core.telegram_bot import telegram_bot

async def test_ibkr_connection():
    """Test if IBKR TWS/Gateway is running"""
    print("🔍 Testing IBKR Connection...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 7497))
        sock.close()
        
        if result == 0:
            print("✅ IBKR Paper Trading port (7497) is OPEN")
            print("   📋 TWS/Gateway is running!")
            return True
        else:
            print("❌ IBKR Paper Trading port (7497) is CLOSED")
            print("   📋 Please start TWS/Gateway first")
            return False
            
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return False

async def test_paper_trade():
    """Test a real paper trade with IBKR"""
    print("\n🧪 TESTING REAL PAPER TRADE")
    print("=" * 50)
    
    # Enable paper trading mode
    os.environ['TRADING_ENABLED'] = 'true'
    os.environ['PAPER_TRADING'] = 'true'
    os.environ['IBKR_REQUIRED'] = 'true'  # Require IBKR for real test
    
    ibkr = IBKRManager()
    
    print(f"📊 Trading Mode: {ibkr.trading_mode.get_mode_description()}")
    print(f"🏦 Paper Trading: {ibkr.trading_mode.PAPER_TRADING}")
    print(f"⚡ Trading Enabled: {ibkr.trading_mode.TRADING_ENABLED}")
    print()
    
    # Step 1: Connect to IBKR
    print("🔌 Step 1: Connecting to IBKR...")
    try:
        await ibkr.connect()
        print("✅ IBKR connection successful!")
        
        # Check connection status
        if ibkr.connected:
            print("✅ IBKR client connected and ready")
        else:
            print("❌ IBKR connection failed")
            return False
            
    except Exception as e:
        print(f"❌ IBKR connection error: {e}")
        print("📋 Make sure TWS/Gateway is running with API enabled")
        return False
    
    # Step 2: Get account info
    print("\n💰 Step 2: Getting Account Information...")
    try:
        account_info = await ibkr.get_account_summary()
        print(f"✅ Account connected: {account_info}")
    except Exception as e:
        print(f"⚠️ Account info error: {e}")
    
    # Step 3: Get live market data
    print("\n📊 Step 3: Getting Live RTX Market Data...")
    try:
        market_data = await ibkr.get_market_data('RTX')
        print(f"✅ RTX Market Data:")
        print(f"   Price: ${market_data['price']}")
        print(f"   Volume: {market_data['volume']:,}")
        print(f"   Source: {market_data['source']}")
    except Exception as e:
        print(f"❌ Market data error: {e}")
        return False
    
    # Step 4: Place paper trade
    print("\n📝 Step 4: Placing REAL Paper Trade...")
    order_data = {
        'symbol': 'RTX',
        'action': 'BUY',
        'quantity': 5,  # Small test trade
        'type': 'MKT'
    }
    
    estimated_cost = market_data['price'] * order_data['quantity']
    print(f"   Order: {order_data['action']} {order_data['quantity']} shares of {order_data['symbol']}")
    print(f"   Estimated Cost: ${estimated_cost:,.2f}")
    print(f"   Order Type: Market Order")
    print()
    
    try:
        print("🚀 Sending order to IBKR...")
        result = await ibkr.place_order(order_data)
        
        print(f"✅ PAPER TRADE EXECUTED!")
        print(f"   Status: {result.get('status')}")
        print(f"   Order ID: {result.get('order_id', 'N/A')}")
        print(f"   Timestamp: {result.get('timestamp')}")
        
        if result.get('status') == 'SUBMITTED':
            print("\n🎉 SUCCESS! Real paper trade placed with IBKR!")
            print("   📋 Check your TWS portfolio to see the position")
            
            # Send success notification
            if telegram_bot.enabled:
                await telegram_bot.send_message(
                    f"🎉 IBKR Paper Trade SUCCESS!\n\n"
                    f"📊 Order: {order_data['action']} {order_data['quantity']} RTX\n"
                    f"💰 Cost: ${estimated_cost:,.2f}\n"
                    f"🏦 Status: {result.get('status')}\n"
                    f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}"
                )
        
        return True
        
    except Exception as e:
        print(f"❌ Paper trade error: {e}")
        return False
    
    finally:
        # Disconnect
        print("\n🔌 Disconnecting from IBKR...")
        await ibkr.disconnect()

async def main():
    """Main test function"""
    print("🏦 IBKR PAPER TRADING INTEGRATION TEST")
    print("=" * 60)
    print("📋 This script tests REAL paper trading with Interactive Brokers")
    print("📋 Make sure you have TWS or IB Gateway running first!")
    print()
    
    # Test IBKR connection availability
    ibkr_available = await test_ibkr_connection()
    
    if ibkr_available:
        # Run the paper trading test
        success = await test_paper_trade()
        
        if success:
            print("\n🎉 IBKR PAPER TRADING TEST: PASSED!")
            print("✅ Your AlgoSlayer is ready for paper trading!")
            print("✅ All trading infrastructure is operational!")
        else:
            print("\n❌ IBKR PAPER TRADING TEST: FAILED")
            print("🔧 Check TWS/Gateway settings and try again")
    else:
        print("\n📋 TO ENABLE PAPER TRADING:")
        print("1. Download IBKR TWS or IB Gateway")
        print("2. Login with paper trading account")
        print("3. Go to Configure > API > Settings")
        print("4. Enable 'Enable ActiveX and Socket Clients'")
        print("5. Set Socket port to 7497")
        print("6. Run this script again")
        print()
        print("🔗 Download: https://www.interactivebrokers.com/en/trading/tws.php")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test error: {e}")
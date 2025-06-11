#!/usr/bin/env python3

"""
Simple Options System Test
"""

print("🚀 Starting Simple Options System Test")

try:
    # Test 1: Options Config
    print("1. Testing Options Config...")
    from config.options_config import options_config
    print(f"   ✅ Expiration preference: {options_config.EXPIRATION_PREFERENCE}")
    print(f"   ✅ Strike selection: {options_config.STRIKE_SELECTION}")
    print(f"   ✅ Max position size: {options_config.MAX_POSITION_SIZE_PCT:.0%}")
    
    # Test 2: Options Data Engine
    print("\n2. Testing Options Data Engine...")
    from src.core.options_data_engine import options_data_engine
    print("   ✅ Options data engine loaded")
    
    # Test 3: Options Prediction Engine
    print("\n3. Testing Options Prediction Engine...")
    from src.core.options_prediction_engine import options_prediction_engine
    print("   ✅ Options prediction engine loaded")
    
    # Test 4: Paper Trader
    print("\n4. Testing Paper Trader...")
    from src.core.options_paper_trader import options_paper_trader
    print(f"   ✅ Paper trader loaded, balance: ${options_paper_trader.account_balance:.2f}")
    
    # Test 5: Scheduler
    print("\n5. Testing Scheduler...")
    from src.core.options_scheduler import options_scheduler
    print("   ✅ Options scheduler loaded")
    
    # Test 6: ML Integration
    print("\n6. Testing ML Integration...")
    from src.core.options_ml_integration import options_ml_integration
    print("   ✅ ML integration loaded")
    
    print("\n🎉 ALL COMPONENTS LOADED SUCCESSFULLY!")
    print("🚀 RTX Options Trading System is ready!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
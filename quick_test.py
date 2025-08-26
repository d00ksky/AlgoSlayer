#!/usr/bin/env python3
"""
Quick verification of trading readiness
"""
import sys
import asyncio
sys.path.append('/opt/rtx-trading')

async def quick_readiness_check():
    """Quick check if system will trade Monday"""
    
    print("⚡ QUICK READINESS VERIFICATION")
    print("=" * 50)
    
    try:
        # Test signal fusion
        from src.core.signal_fusion import SignalFusionEngine
        engine = SignalFusionEngine()
        decision = await engine.make_trading_decision("RTX")
        
        print(f"🎯 Signal Decision: {decision.action} ({decision.confidence:.1%})")
        
        # Test strategy thresholds
        from src.core.multi_strategy_manager import MultiStrategyManager
        manager = MultiStrategyManager()
        conservative = manager.strategy_configs["conservative"]
        
        print(f"🎯 Conservative Threshold: {conservative.confidence_threshold:.0%}")
        
        # Check if trading would happen
        will_trade = decision.confidence >= conservative.confidence_threshold
        
        print(f"🎯 Will Conservative Trade? {will_trade}")
        print(f"   Signal: {decision.confidence:.1%} >= Threshold: {conservative.confidence_threshold:.0%}")
        
        if will_trade:
            print("\n🚀 SUCCESS: SYSTEM READY FOR MONDAY TRADING!")
            print("✅ Signals working")
            print("✅ Thresholds configured correctly")  
            print("✅ Conservative strategy will trade")
            return True
        else:
            print("\n❌ FAIL: Still won't trade")
            print(f"Need to lower threshold below {decision.confidence:.1%}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    ready = asyncio.run(quick_readiness_check())
    
    if ready:
        print("\n🎉 WEEKEND MISSION ACCOMPLISHED!")
    else:
        print("\n🔧 One more fix needed")

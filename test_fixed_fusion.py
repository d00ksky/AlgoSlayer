#!/usr/bin/env python3
"""
Test the fixed signal fusion system
"""
import sys
import asyncio
sys.path.append('/opt/rtx-trading')

async def test_fixed_signal_fusion():
    """Test if the fixed signal fusion works with all signals"""
    
    print("🔧 TESTING FIXED SIGNAL FUSION SYSTEM")
    print("=" * 60)
    
    try:
        from src.core.signal_fusion import SignalFusionEngine
        
        print("✅ Signal fusion import successful")
        
        # Initialize the engine
        engine = SignalFusionEngine()
        print(f"✅ Signal fusion engine initialized with {len(engine.signals)} signals")
        
        # List all signals
        print(f"\n📊 LOADED SIGNALS:")
        for i, signal in enumerate(engine.signals):
            signal_name = getattr(signal, 'signal_name', signal.__class__.__name__)
            print(f"  {i+1}. {signal_name}")
        
        # Test getting all signals
        print(f"\n🔍 TESTING SIGNAL GATHERING...")
        signals = await engine.get_all_signals("RTX")
        
        print(f"\n📈 SIGNAL RESULTS:")
        working_count = 0
        for signal in signals:
            print(f"  ✅ {signal.signal_name}: {signal.direction} ({signal.confidence:.1%})")
            print(f"     Reasoning: {signal.reasoning[:80]}...")
            working_count += 1
        
        print(f"\n🎯 MAKING TRADING DECISION...")
        decision = await engine.make_trading_decision("RTX")
        
        print(f"\n📊 FINAL DECISION:")
        print(f"  Action: {decision.action}")
        print(f"  Confidence: {decision.confidence:.1%}")
        print(f"  Signals Used: {len(decision.signals_used)}")
        print(f"  Reasoning: {decision.reasoning}")
        
        print(f"\n🎉 SUCCESS SUMMARY:")
        print(f"  Working Signals: {working_count}/12 expected")
        print(f"  Signal Fusion: {'✅ WORKING' if working_count > 0 else '❌ BROKEN'}")
        print(f"  Trading Ready: {'✅ YES' if working_count >= 3 else '❌ NO'}")
        
        if working_count >= 6:
            print(f"\n🚀 EXCELLENT: {working_count} signals working - ready for full trading!")
        elif working_count >= 3:
            print(f"\n✅ GOOD: {working_count} signals working - Conservative strategy ready!")
        else:
            print(f"\n⚠️  NEEDS WORK: Only {working_count} signals working")
        
        return working_count
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    working_signals = asyncio.run(test_fixed_signal_fusion())
    
    print(f"\n🎯 FINAL ASSESSMENT:")
    if working_signals >= 3:
        print("✅ READY TO RESTART TRADING SERVICE!")
        print("sudo systemctl restart rtx-trading")
        print("Trading should start within 15 minutes")
    else:
        print("🔧 More debugging needed")
        
    print(f"\nWorking signals: {working_signals}")
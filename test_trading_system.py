#!/usr/bin/env python3
"""
Test if AlgoSlayer is actually working
"""
import asyncio
import sys
sys.path.append('.')

async def test_system():
    print("\n" + "="*60)
    print("ALGOSLAYER FUNCTIONALITY TEST")
    print("="*60)
    
    # Test 1: Options Data Engine
    print("\n1. Testing Options Data Engine...")
    try:
        from src.core.options_data_engine import OptionsDataEngine
        engine = OptionsDataEngine()
        
        # Test get_current_price
        price = await engine.get_current_price("RTX")
        print(f"   ✅ Current RTX price: ${price:.2f}")
        
        # Test get options chain
        chain = await engine.get_options_chain("RTX")
        if chain:
            print(f"   ✅ Options chain: {len(chain)} contracts")
        else:
            print(f"   ⚠️  No options data")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Signal Fusion
    print("\n2. Testing Signal Fusion...")
    try:
        from src.core.signal_fusion import SignalFusionEngine
        fusion = SignalFusionEngine()
        decision = await fusion.make_trading_decision("RTX")
        result = decision.to_dict()
        
        print(f"   ✅ Direction: {result.get('direction')}")
        print(f"   ✅ Confidence: {result.get('confidence'):.1%}")
        
        # Check if confidence is reasonable
        if result.get('confidence', 0) > 0.20:
            print(f"   ✅ Confidence is tradeable!")
        else:
            print(f"   ⚠️  Confidence too low for trading")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Strategy Manager
    print("\n3. Testing Strategy Manager...")
    try:
        from src.core.multi_strategy_manager import MultiStrategyManager
        manager = MultiStrategyManager()
        
        for strategy_id, strategy in manager.active_strategies.items():
            config = strategy["config"]
            print(f"   {strategy_id}: threshold={config.confidence_threshold:.1%}, signals={config.min_signals_required}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_system())

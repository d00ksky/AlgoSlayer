#!/usr/bin/env python3
"""
Test the fixed AlgoSlayer system
"""
import asyncio
import sys
import os

sys.path.append('.')
os.environ['TRADING_ENABLED'] = 'true'
os.environ['PAPER_TRADING'] = 'true'

async def test_system():
    print("\n" + "="*60)
    print("TESTING FIXED ALGOSLAYER SYSTEM")
    print("="*60)
    
    results = {"passed": 0, "failed": 0, "warnings": 0}
    
    # Test 1: Options Data Engine
    print("\n1. TESTING OPTIONS DATA ENGINE")
    print("-" * 40)
    try:
        from src.core.options_data_engine import OptionsDataEngine
        engine = OptionsDataEngine()
        
        # Test get_current_price
        price = await engine.get_current_price("RTX")
        if price and price > 0:
            print(f"✅ get_current_price: ${price:.2f}")
            results["passed"] += 1
        else:
            print(f"❌ get_current_price failed")
            results["failed"] += 1
        
        # Test get_options_chain
        chain = await engine.get_options_chain("RTX")
        if chain and len(chain) > 0:
            print(f"✅ get_options_chain: {len(chain)} contracts")
            results["passed"] += 1
        else:
            print(f"⚠️  get_options_chain: No data")
            results["warnings"] += 1
            
    except Exception as e:
        print(f"❌ Options Engine Error: {e}")
        results["failed"] += 1
    
    # Test 2: Signal Confidence Values
    print("\n2. TESTING SIGNAL CONFIDENCE VALUES")
    print("-" * 40)
    
    signals_to_test = [
        ("rtx_earnings", "RTXEarningsSignal"),
        ("defense_contract", "DefenseContractSignal"),
        ("trump_geopolitical", "TrumpGeopoliticalSignal"),
        ("options_iv_percentile", "OptionsIVPercentileSignal")
    ]
    
    for signal_name, class_name in signals_to_test:
        try:
            if signal_name == "rtx_earnings":
                from src.signals.rtx_earnings_signal import RTXEarningsSignal
                signal = RTXEarningsSignal()
            elif signal_name == "defense_contract":
                from src.signals.defense_contract_signal import DefenseContractSignal
                signal = DefenseContractSignal()
            elif signal_name == "trump_geopolitical":
                from src.signals.trump_geopolitical_signal import TrumpGeopoliticalSignal
                signal = TrumpGeopoliticalSignal()
            elif signal_name == "options_iv_percentile":
                from src.signals.options_iv_percentile_signal import OptionsIVPercentileSignal
                signal = OptionsIVPercentileSignal()
            
            result = await signal.analyze("RTX")
            confidence = result.get("confidence", 0)
            
            # Check if confidence is reasonable (0-1 range)
            if 0 <= confidence <= 1:
                print(f"✅ {signal_name}: {confidence:.1%}")
                results["passed"] += 1
            else:
                print(f"❌ {signal_name}: Invalid confidence {confidence}")
                results["failed"] += 1
                
        except Exception as e:
            print(f"❌ {signal_name}: {e}")
            results["failed"] += 1
    
    # Test 3: Signal Fusion
    print("\n3. TESTING SIGNAL FUSION")
    print("-" * 40)
    try:
        from src.core.signal_fusion import SignalFusionEngine
        fusion = SignalFusionEngine()
        
        decision = await fusion.make_trading_decision("RTX")
        result = decision.to_dict()
        
        direction = result.get("direction")
        confidence = result.get("confidence", 0)
        
        if direction and 0 <= confidence <= 1:
            print(f"✅ Direction: {direction}")
            print(f"✅ Confidence: {confidence:.1%}")
            
            if confidence > 0.30:
                print(f"✅ Confidence is tradeable (>{30}%)")
                results["passed"] += 1
            else:
                print(f"⚠️  Confidence too low for trading")
                results["warnings"] += 1
        else:
            print(f"❌ Invalid fusion result")
            results["failed"] += 1
            
    except Exception as e:
        print(f"❌ Signal Fusion Error: {e}")
        results["failed"] += 1
    
    # Test 4: Strategy Thresholds
    print("\n4. TESTING STRATEGY THRESHOLDS")
    print("-" * 40)
    try:
        from src.core.multi_strategy_manager import MultiStrategyManager
        manager = MultiStrategyManager()
        
        for strategy_id, strategy in manager.active_strategies.items():
            config = strategy["config"]
            threshold = config.confidence_threshold
            min_signals = config.min_signals_required
            
            # Check if thresholds are reasonable
            if 0.30 <= threshold <= 0.75 and 1 <= min_signals <= 4:
                print(f"✅ {strategy_id}: {threshold:.0%} / {min_signals} signals")
                results["passed"] += 1
            else:
                print(f"⚠️  {strategy_id}: threshold may be too restrictive")
                results["warnings"] += 1
                
    except Exception as e:
        print(f"❌ Strategy Manager Error: {e}")
        results["failed"] += 1
    
    # Test 5: Can We Make a Trade?
    print("\n5. TESTING TRADE CAPABILITY")
    print("-" * 40)
    try:
        # Simulate a trading decision
        can_trade = False
        
        if confidence > 0.35:  # Lowest threshold
            can_trade = True
            print(f"✅ System can trade (confidence {confidence:.1%} > 35%)")
            results["passed"] += 1
        else:
            print(f"⚠️  Confidence too low to trade ({confidence:.1%})")
            results["warnings"] += 1
            
    except:
        pass
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {results['passed']}")
    print(f"⚠️  Warnings: {results['warnings']}")
    print(f"❌ Failed: {results['failed']}")
    
    if results["failed"] == 0:
        print("\n🎉 ALL CRITICAL TESTS PASSED! System should work.")
    else:
        print(f"\n❌ {results['failed']} critical failures need fixing.")
    
    return results["failed"] == 0

if __name__ == "__main__":
    import logging
    logging.getLogger().setLevel(logging.WARNING)
    
    success = asyncio.run(test_system())
    sys.exit(0 if success else 1)
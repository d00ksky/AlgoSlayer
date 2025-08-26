#!/usr/bin/env python3
"""Debug individual signals to find the attribute error"""
import sys
import asyncio
sys.path.append('.')

async def debug_signals():
    print("Debugging individual signals...")
    
    # Test problematic signals one by one
    signals_to_test = [
        ("rtx_earnings", "RTXEarningsSignal"),
        ("defense_contract", "DefenseContractSignal"),
        ("trump_geopolitical", "TrumpGeopoliticalSignal"),
        ("options_iv_percentile", "OptionsIVPercentileSignal")
    ]
    
    for signal_name, class_name in signals_to_test:
        print(f"\n=== Testing {signal_name} ===")
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
            
            # Call analyze method directly
            result = await signal.analyze('RTX')
            
            print(f"✅ {signal_name} returned: {type(result)}")
            print(f"   Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            if isinstance(result, dict):
                confidence = result.get('confidence', 'MISSING')
                direction = result.get('direction', 'MISSING')
                print(f"   Confidence: {confidence} (type: {type(confidence)})")
                print(f"   Direction: {direction}")
                
                # Check if confidence is a number
                try:
                    conf_float = float(confidence)
                    if conf_float > 1:
                        print(f"   ⚠️  Confidence {conf_float} > 1 (should be 0-1)")
                    else:
                        print(f"   ✅ Confidence format OK")
                except:
                    print(f"   ❌ Confidence not convertible to float")
            
        except Exception as e:
            print(f"❌ {signal_name} failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_signals())
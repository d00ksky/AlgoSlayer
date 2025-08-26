#!/usr/bin/env python3
"""
Corrected signal test - use get_signal_if_enabled() like the real system
"""
import sys
import asyncio
sys.path.append('/opt/rtx-trading')

async def test_corrected_signals():
    """Test signals using the correct BaseSignal method"""
    
    print("🔍 TESTING SIGNALS WITH CORRECT METHOD")
    print("=" * 60)
    
    # List of all signals to test
    signals_to_test = [
        ("news_sentiment", "from src.signals.news_sentiment_signal import NewsSentimentSignal"),
        ("technical_analysis", "from src.signals.technical_analysis_signal import TechnicalAnalysisSignal"), 
        ("volatility_analysis", "from src.signals.volatility_analysis_signal import VolatilityAnalysisSignal"),
        ("momentum", "from src.signals.momentum_signal import MomentumSignal"),
        ("mean_reversion", "from src.signals.mean_reversion_signal import MeanReversionSignal"),
        ("market_regime", "from src.signals.market_regime_signal import MarketRegimeSignal"),
        ("trump_geopolitical", "from src.signals.trump_geopolitical_signal import TrumpGeopoliticalSignal"),
        ("defense_contract", "from src.signals.defense_contract_signal import DefenseContractSignal"), 
        ("rtx_earnings", "from src.signals.rtx_earnings_signal import RTXEarningsSignal")
    ]
    
    working_signals = 0
    broken_signals_list = []
    
    for signal_name, import_statement in signals_to_test:
        print(f"\\n🧪 TESTING: {signal_name}")
        print("-" * 30)
        
        try:
            # Step 1: Test import
            exec(import_statement)
            print(f"✅ Import successful")
            
            # Step 2: Test instantiation
            class_name = ''.join(word.capitalize() for word in signal_name.split('_')) + 'Signal'
            signal_class = eval(class_name)
            signal_instance = signal_class()
            print(f"✅ Instantiation successful")
            
            # Step 3: Test signal execution using CORRECT method
            try:
                # Use get_signal_if_enabled() which is what the real system calls
                result = await signal_instance.get_signal_if_enabled("RTX")
                
                if result is None:
                    print(f"⚠️  Signal disabled or returned None")
                    broken_signals_list.append({
                        'name': signal_name,
                        'issue': 'returned_none',
                        'status': 'disabled_or_none'
                    })
                else:
                    confidence = getattr(result, 'confidence', 0)
                    direction = getattr(result, 'direction', 'UNKNOWN')
                    reasoning = getattr(result, 'reasoning', 'No reasoning provided')
                    
                    print(f"📊 Result: {direction} ({confidence}%)") 
                    print(f"💭 Reasoning: {reasoning[:100]}...")
                    
                    # Check if signal is actually working (not returning default values)
                    if confidence in [50.0, 40.0] and direction == 'HOLD':
                        print(f"⚠️  LIKELY BROKEN: Default values detected")
                        broken_signals_list.append({
                            'name': signal_name,
                            'issue': 'returning_default_values',
                            'confidence': confidence,
                            'reasoning': reasoning
                        })
                    elif confidence == 0 or direction == 'UNKNOWN':
                        print(f"❌ DEFINITELY BROKEN: Zero confidence or unknown direction")
                        broken_signals_list.append({
                            'name': signal_name, 
                            'issue': 'execution_failed',
                            'confidence': confidence,
                            'reasoning': reasoning
                        })
                    else:
                        print(f"✅ APPEARS WORKING: Non-default values")
                        working_signals += 1
                        
            except Exception as e:
                print(f"❌ Signal execution failed: {e}")
                broken_signals_list.append({
                    'name': signal_name,
                    'issue': 'execution_exception', 
                    'error': str(e)
                })
                
        except Exception as e:
            print(f"❌ Import/instantiation failed: {e}")
            broken_signals_list.append({
                'name': signal_name,
                'issue': 'import_failed',
                'error': str(e)
            })
    
    # Summary
    print(f"\\n🎯 SIGNAL DIAGNOSTICS SUMMARY")
    print("=" * 40)
    print(f"Working signals: {working_signals}/9")
    print(f"Broken signals: {len(broken_signals_list)}/9")
    
    if broken_signals_list:
        print(f"\\n🔧 BROKEN SIGNALS ANALYSIS:")
        for signal in broken_signals_list:
            print(f"• {signal['name']}: {signal['issue']}")
            if 'error' in signal:
                print(f"  Error: {signal['error']}")
            elif 'reasoning' in signal:
                print(f"  Reasoning: {signal['reasoning'][:50]}...")
    
    if working_signals >= 6:
        print(f"\\n🎉 SUCCESS: {working_signals}/9 signals working!")
        print("✅ System should be able to trade with these signals")
    elif working_signals >= 3:
        print(f"\\n🔄 PARTIAL: {working_signals}/9 signals working")
        print("✅ Conservative strategy (needs 3) should work")
    else:
        print(f"\\n❌ INSUFFICIENT: Only {working_signals}/9 signals working")
        print("⚠️  Need more signals for reliable trading")
    
    return working_signals, broken_signals_list

if __name__ == "__main__":
    working, broken = asyncio.run(test_corrected_signals())
    
    print(f"\\n🎯 FINAL ASSESSMENT:")
    print(f"Working signals: {working}/9")
    
    if working >= 6:
        print("🚀 READY FOR TRADING: Restart service and test!")
    elif working >= 3:
        print("✅ CONSERVATIVE STRATEGY READY: Restart service!")
    else:
        print("🔧 MORE FIXES NEEDED: Continue debugging signals")
        
    print("\\nNext: sudo systemctl restart rtx-trading")
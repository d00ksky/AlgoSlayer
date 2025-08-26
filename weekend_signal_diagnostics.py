#!/usr/bin/env python3
"""
Weekend Signal Diagnostics - Test each broken signal individually
"""

signal_test_code = '''#!/usr/bin/env python3
"""
Test each signal individually to find what's broken
"""
import sys
import asyncio
sys.path.append('/opt/rtx-trading')

async def test_individual_signals():
    """Test each of the 9 broken signals individually"""
    
    print("🔍 TESTING 9 BROKEN SIGNALS INDIVIDUALLY")
    print("=" * 60)
    
    # List of broken signals (returning HOLD 50%)
    broken_signals = [
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
    
    for signal_name, import_statement in broken_signals:
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
            
            # Step 3: Test signal execution
            try:
                result = await signal_instance.get_signal()
                
                confidence = getattr(result, 'confidence', 0)
                direction = getattr(result, 'direction', 'UNKNOWN')
                reasoning = getattr(result, 'reasoning', 'No reasoning provided')
                
                print(f"📊 Result: {direction} ({confidence}%)")
                print(f"💭 Reasoning: {reasoning[:100]}...")
                
                # Check if signal is actually broken (returning default values)
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
    
    return working_signals, broken_signals_list

if __name__ == "__main__":
    working, broken = asyncio.run(test_individual_signals())
    
    print(f"\\n🎯 WEEKEND FIX RECOMMENDATIONS:")
    
    if broken:
        print("1. Fix the broken signals above")
        print("2. Most likely issues: API keys, missing data, configuration")
        print("3. Check each signal's data sources and requirements")
        print("4. Test fixes immediately - no need to wait for Monday")
    
    if working >= 6:
        print("✅ Once fixed, you'll have 6+ working signals") 
        print("✅ System should start trading Monday morning!")
    else:
        print("⚠️ Need to fix more signals for reliable trading")
        
    print(f"\\nNext: Run individual signal fixes and retest")
'''

print("🔍 Creating weekend signal diagnostics...")

with open('weekend_signal_test.py', 'w') as f:
    f.write(signal_test_code)

print("✅ Created weekend_signal_test.py")
print("\\nDeploy and run:")
print("scp weekend_signal_test.py root@64.226.96.90:/opt/rtx-trading/")
print("ssh root@64.226.96.90 'cd /opt/rtx-trading && rtx-env/bin/python weekend_signal_test.py'")
print("\\nThis will test each broken signal and tell us exactly what to fix!")
#!/usr/bin/env python3
"""
Test New AI Signals
Quick test of the 4 new high-value signals we just added
"""
import asyncio
from datetime import datetime
from loguru import logger

# Import our new signals
from src.signals.rtx_earnings_signal import RTXEarningsSignal
from src.signals.options_iv_percentile_signal import OptionsIVPercentileSignal
from src.signals.defense_contract_signal import DefenseContractSignal
from src.signals.trump_geopolitical_signal import TrumpGeopoliticalSignal

async def test_signal(signal, signal_name):
    """Test a single signal"""
    try:
        logger.info(f"🧪 Testing {signal_name}...")
        
        # Test the signal
        result = await signal.analyze()
        
        if isinstance(result, dict):
            direction = result.get('direction', 'UNKNOWN')
            confidence = result.get('confidence', 0)
            reasoning = result.get('reasoning', 'No reasoning provided')[:100]
            metadata = result.get('metadata', {})
            
            logger.success(f"✅ {signal_name}: {direction} ({confidence}%) - {reasoning}")
            
            # Log some metadata for debugging
            if metadata:
                key_items = list(metadata.items())[:3]  # First 3 items
                meta_str = ", ".join([f"{k}: {v}" for k, v in key_items])
                logger.info(f"   Metadata: {meta_str}")
            
            return True
        else:
            logger.error(f"❌ {signal_name}: Invalid result type {type(result)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ {signal_name}: Error - {str(e)}")
        return False

async def test_all_new_signals():
    """Test all 4 new signals"""
    logger.info("🚀 Testing New AI Signals for RTX Options Trading")
    logger.info("=" * 60)
    
    # Initialize signals
    signals = [
        (RTXEarningsSignal(), "RTX Earnings Calendar Signal"),
        (OptionsIVPercentileSignal(), "Options IV Percentile Signal"),
        (DefenseContractSignal(), "Defense Contract News Signal"),
        (TrumpGeopoliticalSignal(), "Trump Geopolitical Signal")
    ]
    
    # Test each signal
    results = []
    for signal, name in signals:
        success = await test_signal(signal, name)
        results.append(success)
    
    # Summary
    logger.info("=" * 60)
    logger.info("📊 Test Results Summary:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        logger.success(f"✅ ALL {total} NEW SIGNALS WORKING ({passed}/{total})")
        logger.success("🎯 Ready to add these signals to the trading system!")
    else:
        logger.warning(f"⚠️ {passed}/{total} signals working - need to fix {total-passed} signals")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(test_all_new_signals())
    
    if success:
        print("\n🎉 NEW SIGNALS READY FOR PRODUCTION!")
        print("💡 Next steps:")
        print("   1. Test with historical data")
        print("   2. Deploy to cloud server")
        print("   3. Monitor Monday performance")
    else:
        print("\n🔧 SIGNALS NEED FIXES")
        print("💡 Fix the failing signals before deployment")
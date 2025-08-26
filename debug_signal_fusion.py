#!/usr/bin/env python3
"""Debug signal fusion to find attribute error"""
import sys
import asyncio
import traceback
sys.path.append('.')

async def debug_fusion():
    print("Debugging signal fusion...")
    
    try:
        from src.core.signal_fusion import SignalFusionEngine
        fusion = SignalFusionEngine()
        
        print("Getting all signals...")
        signals = await fusion.get_all_signals('RTX')
        print(f"Got {len(signals)} signals")
        
        for i, signal in enumerate(signals):
            print(f"Signal {i}: {signal.signal_name} - {signal.direction} @ {signal.confidence:.2f}")
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_fusion())
"""
RTX AlgoSlayer - Signal Fusion Test
Quick test of our AI-powered trading signals
"""
import asyncio
import os
from datetime import datetime

# Set up basic environment
if not os.getenv("OPENAI_API_KEY"):
    print("⚠️ Set OPENAI_API_KEY environment variable to run this test")
    print("💡 Example: export OPENAI_API_KEY='your-key-here'")
    exit(1)

from src.core.signal_fusion import SignalFusionEngine
from config.trading_config import config

async def test_rtx_signals():
    """Test the RTX signal fusion system"""
    print("🚀 RTX AlgoSlayer - Signal Fusion Test")
    print("=" * 50)
    
    # Initialize the fusion engine
    print("Initializing AI Signal Fusion Engine...")
    fusion_engine = SignalFusionEngine()
    
    print(f"Loaded {len(fusion_engine.signals)} AI signals:")
    for signal in fusion_engine.signals:
        print(f"  - {signal.name} (weight: {signal.weight:.2f})")
    
    print("\n" + "=" * 50)
    print("Analyzing RTX for trading opportunities...")
    print("=" * 50)
    
    # Test the fusion system
    try:
        decision = await fusion_engine.make_trading_decision("RTX")
        
        # Display results
        print(f"\n🎯 TRADING DECISION:")
        print(f"Symbol: {decision.symbol}")
        print(f"Action: {decision.action}")
        print(f"Trade Type: {decision.trade_type}")
        print(f"Confidence: {decision.confidence:.2%}")
        print(f"Position Size: ${decision.position_size:.2f}")
        print(f"Risk Score: {decision.risk_score:.2f}")
        print(f"Signals Used: {len(decision.signals_used)}")
        print(f"Reasoning: {decision.reasoning}")
        
        print(f"\n📊 INDIVIDUAL SIGNALS:")
        for signal in decision.signals_used:
            print(f"  {signal.signal_name}:")
            print(f"    Direction: {signal.direction}")
            print(f"    Confidence: {signal.confidence:.2%}")
            print(f"    Reasoning: {signal.reasoning}")
            if signal.data:
                print(f"    AI Analysis: {signal.data.get('ai_analysis', 'N/A')[:100]}...")
        
        print(f"\n⚙️  CONFIGURATION:")
        print(f"Paper Trading: {config.PAPER_TRADING}")
        print(f"Min Signals Required: {config.MIN_SIGNALS_REQUIRED}")
        print(f"Min Confidence Threshold: {config.CONFIDENCE_THRESHOLD:.1%}")
        print(f"Max Position Size: ${config.MAX_POSITION_SIZE}")
        
    except Exception as e:
        print(f"❌ Error during signal analysis: {e}")
        print("Make sure to set your OPENAI_API_KEY in the script!")

if __name__ == "__main__":
    print("Starting RTX AlgoSlayer test...")
    asyncio.run(test_rtx_signals()) 
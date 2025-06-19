#!/usr/bin/env python3
"""
Test Signals Capture for ML Learning
Tests whether signals data is being properly captured and stored
"""
import asyncio
import json
from datetime import datetime
from loguru import logger

from src.core.options_scheduler import OptionsScheduler
from src.core.options_prediction_engine import options_prediction_engine
from src.core.options_paper_trader import options_paper_trader

async def test_signals_capture():
    """Test if signals data is being captured properly"""
    
    logger.info("🧪 Testing signals data capture for ML learning...")
    
    # Create scheduler instance
    scheduler = OptionsScheduler()
    
    # Generate signals
    logger.info("🤖 Generating AI signals...")
    signals_data = await scheduler._generate_signals()
    
    if not signals_data:
        logger.error("❌ No signals generated")
        return False
    
    logger.info("📊 Signals data structure:")
    logger.info(f"   Direction: {signals_data.get('direction')}")
    logger.info(f"   Confidence: {signals_data.get('confidence', 0):.1%}")
    logger.info(f"   Individual signals: {len(signals_data.get('individual_signals', {}))}")
    logger.info(f"   Signal weights: {len(signals_data.get('signal_weights', {}))}")
    
    # Show individual signals
    individual_signals = signals_data.get('individual_signals', {})
    logger.info("🔍 Individual signals breakdown:")
    for name, signal_data in individual_signals.items():
        if isinstance(signal_data, dict):
            direction = signal_data.get('direction', 'UNKNOWN')
            confidence = signal_data.get('confidence', 0)
            if confidence > 1:  # Handle percentage format
                confidence = confidence / 100
            logger.info(f"   • {name}: {direction} ({confidence:.1%})")
    
    # Test prediction generation
    logger.info("🎯 Testing prediction generation...")
    prediction = options_prediction_engine.generate_options_prediction(
        signals_data, 1000.0
    )
    
    if prediction:
        logger.success("✅ Prediction generated successfully")
        logger.info(f"   Action: {prediction.get('action')}")
        logger.info(f"   Confidence: {prediction.get('confidence', 0):.1%}")
        logger.info(f"   Individual signals stored: {len(prediction.get('individual_signals', {}))}")
        logger.info(f"   Signal weights stored: {len(prediction.get('signal_weights', {}))}")
        
        # Show what would be stored in database
        signals_for_db = prediction.get('individual_signals', {})
        logger.info("💾 Signals data that would be stored in DB:")
        logger.info(f"   JSON length: {len(json.dumps(signals_for_db))}")
        if signals_for_db:
            logger.info(f"   Sample: {list(signals_for_db.keys())[:3]}")
        else:
            logger.warning("   ⚠️ Empty signals data - this is the problem!")
        
        return True
    else:
        logger.error("❌ No prediction generated")
        return False

async def test_database_storage():
    """Test if signals data is being stored in database correctly"""
    
    logger.info("🗄️ Testing database storage...")
    
    # Create a mock prediction with signals data
    test_prediction = {
        'prediction_id': f'test_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'timestamp': datetime.now().isoformat(),
        'symbol': 'RTX',
        'action': 'BUY_TO_OPEN_CALL',
        'contract_symbol': 'RTX250620C00147000',
        'option_type': 'call',
        'strike': 147.0,
        'expiry': '2025-06-20',
        'days_to_expiry': 1,
        'entry_price': 1.50,
        'contracts': 1,
        'total_cost': 150.0,
        'commission': 1.15,
        'direction': 'BUY',
        'confidence': 0.85,
        'expected_move': 0.03,
        'expected_profit_pct': 1.0,
        'implied_volatility': 0.25,
        'delta': 0.5,
        'gamma': 0.1,
        'theta': -0.05,
        'vega': 0.1,
        'profit_target_price': 3.0,
        'stop_loss_price': 0.75,
        'max_loss_dollars': 75.0,
        'stock_price_entry': 146.5,
        'volume': 100,
        'open_interest': 1000,
        'reasoning': 'Test prediction for signals capture',
        
        # Test signals data
        'individual_signals': {
            'technical_analysis': {'direction': 'BUY', 'confidence': 0.8, 'strength': 0.3},
            'momentum': {'direction': 'BUY', 'confidence': 0.7, 'strength': 0.25},
            'news_sentiment': {'direction': 'HOLD', 'confidence': 0.5, 'strength': 0.1}
        },
        'signal_weights': {
            'technical_analysis': 0.12,
            'momentum': 0.08,
            'news_sentiment': 0.10
        }
    }
    
    logger.info("💾 Storing test prediction with signals data...")
    success = options_paper_trader.open_position(test_prediction)
    
    if success:
        logger.success("✅ Test prediction stored successfully")
        
        # Verify storage
        import sqlite3
        conn = sqlite3.connect(options_paper_trader.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT signals_data FROM options_predictions 
        WHERE prediction_id = ?
        """, (test_prediction['prediction_id'],))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            stored_signals = json.loads(result[0])
            logger.success(f"✅ Signals data stored: {len(stored_signals)} signals")
            for name, data in stored_signals.items():
                logger.info(f"   • {name}: {data}")
            return True
        else:
            logger.error("❌ No signals data found in database")
            return False
    else:
        logger.error("❌ Failed to store test prediction")
        return False

if __name__ == "__main__":
    async def main():
        logger.info("🧪 Starting signals capture test...")
        
        # Test 1: Signals generation
        signals_ok = await test_signals_capture()
        
        # Test 2: Database storage
        storage_ok = await test_database_storage()
        
        if signals_ok and storage_ok:
            logger.success("✅ All tests passed - signals capture working!")
        else:
            logger.error("❌ Some tests failed - signals capture needs fixing")
            if not signals_ok:
                logger.error("   - Signals generation issue")
            if not storage_ok:
                logger.error("   - Database storage issue")
    
    asyncio.run(main())
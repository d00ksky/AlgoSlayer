"""
Test Accelerated Learning System
Verify the learning engine works at 180x speed
"""
import asyncio
from datetime import datetime
from loguru import logger
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.accelerated_learning import learning_engine

async def test_basic_learning():
    """Test basic accelerated learning functionality"""
    
    logger.info("🧪 Testing basic accelerated learning...")
    
    # Test 1-month learning cycle
    results = await learning_engine.learn_from_historical_data("RTX", months_back=1)
    
    logger.info("📊 Learning Results:")
    logger.info(f"   • Symbol: {results.get('symbol', 'Unknown')}")
    logger.info(f"   • Data period: {results.get('data_period_days', 0)} days")
    logger.info(f"   • Predictions made: {results.get('predictions_made', 0):,}")
    logger.info(f"   • Accuracy rate: {results.get('accuracy_rate', 0):.1%}")
    logger.info(f"   • Learning time: {results.get('learning_time_seconds', 0):.2f} seconds")
    logger.info(f"   • Speed multiplier: {results.get('speed_multiplier', 0):,.0f}x real-time")
    logger.info(f"   • Latest RTX price: ${results.get('latest_price', 0):.2f}")
    
    # Verify results
    assert results.get('predictions_made', 0) > 0, "No predictions made"
    assert results.get('speed_multiplier', 0) > 100, "Speed not accelerated enough"
    assert 0 <= results.get('accuracy_rate', 0) <= 1, "Invalid accuracy rate"
    
    logger.success("✅ Basic learning test passed!")
    return results

async def test_multiple_scenarios():
    """Test multiple learning scenarios"""
    
    logger.info("🧪 Testing multiple learning scenarios...")
    
    scenarios_results = await learning_engine.test_multiple_scenarios("RTX")
    
    logger.info("📊 Multi-Scenario Results:")
    logger.info(f"   • Scenarios tested: {scenarios_results.get('scenarios_tested', 0)}")
    logger.info(f"   • Total predictions: {scenarios_results.get('total_predictions', 0):,}")
    logger.info(f"   • Overall accuracy: {scenarios_results.get('overall_accuracy', 0):.1%}")
    logger.info(f"   • Best scenario: {scenarios_results.get('best_scenario', 'Unknown')}")
    
    # Check individual scenarios
    scenario_results = scenarios_results.get('scenario_results', {})
    for scenario, results in scenario_results.items():
        logger.info(f"   • {scenario}: {results.get('accuracy_rate', 0):.1%} accuracy, "
                   f"{results.get('speed_multiplier', 0):,.0f}x speed")
    
    # Verify results
    assert scenarios_results.get('scenarios_tested', 0) >= 3, "Not enough scenarios tested"
    assert scenarios_results.get('total_predictions', 0) > 100, "Too few total predictions"
    
    logger.success("✅ Multi-scenario test passed!")
    return scenarios_results

async def test_continuous_learning():
    """Test continuous learning simulation"""
    
    logger.info("🧪 Testing continuous learning simulation (2 minutes)...")
    
    simulation_results = await learning_engine.continuous_learning_simulation("RTX", duration_minutes=2)
    
    logger.info("📊 Continuous Learning Results:")
    logger.info(f"   • Duration: {simulation_results.get('duration_minutes', 0):.1f} minutes")
    logger.info(f"   • Learning cycles: {simulation_results.get('learning_cycles', 0)}")
    logger.info(f"   • Total predictions: {simulation_results.get('total_predictions', 0):,}")
    logger.info(f"   • Average accuracy: {simulation_results.get('average_accuracy', 0):.1%}")
    logger.info(f"   • Cycles per minute: {simulation_results.get('cycles_per_minute', 0):.1f}")
    
    # Verify results
    assert simulation_results.get('learning_cycles', 0) > 0, "No learning cycles completed"
    assert simulation_results.get('duration_minutes', 0) > 1.5, "Test too short"
    
    logger.success("✅ Continuous learning test passed!")
    return simulation_results

async def test_learning_status():
    """Test learning system status"""
    
    logger.info("🧪 Testing learning system status...")
    
    status = learning_engine.get_learning_status()
    
    logger.info("📊 Learning System Status:")
    logger.info(f"   • System: {status.get('system', 'Unknown')}")
    logger.info(f"   • Max speed: {status.get('capabilities', {}).get('max_speed_multiplier', 0)}x")
    logger.info(f"   • Supported periods: {status.get('capabilities', {}).get('supported_periods', [])}")
    logger.info(f"   • Accuracy tracking: {status.get('capabilities', {}).get('accuracy_tracking', False)}")
    
    # Verify status
    assert status.get('system') == 'operational', "System not operational"
    assert status.get('capabilities', {}).get('max_speed_multiplier', 0) > 0, "No speed multiplier"
    
    logger.success("✅ Learning status test passed!")
    return status

async def test_performance_benchmark():
    """Benchmark learning performance"""
    
    logger.info("🧪 Running performance benchmark...")
    
    start_time = datetime.now()
    
    # Learn from 6 months of data
    results = await learning_engine.learn_from_historical_data("RTX", months_back=6)
    
    end_time = datetime.now()
    actual_duration = (end_time - start_time).total_seconds()
    
    # Calculate performance metrics
    predictions_made = results.get('predictions_made', 0)
    predictions_per_second = predictions_made / actual_duration if actual_duration > 0 else 0
    speed_multiplier = results.get('speed_multiplier', 0)
    
    logger.info("📊 Performance Benchmark:")
    logger.info(f"   • Actual duration: {actual_duration:.2f} seconds")
    logger.info(f"   • Predictions made: {predictions_made:,}")
    logger.info(f"   • Predictions/second: {predictions_per_second:,.0f}")
    logger.info(f"   • Speed multiplier: {speed_multiplier:,.0f}x real-time")
    logger.info(f"   • Efficiency: {'EXCELLENT' if speed_multiplier > 10000 else 'GOOD' if speed_multiplier > 1000 else 'FAIR'}")
    
    # Performance assertions
    assert predictions_made > 1000, "Too few predictions for 6 months"
    assert speed_multiplier > 1000, "Speed not fast enough"
    assert actual_duration < 30, "Learning took too long"
    
    logger.success("✅ Performance benchmark passed!")
    return {
        'duration': actual_duration,
        'predictions_made': predictions_made,
        'predictions_per_second': predictions_per_second,
        'speed_multiplier': speed_multiplier
    }

async def main():
    """Run all accelerated learning tests"""
    
    logger.info("🚀 Starting Accelerated Learning System Tests")
    logger.info("=" * 60)
    
    try:
        # Test 1: Basic learning
        basic_results = await test_basic_learning()
        logger.info("")
        
        # Test 2: Multiple scenarios
        scenario_results = await test_multiple_scenarios()
        logger.info("")
        
        # Test 3: Continuous learning
        continuous_results = await test_continuous_learning()
        logger.info("")
        
        # Test 4: System status
        status_results = await test_learning_status()
        logger.info("")
        
        # Test 5: Performance benchmark
        benchmark_results = await test_performance_benchmark()
        logger.info("")
        
        # Summary
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("=" * 60)
        logger.info("📊 SUMMARY:")
        logger.info(f"   • Learning speed: {basic_results.get('speed_multiplier', 0):,.0f}x real-time")
        logger.info(f"   • Overall accuracy: {scenario_results.get('overall_accuracy', 0):.1%}")
        logger.info(f"   • Performance: {benchmark_results.get('predictions_per_second', 0):,.0f} predictions/sec")
        logger.info(f"   • System status: {status_results.get('system', 'Unknown')}")
        
        logger.success("✅ Accelerated Learning System is FULLY OPERATIONAL!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    # Run the tests
    asyncio.run(main()) 
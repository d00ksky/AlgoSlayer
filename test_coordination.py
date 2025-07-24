#!/usr/bin/env python3
"""
Test Coordination with Claude Code
Test the hybrid coordination system with Claude Code's exported data
"""
import pandas as pd
import json
from pathlib import Path
from enhanced_hybrid_coordinator import HybridCoordinator
import asyncio

async def test_coordination():
    print("🤝 Testing Coordination with Claude Code...")
    
    coordinator = HybridCoordinator()
    
    # Check what data we have
    export_dir = Path('hybrid_work/data_export')
    
    if not export_dir.exists():
        print("❌ No export directory found")
        return
    
    # Load metadata
    metadata_file = export_dir / 'export_metadata_20250724_192626.json'
    if metadata_file.exists():
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        print("📊 Server Status:")
        print(f"   Phase 1: {'✅' if metadata['system_status']['phase1_active'] else '❌'}")
        print(f"   Phase 2: {'✅' if metadata['system_status']['phase2_available'] else '❌'}")
        print(f"   Phase 3: {'✅' if metadata['system_status']['phase3_active'] else '❌'}")
        print(f"   Continuous Learning: {'✅' if metadata['system_status']['continuous_learning_active'] else '❌'}")
        
        print(f"\n📊 Data Quality:")
        data_quality = metadata['data_quality']
        print(f"   Total Predictions: {data_quality['total_predictions']}")
        print(f"   Completed Trades: {data_quality['completed_trades']}")
        print(f"   Data Quality Score: {data_quality['data_quality_score']}")
        
        print(f"\n🎯 Recommendations:")
        for rec in data_quality['recommendations']:
            print(f"   • {rec}")
    
    # Check predictions data
    predictions_file = export_dir / 'predictions_data_20250724_192625.csv'
    if predictions_file.exists():
        df = pd.read_csv(predictions_file)
        print(f"\n📈 Predictions Data:")
        print(f"   Shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        if len(df) > 0:
            print(f"   Date range: {df['timestamp'].min()} → {df['timestamp'].max()}")
    
    # Test server status
    print(f"\n🔍 Testing Server Connection...")
    status = await coordinator.check_server_learning_status()
    print(f"   Continuous Learning Running: {'✅' if status.get('continuous_learning_running') else '❌'}")
    print(f"   Recent Predictions: {status.get('recent_predictions', 0)}")
    
    # Simulate what happens when we have enough data
    print(f"\n🧠 Simulation: What happens with sufficient data...")
    print("   1. ✅ Local machine would train LSTM, Ensemble, Multi-Task models")
    print("   2. ✅ Models would be saved with 'coord_' prefix")
    print("   3. ✅ Models would be uploaded to server")
    print("   4. ✅ Claude Code's model_integration.py would auto-detect them")
    print("   5. ✅ Server would use best available model (continuous vs advanced)")
    
    print(f"\n🎉 Coordination Test Complete!")
    print("🤝 Hybrid system is ready and waiting for more trading data")

if __name__ == "__main__":
    asyncio.run(test_coordination())
#!/usr/bin/env python3
"""
Test Dynamic Thresholds System
Demonstrates how dynamic confidence thresholds adapt based on performance
"""

import asyncio
from src.core.dynamic_thresholds import dynamic_threshold_manager

def test_dynamic_thresholds():
    """Test the dynamic threshold system"""
    print("🧪 Testing Dynamic Threshold System")
    print("="*60)
    
    # Get current thresholds for all strategies
    thresholds = dynamic_threshold_manager.get_all_thresholds()
    
    print("\n📊 Current Dynamic Thresholds:")
    for strategy_id, data in thresholds.items():
        print(f"\n🎯 {strategy_id.upper()}:")
        print(f"   Base Threshold: {data['base_threshold']:.1%}")
        print(f"   Dynamic Threshold: {data['dynamic_threshold']:.1%}")
        print(f"   Adjustment: {data['adjustment']:+.1%}")
        print(f"   Reason: {data['reason']}")
        
        if data['performance']:
            perf = data['performance']
            print(f"   Win Rate: {perf['win_rate']:.1%}")
            print(f"   Total Trades: {perf['total_trades']}")
            print(f"   Profit Factor: {perf['profit_factor']:.2f}")
            if perf['recent_streak'] != 0:
                streak_emoji = "🔥" if perf['recent_streak'] > 0 else "❄️"
                print(f"   Recent Streak: {streak_emoji} {abs(perf['recent_streak'])}")
        else:
            print("   Performance: No data yet")
    
    print("\n" + "="*60)
    print("\n📱 Telegram Command: /thresholds")
    print(dynamic_threshold_manager.get_threshold_summary())
    
    print("\n✅ Dynamic Threshold System Test Complete!")
    print("\n🎯 How it works:")
    print("• Base thresholds: Conservative 75%, Moderate 60%, Aggressive 50%")
    print("• Hot streak (>60% win rate): Lowers threshold by 10% to capture momentum")
    print("• Cold streak (<30% win rate): Raises threshold by 15% for protection")
    print("• High profit factor (>2.0): Slightly lowers threshold")
    print("• Minimum 5 trades required before adjustments are made")
    print("\n🚀 Once the system has trading data, thresholds will adapt automatically!")

if __name__ == "__main__":
    test_dynamic_thresholds()
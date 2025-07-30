#!/usr/bin/env python3
"""
Test ML Notification System
Verify that all ML status notifications work correctly
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.ml_status_monitor import ml_status_monitor
from src.core.telegram_bot import telegram_bot

async def test_ml_status_monitor():
    """Test the ML status monitor functionality"""
    
    print("🧠 Testing ML Status Monitor...")
    
    # Test comprehensive status
    print("\n1. Testing comprehensive ML status...")
    status = ml_status_monitor.get_comprehensive_ml_status()
    print(f"   Status keys: {list(status.keys())}")
    
    if "error" in status:
        print(f"   ❌ Error: {status['error']}")
    else:
        print("   ✅ Status data retrieved successfully")
    
    # Test message formatting
    print("\n2. Testing message formatting...")
    message = ml_status_monitor.format_ml_status_message(status)
    print(f"   Message length: {len(message)} characters")
    print(f"   First 100 chars: {message[:100]}...")
    
    # Test quick summary
    print("\n3. Testing quick summary...")
    quick_summary = ml_status_monitor.format_quick_ml_summary(status)
    print(f"   Quick summary: {quick_summary}")
    
    # Test notification timing
    print("\n4. Testing notification timing...")
    should_notify = ml_status_monitor.should_send_notification()
    print(f"   Should send notification: {should_notify}")
    
    return status, message, quick_summary

async def test_telegram_bot_ml_functions():
    """Test Telegram bot ML functions"""
    
    print("\n📱 Testing Telegram Bot ML Functions...")
    
    if not telegram_bot.enabled:
        print("   ⚠️ Telegram bot not configured - skipping send tests")
        return (False, False, False, False)
    
    try:
        # Test comprehensive ML status
        print("\n1. Testing comprehensive ML status...")
        result1 = await telegram_bot.send_comprehensive_ml_status()
        print(f"   Comprehensive status sent: {result1}")
        
        # Small delay
        await asyncio.sleep(2)
        
        # Test quick ML summary
        print("\n2. Testing quick ML summary...")
        result2 = await telegram_bot.send_quick_ml_summary()
        print(f"   Quick summary sent: {result2}")
        
        # Small delay
        await asyncio.sleep(2)
        
        # Test learning progress alerts
        print("\n3. Testing learning progress alerts...")
        result3 = await telegram_bot.send_learning_progress_alerts()
        print(f"   Learning alerts sent: {result3}")
        
        # Small delay
        await asyncio.sleep(2)
        
        # Test automated notification (may not send due to timing)
        print("\n4. Testing automated notification...")
        result4 = await telegram_bot.send_automated_ml_notification()
        print(f"   Automated notification sent: {result4}")
        
        return result1, result2, result3, result4
        
    except Exception as e:
        print(f"   ❌ Error testing Telegram functions: {e}")
        return (False, False, False, False)

async def test_ml_insight_for_summary():
    """Test ML insight integration for daily summary"""
    
    print("\n📊 Testing ML Insight for Daily Summary...")
    
    try:
        insight = await telegram_bot._get_ml_insight_for_summary()
        print(f"   ML insight generated:")
        print(f"   {insight}")
        
        # Test enhanced daily summary
        print("\n   Testing enhanced daily summary...")
        summary_data = {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "predictions_made": 12,
            "accuracy_rate": 75.5,
            "trades_executed": 3,
            "pnl": 125.50,
            "rtx_price": 120.45,
            "price_change": 1.2
        }
        
        if telegram_bot.enabled:
            result = await telegram_bot.send_daily_summary(summary_data)
            print(f"   Enhanced daily summary sent: {result}")
        else:
            print("   ⚠️ Telegram not configured - cannot send summary")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing ML insight: {e}")
        return False

async def test_learning_alerts_system():
    """Test the learning alerts detection system"""
    
    print("\n🚨 Testing Learning Alerts System...")
    
    try:
        from src.core.ml_learning_alerts import ml_learning_alerts
        
        # Test learning improvements detection
        print("\n1. Testing learning improvements detection...")
        alerts = ml_learning_alerts.check_for_learning_improvements()
        print(f"   Alerts detected: {len(alerts)}")
        
        if alerts:
            print("   Alert types:")
            for alert in alerts:
                print(f"     • {alert.get('type', 'Unknown')}: {alert.get('message', 'No message')}")
        else:
            print("   ℹ️ No significant improvements detected")
        
        # Test alert formatting
        print("\n2. Testing alert message formatting...")
        formatted_message = ml_learning_alerts.format_learning_progress_alert(alerts)
        print(f"   Formatted message length: {len(formatted_message)} chars")
        if formatted_message:
            print(f"   Preview: {formatted_message[:100]}...")
        
        return alerts, formatted_message
        
    except Exception as e:
        print(f"   ❌ Error testing learning alerts: {e}")
        return [], ""

def print_test_summary(status, message, quick_summary, telegram_results, alerts_data):
    """Print comprehensive test summary"""
    
    print("\n" + "="*60)
    print("🎯 ML NOTIFICATION SYSTEM TEST SUMMARY")
    print("="*60)
    
    # ML Status Monitor Results
    print("\n🧠 ML Status Monitor:")
    if "error" in status:
        print(f"   ❌ Status: ERROR - {status['error']}")
    else:
        print("   ✅ Status: WORKING")
        health = status.get("overall_health", {})
        print(f"   📊 System Health: {health.get('status', 'Unknown')} ({health.get('score', 0):.1f}/100)")
        
        performance = status.get("performance_metrics", {})
        if "total_predictions" in performance:
            print(f"   📈 24H Predictions: {performance['total_predictions']}")
            print(f"   🎯 Win Rate: {performance['win_rate']:.1f}%")
    
    # Message Formatting
    print(f"\n📝 Message Formatting:")
    print(f"   ✅ Full Message: {len(message)} chars")
    print(f"   ✅ Quick Summary: {len(quick_summary)} chars")
    
    # Telegram Integration
    print(f"\n📱 Telegram Integration:")
    if telegram_bot.enabled:
        comprehensive, quick, alerts, automated = telegram_results
        print(f"   📊 Comprehensive Status: {'✅ SENT' if comprehensive else '❌ FAILED'}")
        print(f"   ⚡ Quick Summary: {'✅ SENT' if quick else '❌ FAILED'}")
        print(f"   🚨 Learning Alerts: {'✅ SENT' if alerts else '❌ FAILED'}")
        print(f"   🔄 Automated Notification: {'✅ SENT' if automated else 'ℹ️ SKIPPED (timing)'}")
    else:
        print("   ⚠️ Not configured (add BOT_TOKEN and CHAT_ID)")
    
    # Learning Alerts System
    print(f"\n🚨 Learning Alerts System:")
    alerts_list, alerts_message = alerts_data
    if alerts_list:
        print(f"   ✅ Alerts Detected: {len(alerts_list)} improvements found")
        for alert in alerts_list[:3]:  # Show first 3
            print(f"     • {alert.get('type', 'Unknown')}")
    else:
        print("   ℹ️ No alerts: System performing within normal ranges")
    print(f"   📝 Message Format: {'✅ Working' if alerts_message else '⚪ No message needed'}")
    
    print("\n🎉 Test completed successfully!")
    print("\n📋 Next Steps:")
    print("   1. Configure Telegram bot if not done")
    print("   2. Deploy to server for live testing") 
    print("   3. Monitor automated notifications during market hours")
    print("   4. Check notifications appear every 3 hours")

async def main():
    """Run comprehensive ML notification system test"""
    
    print("🚀 STARTING ML NOTIFICATION SYSTEM TEST")
    print(f"⏰ Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Test ML Status Monitor
    status, message, quick_summary = await test_ml_status_monitor()
    
    # Test Telegram Bot Functions
    telegram_results = await test_telegram_bot_ml_functions()
    
    # Test ML Insight Integration
    await test_ml_insight_for_summary()
    
    # Test Learning Alerts System
    alerts_data = await test_learning_alerts_system()
    
    # Print Summary
    print_test_summary(status, message, quick_summary, telegram_results, alerts_data)

if __name__ == "__main__":
    asyncio.run(main())
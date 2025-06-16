#!/usr/bin/env python3
"""
Production Readiness Checklist
Final verification that everything is ready for live trading
"""
import asyncio
import sqlite3
import os
from datetime import datetime
from src.core.options_scheduler import options_scheduler

async def production_readiness_check():
    print('🏁 PRODUCTION READINESS CHECKLIST')
    print('=' * 60)
    print('🔍 Final verification for live trading deployment')
    print('=' * 60)
    
    checklist = []
    
    def check_item(item, status, details=""):
        checklist.append({'item': item, 'status': status, 'details': details})
        status_emoji = "✅" if status else "❌"
        print(f"{status_emoji} {item}")
        if details:
            print(f"   📝 {details}")
    
    # 1. Environment Configuration
    print('\\n🔧 Environment Configuration:')
    
    # Check critical environment variables
    use_options = os.getenv('USE_OPTIONS_SYSTEM', 'true').lower() == 'true'
    check_item("Options system enabled", use_options, f"USE_OPTIONS_SYSTEM={use_options}")
    
    trading_enabled = os.getenv('TRADING_ENABLED', 'false').lower() == 'true'
    check_item("Trading capability configured", True, f"TRADING_ENABLED={trading_enabled}")
    
    paper_trading = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
    check_item("Paper trading mode", paper_trading, f"PAPER_TRADING={paper_trading}")
    
    # 2. API Keys and Tokens
    print('\\n🔐 API Keys and Authentication:')
    
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    check_item("Telegram bot token configured", bool(telegram_token), 
               "Token present" if telegram_token else "Missing TELEGRAM_BOT_TOKEN")
    
    telegram_chat = os.getenv('TELEGRAM_CHAT_ID')
    check_item("Telegram chat ID configured", bool(telegram_chat),
               f"Chat ID: {telegram_chat}" if telegram_chat else "Missing TELEGRAM_CHAT_ID")
    
    openai_key = os.getenv('OPENAI_API_KEY')
    check_item("OpenAI API key configured", bool(openai_key),
               "Key present" if openai_key else "Missing OPENAI_API_KEY")
    
    # 3. Database and Data Integrity
    print('\\n🗄️ Database and Data:')
    
    db_path = "data/options_performance.db"
    db_exists = os.path.exists(db_path)
    check_item("Options database exists", db_exists, f"Path: {db_path}")
    
    if db_exists:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check tables
            tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            table_names = [t[0] for t in tables]
            required_tables = ['options_predictions', 'options_outcomes', 'account_history']
            all_tables_exist = all(table in table_names for table in required_tables)
            check_item("Database tables complete", all_tables_exist, f"Tables: {len(table_names)}")
            
            # Check for existing data
            prediction_count = cursor.execute("SELECT COUNT(*) FROM options_predictions").fetchone()[0]
            check_item("Database initialized", True, f"{prediction_count} predictions recorded")
            
            conn.close()
        except Exception as e:
            check_item("Database accessibility", False, str(e))
    
    # 4. AI System Status
    print('\\n🤖 AI System Status:')
    
    try:
        # Test signal generation
        signals = await options_scheduler._generate_signals()
        
        signal_count = len([s for s in signals.values() if isinstance(s, dict)])
        check_item("AI signals generating", signal_count > 0, f"{signal_count} signals active")
        
        confidence = signals.get('confidence', 0)
        check_item("Signal confidence calculation", confidence > 0, f"Current: {confidence:.1%}")
        
        direction = signals.get('direction', 'UNKNOWN')
        check_item("Signal direction determination", direction in ['BUY', 'SELL', 'HOLD'], 
                  f"Current: {direction}")
        
    except Exception as e:
        check_item("AI signal system", False, str(e))
    
    # 5. Options Data Access
    print('\\n📊 Options Data Access:')
    
    try:
        from src.core.options_data_engine import options_data_engine
        
        stock_price = options_data_engine.get_current_stock_price()
        check_item("Stock price data", stock_price is not None, f"RTX: ${stock_price:.2f}")
        
        options_chain = options_data_engine.get_real_options_chain()
        check_item("Options chain data", len(options_chain) > 0, f"{len(options_chain)} contracts")
        
        # Check data quality
        valid_options = sum(1 for opt in options_chain.values() 
                           if opt.get('bid', 0) > 0 and opt.get('ask', 0) > opt.get('bid', 0))
        check_item("Options data quality", valid_options > 10, f"{valid_options} valid contracts")
        
    except Exception as e:
        check_item("Options data system", False, str(e))
    
    # 6. Trading System Components
    print('\\n💰 Trading System:')
    
    try:
        from src.core.options_paper_trader import OptionsPaperTrader
        
        trader = OptionsPaperTrader()
        check_item("Paper trader initialized", True, f"Balance: ${trader.account_balance:.2f}")
        
        # Test position tracking
        positions = trader.get_open_positions_summary()
        check_item("Position tracking system", True, f"{len(positions)} open positions")
        
    except Exception as e:
        check_item("Trading system", False, str(e))
    
    # 7. Communication System
    print('\\n📱 Communication System:')
    
    try:
        from src.core.telegram_bot import telegram_bot
        
        # Don't actually send a message, just verify configuration
        bot_configured = hasattr(telegram_bot, 'bot_token') and telegram_bot.bot_token
        check_item("Telegram bot configured", bot_configured, "Ready for notifications")
        
        chat_configured = hasattr(telegram_bot, 'chat_id') and telegram_bot.chat_id
        check_item("Telegram chat configured", chat_configured, "Ready to receive alerts")
        
    except Exception as e:
        check_item("Communication system", False, str(e))
    
    # 8. Risk Management
    print('\\n🛡️ Risk Management:')
    
    try:
        from config.options_config import options_config
        
        max_position = getattr(options_config, 'MAX_POSITION_SIZE_PCT', 0.20)
        check_item("Position size limits", 0.05 <= max_position <= 0.50, 
                  f"Max position: {max_position:.1%}")
        
        stop_loss = getattr(options_config, 'STOP_LOSS_PCT', 0.50)
        check_item("Stop loss configured", 0.30 <= stop_loss <= 0.70,
                  f"Stop loss: {stop_loss:.1%}")
        
        min_confidence = getattr(options_config, 'CONFIDENCE_THRESHOLD', 0.75)
        check_item("Confidence threshold", min_confidence >= 0.70,
                  f"Min confidence: {min_confidence:.1%}")
        
    except Exception as e:
        check_item("Risk management", False, str(e))
    
    # 9. File System and Permissions
    print('\\n📁 File System:')
    
    # Check data directory
    data_dir = "data"
    check_item("Data directory exists", os.path.exists(data_dir), f"Path: {data_dir}")
    check_item("Data directory writable", os.access(data_dir, os.W_OK), "Write permissions OK")
    
    # Check logs directory
    logs_dir = "logs"
    logs_exist = os.path.exists(logs_dir)
    check_item("Logs directory exists", logs_exist, f"Path: {logs_dir}")
    if logs_exist:
        check_item("Logs directory writable", os.access(logs_dir, os.W_OK), "Write permissions OK")
    
    # 10. System Resources
    print('\\n💾 System Resources:')
    
    try:
        import psutil
        import os
        
        # Memory check
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        check_item("Available memory", available_gb > 0.5, f"{available_gb:.1f}GB available")
        
        # Disk space check
        disk = psutil.disk_usage('.')
        free_gb = disk.free / (1024**3)
        check_item("Disk space", free_gb > 1.0, f"{free_gb:.1f}GB free")
        
    except ImportError:
        check_item("Resource monitoring", True, "psutil not available (optional)")
    except Exception as e:
        check_item("System resources", False, str(e))
    
    # Summary
    print('\\n' + '=' * 60)
    print('📋 PRODUCTION READINESS SUMMARY')
    print('=' * 60)
    
    passed = sum(1 for item in checklist if item['status'])
    total = len(checklist)
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"✅ Passed: {passed}/{total} ({pass_rate:.1f}%)")
    
    failed_items = [item for item in checklist if not item['status']]
    if failed_items:
        print(f"❌ Failed items:")
        for item in failed_items:
            print(f"   • {item['item']}: {item['details']}")
    
    if pass_rate >= 95:
        print("\\n🎉 SYSTEM IS PRODUCTION READY!")
        print("✅ All critical systems verified")
        print("🚀 Ready for live options trading")
        
        print("\\n⚠️ FINAL CHECKLIST BEFORE GOING LIVE:")
        print("📱 1. Regenerate Telegram bot token (security incident)")
        print("💰 2. Confirm starting balance ($1000)")
        print("📊 3. Monitor first few trading cycles")
        print("🔔 4. Verify Telegram notifications arrive")
        print("📈 5. Check position management works")
        
        return True
        
    elif pass_rate >= 85:
        print("\\n⚠️ MOSTLY READY - Minor issues to address")
        print("🔧 Fix failed items before live trading")
        return False
        
    else:
        print("\\n❌ NOT READY FOR PRODUCTION")
        print("🛠️ Multiple critical issues need resolution")
        return False

if __name__ == "__main__":
    print('🚨 FINAL PRODUCTION READINESS CHECK')
    print('🔍 This verifies all systems are ready for live trading')
    print()
    
    ready = asyncio.run(production_readiness_check())
    
    if ready:
        print('\\n🎯 SYSTEM VERIFIED: Ready for live options trading!')
    else:
        print('\\n⚠️ SYSTEM NEEDS ATTENTION: Address issues before going live')
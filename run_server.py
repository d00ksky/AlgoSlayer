"""
RTX Autonomous Trading System - Main Server
Production-ready autonomous trading with RTX Corporation
"""
import asyncio
import signal
import sys
import os
from datetime import datetime
from loguru import logger

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.scheduler import scheduler
from config.trading_config import config, TradingModeConfig

class RTXTradingServer:
    """Main server for autonomous RTX trading"""
    
    def __init__(self):
        self.scheduler = scheduler
        self.running = False
        self.start_time = None
        
        # Setup logging
        self._setup_logging()
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
    def _setup_logging(self):
        """Setup comprehensive logging"""
        
        # Create logs directory
        os.makedirs("logs", exist_ok=True)
        
        # Configure loguru
        logger.remove()  # Remove default handler
        
        # Console logging
        logger.add(
            sys.stdout,
            level="INFO",
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True
        )
        
        # File logging
        logger.add(
            "logs/rtx_trading_{time:YYYY-MM-DD}.log",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="1 day",
            retention="30 days",
            compression="zip"
        )
        
        # Error file
        logger.add(
            "logs/rtx_errors_{time:YYYY-MM-DD}.log",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="1 day",
            retention="7 days"
        )
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        
        def signal_handler(signum, frame):
            logger.info(f"📡 Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
        
        if hasattr(signal, 'SIGBREAK'):  # Windows
            signal.signal(signal.SIGBREAK, signal_handler)
    
    async def start(self):
        """Start the RTX trading server"""
        
        if self.running:
            logger.warning("⚠️ Server already running")
            return
        
        self.running = True
        self.start_time = datetime.now()
        
        # Load trading configuration
        trading_mode = TradingModeConfig.load_from_env()
        
        # System startup
        logger.info("🚀 RTX AUTONOMOUS TRADING SYSTEM")
        logger.info("=" * 60)
        logger.info(f"📊 Mode: {trading_mode.get_mode_description()}")
        logger.info(f"🎯 Target: RTX Corporation")
        logger.info(f"💰 Capital: ${config.STARTING_CAPITAL:,}")
        logger.info(f"🔍 Analysis: Every {config.PREDICTION_INTERVAL_MINUTES} minutes")
        logger.info(f"🤖 AI Signals: 8 signals active")
        logger.info(f"⚡ Learning: {config.learning.LEARNING_SPEED_MULTIPLIER}x speed")
        logger.info("=" * 60)
        
        # Safety checks
        if not trading_mode.TRADING_ENABLED:
            logger.info("🛡️ TRADING DISABLED - Running in prediction mode only")
        elif trading_mode.PAPER_TRADING:
            logger.info("📄 PAPER TRADING MODE - Using virtual money")
        else:
            logger.warning("💰 LIVE TRADING MODE - Using real money!")
            logger.warning("⚠️ Ensure you understand the risks!")
        
        # Environment checks
        self._check_environment()
        
        try:
            # Start the trading scheduler
            logger.info("🔄 Starting trading scheduler...")
            await self.scheduler.start()
            
        except KeyboardInterrupt:
            logger.info("⌨️ Keyboard interrupt received")
            await self.stop()
        except Exception as e:
            logger.error(f"❌ Server error: {e}")
            await self.stop()
            raise
    
    def _check_environment(self):
        """Check environment configuration"""
        
        logger.info("🔍 Checking environment configuration...")
        
        # Check required environment variables
        required_vars = ["OPENAI_API_KEY"]
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
            logger.info("💡 Some features may not work without proper configuration")
        
        # Check optional but recommended variables
        recommended_vars = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
        missing_recommended = []
        
        for var in recommended_vars:
            if not os.getenv(var):
                missing_recommended.append(var)
        
        if missing_recommended:
            logger.info(f"💡 Recommended variables not set: {', '.join(missing_recommended)}")
            logger.info("📱 Telegram notifications will be disabled")
        
        logger.success("✅ Environment check complete")
    
    async def stop(self):
        """Stop the RTX trading server"""
        
        if not self.running:
            logger.warning("⚠️ Server not running")
            return
        
        logger.info("🛑 Stopping RTX Trading Server...")
        
        self.running = False
        
        # Stop the scheduler
        try:
            await self.scheduler.stop()
        except Exception as e:
            logger.error(f"❌ Error stopping scheduler: {e}")
        
        # Calculate uptime
        if self.start_time:
            uptime = datetime.now() - self.start_time
            logger.info(f"⏱️ Server uptime: {uptime}")
        
        logger.success("✅ RTX Trading Server stopped gracefully")
    
    def get_status(self) -> dict:
        """Get server status"""
        
        uptime = str(datetime.now() - self.start_time) if self.start_time else "Not started"
        
        return {
            "server_running": self.running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime": uptime,
            "scheduler_status": self.scheduler.get_system_status() if self.running else None,
            "trading_mode": TradingModeConfig.load_from_env().get_mode_description()
        }

async def main():
    """Main entry point"""
    
    # ASCII art banner
    print("""
    ██████╗ ████████╗██╗  ██╗    ████████╗██████╗  █████╗ ██████╗ ███████╗██████╗ 
    ██╔══██╗╚══██╔══╝╚██╗██╔╝    ╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
    ██████╔╝   ██║    ╚███╔╝        ██║   ██████╔╝███████║██║  ██║█████╗  ██████╔╝
    ██╔══██╗   ██║    ██╔██╗        ██║   ██╔══██╗██╔══██║██║  ██║██╔══╝  ██╔══██╗
    ██║  ██║   ██║   ██╔╝ ██╗       ██║   ██║  ██║██║  ██║██████╔╝███████╗██║  ██║
    ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝
    
    🤖 AUTONOMOUS AI TRADING SYSTEM 🤖
    🎯 TARGET: RTX CORPORATION
    ⚡ POWERED BY 8 AI SIGNALS
    """)
    
    # Create and start server
    server = RTXTradingServer()
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("👋 Goodbye!")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Handle Windows event loop policy
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Run the server
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Shutdown complete!")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1) 
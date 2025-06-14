#!/bin/bash
# Start Telegram ML Bot Daemon
# This allows two-way communication with the ML system via Telegram

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BOT_PID_FILE="$SCRIPT_DIR/telegram_bot.pid"
BOT_LOG_FILE="$SCRIPT_DIR/logs/telegram_bot.log"

# Create logs directory
mkdir -p logs

# Function to check if bot is running
is_bot_running() {
    if [ -f "$BOT_PID_FILE" ]; then
        PID=$(cat "$BOT_PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$BOT_PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to start bot
start_bot() {
    echo "🚀 Starting Telegram ML Bot daemon..."
    
    # Check connectivity first
    if ! ping -c 1 -W 3 google.com > /dev/null 2>&1; then
        echo "❌ No internet connection - cannot start bot"
        exit 1
    fi
    
    # Start bot in background
    nohup python3 telegram_ml_bot.py daemon >> "$BOT_LOG_FILE" 2>&1 &
    BOT_PID=$!
    
    # Save PID
    echo $BOT_PID > "$BOT_PID_FILE"
    
    # Wait a moment and check if it started successfully
    sleep 2
    if ps -p "$BOT_PID" > /dev/null 2>&1; then
        echo "✅ Telegram bot started successfully (PID: $BOT_PID)"
        echo "📱 You can now control ML system via Telegram commands"
        echo "💡 Send /help to the bot for available commands"
    else
        echo "❌ Failed to start Telegram bot"
        rm -f "$BOT_PID_FILE"
        exit 1
    fi
}

# Function to stop bot
stop_bot() {
    if is_bot_running; then
        PID=$(cat "$BOT_PID_FILE")
        echo "🛑 Stopping Telegram bot (PID: $PID)..."
        kill "$PID"
        rm -f "$BOT_PID_FILE"
        echo "✅ Telegram bot stopped"
    else
        echo "ℹ️ Telegram bot is not running"
    fi
}

# Function to restart bot
restart_bot() {
    stop_bot
    sleep 1
    start_bot
}

# Function to show status
status_bot() {
    if is_bot_running; then
        PID=$(cat "$BOT_PID_FILE")
        echo "✅ Telegram bot is running (PID: $PID)"
        
        # Show recent log entries
        if [ -f "$BOT_LOG_FILE" ]; then
            echo ""
            echo "📋 Recent log entries:"
            tail -5 "$BOT_LOG_FILE"
        fi
    else
        echo "❌ Telegram bot is not running"
    fi
}

# Handle command line arguments
case "${1:-start}" in
    start)
        if is_bot_running; then
            echo "ℹ️ Telegram bot is already running"
            status_bot
        else
            start_bot
        fi
        ;;
    stop)
        stop_bot
        ;;
    restart)
        restart_bot
        ;;
    status)
        status_bot
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo ""
        echo "🤖 Telegram ML Bot Control Script"
        echo ""
        echo "Commands:"
        echo "  start   - Start bot daemon (default)"
        echo "  stop    - Stop bot daemon" 
        echo "  restart - Restart bot daemon"
        echo "  status  - Show bot status"
        echo ""
        echo "The bot enables two-way Telegram communication to:"
        echo "  • Monitor ML training status remotely"
        echo "  • Force training while traveling"
        echo "  • Check cloud server status"
        echo "  • Enable/disable auto-training"
        echo "  • View logs and statistics"
        exit 1
        ;;
esac
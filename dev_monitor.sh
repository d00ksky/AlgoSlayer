#!/bin/bash

# Development Monitoring Script for AlgoSlayer
# Use this when SSH'd into the server for real-time monitoring

echo "🚀 AlgoSlayer Development Monitor"
echo "================================="
echo "🕐 $(date)"
echo ""

# Function to show colored status
show_status() {
    local service=$1
    local status=$(systemctl is-active $service)
    if [[ "$status" == "active" ]]; then
        echo "✅ $service: $status"
    else
        echo "❌ $service: $status"
    fi
}

# System Status
echo "📊 SYSTEM STATUS:"
show_status rtx-trading
show_status rtx-ibkr
echo ""

# Resource Usage
echo "💾 RESOURCES:"
echo "  Memory: $(free -h | grep Mem | awk '{print $3"/"$2" ("int($3/$2*100)"%)"}')"
echo "  Disk: $(df -h /opt/rtx-trading | tail -1 | awk '{print $3"/"$2" ("$5")"}')"
echo "  Load: $(uptime | awk -F'load average:' '{print $2}')"
echo ""

# Network Ports
echo "🌐 NETWORK PORTS:"
echo "  IBKR Gateway: $(ss -tuln | grep :7497 > /dev/null && echo 'OPEN' || echo 'CLOSED')"
echo "  VNC Server: $(ss -tuln | grep :5900 > /dev/null && echo 'OPEN' || echo 'CLOSED')"
echo ""

# Recent Trading Activity
echo "💰 RECENT TRADING LOGS (last 10 lines):"
echo "----------------------------------------"
journalctl -u rtx-trading -n 10 --no-pager | tail -10
echo ""

# Interactive Menu
echo "🛠️ DEVELOPMENT COMMANDS:"
echo "1) Watch live trading logs     (journalctl -u rtx-trading -f)"
echo "2) Watch IBKR Gateway logs     (journalctl -u rtx-ibkr -f)"
echo "3) Restart trading system      (systemctl restart rtx-trading)"
echo "4) Restart IBKR Gateway        (systemctl restart rtx-ibkr)"
echo "5) Check error logs            (journalctl -u rtx-trading --since '1 hour ago' -p err)"
echo "6) System performance          (htop)"
echo "7) Git pull latest updates     (cd /opt/rtx-trading && git pull)"
echo "8) Test system integration     (cd /opt/rtx-trading && python test_system_integration.py)"
echo "9) Exit"
echo ""

read -p "Select option (1-9): " choice

case $choice in
    1)
        echo "📊 Watching live trading logs (Ctrl+C to exit)..."
        journalctl -u rtx-trading -f
        ;;
    2)
        echo "🏦 Watching IBKR Gateway logs (Ctrl+C to exit)..."
        journalctl -u rtx-ibkr -f
        ;;
    3)
        echo "🔄 Restarting trading system..."
        systemctl restart rtx-trading
        echo "✅ Done. Check status with: systemctl status rtx-trading"
        ;;
    4)
        echo "🔄 Restarting IBKR Gateway..."
        systemctl restart rtx-ibkr
        echo "✅ Done. Check status with: systemctl status rtx-ibkr"
        ;;
    5)
        echo "🔍 Error logs from last hour:"
        journalctl -u rtx-trading --since '1 hour ago' -p err
        ;;
    6)
        echo "📈 System performance monitor (q to quit)..."
        htop
        ;;
    7)
        echo "📥 Pulling latest updates..."
        cd /opt/rtx-trading
        git pull
        echo "🔄 Restart services to apply updates? (y/n)"
        read -n 1 restart_choice
        if [[ $restart_choice =~ ^[Yy]$ ]]; then
            systemctl restart rtx-trading
            echo -e "\n✅ Services restarted"
        fi
        ;;
    8)
        echo "🧪 Running system integration test..."
        cd /opt/rtx-trading
        source rtx-env/bin/activate
        python test_system_integration.py
        ;;
    9)
        echo "👋 Happy trading!"
        exit 0
        ;;
    *)
        echo "❌ Invalid option"
        ;;
esac
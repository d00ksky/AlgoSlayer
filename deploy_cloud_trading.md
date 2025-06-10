# 🏦 **IBKR + AlgoSlayer on DigitalOcean: Complete Guide**

## 🎯 **Architecture Overview**

Your RTX trading system can run on DigitalOcean in multiple configurations:

### **Option 1: Hybrid Architecture (Recommended)**
```
┌─────────────────┐    ┌─────────────────┐
│   Local IBKR    │────│  Cloud Server   │
│   TWS/Gateway   │    │   AlgoSlayer    │
│   (Your PC)     │    │  (DigitalOcean) │
└─────────────────┘    └─────────────────┘
```

**Benefits:**
- ✅ **Reliable IBKR connection** (your local machine)
- ✅ **24/7 cloud analysis** (DigitalOcean server)
- ✅ **Lower server costs** (no GUI needed)
- ✅ **Easy IBKR management** (familiar interface)

### **Option 2: Full Cloud (Advanced)**
```
┌─────────────────────────────────┐
│        Cloud Server             │
│  ┌─────────────┐ ┌─────────────┐│
│  │ IBKR Gateway│ │ AlgoSlayer  ││
│  │   (VNC)     │ │    (AI)     ││
│  └─────────────┘ └─────────────┘│
└─────────────────────────────────┘
```

**Benefits:**
- ✅ **Fully autonomous** (no local dependencies)
- ✅ **Professional setup** (hedge fund style)
- ⚠️ **Requires VNC access** for IBKR login

## 🚀 **Deployment Options**

### **Quick Start: Hybrid Mode (Easiest)**

**Step 1: Deploy AlgoSlayer to Cloud**
```bash
# On DigitalOcean droplet
curl -O https://raw.githubusercontent.com/your-repo/setup_server_simple.sh
sudo bash setup_server_simple.sh
```

**Step 2: Configure Local IBKR**
```bash
# On your local machine
# 1. Install IBKR TWS/Gateway
# 2. Enable API access (port 7497 for paper)
# 3. Update server .env file:
IBKR_HOST=YOUR_LOCAL_IP  # Your machine's IP
IBKR_REQUIRED=true
AUTO_CONNECT_IBKR=true
```

**Step 3: Network Setup**
```bash
# Port forward IBKR port to cloud server
ssh -R 7497:localhost:7497 root@your-server-ip
# Keep this SSH tunnel running
```

### **Professional: Full Cloud Mode**

**Step 1: Deploy Complete System**
```bash
# Upload and run the complete setup
scp setup_server_with_ibkr.sh root@your-server-ip:/tmp/
ssh root@your-server-ip
cd /tmp && bash setup_server_with_ibkr.sh
```

**Step 2: Access IBKR Gateway via VNC**
```bash
# From your local machine
ssh -L 5900:localhost:5900 root@your-server-ip
# Open VNC viewer to localhost:5900
# Login to IBKR Gateway once
```

**Step 3: Automation (Optional)**
```bash
# Set up IBKR auto-login with saved credentials
# Configure daily restart schedule
# Monitor via Telegram notifications
```

## 📊 **Recommended Droplet Specs**

### **For AlgoSlayer Only (Hybrid Mode)**
- **Size**: 1GB RAM, 1 vCPU ($12/month)
- **OS**: Ubuntu 22.04 LTS
- **Storage**: 25GB SSD

### **For AlgoSlayer + IBKR (Full Cloud)**
- **Size**: 2GB RAM, 1 vCPU ($24/month)  
- **OS**: Ubuntu 22.04 LTS
- **Storage**: 50GB SSD
- **Add-ons**: Enable monitoring

## 🔧 **Configuration Examples**

### **Hybrid Mode .env**
```bash
# AlgoSlayer runs on cloud, IBKR on local machine
TRADING_ENABLED=true
PAPER_TRADING=true
IBKR_HOST=192.168.1.100  # Your local machine IP
IBKR_PAPER_PORT=7497
IBKR_REQUIRED=true
AUTO_CONNECT_IBKR=true

# SSH tunnel required:
# ssh -R 7497:localhost:7497 root@server-ip
```

### **Full Cloud .env**
```bash
# Everything runs on DigitalOcean
TRADING_ENABLED=true
PAPER_TRADING=true
IBKR_HOST=127.0.0.1
IBKR_PAPER_PORT=7497
IBKR_REQUIRED=true
AUTO_CONNECT_IBKR=true

# VNC access for IBKR login:
# ssh -L 5900:localhost:5900 root@server-ip
```

## 🛡️ **Security & Best Practices**

### **Firewall Configuration**
```bash
# Essential ports only
ufw allow ssh
ufw allow 7497  # IBKR paper trading
ufw allow 5900  # VNC (if using full cloud)
ufw deny 7496   # IBKR live trading (enable only when needed)
```

### **Monitoring Setup**
```bash
# Health checks every 5 minutes
*/5 * * * * /opt/rtx-trading/monitor_system.sh

# Daily system reports
0 17 * * * systemctl status rtx-trading | mail -s "RTX System Status" your@email.com
```

### **Backup Strategy**
```bash
# Daily database backup
0 2 * * * cp /opt/rtx-trading/data/*.db /backup/$(date +%Y%m%d)_rtx_backup.db

# Weekly full backup
0 3 * * 0 tar -czf /backup/rtx_system_$(date +%Y%m%d).tar.gz /opt/rtx-trading
```

## 📱 **Mobile Management**

### **Telegram Commands** (Future Enhancement)
```
/status - System health check
/performance - Trading performance
/stop - Emergency stop
/start - Resume trading
/logs - Recent activity
```

### **VNC Mobile Access**
```bash
# Access IBKR Gateway from phone
# 1. Install VNC Viewer app
# 2. Connect via SSH tunnel
# 3. Monitor IBKR status remotely
```

## 🎯 **Recommended Deployment Path**

### **Phase 1: Start Simple (Hybrid)**
1. ✅ Deploy AlgoSlayer to DigitalOcean ($12/month)
2. ✅ Run IBKR TWS on your local machine
3. ✅ Use SSH tunnel for connection
4. ✅ Test paper trading functionality

### **Phase 2: Scale Up (Full Cloud)**
1. ✅ Upgrade to 2GB droplet ($24/month)
2. ✅ Install IBKR Gateway on server
3. ✅ Set up VNC access
4. ✅ Configure auto-restart and monitoring

### **Phase 3: Production (Live Trading)**
1. ✅ Switch to live IBKR account
2. ✅ Enable live trading mode
3. ✅ Implement advanced monitoring
4. ✅ Set up automated reporting

## 💰 **Cost Analysis**

### **Monthly Costs**
- **Hybrid Mode**: $12 (1GB droplet) + $0 (local IBKR)
- **Full Cloud**: $24 (2GB droplet) + $0 (cloud IBKR)
- **Live Trading**: +$0 (IBKR account free with trading)

### **Cost Comparison**
- **Traditional VPS + Manual Trading**: $50-100/month
- **AlgoSlayer Hybrid**: $12/month
- **AlgoSlayer Full Cloud**: $24/month
- **Professional Trading Platform**: $200-500/month

## 🚀 **Next Steps**

Choose your deployment strategy:

**🎯 Recommended for Beginners:**
```bash
# 1. Start with hybrid mode
# 2. Deploy AlgoSlayer to cloud
# 3. Keep IBKR on local machine
# 4. Test paper trading
```

**🎯 Recommended for Advanced:**
```bash
# 1. Deploy full cloud solution
# 2. Use complete setup script
# 3. Access via VNC when needed
# 4. Full automation
```

Ready to deploy? Let me know which option you prefer!
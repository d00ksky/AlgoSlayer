#!/bin/bash

# IBKR Gateway Memory Fix for Low-Memory Droplets
# This script prepares your system for IBKR Gateway installation

set -e

echo "🔧 IBKR Gateway Memory Fix Script"
echo "================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Please run as root: sudo bash fix_ibkr_memory.sh"
   exit 1
fi

# Check current memory
TOTAL_MEM=$(grep MemTotal /proc/meminfo | awk '{print $2}')
TOTAL_MEM_GB=$((TOTAL_MEM / 1024 / 1024))
echo "💾 Current RAM: ${TOTAL_MEM_GB}GB"

# 1. Create/Expand Swap File
echo ""
echo "📊 Setting up swap file..."
if [[ -f /swapfile ]]; then
    echo "⚠️ Swap file exists, checking size..."
    SWAP_SIZE=$(du -m /swapfile | cut -f1)
    if [[ $SWAP_SIZE -lt 2048 ]]; then
        echo "📈 Expanding swap to 4GB..."
        swapoff /swapfile
        rm /swapfile
        fallocate -l 4G /swapfile
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
    fi
else
    echo "📝 Creating 4GB swap file..."
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
fi

# 2. Optimize system settings
echo ""
echo "⚙️ Optimizing system settings..."

# Increase file descriptor limits
cat > /etc/security/limits.d/99-ibkr.conf << EOF
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768
root soft nofile 65536
root hard nofile 65536
root soft nproc 32768
root hard nproc 32768
EOF

# Update sysctl for better memory management
cat > /etc/sysctl.d/99-ibkr.conf << EOF
# File descriptor limits
fs.file-max = 100000

# Memory optimization
vm.swappiness = 10
vm.vfs_cache_pressure = 50
vm.max_map_count = 262144

# Network optimization
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
EOF

sysctl -p /etc/sysctl.d/99-ibkr.conf

# 3. Install memory monitoring tools
echo ""
echo "📦 Installing monitoring tools..."
apt-get update -qq
apt-get install -y htop iotop sysstat

# 4. Create memory-optimized IBKR installer wrapper
echo ""
echo "🛠️ Creating IBKR installer wrapper..."

cat > /tmp/install_ibkr_lowmem.sh << 'INSTALLER_EOF'
#!/bin/bash

# IBKR Gateway Low-Memory Installation Wrapper

APP_DIR="/opt/rtx-trading"
IBKR_DIR="$APP_DIR/ibkr"

echo "🏦 Installing IBKR Gateway (Low Memory Mode)..."

# Create directories
mkdir -p $IBKR_DIR
cd $IBKR_DIR

# Download installer
echo "📥 Downloading IBKR Gateway installer..."
IBKR_URL="https://download2.interactivebrokers.com/installers/gateway/stable-standalone/gateway-1026-standalone-linux-x64.sh"
wget -O ibgateway-installer.sh "$IBKR_URL" || {
    echo "❌ Download failed. Try manual download from:"
    echo "   https://www.interactivebrokers.com/en/trading/ib-gateway-download.php"
    exit 1
}

chmod +x ibgateway-installer.sh

# Set memory limits
export _JAVA_OPTIONS="-Xmx512m -Xms256m -XX:MaxMetaspaceSize=256m"
export INSTALL4J_JAVA_HOME_OVERRIDE=/usr/lib/jvm/java-11-openjdk-amd64

# Apply current session limits
ulimit -n 65536
ulimit -u 32768

echo "📦 Installing with reduced memory settings..."
echo "⏳ This may take a few minutes..."

# Try installation with force options
./ibgateway-installer.sh -q -dir $IBKR_DIR/IBJts -J-Xmx512m -J-Xms256m \
    -J-XX:MaxMetaspaceSize=256m -J-XX:+UseG1GC -J-XX:+UseStringDeduplication \
    -J-XX:+CompactStrings 2>&1 | tee install.log

if [[ -d "$IBKR_DIR/IBJts" ]] && [[ -f "$IBKR_DIR/IBJts/ibgateway" ]]; then
    echo "✅ IBKR Gateway installed successfully!"
    
    # Create low-memory startup script
    cat > $IBKR_DIR/start_gateway_lowmem.sh << 'STARTUP_EOF'
#!/bin/bash
export DISPLAY=:1
export _JAVA_OPTIONS="-Xmx768m -Xms256m -XX:MaxMetaspaceSize=256m -XX:+UseG1GC"

cd $(dirname $0)/IBJts
./ibgateway "$@"
STARTUP_EOF
    
    chmod +x $IBKR_DIR/start_gateway_lowmem.sh
    echo "✅ Created low-memory startup script"
else
    echo "❌ Installation failed. Check install.log for details"
    echo ""
    echo "💡 ALTERNATIVE SOLUTIONS:"
    echo "   1. Upgrade to 2GB+ droplet (recommended)"
    echo "   2. Use IBKR Web API instead of Gateway"
    echo "   3. Install on another machine and copy files"
    exit 1
fi
INSTALLER_EOF

chmod +x /tmp/install_ibkr_lowmem.sh

# 5. Show system status
echo ""
echo "📊 System Status:"
free -h
echo ""
swapon --show
echo ""
echo "File descriptor limit: $(ulimit -n)"

echo ""
echo "✅ System prepared for IBKR Gateway installation!"
echo ""
echo "📋 Next steps:"
echo "   1. Run the installer: /tmp/install_ibkr_lowmem.sh"
echo "   2. Or run the main setup: sudo ./setup_server_with_ibkr.sh"
echo ""
echo "💡 Tips:"
echo "   - Monitor memory during install: watch -n 1 free -h"
echo "   - If install fails, consider upgrading to 2GB droplet"
echo "   - IBKR Gateway needs ~1GB RAM to run comfortably"
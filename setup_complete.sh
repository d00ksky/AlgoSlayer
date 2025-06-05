#!/bin/bash

# AlgoSlayer Complete Setup Script for DigitalOcean
# This script sets up everything needed for a production-ready deployment
# Run this on your DigitalOcean server: sudo bash setup_complete.sh

set -e  # Exit on error
set -o pipefail  # Exit on pipe failure

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Banner
echo -e "${PURPLE}"
cat << "EOF"
    _    _            ____  _                       
   / \  | | __ _  ___/ ___|| | __ _ _   _  ___ _ __ 
  / _ \ | |/ _` |/ _ \___ \| |/ _` | | | |/ _ \ '__|
 / ___ \| | (_| | (_) |__) | | (_| | |_| |  __/ |   
/_/   \_\_|\__, |\___/____/|_|\__,_|\__, |\___|_|   
           |___/                    |___/            

🚀 Complete Production Setup Script
EOF
echo -e "${NC}"

# Configuration
APP_DIR="/opt/algoslayer"
APP_USER="algoslayer"
LOG_DIR="/var/log/algoslayer"
BACKUP_DIR="/var/backups/algoslayer"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root${NC}"
   echo "Please run: sudo bash setup_complete.sh"
   exit 1
fi

echo -e "${GREEN}✅ Running as root${NC}"

# Function to check if command was successful
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ Failed: $1${NC}"
        exit 1
    fi
}

# Function to generate secure random passwords
generate_password() {
    openssl rand -base64 12 | tr -d "=+/" | cut -c1-16
}

# Update system
echo -e "${BLUE}📦 Updating system packages...${NC}"
apt-get update -qq && apt-get upgrade -y -qq
check_status "System updated"

# Install essential packages
echo -e "${BLUE}🔧 Installing essential packages...${NC}"
apt-get install -y -qq \
    curl \
    git \
    wget \
    htop \
    vim \
    ufw \
    fail2ban \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    redis-server \
    nginx \
    certbot \
    python3-certbot-nginx \
    supervisor \
    postgresql \
    postgresql-contrib \
    jq \
    tmux
check_status "Essential packages installed"

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo -e "${BLUE}🐳 Installing Docker...${NC}"
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    check_status "Docker installed"
else
    echo -e "${GREEN}✅ Docker already installed${NC}"
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${BLUE}🐳 Installing Docker Compose...${NC}"
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    check_status "Docker Compose installed"
else
    echo -e "${GREEN}✅ Docker Compose already installed${NC}"
fi

# Configure firewall
echo -e "${BLUE}🔥 Configuring firewall...${NC}"
ufw --force enable
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 3000/tcp  # Grafana
ufw allow 9090/tcp  # Prometheus (restrict in production)
ufw allow 6379/tcp  # Redis (restrict in production)
check_status "Firewall configured"

# Configure fail2ban for security
echo -e "${BLUE}🛡️ Configuring fail2ban...${NC}"
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
logpath = %(sshd_log)s
backend = %(sshd_backend)s
EOF
systemctl enable fail2ban
systemctl restart fail2ban
check_status "Fail2ban configured"

# Create application user
echo -e "${BLUE}👤 Creating application user...${NC}"
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash $APP_USER
    usermod -aG docker $APP_USER
    check_status "Application user created"
else
    echo -e "${GREEN}✅ Application user already exists${NC}"
fi

# Create directory structure
echo -e "${BLUE}📁 Creating directory structure...${NC}"
mkdir -p $APP_DIR/{src,config,logs,data,backups,ssl,scripts}
mkdir -p $LOG_DIR
mkdir -p $BACKUP_DIR
check_status "Directories created"

# Set up PostgreSQL database
echo -e "${BLUE}🗄️ Setting up PostgreSQL database...${NC}"
DB_NAME="algoslayer"
DB_USER="algoslayer"
DB_PASS=$(generate_password)

sudo -u postgres psql << EOF
CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF
check_status "PostgreSQL database created"

# Configure Redis
echo -e "${BLUE}📦 Configuring Redis...${NC}"
cat > /etc/redis/redis.conf << EOF
bind 127.0.0.1
protected-mode yes
port 6379
dir /var/lib/redis
dbfilename dump.rdb
save 900 1
save 300 10
save 60 10000
maxmemory 256mb
maxmemory-policy allkeys-lru
appendonly yes
appendfilename "appendonly.aof"
EOF
systemctl enable redis-server
systemctl restart redis-server
check_status "Redis configured"

# Collect configuration
echo ""
echo -e "${CYAN}🔑 Configuration Setup${NC}"
echo -e "${CYAN}=====================${NC}"

# Function to validate input
validate_input() {
    local input=$1
    local pattern=$2
    local message=$3
    
    while [[ ! $input =~ $pattern ]]; do
        echo -e "${RED}Invalid input. $message${NC}"
        read -p "Please try again: " input
    done
    echo $input
}

# Get OpenAI API key
while [[ -z "$OPENAI_API_KEY" ]]; do
    read -p "🤖 Enter your OpenAI API Key (required): " OPENAI_API_KEY
done

# Telegram configuration (optional but recommended)
echo ""
echo -e "${YELLOW}📱 Telegram Bot Setup (Highly Recommended)${NC}"
echo "Telegram provides real-time alerts and monitoring"
read -p "Do you have a Telegram Bot Token? (y/N): " -n 1 HAS_TELEGRAM
echo ""

if [[ $HAS_TELEGRAM =~ ^[Yy]$ ]]; then
    read -p "📱 Enter Telegram Bot Token: " TELEGRAM_BOT_TOKEN
    read -p "📱 Enter Telegram Chat ID: " TELEGRAM_CHAT_ID
else
    echo -e "${YELLOW}⚠️  Telegram notifications disabled${NC}"
    TELEGRAM_BOT_TOKEN=""
    TELEGRAM_CHAT_ID=""
fi

# Trading configuration
echo ""
echo -e "${CYAN}💰 Trading Configuration${NC}"
echo -e "${YELLOW}⚠️  Please choose your trading mode carefully${NC}"
echo ""
echo "1) Prediction Only Mode (Safest - No Trading)"
echo "2) Paper Trading Mode (Simulated Trading)"
echo "3) Live Trading Mode (Real Money - Use with Caution!)"
echo ""
read -p "Select mode (1-3): " TRADING_MODE

case $TRADING_MODE in
    1)
        TRADING_ENABLED="false"
        PREDICTION_ONLY="true"
        PAPER_TRADING="true"
        echo -e "${GREEN}✅ Prediction Only Mode selected${NC}"
        ;;
    2)
        TRADING_ENABLED="true"
        PREDICTION_ONLY="false"
        PAPER_TRADING="true"
        echo -e "${BLUE}📄 Paper Trading Mode selected${NC}"
        ;;
    3)
        echo -e "${RED}⚠️  WARNING: Live Trading Mode uses REAL MONEY!${NC}"
        echo -e "${RED}You can lose your entire investment!${NC}"
        read -p "Type 'I UNDERSTAND THE RISKS' to continue: " CONFIRM
        if [[ "$CONFIRM" == "I UNDERSTAND THE RISKS" ]]; then
            TRADING_ENABLED="true"
            PREDICTION_ONLY="false"
            PAPER_TRADING="false"
            echo -e "${RED}💸 Live Trading Mode selected${NC}"
        else
            echo "Defaulting to Paper Trading Mode"
            TRADING_ENABLED="true"
            PREDICTION_ONLY="false"
            PAPER_TRADING="true"
        fi
        ;;
    *)
        echo "Invalid selection. Defaulting to Prediction Only Mode"
        TRADING_ENABLED="false"
        PREDICTION_ONLY="true"
        PAPER_TRADING="true"
        ;;
esac

# Interactive Brokers configuration (if trading enabled)
if [[ "$TRADING_ENABLED" == "true" ]]; then
    echo ""
    echo -e "${CYAN}🏦 Interactive Brokers Configuration${NC}"
    read -p "Do you have IBKR credentials? (y/N): " -n 1 HAS_IBKR
    echo ""
    if [[ $HAS_IBKR =~ ^[Yy]$ ]]; then
        read -p "IBKR Username: " IBKR_USERNAME
        read -s -p "IBKR Password: " IBKR_PASSWORD
        echo ""
        IBKR_REQUIRED="true"
    else
        IBKR_USERNAME=""
        IBKR_PASSWORD=""
        IBKR_REQUIRED="false"
    fi
else
    IBKR_USERNAME=""
    IBKR_PASSWORD=""
    IBKR_REQUIRED="false"
fi

# Risk management settings
echo ""
echo -e "${CYAN}⚡ Risk Management Settings${NC}"
read -p "Starting Capital (default 1000): " STARTING_CAPITAL
STARTING_CAPITAL=${STARTING_CAPITAL:-1000}
read -p "Max Position Size (default 200): " MAX_POSITION_SIZE
MAX_POSITION_SIZE=${MAX_POSITION_SIZE:-200}
read -p "Max Daily Loss (default 50): " MAX_DAILY_LOSS
MAX_DAILY_LOSS=${MAX_DAILY_LOSS:-50}
read -p "Confidence Threshold (0.0-1.0, default 0.35): " CONFIDENCE_THRESHOLD
CONFIDENCE_THRESHOLD=${CONFIDENCE_THRESHOLD:-0.35}

# Generate secure passwords for services
GRAFANA_PASSWORD=$(generate_password)
POSTGRES_PASSWORD=$DB_PASS
REDIS_PASSWORD=$(generate_password)

# Create .env file
echo -e "${BLUE}📝 Creating environment configuration...${NC}"
cat > $APP_DIR/.env << EOF
# AlgoSlayer Production Configuration
# Generated: $(date)

# === TRADING CONFIGURATION ===
TRADING_ENABLED=${TRADING_ENABLED}
PAPER_TRADING=${PAPER_TRADING}
PREDICTION_ONLY=${PREDICTION_ONLY}
IBKR_REQUIRED=${IBKR_REQUIRED}
AUTO_CONNECT_IBKR=true

# === API KEYS ===
OPENAI_API_KEY=${OPENAI_API_KEY}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}

# === IBKR CONFIGURATION ===
IBKR_USERNAME=${IBKR_USERNAME}
IBKR_PASSWORD=${IBKR_PASSWORD}
IBKR_HOST=ibkr-gateway
IBKR_PAPER_PORT=7497
IBKR_LIVE_PORT=7496
IBKR_CLIENT_ID=1

# === RISK MANAGEMENT ===
STARTING_CAPITAL=${STARTING_CAPITAL}
MAX_POSITION_SIZE=${MAX_POSITION_SIZE}
MAX_DAILY_LOSS=${MAX_DAILY_LOSS}
STOP_LOSS_PERCENTAGE=0.15
CONFIDENCE_THRESHOLD=${CONFIDENCE_THRESHOLD}

# === SYSTEM CONFIGURATION ===
LOG_LEVEL=INFO
PREDICTION_INTERVAL_MINUTES=15
TIMEZONE=America/New_York

# === DATABASE ===
DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@localhost:5432/${DB_NAME}
REDIS_URL=redis://:${REDIS_PASSWORD}@localhost:6379/0

# === MONITORING ===
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}
PROMETHEUS_RETENTION=30d

# === PATHS ===
APP_DIR=${APP_DIR}
LOG_DIR=${LOG_DIR}
BACKUP_DIR=${BACKUP_DIR}
EOF

chmod 600 $APP_DIR/.env
check_status "Environment configuration created"

# Create monitoring configuration
echo -e "${BLUE}📊 Setting up monitoring...${NC}"
cat > $APP_DIR/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'algoslayer'
    static_configs:
      - targets: ['localhost:8000']
    
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
    
  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
EOF

# Create nginx configuration
echo -e "${BLUE}🌐 Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/algoslayer << EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /grafana/ {
        proxy_pass http://localhost:3000/;
        proxy_set_header Host \$host;
    }
    
    location /prometheus/ {
        proxy_pass http://localhost:9090/;
        proxy_set_header Host \$host;
    }
}
EOF

ln -sf /etc/nginx/sites-available/algoslayer /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
check_status "Nginx configured"

# Create systemd service
echo -e "${BLUE}⚙️ Creating system service...${NC}"
cat > /etc/systemd/system/algoslayer.service << EOF
[Unit]
Description=AlgoSlayer Trading System
After=network.target redis.service postgresql.service docker.service
Requires=redis.service postgresql.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=/usr/bin:/usr/local/bin"
EnvironmentFile=$APP_DIR/.env
ExecStartPre=/bin/bash -c 'docker-compose pull'
ExecStart=/usr/local/bin/docker-compose up
ExecStop=/usr/local/bin/docker-compose down
Restart=always
RestartSec=10
StandardOutput=append:$LOG_DIR/algoslayer.log
StandardError=append:$LOG_DIR/algoslayer.error.log

[Install]
WantedBy=multi-user.target
EOF

# Create backup script
echo -e "${BLUE}💾 Creating backup script...${NC}"
cat > $APP_DIR/scripts/backup.sh << 'EOF'
#!/bin/bash
# AlgoSlayer Backup Script

BACKUP_DIR="/var/backups/algoslayer"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/algoslayer_backup_$TIMESTAMP.tar.gz"

# Create backup
echo "Starting backup..."
cd /opt/algoslayer
tar -czf $BACKUP_FILE data/ logs/ .env

# Backup database
pg_dump algoslayer | gzip > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
EOF

chmod +x $APP_DIR/scripts/backup.sh

# Create backup cron job
echo "0 2 * * * $APP_USER $APP_DIR/scripts/backup.sh" > /etc/cron.d/algoslayer-backup

# Create health check script
echo -e "${BLUE}🏥 Creating health check script...${NC}"
cat > $APP_DIR/scripts/health_check.sh << 'EOF'
#!/bin/bash
# AlgoSlayer Health Check Script

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "AlgoSlayer System Health Check"
echo "=============================="

# Check services
check_service() {
    if systemctl is-active --quiet $1; then
        echo -e "$1: ${GREEN}✓ Running${NC}"
    else
        echo -e "$1: ${RED}✗ Not Running${NC}"
    fi
}

check_service "algoslayer"
check_service "docker"
check_service "redis"
check_service "postgresql"
check_service "nginx"

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 80 ]; then
    echo -e "Disk Space: ${GREEN}✓ ${DISK_USAGE}% used${NC}"
else
    echo -e "Disk Space: ${YELLOW}⚠ ${DISK_USAGE}% used${NC}"
fi

# Check API endpoints
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "API Health: ${GREEN}✓ Healthy${NC}"
else
    echo -e "API Health: ${RED}✗ Unhealthy${NC}"
fi

# Check last prediction time
if [ -f /opt/algoslayer/data/last_prediction.txt ]; then
    LAST_PREDICTION=$(cat /opt/algoslayer/data/last_prediction.txt)
    echo -e "Last Prediction: ${GREEN}$LAST_PREDICTION${NC}"
fi
EOF

chmod +x $APP_DIR/scripts/health_check.sh

# Install Python dependencies globally (for scripts)
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip3 install --upgrade pip
pip3 install supervisor docker-compose
check_status "Python dependencies installed"

# Check if application code exists
if [[ ! -f "$APP_DIR/run_server.py" ]]; then
    echo ""
    echo -e "${YELLOW}⚠️ Application code not found${NC}"
    echo -e "${BLUE}📤 Please upload your code to: $APP_DIR${NC}"
    echo ""
    echo "You can use these commands from your local machine:"
    echo -e "${CYAN}rsync -avz --exclude='.git' --exclude='__pycache__' ./ root@$(curl -s ifconfig.me):$APP_DIR/${NC}"
    echo ""
    read -p "Press Enter when code is uploaded..."
fi

# Set permissions
echo -e "${BLUE}🔒 Setting permissions...${NC}"
chown -R $APP_USER:$APP_USER $APP_DIR
chown -R $APP_USER:$APP_USER $LOG_DIR
chmod -R 755 $APP_DIR
chmod 600 $APP_DIR/.env
check_status "Permissions set"

# Enable and start services
echo -e "${BLUE}🚀 Starting services...${NC}"
systemctl daemon-reload
systemctl enable algoslayer
systemctl enable redis-server
systemctl enable postgresql
systemctl enable nginx
systemctl enable docker

# Generate SSL certificate (optional)
echo ""
read -p "Do you have a domain name for SSL? (y/N): " -n 1 HAS_DOMAIN
echo ""
if [[ $HAS_DOMAIN =~ ^[Yy]$ ]]; then
    read -p "Enter your domain name: " DOMAIN_NAME
    certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos --email admin@$DOMAIN_NAME
fi

# Create summary file
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "Unable to detect")

cat > $APP_DIR/DEPLOYMENT_INFO.txt << EOF
AlgoSlayer Deployment Information
=================================
Deployed: $(date)
Server IP: $SERVER_IP
App Directory: $APP_DIR
Log Directory: $LOG_DIR
Backup Directory: $BACKUP_DIR

Trading Configuration:
- Mode: $(if [[ "$TRADING_ENABLED" == "true" ]]; then echo "Enabled"; else echo "Disabled"; fi)
- Paper Trading: $(if [[ "$PAPER_TRADING" == "true" ]]; then echo "Yes"; else echo "No (LIVE)"; fi)
- Prediction Only: $(if [[ "$PREDICTION_ONLY" == "true" ]]; then echo "Yes"; else echo "No"; fi)

Services:
- PostgreSQL Database: $DB_NAME (User: $DB_USER, Pass: $DB_PASS)
- Redis: localhost:6379 (Password: $REDIS_PASSWORD)
- Grafana: http://$SERVER_IP:3000 (admin/$GRAFANA_PASSWORD)
- Prometheus: http://$SERVER_IP:9090

Commands:
- Check status: systemctl status algoslayer
- View logs: journalctl -u algoslayer -f
- Health check: $APP_DIR/scripts/health_check.sh
- Manual backup: $APP_DIR/scripts/backup.sh
- Restart: systemctl restart algoslayer

Security:
- Firewall: Enabled (ufw)
- Fail2ban: Active
- SSL: $(if [[ $HAS_DOMAIN =~ ^[Yy]$ ]]; then echo "Configured for $DOMAIN_NAME"; else echo "Not configured"; fi)

Telegram Bot:
$(if [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then echo "- Status: Configured"; else echo "- Status: Not configured"; fi)
$(if [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then echo "- Commands: /status, /help, /trades, /performance"; fi)
EOF

# Start the application if code exists
if [[ -f "$APP_DIR/run_server.py" ]]; then
    echo -e "${BLUE}🚀 Starting AlgoSlayer...${NC}"
    systemctl start algoslayer
    sleep 5
    
    if systemctl is-active --quiet algoslayer; then
        echo -e "${GREEN}✅ AlgoSlayer is running!${NC}"
    else
        echo -e "${YELLOW}⚠️ AlgoSlayer may have issues. Check logs:${NC}"
        echo "journalctl -u algoslayer -f"
    fi
fi

# Final summary
echo ""
echo -e "${GREEN}🎉 SETUP COMPLETE!${NC}"
echo -e "${GREEN}==================${NC}"
echo ""
echo -e "${BLUE}📊 Server Information:${NC}"
echo "   IP Address: $SERVER_IP"
echo "   App Directory: $APP_DIR"
echo ""
echo -e "${BLUE}🔗 Access URLs:${NC}"
echo "   Main App: http://$SERVER_IP"
echo "   Grafana: http://$SERVER_IP:3000 (admin/$GRAFANA_PASSWORD)"
if [[ $HAS_DOMAIN =~ ^[Yy]$ ]]; then
    echo "   SSL Domain: https://$DOMAIN_NAME"
fi
echo ""
echo -e "${BLUE}💰 Trading Status:${NC}"
if [[ "$TRADING_ENABLED" == "true" ]]; then
    if [[ "$PAPER_TRADING" == "true" ]]; then
        echo -e "   ${GREEN}Paper Trading Mode (Safe)${NC}"
    else
        echo -e "   ${RED}⚠️  LIVE TRADING MODE (Real Money at Risk!)${NC}"
    fi
else
    echo -e "   ${YELLOW}Prediction Only Mode${NC}"
fi
echo ""
if [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then
    echo -e "${BLUE}📱 Telegram Bot:${NC}"
    echo "   Bot is configured and will send notifications"
    echo "   Commands: /status, /help, /trades, /performance"
fi
echo ""
echo -e "${YELLOW}📚 Important Files:${NC}"
echo "   Config: $APP_DIR/.env"
echo "   Logs: $LOG_DIR/"
echo "   Info: $APP_DIR/DEPLOYMENT_INFO.txt"
echo ""
echo -e "${CYAN}🚀 Your AlgoSlayer system is ready!${NC}"
echo ""
echo "Next steps:"
echo "1. Check system health: $APP_DIR/scripts/health_check.sh"
echo "2. Monitor logs: journalctl -u algoslayer -f"
if [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then
    echo "3. Check Telegram bot for notifications"
fi
echo ""
echo -e "${GREEN}Happy Trading! 🤖📈${NC}"
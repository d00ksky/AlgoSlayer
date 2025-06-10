# AlgoSlayer - Full Cloud Trading System with IBKR Gateway
FROM ubuntu:22.04

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /opt/algoslayer

# Install system dependencies for full cloud deployment
RUN apt-get update && apt-get install -y \
    # Python and build tools
    python3.11 \
    python3-pip \
    python3-venv \
    python3-dev \
    gcc g++ \
    build-essential \
    wget curl git \
    # IBKR Gateway requirements
    openjdk-11-jdk \
    xvfb \
    x11vnc \
    fluxbox \
    # System utilities
    htop nano \
    supervisor \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install TA-Lib (optional technical analysis)
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    ./configure --prefix=/usr && \
    make && make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Create Python virtual environment
RUN python3 -m venv /opt/algoslayer/venv
ENV PATH="/opt/algoslayer/venv/bin:$PATH"

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data backups ibkr/config

# Set environment variables
ENV PYTHONPATH=/opt/algoslayer
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:1
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

# Create supervisor configuration for multi-service management
RUN mkdir -p /etc/supervisor/conf.d

# Create supervisor configs
RUN echo '[program:algoslayer]\n\
command=/opt/algoslayer/venv/bin/python run_server.py\n\
directory=/opt/algoslayer\n\
user=trader\n\
autorestart=true\n\
stdout_logfile=/opt/algoslayer/logs/algoslayer.log\n\
stderr_logfile=/opt/algoslayer/logs/algoslayer_error.log\n\
environment=PYTHONPATH="/opt/algoslayer"' > /etc/supervisor/conf.d/algoslayer.conf

RUN echo '[program:xvfb]\n\
command=Xvfb :1 -screen 0 1024x768x24\n\
user=trader\n\
autorestart=true\n\
stdout_logfile=/opt/algoslayer/logs/xvfb.log\n\
stderr_logfile=/opt/algoslayer/logs/xvfb_error.log' > /etc/supervisor/conf.d/xvfb.conf

RUN echo '[program:vnc]\n\
command=x11vnc -display :1 -nopw -listen localhost -xkb -ncache 10 -ncache_cr -forever\n\
user=trader\n\
autorestart=true\n\
stdout_logfile=/opt/algoslayer/logs/vnc.log\n\
stderr_logfile=/opt/algoslayer/logs/vnc_error.log\n\
depends_on=xvfb' > /etc/supervisor/conf.d/vnc.conf

# Create trader user with proper permissions
RUN useradd -m -u 1000 trader && \
    chown -R trader:trader /opt/algoslayer && \
    usermod -aG sudo trader

# Switch to trader user
USER trader

# Health check for the trading system
HEALTHCHECK --interval=60s --timeout=30s --start-period=30s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Expose ports
EXPOSE 8000 5900 7497 7496

# Create startup script
RUN echo '#!/bin/bash\n\
# Start all services via supervisor\n\
exec /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf' > /opt/algoslayer/start.sh && \
    chmod +x /opt/algoslayer/start.sh

# Default command
CMD ["/opt/algoslayer/start.sh"] 
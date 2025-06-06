#!/bin/bash

# Codex launch script for AlgoSlayer
# Sets up Python environment and installs all dependencies

set -e

# Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install system packages required for TA-Lib and other builds
sudo apt-get update
sudo apt-get install -y \
  gcc g++ make wget curl git build-essential \
  libssl-dev libffi-dev python3 python3-dev python3-venv python3-pip

# Build and install TA-Lib (required by some technical analysis components)
if ! python -c "import talib" 2>/dev/null; then
    wget -q http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
    tar -xzf ta-lib-0.4.0-src.tar.gz
    cd ta-lib
    ./configure --prefix=/usr
    make
    sudo make install
    cd ..
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz
fi

# Install Python dependencies
pip install -r requirements.txt

echo "\n✅ Environment setup complete. Activate with 'source .venv/bin/activate' and run 'python run_server.py'"


#!/bin/bash
# Quick Cloud Data Fetch
cd "$(dirname "$0")"

echo "📥 Fetching latest data from cloud server..."
python fetch_cloud_data.py --quick

echo "📁 Check cloud_data_analysis/ for results"

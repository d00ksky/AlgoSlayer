#!/usr/bin/env python3
"""
Fetch cloud server data for local development
Retrieves logs, predictions, and performance data from production server
"""
import os
import subprocess
import json
from datetime import datetime, timedelta
from loguru import logger
import argparse

# Cloud server configuration
CLOUD_SERVER = "root@64.226.96.90"
LOCAL_ANALYSIS_DIR = "cloud_data_analysis"

def run_ssh_command(command):
    """Execute command on cloud server via SSH"""
    ssh_cmd = f"ssh -o StrictHostKeyChecking=no {CLOUD_SERVER} '{command}'"
    try:
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"SSH command failed: {result.stderr}")
            return None
        return result.stdout
    except Exception as e:
        logger.error(f"SSH error: {e}")
        return None

def fetch_recent_logs(days=2):
    """Fetch recent trading logs from cloud server"""
    logger.info(f"📥 Fetching logs from last {days} days...")
    
    # Create local directory
    os.makedirs(f"{LOCAL_ANALYSIS_DIR}/logs", exist_ok=True)
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Download logs
    for i in range(days + 1):
        date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        log_file = f"rtx_trading_{date}.log"
        
        # Check if log exists
        exists = run_ssh_command(f"test -f /opt/rtx-trading/logs/{log_file} && echo 'exists'")
        if exists and 'exists' in exists:
            logger.info(f"📄 Downloading {log_file}...")
            subprocess.run(f"scp -o StrictHostKeyChecking=no {CLOUD_SERVER}:/opt/rtx-trading/logs/{log_file} {LOCAL_ANALYSIS_DIR}/logs/", shell=True)

def analyze_predictions():
    """Analyze predictions from cloud server logs"""
    logger.info("🔍 Analyzing predictions...")
    
    # Extract predictions with grep
    predictions_cmd = """
    cd /opt/rtx-trading && 
    grep -E 'Prediction cycle complete' logs/rtx_trading_*.log | 
    grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}|BUY|SELL|HOLD|[0-9]+\\.[0-9]+%' |
    paste -d',' - - - |
    tail -100
    """
    
    predictions_raw = run_ssh_command(predictions_cmd)
    if not predictions_raw:
        return None
    
    # Parse predictions
    predictions = []
    for line in predictions_raw.strip().split('\n'):
        if ',' in line:
            parts = line.split(',')
            if len(parts) >= 3:
                predictions.append({
                    'timestamp': parts[0],
                    'direction': parts[1],
                    'confidence': float(parts[2])
                })
    
    # Save predictions
    with open(f"{LOCAL_ANALYSIS_DIR}/predictions.json", 'w') as f:
        json.dump(predictions, f, indent=2)
    
    return predictions

def get_signal_performance():
    """Get individual signal performance from logs"""
    logger.info("📊 Analyzing signal performance...")
    
    signals = [
        'news_sentiment', 'technical_analysis', 'options_flow', 
        'volatility_analysis', 'momentum', 'sector_correlation',
        'mean_reversion', 'market_regime'
    ]
    
    signal_data = {}
    
    for signal in signals:
        # Count signal occurrences and directions
        cmd = f"""
        cd /opt/rtx-trading && 
        grep -A5 '{signal}' logs/rtx_trading_*.log | 
        grep -E 'BUY|SELL|HOLD' | 
        head -20
        """
        
        result = run_ssh_command(cmd)
        if result:
            signal_data[signal] = result.strip()
    
    # Save signal data
    with open(f"{LOCAL_ANALYSIS_DIR}/signal_performance.json", 'w') as f:
        json.dump(signal_data, f, indent=2)
    
    return signal_data

def get_system_stats():
    """Get system statistics and health"""
    logger.info("💻 Getting system statistics...")
    
    stats = {}
    
    # Service status
    service_status = run_ssh_command("systemctl status rtx-trading --no-pager -n 0")
    if service_status:
        stats['service_active'] = 'active (running)' in service_status
        stats['service_status'] = service_status.strip()
    
    # Uptime
    uptime = run_ssh_command("systemctl show rtx-trading --property=ActiveEnterTimestamp")
    if uptime:
        stats['uptime'] = uptime.strip()
    
    # Memory usage
    memory = run_ssh_command("systemctl show rtx-trading --property=MemoryCurrent")
    if memory:
        stats['memory_usage'] = memory.strip()
    
    # Disk usage
    disk = run_ssh_command("df -h /opt/rtx-trading")
    if disk:
        stats['disk_usage'] = disk.strip()
    
    # Environment variables (sanitized)
    env_vars = run_ssh_command("grep -E '^TRADING_ENABLED|^PAPER_TRADING|^PREDICTION_ONLY|^CONFIDENCE_THRESHOLD' /opt/rtx-trading/.env")
    if env_vars:
        stats['config'] = env_vars.strip()
    
    # Save stats
    with open(f"{LOCAL_ANALYSIS_DIR}/system_stats.json", 'w') as f:
        json.dump(stats, f, indent=2)
    
    return stats

def get_confidence_distribution():
    """Analyze confidence distribution"""
    logger.info("📈 Analyzing confidence distribution...")
    
    cmd = """
    cd /opt/rtx-trading && 
    grep -oE '[0-9]+\\.[0-9]+%' logs/rtx_trading_*.log | 
    grep -E 'complete' -B1 | 
    grep -oE '[0-9]+\\.[0-9]+' | 
    sort -n | 
    tail -200
    """
    
    confidence_values = run_ssh_command(cmd)
    if not confidence_values:
        return None
    
    values = [float(v) for v in confidence_values.strip().split('\n') if v]
    
    # Calculate statistics
    if values:
        stats = {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'above_80': len([v for v in values if v >= 80]),
            'above_70': len([v for v in values if v >= 70]),
            'above_60': len([v for v in values if v >= 60])
        }
        
        # Save distribution
        with open(f"{LOCAL_ANALYSIS_DIR}/confidence_distribution.json", 'w') as f:
            json.dump({
                'values': values,
                'stats': stats
            }, f, indent=2)
        
        return stats
    
    return None

def generate_summary_report():
    """Generate summary report of cloud data"""
    logger.info("📝 Generating summary report...")
    
    report = []
    report.append("# RTX Trading System - Cloud Data Summary")
    report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Server: {CLOUD_SERVER}")
    
    # System status
    if os.path.exists(f"{LOCAL_ANALYSIS_DIR}/system_stats.json"):
        with open(f"{LOCAL_ANALYSIS_DIR}/system_stats.json") as f:
            stats = json.load(f)
            report.append("\n## System Status")
            report.append(f"- Service: {'🟢 Active' if stats.get('service_active') else '🔴 Inactive'}")
            if 'config' in stats:
                report.append("\n### Configuration")
                report.append("```")
                report.append(stats['config'])
                report.append("```")
    
    # Predictions
    if os.path.exists(f"{LOCAL_ANALYSIS_DIR}/predictions.json"):
        with open(f"{LOCAL_ANALYSIS_DIR}/predictions.json") as f:
            predictions = json.load(f)
            if predictions:
                report.append("\n## Recent Predictions")
                report.append(f"- Total predictions: {len(predictions)}")
                
                # Direction breakdown
                buy_count = len([p for p in predictions if p['direction'] == 'BUY'])
                sell_count = len([p for p in predictions if p['direction'] == 'SELL'])
                hold_count = len([p for p in predictions if p['direction'] == 'HOLD'])
                
                report.append(f"- BUY: {buy_count} ({buy_count/len(predictions)*100:.1f}%)")
                report.append(f"- SELL: {sell_count} ({sell_count/len(predictions)*100:.1f}%)")
                report.append(f"- HOLD: {hold_count} ({hold_count/len(predictions)*100:.1f}%)")
                
                # High confidence predictions
                high_conf = [p for p in predictions if p['confidence'] >= 80]
                report.append(f"\n### High Confidence Predictions (≥80%)")
                report.append(f"- Count: {len(high_conf)}")
                if high_conf:
                    report.append("\nLatest high-confidence signals:")
                    for p in high_conf[-5:]:
                        report.append(f"- {p['timestamp']}: {p['direction']} ({p['confidence']}%)")
    
    # Confidence distribution
    if os.path.exists(f"{LOCAL_ANALYSIS_DIR}/confidence_distribution.json"):
        with open(f"{LOCAL_ANALYSIS_DIR}/confidence_distribution.json") as f:
            conf_data = json.load(f)
            if 'stats' in conf_data:
                stats = conf_data['stats']
                report.append("\n## Confidence Distribution")
                report.append(f"- Average confidence: {stats['avg']:.1f}%")
                report.append(f"- Min/Max: {stats['min']:.1f}% / {stats['max']:.1f}%")
                report.append(f"- Predictions ≥80%: {stats['above_80']} ({stats['above_80']/stats['count']*100:.1f}%)")
                report.append(f"- Predictions ≥70%: {stats['above_70']} ({stats['above_70']/stats['count']*100:.1f}%)")
    
    # Save report
    report_text = '\n'.join(report)
    with open(f"{LOCAL_ANALYSIS_DIR}/summary_report.md", 'w') as f:
        f.write(report_text)
    
    logger.success(f"✅ Report saved to {LOCAL_ANALYSIS_DIR}/summary_report.md")
    print(f"\n{report_text}")

def main():
    """Main function to fetch and analyze cloud data"""
    parser = argparse.ArgumentParser(description='Fetch and analyze RTX trading data from cloud server')
    parser.add_argument('--days', type=int, default=2, help='Number of days of logs to fetch')
    parser.add_argument('--quick', action='store_true', help='Quick analysis without downloading logs')
    args = parser.parse_args()
    
    logger.info(f"🚀 Starting cloud data fetch from {CLOUD_SERVER}")
    
    # Create analysis directory
    os.makedirs(LOCAL_ANALYSIS_DIR, exist_ok=True)
    
    # Fetch data
    if not args.quick:
        fetch_recent_logs(args.days)
    
    # Analyze data
    predictions = analyze_predictions()
    if predictions:
        logger.success(f"✅ Analyzed {len(predictions)} predictions")
    
    signal_perf = get_signal_performance()
    if signal_perf:
        logger.success(f"✅ Analyzed {len(signal_perf)} signals")
    
    system_stats = get_system_stats()
    if system_stats:
        logger.success("✅ Retrieved system statistics")
    
    conf_dist = get_confidence_distribution()
    if conf_dist:
        logger.success(f"✅ Analyzed confidence distribution ({conf_dist['count']} samples)")
    
    # Generate report
    generate_summary_report()
    
    logger.info(f"📁 All data saved to: {LOCAL_ANALYSIS_DIR}/")

if __name__ == "__main__":
    main()
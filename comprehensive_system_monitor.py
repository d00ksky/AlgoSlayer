#!/usr/bin/env python3
"""
Comprehensive System Health Monitor for AlgoSlayer
Weekend upgrade: Complete system monitoring and diagnostics
"""
import asyncio
import json
import sqlite3
import subprocess
import psutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

class AlgoSlayerHealthMonitor:
    """Comprehensive system health monitoring"""
    
    def __init__(self):
        self.base_path = Path("/opt/rtx-trading")
        self.services = ["rtx-trading.service"]
        self.databases = [
            "algoslayer_multi_strategy.db",
            "options_performance_conservative.db", 
            "options_performance_moderate.db",
            "options_performance_aggressive.db",
            "options_performance_scalping.db",
            "options_performance_swing.db", 
            "options_performance_momentum.db",
            "options_performance_volatility.db",
            "options_performance_mean_reversion.db"
        ]
        self.critical_processes = ["python", "java"]  # Trading system + IB Gateway
        
    def check_system_resources(self) -> Dict:
        """Check CPU, memory, disk usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024**3)
            
            # Load average (Linux specific)
            try:
                load_avg = psutil.getloadavg()
            except:
                load_avg = (0, 0, 0)
            
            status = "healthy"
            issues = []
            
            # Check thresholds
            if cpu_percent > 80:
                status = "warning"
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            if memory_percent > 85:
                status = "critical" if memory_percent > 95 else "warning" 
                issues.append(f"High memory usage: {memory_percent:.1f}%")
                
            if disk_percent > 90:
                status = "critical"
                issues.append(f"Low disk space: {disk_percent:.1f}% used")
                
            if memory_available_gb < 0.5:
                status = "critical"
                issues.append(f"Very low memory: {memory_available_gb:.1f}GB available")
            
            return {
                "status": status,
                "issues": issues,
                "metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "memory_available_gb": round(memory_available_gb, 2),
                    "disk_percent": disk_percent,
                    "disk_free_gb": round(disk_free_gb, 2),
                    "load_average": [round(x, 2) for x in load_avg]
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "issues": [f"Resource check failed: {e}"],
                "metrics": {}
            }
    
    def check_services(self) -> Dict:
        """Check systemd services status"""
        results = {}
        overall_status = "healthy"
        issues = []
        
        for service in self.services:
            try:
                # Check if service is active
                result = subprocess.run(
                    ["systemctl", "is-active", service],
                    capture_output=True, text=True, timeout=5
                )
                is_active = result.stdout.strip() == "active"
                
                # Get detailed status
                status_result = subprocess.run(
                    ["systemctl", "status", service, "--no-pager", "-l"],
                    capture_output=True, text=True, timeout=10
                )
                
                # Extract key info
                status_lines = status_result.stdout.split('\n')
                main_pid = "unknown"
                memory_usage = "unknown"
                
                for line in status_lines:
                    if "Main PID:" in line:
                        main_pid = line.split("Main PID:")[1].split()[0]
                    elif "Memory:" in line:
                        memory_usage = line.split("Memory:")[1].strip().split()[0]
                
                results[service] = {
                    "active": is_active,
                    "main_pid": main_pid,
                    "memory_usage": memory_usage,
                    "status": "healthy" if is_active else "critical"
                }
                
                if not is_active:
                    overall_status = "critical"
                    issues.append(f"{service} is not active")
                    
            except Exception as e:
                results[service] = {
                    "active": False,
                    "error": str(e),
                    "status": "error"
                }
                overall_status = "error"
                issues.append(f"Failed to check {service}: {e}")
        
        return {
            "status": overall_status,
            "issues": issues,
            "services": results
        }
    
    def check_databases(self) -> Dict:
        """Check database integrity and performance"""
        results = {}
        overall_status = "healthy"
        issues = []
        
        for db_name in self.databases:
            db_path = self.base_path / "data" / db_name
            
            try:
                if not db_path.exists():
                    results[db_name] = {
                        "exists": False,
                        "status": "warning",
                        "size_mb": 0
                    }
                    issues.append(f"Database {db_name} does not exist")
                    if overall_status == "healthy":
                        overall_status = "warning"
                    continue
                
                # Check file size
                size_bytes = db_path.stat().st_size
                size_mb = round(size_bytes / (1024**2), 2)
                
                # Quick integrity check
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                # Pragma integrity check
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]
                
                # Get table info
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Count records in main tables
                record_counts = {}
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        record_counts[table] = cursor.fetchone()[0]
                    except:
                        record_counts[table] = "error"
                
                conn.close()
                
                # Determine status
                status = "healthy"
                db_issues = []
                
                if integrity_result != "ok":
                    status = "critical"
                    db_issues.append("Integrity check failed")
                
                if size_bytes == 0:
                    status = "critical"
                    db_issues.append("Database is empty (0 bytes)")
                
                results[db_name] = {
                    "exists": True,
                    "size_mb": size_mb,
                    "integrity": integrity_result == "ok",
                    "tables": len(tables),
                    "record_counts": record_counts,
                    "status": status,
                    "issues": db_issues
                }
                
                if status == "critical":
                    overall_status = "critical"
                    issues.extend([f"{db_name}: {issue}" for issue in db_issues])
                elif status == "warning" and overall_status == "healthy":
                    overall_status = "warning"
                    
            except Exception as e:
                results[db_name] = {
                    "exists": db_path.exists(),
                    "error": str(e),
                    "status": "error"
                }
                overall_status = "error"
                issues.append(f"Database check failed for {db_name}: {e}")
        
        return {
            "status": overall_status,
            "issues": issues,
            "databases": results
        }
    
    def check_processes(self) -> Dict:
        """Check critical processes"""
        results = {}
        overall_status = "healthy"
        issues = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
            try:
                proc_info = proc.info
                proc_name = proc_info['name']
                cmdline = ' '.join(proc_info['cmdline'] or [])
                
                # Check for trading system processes
                if ('rtx-trading' in cmdline or 
                    'run_multi_strategy.py' in cmdline or
                    'enhanced_automated_ml.py' in cmdline):
                    
                    results[f"trading_{proc_info['pid']}"] = {
                        "pid": proc_info['pid'],
                        "name": proc_name,
                        "cmdline": cmdline[:100] + "..." if len(cmdline) > 100 else cmdline,
                        "cpu_percent": proc_info['cpu_percent'],
                        "memory_percent": proc_info['memory_percent'],
                        "status": "healthy"
                    }
                
                # Check for IB Gateway
                elif 'ibgateway' in cmdline.lower() or 'IBJts' in cmdline:
                    results[f"ib_gateway_{proc_info['pid']}"] = {
                        "pid": proc_info['pid'],
                        "name": proc_name,
                        "cmdline": "IB Gateway Java Process",
                        "cpu_percent": proc_info['cpu_percent'],
                        "memory_percent": proc_info['memory_percent'],
                        "status": "healthy"
                    }
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        # Check if we have required processes
        trading_processes = [k for k in results.keys() if k.startswith('trading_')]
        ib_processes = [k for k in results.keys() if k.startswith('ib_gateway_')]
        
        if not trading_processes:
            overall_status = "critical"
            issues.append("No trading system processes found")
            
        if not ib_processes:
            overall_status = "warning"
            issues.append("IB Gateway not detected")
            
        return {
            "status": overall_status,
            "issues": issues,
            "processes": results,
            "summary": {
                "trading_processes": len(trading_processes),
                "ib_processes": len(ib_processes),
                "total_monitored": len(results)
            }
        }
    
    def check_telegram_bot(self) -> Dict:
        """Check Telegram bot status and prevent 409 conflicts"""
        try:
            # Check if multiple telegram processes exist
            telegram_processes = []
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'telegram' in cmdline.lower() and 'python' in cmdline.lower():
                        telegram_processes.append({
                            "pid": proc.info['pid'],
                            "cmdline": cmdline[:100] + "..." if len(cmdline) > 100 else cmdline
                        })
                except:
                    continue
            
            status = "healthy"
            issues = []
            
            # Check for multiple instances (potential 409 cause)
            if len(telegram_processes) > 1:
                status = "warning"
                issues.append(f"Multiple Telegram processes detected ({len(telegram_processes)})")
            
            # Test bot configuration
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            
            config_status = "configured" if (bot_token and chat_id) else "missing"
            if config_status == "missing":
                status = "warning"
                issues.append("Telegram credentials not configured")
            
            return {
                "status": status,
                "issues": issues,
                "processes": telegram_processes,
                "config_status": config_status,
                "bot_token_configured": bool(bot_token),
                "chat_id_configured": bool(chat_id)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "issues": [f"Telegram check failed: {e}"],
                "processes": [],
                "config_status": "error"
            }
    
    def check_network_connectivity(self) -> Dict:
        """Check external API connectivity"""
        endpoints = [
            {"name": "Telegram API", "host": "api.telegram.org", "port": 443},
            {"name": "Yahoo Finance", "host": "query1.finance.yahoo.com", "port": 443},
            {"name": "Interactive Brokers", "host": "www.interactivebrokers.com", "port": 443}
        ]
        
        results = {}
        overall_status = "healthy"
        issues = []
        
        for endpoint in endpoints:
            try:
                # Simple socket connection test
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((endpoint["host"], endpoint["port"]))
                sock.close()
                
                is_reachable = result == 0
                results[endpoint["name"]] = {
                    "host": endpoint["host"],
                    "port": endpoint["port"],
                    "reachable": is_reachable,
                    "status": "healthy" if is_reachable else "warning"
                }
                
                if not is_reachable:
                    if overall_status == "healthy":
                        overall_status = "warning"
                    issues.append(f"{endpoint['name']} unreachable")
                    
            except Exception as e:
                results[endpoint["name"]] = {
                    "host": endpoint["host"],
                    "error": str(e),
                    "status": "error"
                }
                overall_status = "error"
                issues.append(f"{endpoint['name']} check failed: {e}")
        
        return {
            "status": overall_status,
            "issues": issues,
            "endpoints": results
        }
    
    async def run_comprehensive_check(self) -> Dict:
        """Run all health checks"""
        print("🔍 Running comprehensive system health check...")
        
        start_time = time.time()
        
        # Run all checks
        checks = {
            "system_resources": self.check_system_resources(),
            "services": self.check_services(),
            "databases": self.check_databases(),
            "processes": self.check_processes(),
            "telegram_bot": self.check_telegram_bot(),
            "network": self.check_network_connectivity()
        }
        
        # Determine overall system health
        statuses = [check["status"] for check in checks.values()]
        
        if "critical" in statuses:
            overall_status = "critical"
        elif "error" in statuses:
            overall_status = "error"
        elif "warning" in statuses:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        # Collect all issues
        all_issues = []
        for check_name, check_result in checks.items():
            for issue in check_result.get("issues", []):
                all_issues.append(f"{check_name}: {issue}")
        
        end_time = time.time()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "check_duration_seconds": round(end_time - start_time, 2),
            "overall_status": overall_status,
            "total_issues": len(all_issues),
            "issues": all_issues,
            "checks": checks
        }
    
    def generate_health_report(self, results: Dict) -> str:
        """Generate human-readable health report"""
        status_emoji = {
            "healthy": "✅",
            "warning": "⚠️",
            "critical": "❌",
            "error": "💥"
        }
        
        report = f"""
🏥 **ALGOSLAYER SYSTEM HEALTH REPORT**
🕐 **Time:** {results['timestamp']}
{status_emoji[results['overall_status']]} **Overall Status:** {results['overall_status'].upper()}
⏱️ **Check Duration:** {results['check_duration_seconds']}s

"""
        
        if results['total_issues'] > 0:
            report += f"🚨 **Issues Found ({results['total_issues']}):**\n"
            for issue in results['issues']:
                report += f"• {issue}\n"
            report += "\n"
        else:
            report += "✨ **No Issues Found - System Running Perfectly!**\n\n"
        
        # Summary by category
        for check_name, check_data in results['checks'].items():
            emoji = status_emoji[check_data['status']]
            report += f"{emoji} **{check_name.replace('_', ' ').title()}:** {check_data['status']}\n"
        
        # Resource details
        resources = results['checks']['system_resources']['metrics']
        report += f"""
📊 **Resource Usage:**
• CPU: {resources.get('cpu_percent', 0):.1f}%
• Memory: {resources.get('memory_percent', 0):.1f}% ({resources.get('memory_available_gb', 0):.1f}GB available)
• Disk: {resources.get('disk_percent', 0):.1f}% ({resources.get('disk_free_gb', 0):.1f}GB free)
• Load: {resources.get('load_average', [0,0,0])}

"""
        
        # Process summary
        proc_summary = results['checks']['processes']['summary']
        report += f"""
⚙️ **Process Status:**
• Trading Processes: {proc_summary.get('trading_processes', 0)}
• IB Gateway: {proc_summary.get('ib_processes', 0)}
• Total Monitored: {proc_summary.get('total_monitored', 0)}

"""
        
        # Database summary
        db_results = results['checks']['databases']['databases']
        healthy_dbs = sum(1 for db in db_results.values() if db.get('status') == 'healthy')
        total_dbs = len(db_results)
        
        report += f"""
💾 **Database Status:**
• Healthy Databases: {healthy_dbs}/{total_dbs}
• Total DB Size: {sum(db.get('size_mb', 0) for db in db_results.values()):.1f}MB

"""
        
        return report.strip()

# Create monitoring instance
health_monitor = AlgoSlayerHealthMonitor()

async def main():
    """Run comprehensive health check"""
    results = await health_monitor.run_comprehensive_check()
    
    # Generate and save report
    report = health_monitor.generate_health_report(results)
    
    print(report)
    
    # Save detailed results to file
    with open('health_check_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: health_check_results.json")
    
    # Return overall status for scripting
    return results['overall_status']

if __name__ == "__main__":
    import os
    # Add required environment for server execution
    os.environ.setdefault('PYTHONPATH', '/opt/rtx-trading')
    
    status = asyncio.run(main())
    print(f"\n🎯 System Status: {status.upper()}")
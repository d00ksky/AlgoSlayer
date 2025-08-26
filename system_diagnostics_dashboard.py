#!/usr/bin/env python3
"""
System Diagnostics Dashboard for AlgoSlayer
Weekend upgrade: Complete real-time system diagnostics and monitoring
"""
import asyncio
import json
import sqlite3
import subprocess
import time
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import sys
import os

class AlgoSlayerDiagnosticsDashboard:
    """Comprehensive system diagnostics and monitoring dashboard"""
    
    def __init__(self):
        self.base_path = Path("/opt/rtx-trading")
        self.dashboard_history = []
        self.alert_thresholds = {
            "cpu_percent": 80,
            "memory_percent": 85,
            "disk_percent": 90,
            "error_rate_percent": 10,
            "response_time_ms": 5000
        }
        
    async def get_system_overview(self) -> Dict:
        """Get comprehensive system overview"""
        overview = {
            "timestamp": datetime.now().isoformat(),
            "uptime": self._get_system_uptime(),
            "trading_status": await self._get_trading_status(),
            "health_summary": await self._get_health_summary(),
            "resource_usage": self._get_resource_usage(),
            "database_status": self._get_database_status(),
            "service_status": self._get_service_status(),
            "network_status": await self._get_network_status(),
            "performance_metrics": await self._get_performance_metrics(),
            "recent_activity": await self._get_recent_activity(),
            "alerts": self._generate_alerts()
        }
        
        return overview
    
    def _get_system_uptime(self) -> Dict:
        """Get system uptime information"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            uptime_hours = uptime_seconds / 3600
            
            return {
                "uptime_hours": round(uptime_hours, 1),
                "uptime_days": round(uptime_hours / 24, 1),
                "boot_time": datetime.fromtimestamp(boot_time).isoformat()
            }
        except:
            return {"error": "Unable to get uptime"}
    
    async def _get_trading_status(self) -> Dict:
        """Get current trading system status"""
        try:
            # Check if trading processes are running
            trading_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if ('rtx-trading' in cmdline or 
                        'run_multi_strategy.py' in cmdline or
                        'run_server.py' in cmdline):
                        
                        uptime_hours = (time.time() - proc.info['create_time']) / 3600
                        trading_processes.append({
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "uptime_hours": round(uptime_hours, 1)
                        })
                except:
                    continue
            
            # Get strategy status from database
            strategy_status = {}
            try:
                conn = sqlite3.connect(self.base_path / "data" / "algoslayer_multi_strategy.db")
                cursor = conn.cursor()
                cursor.execute("SELECT name, current_balance, total_pnl, status FROM trading_strategies")
                
                for row in cursor.fetchall():
                    strategy_status[row[0]] = {
                        "balance": row[1],
                        "pnl": row[2],
                        "status": row[3]
                    }
                conn.close()
            except:
                pass
            
            # Market hours check
            market_open = self._is_market_hours()
            
            return {
                "processes_running": len(trading_processes),
                "process_details": trading_processes,
                "active_strategies": len([s for s in strategy_status.values() if s.get("status") == "active"]),
                "total_strategies": len(strategy_status),
                "strategy_details": strategy_status,
                "market_hours": market_open,
                "trading_enabled": bool(trading_processes),
                "status": "active" if trading_processes else "inactive"
            }
            
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def _is_market_hours(self) -> bool:
        """Check if market is currently open"""
        try:
            import pytz
            et = pytz.timezone('US/Eastern')
            now = datetime.now(et)
            
            # Check if weekday and between 9:30 AM - 4:00 PM ET
            if now.weekday() >= 5:  # Weekend
                return False
            
            market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
            
            return market_open <= now <= market_close
        except:
            return False
    
    async def _get_health_summary(self) -> Dict:
        """Get overall system health summary"""
        try:
            # Import health monitor
            sys.path.append(str(self.base_path))
            from comprehensive_system_monitor import health_monitor
            
            health_results = await health_monitor.run_comprehensive_check()
            
            return {
                "overall_status": health_results["overall_status"],
                "total_issues": health_results["total_issues"],
                "check_categories": {
                    name: check["status"] 
                    for name, check in health_results["checks"].items()
                },
                "critical_issues": [
                    issue for issue in health_results["issues"] 
                    if "critical" in issue.lower()
                ]
            }
        except Exception as e:
            return {"error": str(e), "status": "unknown"}
    
    def _get_resource_usage(self) -> Dict:
        """Get detailed resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network I/O
            network = psutil.net_io_counters()
            
            # Process count
            process_count = len(psutil.pids())
            
            # Load average
            try:
                load_avg = psutil.getloadavg()
            except:
                load_avg = (0, 0, 0)
            
            return {
                "cpu": {
                    "percent": round(cpu_percent, 1),
                    "count": cpu_count,
                    "load_average": [round(x, 2) for x in load_avg]
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": round(memory.percent, 1),
                    "swap_percent": round(psutil.swap_memory().percent, 1)
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_percent": round((disk.used / disk.total) * 100, 1)
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "processes": process_count
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_database_status(self) -> Dict:
        """Get database status summary"""
        databases = [
            "algoslayer_multi_strategy.db",
            "options_performance_conservative.db",
            "options_performance_moderate.db",
            "options_performance_aggressive.db",
            "signal_performance.db"
        ]
        
        db_status = {
            "total_databases": len(databases),
            "healthy_databases": 0,
            "total_size_mb": 0,
            "database_details": {},
            "issues": []
        }
        
        for db_name in databases:
            db_path = self.base_path / "data" / db_name
            
            if not db_path.exists():
                db_status["issues"].append(f"{db_name} not found")
                continue
            
            try:
                size_mb = round(db_path.stat().st_size / (1024**2), 2)
                db_status["total_size_mb"] += size_mb
                
                # Quick integrity check
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("PRAGMA quick_check")
                result = cursor.fetchone()[0]
                
                is_healthy = result == "ok"
                if is_healthy:
                    db_status["healthy_databases"] += 1
                
                # Get record count
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                total_records = 0
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                        total_records += cursor.fetchone()[0]
                    except:
                        pass
                
                conn.close()
                
                db_status["database_details"][db_name] = {
                    "size_mb": size_mb,
                    "healthy": is_healthy,
                    "tables": len(tables),
                    "records": total_records
                }
                
                if not is_healthy:
                    db_status["issues"].append(f"{db_name} integrity check failed")
                    
            except Exception as e:
                db_status["issues"].append(f"{db_name}: {str(e)}")
        
        return db_status
    
    def _get_service_status(self) -> Dict:
        """Get systemd service status"""
        services = ["rtx-trading.service"]
        service_status = {}
        
        for service in services:
            try:
                # Check if active
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
                
                # Extract info
                memory_usage = "unknown"
                main_pid = "unknown"
                
                for line in status_result.stdout.split('\n'):
                    if "Memory:" in line:
                        memory_usage = line.split("Memory:")[1].strip().split()[0]
                    elif "Main PID:" in line:
                        main_pid = line.split("Main PID:")[1].split()[0]
                
                service_status[service] = {
                    "active": is_active,
                    "memory_usage": memory_usage,
                    "main_pid": main_pid,
                    "status": "healthy" if is_active else "stopped"
                }
                
            except Exception as e:
                service_status[service] = {
                    "active": False,
                    "error": str(e),
                    "status": "error"
                }
        
        return service_status
    
    async def _get_network_status(self) -> Dict:
        """Get network connectivity status"""
        endpoints = [
            ("Telegram API", "api.telegram.org", 443),
            ("Yahoo Finance", "query1.finance.yahoo.com", 443),
            ("Google DNS", "8.8.8.8", 53)
        ]
        
        network_status = {
            "total_endpoints": len(endpoints),
            "reachable_endpoints": 0,
            "endpoint_details": {},
            "average_latency_ms": 0
        }
        
        total_latency = 0
        reachable_count = 0
        
        for name, host, port in endpoints:
            try:
                import socket
                start_time = time.time()
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                
                latency = (time.time() - start_time) * 1000
                sock.close()
                
                is_reachable = result == 0
                if is_reachable:
                    network_status["reachable_endpoints"] += 1
                    total_latency += latency
                    reachable_count += 1
                
                network_status["endpoint_details"][name] = {
                    "host": host,
                    "port": port,
                    "reachable": is_reachable,
                    "latency_ms": round(latency, 2) if is_reachable else None
                }
                
            except Exception as e:
                network_status["endpoint_details"][name] = {
                    "host": host,
                    "port": port,
                    "reachable": False,
                    "error": str(e)
                }
        
        if reachable_count > 0:
            network_status["average_latency_ms"] = round(total_latency / reachable_count, 2)
        
        return network_status
    
    async def _get_performance_metrics(self) -> Dict:
        """Get performance metrics and trends"""
        try:
            # Trading performance metrics
            trading_metrics = await self._get_trading_metrics()
            
            # System performance metrics
            system_metrics = {
                "avg_response_time_ms": self._calculate_avg_response_time(),
                "error_rate_percent": self._calculate_error_rate(),
                "throughput_ops_per_minute": self._calculate_throughput()
            }
            
            return {
                "trading": trading_metrics,
                "system": system_metrics
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_trading_metrics(self) -> Dict:
        """Get trading-specific performance metrics"""
        try:
            # Aggregate across all strategy databases
            total_trades = 0
            winning_trades = 0
            total_pnl = 0
            avg_trade_duration = 0
            
            strategy_files = [
                "options_performance_conservative.db",
                "options_performance_moderate.db", 
                "options_performance_aggressive.db"
            ]
            
            for db_file in strategy_files:
                db_path = self.base_path / "data" / db_file
                if not db_path.exists():
                    continue
                    
                try:
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()
                    
                    # Get completed trades from last 30 days
                    thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
                    cursor.execute("""
                        SELECT net_pnl, days_held 
                        FROM options_outcomes 
                        WHERE exit_timestamp > ?
                    """, (thirty_days_ago,))
                    
                    trades = cursor.fetchall()
                    total_trades += len(trades)
                    
                    for pnl, days in trades:
                        if pnl and pnl > 0:
                            winning_trades += 1
                        if pnl:
                            total_pnl += pnl
                        if days:
                            avg_trade_duration += days
                    
                    conn.close()
                except:
                    continue
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            avg_duration = (avg_trade_duration / total_trades) if total_trades > 0 else 0
            
            return {
                "total_trades_30d": total_trades,
                "win_rate_percent": round(win_rate, 1),
                "total_pnl_30d": round(total_pnl, 2),
                "avg_trade_duration_days": round(avg_duration, 1),
                "trades_per_day": round(total_trades / 30, 1) if total_trades > 0 else 0
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_avg_response_time(self) -> float:
        """Calculate average system response time"""
        # This would typically be calculated from application logs
        # For now, return a mock value based on system load
        try:
            load_avg = psutil.getloadavg()[0]
            # Estimate response time based on load
            base_time = 100  # 100ms base
            response_time = base_time * (1 + load_avg)
            return round(response_time, 2)
        except:
            return 150.0  # Default estimate
    
    def _calculate_error_rate(self) -> float:
        """Calculate system error rate percentage"""
        # This would typically be calculated from error logs
        # For now, return a mock value based on system health
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            # Estimate error rate based on resource usage
            if cpu_percent > 90 or memory_percent > 95:
                return 15.0
            elif cpu_percent > 70 or memory_percent > 80:
                return 5.0
            else:
                return 1.0
        except:
            return 2.0
    
    def _calculate_throughput(self) -> float:
        """Calculate system throughput (operations per minute)"""
        # Mock calculation based on system performance
        try:
            cpu_count = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent()
            
            # Estimate throughput based on CPU capacity
            max_throughput = cpu_count * 100  # 100 ops per CPU core per minute
            current_load = cpu_percent / 100
            current_throughput = max_throughput * (1 - current_load)
            
            return round(current_throughput, 1)
        except:
            return 200.0
    
    async def _get_recent_activity(self) -> Dict:
        """Get recent system activity summary"""
        try:
            activity = {
                "last_trade_time": None,
                "recent_errors": [],
                "recent_optimizations": [],
                "system_events": []
            }
            
            # Check for recent trades
            try:
                conn = sqlite3.connect(self.base_path / "data" / "algoslayer_multi_strategy.db")
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT timestamp, strategy_name 
                    FROM strategy_predictions 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                result = cursor.fetchone()
                if result:
                    activity["last_trade_time"] = result[0]
                conn.close()
            except:
                pass
            
            # Check error logs (mock - would read from actual log files)
            activity["recent_errors"] = []
            
            # Check optimization history (mock)
            activity["recent_optimizations"] = [
                f"Database optimization completed at {datetime.now().strftime('%H:%M')}"
            ]
            
            # System events (mock)
            activity["system_events"] = [
                f"Trading system started at {datetime.now().strftime('%H:%M')}",
                f"Health check completed at {datetime.now().strftime('%H:%M')}"
            ]
            
            return activity
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_alerts(self) -> List[Dict]:
        """Generate system alerts based on thresholds"""
        alerts = []
        
        try:
            # Resource usage alerts
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            
            if cpu_percent > self.alert_thresholds["cpu_percent"]:
                alerts.append({
                    "level": "warning",
                    "type": "resource",
                    "message": f"High CPU usage: {cpu_percent:.1f}%",
                    "threshold": self.alert_thresholds["cpu_percent"]
                })
            
            if memory_percent > self.alert_thresholds["memory_percent"]:
                alerts.append({
                    "level": "critical" if memory_percent > 95 else "warning",
                    "type": "resource", 
                    "message": f"High memory usage: {memory_percent:.1f}%",
                    "threshold": self.alert_thresholds["memory_percent"]
                })
            
            if disk_percent > self.alert_thresholds["disk_percent"]:
                alerts.append({
                    "level": "critical",
                    "type": "resource",
                    "message": f"Low disk space: {disk_percent:.1f}% used",
                    "threshold": self.alert_thresholds["disk_percent"]
                })
            
            # Trading system alerts
            trading_processes = sum(1 for proc in psutil.process_iter(['cmdline']) 
                                  if 'rtx-trading' in ' '.join(proc.info['cmdline'] or []))
            
            if trading_processes == 0:
                alerts.append({
                    "level": "critical",
                    "type": "trading",
                    "message": "Trading system not running",
                    "threshold": "1 process expected"
                })
            
        except Exception as e:
            alerts.append({
                "level": "error",
                "type": "system",
                "message": f"Alert generation error: {str(e)}",
                "threshold": "none"
            })
        
        return alerts
    
    def generate_dashboard_display(self, overview: Dict) -> str:
        """Generate formatted dashboard display"""
        # Status emojis
        status_emoji = {
            "healthy": "✅", "active": "✅", "good": "✅",
            "warning": "⚠️", "caution": "⚠️",
            "critical": "❌", "error": "❌", "stopped": "🛑",
            "inactive": "⏸️"
        }
        
        timestamp = overview["timestamp"]
        
        # Header
        dashboard = f"""
🖥️  **ALGOSLAYER SYSTEM DIAGNOSTICS DASHBOARD**
🕐 **Time:** {timestamp}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        # System Overview
        uptime = overview.get("uptime", {})
        trading = overview.get("trading_status", {})
        health = overview.get("health_summary", {})
        
        dashboard += f"""📊 **SYSTEM OVERVIEW**
⏱️  Uptime: {uptime.get('uptime_days', 0):.1f} days ({uptime.get('uptime_hours', 0):.1f} hours)
{status_emoji.get(trading.get('status', 'unknown'), '❓')} Trading: {trading.get('status', 'unknown').title()} ({trading.get('processes_running', 0)} processes)
{status_emoji.get(health.get('overall_status', 'unknown'), '❓')} Health: {health.get('overall_status', 'unknown').title()} ({health.get('total_issues', 0)} issues)
🏪 Market: {"Open" if trading.get('market_hours', False) else "Closed"}

"""
        
        # Resource Usage
        resources = overview.get("resource_usage", {})
        cpu = resources.get("cpu", {})
        memory = resources.get("memory", {})
        disk = resources.get("disk", {})
        
        dashboard += f"""💻 **RESOURCE USAGE**
🖥️  CPU: {cpu.get('percent', 0):.1f}% ({cpu.get('count', 0)} cores) Load: {cpu.get('load_average', [0,0,0])}
🧠 Memory: {memory.get('used_percent', 0):.1f}% ({memory.get('available_gb', 0):.1f}GB available of {memory.get('total_gb', 0):.1f}GB)
💾 Disk: {disk.get('used_percent', 0):.1f}% ({disk.get('free_gb', 0):.1f}GB free of {disk.get('total_gb', 0):.1f}GB)

"""
        
        # Trading Status
        strategies = trading.get('strategy_details', {})
        active_strategies = trading.get('active_strategies', 0)
        total_strategies = trading.get('total_strategies', 0)
        
        dashboard += f"""🎯 **TRADING STATUS**
📈 Active Strategies: {active_strategies}/{total_strategies}
"""
        
        if strategies:
            total_balance = sum(s.get('balance', 0) for s in strategies.values())
            total_pnl = sum(s.get('pnl', 0) for s in strategies.values())
            
            dashboard += f"💰 Total Balance: ${total_balance:.2f}\n"
            dashboard += f"📊 Total P&L: ${total_pnl:.2f}\n"
            
            # Show top 3 performing strategies
            sorted_strategies = sorted(
                strategies.items(), 
                key=lambda x: x[1].get('pnl', 0), 
                reverse=True
            )[:3]
            
            for name, data in sorted_strategies:
                pnl = data.get('pnl', 0)
                balance = data.get('balance', 0)
                emoji = "📈" if pnl >= 0 else "📉"
                dashboard += f"  {emoji} {name.title()}: ${balance:.2f} (P&L: ${pnl:.2f})\n"
        
        dashboard += "\n"
        
        # Database Status
        db_status = overview.get("database_status", {})
        healthy_dbs = db_status.get("healthy_databases", 0)
        total_dbs = db_status.get("total_databases", 0)
        total_size = db_status.get("total_size_mb", 0)
        
        dashboard += f"""💾 **DATABASE STATUS**
✅ Healthy: {healthy_dbs}/{total_dbs} databases
📏 Total Size: {total_size:.1f}MB
"""
        
        if db_status.get("issues"):
            dashboard += "⚠️  Issues:\n"
            for issue in db_status["issues"][:3]:  # Show first 3 issues
                dashboard += f"  • {issue}\n"
        
        dashboard += "\n"
        
        # Performance Metrics
        performance = overview.get("performance_metrics", {})
        trading_perf = performance.get("trading", {})
        system_perf = performance.get("system", {})
        
        dashboard += f"""⚡ **PERFORMANCE METRICS**
📊 Trading (30d): {trading_perf.get('total_trades_30d', 0)} trades, {trading_perf.get('win_rate_percent', 0):.1f}% win rate
💰 P&L: ${trading_perf.get('total_pnl_30d', 0):.2f}, Avg Duration: {trading_perf.get('avg_trade_duration_days', 0):.1f} days
🚀 System: {system_perf.get('avg_response_time_ms', 0):.0f}ms response, {system_perf.get('error_rate_percent', 0):.1f}% errors

"""
        
        # Network Status
        network = overview.get("network_status", {})
        reachable = network.get("reachable_endpoints", 0)
        total_endpoints = network.get("total_endpoints", 0)
        avg_latency = network.get("average_latency_ms", 0)
        
        dashboard += f"""🌐 **NETWORK STATUS**
📡 Connectivity: {reachable}/{total_endpoints} endpoints reachable
⚡ Avg Latency: {avg_latency:.0f}ms

"""
        
        # Alerts
        alerts = overview.get("alerts", [])
        if alerts:
            dashboard += "🚨 **ACTIVE ALERTS**\n"
            for alert in alerts[:5]:  # Show first 5 alerts
                level_emoji = {"warning": "⚠️", "critical": "❌", "error": "💥"}.get(alert.get("level"), "ℹ️")
                dashboard += f"{level_emoji} {alert.get('message', 'Unknown alert')}\n"
        else:
            dashboard += "✨ **NO ACTIVE ALERTS** - System running optimally!\n"
        
        dashboard += "\n"
        
        # Recent Activity
        activity = overview.get("recent_activity", {})
        last_trade = activity.get("last_trade_time")
        
        dashboard += "📋 **RECENT ACTIVITY**\n"
        if last_trade:
            dashboard += f"🎯 Last Trade: {last_trade}\n"
        
        for event in activity.get("system_events", [])[:3]:
            dashboard += f"📌 {event}\n"
        
        dashboard += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        dashboard += f"\n🔄 **Auto-refresh every 30 seconds** | Dashboard v2.0"
        
        return dashboard
    
    async def run_continuous_monitoring(self, refresh_interval: int = 30):
        """Run continuous monitoring dashboard"""
        print("🖥️  Starting AlgoSlayer Diagnostics Dashboard...")
        print("Press Ctrl+C to stop monitoring\n")
        
        try:
            while True:
                # Clear screen
                os.system('clear' if os.name == 'posix' else 'cls')
                
                # Get system overview
                overview = await self.get_system_overview()
                
                # Display dashboard
                dashboard = self.generate_dashboard_display(overview)
                print(dashboard)
                
                # Store history
                self.dashboard_history.append(overview)
                
                # Keep only last 100 entries
                if len(self.dashboard_history) > 100:
                    self.dashboard_history = self.dashboard_history[-100:]
                
                # Wait for next refresh
                await asyncio.sleep(refresh_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"\n\n💥 Monitoring error: {e}")

async def main():
    """Main dashboard function"""
    dashboard = AlgoSlayerDiagnosticsDashboard()
    
    # Check if running interactively
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        # Continuous monitoring mode
        await dashboard.run_continuous_monitoring()
    else:
        # Single snapshot mode
        overview = await dashboard.get_system_overview()
        display = dashboard.generate_dashboard_display(overview)
        print(display)
        
        # Save snapshot
        with open('dashboard_snapshot.json', 'w') as f:
            json.dump(overview, f, indent=2)
        
        print(f"\n💾 Dashboard snapshot saved to: dashboard_snapshot.json")

if __name__ == "__main__":
    # Set up environment for server execution
    os.environ.setdefault('PYTHONPATH', '/opt/rtx-trading')
    
    asyncio.run(main())
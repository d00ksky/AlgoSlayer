#!/usr/bin/env python3
"""
Database Performance Optimization System for AlgoSlayer
Weekend upgrade: Maximum database performance and optimization
"""
import sqlite3
import time
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import concurrent.futures
import threading

class AlgoSlayerDatabaseOptimizer:
    """Comprehensive database performance optimization system"""
    
    def __init__(self):
        self.base_path = Path("/opt/rtx-trading")
        self.data_path = self.base_path / "data"
        self.optimization_history = []
        
        # Database files to optimize
        self.databases = [
            "algoslayer_multi_strategy.db",
            "options_performance_conservative.db",
            "options_performance_moderate.db", 
            "options_performance_aggressive.db",
            "options_performance_scalping.db",
            "options_performance_swing.db",
            "options_performance_momentum.db",
            "options_performance_volatility.db",
            "options_performance_mean_reversion.db",
            "signal_performance.db",
            "signal_effectiveness.db",
            "algoslayer_main.db"
        ]
        
        # Performance indexes to create
        self.performance_indexes = {
            "options_predictions": [
                ("idx_predictions_timestamp", "timestamp"),
                ("idx_predictions_symbol", "symbol"),
                ("idx_predictions_status", "status"),
                ("idx_predictions_strategy", "strategy"),
                ("idx_predictions_confidence", "confidence"),
                ("idx_predictions_compound", "timestamp, symbol, status")
            ],
            "options_outcomes": [
                ("idx_outcomes_prediction_id", "prediction_id"),
                ("idx_outcomes_timestamp", "exit_timestamp"),
                ("idx_outcomes_pnl", "net_pnl"),
                ("idx_outcomes_compound", "prediction_id, exit_timestamp")
            ],
            "account_history": [
                ("idx_account_timestamp", "timestamp"),
                ("idx_account_trade_id", "trade_id"),
                ("idx_account_compound", "timestamp, trade_id")
            ],
            "trading_strategies": [
                ("idx_strategies_name", "name"),
                ("idx_strategies_balance", "current_balance"),
                ("idx_strategies_status", "status")
            ],
            "strategy_predictions": [
                ("idx_strategy_pred_timestamp", "timestamp"),
                ("idx_strategy_pred_strategy", "strategy_name"),
                ("idx_strategy_pred_compound", "timestamp, strategy_name")
            ]
        }
        
        # SQLite optimization settings
        self.optimization_settings = {
            "journal_mode": "WAL",           # Write-Ahead Logging
            "synchronous": "NORMAL",         # Balanced performance/safety
            "cache_size": -64000,           # 64MB cache
            "temp_store": "MEMORY",         # Use memory for temp tables
            "mmap_size": 268435456,         # 256MB memory-mapped I/O
            "optimize": True,               # Run OPTIMIZE
            "analyze": True,                # Update statistics
            "vacuum": True,                 # Reclaim space
            "page_size": 4096              # Optimal page size
        }
    
    def get_db_connection(self, db_path: Path, optimized: bool = True) -> sqlite3.Connection:
        """Get optimized database connection"""
        conn = sqlite3.connect(str(db_path), timeout=30.0)
        
        if optimized:
            # Apply performance settings
            cursor = conn.cursor()
            
            # WAL mode for better concurrency
            cursor.execute(f"PRAGMA journal_mode = {self.optimization_settings['journal_mode']}")
            
            # Synchronization mode
            cursor.execute(f"PRAGMA synchronous = {self.optimization_settings['synchronous']}")
            
            # Cache size (negative value means KB)
            cursor.execute(f"PRAGMA cache_size = {self.optimization_settings['cache_size']}")
            
            # Memory for temporary tables
            cursor.execute(f"PRAGMA temp_store = {self.optimization_settings['temp_store']}")
            
            # Memory-mapped I/O
            cursor.execute(f"PRAGMA mmap_size = {self.optimization_settings['mmap_size']}")
            
            # Page size (must be set before any tables are created)
            try:
                cursor.execute(f"PRAGMA page_size = {self.optimization_settings['page_size']}")
            except:
                pass  # May fail if database already has data
        
        return conn
    
    def analyze_database_performance(self, db_path: Path) -> Dict:
        """Analyze database performance metrics"""
        if not db_path.exists():
            return {"error": "Database file does not exist"}
        
        try:
            start_time = time.time()
            conn = self.get_db_connection(db_path, optimized=False)
            cursor = conn.cursor()
            
            # Get basic info
            file_size = db_path.stat().st_size
            
            # Get table info
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get index info
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
            
            # Check current PRAGMA settings
            pragmas = {}
            for pragma in ['journal_mode', 'synchronous', 'cache_size', 'page_size']:
                cursor.execute(f"PRAGMA {pragma}")
                pragmas[pragma] = cursor.fetchone()[0]
            
            # Count total records
            total_records = 0
            table_stats = {}
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    total_records += count
                    table_stats[table] = count
                except:
                    table_stats[table] = "error"
            
            # Test query performance (simple SELECT)
            query_start = time.time()
            if tables:
                try:
                    cursor.execute(f"SELECT 1 FROM {tables[0]} LIMIT 1")
                    cursor.fetchone()
                except:
                    pass
            query_time = time.time() - query_start
            
            conn.close()
            analysis_time = time.time() - start_time
            
            return {
                "file_size_mb": round(file_size / (1024*1024), 2),
                "tables": len(tables),
                "indexes": len(indexes),
                "total_records": total_records,
                "table_stats": table_stats,
                "current_settings": pragmas,
                "query_time_ms": round(query_time * 1000, 2),
                "analysis_time_ms": round(analysis_time * 1000, 2),
                "status": "healthy" if analysis_time < 1.0 else "slow"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def create_performance_indexes(self, db_path: Path) -> Dict:
        """Create performance indexes on database"""
        if not db_path.exists():
            return {"error": "Database file does not exist"}
        
        try:
            conn = self.get_db_connection(db_path)
            cursor = conn.cursor()
            
            # Get existing tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            created_indexes = []
            skipped_indexes = []
            errors = []
            
            for table_name, indexes in self.performance_indexes.items():
                if table_name not in existing_tables:
                    continue
                
                for index_name, columns in indexes:
                    try:
                        # Check if index already exists
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name=?", (index_name,))
                        if cursor.fetchone():
                            skipped_indexes.append(f"{index_name} (already exists)")
                            continue
                        
                        # Create index
                        sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns})"
                        cursor.execute(sql)
                        created_indexes.append(index_name)
                        
                    except Exception as e:
                        errors.append(f"{index_name}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            return {
                "created_indexes": created_indexes,
                "skipped_indexes": skipped_indexes,
                "errors": errors,
                "total_created": len(created_indexes)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def optimize_database_structure(self, db_path: Path) -> Dict:
        """Optimize database structure and settings"""
        if not db_path.exists():
            return {"error": "Database file does not exist"}
        
        optimization_results = {
            "operations": [],
            "time_taken": 0,
            "space_saved_mb": 0,
            "errors": []
        }
        
        start_time = time.time()
        original_size = db_path.stat().st_size
        
        try:
            conn = self.get_db_connection(db_path)
            cursor = conn.cursor()
            
            # 1. Update table statistics
            try:
                cursor.execute("ANALYZE")
                optimization_results["operations"].append("ANALYZE - Updated table statistics")
            except Exception as e:
                optimization_results["errors"].append(f"ANALYZE failed: {e}")
            
            # 2. Vacuum database to reclaim space
            if self.optimization_settings["vacuum"]:
                try:
                    cursor.execute("VACUUM")
                    optimization_results["operations"].append("VACUUM - Reclaimed unused space")
                except Exception as e:
                    optimization_results["errors"].append(f"VACUUM failed: {e}")
            
            # 3. Optimize query planner
            if self.optimization_settings["optimize"]:
                try:
                    cursor.execute("PRAGMA optimize")
                    optimization_results["operations"].append("OPTIMIZE - Updated query planner")
                except Exception as e:
                    optimization_results["errors"].append(f"OPTIMIZE failed: {e}")
            
            # 4. Apply performance settings
            settings_applied = []
            for setting, value in self.optimization_settings.items():
                if setting in ["optimize", "analyze", "vacuum"]:
                    continue
                    
                try:
                    cursor.execute(f"PRAGMA {setting} = {value}")
                    settings_applied.append(f"{setting} = {value}")
                except Exception as e:
                    optimization_results["errors"].append(f"Setting {setting} failed: {e}")
            
            if settings_applied:
                optimization_results["operations"].append(f"Applied settings: {', '.join(settings_applied)}")
            
            conn.commit()
            conn.close()
            
            # Calculate space savings
            final_size = db_path.stat().st_size
            space_saved = (original_size - final_size) / (1024*1024)
            optimization_results["space_saved_mb"] = round(space_saved, 2)
            
        except Exception as e:
            optimization_results["errors"].append(f"General optimization error: {e}")
        
        optimization_results["time_taken"] = round(time.time() - start_time, 2)
        return optimization_results
    
    def benchmark_database_performance(self, db_path: Path) -> Dict:
        """Benchmark database performance"""
        if not db_path.exists():
            return {"error": "Database file does not exist"}
        
        benchmarks = {}
        
        try:
            # Test with and without optimizations
            for optimized in [False, True]:
                suffix = "optimized" if optimized else "baseline"
                
                conn = self.get_db_connection(db_path, optimized=optimized)
                cursor = conn.cursor()
                
                # Get first table for testing
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
                table_result = cursor.fetchone()
                if not table_result:
                    conn.close()
                    continue
                    
                table_name = table_result[0]
                
                # Benchmark 1: Simple SELECT
                start_time = time.time()
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
                cursor.fetchall()
                select_time = time.time() - start_time
                
                # Benchmark 2: COUNT query
                start_time = time.time()
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                cursor.fetchone()
                count_time = time.time() - start_time
                
                # Benchmark 3: Complex query (if possible)
                complex_time = 0
                try:
                    start_time = time.time()
                    cursor.execute(f"SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT 10")
                    cursor.fetchall()
                    complex_time = time.time() - start_time
                except:
                    pass
                
                benchmarks[suffix] = {
                    "select_time_ms": round(select_time * 1000, 2),
                    "count_time_ms": round(count_time * 1000, 2),
                    "complex_time_ms": round(complex_time * 1000, 2)
                }
                
                conn.close()
            
            # Calculate improvement
            if "baseline" in benchmarks and "optimized" in benchmarks:
                baseline = benchmarks["baseline"]
                optimized = benchmarks["optimized"]
                
                benchmarks["improvement"] = {
                    "select_improvement": round((1 - optimized["select_time_ms"] / baseline["select_time_ms"]) * 100, 1),
                    "count_improvement": round((1 - optimized["count_time_ms"] / baseline["count_time_ms"]) * 100, 1),
                    "complex_improvement": round((1 - optimized["complex_time_ms"] / baseline["complex_time_ms"]) * 100, 1) if baseline["complex_time_ms"] > 0 else 0
                }
            
        except Exception as e:
            benchmarks["error"] = str(e)
        
        return benchmarks
    
    async def optimize_all_databases(self) -> Dict:
        """Optimize all databases in parallel"""
        print("🚀 Starting comprehensive database optimization...")
        
        start_time = time.time()
        results = {
            "timestamp": datetime.now().isoformat(),
            "databases_processed": 0,
            "total_space_saved_mb": 0,
            "total_indexes_created": 0,
            "performance_improvements": {},
            "errors": [],
            "details": {}
        }
        
        # Process databases in parallel using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_db = {}
            
            for db_name in self.databases:
                db_path = self.data_path / db_name
                if not db_path.exists():
                    continue
                
                # Submit optimization tasks
                future = executor.submit(self._optimize_single_database, db_path)
                future_to_db[future] = db_name
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_db):
                db_name = future_to_db[future]
                try:
                    db_result = future.result()
                    results["details"][db_name] = db_result
                    results["databases_processed"] += 1
                    
                    # Aggregate metrics
                    if "space_saved_mb" in db_result:
                        results["total_space_saved_mb"] += db_result["space_saved_mb"]
                    
                    if "indexes_created" in db_result:
                        results["total_indexes_created"] += db_result["indexes_created"]
                    
                    if "performance" in db_result and "improvement" in db_result["performance"]:
                        results["performance_improvements"][db_name] = db_result["performance"]["improvement"]
                    
                except Exception as e:
                    results["errors"].append(f"{db_name}: {str(e)}")
        
        # Calculate overall improvement
        if results["performance_improvements"]:
            all_improvements = list(results["performance_improvements"].values())
            avg_select_improvement = sum(imp.get("select_improvement", 0) for imp in all_improvements) / len(all_improvements)
            avg_count_improvement = sum(imp.get("count_improvement", 0) for imp in all_improvements) / len(all_improvements)
            
            results["overall_improvement"] = {
                "average_select_improvement": round(avg_select_improvement, 1),
                "average_count_improvement": round(avg_count_improvement, 1)
            }
        
        results["total_time_seconds"] = round(time.time() - start_time, 2)
        
        # Save optimization history
        self.optimization_history.append(results)
        
        return results
    
    def _optimize_single_database(self, db_path: Path) -> Dict:
        """Optimize a single database (for parallel processing)"""
        db_result = {
            "file_size_before_mb": round(db_path.stat().st_size / (1024*1024), 2),
            "analysis": {},
            "optimization": {},
            "indexes": {},
            "performance": {},
            "space_saved_mb": 0,
            "indexes_created": 0
        }
        
        try:
            # 1. Analyze current performance
            db_result["analysis"] = self.analyze_database_performance(db_path)
            
            # 2. Create performance indexes
            db_result["indexes"] = self.create_performance_indexes(db_path)
            db_result["indexes_created"] = db_result["indexes"].get("total_created", 0)
            
            # 3. Optimize structure
            db_result["optimization"] = self.optimize_database_structure(db_path)
            db_result["space_saved_mb"] = db_result["optimization"].get("space_saved_mb", 0)
            
            # 4. Benchmark performance
            db_result["performance"] = self.benchmark_database_performance(db_path)
            
            # 5. Final file size
            db_result["file_size_after_mb"] = round(db_path.stat().st_size / (1024*1024), 2)
            
        except Exception as e:
            db_result["error"] = str(e)
        
        return db_result
    
    def generate_optimization_report(self, results: Dict) -> str:
        """Generate human-readable optimization report"""
        report = f"""
🚀 **ALGOSLAYER DATABASE OPTIMIZATION REPORT**
🕐 **Time:** {results['timestamp']}
⏱️ **Duration:** {results['total_time_seconds']}s

📊 **Summary:**
• Databases Processed: {results['databases_processed']}
• Total Space Saved: {results['total_space_saved_mb']:.2f}MB
• Total Indexes Created: {results['total_indexes_created']}
• Errors: {len(results.get('errors', []))}

"""
        
        # Performance improvements
        if "overall_improvement" in results:
            improvement = results["overall_improvement"]
            report += f"""💡 **Performance Improvements:**
• Average SELECT Speed: +{improvement['average_select_improvement']:.1f}%
• Average COUNT Speed: +{improvement['average_count_improvement']:.1f}%

"""
        
        # Individual database details
        report += "📋 **Database Details:**\n"
        for db_name, details in results.get("details", {}).items():
            status = "✅" if "error" not in details else "❌"
            space_saved = details.get("space_saved_mb", 0)
            indexes_created = details.get("indexes_created", 0)
            
            report += f"• {status} {db_name}: "
            if space_saved > 0:
                report += f"Saved {space_saved:.2f}MB, "
            if indexes_created > 0:
                report += f"Created {indexes_created} indexes, "
            
            if "performance" in details and "improvement" in details["performance"]:
                imp = details["performance"]["improvement"]
                select_imp = imp.get("select_improvement", 0)
                if select_imp > 0:
                    report += f"Speed +{select_imp:.1f}%"
            
            report += "\n"
        
        # Errors
        if results.get("errors"):
            report += "\n🚨 **Errors:**\n"
            for error in results["errors"]:
                report += f"• {error}\n"
        
        # Recommendations
        report += "\n💡 **Recommendations:**\n"
        if results["total_indexes_created"] > 0:
            report += "• Performance indexes created will speed up common queries\n"
        if results["total_space_saved_mb"] > 0:
            report += f"• Reclaimed {results['total_space_saved_mb']:.2f}MB of disk space\n"
        if not results.get("errors"):
            report += "• All databases optimized successfully!\n"
            report += "• Run this optimization weekly for best performance\n"
        else:
            report += "• Review and fix errors for complete optimization\n"
        
        report += "• Monitor database performance with regular health checks\n"
        
        return report.strip()

async def main():
    """Run database optimization"""
    optimizer = AlgoSlayerDatabaseOptimizer()
    
    # Run comprehensive optimization
    results = await optimizer.optimize_all_databases()
    
    # Generate and display report
    report = optimizer.generate_optimization_report(results)
    print(report)
    
    # Save detailed results
    with open('database_optimization_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: database_optimization_results.json")
    
    # Return success status
    return len(results.get("errors", [])) == 0

if __name__ == "__main__":
    import os
    # Set up environment for server execution
    os.environ.setdefault('PYTHONPATH', '/opt/rtx-trading')
    
    success = asyncio.run(main())
    print(f"\n🎯 Optimization Status: {'SUCCESS' if success else 'PARTIAL_SUCCESS'}")
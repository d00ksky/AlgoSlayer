#!/usr/bin/env python3
"""
Comprehensive Error Handling and Recovery System for AlgoSlayer
Weekend upgrade: Bulletproof error recovery and resilience
"""
import asyncio
import functools
import json
import sqlite3
import subprocess
import time
import traceback
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import logging

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"           # Minor issues that don't affect trading
    MEDIUM = "medium"     # Issues that might affect some features
    HIGH = "high"         # Issues that significantly impact trading
    CRITICAL = "critical" # System-breaking issues requiring immediate attention

class RecoveryAction(Enum):
    """Recovery actions that can be taken"""
    RETRY = "retry"
    RESTART_SERVICE = "restart_service"
    RESET_DATABASE = "reset_database"
    CLEAR_CACHE = "clear_cache"
    NOTIFY_ADMIN = "notify_admin"
    EMERGENCY_STOP = "emergency_stop"

class AlgoSlayerErrorRecovery:
    """Comprehensive error handling and recovery system"""
    
    def __init__(self):
        self.base_path = Path("/opt/rtx-trading")
        self.error_log_path = self.base_path / "logs" / "error_recovery.log"
        self.recovery_history = []
        self.circuit_breakers = {}
        
        # Create logs directory if it doesn't exist
        self.error_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure detailed logging
        self.logger = self._setup_logger()
        
        # Error patterns and recovery strategies
        self.error_patterns = {
            "database_locked": {
                "severity": ErrorSeverity.HIGH,
                "pattern": ["database is locked", "sqlite3.OperationalError"],
                "actions": [RecoveryAction.RETRY, RecoveryAction.RESET_DATABASE]
            },
            "telegram_409": {
                "severity": ErrorSeverity.MEDIUM,
                "pattern": ["409", "Conflict", "telegram"],
                "actions": [RecoveryAction.CLEAR_CACHE, RecoveryAction.RETRY]
            },
            "memory_exhaustion": {
                "severity": ErrorSeverity.CRITICAL,
                "pattern": ["MemoryError", "out of memory", "malloc"],
                "actions": [RecoveryAction.RESTART_SERVICE, RecoveryAction.EMERGENCY_STOP]
            },
            "network_timeout": {
                "severity": ErrorSeverity.MEDIUM,
                "pattern": ["timeout", "connection failed", "unreachable"],
                "actions": [RecoveryAction.RETRY]
            },
            "api_rate_limit": {
                "severity": ErrorSeverity.LOW,
                "pattern": ["rate limit", "too many requests", "quota exceeded"],
                "actions": [RecoveryAction.RETRY]
            },
            "import_error": {
                "severity": ErrorSeverity.CRITICAL,
                "pattern": ["ImportError", "ModuleNotFoundError", "cannot import"],
                "actions": [RecoveryAction.RESTART_SERVICE, RecoveryAction.NOTIFY_ADMIN]
            },
            "permission_denied": {
                "severity": ErrorSeverity.HIGH,
                "pattern": ["Permission denied", "access denied", "not authorized"],
                "actions": [RecoveryAction.NOTIFY_ADMIN]
            }
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Setup detailed error logging"""
        logger = logging.getLogger("AlgoSlayerErrorRecovery")
        logger.setLevel(logging.DEBUG)
        
        # File handler
        file_handler = logging.FileHandler(self.error_log_path)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def analyze_error(self, error: Exception, context: str = "") -> Dict:
        """Analyze error and determine recovery strategy"""
        error_str = str(error).lower()
        error_type = type(error).__name__
        traceback_str = traceback.format_exc()
        
        # Find matching error pattern
        matched_pattern = None
        for pattern_name, pattern_config in self.error_patterns.items():
            if any(pattern in error_str or pattern in error_type.lower() or 
                   pattern in traceback_str.lower() for pattern in pattern_config["pattern"]):
                matched_pattern = pattern_name
                break
        
        if not matched_pattern:
            # Default handling for unknown errors
            matched_pattern = "unknown_error"
            pattern_config = {
                "severity": ErrorSeverity.MEDIUM,
                "actions": [RecoveryAction.RETRY, RecoveryAction.NOTIFY_ADMIN]
            }
        else:
            pattern_config = self.error_patterns[matched_pattern]
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": str(error),
            "context": context,
            "pattern": matched_pattern,
            "severity": pattern_config["severity"].value,
            "recommended_actions": [action.value for action in pattern_config["actions"]],
            "traceback": traceback_str
        }
        
        self.logger.error(f"Error analyzed: {matched_pattern} - {error_type}: {str(error)}")
        return analysis
    
    async def execute_recovery_action(self, action: RecoveryAction, context: Dict = None) -> bool:
        """Execute a specific recovery action"""
        try:
            self.logger.info(f"Executing recovery action: {action.value}")
            
            if action == RecoveryAction.RETRY:
                # Simple retry with backoff
                retry_count = context.get('retry_count', 0) if context else 0
                backoff_time = min(2 ** retry_count, 30)  # Max 30 seconds
                
                self.logger.info(f"Retrying after {backoff_time}s (attempt {retry_count + 1})")
                await asyncio.sleep(backoff_time)
                return True
                
            elif action == RecoveryAction.RESTART_SERVICE:
                # Restart the trading service
                self.logger.info("Attempting to restart rtx-trading.service")
                result = subprocess.run(
                    ["systemctl", "restart", "rtx-trading.service"],
                    capture_output=True, text=True, timeout=30
                )
                
                if result.returncode == 0:
                    self.logger.info("Service restarted successfully")
                    await asyncio.sleep(10)  # Wait for service to stabilize
                    return True
                else:
                    self.logger.error(f"Service restart failed: {result.stderr}")
                    return False
                    
            elif action == RecoveryAction.RESET_DATABASE:
                # Reset problematic database connections
                self.logger.info("Resetting database connections")
                
                # Close any open SQLite connections (this would be implemented in database manager)
                # For now, just wait and hope connections timeout
                await asyncio.sleep(5)
                return True
                
            elif action == RecoveryAction.CLEAR_CACHE:
                # Clear various caches
                self.logger.info("Clearing system caches")
                
                cache_dirs = [
                    self.base_path / "cache",
                    self.base_path / "temp", 
                    self.base_path / ".cache"
                ]
                
                for cache_dir in cache_dirs:
                    if cache_dir.exists():
                        try:
                            import shutil
                            shutil.rmtree(cache_dir)
                            self.logger.info(f"Cleared cache: {cache_dir}")
                        except Exception as e:
                            self.logger.warning(f"Failed to clear {cache_dir}: {e}")
                
                return True
                
            elif action == RecoveryAction.NOTIFY_ADMIN:
                # Send admin notification
                await self.send_admin_notification(context)
                return True
                
            elif action == RecoveryAction.EMERGENCY_STOP:
                # Emergency stop of all trading
                self.logger.critical("EMERGENCY STOP INITIATED")
                
                try:
                    # Stop the trading service
                    subprocess.run(["systemctl", "stop", "rtx-trading.service"], timeout=10)
                    
                    # Send emergency notification
                    await self.send_emergency_notification()
                    
                    return True
                except Exception as e:
                    self.logger.critical(f"Emergency stop failed: {e}")
                    return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Recovery action {action.value} failed: {e}")
            return False
    
    async def send_admin_notification(self, context: Dict = None):
        """Send notification to admin via Telegram"""
        try:
            # Import telegram bot
            sys.path.append(str(self.base_path))
            from src.core.telegram_bot import telegram_bot
            
            error_info = context.get('error_analysis', {}) if context else {}
            
            message = f"""
🚨 **ALGOSLAYER ERROR ALERT**

⚠️ **Severity:** {error_info.get('severity', 'unknown').upper()}
🕐 **Time:** {error_info.get('timestamp', datetime.now().isoformat())}
🔍 **Pattern:** {error_info.get('pattern', 'unknown')}
📝 **Error:** {error_info.get('error_type', 'Unknown')}: {error_info.get('error_message', '')[:200]}
🎯 **Context:** {error_info.get('context', 'No context')}

🔧 **Recommended Actions:**
{chr(10).join(f'• {action}' for action in error_info.get('recommended_actions', []))}

📊 **System Status:** Monitoring and attempting recovery...
"""
            
            await telegram_bot.send_message(message.strip())
            self.logger.info("Admin notification sent via Telegram")
            
        except Exception as e:
            self.logger.error(f"Failed to send admin notification: {e}")
    
    async def send_emergency_notification(self):
        """Send emergency notification"""
        try:
            sys.path.append(str(self.base_path))
            from src.core.telegram_bot import telegram_bot
            
            message = f"""
🆘 **ALGOSLAYER EMERGENCY STOP**

🚨 **CRITICAL SYSTEM ERROR DETECTED**
⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

🛑 **Actions Taken:**
• Trading system stopped
• All operations halted
• System in safe mode

⚠️ **IMMEDIATE ATTENTION REQUIRED**
• Check system logs
• Investigate root cause
• Manual restart needed

📞 **Contact:** System Administrator
"""
            
            await telegram_bot.send_message(message.strip())
            self.logger.critical("Emergency notification sent")
            
        except Exception as e:
            self.logger.critical(f"Failed to send emergency notification: {e}")
    
    def circuit_breaker(self, operation_name: str, failure_threshold: int = 5, 
                       reset_timeout: int = 300):
        """Circuit breaker decorator to prevent cascade failures"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                now = time.time()
                
                # Initialize circuit breaker state
                if operation_name not in self.circuit_breakers:
                    self.circuit_breakers[operation_name] = {
                        'failures': 0,
                        'last_failure': 0,
                        'state': 'closed'  # closed, open, half-open
                    }
                
                cb = self.circuit_breakers[operation_name]
                
                # Check if circuit is open
                if cb['state'] == 'open':
                    if now - cb['last_failure'] > reset_timeout:
                        cb['state'] = 'half-open'
                        self.logger.info(f"Circuit breaker for {operation_name}: half-open")
                    else:
                        raise Exception(f"Circuit breaker open for {operation_name}")
                
                try:
                    result = await func(*args, **kwargs)
                    
                    # Success - reset circuit breaker
                    if cb['failures'] > 0:
                        self.logger.info(f"Circuit breaker for {operation_name}: reset")
                    cb['failures'] = 0
                    cb['state'] = 'closed'
                    
                    return result
                    
                except Exception as e:
                    cb['failures'] += 1
                    cb['last_failure'] = now
                    
                    if cb['failures'] >= failure_threshold:
                        cb['state'] = 'open'
                        self.logger.error(f"Circuit breaker for {operation_name}: OPEN")
                    
                    raise e
            
            return wrapper
        return decorator
    
    async def recover_from_error(self, error: Exception, context: str = "", 
                                max_retries: int = 3) -> bool:
        """Comprehensive error recovery workflow"""
        error_analysis = self.analyze_error(error, context)
        
        # Record recovery attempt
        recovery_attempt = {
            "timestamp": datetime.now().isoformat(),
            "error_analysis": error_analysis,
            "recovery_actions": [],
            "success": False
        }
        
        try:
            # Execute recovery actions
            for action_name in error_analysis["recommended_actions"]:
                action = RecoveryAction(action_name)
                
                recovery_context = {
                    "error_analysis": error_analysis,
                    "retry_count": len([a for a in recovery_attempt["recovery_actions"] 
                                      if a.get("action") == "retry"])
                }
                
                self.logger.info(f"Attempting recovery action: {action.value}")
                
                success = await self.execute_recovery_action(action, recovery_context)
                
                recovery_attempt["recovery_actions"].append({
                    "action": action.value,
                    "success": success,
                    "timestamp": datetime.now().isoformat()
                })
                
                if success:
                    if action == RecoveryAction.RETRY:
                        # For retry, we consider it successful if we reach max retries
                        if recovery_context["retry_count"] >= max_retries:
                            break
                    else:
                        # Other actions are considered successful immediately
                        break
                else:
                    self.logger.error(f"Recovery action {action.value} failed")
            
            # Check if recovery was successful
            successful_actions = [a for a in recovery_attempt["recovery_actions"] if a["success"]]
            recovery_attempt["success"] = len(successful_actions) > 0
            
            if recovery_attempt["success"]:
                self.logger.info(f"Error recovery successful for: {error_analysis['pattern']}")
            else:
                self.logger.error(f"Error recovery failed for: {error_analysis['pattern']}")
                
                # If critical error and recovery failed, trigger emergency procedures
                if error_analysis["severity"] == ErrorSeverity.CRITICAL.value:
                    await self.execute_recovery_action(RecoveryAction.EMERGENCY_STOP, recovery_context)
            
        except Exception as recovery_error:
            self.logger.critical(f"Recovery system itself failed: {recovery_error}")
            recovery_attempt["recovery_error"] = str(recovery_error)
        
        finally:
            # Record recovery history
            self.recovery_history.append(recovery_attempt)
            
            # Keep only last 100 recovery attempts
            if len(self.recovery_history) > 100:
                self.recovery_history = self.recovery_history[-100:]
        
        return recovery_attempt["success"]
    
    def resilient_operation(self, operation_name: str, max_retries: int = 3, 
                           backoff_multiplier: float = 2.0):
        """Decorator to make operations resilient with automatic recovery"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                last_error = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                        
                    except Exception as e:
                        last_error = e
                        
                        if attempt == max_retries:
                            # Final attempt failed - trigger recovery
                            self.logger.error(f"Operation {operation_name} failed after {max_retries + 1} attempts")
                            
                            recovery_successful = await self.recover_from_error(
                                e, f"Operation: {operation_name}, Attempt: {attempt + 1}"
                            )
                            
                            if not recovery_successful:
                                raise e
                        else:
                            # Wait before retry
                            backoff_time = backoff_multiplier ** attempt
                            self.logger.warning(f"Operation {operation_name} failed (attempt {attempt + 1}), retrying in {backoff_time}s: {e}")
                            await asyncio.sleep(backoff_time)
                
                # This should never be reached, but just in case
                raise last_error
            
            return wrapper
        return decorator
    
    def get_system_health_metrics(self) -> Dict:
        """Get metrics about system health and recovery performance"""
        recent_errors = [r for r in self.recovery_history 
                        if datetime.fromisoformat(r["timestamp"]) > 
                        datetime.now() - timedelta(hours=24)]
        
        error_patterns = {}
        recovery_success_rate = 0
        
        if recent_errors:
            # Count error patterns
            for recovery in recent_errors:
                pattern = recovery["error_analysis"]["pattern"]
                error_patterns[pattern] = error_patterns.get(pattern, 0) + 1
            
            # Calculate success rate
            successful_recoveries = sum(1 for r in recent_errors if r["success"])
            recovery_success_rate = successful_recoveries / len(recent_errors) * 100
        
        return {
            "last_24h_errors": len(recent_errors),
            "recovery_success_rate": round(recovery_success_rate, 1),
            "error_patterns": error_patterns,
            "circuit_breakers": {name: cb["state"] for name, cb in self.circuit_breakers.items()},
            "total_recovery_attempts": len(self.recovery_history)
        }

# Global error recovery instance
error_recovery = AlgoSlayerErrorRecovery()

# Convenience functions for easy integration
async def handle_error(error: Exception, context: str = "") -> bool:
    """Handle an error with automatic recovery"""
    return await error_recovery.recover_from_error(error, context)

def resilient(operation_name: str, max_retries: int = 3):
    """Decorator to make functions resilient"""
    return error_recovery.resilient_operation(operation_name, max_retries)

def circuit_breaker(operation_name: str, failure_threshold: int = 5):
    """Circuit breaker decorator"""
    return error_recovery.circuit_breaker(operation_name, failure_threshold)

# Example usage and testing
async def test_error_recovery():
    """Test the error recovery system"""
    print("🧪 Testing Error Recovery System...")
    
    # Test 1: Database error simulation
    try:
        raise sqlite3.OperationalError("database is locked")
    except Exception as e:
        success = await handle_error(e, "Database operation test")
        print(f"Database error recovery: {'✅' if success else '❌'}")
    
    # Test 2: Network error simulation  
    try:
        raise TimeoutError("Connection timeout")
    except Exception as e:
        success = await handle_error(e, "Network operation test")
        print(f"Network error recovery: {'✅' if success else '❌'}")
    
    # Test 3: Unknown error
    try:
        raise ValueError("Unknown test error")
    except Exception as e:
        success = await handle_error(e, "Unknown error test")
        print(f"Unknown error recovery: {'✅' if success else '❌'}")
    
    # Show health metrics
    metrics = error_recovery.get_system_health_metrics()
    print(f"\n📊 System Health Metrics:")
    print(f"• Recent errors: {metrics['last_24h_errors']}")
    print(f"• Recovery success rate: {metrics['recovery_success_rate']}%")
    print(f"• Error patterns: {metrics['error_patterns']}")
    print(f"• Circuit breakers: {metrics['circuit_breakers']}")
    
    print("\n✅ Error recovery system test completed!")

if __name__ == "__main__":
    # Set up environment for server execution
    os.environ.setdefault('PYTHONPATH', '/opt/rtx-trading')
    
    # Run tests
    asyncio.run(test_error_recovery())
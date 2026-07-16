# ──────────────────────────────────────────────────────────────────────────────
# monitoring.py - Application Health Monitoring & Diagnostics
# Provides real-time health checks, performance metrics, and system status
# ──────────────────────────────────────────────────────────────────────────────

import asyncio
import logging
import os
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class HealthCheck:
    """Application health status monitor."""
    
    def __init__(self):
        self.start_time = time.time()
        self.last_check = None
        self.status = "starting"
        self.checks = {}
    
    @property
    def uptime_seconds(self) -> float:
        """Get application uptime in seconds."""
        return time.time() - self.start_time
    
    @property
    def uptime_formatted(self) -> str:
        """Get human-readable uptime."""
        seconds = self.uptime_seconds
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {secs}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    async def check_database(self, conn_func) -> Dict:
        """Check database connectivity."""
        try:
            conn = conn_func()
            cursor = conn.execute("SELECT 1")
            conn.close()
            return {"status": "healthy", "latency_ms": 0}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_redis(self, redis_client) -> Dict:
        """Check Redis connectivity."""
        try:
            redis_client.ping()
            return {"status": "healthy"}
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def check_system(self) -> Dict:
        """Check system resources."""
        try:
            process = psutil.Process()
            cpu_percent = process.cpu_percent(interval=0.1)
            memory_info = process.memory_info()
            disk_usage = psutil.disk_usage("/")
            
            return {
                "cpu_percent": cpu_percent,
                "memory_mb": memory_info.rss / 1024 / 1024,
                "memory_percent": process.memory_percent(),
                "disk_percent": disk_usage.percent,
                "open_files": len(process.open_files()),
            }
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def full_check(self, db_func=None, redis_client=None) -> Dict:
        """Run all health checks."""
        checks = {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": self.uptime_seconds,
            "uptime": self.uptime_formatted,
            "status": "healthy",
            "system": self.check_system(),
        }
        
        if db_func:
            checks["database"] = await self.check_database(db_func)
        
        if redis_client:
            checks["redis"] = await self.check_redis(redis_client)
        
        # Overall status
        if any(
            check.get("status") == "unhealthy"
            for check in [checks.get("database"), checks.get("redis")]
            if check
        ):
            checks["status"] = "degraded"
        
        self.checks = checks
        self.last_check = datetime.utcnow()
        return checks


class PerformanceMonitor:
    """Track application performance metrics."""
    
    def __init__(self):
        self.metrics = {
            "requests": {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "avg_response_time_ms": 0,
            },
            "database": {
                "total_queries": 0,
                "slow_queries": 0,
                "avg_query_time_ms": 0,
            },
            "errors": {
                "total": 0,
                "by_type": {},
            }
        }
        self.request_times = []
        self.query_times = []
    
    def record_request(self, status_code: int, response_time_ms: float):
        """Record HTTP request metrics."""
        self.metrics["requests"]["total"] += 1
        
        if 200 <= status_code < 400:
            self.metrics["requests"]["successful"] += 1
        else:
            self.metrics["requests"]["failed"] += 1
        
        self.request_times.append(response_time_ms)
        
        # Keep only last 1000 measurements
        if len(self.request_times) > 1000:
            self.request_times = self.request_times[-1000:]
        
        if self.request_times:
            self.metrics["requests"]["avg_response_time_ms"] = sum(self.request_times) / len(self.request_times)
    
    def record_query(self, query_time_ms: float, is_slow: bool = False):
        """Record database query metrics."""
        self.metrics["database"]["total_queries"] += 1
        
        if is_slow:
            self.metrics["database"]["slow_queries"] += 1
        
        self.query_times.append(query_time_ms)
        
        # Keep only last 1000 measurements
        if len(self.query_times) > 1000:
            self.query_times = self.query_times[-1000:]
        
        if self.query_times:
            self.metrics["database"]["avg_query_time_ms"] = sum(self.query_times) / len(self.query_times)
    
    def record_error(self, error_type: str):
        """Record error metrics."""
        self.metrics["errors"]["total"] += 1
        self.metrics["errors"]["by_type"][error_type] = self.metrics["errors"]["by_type"].get(error_type, 0) + 1
    
    def get_metrics(self) -> Dict:
        """Get current performance metrics."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            **self.metrics,
        }
    
    def get_summary(self) -> str:
        """Get human-readable performance summary."""
        m = self.metrics
        return (
            f"Requests: {m['requests']['total']} total, "
            f"{m['requests']['successful']} successful, "
            f"avg {m['requests']['avg_response_time_ms']:.1f}ms | "
            f"Queries: {m['database']['total_queries']} total, "
            f"{m['database']['slow_queries']} slow, "
            f"avg {m['database']['avg_query_time_ms']:.1f}ms | "
            f"Errors: {m['errors']['total']} total"
        )


# Global instances
health_check = HealthCheck()
performance_monitor = PerformanceMonitor()


def get_diagnostic_report() -> Dict:
    """Get comprehensive diagnostic report."""
    return {
        "health": health_check.checks,
        "performance": performance_monitor.get_metrics(),
        "environment": {
            "python_version": os.sys.version,
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "debug": os.getenv("DEBUG", "false"),
        }
    }

"""
Health check endpoint for monitoring
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
import psutil
import os
from loguru import logger

app = FastAPI()

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get process info
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "process_memory_mb": round(process_memory, 2)
                },
                "service": "algoslayer"
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint"""
    try:
        # Get metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Format as Prometheus metrics
        metrics_text = f"""# HELP algoslayer_cpu_usage CPU usage percentage
# TYPE algoslayer_cpu_usage gauge
algoslayer_cpu_usage {cpu_percent}

# HELP algoslayer_memory_usage Memory usage percentage
# TYPE algoslayer_memory_usage gauge
algoslayer_memory_usage {memory.percent}

# HELP algoslayer_disk_usage Disk usage percentage
# TYPE algoslayer_disk_usage gauge
algoslayer_disk_usage {disk.percent}

# HELP algoslayer_up Service up status
# TYPE algoslayer_up gauge
algoslayer_up 1
"""
        
        return JSONResponse(
            content=metrics_text,
            media_type="text/plain"
        )
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

def start_health_server(port: int = 8000):
    """Start the health check server"""
    logger.info(f"Starting health check server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
#!/bin/bash
# -----------------------------------------------------------------------------
# 🚀 JobHunt Pro - Production Gunicorn/Uvicorn ASGI Startup Script
# -----------------------------------------------------------------------------
# This script launches FastAPI using Gunicorn as a process manager and Uvicorn
# as the asynchronous worker class. This resolves WSGI bottlenecks and allows
# for maximum concurrency.

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting JobHunt Pro via Gunicorn/Uvicorn..."

# Determine optimal number of workers (2 * CPU cores + 1)
# For constrained VPS environments, limit to 2 or 4 to prevent OOM
NUM_WORKERS=${GUNICORN_WORKERS:-4}
BIND_ADDR=${GUNICORN_BIND:-"0.0.0.0:8000"}

# Execute Gunicorn
# -k uvicorn.workers.UvicornWorker: Specifies the ASGI worker class
# --max-requests: Restarts workers automatically to prevent memory leaks
# --max-requests-jitter: Prevents the "thundering herd" by jittering restarts
exec gunicorn web.app_v2:app \
    --workers $NUM_WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind $BIND_ADDR \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --log-level info \
    --access-logfile - \
    --error-logfile -

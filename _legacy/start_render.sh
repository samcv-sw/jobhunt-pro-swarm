#!/bin/bash
# start_render.sh - Minimal web server for Render fast health check
# 1. Start uvicorn directly - no Xvfb or swarm_master
exec python -m uvicorn web.app_v2:app --host 0.0.0.0 --port 10000

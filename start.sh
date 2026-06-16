#!/bin/bash
# Start Xvfb in the background
Xvfb :99 -screen 0 1280x1024x24 &

# Wait for Xvfb to be ready
sleep 2

# Start the Swarm Master
exec python core/swarm_master.py

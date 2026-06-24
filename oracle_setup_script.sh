#!/bin/bash
# =====================================================================
# JobHunt Pro: Oracle Cloud (Always Free) Hydra Setup Script
# Run this on your 24GB RAM ARM Oracle instance to host the Worker Head
# =====================================================================

set -e

echo "[HYDRA] Updating system and installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git htop

echo "[HYDRA] Setting up application directory..."
mkdir -p /opt/jobhunt
cd /opt/jobhunt

if [ ! -d "/opt/jobhunt/.git" ]; then
    echo "[HYDRA] Warning: You need to clone your repository here."
    echo "Run: git clone <your-repo-url> ."
    exit 1
fi

echo "[HYDRA] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "[HYDRA] Installing requirements..."
pip install -r requirements.txt

# Create the systemd service for the immortal worker
echo "[HYDRA] Creating systemd service for 24/7 background worker..."

cat <<EOF | sudo tee /etc/systemd/system/jobhunt-worker.service
[Unit]
Description=JobHunt Pro Hydra Worker Swarm
After=network.target

[Service]
User=$USER
WorkingDirectory=/opt/jobhunt
Environment="PATH=/opt/jobhunt/venv/bin"
# NOTE: Replace the database URL with your Neon/Turso serverless DB URL
Environment="DATABASE_URL=postgresql://user:pass@neon.tech/db"
Environment="MAX_WORKERS=5000"
Environment="CLOUD_MODE=true"
ExecStart=/opt/jobhunt/venv/bin/python start_cloud.py --worker-only
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable jobhunt-worker.service
sudo systemctl start jobhunt-worker.service

echo "============================================================"
echo "HYDRA COMPUTE HEAD DEPLOYED SUCESSFULLY!"
echo "The worker swarm is now running continuously in the background."
echo "Check logs with: sudo journalctl -u jobhunt-worker.service -f"
echo "============================================================"

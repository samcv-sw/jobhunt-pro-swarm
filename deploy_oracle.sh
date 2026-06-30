#!/bin/bash
# Oracle Cloud Automated Deployment Script for JobHunt Pro

set -e

echo "================================================="
echo "🐉 JOBHUNT PRO - ORACLE CLOUD DEPLOYMENT SCRIPT "
echo "================================================="
echo "Initializing..."

# 1. Update and install dependencies
echo "[1/4] Installing system dependencies..."
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-venv git curl ufw docker.io docker-compose

# 2. Setup firewall rules
echo "[2/4] Configuring Firewall (UFW)..."
sudo ufw allow ssh
sudo ufw allow 8080/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# 3. Setup application directory
echo "[3/4] Preparing application environment..."
if [ ! -d "jobhunt-pro" ]; then
    mkdir -p jobhunt-pro
fi
cd jobhunt-pro

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Create Systemd Service for 24/7 Uptime
echo "[4/4] Creating immortal Systemd service..."
cat << 'EOF' | sudo tee /etc/systemd/system/jobhunt-pro.service
[Unit]
Description=JobHunt Pro - God Tier AI Swarm
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/jobhunt-pro
ExecStart=/home/ubuntu/jobhunt-pro/venv/bin/uvicorn web.app_v2:app --host 0.0.0.0 --port 8080 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable jobhunt-pro.service

echo "================================================="
echo "✅ Oracle Cloud Node configured successfully!"
echo "Next Steps:"
echo "1. Upload your code to /home/ubuntu/jobhunt-pro"
echo "2. Add your .env file"
echo "3. Run: sudo systemctl start jobhunt-pro.service"
echo "================================================="

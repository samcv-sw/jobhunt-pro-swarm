#!/bin/bash
#==============================================================#
# JobHunt Pro v16.7 - Oracle Cloud Always Free Deployment Script
#==============================================================#
# Run this script on your Oracle Cloud VM (Ubuntu 22.04/24.04)
# Usage: bash deploy_oracle.sh
#==============================================================#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  JobHunt Pro v16.7 - Oracle Cloud Setup${NC}"
echo -e "${GREEN}============================================${NC}"

# ------------------------------------------------------------
# Step 1: System update & dependencies
# ------------------------------------------------------------
echo -e "${YELLOW}[1/8] Updating system packages...${NC}"
sudo apt update -y && sudo apt upgrade -y

echo -e "${YELLOW}[2/8] Installing Python 3.10+ and tools...${NC}"
sudo apt install -y python3 python3-pip python3-venv git curl wget

# ------------------------------------------------------------
# Step 2: Clone the repository
# ------------------------------------------------------------
echo -e "${YELLOW}[3/8] Cloning repository...${NC}"
cd /home/ubuntu
if [ -d "jobhunt-pro" ]; then
    echo "  Repo exists, pulling latest..."
    cd jobhunt-pro && git pull
else
    git clone https://github.com/Rita-Cordahi/jobhunt-pro.git
    cd jobhunt-pro
fi

# ------------------------------------------------------------
# Step 3: Create .env file from user input
# ------------------------------------------------------------
echo -e "${YELLOW}[4/8] Configuring environment variables...${NC}"
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# ============================================#
# JobHunt Pro v16.7 - Environment Config
# Oracle Cloud Backup Instance
# ============================================#
CLOUD_MODE=true
DRY_RUN=true
MAX_WORKERS=50
CYCLE_INTERVAL=60

# --- AI Provider ---
GROQ_API_KEY=

# --- Email Providers ---
GMAIL_SMTP_USER_1=
GMAIL_APP_PASSWORD_1=
BREVO_API_KEY=

# --- Job Search ---
JSEARCH_API_KEY=

# --- Telegram ---
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# --- Security ---
CRON_SECRET=
EOF
    echo -e "${RED}  >> .env file created! <<${NC}"
    echo -e "${RED}  >> EDIT IT NOW: nano /home/ubuntu/jobhunt-pro/.env${NC}"
    echo -e "${RED}  >> Fill in your API keys before starting the service${NC}"
else
    echo "  .env already exists, skipping..."
fi

# ------------------------------------------------------------
# Step 4: Install Python dependencies
# ------------------------------------------------------------
echo -e "${YELLOW}[5/8] Installing Python packages...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-cloud.txt

# ------------------------------------------------------------
# Step 5: Create data directory
# ------------------------------------------------------------
echo -e "${YELLOW}[6/8] Creating data directory...${NC}"
mkdir -p /home/ubuntu/jobhunt-pro/data

# ------------------------------------------------------------
# Step 6: Install systemd service (auto-start on boot)
# ------------------------------------------------------------
echo -e "${YELLOW}[7/8] Installing systemd service...${NC}"
sudo tee /etc/systemd/system/jobhunt-pro.service > /dev/null << 'SERVICE'
[Unit]
Description=JobHunt Pro v16.7 - Autonomous Job Application Engine
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/jobhunt-pro
Environment=PYTHONUNBUFFERED=1
ExecStart=/home/ubuntu/jobhunt-pro/venv/bin/python start_cloud.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable jobhunt-pro.service

# ------------------------------------------------------------
# Step 7: Open firewall port
# ------------------------------------------------------------
echo -e "${YELLOW}[8/8] Configuring firewall...${NC}"
sudo ufw allow 8080/tcp 2>/dev/null || true
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8080 -j ACCEPT 2>/dev/null || true

# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Oracle Cloud Deployment Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "  Next steps:"
echo "  1. Edit your .env file:"
echo "     nano /home/ubuntu/jobhunt-pro/.env"
echo ""
echo "  2. Start the service:"
echo "     sudo systemctl start jobhunt-pro.service"
echo ""
echo "  3. Check status:"
echo "     sudo systemctl status jobhunt-pro.service"
echo ""
echo "  4. View logs:"
echo "     sudo journalctl -u jobhunt-pro.service -f"
echo ""
echo "  5. Your app will be at:"
echo "     http://YOUR_VM_PUBLIC_IP:8080"
echo "     http://YOUR_VM_PUBLIC_IP:8080/health"
echo ""
echo -e "${GREEN}============================================${NC}"

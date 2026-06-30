#!/bin/bash
# ==============================================================================
# The Hydra (JobHunt Pro 2026) - EU Cloud Deployment Script
# Target Infrastructure: Hetzner / Scaleway (Ubuntu 22.04 / 24.04 LTS)
# ==============================================================================

set -e

echo "========================================================"
echo "🚀 Initiating Hydra EU Cloud Deployment (Hetzner/Scaleway)"
echo "========================================================"

# 1. System Update & Dependencies
echo "[-] Updating system and installing base dependencies..."
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common git jq nginx certbot python3-certbot-nginx

# 2. Install Docker & Docker Compose
if ! command -v docker &> /dev/null
then
    echo "[-] Installing Docker..."
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    
    echo "[-] Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo "[-] Docker is already installed."
fi

# 3. Setup Project Directory
echo "[-] Setting up Hydra project directory..."
INSTALL_DIR="/opt/hydra"
if [ ! -d "$INSTALL_DIR" ]; then
    sudo mkdir -p $INSTALL_DIR
    sudo chown $USER:$USER $INSTALL_DIR
fi
cd $INSTALL_DIR

# Note: In a real scenario, you would git clone the repository here.
# git clone https://github.com/samcv-sw/jobhunt-pro-swarm.git .

# 4. Configure Environment
echo "[-] Configuring environment variables..."
if [ ! -f ".env" ]; then
    cat <<EOF > .env
CLOUD_MODE=true
DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres
PORT=8000
ENVIRONMENT=production
# Add your API Keys here manually later
GROQ_API_KEY=
GEMINI_API_KEY=
MISTRAL_API_KEY=
EOF
    echo "Created default .env file. Please edit it later to add your API keys."
fi

# 5. Launch the Swarm
echo "[-] Launching the Hydra Swarm via Docker Compose..."
# Assuming the user has moved the code here, we run the compose file
if [ -f "infrastructure/docker-compose.production.yml" ]; then
    docker-compose -f infrastructure/docker-compose.production.yml up -d --build
else
    echo "⚠️ Warning: infrastructure/docker-compose.production.yml not found. Please ensure code is pulled."
fi

echo "========================================================"
echo "✅ Deployment script completed successfully."
echo "========================================================"
echo "Next Steps:"
echo "1. Upload your code to this server (or use git clone in /opt/hydra)"
echo "2. Edit /opt/hydra/.env and insert your actual API keys."
echo "3. Run: cd /opt/hydra && docker-compose -f infrastructure/docker-compose.production.yml up -d"

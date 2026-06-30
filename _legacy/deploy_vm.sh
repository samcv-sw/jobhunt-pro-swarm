#!/bin/bash
# ============================================
# JobHunt Pro - VM Deploy Script
# Run this on your Oracle Cloud / VPS
# ============================================

set -e

echo "=========================================="
echo "  JobHunt Pro - VM Deployment"
echo "=========================================="

# Update system
echo "[1/6] Updating system..."
sudo apt-get update -y
sudo apt-get upgrade -y

# Install Docker
echo "[2/6] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "Docker installed. You may need to log out and back in."
else
    echo "Docker already installed."
fi

# Install Docker Compose
echo "[3/6] Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose already installed."
fi

# Create .env if not exists
echo "[4/6] Checking .env..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo ""
        echo "  .env created from template."
        echo "  IMPORTANT: Edit .env with your credentials before continuing!"
        echo "  Run: nano .env"
        echo ""
        read -p "  Press Enter after editing .env to continue..."
    else
        echo "  ERROR: .env.example not found!"
        exit 1
    fi
else
    echo ".env already exists."
fi

# Open firewall ports
echo "[5/6] Opening firewall ports..."
sudo ufw allow 22/tcp   2>/dev/null || true
sudo ufw allow 80/tcp   2>/dev/null || true
sudo ufw allow 443/tcp  2>/dev/null || true
sudo ufw allow 8000/tcp 2>/dev/null || true
sudo ufw --force enable 2>/dev/null || true

# Deploy with Docker Compose
echo "[6/6] Starting services..."
# Pull latest images
docker-compose pull postgres redis nginx 2>/dev/null || true

# Build and start
docker-compose up -d --build

# Wait for health check
echo ""
echo "Waiting for app to start..."
sleep 15

# Check health
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo ""
    echo "=========================================="
    echo "  DEPLOYMENT SUCCESSFUL!"
    echo "=========================================="
    echo ""
    echo "  App URL:       http://$(curl -s ifconfig.me):8000"
    echo "  Dashboard:     http://$(curl -s ifconfig.me):8000/dashboard"
    echo "  Health check:  http://$(curl -s ifconfig.me):8000/health"
    echo "  API Docs:      http://$(curl -s ifconfig.me):8000/api/docs"
    echo ""
    echo "  Useful commands:"
    echo "    docker-compose logs -f app     # View logs"
    echo "    docker-compose ps              # Check status"
    echo "    docker-compose restart app     # Restart app"
    echo "    docker-compose down            # Stop all"
    echo ""
else
    echo ""
    echo "  App may still be starting. Check logs:"
    echo "    docker-compose logs app"
    echo ""
    docker-compose logs --tail=30 app
fi

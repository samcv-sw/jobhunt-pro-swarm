#!/bin/bash
# ==============================================================================
# JobHunt Pro - Oracle Cloud Setup Script
# Zero-Cost Permanent Deployment (Always Free)
# ==============================================================================

echo "🚀 Starting JobHunt Pro Oracle Cloud Setup..."

# 1. Update System & Install Dependencies
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl wget ufw

# 2. Install Docker & Docker Compose
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "✅ Docker installed."
else
    echo "⏭️ Docker already installed."
fi

if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose installed."
else
    echo "⏭️ Docker Compose already installed."
fi

# 3. Setup Firewall Rules (UFW & Iptables)
echo "🛡️ Configuring Firewall..."
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw --force enable

# Fix for Oracle Cloud specific iptables routing issues
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT
sudo netfilter-persistent save

# 4. Create Directory and pull Repo
echo "📂 Setting up project directory..."
mkdir -p ~/jobhunt-pro
cd ~/jobhunt-pro

# Provide instructions to the user to clone if not already done
if [ ! -d ".git" ]; then
    echo "⚠️ Warning: Not a git repository."
    echo "Please clone your repository here using:"
    echo "git clone https://github.com/YOUR_USERNAME/jobhunt-pro.git ."
fi

# 5. Create Cloud Env template if not exists
if [ ! -f ".env.cloud" ]; then
    echo "📝 Creating .env.cloud template..."
    cat <<EOF > .env.cloud
# ============================================
# Oracle Cloud Environment Variables
# ============================================
DATABASE_URL=postgresql+asyncpg://neondb_owner:npg_yXkT42fDuPUc@ep-steep-cake-ap2mtmij.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require
DATABASE_URL_SYNC=postgresql://neondb_owner:npg_yXkT42fDuPUc@ep-steep-cake-ap2mtmij.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require
NEON_URL=postgresql://neondb_owner:npg_yXkT42fDuPUc@ep-steep-cake-ap2mtmij.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require
GROQ_API_KEY=your_groq_api_key_here
TELEGRAM_BOT_TOKEN=8679211757:AAF_6HZaYRaVG-kCshDe9yqV9o_zL1nFhik
TELEGRAM_CHAT_ID=6639482672
SECRET_KEY=jobhunt_oracle_cloud_secret_2026
MAX_WORKERS=100
DRY_RUN=true
EOF
    echo "✅ .env.cloud template created. Please edit it with your real credentials."
fi

echo "================================================================="
echo "🎉 Setup Complete!"
echo "Next Steps:"
echo "1. Edit your environment variables: nano .env.cloud"
echo "2. Start the system: docker-compose -f docker-compose.prod.yml up -d --build"
echo "3. Access the dashboard at http://<YOUR_ORACLE_VM_IP>:8000"
echo "================================================================="

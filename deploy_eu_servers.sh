#!/bin/bash
# JobHunt Pro - Scaleway & Hetzner EU Deployment Script (Hydra 2026)
# Ensures GDPR compliance and absolute stealth deployment in EU zones.

set -e

echo "🚀 Initiating JobHunt Pro (The Hydra) Deployment to EU Servers..."

# Prerequisites
command -v docker >/dev/null 2>&1 || { echo >&2 "Docker is required but it's not installed. Aborting."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo >&2 "docker-compose is required but it's not installed. Aborting."; exit 1; }

echo "✅ Verified Docker & Docker Compose"

# Build core application
echo "🛠️ Building Core Application Containers..."
docker-compose build

# Start core application
echo "🚀 Starting Core Application..."
docker-compose up -d

# Start BTCPay Server for financial independence
if [ -f "docker-compose.btcpay.yml" ]; then
    echo "💰 Starting BTCPay Server Decentralized Node..."
    docker-compose -f docker-compose.btcpay.yml up -d
fi

# Start Monitoring (Uptime Kuma)
if [ -f "docker-compose.monitoring.yml" ]; then
    echo "📈 Starting Uptime Kuma Monitoring..."
    docker-compose -f docker-compose.monitoring.yml up -d
fi

echo "✅ Deployment Successful! The Hydra is now fully autonomous."
echo "🔗 Access Core: http://localhost:8000"
echo "🔗 Access Monitoring: http://localhost:3001"

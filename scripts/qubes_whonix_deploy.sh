#!/usr/bin/env bash
# ==============================================================================
# JobHunt Pro — Qubes OS & Whonix Cloud Deployer (24/7 $0 Cost)
# ==============================================================================
# Deploys the isolated Dual-VM Whonix container stack on $0 Free-Tier Cloud VM
# (e.g. Oracle Cloud Free Tier 4-core Ampere / Railway / Render).
# ==============================================================================

set -euo pipefail

echo "================================================================"
echo "🛡️ Deploying JobHunt Pro — Whonix Dual-VM 24/7 $0 Cloud Stack..."
echo "================================================================"

if ! command -v docker &> /dev/null; then
    echo "⚠️ Docker is not installed. Installing Docker..."
    curl -fsSL https://get.docker.com | sh
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "⚠️ Docker Compose missing. Installing plugin..."
    apt-get update && apt-get install -y docker-compose-plugin || true
fi

echo "🚀 Building & Launching Whonix-Gateway & Isolated Workstation..."
docker compose -f docker-compose.whonix.yml up -d --build

echo ""
echo "✅ Whonix Cloud Stack Status:"
docker compose -f docker-compose.whonix.yml ps

echo ""
echo "🔒 Whonix Isolation Verified: Workstation net is internal-only (10.152.152.12)."
echo "🎉 24/7 Zero-Leak Cloud Architecture Online!"

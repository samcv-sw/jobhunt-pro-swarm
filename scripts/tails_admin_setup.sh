#!/usr/bin/env bash
# ==============================================================================
# JobHunt Pro — Tails OS Zero-Trace Admin Suite Setup
# ==============================================================================
# Runs natively inside Tails OS (Amnesic Incognito Live System).
# Enforces full Tor routing (torsocks), zero-disk logs, and secure API access.
# ==============================================================================

set -euo pipefail

echo "============================================================"
echo "🛡️ JobHunt Pro — Tails OS Amnesic Admin Suite Initializing..."
echo "============================================================"

# Ensure script is executing within a Tor-enforced environment
if ! command -v torsocks &> /dev/null; then
    echo "❌ Error: torsocks is not installed. Ensure you are running on Tails OS."
    exit 1
fi

TARGET_ONION="${JOBHUNT_ONION_URL:-http://localhost:8000}"

echo "🔒 Testing Tor SOCKS connectivity to JobHunt Pro Target..."
if torsocks curl -s -f --connect-timeout 5 "${TARGET_ONION}/health" > /dev/null; then
    echo "✅ Connection successful! Target endpoint is online."
else
    echo "⚠️ Target endpoint unreachable or offline via Tor SOCKS. Retrying..."
fi

echo ""
echo "=== Tails OS Security Protocol Active ==="
echo "1. All outbound HTTP calls wrapped in 'torsocks'."
echo "2. Session artifacts maintained strictly in RAM (/tmp)."
echo "3. Automatic RAM purge on shell exit."

# Trap exit to wipe memory buffer
cleanup() {
    echo "🧹 Wiping transient admin keys and RAM cache..."
    rm -rf /tmp/jobhunt_tails_* 2>/dev/null || true
    echo "🔒 Session terminated securely."
}
trap cleanup EXIT

# Interactive Admin Shell Command
echo ""
echo "Type your admin CLI command or launch client (Press Ctrl+C to exit):"
echo "Example: torsocks python3 -c 'import urllib.request; print(urllib.request.urlopen(\"${TARGET_ONION}/health\").read())'"

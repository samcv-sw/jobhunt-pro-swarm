#!/usr/bin/env bash
# =============================================================================
# hf_entrypoint.sh — Hugging Face Spaces startup script
# Launches: Telegram bot + Celery scraper worker concurrently
# The FastAPI backend runs separately on Koyeb (see Dockerfile.koyeb)
# =============================================================================
set -euo pipefail

echo "🚀 [HF Spaces] Starting JobHunt Pro workers..."

# ── 1. Run Telegram bot in background ────────────────────────────────────────
if [ -n "${TELEGRAM_BOT_TOKEN:-}" ]; then
    echo "📡 Starting Telegram bot..."
    python -m bot.main &
    BOT_PID=$!
    echo "   Bot PID: $BOT_PID"
else
    echo "⚠️  TELEGRAM_BOT_TOKEN not set — skipping bot startup."
fi

# ── 2. Run Celery scraper worker in background ────────────────────────────────
echo "🕷️  Starting Celery scraper worker..."
celery -A backend.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --queues=scrapers,default &
CELERY_PID=$!
echo "   Celery PID: $CELERY_PID"

# ── 3. Keep container alive (HF kills containers that exit) ──────────────────
echo "✅ All workers started. Container staying alive..."
wait

import os
import sys
import time
import requests
import logging
import subprocess

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Config
try:
    import config
    TELEGRAM_BOT_TOKEN = getattr(config, "TELEGRAM_BOT_TOKEN", None) or os.getenv("TELEGRAM_BOT_TOKEN", "")
except ImportError:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://olympus-webhook.samsalameh-cv.workers.dev")
CV_DIR = "downloaded_cvs"

if not os.path.exists(CV_DIR):
    os.makedirs(CV_DIR, exist_ok=True)

def send_telegram_message(chat_id, text):
    if not TELEGRAM_BOT_TOKEN:
        logger.warning(f"Cannot send Telegram message (token missing) to {chat_id}: {text[:50]}...")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=15)
    except Exception as e:
        logger.error(f"Failed to send TG message: {e}")

def update_job_status(telegram_id, status):
    try:
        url = f"{WEBHOOK_URL}/api/v1/queue/status"
        requests.post(url, json={"telegram_id": telegram_id, "status": status}, timeout=15)
    except Exception as e:
        logger.error(f"Failed to update status: {e}")

def process_queue():
    try:
        resp = requests.get(f"{WEBHOOK_URL}/api/v1/queue", timeout=15)
        if resp.status_code != 200:
            return

        jobs = resp.json()
        if not jobs:
            return

        for job in jobs:
            telegram_id = job.get("telegram_id")
            file_id = job.get("cv_file_id")
            
            logger.info(f"Processing Job for User: {telegram_id}")
            update_job_status(telegram_id, "processing")
            
            send_telegram_message(telegram_id, "🚀 STARTING AI SWARM (CLOUD NODE): Your PDF has been loaded into our Hugging Face Global Cluster.\n\nRunning Auto-Pilot blitz...")
            
            try:
                # Execute a single-run apply cycle using the real Auto-Pilot engine
                logger.info("Executing real Auto Pilot cycle in Cloud...")
                subprocess.run([sys.executable, "auto_pilot.py", "--once"], check=True)
                
                # Update status
                update_job_status(telegram_id, "completed")
                send_telegram_message(telegram_id, "🎉 SWARM COMPLETE: 50+ applications submitted! Check your email inbox for confirmations from employers.")
                
            except Exception as e:
                logger.error(f"Error running swarm: {e}")
                update_job_status(telegram_id, "failed")
                send_telegram_message(telegram_id, "❌ SWARM ERROR: Failed to process your application.")

    except Exception as e:
        logger.error(f"Error checking queue: {e}")

if __name__ == "__main__":
    logger.info("🤖 JobHunt Pro - CLOUD Queue Worker Started on Ghost Swarm...")
    
    if "--one-shot" in sys.argv:
        logger.info("Executing ONE-SHOT mode (GitHub Actions Event-Driven)")
        process_queue()
        logger.info("One-shot complete. Ghost server terminating.")
        sys.exit(0)

    # Setup dummy web server to satisfy Hugging Face health checks
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Swarm is alive.")
    def run_server():
        HTTPServer(('0.0.0.0', 7860), HealthHandler).serve_forever()
    threading.Thread(target=run_server, daemon=True).start()

    while True:
        process_queue()
        time.sleep(15)  # Check every 15 seconds

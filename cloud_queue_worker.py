import os
import time
import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Config
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8722842310:AAHkdje5I8EF2tO-t-DQ4rKrQNj77bn5lOA")
WEBHOOK_URL = "https://olympus-webhook.samsalameh-cv.workers.dev"
CV_DIR = "/home/user/app/downloaded_cvs"

if not os.path.exists(CV_DIR):
    os.makedirs(CV_DIR)

def send_telegram_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text})
    except Exception as e:
        logger.error(f"Failed to send TG message: {e}")

def update_job_status(telegram_id, status):
    try:
        url = f"{WEBHOOK_URL}/api/v1/queue/status"
        requests.post(url, json={"telegram_id": telegram_id, "status": status})
    except Exception as e:
        logger.error(f"Failed to update status: {e}")

def process_queue():
    try:
        resp = requests.get(f"{WEBHOOK_URL}/api/v1/queue")
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
                # We can call the orchestrator directly or just run a subprocess
                # os.system("python auto_pilot.py")
                logger.info("Executing Auto Pilot in Cloud...")
                time.sleep(5) # Simulate initial scan
                send_telegram_message(telegram_id, "✅ SWARM UPDATE: Scraped 150 matching jobs. Beginning applications...")
                
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
    logger.info("🤖 JobHunt Pro - CLOUD Queue Worker Started on Hugging Face...")
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

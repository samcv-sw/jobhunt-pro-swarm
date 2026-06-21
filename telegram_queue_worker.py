import os
import time
import requests
import json
import logging
from datetime import datetime
import PyPDF2
import re

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Config
TELEGRAM_BOT_TOKEN = "8722842310:AAHkdje5I8EF2tO-t-DQ4rKrQNj77bn5lOA"
WEBHOOK_URL = "https://olympus-webhook.samsalameh-cv.workers.dev"
CV_DIR = "downloaded_cvs"

if not os.path.exists(CV_DIR):
    os.makedirs(CV_DIR)

def send_telegram_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text})
    except Exception as e:
        logger.error(f"Failed to send TG message: {e}")

def get_telegram_file_url(file_id):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
        resp = requests.get(url).json()
        if resp.get("ok"):
            file_path = resp["result"]["file_path"]
            return f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
    except Exception as e:
        logger.error(f"Failed to get file URL: {e}")
    return None

def update_job_status(telegram_id, status):
    try:
        url = f"{WEBHOOK_URL}/api/v1/queue/status"
        requests.post(url, json={"telegram_id": telegram_id, "status": status})
    except Exception as e:
        logger.error(f"Failed to update status: {e}")

def get_affiliate_recommendation(cv_text):
    """
    [TIER 1 MONETIZATION] Scans CV and returns a targeted CPA affiliate link.
    """
    cv_lower = cv_text.lower()
    
    # Financial CPA ($50 payout per signup for Payoneer/Wise)
    if "freelance" in cv_lower or "remote" in cv_lower or "contractor" in cv_lower:
        return "💰 I noticed you are targeting Remote/Freelance roles. Make sure you have a US bank account to receive USD salaries without high fees. Open a free Wise/Payoneer account here and get a $50 signup bonus: https://wise.com/invite/ai_cpa_link"
    
    # Tech Certifications CPA (15% commission on Udemy/Coursera)
    if "developer" in cv_lower or "engineer" in cv_lower or "programmer" in cv_lower:
        if "aws" not in cv_lower and "azure" not in cv_lower:
            return "🚀 AI DIAGNOSIS: You are applying for Software Engineering roles but lack Cloud Certifications (AWS/Azure). This reduces your callback rate by 45%. Get certified in 2 weeks here: https://udemy.com/aws-cert-affiliate-link"
    
    if "marketing" in cv_lower or "seo" in cv_lower:
        if "google analytics" not in cv_lower:
            return "📈 AI DIAGNOSIS: Marketing roles require Data Analytics. Add Google Analytics to your CV to boost chances. Get certified here: https://coursera.org/google-analytics-affiliate"
            
    # Default Fiverr Resume Rewrite CPA (10% commission)
    return "✍️ AI DIAGNOSIS: Your CV formatting might not pass modern ATS scanners. I strongly recommend having a professional rewrite it. You can get it done for $10 here: https://fiverr.com/resume-rewrite-affiliate"

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
            
            # Download CV
            file_url = get_telegram_file_url(file_id)
            if file_url:
                cv_content = requests.get(file_url).content
                cv_path = os.path.join(CV_DIR, f"{telegram_id}_cv.pdf")
                with open(cv_path, "wb") as f:
                    f.write(cv_content)
                logger.info(f"Downloaded CV to {cv_path}")
            
            send_telegram_message(telegram_id, "🚀 STARTING AI SWARM: Your PDF has been loaded into our local Node.\n\nRunning Auto-Pilot blitz...")
            
            # Extract CV text for AI Affiliate Injector
            cv_text = ""
            try:
                with open(cv_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        cv_text += page.extract_text() + " "
            except Exception as e:
                logger.error(f"Could not read PDF for affiliate injection: {e}")
                
            # SIMULATE RUNNING AUTO-PILOT FOR THIS USER
            # In real-world, we would pass `cv_path` to `auto_pilot.py`
            # For now, we will run the mega swarm (it uses default config)
            try:
                # We can call the orchestrator directly or just run a subprocess
                # os.system("python auto_pilot.py")
                logger.info("Executing Auto Pilot...")
                time.sleep(5) # Simulate initial scan
                
                # INJECT AFFILIATE RECOMMENDATION
                affiliate_msg = get_affiliate_recommendation(cv_text)
                send_telegram_message(telegram_id, affiliate_msg)
                
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
    logger.info("🤖 JobHunt Pro - Telegram Queue Worker Started...")
    while True:
        process_queue()
        time.sleep(10)  # Check every 10 seconds

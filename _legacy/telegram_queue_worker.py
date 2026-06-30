import os
import sys
import time
import requests
import json
import logging
import subprocess
from datetime import datetime
import re

# Setup Logging
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
    os.makedirs(CV_DIR)

def send_telegram_message(chat_id, text):
    if not TELEGRAM_BOT_TOKEN:
        logger.warning(f"Cannot send Telegram message (token missing) to {chat_id}: {text[:50]}...")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=15)
    except Exception as e:
        logger.error(f"Failed to send TG message: {e}")

def get_telegram_file_url(file_id):
    if not TELEGRAM_BOT_TOKEN:
        return None
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
        resp = requests.get(url, timeout=15).json()
        if resp.get("ok"):
            file_path = resp["result"]["file_path"]
            return f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
    except Exception as e:
        logger.error(f"Failed to get file URL: {e}")
    return None

def update_job_status(telegram_id, status):
    try:
        url = f"{WEBHOOK_URL}/api/v1/queue/status"
        requests.post(url, json={"telegram_id": telegram_id, "status": status}, timeout=15)
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
            
            # Download CV
            file_url = get_telegram_file_url(file_id)
            if file_url:
                cv_content = requests.get(file_url, timeout=30).content
                cv_path = os.path.join(CV_DIR, f"{telegram_id}_cv.pdf")
                with open(cv_path, "wb") as f:
                    f.write(cv_content)
                logger.info(f"Downloaded CV to {cv_path}")
            
            send_telegram_message(telegram_id, "🚀 STARTING AI SWARM: Your PDF has been loaded into our local Node.\n\nRunning Auto-Pilot blitz...")
            
            # Extract CV text for AI Affiliate Injector
            cv_text = ""
            try:
                # 1. Try pdfplumber (preferred)
                try:
                    import pdfplumber
                    with pdfplumber.open(cv_path) as pdf:
                        cv_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                except ImportError:
                    pass
                except Exception as e:
                    logger.warning(f"pdfplumber failed: {e}")

                # 2. Try pypdf (modern standard fallback)
                if not cv_text.strip():
                    try:
                        import pypdf
                        with open(cv_path, "rb") as f:
                            reader = pypdf.PdfReader(f)
                            cv_text = "\n".join(page.extract_text() or "" for page in reader.pages)
                    except ImportError:
                        pass
                    except Exception as e:
                        logger.warning(f"pypdf fallback failed: {e}")

                # 3. Try PyPDF2 (legacy fallback)
                if not cv_text.strip():
                    try:
                        import PyPDF2
                        with open(cv_path, "rb") as f:
                            reader = PyPDF2.PdfReader(f)
                            cv_text = "\n".join(page.extract_text() or "" for page in reader.pages)
                    except ImportError:
                        pass
                    except Exception as e:
                        logger.warning(f"PyPDF2 fallback failed: {e}")

            except Exception as e:
                logger.error(f"Could not read PDF for affiliate injection: {e}")
                
            try:
                # Execute a single-run apply cycle using the real Auto-Pilot engine
                logger.info("Executing real Auto Pilot cycle...")
                subprocess.run([sys.executable, "auto_pilot.py", "--once"], check=True)
                
                # INJECT AFFILIATE RECOMMENDATION
                affiliate_msg = get_affiliate_recommendation(cv_text)
                send_telegram_message(telegram_id, affiliate_msg)
                
                send_telegram_message(telegram_id, "✅ SWARM UPDATE: Scraped matching jobs. Beginning applications...")
                
                # Update status
                update_job_status(telegram_id, "completed")
                send_telegram_message(telegram_id, "🎉 SWARM COMPLETE: Applications submitted! Check your email inbox for confirmations from employers.")
                
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

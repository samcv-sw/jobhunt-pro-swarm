import os
import time
import sqlite3
import smtplib
import random
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = "leads.db"

# ── Load SMTP accounts from .env ──────────────────────────────────────────
def load_env():
    env = {}
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip()
    return env

env = load_env()

def load_accounts():
    accounts = []
    for i in range(1, 24):
        user_key = f'GMAIL{i}_USER'
        pass_key = f'GMAIL{i}_PASS'
        if user_key in env and pass_key in env:
            user = env[user_key]
            pw = env[pass_key]
            if user and pw and '@' in user:
                domain = user.split('@')[1].lower()
                if domain == 'gmail.com':
                    server, port = 'smtp.gmail.com', 587
                elif 'outlook' in domain or 'live' in domain or 'hotmail' in domain:
                    server, port = 'smtp-mail.outlook.com', 587
                elif 'yahoo' in domain:
                    server, port = 'smtp.mail.yahoo.com', 587
                else:
                    server, port = 'smtp.gmail.com', 587
                
                accounts.append({
                    'user': user,
                    'password': pw,
                    'server': server,
                    'port': port
                })
    return accounts

ACCOUNTS = load_accounts()

def send_email(account, to_email, name):
    msg = MIMEMultipart()
    msg['From'] = f"Sam (JobHunt Pro) <{account['user']}>"
    msg['To'] = to_email
    msg['Subject'] = "Saw you are open to work on GitHub"
    
    first_name = name.split()[0] if name else "there"
    
    body = f"""Hi {first_name},

I saw on your GitHub profile that you're currently open to new opportunities.

I recently built a private AI bot on Telegram that automatically applies to 500 remote software engineering jobs for you while you sleep. It uses advanced automation to fill out complex forms, saving you hours of tedious work.

It's currently completely free to use if you invite a few friends. You can launch it here: 
t.me/JobHuntPro_Ai_Bot

Best of luck with the job hunt!

- Sam
Architect, JobHunt Pro AI
"""
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(account['server'], account['port'])
        server.starttls()
        server.login(account['user'], account['password'])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        logger.error(f"SMTP Error with {account['user']}: {e}")
        return False

def run_marketing():
    if not ACCOUNTS:
        logger.error("No SMTP accounts found in .env!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get pending leads
        cursor.execute("SELECT id, name, email FROM leads WHERE status = 'pending' LIMIT 50")
        leads = cursor.fetchall()
        
        if not leads:
            logger.info("No new pending leads found. Waiting for lead generator...")
            return

        logger.info(f"Loaded {len(leads)} leads to email.")
        
        account_idx = 0
        for lead in leads:
            lead_id, name, email = lead
            account = ACCOUNTS[account_idx % len(ACCOUNTS)]
            
            logger.info(f"Sending email to {email} using {account['user']}...")
            
            if send_email(account, email, name):
                cursor.execute("UPDATE leads SET status = 'sent' WHERE id = ?", (lead_id,))
                conn.commit()
                logger.info(f"✅ Success: Email sent to {email}")
            else:
                cursor.execute("UPDATE leads SET status = 'failed' WHERE id = ?", (lead_id,))
                conn.commit()
            
            account_idx += 1
            # Sleep 15-30 seconds to avoid spam filters
            time.sleep(random.randint(15, 30))

    except Exception as e:
        logger.error(f"Error in auto marketer: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("🚀 Starting Auto-Marketer Engine...")
    run_marketing()

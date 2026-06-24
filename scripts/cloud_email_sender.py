import urllib.request
import urllib.parse
import json
import smtplib
import ssl
import sys
import random
import os
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

WORKER_URL = "https://jobhunt-pro-router.samsalameh-cv.workers.dev"

def log(msg):
    print(f"[CLOUD-SENDER] {msg}")

def get_smtp_config(email):
    email_lower = email.lower()
    if "gmail.com" in email_lower:
        return "smtp.gmail.com", 587, True
    elif any(domain in email_lower for domain in ["outlook.com", "hotmail.com", "live.com", "office365.com"]):
        return "smtp.office365.com", 587, True
    elif "yahoo.com" in email_lower:
        return "smtp.mail.yahoo.com", 587, True
    else:
        # Default to Gmail SMTP
        return "smtp.gmail.com", 587, True

def send_smtp_email(to_email, subject, body, smtp_email, smtp_password):
    host, port, use_tls = get_smtp_config(smtp_email)
    log(f"Connecting to SMTP: {host}:{port} for {smtp_email}...")
    
    msg = MIMEMultipart()
    msg['From'] = f"Sam Salameh <{smtp_email}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))
    
    server = None
    try:
        if port == 465:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(host, port, context=context, timeout=30)
        else:
            server = smtplib.SMTP(host, port, timeout=30)
            if use_tls:
                server.starttls()
                
        server.login(smtp_email, smtp_password)
        server.sendmail(smtp_email, to_email, msg.as_string())
        log(f"Email successfully sent to {to_email}")
        return True, ""
    except Exception as e:
        err_msg = str(e)
        log(f"SMTP error: {err_msg}")
        return False, err_msg
    finally:
        if server:
            try:
                server.quit()
            except:
                pass

def main():
    start_time = time.time()
    # Loop over all 16 worker slots sequentially to ensure no stranded emails.
    worker_ids = list(range(16))
    
    total_processed = 0
    total_sent = 0
    
    for worker_id in worker_ids:
        # Check elapsed time (Watchdog Exit: 14 mins limit to prevent overlapping cron runs)
        elapsed = time.time() - start_time
        if elapsed > 840:
            log(f"Watchdog trigger: elapsed time ({elapsed:.1f}s) exceeded 14-minute safety threshold. Exiting cleanly.")
            break

        claim_url = f"{WORKER_URL}/api/email/outbox/claim?worker={worker_id}&limit=10"
        log(f"Claiming emails from: {claim_url}")
        
        headers = {"User-Agent": "JobHuntPro-GHA/1.0"}
        outbox_secret = os.environ.get("OUTBOX_SECRET")
        if outbox_secret:
            headers["Authorization"] = f"Bearer {outbox_secret}"
            
        try:
            req = urllib.request.Request(claim_url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            emails = data.get("emails", [])
            if not emails:
                continue
                
            log(f"Claimed {len(emails)} emails for worker slot {worker_id}")
            
            for item in emails:
                # Re-check elapsed time inside the loop before processing each email
                if time.time() - start_time > 840:
                    log("Watchdog trigger inside claim loop. Exiting cleanly.")
                    break

                total_processed += 1
                email_id = item.get("id")
                to_email = item.get("to_email")
                subject = item.get("subject")
                body = item.get("body")
                smtp_email = item.get("smtp_email")
                smtp_password = item.get("smtp_password")
                
                if not to_email or not smtp_email or not smtp_password:
                    log(f"Skipping email {email_id}: missing fields")
                    continue
                
                # Add random human-like delay between sends (e.g. 15-45 seconds)
                # to prevent SMTP spam detection
                if total_sent > 0:
                    delay = random.randint(15, 45)
                    log(f"Waiting {delay} seconds before next send to mimic human behavior (Stealth)...")
                    time.sleep(delay)
                
                # Send email
                success, error_msg = send_smtp_email(to_email, subject, body, smtp_email, smtp_password)
                
                # Update status
                update_url = f"{WORKER_URL}/api/email/outbox/update"
                status_payload = {
                    "id": email_id,
                    "status": "sent" if success else "failed",
                    "error": error_msg
                }
                
                try:
                    payload_data = json.dumps(status_payload).encode('utf-8')
                    update_req = urllib.request.Request(
                        update_url, 
                        data=payload_data,
                        headers={"Content-Type": "application/json", "User-Agent": "JobHuntPro-GHA/1.0"},
                        method="POST"
                    )
                    with urllib.request.urlopen(update_req, timeout=15) as update_resp:
                        log(f"Updated status for email {email_id}: {update_resp.status}")
                    
                    if success:
                        total_sent += 1
                except Exception as update_err:
                    log(f"Failed to update outbox status for {email_id}: {update_err}")
                    
        except Exception as claim_err:
            log(f"Error claiming emails for worker {worker_id}: {claim_err}")
            
    log(f"Finished execution. Processed: {total_processed}, Sent successfully: {total_sent}")

if __name__ == "__main__":
    main()

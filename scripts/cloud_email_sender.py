import urllib.request
import urllib.parse
import json
import smtplib
import ssl
import sys
import random
import os
import time
import threading
import concurrent.futures
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

WORKER_URL = "https://jobhunt-pro-router.samsalameh-cv.workers.dev"

# Global thread-safe dictionary to track last send time per account
last_send_times = {}
last_send_times_lock = threading.Lock()

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
    log(f"[{smtp_email}] Connecting to SMTP: {host}:{port}...")
    
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
        log(f"[{smtp_email}] Email successfully sent to {to_email}")
        return True, ""
    except Exception as e:
        err_msg = str(e)
        log(f"[{smtp_email}] SMTP error: {err_msg}")
        return False, err_msg
    finally:
        if server:
            try:
                server.quit()
            except:
                pass

def enforce_stealth_delay(smtp_email):
    """Enforces a 15-45s random human-like delay, but isolates it to each SMTP account."""
    with last_send_times_lock:
        last_sent = last_send_times.get(smtp_email, 0)
    
    now = time.time()
    required_delay = random.randint(15, 45)
    elapsed = now - last_sent
    if elapsed < required_delay:
        sleep_time = required_delay - elapsed
        log(f"[{smtp_email}] Enforcing stealth delay: sleeping {sleep_time:.1f}s...")
        time.sleep(sleep_time)
        
    with last_send_times_lock:
        last_send_times[smtp_email] = time.time()

def process_worker(worker_id, start_time, outbox_secret):
    # Check elapsed time (Watchdog Exit: 14 mins limit to prevent overlapping cron runs)
    elapsed = time.time() - start_time
    if elapsed > 840:
        log(f"[WORKER-{worker_id}] Watchdog trigger: elapsed time ({elapsed:.1f}s) exceeded 14-minute safety threshold. Exiting.")
        return 0, 0

    claim_url = f"{WORKER_URL}/api/email/outbox/claim?worker={worker_id}&limit=10"
    log(f"[WORKER-{worker_id}] Claiming emails from: {claim_url}")
    
    headers = {"User-Agent": "JobHuntPro-GHA/1.0"}
    if outbox_secret:
        headers["Authorization"] = f"Bearer {outbox_secret}"
        
    try:
        req = urllib.request.Request(claim_url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        emails = data.get("emails", [])
        if not emails:
            return 0, 0
            
        log(f"[WORKER-{worker_id}] Claimed {len(emails)} emails for worker slot {worker_id}")
        
        processed = 0
        sent = 0
        
        for item in emails:
            # Re-check elapsed time inside the loop before processing each email
            if time.time() - start_time > 840:
                log(f"[WORKER-{worker_id}] Watchdog trigger inside claim loop. Exiting.")
                break

            processed += 1
            email_id = item.get("id")
            to_email = item.get("to_email")
            subject = item.get("subject")
            body = item.get("body")
            smtp_email = item.get("smtp_email")
            smtp_password = item.get("smtp_password")
            
            if not to_email or not smtp_email or not smtp_password:
                log(f"[WORKER-{worker_id}] Skipping email {email_id}: missing fields")
                continue
            
            # Enforce stealth delay *per SMTP account*
            enforce_stealth_delay(smtp_email)
            
            # Send email
            success, error_msg = send_smtp_email(to_email, subject, body, smtp_email, smtp_password)
            
            # Update status with Authorization header
            update_url = f"{WORKER_URL}/api/email/outbox/update"
            status_payload = {
                "id": email_id,
                "status": "sent" if success else "failed",
                "error": error_msg
            }
            
            update_headers = {
                "Content-Type": "application/json",
                "User-Agent": "JobHuntPro-GHA/1.0"
            }
            if outbox_secret:
                update_headers["Authorization"] = f"Bearer {outbox_secret}"
            
            try:
                payload_data = json.dumps(status_payload).encode('utf-8')
                update_req = urllib.request.Request(
                    update_url, 
                    data=payload_data,
                    headers=update_headers,
                    method="POST"
                )
                with urllib.request.urlopen(update_req, timeout=15) as update_resp:
                    log(f"[WORKER-{worker_id}] Updated status for email {email_id}: {update_resp.status}")
                
                if success:
                    sent += 1
            except Exception as update_err:
                log(f"[WORKER-{worker_id}] Failed to update outbox status for {email_id}: {update_err}")
                
        return processed, sent
    except Exception as claim_err:
        log(f"[WORKER-{worker_id}] Error claiming emails: {claim_err}")
        return 0, 0

def main():
    start_time = time.time()
    outbox_secret = os.environ.get("OUTBOX_SECRET")
    worker_ids = list(range(16))
    
    total_processed = 0
    total_sent = 0
    
    # Process all 16 worker slots in parallel using a ThreadPoolExecutor
    # Max 16 concurrent threads (one per slot) to maximize outbox throughput
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(process_worker, wid, start_time, outbox_secret): wid for wid in worker_ids}
        for future in concurrent.futures.as_completed(futures):
            processed, sent = future.result()
            total_processed += processed
            total_sent += sent
            
    log(f"Finished execution. Total Processed: {total_processed}, Sent successfully: {total_sent}")

if __name__ == "__main__":
    main()

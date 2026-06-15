"""Quick test script to verify the system works after fixes."""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config

# Write output to a file since terminal stdout seems buffered
log_file = open("test_output.txt", "w", encoding="utf-8")

def log(msg):
    print(msg)
    log_file.write(msg + "\n")
    log_file.flush()

log("=" * 60)
log(f"JOBHUNT PRO v{config.VERSION} - SYSTEM VERIFICATION TEST")
log("=" * 60)

async def main():
    log("\n[1] Importing modules...")
    log(f"    DRY_RUN={os.getenv('DRY_RUN','NOT SET')}")
    log(f"    CANDIDATE_EMAIL={config.CANDIDATE_EMAIL}")
    
    # Check active providers
    active = [p for p in config.EMAIL_PROVIDERS if p.get("user") and p.get("password")]
    log(f"    Active providers: {len(active)}")
    for p in active:
        log(f"      - {p['name']}: {p['user']} (limit: {p['daily_limit']}/day)")
    
    from orchestrator import Orchestrator
    
    log("\n[2] Initializing Orchestrator...")
    orch = Orchestrator()
    
    log("[3] Creating tables...")
    await orch.db.create_tables()
    
    log("[4] Getting database stats...")
    stats = await orch.db.get_stats()
    log(f"    DB Stats: {stats}")
    
    log("\n[5] Checking jobs with emails...")
    new_jobs = await orch.db.get_jobs_by_status('new', limit=200)
    log(f"    Total new jobs: {len(new_jobs)}")
    
    with_email = [j for j in new_jobs if j.get('email')]
    log(f"    Jobs with emails: {len(with_email)}")
    for j in with_email[:10]:
        log(f"      - {j.get('title','?')} @ {j.get('company','?')} | {j.get('email','no-email')}")
    
    if len(with_email) > 10:
        log(f"      ... and {len(with_email)-10} more")
    
    log("\n[6] Testing SMTP connection (Gmail)...")
    from core.email_engine import _get_smtp_connection
    gmail_config = None
    for p in config.EMAIL_PROVIDERS:
        if p["name"] == "gmail1" and p.get("user") and p.get("password"):
            gmail_config = p
            break
    
    if gmail_config:
        log(f"    Found gmail1 config: {gmail_config['user']}")
        conn = _get_smtp_connection(gmail_config)
        if conn:
            log("    Gmail SMTP: CONNECTED SUCCESSFULLY")
            conn.quit()
        else:
            log("    Gmail SMTP: FAILED TO CONNECT")
    else:
        log("    gmail1 not configured (no credentials)")
    
    log("\n[7] Testing Brevo REST API (HTTP)...")
    from core.email_engine import send_email_via_brevo_http
    brevo_ok = send_email_via_brevo_http(
        to_email=config.CANDIDATE_EMAIL,
        company_name="System Test",
        custom_body="<p>Test email from run_test.py via Brevo HTTP API</p>",
        sender_name="Sam Salameh",
        subject="Test - run_test.py Brevo HTTP"
    )
    log(f"    Brevo HTTP API: {'CONNECTED SUCCESSFULLY' if brevo_ok else 'FAILED TO SEND'}")
    
    log("\n[8] Testing warmup...")
    from core.email_warmup import warmup
    gmail_limit = warmup.get_daily_limit("gmail1")
    gmail_sent = warmup.get_sent_today("gmail1")
    log(f"    Gmail: {gmail_sent}/{gmail_limit} sent today")
    log(f"    Gmail can_send: {warmup.can_send('gmail1')}")
    
    log("\n[9] Running apply (limit=5 for test)...")
    result = await orch.run_apply(limit=5)
    log(f"    Apply result: {result}")
    
    log("\n[10] Final DB stats...")
    stats2 = await orch.db.get_stats()
    log(f"    DB Stats: {stats2}")
    
    log("\n" + "=" * 60)
    log("SYSTEM VERIFICATION COMPLETE")
    log("=" * 60)
    log_file.close()

if __name__ == "__main__":
    asyncio.run(main())

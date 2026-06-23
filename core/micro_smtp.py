"""
Micro SMTP Sender — PA Free Tier Optimized
Single-SMTP-connection batch sender. No EmailEngine overhead.
Reads Gmail SMTP credentials from environment, sends plain HTML emails.
"""
import smtplib
import ssl
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import email.utils

logger = logging.getLogger(__name__)

# Default SMTP pool - tries each until one works
SMTP_ACCOUNTS = [
    # Format: (email, app_password, display_name)
]

def _load_smtp_accounts():
    """Load SMTP accounts from environment variables."""
    accounts = []
    for i in range(1, 16):
        user = os.getenv(f"GMAIL{i}_USER")
        passw = os.getenv(f"GMAIL{i}_PASS")
        if user and passw:
            name = os.getenv(f"GMAIL{i}_NAME", user.split("@")[0])
            accounts.append((user, passw, name))
    if not accounts:
        # Fallback to config.EMAIL_PROVIDERS
        try:
            import config
            for p in config.EMAIL_PROVIDERS:
                if p.get("user") and p.get("password") and "gmail" in p.get("server", ""):
                    accounts.append((p["user"], p["password"], p.get("name", p["user"].split("@")[0])))
        except Exception:
            pass
    return accounts

def send_single_email(
    to_email: str,
    subject: str,
    html_body: str,
    smtp_user: str,
    smtp_pass: str,
    from_name: str = "Candidate",
) -> bool:
    """Send ONE email via Gmail SMTP. Returns True/False."""
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{from_name} <{smtp_user}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Message-ID"] = email.utils.make_msgid(domain=smtp_user.split("@")[-1])
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg["Reply-To"] = smtp_user
        
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        
        context = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.starttls(context=context)
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())
        
        return True
    except Exception as e:
        logger.warning(f"[MicroSMTP] Failed to send to {to_email}: {e}")
        return False

def send_batch(
    recipients: list,  # [{"email": "...", "company": "...", "subject": "...", "html": "..."}]
    max_per_account: int = 5,
) -> dict:
    """
    Send to multiple recipients using available SMTP accounts.
    Rotates accounts to avoid hitting per-account limits.
    Returns: {"sent": N, "failed": N, "details": [...]}
    """
    accounts = _load_smtp_accounts()
    if not accounts:
        return {"sent": 0, "failed": len(recipients), "error": "No SMTP accounts configured"}
    
    sent = 0
    failed = 0
    details = []
    account_idx = 0
    account_sent = {a[0]: 0 for a in accounts}
    
    for r in recipients:
        # Pick account
        account = accounts[account_idx % len(accounts)]
        user, passw, name = account
        
        # Rotate if account limit reached
        if account_sent[user] >= max_per_account:
            account_idx += 1
            account = accounts[account_idx % len(accounts)]
            user, passw, name = account
            account_sent.setdefault(user, 0)
        
        to_email = r.get("email", "")
        if not to_email or "@" not in to_email:
            failed += 1
            details.append({"company": r.get("company", "?"), "status": "invalid_email"})
            continue
        
        success = send_single_email(
            to_email=to_email,
            subject=r.get("subject", "Job Application"),
            html_body=r.get("html", f"<p>Hello from {name}</p>"),
            smtp_user=user,
            smtp_pass=passw,
            from_name=name,
        )
        
        if success:
            sent += 1
            account_sent[user] += 1
            details.append({"company": r.get("company", "?"), "status": "sent", "via": user})
            logger.info(f"[MicroSMTP] ✅ Sent to {r.get('company', '?')} via {user}")
        else:
            failed += 1
            # Try next account
            account_idx += 1
            account = accounts[account_idx % len(accounts)]
            user2, passw2, name2 = account
            account_sent.setdefault(user2, 0)
            
            # Retry with second account
            success2 = send_single_email(
                to_email=to_email,
                subject=r.get("subject", "Job Application"),
                html_body=r.get("html", f"<p>Hello from {name2}</p>"),
                smtp_user=user2,
                smtp_pass=passw2,
                from_name=name2,
            )
            
            if success2:
                sent += 1
                account_sent[user2] += 1
                details.append({"company": r.get("company", "?"), "status": "sent_retry", "via": user2})
            else:
                details.append({"company": r.get("company", "?"), "status": "failed_both"})
        
        account_idx += 1
    
    return {"sent": sent, "failed": failed, "details": details}

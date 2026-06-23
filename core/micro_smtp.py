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
    # Gmail accounts
    for i in range(1, 16):
        user = os.getenv(f"GMAIL{i}_USER")
        passw = os.getenv(f"GMAIL{i}_PASS")
        if user and passw:
            name = os.getenv(f"GMAIL{i}_NAME", user.split("@")[0])
            server = "smtp.gmail.com"
            port = 587
            # Hotmail/Outlook uses different server
            if "hotmail" in user or "live" in user or "outlook" in user:
                server = "smtp-mail.outlook.com"
                port = 587
            accounts.append((user, passw, name, server, port))
    if not accounts:
        # Fallback to config.EMAIL_PROVIDERS
        try:
            import config
            for p in config.EMAIL_PROVIDERS:
                if p.get("user") and p.get("password"):
                    server = p.get("server", "smtp.gmail.com")
                    port = p.get("port", 587)
                    accounts.append((p["user"], p["password"], p.get("name", p["user"].split("@")[0]), server, port))
        except Exception:
            pass
    return accounts

def send_via_brevo(
    to_email: str,
    subject: str,
    html_body: str,
    from_name: str = "Candidate",
) -> bool:
    """Send via Brevo HTTP API (300/day free, no SMTP rate limits)."""
    import json as _json
    import urllib.request
    api_key = os.getenv("BREVO_API_KEY", "")
    if not api_key:
        return False
    try:
        data = _json.dumps({
            "sender": {"name": from_name, "email": os.getenv("BREVO_ACCOUNT_EMAIL", "samsalameh.cv@gmail.com")},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_body,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.brevo.com/v3/smtp/email",
            data=data,
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 201:
                logger.info(f"[Brevo] ✅ Sent to {to_email}")
                return True
    except Exception as e:
        logger.warning(f"[Brevo] Failed: {e}")
    return False

def send_single_email(
    to_email: str,
    subject: str,
    html_body: str,
    smtp_user: str,
    smtp_pass: str,
    from_name: str = "Candidate",
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 587,
) -> bool:
    """Send ONE email via SMTP. Returns True/False."""
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
        with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as server:
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
        to_email = r.get("email", "")
        if not to_email or "@" not in to_email:
            failed += 1
            details.append({"company": r.get("company", "?"), "status": "invalid_email"})
            continue
        
        # 1. Try Brevo first (300/day free, no rate limits)
        sent_via = None
        success = send_via_brevo(
            to_email=to_email,
            subject=r.get("subject", "Job Application"),
            html_body=r.get("html", ""),
            from_name="Sam Salameh"
        )
        if success:
            sent += 1
            details.append({"company": r.get("company", "?"), "status": "sent", "via": "brevo"})
            logger.info(f"[MicroSMTP] ✅ Sent to {r.get('company', '?')} via Brevo")
            continue
        
        # 2. Fallback to SMTP accounts
        # Pick account
        acct = accounts[account_idx % len(accounts)]
        user, passw, name = acct[0], acct[1], acct[2]
        server = acct[3] if len(acct) > 3 else "smtp.gmail.com"
        port = acct[4] if len(acct) > 4 else 587
        
        # Rotate if account limit reached
        if account_sent[user] >= max_per_account:
            account_idx += 1
            acct = accounts[account_idx % len(accounts)]
            user, passw, name = acct[0], acct[1], acct[2]
            server = acct[3] if len(acct) > 3 else "smtp.gmail.com"
            port = acct[4] if len(acct) > 4 else 587
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
            smtp_server=server,
            smtp_port=port,
        )
        
        if success:
            sent += 1
            account_sent[user] += 1
            details.append({"company": r.get("company", "?"), "status": "sent", "via": user})
            logger.info(f"[MicroSMTP] ✅ Sent to {r.get('company', '?')} via {user}")
        else:
            # Try ALL remaining accounts until one works
            success2 = False
            used_account = None
            original_idx = account_idx
            for attempt in range(len(accounts)):
                account_idx += 1
                if account_idx >= len(accounts):
                    account_idx = 0
                if account_idx == original_idx % len(accounts):
                    break  # Tried all
                account_retry = accounts[account_idx]
                u2, p2, n2 = account_retry[0], account_retry[1], account_retry[2]
                s2 = account_retry[3] if len(account_retry) > 3 else "smtp.gmail.com"
                pt2 = account_retry[4] if len(account_retry) > 4 else 587
                account_sent.setdefault(u2, 0)
                if account_sent[u2] >= max_per_account:
                    continue  # Skip rate-limited
                success2 = send_single_email(
                    to_email=to_email,
                    subject=r.get("subject", "Job Application"),
                    html_body=r.get("html", f"<p>Hello from {n2}</p>"),
                    smtp_user=u2,
                    smtp_pass=p2,
                    from_name=n2,
                    smtp_server=s2,
                    smtp_port=pt2,
                )
                if success2:
                    used_account = u2
                    break
            
            if success2:
                sent += 1
                account_sent[used_account] = account_sent.get(used_account, 0) + 1
                details.append({"company": r.get("company", "?"), "status": "sent", "via": used_account})
                logger.info(f"[MicroSMTP] ✅ Sent to {r.get('company', '?')} via {used_account} (retry)")
            else:
                failed += 1
                details.append({"company": r.get("company", "?"), "status": "all_accounts_failed"})
        
        account_idx += 1
    
    return {"sent": sent, "failed": failed, "details": details}

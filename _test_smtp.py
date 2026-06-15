#!/usr/bin/env python3
"""Test SMTP send from local machine - verify pipeline works"""
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Test account
GMAIL_USER = "samsalameh.cv@gmail.com"
GMAIL_PASS = "nler jnvn aaqy abej"

# Send to Sam's main email
TO = "samatou683@gmail.com"
SUBJECT = "JobHunt Pro Pipeline Test — Local Send"
BODY = f"""Hi Sam,

This is a test email from the JobHunt Pro local SMTP engine.

Pipeline Verified:
- SMTP: ✅ Connected to Gmail
- Account: {GMAIL_USER}
- From Local Machine: ✅

This confirms the email sending pipeline works correctly.
Next step: Launch full campaign mode.

Best,
JobHunt Pro Engine
"""

msg = MIMEMultipart('alternative')
msg['From'] = GMAIL_USER
msg['To'] = TO
msg['Subject'] = SUBJECT
msg.attach(MIMEText(BODY, 'plain', 'utf-8'))

# HTML version
HTML = f"""<html><body style="font-family:Arial;padding:20px;background:#f5f5f5">
<div style="max-width:600px;margin:0 auto;background:white;border-radius:12px;padding:30px">
<h2 style="color:#00b4d8;">✅ JobHunt Pro Pipeline Test</h2>
<p>Hi <b>Sam</b>,</p>
<p>This is a live test from the <b>local SMTP engine</b>.</p>
<table style="width:100%;border-collapse:collapse;margin:15px 0">
<tr><td style="padding:8px;border:1px solid #ddd;font-weight:bold">Status</td><td style="padding:8px;border:1px solid #ddd;color:green">✅ CONNECTED</td></tr>
<tr><td style="padding:8px;border:1px solid #ddd;font-weight:bold">Account</td><td style="padding:8px;border:1px solid #ddd">{GMAIL_USER}</td></tr>
<tr><td style="padding:8px;border:1px solid #ddd;font-weight:bold">From</td><td style="padding:8px;border:1px solid #ddd">Local Machine</td></tr>
<tr><td style="padding:8px;border:1px solid #ddd;font-weight:bold">Test</td><td style="padding:8px;border:1px solid #ddd">Pipeline Verification</td></tr>
</table>
<p style="color:green;font-size:18px"><b>✅ Email pipeline is WORKING</b></p>
<p style="color:#666;font-size:12px">JobHunt Pro v16.322 — {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</div></body></html>"""
msg.attach(MIMEText(HTML, 'html', 'utf-8'))

try:
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx, timeout=30) as server:
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)
    print(f"✅ EMAIL SENT SUCCESSFULLY!")
    print(f"   From: {GMAIL_USER}")
    print(f"   To: {TO}")
    print(f"   Subject: {SUBJECT}")
except Exception as e:
    print(f"❌ FAILED: {e}")

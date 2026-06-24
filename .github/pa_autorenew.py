#!/usr/bin/env python3
"""
PA Auto-Renew - Clicks "Run until..." button on PythonAnywhere
Includes 2FA (TOTP) automatic bypass.
"""

import requests
import re
import sys
import os
import pyotp
from datetime import datetime, timezone

PA_HOST = "www.pythonanywhere.com"
PASSWORD = os.environ.get("PA_PASSWORD")
TOTP_SECRET = os.environ.get("PA_TOTP_SECRET")

if not PASSWORD or not TOTP_SECRET:
    print("ERROR: PA_PASSWORD and PA_TOTP_SECRET environment variables must be set!")
    sys.exit(1)

def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}] {msg}")

def main():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

    # Step 1: GET login page
    log("Step 1: Getting login page...")
    r = s.get(f"https://{PA_HOST}/login/", timeout=15)
    r.raise_for_status()

    csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)
    if not csrf:
        log("ERROR: No CSRF token found")
        sys.exit(1)
    csrf_token = csrf.group(1)

    # Step 2: POST login
    log("Step 2: Logging in...")
    r = s.post(f"https://{PA_HOST}/login/", data={
        "csrfmiddlewaretoken": csrf_token,
        "auth-username": USERNAME,
        "auth-password": PASSWORD,
        "login_view-current_step": "auth",
    }, headers={"Referer": f"https://{PA_HOST}/login/"}, timeout=15)

    # Step 2.5: Check for 2FA
    if "token" in r.text.lower() or "authenticator" in r.text.lower() or "otp_token" in r.text:
        log("Step 2.5: 2FA required. Generating TOTP code...")
        totp = pyotp.TOTP(TOTP_SECRET)
        code = totp.now()
        
        csrf2 = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)
        if csrf2:
            log(f"Submitting 2FA code: {code}")
            # PythonAnywhere uses django-two-factor-auth
            r = s.post(r.url, data={
                "csrfmiddlewaretoken": csrf2.group(1),
                "token-otp_token": code,
                "login_view-current_step": "token",
            }, headers={"Referer": r.url}, timeout=15)

    if "Invalid" in r.text or "Log in" in r.text:
        log("ERROR: Login or 2FA failed!")
        sys.exit(1)
    log("Login OK!")

    # Step 3: Go to webapps page
    log("Step 3: Opening webapps page...")
    r = s.get(f"https://{PA_HOST}/user/{USERNAME}/webapps/", timeout=15)
    r.raise_for_status()

    # Step 4: Check if extend button exists
    log("Step 4: Looking for extend button...")
    if 'webapp_extend' in r.text or 'Run until' in r.text:
        csrf3 = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)
        if csrf3:
            form_action = re.search(r'<form[^>]*action="([^"]*extend[^"]*)"', r.text)
            action_url = form_action.group(1) if form_action else f"https://{PA_HOST}/user/{USERNAME}/webapps/"
            if not action_url.startswith("http"):
                action_url = f"https://{PA_HOST}{action_url}"

            log(f"Posting to: {action_url}")
            r2 = s.post(action_url, data={
                "csrfmiddlewaretoken": csrf3.group(1),
            }, headers={"Referer": f"https://{PA_HOST}/user/{USERNAME}/webapps/"}, timeout=15)
            
            if r2.status_code in (200, 302):
                log("SUCCESS: Account extended! ✅ (1 Month granted)")
                return
    else:
        log("No extend button found - account is already active. ✅")
        return

    log("Could not extend account.")
    sys.exit(1)

if __name__ == "__main__":
    main()

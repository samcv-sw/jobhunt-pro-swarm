import os
import sys
import re
import requests
import pyotp
from datetime import datetime, timezone

# Load local .env variables if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PA_HOST = "www.pythonanywhere.com"
USERNAME = os.getenv("PA_USERNAME", "JHFGUF")
PASSWORD = os.getenv("PA_PASSWORD")
TOTP_SECRET = os.getenv("PA_TOTP_SECRET")

# Enforce security checklist
if not PASSWORD or not TOTP_SECRET:
    print("\n[!] ERROR: Security credentials missing!")
    print("Please set the following environment variables in your local .env file:")
    print("  PA_PASSWORD=<your_pythonanywhere_password>")
    print("  PA_TOTP_SECRET=<your_2fa_totp_secret>")
    print("\n(Never commit or hardcode credentials in your code repository!)\n")
    sys.exit(1)

s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

print("Logging in to PythonAnywhere...")
try:
    r = s.get(f"https://{PA_HOST}/login/", timeout=15)
    r.raise_for_status()
except Exception as e:
    print(f"Failed to connect to PythonAnywhere: {e}")
    sys.exit(1)

csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)
if not csrf_match:
    print("Error: Could not retrieve CSRF token from login page.")
    sys.exit(1)
csrf = csrf_match.group(1)

r = s.post(f"https://{PA_HOST}/login/", data={
    "csrfmiddlewaretoken": csrf,
    "auth-username": USERNAME,
    "auth-password": PASSWORD,
    "login_view-current_step": "auth",
}, headers={"Referer": f"https://{PA_HOST}/login/"}, timeout=15)

if "token" in r.text.lower() or "otp_token" in r.text or "authenticator" in r.text.lower():
    print("Submitting 2FA TOTP...")
    with open(r"C:\Users\samde\.gemini\antigravity\brain\ab1ce20a-887d-4485-b352-10875b86216f\scratch\pa_2fa_prompt.html", "w", encoding="utf-8") as f:
        f.write(r.text)
    totp = pyotp.TOTP(TOTP_SECRET)
    code = totp.now()
    csrf2_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)
    if csrf2_match:
        csrf2 = csrf2_match.group(1)
        r = s.post(r.url, data={
            "csrfmiddlewaretoken": csrf2,
            "token-otp_token": code,
            "login_view-current_step": "token",
        }, headers={"Referer": r.url}, timeout=15)

if "Invalid" in r.text or "Log in" in r.text:
    print("Error: Login or 2FA verification failed.")
    scratch_path = r"C:\Users\samde\.gemini\antigravity\brain\ab1ce20a-887d-4485-b352-10875b86216f\scratch\pa_login_failed.html"
    with open(scratch_path, "w", encoding="utf-8") as f:
        f.write(r.text)
    print(f"Saved failed login HTML to: {scratch_path}")
    sys.exit(1)

print("Login successful! Fetching webapps page...")
r = s.get(f"https://{PA_HOST}/user/{USERNAME}/webapps/", timeout=15)
log_url = re.search(r'href="(/user/[^"]+/files/var/log/[^"]+error\.log)"', r.text)
if log_url:
    err_url = f"https://{PA_HOST}{log_url.group(1)}"
    print(f"Found error log URL: {err_url}")
    r_err = s.get(err_url)
    print("--- TAIL OF ERROR LOG ---")
    lines = r_err.text.splitlines()[-50:]
    for l in lines:
        print(l)
else:
    print("Could not find error log link")

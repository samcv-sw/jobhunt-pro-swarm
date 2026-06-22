import requests, re, pyotp, sys
PA_HOST = "www.pythonanywhere.com"
USERNAME = "JHFGUF"
PASSWORD = "JKHgfk^%#FKF6538653YT"
TOTP_SECRET = "4RQLUKK6XN62I4OH3DTXMORWVABDRZS6"

s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0"})

print("Logging in to PythonAnywhere...")
r = s.get(f"https://{PA_HOST}/login/")
csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text).group(1)

r = s.post(f"https://{PA_HOST}/login/", data={
    "csrfmiddlewaretoken": csrf,
    "auth-username": USERNAME,
    "auth-password": PASSWORD,
    "login_view-current_step": "auth",
}, headers={"Referer": f"https://{PA_HOST}/login/"})

if "token" in r.text.lower() or "otp_token" in r.text:
    print("Submitting 2FA TOTP...")
    totp = pyotp.TOTP(TOTP_SECRET)
    code = totp.now()
    csrf2 = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text).group(1)
    r = s.post(r.url, data={
        "csrfmiddlewaretoken": csrf2,
        "token-otp_token": code,
        "login_view-current_step": "token",
    }, headers={"Referer": r.url})

print("Fetching webapps page...")
r = s.get(f"https://{PA_HOST}/user/{USERNAME}/webapps/")
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

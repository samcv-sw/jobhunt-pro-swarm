"""
PythonAnywhere Autonomous Auto-Extend & Renewal Script.
Uses PythonAnywhere API and TOTP 2FA authentication to extend webapp expiry (3 months)
and reload the webapp automatically, ensuring 100% zero manual work forever.
"""
import os
import re
import time
import hmac
import struct
import base64
import hashlib
import requests
from typing import Dict, Any, Optional

def generate_totp_token(secret_b32: str) -> str:
    """Generates standard 6-digit TOTP token using Python native standard library."""
    clean_secret = secret_b32.strip().replace(" ", "").upper()
    padding = '=' * ((8 - len(clean_secret) % 8) % 8)
    key = base64.b32decode(clean_secret + padding)
    counter = struct.pack(">Q", int(time.time()) // 30)
    mac = hmac.new(key, counter, hashlib.sha1).digest()
    offset = mac[-1] & 0x0f
    binary = struct.unpack(">I", mac[offset:offset+4])[0] & 0x7fffffff
    return str(binary % 1000000).zfill(6)

class PythonAnywhereAutoExtender:
    def __init__(
        self,
        username: str = "JHFGUF",
        domain: str = "jhfguf.pythonanywhere.com",
        password: str = "JKHgfk^%#FKF6538653YT",
        totp_secret: str = "4RQLUKK6XN62I4OH3DTXMORWVABDRZS6",
        api_token: Optional[str] = None
    ):
        self.username = username
        self.domain = domain
        self.password = password
        self.totp_secret = totp_secret
        self.api_token = api_token or os.getenv("PYTHONANYWHERE_API_TOKEN", "")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        })

    def run_auto_extension(self) -> Dict[str, Any]:
        """
        Logs into PythonAnywhere web console with TOTP 2FA, extends expiry date, and reloads webapp.
        """
        login_url = "https://www.pythonanywhere.com/login/"
        extend_url = f"https://www.pythonanywhere.com/user/{self.username}/webapps/{self.domain}/extend"
        reload_api_url = f"https://www.pythonanywhere.com/api/v0/user/{self.username}/webapps/{self.domain}/reload/"

        try:
            # Step 1: Get CSRF token from login page
            r_get = self.session.get(login_url, timeout=10)
            match = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', r_get.text)
            csrf_token = match.group(1) if match else ""

            # Step 2: Submit initial login form
            login_data = {
                "csrfmiddlewaretoken": csrf_token,
                "auth-username": self.username,
                "auth-password": self.password,
                "login_view-current_step": "auth"
            }
            r_login = self.session.post(login_url, data=login_data, headers={"Referer": login_url}, timeout=10)

            # Step 3: Handle TOTP 2FA if prompted
            if "token" in r_login.text or "2fa" in r_login.url.lower() or "authenticator" in r_login.text.lower():
                totp_code = generate_totp_token(self.totp_secret)
                match_2fa = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', r_login.text)
                csrf_2fa = match_2fa.group(1) if match_2fa else csrf_token

                totp_data = {
                    "csrfmiddlewaretoken": csrf_2fa,
                    "2fa-token": totp_code,
                    "login_view-current_step": "2fa"
                }
                r_2fa = self.session.post(login_url, data=totp_data, headers={"Referer": r_login.url}, timeout=10)

            # Step 4: Post webapp expiry extension request
            r_csrf_ext = self.session.get(f"https://www.pythonanywhere.com/user/{self.username}/webapps/", timeout=10)
            match_ext = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', r_csrf_ext.text)
            csrf_ext = match_ext.group(1) if match_ext else ""

            r_extend = self.session.post(
                extend_url,
                data={"csrfmiddlewaretoken": csrf_ext},
                headers={"Referer": f"https://www.pythonanywhere.com/user/{self.username}/webapps/"},
                timeout=10
            )

            # Step 5: Reload WebApp via API or session
            reload_status = "reloaded"
            if self.api_token:
                r_reload = requests.post(
                    reload_api_url,
                    headers={"Authorization": f"Token {self.api_token}"},
                    timeout=10
                )
                reload_status = f"api_status_{r_reload.status_code}"
            else:
                self.session.post(
                    f"https://www.pythonanywhere.com/user/{self.username}/webapps/{self.domain}/reload",
                    data={"csrfmiddlewaretoken": csrf_ext},
                    timeout=10
                )

            return {
                "username": self.username,
                "domain": self.domain,
                "status": "extended_and_reloaded",
                "extend_response_code": r_extend.status_code,
                "reload_status": reload_status,
                "extended_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as err:
            return {
                "username": self.username,
                "domain": self.domain,
                "status": "fallback_triggered",
                "error": str(err),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

if __name__ == "__main__":
    extender = PythonAnywhereAutoExtender()
    res = extender.run_auto_extension()
    print("PythonAnywhere Renewal Result:", res)

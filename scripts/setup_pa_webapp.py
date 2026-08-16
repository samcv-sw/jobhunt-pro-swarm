import re
import requests
import sys
sys.path.append('scripts')
import pythonanywhere_auto_extend as pa

def setup_webapp():
    ext = pa.PythonAnywhereAutoExtender()
    login_url = "https://www.pythonanywhere.com/login/"
    r_get = ext.session.get(login_url)
    m = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', r_get.text)
    csrf_token = m.group(1) if m else ""
    
    login_data = {
        "csrfmiddlewaretoken": csrf_token,
        "auth-username": ext.username,
        "auth-password": ext.password,
        "login_view-current_step": "auth"
    }
    r_login = ext.session.post(login_url, data=login_data, headers={"Referer": login_url})
    if "token" in r_login.text or "2fa" in r_login.url.lower():
        totp = pa.generate_totp_token(ext.totp_secret)
        m2 = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', r_login.text)
        csrf_2fa = m2.group(1) if m2 else csrf_token
        ext.session.post(login_url, data={"csrfmiddlewaretoken": csrf_2fa, "2fa-token": totp, "login_view-current_step": "2fa"}, headers={"Referer": r_login.url})

    print("[*] Logged in successfully.")

    # 1. Create API token
    r_acc = ext.session.get("https://www.pythonanywhere.com/user/JHFGUF/account/")
    m_csrf = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', r_acc.text)
    csrf_acc = m_csrf.group(1) if m_csrf else ""
    
    r_tok = ext.session.post(
        "https://www.pythonanywhere.com/user/JHFGUF/account/api_token",
        data={"csrfmiddlewaretoken": csrf_acc},
        headers={"Referer": "https://www.pythonanywhere.com/user/JHFGUF/account/"}
    )
    print(f"[*] API Token Creation POST status: {r_tok.status_code}")

    r_acc2 = ext.session.get("https://www.pythonanywhere.com/user/JHFGUF/account/")
    tokens = re.findall(r'[a-f0-9]{40}', r_acc2.text)
    print(f"[*] Found API Tokens: {tokens}")
    active_token = tokens[0] if tokens else ""

    if not active_token:
        # Check input value
        m_val = re.search(r'id="id_api_token"[^>]*value="([^"]+)"', r_acc2.text)
        if m_val:
            active_token = m_val.group(1)
            print(f"[✓] Active API Token from input: {active_token}")

    if active_token:
        headers = {"Authorization": f"Token {active_token}"}
        # 2. Check webapps via REST API
        r_webapps = requests.get(f"https://www.pythonanywhere.com/api/v0/user/JHFGUF/webapps/", headers=headers)
        print(f"[*] Webapps via API ({r_webapps.status_code}): {r_webapps.text}")

        # 3. Create WebApp if not exists
        if r_webapps.status_code == 200 and len(r_webapps.json()) == 0:
            print("[*] Creating WebApp jhfguf.pythonanywhere.com with Python 3.10...")
            payload = {
                "domain_name": "jhfguf.pythonanywhere.com",
                "python_version": "python310"
            }
            r_create = requests.post(f"https://www.pythonanywhere.com/api/v0/user/JHFGUF/webapps/", json=payload, headers=headers)
            print(f"[*] Create WebApp response ({r_create.status_code}): {r_create.text}")

            # Reload webapp
            r_reload = requests.post(f"https://www.pythonanywhere.com/api/v0/user/JHFGUF/webapps/jhfguf.pythonanywhere.com/reload/", headers=headers)
            print(f"[✓] Reload WebApp response ({r_reload.status_code}): {r_reload.text}")

if __name__ == "__main__":
    setup_webapp()

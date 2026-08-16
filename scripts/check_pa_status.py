import re
import requests
import pythonanywhere_auto_extend as pa

def check_pa():
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

    r_web = ext.session.get("https://www.pythonanywhere.com/user/JHFGUF/webapps/")
    print("Web Tab Status:", r_web.status_code)
    
    # Check if there is any webapp created or "Add a new web app"
    if "Add a new web app" in r_web.text:
        print("Note: 'Add a new web app' button is present.")
    
    domains = re.findall(r'id="id_([^"]+_pythonanywhere_com)"', r_web.text)
    print("Domains found:", domains)
    
    wsgi_files = set(re.findall(r'/var/www/[^\s"\'<]+', r_web.text))
    print("WSGI Files:", wsgi_files)

    # Check API Token page
    r_account = ext.session.get("https://www.pythonanywhere.com/user/JHFGUF/account/")
    print("Account page status:", r_account.status_code)
    api_token_match = re.search(r'id="id_api_token"[^>]*value="([^"]+)"', r_account.text)
    if api_token_match:
        print("API Token on Account page:", api_token_match.group(1))
    else:
        # Look for token text in account page
        tokens = re.findall(r'[a-f0-9]{40}', r_account.text)
        print("Potential API Tokens on Account page:", tokens)

if __name__ == "__main__":
    check_pa()

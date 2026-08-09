import requests
import re

def main():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    })
    
    print("1. Fetching login page...")
    r1 = s.get("https://www.pythonanywhere.com/login/")
    csrf1 = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', r1.text)
    token1 = csrf1.group(1) if csrf1 else ""
    print(f"CSRF 1: {token1[:10]}...")

    print("2. Submitting credentials...")
    payload = {
        "csrfmiddlewaretoken": token1,
        "auth-username": "JHFGUF",
        "auth-password": "JHGjhf5475%^",
        "login_view-current_step": "auth"
    }
    r2 = s.post("https://www.pythonanywhere.com/login/", data=payload, headers={"Referer": "https://www.pythonanywhere.com/login/"})
    print(f"Login Response: {r2.status_code}, Final URL: {r2.url}")
    
    if "2fa" in r2.url or "2fa" in r2.text.lower():
        print("Account requires 2FA or TOTP token!")
    
    print("3. Fetching webapps dashboard...")
    r3 = s.get("https://www.pythonanywhere.com/user/JHFGUF/webapps/")
    print(f"Webapps Page Status: {r3.status_code}")
    csrf2 = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', r3.text)
    token2 = csrf2.group(1) if csrf2 else token1

    print("4. Extending webapp expiration date...")
    r4 = s.post(
        "https://www.pythonanywhere.com/user/JHFGUF/webapps/jhfguf.pythonanywhere.com/extend",
        data={"csrfmiddlewaretoken": token2},
        headers={"Referer": "https://www.pythonanywhere.com/user/JHFGUF/webapps/"}
    )
    print(f"Extend Response: {r4.status_code}")

    print("5. Reloading webapp...")
    r5 = s.post(
        "https://www.pythonanywhere.com/user/JHFGUF/webapps/jhfguf.pythonanywhere.com/reload",
        data={"csrfmiddlewaretoken": token2},
        headers={"Referer": "https://www.pythonanywhere.com/user/JHFGUF/webapps/"}
    )
    print(f"Reload Response: {r5.status_code}")

if __name__ == "__main__":
    main()

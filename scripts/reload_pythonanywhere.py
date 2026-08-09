#!/usr/bin/env python3
import os
import sys
import requests

def reload_pa():
    token = os.getenv("PA_API_TOKEN", "")
    username = os.getenv("PYTHONANYWHERE_USERNAME", "JHFGUF")
    domain = "jhfguf.pythonanywhere.com"
    
    url = f"https://www.pythonanywhere.com/api/v0/user/{username}/webapps/{domain}/reload/"
    print(f"[*] Triggering PythonAnywhere reload via API: {url}...")
    
    if token:
        headers = {"Authorization": f"Token {token}"}
        try:
            resp = requests.post(url, headers=headers, timeout=15)
            if resp.status_code in (200, 201):
                print(f"[✓] PythonAnywhere Webapp reloaded successfully! (HTTP {resp.status_code})")
                return True
            else:
                print(f"[!] Reload response HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"[!] Error calling reload API: {e}")
    else:
        print("[!] PA_API_TOKEN not set in environment. Skipping remote API call.")
    
    wsgi_file = "/var/www/jhfguf_pythonanywhere_com_wsgi.py"
    if os.path.exists(wsgi_file):
        os.utime(wsgi_file, None)
        print(f"[✓] Touched {wsgi_file}")
        return True
    return False

if __name__ == "__main__":
    reload_pa()

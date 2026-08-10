import os
import sys
import hashlib
import requests

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

files_to_check = [
    "web/templates/upload_cv_v3.html",
    "web/templates/en/upload_cv_v3.html",
    "web/app_v2.py",
    "web/routers/jobs.py",
    "cloud_wsgi.py"
]

def get_md5(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()

def compare_hashes():
    print("=== COMPARING LOCAL VS REMOTE PYTHONANYWHERE FILE HASHES ===")
    all_match = True
    for rel_path in files_to_check:
        local_abs = os.path.join(PROJECT_ROOT, rel_path)
        if not os.path.exists(local_abs):
            print(f"[!] Local file missing: {rel_path}")
            continue
        with open(local_abs, "rb") as f:
            local_bytes = f.read()
        local_hash = get_md5(local_bytes)

        remote_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/jobhunt/{rel_path}"
        r = SESSION.get(remote_url)
        if r.status_code == 200:
            remote_hash = get_md5(r.content)
            match = (local_hash == remote_hash)
            symbol = "✓ MATCH" if match else "✗ MISMATCH"
            print(f"[{symbol}] {rel_path}")
            print(f"    Local  MD5: {local_hash}")
            print(f"    Remote MD5: {remote_hash}")
            if not match:
                all_match = False
        else:
            print(f"[✗ ERROR] {rel_path} -> HTTP {r.status_code}: {r.text}")
            all_match = False

    return all_match

if __name__ == "__main__":
    compare_hashes()

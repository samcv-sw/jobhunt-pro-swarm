import sys
import time
import requests

if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}

home_targets = [
    f"/home/{USERNAME}/deploy.zip",
    f"/home/{USERNAME}/jobhunt_deploy.zip",
    f"/home/{USERNAME}/jobhunt_saas_v2.db.gz",
    f"/home/{USERNAME}/tmp6nb06vep",
    f"/home/{USERNAME}/tmpbi44s3g8",
    f"/home/{USERNAME}/tmpc1v8fpon",
    f"/home/{USERNAME}/tmpds1yq0w_",
    f"/home/{USERNAME}/tmpigq69tx8",
    f"/home/{USERNAME}/tmpqejnxdi2",
    f"/home/{USERNAME}/tmpqqm26vuc",
    f"/home/{USERNAME}/tmpresszx81",
    f"/home/{USERNAME}/tmpvai5etws",
    f"/home/{USERNAME}/tmpvbimt4ws",
    f"/home/{USERNAME}/tmpve9d03dc",
    f"/home/{USERNAME}/tmpx4efeum3",
    f"/home/{USERNAME}/tmpzicz8t96",
    f"/home/{USERNAME}/_check_fpdf.py",
    f"/home/{USERNAME}/_check_pdf.py",
    f"/home/{USERNAME}/_check_pdf_tools.py",
    f"/home/{USERNAME}/_check_pdfminer2.py",
    f"/home/{USERNAME}/_check_pkgs.py",
    f"/home/{USERNAME}/_install_pdfminer.py",
]

print("=== Clearing Root Home Directory Zip & Temp Files on PythonAnywhere ===")
freed_count = 0

for path in home_targets:
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{path}"
    for attempt in range(3):
        try:
            r = requests.delete(url, headers=HEADERS, timeout=15)
            if r.status_code in (200, 204):
                print(f"[DELETED 204] {path}")
                freed_count += 1
                time.sleep(1.2)
                break
            elif r.status_code == 404:
                break
            elif r.status_code == 429:
                print(f"[429 Rate Limit] Waiting 4s...")
                time.sleep(4)
        except Exception as e:
            print(f"Exception deleting {path}: {e}")
            time.sleep(2)

print(f"\n[✓] Root disk cleanup complete: {freed_count} root bloat targets removed!")

# Reload WebApp
time.sleep(2)
r_reload = requests.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{USERNAME.lower()}.pythonanywhere.com/reload/", headers=HEADERS)
print(f"[✓] Webapp Reload Status: {r_reload.status_code}")

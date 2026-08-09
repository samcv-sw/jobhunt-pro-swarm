import os
import sys
import asyncio

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure root directory is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ["FORCE_SQLITE"] = "1"
os.environ["SKIP_INSTALL"] = "1"

print("====================================================================")
print(" [AUDIT] ROUTE & TEMPLATE AUDITOR FOR JOBHUNT PRO SAAS")
print("====================================================================")

try:
    from fastapi.testclient import TestClient
    from web.app_v2 import app
    print(" [OK] Successfully imported web.app_v2")
except Exception as e:
    print(f" [CRITICAL ERROR] Failed to import web.app_v2: {e}")
    sys.exit(1)

client = TestClient(app, raise_server_exceptions=False)

routes_to_test = []
for route in app.routes:
    if hasattr(route, "path") and hasattr(route, "methods"):
        if "GET" in route.methods:
            routes_to_test.append(route.path)

print(f" [+] Discovered {len(routes_to_test)} GET routes across app and routers.")

passed = 0
failed_500 = []
failed_other = []

cookies = {"session_token": "test_session_123"}

for path in sorted(set(routes_to_test)):
    if "{" in path or "ws" in path.lower():
        continue
    try:
        res = client.get(path, cookies=cookies, follow_redirects=False)
        if res.status_code == 500:
            print(f" [500 INTERNAL ERROR] {path}")
            failed_500.append((path, res.text[:200]))
        elif res.status_code in (200, 301, 302, 303, 307, 308, 401, 403, 404):
            passed += 1
            print(f" [{res.status_code}] {path}")
        else:
            failed_other.append((path, res.status_code, res.text[:100]))
            print(f" [{res.status_code}] {path}")
    except Exception as exc:
        print(f" [EXC] {path}: {exc}")
        failed_500.append((path, str(exc)))

print("====================================================================")
print(f" AUDIT COMPLETE: {passed} routes verified clean.")
if failed_500:
    print(f" {len(failed_500)} ROUTES RETURNED 500 ERROR:")
    for path, err in failed_500:
        print(f"   - {path}: {err[:100]}")
else:
    print(" 0 INTERNAL SERVER ERRORS FOUND ACROSS ALL GET ROUTES!")
print("====================================================================")

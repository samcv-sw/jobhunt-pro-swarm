import re
import sys
import time
import pyotp
import requests
import websocket
import ssl
import json
import random
import string
import traceback

PA_HOST = "www.pythonanywhere.com"
USERNAME = "JHFGUF"
pwd = "JHGjhf5475%^"
TOTP_SECRET = "4RQLUKK6XN62I4OH3DTXMORWVABDRZS6"

def try_login_with_offset(offset):
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    
    print(f"Attempting login with offset {offset} seconds...")
    r = s.get(f"https://{PA_HOST}/login/", timeout=15)
    csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)
    if not csrf:
         return None, "No CSRF token found on login page"
    csrf_token = csrf.group(1)

    r = s.post(f"https://{PA_HOST}/login/", data={
        "csrfmiddlewaretoken": csrf_token,
        "auth-username": USERNAME,
        "auth-password": pwd,
        "login_view-current_step": "auth",
    }, headers={"Referer": f"https://{PA_HOST}/login/"}, timeout=15)

    if "token" in r.text.lower() or "authenticator" in r.text.lower() or "otp_token" in r.text:
        totp = pyotp.TOTP(TOTP_SECRET)
        code = totp.at(time.time() + offset)
        print(f"Generated TOTP for offset {offset}: {code}")
        
        csrf2 = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)
        if csrf2:
            r = s.post(r.url, data={
                "csrfmiddlewaretoken": csrf2.group(1),
                "token-otp_token": code,
                "login_view-current_step": "token",
            }, headers={"Referer": r.url}, timeout=15)
        else:
            return None, "No CSRF token found on TOTP page"

    if "Log out" in r.text or f"/user/{USERNAME}/" in r.text or r.url == f"https://{PA_HOST}/user/{USERNAME}/":
        print(f"Login SUCCESSFUL with offset {offset}!")
        return s, None
    else:
        return None, "Login rejected"

# Try offsets sequentially
offsets = [0, 30, -30]
s = None
err = None
for offset in offsets:
    s, err = try_login_with_offset(offset)
    if s:
        break
    else:
        print(f"Failed with offset {offset}: {err}")
        time.sleep(1)

if not s:
    print("All login attempts failed. Exiting.")
    sys.exit(1)

try:
    # Retrieve consoles list
    print("Fetching consoles list...")
    headers = {
        "X-CSRFToken": s.cookies.get("csrftoken", ""),
        "Referer": f"https://{PA_HOST}/user/{USERNAME}/consoles/"
    }
    r_api = s.get(f"https://{PA_HOST}/api/v0/user/{USERNAME}/consoles/", headers=headers, timeout=15)
    print("Consoles response code:", r_api.status_code)
    if r_api.status_code != 200:
        print("Failed to fetch consoles list. Body:", r_api.text[:200])
        sys.exit(1)

    consoles = r_api.json()
    print("Available consoles:", consoles)

    bash_console = None
    for c in consoles:
        if c.get("executable") == "bash":
            bash_console = c
            break

    if not bash_console:
        print("No active bash console found. Creating one...")
        r_create = s.post(f"https://{PA_HOST}/api/v0/user/{USERNAME}/consoles/", json={
            "executable": "bash"
        }, headers=headers, timeout=15)
        if r_create.status_code == 201:
            bash_console = r_create.json()
            print("Created new console:", bash_console)
        else:
            print("Failed to create new console. Status code:", r_create.status_code)
            sys.exit(1)

    console_id = bash_console["id"]
    r_frame = s.get(f"https://{PA_HOST}/user/{USERNAME}/consoles/{console_id}/frame/", timeout=15)
    console_server = re.search(r'Anywhere\.LoadConsole\("([^"]+)"', r_frame.text).group(1)
    session_key = re.search(r'Anywhere\.LoadConsole\("[^"]+",\s*"([^"]+)"', r_frame.text).group(1)
    print(f"Console Server: {console_server}")
    print(f"Session Key: {session_key}")

    # Generate random SockJS server_id and session_id
    server_id = f"{random.randint(0, 999):03d}"
    session_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    ws_url = f"wss://{console_server}/sj/{server_id}/{session_id}/websocket"

    print(f"Connecting to SockJS WebSocket: {ws_url}")
    ws = websocket.create_connection(
        ws_url,
        sslopt={"cert_reqs": ssl.CERT_NONE},
        timeout=10
    )

    ws.recv() # SockJS open frame 'o'
    ws.send(json.dumps([f"\x1b[{session_key};{console_id};;a"]))
    ws.send(json.dumps(["\x1b[8;24;80t"]))

    # Read output helper
    def read_sockjs_output(ws_conn, timeout=3):
        start_time = time.time()
        output = ""
        ws_conn.settimeout(timeout)
        while True:
            try:
                msg = ws_conn.recv()
                if msg.startswith("a"):
                    data = json.loads(msg[1:])
                    for item in data:
                        output += item
                if time.time() - start_time > timeout:
                    break
            except Exception:
                break
        return output

    # Wait for bash to settle
    read_sockjs_output(ws, timeout=3)

    print("Hard resetting local changes on server to avoid conflicts...")
    ws.send(json.dumps(["cd ~/jobhunt && git reset --hard && git clean -fd\n"]))
    print(read_sockjs_output(ws, timeout=5).encode('ascii', errors='ignore').decode('ascii'))

    print("Sending command: 'git pull'")
    ws.send(json.dumps(["git pull\n"]))

    print("Reading git pull results (waiting up to 45 seconds)...")
    git_out = read_sockjs_output(ws, timeout=45)
    print("--- Git Pull Result ---")
    print(git_out.encode('ascii', errors='ignore').decode('ascii'))
    print("-----------------------")

    print("Running server env update script...")
    ws.send(json.dumps(["python3.12 scratch/update_server_env.py\n"]))
    print(read_sockjs_output(ws, timeout=10).encode('ascii', errors='ignore').decode('ascii'))

    print("Ensuring data/ directory exists on server...")
    ws.send(json.dumps(["mkdir -p ~/jobhunt/data\n"]))
    print(read_sockjs_output(ws, timeout=3).encode('ascii', errors='ignore').decode('ascii'))

    print("Restoring populated database to unified data/ directory...")
    ws.send(json.dumps(["cp -f ~/jobhunt/jobhunt_saas_v2.db ~/jobhunt/data/jobhunt_saas_v2.db\n"]))
    print(read_sockjs_output(ws, timeout=3).encode('ascii', errors='ignore').decode('ascii'))

    print("Running database tables initialization/seeder...")
    ws.send(json.dumps(["python3.12 scratch/init_pa_dbs.py\n"]))
    print(read_sockjs_output(ws, timeout=15).encode('ascii', errors='ignore').decode('ascii'))

    print("Reloading PythonAnywhere webapp via touching WSGI configuration...")
    ws.send(json.dumps(["touch /var/www/jhfguf_pythonanywhere_com_wsgi.py\n"]))
    print(read_sockjs_output(ws, timeout=5).encode('ascii', errors='ignore').decode('ascii'))

    print("Running DB inspection script on server...")
    ws.send(json.dumps(["python3.12 scratch/inspect_server_dbs.py\n"]))
    db_inspect = read_sockjs_output(ws, timeout=20)
    print("--- DB Inspection Result ---")
    print(db_inspect.encode('ascii', errors='ignore').decode('ascii'))
    print("----------------------------")

    ws.close()

except Exception as e:
    print("An exception occurred:")
    traceback.print_exc()
    sys.exit(1)

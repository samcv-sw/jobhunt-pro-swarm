import requests
import time

API_TOKEN = "3053350f0f1c52a2a96e16ed64bf5c855b95c35f"
USERNAME = "JHFGUF"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

print("1. Fetching and terminating old consoles...")
r_list = SESSION.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/")
if r_list.status_code == 200:
    for c in r_list.json():
        cid = c.get("id")
        r_del = SESSION.delete(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{cid}/")
        print(f"Terminated console #{cid}: {r_del.status_code}")

print("2. Spawning fresh bash console...")
r_new = SESSION.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/", json={"executable": "bash"})
print("Create Console Status:", r_new.status_code)

r_list2 = SESSION.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/")
console_id = r_list2.json()[0]["id"] if r_list2.status_code == 200 and r_list2.json() else None
print(f"Fresh Console ID: {console_id}")

print("3. Polling console status until 'running'...")
for attempt in range(15):
    r_info = SESSION.get(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/")
    if r_info.status_code == 200:
        c_status = r_info.json().get("status", "")
        print(f"Attempt {attempt+1}: Console status = '{c_status}'")
        if c_status.lower() in ("running", "active", "ready"):
            break
    time.sleep(2)

if console_id:
    print("4. Executing deep disk purge command...")
    clean_cmd = (
        "rm -rf /home/JHFGUF/.cache /home/JHFGUF/*.zip /home/JHFGUF/jobhunt/mobile /home/JHFGUF/jobhunt/frontend /home/JHFGUF/jobhunt/test_env /home/JHFGUF/jobhunt/dashboard /home/JHFGUF/jobhunt/chrome_extension /home/JHFGUF/jobhunt/extension\n"
    )
    r_in = SESSION.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{console_id}/send_input/", json={"input": clean_cmd})
    print(f"Send input status: {r_in.status_code}")
    time.sleep(8)

    # Test 1MB upload
    r_test = SESSION.post(f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/home/{USERNAME}/test_clean.txt", files={"content": b"A" * 1000000})
    print("Upload 1MB Test Status:", r_test.status_code, r_test.text)

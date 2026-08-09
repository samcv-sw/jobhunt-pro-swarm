import subprocess
import sys
import os
import time
import re

# 1. Clear any stale process on port 8000 to prevent [Errno 10048]
try:
    netstat_out = subprocess.check_output("netstat -ano", shell=True).decode("utf-8", errors="ignore")
    pids = set(re.findall(r"127\.0\.0\.1:8000\s+.*LISTENING\s+(\d+)", netstat_out))
    for pid in pids:
        if int(pid) != os.getpid():
            subprocess.call(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if pids:
        time.sleep(1.0)
except Exception:
    pass

env = os.environ.copy()
env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
env['FORCE_SQLITE'] = '1'
env['SKIP_INSTALL'] = '1'
env['PYTHONUNBUFFERED'] = '1'

log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'local_server.log')
log_f = open(log_path, 'a', buffering=1)
cmd = [sys.executable, '-m', 'uvicorn', 'web.app_v2:app', '--host', '127.0.0.1', '--port', '8000']
proc = subprocess.Popen(cmd, env=env, stdout=log_f, stderr=log_f)
print(f"Server process launched cleanly with PID {proc.pid}")

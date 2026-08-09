import subprocess
import sys
import os

env = os.environ.copy()
env['PYTHONPATH'] = r'c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi'
env['FORCE_SQLITE'] = '1'
env['SKIP_INSTALL'] = '1'
env['PYTHONUNBUFFERED'] = '1'
env['PYTHONIOENCODING'] = 'utf-8'
env['PYTHONUTF8'] = '1'


with open('local_server.log', 'w', encoding='utf-8') as log_file:
    pass

log_f = open('local_server.log', 'a', encoding='utf-8', errors='ignore', buffering=1)
py_exe = r'C:\Users\samde\AppData\Local\Programs\Python\Python312\python.exe'

cmd = [py_exe, '-m', 'uvicorn', 'web.app_v2:app', '--host', '127.0.0.1', '--port', '8000']

proc = subprocess.Popen(cmd, env=env, stdout=log_f, stderr=log_f)
print(f"Server launched in background with PID {proc.pid}")
proc.wait()

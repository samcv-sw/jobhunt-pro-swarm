import subprocess
import sys
import os

env = os.environ.copy()
env['PYTHONPATH'] = r'c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi'
env['FORCE_SQLITE'] = '1'

p = subprocess.Popen([sys.executable, 'run_local.py'], env=env)
print('Server started with PID:', p.pid)

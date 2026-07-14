import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

cwd = os.getcwd()
app_path = os.path.join(cwd, "web", "app_v2.py")

with open(app_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(1660 - 1, min(1705, len(lines))):
    print(f"{idx + 1}: {lines[idx].rstrip()}")

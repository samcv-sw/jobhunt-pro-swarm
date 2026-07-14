import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

cwd = os.getcwd()
main_path = os.path.join(cwd, "backend", "main.py")

with open(main_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(1, min(200, len(lines))):
    print(f"{idx}: {lines[idx - 1].rstrip()}")

import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

cwd = os.getcwd()
main_path = os.path.join(cwd, "backend", "main.py")

if os.path.exists(main_path):
    print("Searching for bot_instance in backend/main.py:")
    with open(main_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if "bot_instance" in line:
            print(f"  Line {i+1}: {line.strip()}")
else:
    print("backend/main.py does not exist")

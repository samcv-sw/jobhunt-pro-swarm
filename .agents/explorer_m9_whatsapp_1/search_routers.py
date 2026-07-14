import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

cwd = os.getcwd()
main_path = os.path.join(cwd, "backend", "main.py")

with open(main_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Searching app.include_router in backend/main.py:")
for i, line in enumerate(lines):
    if "include_router" in line:
        print(f"  Line {i+1}: {line.strip()}")

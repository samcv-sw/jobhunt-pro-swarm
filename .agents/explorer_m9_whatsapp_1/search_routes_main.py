import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

cwd = os.getcwd()
main_path = os.path.join(cwd, "backend", "main.py")

print("Searching route decorators in backend/main.py:")
with open(main_path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if "@app.get" in line or "@app.post" in line or "@app.put" in line or "@app.delete" in line:
            print(f"  Line {i+1}: {line.strip()}")

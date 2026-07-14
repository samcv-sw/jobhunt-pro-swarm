import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

cwd = os.getcwd()

print("Searching for pause/status logic in runner or worker:")
files_to_search = ["core/campaign_runner.py", "core/worker.py", "backend/tasks.py"]
for f_rel in files_to_search:
    path = os.path.join(cwd, f_rel)
    if os.path.exists(path):
        print(f"=== {f_rel} ===")
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if "status" in line.lower() or "pause" in line.lower() or "active" in line.lower() or "state" in line.lower():
                print(f"  Line {i+1}: {line.strip()[:100]}")

import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

cwd = os.getcwd()

def search_in_file(filename):
    path = os.path.join(cwd, filename)
    if not os.path.exists(path):
        print(f"{filename} does not exist")
        return
    
    print(f"=== Matches in {filename} ===")
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if "process_webhook_update" in line:
            start = max(0, i - 15)
            end = min(len(lines), i + 25)
            print(f"Lines {start+1}-{end}:")
            for j in range(start, end):
                print(f"  {j+1}: {lines[j].rstrip()}")
            print("-" * 40)

search_in_file("web/app_v2.py")
search_in_file("backend/main.py")

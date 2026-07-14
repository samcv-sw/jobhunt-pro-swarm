import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

cwd = os.getcwd()
tg_dir = os.path.join(cwd, "core", "telegram")

print("Searching telegram directory:")
for root, dirs, files in os.walk(tg_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "webhook" in content.lower() or "api/v1/webhook" in content:
                        rel_path = os.path.relpath(path, cwd)
                        print(f"Found in {rel_path}")
                        for i, line in enumerate(content.splitlines()):
                            if "webhook" in line.lower() or "api/v1/webhook" in line:
                                print(f"  Line {i+1}: {line.strip()[:100]}")
            except Exception as e:
                print(f"Error reading {file}: {e}")

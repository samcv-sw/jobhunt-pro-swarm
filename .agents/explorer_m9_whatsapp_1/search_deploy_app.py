import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

cwd = os.getcwd()

print("Searching for app_v2 references in configuration files:")
config_files = ["Procfile", "Dockerfile", "Dockerfile.cloud", "Dockerfile.frontend", "DEPLOY.md", "README.md", "start_cloud.py"]
for f_rel in config_files:
    path = os.path.join(cwd, f_rel)
    if os.path.exists(path):
        print(f"=== {f_rel} ===")
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if "app_v2" in line or "backend.main" in line:
                    print(f"  Line {i+1}: {line.strip()}")

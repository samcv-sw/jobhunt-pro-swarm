import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

cwd = os.getcwd()

# Let's search all .py files in the project for web framework imports
for root, dirs, files in os.walk(cwd):
    if "node_modules" in root or ".git" in root or ".agents" in root or "venv" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "flask" in content.lower() or "fastapi" in content.lower() or "route(" in content.lower():
                        rel_path = os.path.relpath(path, cwd)
                        print(f"Web application file: {rel_path}")
            except Exception as e:
                pass

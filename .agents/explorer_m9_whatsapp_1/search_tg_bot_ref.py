import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

cwd = os.getcwd()

print("Searching for telegram bot imports/references:")
for root, dirs, files in os.walk(cwd):
    if "node_modules" in root or ".git" in root or ".agents" in root or "venv" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "telegram_bot" in content.lower() or "core.telegram" in content.lower() or "import bot" in content:
                        rel_path = os.path.relpath(path, cwd)
                        print(f"Found in {rel_path}")
            except Exception as e:
                pass

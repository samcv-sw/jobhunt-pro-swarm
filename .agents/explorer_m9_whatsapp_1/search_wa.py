import os
import sys

# Configure stdout and stderr to use UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

cwd = os.getcwd()
print("CWD:", cwd)

search_dir = os.path.join(cwd, "core")
print("Search directory exists:", os.path.exists(search_dir))

for root, dirs, files in os.walk(search_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "whatsapp" in content.lower() or "zero_cost" in content.lower():
                        # Use relative path to avoid printing characters that might fail if print has issues, though reconfigure helps
                        rel_path = os.path.relpath(path, cwd)
                        print(f"Found in: {rel_path}")
                        for i, line in enumerate(content.splitlines()):
                            if "whatsapp" in line.lower() or "wa_me" in line.lower() or "zero_cost" in line.lower():
                                print(f"  Line {i+1}: {line.strip()[:100]}")
            except Exception as e:
                print(f"Error reading {file}: {e}")

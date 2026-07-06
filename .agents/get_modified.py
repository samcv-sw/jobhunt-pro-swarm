import os
import sys

# Reconfigure stdout to write utf-8
sys.stdout.reconfigure(encoding='utf-8')

root = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi"
exclude_dirs = {".git", ".agents", ".venv2", ".pytest_cache", "node_modules", "__pycache__", "test_env", "test_env_2"}

files_list = []
for dirpath, dirnames, filenames in os.walk(root):
    # filter exclude dirs in place
    dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
    for f in filenames:
        fp = os.path.join(dirpath, f)
        try:
            mtime = os.path.getmtime(fp)
            files_list.append((fp, mtime))
        except OSError:
            pass

files_list.sort(key=lambda x: x[1], reverse=True)

print("--- TOP 5 MODIFIED FILES ---")
for fp, mtime in files_list[:5]:
    print(f"FILE: {fp}")
    print("--- CONTENT (FIRST 30 LINES) ---")
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            for i in range(30):
                line = f.readline()
                if not line:
                    break
                print(line, end='')
    except Exception as e:
        print(f"Error reading file: {e}")
    print("\n--- END OF FILE CONTENT ---\n")

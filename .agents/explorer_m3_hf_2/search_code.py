import os
import re

root_dir = r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi"
exclude_dirs = {".git", "node_modules", ".agents", "venv", ".venv", "__pycache__", "archive"}
exclude_extensions = {".png", ".jpg", ".jpeg", ".pdf", ".zip", ".tar", ".gz", ".pyc"}

queries = [
    r"edge_cache",
    r"Redis",
    r"setup_cache",
    r"ats_scorer",
    r"ats_matcher",
    r"DATABASE_URL",
    r"postgresql"
]

patterns = [re.compile(q, re.IGNORECASE) for q in queries]

print("Starting scan...")
for dirpath, dirnames, filenames in os.walk(root_dir):
    # Prune directory search
    dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
    
    for filename in filenames:
        ext = os.path.splitext(filename)[1].lower()
        if ext in exclude_extensions:
            continue
        
        filepath = os.path.join(dirpath, filename)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    for q, pat in zip(queries, patterns):
                        if pat.search(line):
                            rel_path = os.path.relpath(filepath, root_dir)
                            print(f"{rel_path}:{line_num} ({q}) -> {line.strip()[:100]}")
        except Exception as e:
            pass

print("Scan complete.")

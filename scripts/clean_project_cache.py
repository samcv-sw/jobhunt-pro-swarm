#!/usr/bin/env python3
"""
JobHunt Pro - Cache and Stale Artifacts Cleaner
Safely purges project __pycache__, .pytest_cache, and lock files without touching .venv.
"""
import os
import sys
import shutil

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXCLUDE_DIRS = {".venv", ".venv2", "node_modules", ".git", ".idea", ".vscode"}


def clean_cache():
    removed_dirs = 0
    for root, dirs, _ in os.walk(ROOT_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for d in list(dirs):
            if d in ("__pycache__", ".pytest_cache", ".ruff_cache"):
                full_path = os.path.join(root, d)
                try:
                    shutil.rmtree(full_path, ignore_errors=True)
                    removed_dirs += 1
                except Exception:
                    pass

    # Clear temp lock files
    temp_dir = os.environ.get("TEMP", "")
    removed_locks = 0
    if temp_dir and os.path.exists(temp_dir):
        for f in os.listdir(temp_dir):
            if f.startswith("jobhunt_") and f.endswith(".lock"):
                try:
                    os.remove(os.path.join(temp_dir, f))
                    removed_locks += 1
                except Exception:
                    pass

    print("====================================================================")
    print(f" [OK] Successfully cleaned {removed_dirs} cache directorie(s) and {removed_locks} lock file(s).")
    print(f" [*] Project Root: {ROOT_DIR}")
    print("====================================================================")


if __name__ == "__main__":
    clean_cache()

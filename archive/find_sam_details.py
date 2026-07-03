import os

project_dir = r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi"
exclude_dirs = {".venv", ".venv2", ".git", "__pycache__", "node_modules"}

found = []
for root, dirs, files in os.walk(project_dir):
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if file.endswith((".py", ".js", ".html", ".sh", ".bat", ".env", ".json", ".toml", ".txt")):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if "admin-f31809ba" in content or "samsalameh" in content.lower() or "samatou683" in content.lower():
                        lines = content.splitlines()
                        matches = []
                        for i, line in enumerate(lines):
                            if "admin-f31809ba" in line or "samsalameh" in line.lower() or "samatou683" in line.lower():
                                matches.append((i+1, line.strip()))
                        found.append((os.path.relpath(path, project_dir), matches))
            except Exception:
                pass

print(f"Found Sam references in {len(found)} files:")
for rel_path, matches in found:
    print(f"\n[FILE] {rel_path} ({len(matches)} matches):")
    for line_num, text in matches[:10]:
        print(f"  Line {line_num}: {text[:100]}")

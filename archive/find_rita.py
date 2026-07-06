import os

project_dir = r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi"
exclude_dirs = {".venv", ".venv2", ".git", "__pycache__", "node_modules", ".wrangler"}

found = []
for root, dirs, files in os.walk(project_dir):
    # Skip excluded directories
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if file.endswith((".py", ".js", ".html", ".sh", ".bat", ".env", ".json", ".toml", ".txt")):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if "demo_user" in content.lower():
                        # Find line numbers
                        lines = content.splitlines()
                        matches = []
                        for i, line in enumerate(lines):
                            if "demo_user" in line.lower():
                                matches.append((i+1, line.strip()))
                        found.append((os.path.relpath(path, project_dir), matches))
            except Exception as e:
                pass

print(f"Found 'demo_user' in {len(found)} files:")
for rel_path, matches in found:
    print(f"\n[FILE] {rel_path} ({len(matches)} matches):")
    for line_num, text in matches[:10]: # show first 10 matches
        print(f"  Line {line_num}: {text[:100]}")
    if len(matches) > 10:
        print(f"  ... and {len(matches) - 10} more matches")


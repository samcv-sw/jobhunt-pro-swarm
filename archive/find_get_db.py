with open("web/app_v2.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "def get_db" in line or "get_conn" in line:
        print(f"web/app_v2.py L{i+1}: {line.strip()}")

print("\n" + "="*50 + "\n")

try:
    with open("core/database.py", "r", encoding="utf-8") as f:
        lines_db = f.readlines()
    for i, line in enumerate(lines_db):
        print(f"core/database.py L{i+1}: {line.strip()}")
except Exception as e:
    print("Error reading core/database.py:", e)

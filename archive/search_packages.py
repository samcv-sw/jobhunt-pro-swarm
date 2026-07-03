with open("web/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if "@app.get" in line or "@app.post" in line:
        if "wallet" in line or "pricing" in line or "register" in line:
            print(f"Line {idx}: {line.strip()}")

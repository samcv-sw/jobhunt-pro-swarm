import re

with open("web/app_v2.py", "r", encoding="utf-8") as f:
    content = f.read()

# Let's search for keywords in app_v2.py and output matches
keywords = ["wallet", "credit", "balance", "purchase", "buy", "deduct", "charge"]
for keyword in keywords:
    print(f"\n--- Searching for '{keyword}' ---")
    matches = []
    for line_no, line in enumerate(content.splitlines(), 1):
        if keyword in line.lower():
            if any(k in line for k in ["def ", "@app.", "conn.execute", "UPDATE", "INSERT"]):
                matches.append((line_no, line.strip()))
    for line_no, m in matches[:15]:
        print(f"Line {line_no}: {m}")

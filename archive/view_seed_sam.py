with open("seed_demo.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "admin-f31809ba" in line or "samsalameh.cv" in line or "target_titles" in line:
        print(f"seed_demo.py L{i+1}: {line.strip()}")

print("\n" + "="*50 + "\n")

with open("seed_pa_data.py", "r", encoding="utf-8") as f:
    lines_pa = f.readlines()

for i, line in enumerate(lines_pa):
    if "admin-f31809ba" in line or "samsalameh.cv" in line or "target_titles" in line:
        print(f"seed_pa_data.py L{i+1}: {line.strip()}")

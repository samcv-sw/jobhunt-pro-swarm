with open("core/multi_tenant.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "def get_tenant_stats" in line:
        print(f"get_tenant_stats starts at line {i+1}")
    elif "def list_tenants" in line:
        print(f"list_tenants starts at line {i+1}")

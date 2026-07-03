import json

with open("scan_report.json", "r", encoding="utf-8") as f:
    report = json.load(f)

for fn in ["dashboard-v4-rtl.css", "dashboard-v4.css"]:
    print(f"=== {fn} ===")
    print("Physical Instances:")
    for inst in report[fn]["physical_instances"]:
        print(f"  {inst['selector']} -> {inst['property']}: {inst['value']} (line {inst['line']})")
    print("RTL Selectors:")
    for inst in report[fn]["rtl_selectors"]:
        print(f"  {inst['selector']} -> {inst['declaration']} (line {inst['line']})")
    print()

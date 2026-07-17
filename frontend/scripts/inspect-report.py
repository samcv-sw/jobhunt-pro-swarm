import json
import os

def main():
    report_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'report-landing-page.json'))
    if not os.path.exists(report_path):
        print("Report not found at", report_path)
        return
        
    with open(report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    audit = data.get('audits', {}).get('unused-javascript', {})
    print("=== unused-javascript ===")
    print("Score:", audit.get('score'))
    print("Display Value:", audit.get('displayValue'))
    details = audit.get('details', {})
    items = details.get('items', [])
    print("Items count:", len(items))
    for item in items[:10]:
        print(json.dumps(item, indent=2))

if __name__ == '__main__':
    main()

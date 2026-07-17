import json

for page in ['landing-page', 'dashboard-page']:
    with open(f'frontend/scripts/report-{page}.json', encoding='utf-8') as f:
        d = json.load(f)
    audits = d.get('audits', {})
    cats = d.get('categories', {})
    print(f'=== {page} ===')
    for k, v in cats.items():
        score = round((v.get('score') or 0) * 100)
        print(f'  {k}: {score}')

    # Best practices - errors in console
    console_audit = audits.get('errors-in-console', {})
    items = console_audit.get('details', {}).get('items', [])
    print(f'  Console errors ({len(items)}):')
    for item in items:
        desc = item.get('description', '')[:120]
        print(f'    - {desc}')

    # Performance issues
    uj = audits.get('unused-javascript', {})
    print(f'  Unused JS: {uj.get("displayValue", "")}')
    rbi = audits.get('render-blocking-insight', {})
    print(f'  Render blocking: {rbi.get("displayValue", "")}')
    tbt = audits.get('total-blocking-time', {})
    print(f'  TBT: {tbt.get("displayValue", "")}')
    lcp = audits.get('largest-contentful-paint', {})
    print(f'  LCP: {lcp.get("displayValue", "")}')
    print()

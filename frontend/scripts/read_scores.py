import json

for page in ['landing-page', 'dashboard-page']:
    with open(f'frontend/scripts/report-{page}.json', encoding='utf-8') as f:
        d = json.load(f)
    cats = d.get('categories', {})
    print(f'=== {page} ===')
    for k, v in cats.items():
        score = round((v.get('score') or 0) * 100)
        print(f'  {k}: {score}')

    # Get top failing audits for performance
    if 'performance' in cats:
        audits = d.get('audits', {})
        perf_refs = cats['performance'].get('auditRefs', [])
        failing = []
        for ref in perf_refs:
            aid = ref.get('id')
            audit = audits.get(aid, {})
            s = audit.get('score')
            if s is not None and s < 1:
                failing.append((aid, round(s * 100), audit.get('displayValue', '')))
        failing.sort(key=lambda x: x[1])
        print(f'  --- Top failing performance audits ---')
        for aid, s, dv in failing[:10]:
            print(f'    {aid}: {s} ({dv})')
    print()

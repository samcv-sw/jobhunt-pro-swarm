import json
import sys

# Read both reports and extract key failing audits
for page in ['landing-page', 'dashboard-page']:
    with open(f'frontend/scripts/report-{page}.json', encoding='utf-8') as f:
        d = json.load(f)
    cats = d.get('categories', {})
    print(f'\n=== {page} SCORES ===')
    for k, v in cats.items():
        score = round((v.get('score') or 0) * 100)
        print(f'  {k}: {score}')

    # Best Practices audits
    print(f'\n  --- Best Practices failures ---')
    bp_cat = cats.get('best-practices', {})
    bp_refs = bp_cat.get('auditRefs', [])
    audits = d.get('audits', {})
    for ref in bp_refs:
        aid = ref.get('id')
        audit = audits.get(aid, {})
        s = audit.get('score')
        if s is not None and s < 1:
            title = audit.get('title', aid)
            desc = audit.get('description', '')[:100]
            print(f'    FAIL: {aid} - {title}')

    # Accessibility audits
    print(f'\n  --- Accessibility failures ---')
    acc_cat = cats.get('accessibility', {})
    acc_refs = acc_cat.get('auditRefs', [])
    for ref in acc_refs:
        aid = ref.get('id')
        audit = audits.get(aid, {})
        s = audit.get('score')
        if s is not None and s < 1:
            title = audit.get('title', aid)
            items = audit.get('details', {}).get('items', [])
            print(f'    FAIL: {aid} - {title} ({len(items)} items)')
            for item in items[:3]:
                node = item.get('node', {})
                snippet = node.get('snippet', '')[:120]
                print(f'      -> {snippet}')

import os, re, json

templates_dir = 'web/templates'
results = {}
physical_pattern = re.compile(r'margin-left|margin-right|padding-left|padding-right|text-align:\s*left|text-align:\s*right|border-left:|border-right:')
desc_pattern = re.compile(r'name=["\']description["\']')

for root, dirs, files in os.walk(templates_dir):
    for f in files:
        if not f.endswith('.html'):
            continue
        path = os.path.join(root, f)
        try:
            content = open(path, encoding='utf-8', errors='ignore').read()
            has_title = bool(re.search(r'<title', content))
            has_h1 = bool(re.search(r'<h1', content))
            has_desc = bool(desc_pattern.search(content))
            violations = physical_pattern.findall(content)
            rel_path = os.path.relpath(path, templates_dir)
            results[rel_path] = {
                'title': has_title,
                'h1': has_h1,
                'desc': has_desc,
                'css_violations': len(violations),
                'violation_types': list(set(violations)),
                'pass': has_title and has_h1 and len(violations) == 0
            }
        except Exception as e:
            results[f] = {'error': str(e)}

no_title = [k for k, v in results.items() if not v.get('title')]
no_h1 = [k for k, v in results.items() if not v.get('h1')]
no_desc = [k for k, v in results.items() if not v.get('desc')]
has_viol = [(k, v['violation_types']) for k, v in results.items() if v.get('css_violations', 0) > 0]
passing = [k for k, v in results.items() if v.get('pass')]

logger.debug(f'Total templates: {len(results)}')
logger.debug(f'PASSING (title+h1+no-css-violations): {len(passing)}')
logger.debug(f'\nMissing <title> ({len(no_title)}):')
for p in no_title:
    logger.debug(f'  - {p}')
logger.debug(f'\nMissing <h1> ({len(no_h1)}):')
for p in no_h1:
    logger.debug(f'  - {p}')
logger.debug(f'\nMissing meta description ({len(no_desc)}):')
for p in no_desc[:15]:
    logger.debug(f'  - {p}')
logger.debug(f'\nCSS Physical Property Violations ({len(has_viol)}):')
for name, types in has_viol:
    logger.debug(f'  - {name}: {types}')

summary = {
    'total': len(results),
    'passing': len(passing),
    'missing_title': no_title,
    'missing_h1': no_h1,
    'missing_desc': no_desc,
    'css_violations': [{'file': k, 'violations': v} for k, v in has_viol],
    'pages': results
}
with open('qa_report_round4.json', 'w', encoding='utf-8') as fp:
    json.dump(summary, fp, indent=2, ensure_ascii=False)
logger.debug('\nSaved qa_report_round4.json')

#!/usr/bin/env python3
"""Fix remaining templates: add cyberpunk.css link and proper body class."""
import os
import re

TEMPLATES = os.path.join(os.path.dirname(__file__), '..', 'templates')
CSS_LINK = '<link rel="stylesheet" href="/static/css/cyberpunk.css">'

# Templates that need cyberpunk wrapping
needy = [
    'api_docs.html', 'ats_scorer.html', 'battle_station.html',
    'checkout.html', 'checkout_v2.html', 'contact.html',
    'funnel_analytics.html', 'pricing_v2.html', 'referral.html',
    'sent_emails.html', 'services.html', 'services_new.html',
    'services_v2.html', 'stats.html', 'track_application.html',
    'wallet.html', 'war_room.html',
]

for fname in needy:
    path = os.path.join(TEMPLATES, fname)
    if not os.path.exists(path):
        print(f'[MISSING] {fname}')
        continue

    with open(path, encoding='utf-8', errors='ignore') as f:
        content = f.read()
    original = content

    if 'cyberpunk' in content:
        print(f'[ALREADY] {fname}')
        continue

    modified = False

    # === pricing_v2.html === Has DOCTYPE + <head> but no <body>
    if fname == 'pricing_v2.html':
        if '</head>' in content:
            content = content.replace('</head>', '</head>\n<body class="cyberpunk-body">')
            content += '\n</body>'
            modified = True

    # === Inline fragments (no DOCTYPE, no <head>) ===
    elif '<head>' not in content and '<!DOCTYPE' not in content:
        # These are inline page fragments - wrap with full structure
        content = ('<!DOCTYPE html>\n<html lang="en">\n<head>\n  '
                   + CSS_LINK + '\n</head>\n<body class="cyberpunk-body">\n'
                   + content + '\n</body>\n</html>\n')
        modified = True

    # === Has DOCTYPE + <head> but no <body> ===
    elif '<body' not in content and '<!DOCTYPE html>' in content:
        if '</head>' in content:
            content = content.replace('</head>', '</head>\n<body class="cyberpunk-body">')
            content += '\n</body>'
            modified = True

    # === Has <head> but no CSS link ===
    elif '<head>' in content and 'cyberpunk' not in content:
        content = content.replace('<head>', '<head>\n  ' + CSS_LINK)
        if '<body' in content and 'class="cyberpunk-body"' not in content:
            # Add class to existing body tag
            content = re.sub(
                r'(<body[^>]*?)(class\s*=\s*)(["\'])([^"\']*?)(["\'])',
                r'\1\2\3\4 cyberpunk-body\5', content, count=1
            )
            if 'class="cyberpunk-body"' not in content:
                content = re.sub(r'(<body)(\s*>)', r'\1 class="cyberpunk-body"\2', content, count=1)
        elif '<body' not in content:
            content = content.replace('</head>', '</head>\n<body class="cyberpunk-body">')
            content += '\n</body>'
        modified = True

    if modified:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'[FIXED] {fname}')
    else:
        print(f'[SKIP] {fname}')

print('\nDone!')

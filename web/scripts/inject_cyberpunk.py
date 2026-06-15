#!/usr/bin/env python3
"""
Cyberpunk CSS Injector for JobHunt Pro
Injects cyberpunk.css link and cyberpunk-body class into all HTML templates.
"""

import os
import glob
import re

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, 'templates')
CSS_PATH = '/static/css/cyberpunk.css'
CSS_FILENAME = 'cyberpunk.css'

CSS_LINK = f'<link rel="stylesheet" href="{CSS_PATH}">'

def process_template(filepath):
    """Inject cyberpunk CSS link and body class into a single HTML template."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    modified = False

    # Already has the CSS? Skip
    if CSS_FILENAME in content:
        return False, 'already has CSS'

    # 1. Inject the CSS link right after <head> (including <head with attributes)
    head_pattern = re.compile(r'(<head[^>]*>)', re.IGNORECASE)
    if head_pattern.search(content):
        content = head_pattern.sub(r'\1\n  ' + CSS_LINK, content)
        modified = True
    else:
        return False, 'no <head> tag'

    # 2. Add class="cyberpunk-body" to <body> tag
    body_pattern = re.compile(r'(<body[^>]*?)(class\s*=\s*["\'])([^"\']*?)(["\'])', re.IGNORECASE)
    body_no_class = re.compile(r'(<body)([^>]*?)(>)', re.IGNORECASE)

    if body_pattern.search(content):
        content = body_pattern.sub(
            r'\1\2\3 cyberpunk-body\4',
            content
        )
        modified = True
    elif body_no_class.search(content):
        content = body_no_class.sub(
            r'\1 class="cyberpunk-body"\2\3',
            content
        )
        modified = True
    else:
        return False, 'no <body> tag'

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return True, 'injected'


def main():
    if not os.path.isdir(TEMPLATES_DIR):
        print(f'ERROR: Templates directory not found: {TEMPLATES_DIR}')
        return

    html_files = glob.glob(os.path.join(TEMPLATES_DIR, '*.html'))
    html_files.sort()
    print(f'Found {len(html_files)} HTML template(s) in {TEMPLATES_DIR}')
    print('=' * 60)

    modified_count = 0
    skipped_count = 0

    for fp in html_files:
        basename = os.path.basename(fp)
        success, reason = process_template(fp)
        if success:
            print(f'  [MODIFIED] {basename} - {reason}')
            modified_count += 1
        else:
            print(f'  [SKIPPED]  {basename} - {reason}')
            skipped_count += 1

    print('=' * 60)
    print(f'SUMMARY: {modified_count} modified, {skipped_count} skipped, {len(html_files)} total')

    if modified_count == 0 and skipped_count == len(html_files):
        print('\nAll files already have cyberpunk.css or are missing <head>/<body> tags.')
        print('The CSS should already be active on all templates.')


if __name__ == '__main__':
    main()

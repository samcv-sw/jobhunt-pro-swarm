#!/usr/bin/env python3
"""
Fix Phase 2: Add missing closing tags (</head>, </body>, </html>)
and move misplaced <link>/<style> tags that appear after </head>.
"""
import os
import re

TEMPLATES_DIR = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"

SKIP = {
    '_public_nav.html', '_public_shell.html',
    '_sidebar.html', '_sidebar_head.html',
}


def fix_file(fpath, fname):
    with open(fpath, encoding='utf-8', errors='replace') as f:
        content = f.read()

    original = content
    changed = False

    # ─────────────────────────────────────────────────
    # 1. Fix missing </head> on pricing_v2.html etc.
    # ─────────────────────────────────────────────────
    if '</head>' not in content.lower():
        # Find </style> closest before <body>
        body_match = re.search(r'<body\b', content, re.IGNORECASE)
        style_end = None
        if body_match:
            before_body = content[:body_match.start()]
            for m in re.finditer(r'</style>', before_body, re.IGNORECASE):
                style_end = m
        if style_end:
            pos = style_end.end()
            content = content[:pos] + '\n</head>\n' + content[pos:]
        elif body_match:
            content = content[:body_match.start()] + '</head>\n' + content[body_match.start():]
        changed = True

    # ─────────────────────────────────────────────────
    # 2. Move <link stylesheet> / <style> that appear AFTER </head>
    #    Strategy: collect them, remove from after-</head> area,
    #    re-insert just before </head>
    # ─────────────────────────────────────────────────
    head_end_match = re.search(r'</head>', content, re.IGNORECASE)
    if head_end_match:
        head_end_pos = head_end_match.start()
        after_head = content[head_end_match.end():]

        # Find stray <link rel="stylesheet"> tags outside head
        stray_links = []
        def collect_link(m):
            stray_links.append(m.group(0))
            return ''
        # Only match link tags that load stylesheets (not icon/font etc already in head)
        after_head_new = re.sub(
            r'<link\s[^>]*rel=["\']stylesheet["\'][^>]*/?>',
            collect_link,
            after_head,
            flags=re.IGNORECASE
        )

        # Find stray <style>...</style> blocks that look like page-level CSS
        # (heuristic: if they contain class definitions, not just inline tweaks)
        stray_styles = []
        def collect_style(m):
            block = m.group(0)
            # Only move substantial style blocks (> 200 chars with CSS rules)
            if len(block) > 200 and '{' in block:
                stray_styles.append(block)
                return ''
            return block
        after_head_new = re.sub(
            r'<style[^>]*>.*?</style>',
            collect_style,
            after_head_new,
            flags=re.DOTALL | re.IGNORECASE
        )

        if stray_links or stray_styles:
            inserts = '\n'.join(stray_links + stray_styles)
            # Insert collected items just before </head>
            content = (
                content[:head_end_pos]
                + '\n' + inserts + '\n'
                + content[head_end_pos:]
                + after_head_new  # after_head_new replaces the tail
            )
            # Wait — reconstruct correctly
            # Actually rebuild: head content + </head> + cleaned after_head
            head_content = content[:head_end_pos]
            content = head_content + '\n' + inserts + '\n</head>\n' + after_head_new
            changed = True

    # ─────────────────────────────────────────────────
    # 3. Fix missing </body></html> at end
    # ─────────────────────────────────────────────────
    stripped = content.rstrip()
    needs_body_close = '</body>' not in content.lower()
    needs_html_close = '</html>' not in content.lower()

    if needs_body_close or needs_html_close:
        # Find last closing script/div tag
        end_tags = []
        if needs_body_close:
            end_tags.append('</body>')
        if needs_html_close:
            end_tags.append('</html>')
        content = stripped + '\n' + '\n'.join(end_tags) + '\n'
        changed = True

    if changed and content != original:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    fixed = 0
    for fname in sorted(os.listdir(TEMPLATES_DIR)):
        if not fname.endswith('.html') or fname in SKIP:
            continue
        fpath = os.path.join(TEMPLATES_DIR, fname)
        try:
            result = fix_file(fpath, fname)
            if result:
                print(f'FIXED: {fname}')
                fixed += 1
            else:
                print(f'OK:    {fname}')
        except Exception as e:
            print(f'ERROR: {fname} -> {e}')
    print(f'\nDone. Fixed {fixed} files.')


if __name__ == '__main__':
    main()

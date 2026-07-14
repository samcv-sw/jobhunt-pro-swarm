"""
Round 6 — Live Site Fix Script
Fixes issues found by auditing https://jhfguf.pythonanywhere.com/
"""
import os
import re

TEMPLATES_DIR = 'web/templates'
STATIC_CSS_DIR = 'web/static/css'

fixed_files = []
issues_found = []

# ──────────────────────────────────────────────
# 1. Fix physical CSS in ALL static CSS files
# ──────────────────────────────────────────────
CSS_REPLACEMENTS = [
    # Position physical -> logical
    (r'\bleft\s*:\s*50%', 'inset-inline-start: 0; inset-inline-end: 0; margin-inline: auto'),
    (r'\bright\s*:\s*0\b', 'inset-inline-end: 0'),
    (r'\bleft\s*:\s*0\b', 'inset-inline-start: 0'),
    (r'\bmargin-left\b', 'margin-inline-start'),
    (r'\bmargin-right\b', 'margin-inline-end'),
    (r'\bpadding-left\b', 'padding-inline-start'),
    (r'\bpadding-right\b', 'padding-inline-end'),
    (r'\bborder-left\b', 'border-inline-start'),
    (r'\bborder-right\b', 'border-inline-end'),
    (r'\btext-align\s*:\s*left\b', 'text-align: start'),
    (r'\btext-align\s*:\s*right\b', 'text-align: end'),
]

for css_file in os.listdir(STATIC_CSS_DIR):
    if not css_file.endswith('.css'):
        continue
    path = os.path.join(STATIC_CSS_DIR, css_file)
    try:
        content = open(path, encoding='utf-8', errors='ignore').read()
        original = content
        for pattern, replacement in CSS_REPLACEMENTS:
            content = re.sub(pattern, replacement, content)
        if content != original:
            open(path, 'w', encoding='utf-8').write(content)
            fixed_files.append(f'CSS: {css_file}')
            print(f'  Fixed CSS: {css_file}')
    except Exception as e:
        issues_found.append(f'CSS error {css_file}: {e}')

# ──────────────────────────────────────────────
# 2. Fix physical CSS in style blocks in ALL templates
# ──────────────────────────────────────────────
def fix_style_blocks(content):
    """Fix physical CSS only inside <style> blocks"""
    def fix_block(m):
        block = m.group(0)
        # Skip if this looks like a template comment
        for pat, rep in CSS_REPLACEMENTS:
            block = re.sub(pat, rep, block)
        return block
    return re.sub(r'<style[^>]*>.*?</style>', fix_block, content, flags=re.DOTALL | re.IGNORECASE)

# ──────────────────────────────────────────────
# 3. Fix inline style= attributes in ALL templates
# ──────────────────────────────────────────────
INLINE_REPLACEMENTS = [
    (r'\bmargin-left\b', 'margin-inline-start'),
    (r'\bmargin-right\b', 'margin-inline-end'),
    (r'\bpadding-left\b', 'padding-inline-start'),
    (r'\bpadding-right\b', 'padding-inline-end'),
    (r'\bborder-left\b', 'border-inline-start'),
    (r'\bborder-right\b', 'border-inline-end'),
    (r'\btext-align\s*:\s*left\b', 'text-align:start'),
    (r'\btext-align\s*:\s*right\b', 'text-align:end'),
]

def fix_inline_styles(content):
    """Fix physical CSS only inside style="" attributes"""
    def fix_attr(m):
        attr = m.group(0)
        for pat, rep in INLINE_REPLACEMENTS:
            attr = re.sub(pat, rep, attr)
        return attr
    return re.sub(r'style=["\'][^"\']*["\']', fix_attr, content)

# ──────────────────────────────────────────────
# 4. Add loading="lazy" to all <img> tags
# ──────────────────────────────────────────────
def add_lazy_loading(content):
    def add_lazy(m):
        tag = m.group(0)
        if 'loading=' not in tag:
            tag = tag.replace('<img ', '<img loading="lazy" ', 1)
        return tag
    return re.sub(r'<img\b[^>]*>', add_lazy, content, flags=re.IGNORECASE)

# ──────────────────────────────────────────────
# 5. Fix <html> lang/dir attributes
# ──────────────────────────────────────────────
def fix_html_lang_dir(content, filepath):
    is_en = os.sep + 'en' + os.sep in filepath or '/en/' in filepath
    if is_en:
        # English pages: lang="en" dir="ltr"
        content = re.sub(
            r'<html([^>]*?)>',
            lambda m: '<html' + re.sub(r'\s+(lang|dir)=["\'][^"\']*["\']', '', m.group(1)) + ' lang="en" dir="ltr">',
            content, count=1, flags=re.IGNORECASE
        )
    else:
        # Arabic pages: lang="ar" dir="rtl"
        if '<html' in content and 'lang=' not in content.split('</head>')[0]:
            content = re.sub(
                r'<html\b',
                '<html lang="ar" dir="rtl"',
                content, count=1, flags=re.IGNORECASE
            )
    return content

# Process all templates
total = 0
for root, dirs, files in os.walk(TEMPLATES_DIR):
    if 'backup' in root.lower():
        continue
    for filename in files:
        if not filename.endswith('.html'):
            continue
        filepath = os.path.join(root, filename)
        try:
            content = open(filepath, encoding='utf-8', errors='ignore').read()
            original = content

            content = fix_style_blocks(content)
            content = fix_inline_styles(content)
            content = add_lazy_loading(content)
            content = fix_html_lang_dir(content, filepath)

            if content != original:
                open(filepath, 'w', encoding='utf-8').write(content)
                rel = os.path.relpath(filepath, TEMPLATES_DIR)
                fixed_files.append(f'HTML: {rel}')
                total += 1

        except Exception as e:
            issues_found.append(f'HTML error {filename}: {e}')

print(f'\nDone! Fixed {total} HTML templates + {sum(1 for f in fixed_files if f.startswith("CSS"))} CSS files.')
if issues_found:
    print(f'Issues ({len(issues_found)}):')
    for i in issues_found:
        print(f'  {i}')
print('\nFixed files:')
for f in fixed_files[:20]:
    print(f'  {f}')
if len(fixed_files) > 20:
    print(f'  ... and {len(fixed_files)-20} more')

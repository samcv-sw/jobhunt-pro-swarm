import re
import os

file_path = "web/static/css/cyberpunk.css"

with open(file_path, "r", encoding="utf-8") as f:
    css = f.read()

# Safe logical property replacements for strict RTL (No width/height destruction)
css = re.sub(r'(?<!-)\bleft:', 'inset-inline-start:', css)
css = re.sub(r'(?<!-)\bright:', 'inset-inline-end:', css)
css = re.sub(r'(?<!-)\bmargin-left:', 'margin-inline-start:', css)
css = re.sub(r'(?<!-)\bmargin-right:', 'margin-inline-end:', css)
css = re.sub(r'(?<!-)\bpadding-left:', 'padding-inline-start:', css)
css = re.sub(r'(?<!-)\bpadding-right:', 'padding-inline-end:', css)
css = re.sub(r'(?<!-)\bborder-left:', 'border-inline-start:', css)
css = re.sub(r'(?<!-)\bborder-right:', 'border-inline-end:', css)

# Add Glassmorphism Noise & inner borders SAFELY without breaking
if 'backdrop-filter:blur(20px)' not in css:
    css = css.replace('backdrop-filter:blur(10px)', 'backdrop-filter:blur(20px) contrast(120%) brightness(110%)')
    css = css.replace('-webkit-backdrop-filter:blur(10px)', '-webkit-backdrop-filter:blur(20px) contrast(120%) brightness(110%)')

if 'box-shadow:inset' not in css:
    css = css.replace('.card, .cyber-card{', '.card, .cyber-card{box-shadow:inset 0 1px 0 rgba(255,255,255,0.1), 0 4px 20px rgba(0, 0, 0, 0.4) !important; ')

# Directional Transform Utility
if '--text-x-direction' not in css:
    css += "\n.dir-icon { transform: scaleX(var(--text-x-direction, 1)); }\n"
    css += "[dir='rtl'] { --text-x-direction: -1; }\n"
    css += "[dir='ltr'] { --text-x-direction: 1; }\n"

with open(file_path, "w", encoding="utf-8") as f:
    f.write(css)

import glob
html_files = glob.glob('web/templates/**/*.html', recursive=True)
count = 0
for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Safe HTML inline style logical replacement
    content = re.sub(r'(style="[^"]*?)\bmargin-left:\s*([^;"]+)', r'\1margin-inline-start: \2', content)
    content = re.sub(r'(style="[^"]*?)\bmargin-right:\s*([^;"]+)', r'\1margin-inline-end: \2', content)
    content = re.sub(r'(style="[^"]*?)\bpadding-left:\s*([^;"]+)', r'\1padding-inline-start: \2', content)
    content = re.sub(r'(style="[^"]*?)\bpadding-right:\s*([^;"]+)', r'\1padding-inline-end: \2', content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        count += 1

logger.debug(f"CSS Refactored. HTML templates refactored: {count}")

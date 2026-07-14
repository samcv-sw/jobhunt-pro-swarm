import glob
import os
import re

template_dir = 'web/templates'
html_files = glob.glob(os.path.join(template_dir, '**', '*.html'), recursive=True)

count = 0
for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # 1. Replace inline physical properties in style="..."
    # width -> inline-size
    content = re.sub(r'(style="[^"]*?)\bwidth:\s*([^;"]+)', r'\1inline-size: \2', content)
    # height -> block-size
    content = re.sub(r'(style="[^"]*?)\bheight:\s*([^;"]+)', r'\1block-size: \2', content)
    # margin-left -> margin-inline-start
    content = re.sub(r'(style="[^"]*?)\bmargin-left:\s*([^;"]+)', r'\1margin-inline-start: \2', content)
    # margin-right -> margin-inline-end
    content = re.sub(r'(style="[^"]*?)\bmargin-right:\s*([^;"]+)', r'\1margin-inline-end: \2', content)
    # padding-left -> padding-inline-start
    content = re.sub(r'(style="[^"]*?)\bpadding-left:\s*([^;"]+)', r'\1padding-inline-start: \2', content)
    # padding-right -> padding-inline-end
    content = re.sub(r'(style="[^"]*?)\bpadding-right:\s*([^;"]+)', r'\1padding-inline-end: \2', content)

    # 2. Inject dir="auto" into inputs and textareas that don't have it
    content = re.sub(r'<input([^>]+)(?<!dir="auto")(?<!dir=\'auto\')>', lambda m: '<input' + m.group(1) + ' dir="auto">' if 'type="hidden"' not in m.group(1) and 'type="submit"' not in m.group(1) and 'dir=' not in m.group(1) else m.group(0), content)
    content = re.sub(r'<textarea([^>]+)(?<!dir="auto")(?<!dir=\'auto\')>', lambda m: '<textarea' + m.group(1) + ' dir="auto">' if 'dir=' not in m.group(1) else m.group(0), content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        count += 1

logger.debug(f"Refactored {count} HTML templates.")

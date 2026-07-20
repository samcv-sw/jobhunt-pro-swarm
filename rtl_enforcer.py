import os
import re

css_replacements = [
    (r'border-top-left-radius:', r'border-start-start-radius:'),
    (r'border-top-right-radius:', r'border-start-end-radius:'),
    (r'border-bottom-left-radius:', r'border-end-start-radius:'),
    (r'border-bottom-right-radius:', r'border-end-end-radius:'),
    (r'border-left-width:', r'border-inline-start-width:'),
    (r'border-right-width:', r'border-inline-end-width:'),
    (r'border-left-color:', r'border-inline-start-color:'),
    (r'border-right-color:', r'border-inline-end-color:'),
    (r'border-left:', r'border-inline-start:'),
    (r'border-right:', r'border-inline-end:'),
    (r'margin-left:', r'margin-inline-start:'),
    (r'margin-right:', r'margin-inline-end:'),
    (r'padding-left:', r'padding-inline-start:'),
    (r'padding-right:', r'padding-inline-end:'),
    (r'float:\s*left', r'float: inline-start'),
    (r'float:\s*right', r'float: inline-end'),
    (r'text-align:\s*left', r'text-align: start'),
    (r'text-align:\s*right', r'text-align: end'),
    (r'(?<![-\w])left:', r'inset-inline-start:'),
    (r'(?<![-\w])right:', r'inset-inline-end:'),
]

html_replacements = [
    # Tailwind classes
    (r'\bml-', r'ms-'),
    (r'\bmr-', r'me-'),
    (r'\bpl-', r'ps-'),
    (r'\bpr-', r'pe-'),
    (r'\btext-left\b', r'text-start'),
    (r'\btext-right\b', r'text-end'),
    (r'\bfloat-left\b', r'float-start'),
    (r'\bfloat-right\b', r'float-end'),
    (r'\bleft-0\b', r'start-0'),
    (r'\bright-0\b', r'end-0'),
    (r'\bborder-l\b', r'border-s'),
    (r'\bborder-r\b', r'border-e'),
]

dirs_to_process = [
    r'web\templates',
    r'web\static\css',
    r'frontend\src',
    r'frontend\app',
    r'frontend\components',
]

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return False

    orig_content = content

    if filepath.endswith('.css'):
        for pattern, repl in css_replacements:
            content = re.sub(pattern, repl, content, flags=re.IGNORECASE)
        # Update fonts
        content = re.sub(r'--font-sans:[^;]+;', r"--font-sans: 'Cairo', 'Tajawal', 'Inter', sans-serif;", content)
        content = re.sub(r"font-family:\s*['\"]Inter['\"][^;]*;", r"font-family: 'Cairo', 'Tajawal', 'Inter', sans-serif;", content)

    elif filepath.endswith(('.html', '.tsx', '.jsx', '.js')):
        for pattern, repl in html_replacements:
            content = re.sub(pattern, repl, content)
        # add dir="auto" to inputs
        content = re.sub(r'(<input[^>]*)(?<!dir="auto")(?<!dir=\'auto\')>', r'\1 dir="auto">', content)
        content = re.sub(r'(<textarea[^>]*)(?<!dir="auto")(?<!dir=\'auto\')>', r'\1 dir="auto">', content)

    if content != orig_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

modified = 0
for d in dirs_to_process:
    if not os.path.exists(d):
        continue
    for root, _, files in os.walk(d):
        for file in files:
            if file.endswith(('.css', '.html', '.tsx', '.jsx', '.js')):
                if process_file(os.path.join(root, file)):
                    modified += 1

print(f"Modified {modified} files for RTL/Logical properties and Arabic fonts.")

# Inject global Arabic typography if possible
style_path = r'web\static\css\style.css'
if os.path.exists(style_path):
    with open(style_path, 'a', encoding='utf-8') as f:
        f.write("\n\n/* Global Arabic Typography */\nbody, html, input, textarea, select {\n  font-family: 'Cairo', 'Tajawal', sans-serif;\n  line-height: 1.8;\n}\n")

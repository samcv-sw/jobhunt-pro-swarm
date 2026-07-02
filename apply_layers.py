import os
import re

base_dir = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"

files = [
    (os.path.join(base_dir, "_public_shell.html"), "/static/css/cyberpunk-rtl.css?v=20260629_v2"),
    (os.path.join(base_dir, "en", "_public_shell.html"), "/static/css/cyberpunk.css"),
    (os.path.join(base_dir, "_base_tailwind.html"), "/static/css/dashboard-v4.css?v=20260629_v2"),
    (os.path.join(base_dir, "en", "_base_tailwind.html"), "/static/css/dashboard-v4.css?v=20260629_v2"),
]

for filepath, legacy_css in files:
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # We want to replace the two <link> tags with the @import layer syntax.
    # Pattern to match the <link> tags.
    pattern1 = f'<link rel="stylesheet" href="{legacy_css}">'
    pattern2 = '<link rel="stylesheet" href="/static/css/premium-ui.css">'
    
    if pattern1 in content and pattern2 in content:
        replacement = f'''<style>
        @layer legacy, premium;
        @import url("{legacy_css}") layer(legacy);
        @import url("/static/css/premium-ui.css") layer(premium);
    </style>'''
        # Replace the first pattern with the replacement block
        content = content.replace(pattern1, replacement)
        # Remove the second pattern
        content = content.replace(pattern2, "")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Applied layers in {filepath}")
    else:
        print(f"Patterns not found in {filepath}. Maybe already applied?")

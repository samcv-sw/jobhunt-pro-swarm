import os
import re

def restore_cyberpunk(filepath, is_en, is_dashboard):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Determine which css to restore
    if is_dashboard:
        css = 'dashboard-v4.css?v=20260629_v2'
    else:
        css = 'cyberpunk.css' if is_en else 'cyberpunk-rtl.css?v=20260629_v2'

    # Check if already present
    if css in content:
        logger.debug(f"Skipping {filepath}, already contains {css}")
        return

    # Replace premium-ui.css with BOTH
    # If it's a shell, it has <link rel="stylesheet" href="/static/css/premium-ui.css">
    pattern = r'<link rel="stylesheet" href="/static/css/premium-ui.css">'
    replacement = f'<link rel="stylesheet" href="/static/css/{css}">\n    <link rel="stylesheet" href="/static/css/premium-ui.css">'
    
    if pattern in content:
        content = content.replace(pattern, replacement)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.debug(f"Restored {css} in {filepath}")
    else:
        logger.debug(f"Pattern not found in {filepath}")

base_dir = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"

restore_cyberpunk(os.path.join(base_dir, "en", "_public_shell.html"), True, False)
restore_cyberpunk(os.path.join(base_dir, "_base_tailwind.html"), False, True)
restore_cyberpunk(os.path.join(base_dir, "en", "_base_tailwind.html"), True, True)

logger.debug("Restoration complete.")

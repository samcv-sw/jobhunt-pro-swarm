import os
import re

ar_dir = r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\ar"
files_to_check = ["_base_tailwind.html", "_public_shell.html", "_dashboard_shell.html", "base.html", "index_v2.html", "index_v3.html", "index_v4.html", "login.html", "login_v2.html"]

for f in files_to_check:
    filepath = os.path.join(ar_dir, f)
    if os.path.exists(filepath):
        with open(filepath, encoding="utf-8") as file:
            content = file.read()

        new_content = re.sub(r'(/static/css/[a-zA-Z0-9_-]+)\.css', r'\1-rtl.css', content)

        if new_content != content:
            with open(filepath, "w", encoding="utf-8") as file:
                file.write(new_content)
            logger.debug(f"Updated {f}")

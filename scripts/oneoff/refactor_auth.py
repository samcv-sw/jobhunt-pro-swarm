import os
import re

def refactor_auth(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add glass-input class to text, email, tel, password inputs
    content = re.sub(
        r'<input dir="auto" type="(text|email|tel|password)"',
        r'<input class="glass-input" dir="auto" type="\1"',
        content
    )
    
    # Also update btn-submit to btn-solid for premium feel
    content = re.sub(
        r'class="btn-submit"',
        r'class="btn-solid"',
        content
    )
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

base_dir = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"
for name in ["register_v2.html", "en/register_v2.html"]:
    refactor_auth(os.path.join(base_dir, name))

logger.debug("Auth forms refactored!")

import re

files = [
    r"web\templates\index_v4.html",
    r"web\templates\en\index_v4.html",
    r"web\templates\_public_footer.html"
]

import os
for file in files:
    if not os.path.exists(file):
        continue
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    # remove the broken links
    content = re.sub(r'<a href="/press"[^>]*>.*?</a>', '', content)
    content = re.sub(r'<a href="/partners"[^>]*>.*?</a>', '', content)
    content = re.sub(r'<a href="/gdpr"[^>]*>.*?</a>', '', content)

    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
print("Removed broken links.")

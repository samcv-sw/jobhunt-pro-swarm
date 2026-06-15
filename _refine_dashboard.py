"""Deep check: remove _sidebar_head include, ensure complete sidebar CSS"""
import re

path = r'C:\Users\samde\Desktop\cv sam new ma3 kimi\web\templates\dashboard_v2.html'

with open(path, 'rb') as f:
    raw = f.read()
text = raw.decode('utf-8', errors='replace')

# Remove {% include "_sidebar_head.html" %} - causes CSS conflicts
text = text.replace('{% include "_sidebar_head.html" %}\n', '')
text = text.replace('{% include "_sidebar_head.html" %}', '')

# Fix encoding issues (the title had a weird char)
text = text.replace('Dashboard \u0092 JobHunt Pro', 'Dashboard — JobHunt Pro')
text = text.replace('Dashboard \u2014 JobHunt Pro', 'Dashboard — JobHunt Pro')

# Check sidebar CSS completeness - add missing responsive sidebar styles
sidebar_additional = """
/* Dashboard sidebar fixes */
@media(max-width:768px){
  .sidebar{display:none !important;}
  .main-wrap{margin-left:0 !important;padding:16px !important;max-width:100% !important;}
}
"""

# Insert after the sidebar CSS block but before the original styles
# Find the split between sidebar CSS and original CSS
sidebar_end = text.find('.main-wrap{margin-left:220px;flex:1;padding:32px 40px;max-width:calc(100vw - 220px);}')
if sidebar_end >= 0:
    css_end = text.find('}\n', sidebar_end) + 2
    # Also find the @media and add after it
    media_pos = text.find('@media', sidebar_end)
    if media_pos >= 0:
        media_end = text.find('}\n', media_pos)
        text = text[:media_end+2] + sidebar_additional + text[media_end+2:]
    else:
        text = text[:css_end] + sidebar_additional + text[css_end:]

# Verify
with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print(f'FINAL SIZE: {len(text)} chars')

# Check critical pieces
checks = {
    'Has sidebar div': '<div class="sidebar">' in text,
    'Has main-wrap': '<div class="main-wrap">' in text, 
    'Has cyberpunk.css': 'cyberpunk.css' in text,
    'Has body !important': '!important' in text[:text.find('<style>')+5000],
    'Has include removed': '{% include "_sidebar_head.html" %}' not in text,
    'Has DOCTYPE': '<!DOCTYPE html>' in text,
    'Has <body>': '<body>' in text,
    'Has </body>': '</body>' in text,
    'Has mobile responsive': '@media(max-width:768px)' in text,
}
for k, v in checks.items():
    print(f'  {k}: {"✅" if v else "❌"}')

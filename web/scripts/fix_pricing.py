# Fix pricing_v2.html - add cyberpunk body class
import os
path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates', 'pricing_v2.html')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
if 'cyberpunk' not in content:
    content = content.replace('</head>', '</head>\n<body class="cyberpunk-body">')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed pricing_v2.html!')
else:
    print('Already has cyberpunk')

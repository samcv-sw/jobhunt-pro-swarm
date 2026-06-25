# Fix pricing_v2.html
import re

import os
path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates', 'pricing_v2.html')
with open(path, 'rb') as f:
    raw = f.read()

print('Total bytes:', len(raw))
print('First 200 bytes:')
print(repr(raw[:200]))
print()

# Check for head content
head_idx = raw.find(b'<head>')
print(f'<head> at index: {head_idx}')

# Find what's after the head opening tag
if head_idx >= 0:
    after_head = raw[head_idx+6:head_idx+100]
    print(f'Content after <head>: {repr(after_head[:80])}')
    
    # Look for a {% include %} followed by style - there's no close head
    # The page uses {% include '_sidebar_head.html' %} which probably contains the style
    # and there's no </head> closing tag explicitly.
    # Let's inject the cyberpunk CSS after <head>
    inject = b'\n  <link rel="stylesheet" href="/static/css/cyberpunk.css">'
    new_raw = raw[:head_idx+6] + inject + raw[head_idx+6:]
    
    # Also add body tag before </body>
    body_idx = new_raw.find(b'</body>')
    print(f'</body> at index: {body_idx}')
    
    with open(path, 'wb') as f:
        f.write(new_raw)
    print('Fixed!')
    
    # Verify
    with open(path, 'rb') as f:
        content = f.read()
    if b'cyberpunk' in content:
        print('cyberpunk.css link injected successfully!')
    else:
        print('SOMETHING WENT WRONG')

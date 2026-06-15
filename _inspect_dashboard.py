"""Inspect dashboard_v2.html structure."""
with open(r'C:\Users\samde\Desktop\cv sam new ma3 kimi\web\templates\dashboard_v2.html', 'rb') as f:
    text = f.read().decode('utf-8', errors='replace')

print('LAST 300 CHARS:')
print(repr(text[-300:]))

print()
for tag in ['<body', '</body>', '<html', '</html>', '<div class=', '<!DOCTYPE', '<nav']:
    if tag in text:
        idx = text.find(tag)
        line_num = text[:idx].count('\n') + 1
        context = repr(text[idx:idx+100])
        print(f'"{tag}" (line ~{line_num}): {context}')
    else:
        print(f'"{tag}": NOT FOUND')

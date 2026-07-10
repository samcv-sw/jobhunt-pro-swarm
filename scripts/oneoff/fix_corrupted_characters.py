"""
Fixes corrupted UTF-8 encodings in HTML templates.
"""
import os

files = [
    'web/templates/pricing_v3.html',
    'web/templates/en/pricing_v3.html'
]

replacements = [
    ('âš¡', '⚡'),
    ('â˜…', '★'),
    ('â€”', '—'),
    ('âœ•', '✖'),
    ('ðŸ”', '🔥'),
    ('âœ”', '✔'),
    ('â€™', "'")
]

fixed_count = 0

for f in files:
    if not os.path.exists(f):
        continue
    try:
        # First read with ignore/errors to handle mixed encodings
        with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
            content = fp.read()
        
        original = content
        for bad, good in replacements:
            content = content.replace(bad, good)
            
        if content != original:
            with open(f, 'w', encoding='utf-8') as fp:
                fp.write(content)
            fixed_count += 1
            print(f"Fixed encoding issues in: {f}")
    except Exception as e:
        print(f"Error fixing {f}: {e}")

print(f"\nSuccessfully cleaned {fixed_count} template files.")

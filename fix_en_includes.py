"""
Fixes template inclusion bugs where English pages load Arabic nav and footer.
Scans all templates in web/templates/en/ and ensures they load en/ versions of nav/footer.
"""
import os

EN_TEMPLATES_DIR = 'web/templates/en'

fixed_count = 0

for root, dirs, files in os.walk(EN_TEMPLATES_DIR):
    for filename in files:
        if not filename.endswith('.html'):
            continue
        filepath = os.path.join(root, filename)
        try:
            content = open(filepath, encoding='utf-8', errors='ignore').read()
            original = content
            
            # Replace includes
            content = content.replace("include '_public_nav.html'", "include 'en/_public_nav.html'")
            content = content.replace('include "_public_nav.html"', 'include "en/_public_nav.html"')
            content = content.replace("include '_public_footer.html'", "include 'en/_public_footer.html'")
            content = content.replace('include "_public_footer.html"', 'include "en/_public_footer.html"')
            
            if content != original:
                open(filepath, 'w', encoding='utf-8').write(content)
                fixed_count += 1
                print(f"Fixed includes in: {os.path.relpath(filepath, EN_TEMPLATES_DIR)}")
        except Exception as e:
            print(f"Error {filename}: {e}")

print(f"\nSuccessfully fixed includes in {fixed_count} English templates.")

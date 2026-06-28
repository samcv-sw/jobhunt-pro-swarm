#!/usr/bin/env python3
"""
Fix the order of closing HTML tags: ensures </body> comes before </html> at the end of templates.
"""
import os
import re

TEMPLATES_DIR = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"

def main():
    fixed_count = 0
    skipped_count = 0

    for fname in sorted(os.listdir(TEMPLATES_DIR)):
        if not fname.endswith('.html'):
            continue
        
        fpath = os.path.join(TEMPLATES_DIR, fname)
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Check if </html> appears before </body>
        if re.search(r'</html>.*</body>', content, re.DOTALL | re.IGNORECASE):
            # Strip trailing whitespace
            stripped = content.rstrip()
            
            # Remove trailing </html> and </body> tags
            while True:
                prev_len = len(stripped)
                stripped = re.sub(r'</html\s*>\s*$', '', stripped, flags=re.IGNORECASE)
                stripped = re.sub(r'</body\s*>\s*$', '', stripped, flags=re.IGNORECASE)
                stripped = stripped.rstrip()
                if len(stripped) == prev_len:
                    break
            
            # Re-append in correct order
            fixed_content = stripped + '\n</body>\n</html>\n'
            
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print(f'  [FIXED] {fname}')
            fixed_count += 1
        else:
            skipped_count += 1

    print(f'\nDone! Fixed {fixed_count} files, skipped {skipped_count}.')

if __name__ == '__main__':
    main()

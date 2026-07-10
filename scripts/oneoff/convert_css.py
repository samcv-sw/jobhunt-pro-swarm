import os
import re

TEMPLATE_DIR = "web/templates"

def convert_logical_properties():
    replacements = {
        r'\bml-': 'ms-',
        r'\bmr-': 'me-',
        r'\bpl-': 'ps-',
        r'\bpr-': 'pe-',
        r'\btext-left\b': 'text-start',
        r'\btext-right\b': 'text-end',
        r'\bfloat-left\b': 'float-start',
        r'\bfloat-right\b': 'float-end',
        r'\bborder-l\b': 'border-s',
        r'\bborder-l-': 'border-s-',
        r'\bborder-r\b': 'border-e',
        r'\bborder-r-': 'border-e-',
    }
    
    changed_files = 0
    for root, dirs, files in os.walk(TEMPLATE_DIR):
        for file in files:
            if file.endswith(".html"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                original_content = content
                for old_regex, new_val in replacements.items():
                    content = re.sub(old_regex, new_val, content)
                
                if content != original_content:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(content)
                    logger.debug(f"Updated {path}")
                    changed_files += 1

    logger.debug(f"Done. Updated {changed_files} files.")

if __name__ == "__main__":
    convert_logical_properties()

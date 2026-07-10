import os
import re

TEMPLATES_DIR = "web/templates"

def replace_logical_css(content):
    # Border
    content = re.sub(r'border-left(?!-color|-width|-style)', r'border-inline-start', content)
    content = re.sub(r'border-right(?!-color|-width|-style)', r'border-inline-end', content)
    # Margin & Padding
    content = re.sub(r'margin-left\b', r'margin-inline-start', content)
    content = re.sub(r'margin-right\b', r'margin-inline-end', content)
    content = re.sub(r'padding-left\b', r'padding-inline-start', content)
    content = re.sub(r'padding-right\b', r'padding-inline-end', content)
    # Absolute/Fixed positioning
    content = re.sub(r'(?<!-)\bleft:\s*', r'inset-inline-start: ', content)
    content = re.sub(r'(?<!-)\bright:\s*', r'inset-inline-end: ', content)
    # Text Align
    content = re.sub(r'text-align:\s*left\b', r'text-align: start', content)
    content = re.sub(r'text-align:\s*right\b', r'text-align: end', content)
    # Float
    content = re.sub(r'float:\s*left\b', r'float: inline-start', content)
    content = re.sub(r'float:\s*right\b', r'float: inline-end', content)
    return content

count = 0
for root, dirs, files in os.walk(TEMPLATES_DIR):
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            new_content = replace_logical_css(content)
            
            # Ensure Cairo font is added if outfit/sans-serif is used directly (skip for now since _base_tailwind handles it, but just in case)
            if 'font-family:' in new_content and 'Cairo' not in new_content:
                new_content = re.sub(r'font-family:\s*([^;]+);', r"font-family: 'Cairo', \1;", new_content)
                
            if new_content != content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                count += 1
                print(f"Fixed CSS in: {file}")

print(f"Total files updated: {count}")

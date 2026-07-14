import os
import re

css_dir = r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\static\css"

def convert_to_rtl(css_content):
    replacements = [
        (r'border-top-left-radius:', r'border-start-start-radius:'),
        (r'border-top-right-radius:', r'border-start-end-radius:'),
        (r'border-bottom-left-radius:', r'border-end-start-radius:'),
        (r'border-bottom-right-radius:', r'border-end-end-radius:'),
        (r'border-left-width:', r'border-inline-start-width:'),
        (r'border-right-width:', r'border-inline-end-width:'),
        (r'border-left-color:', r'border-inline-start-color:'),
        (r'border-right-color:', r'border-inline-end-color:'),
        (r'border-left:', r'border-inline-start:'),
        (r'border-right:', r'border-inline-end:'),
        (r'margin-left:', r'margin-inline-start:'),
        (r'margin-right:', r'margin-inline-end:'),
        (r'padding-left:', r'padding-inline-start:'),
        (r'padding-right:', r'padding-inline-end:'),
        (r'float:\s*left', r'float: inline-start'),
        (r'float:\s*right', r'float: inline-end'),
        (r'text-align:\s*left', r'text-align: start'),
        (r'text-align:\s*right', r'text-align: end'),
        (r'(?<![-\w])left:', r'inset-inline-start:'),
        (r'(?<![-\w])right:', r'inset-inline-end:'),
    ]
    for pattern, repl in replacements:
        css_content = re.sub(pattern, repl, css_content, flags=re.IGNORECASE)
    return css_content

for filename in os.listdir(css_dir):
    if filename.endswith(".css") and not filename.endswith("-rtl.css"):
        filepath = os.path.join(css_dir, filename)
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        rtl_content = convert_to_rtl(content)
        rtl_filename = filename.replace(".css", "-rtl.css")
        with open(os.path.join(css_dir, rtl_filename), "w", encoding="utf-8") as f:
            f.write(rtl_content)
        print(f"Generated {rtl_filename}")

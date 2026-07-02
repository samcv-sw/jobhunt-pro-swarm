import re

filepath = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\static\css\cyberpunk.css"

with open(filepath, "r", encoding="utf-8") as f:
    css = f.read()

# Safe replacements for RTL logical properties
replacements = [
    (r"\bmargin-left\b", "margin-inline-start"),
    (r"\bmargin-right\b", "margin-inline-end"),
    (r"\bpadding-left\b", "padding-inline-start"),
    (r"\bpadding-right\b", "padding-inline-end"),
    (r"\bborder-left\b", "border-inline-start"),
    (r"\bborder-right\b", "border-inline-end"),
    (r"\bborder-left-color\b", "border-inline-start-color"),
    (r"\bborder-right-color\b", "border-inline-end-color"),
    (r"\bborder-top\b", "border-block-start"),
    (r"\bborder-bottom\b", "border-block-end"),
    (r"(?<!-)left\s*:\s*", "inset-inline-start: "),
    (r"(?<!-)right\s*:\s*", "inset-inline-end: "),
    (r"(?<!-)top\s*:\s*", "inset-block-start: "),
    (r"(?<!-)bottom\s*:\s*", "inset-block-end: "),
    # Optional width/height to logical sizes
    # (r"(?<!-)width\s*:\s*", "inline-size: "),
    # (r"(?<!-)height\s*:\s*", "block-size: "),
]

for pattern, repl in replacements:
    css = re.sub(pattern, repl, css)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(css)

print("Refactored cyberpunk.css for CSS Logical Properties!")

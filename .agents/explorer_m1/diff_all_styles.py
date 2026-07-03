import difflib
import sys
import os

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

css_dir = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\static\css"
pairs = [
    ("auth-v2.css", "auth-v2-rtl.css"),
    ("cyberpunk.css", "cyberpunk-rtl.css"),
    ("dashboard-v4.css", "dashboard-v4-rtl.css"),
    ("landing-v4.css", "landing-v4-rtl.css"),
    ("style.css", "style-rtl.css"),
]

def clean_css_tokens(content):
    # Split minified css by ';' and '{'/'}' to make diffing line-by-line readable
    import re
    # Simple formatting: insert newline after '{', '}', and ';'
    formatted = re.sub(r'([;{}])', r'\1\n', content)
    return [line.strip() for line in formatted.splitlines() if line.strip()]

out = []
for ltr, rtl in pairs:
    ltr_path = os.path.join(css_dir, ltr)
    rtl_path = os.path.join(css_dir, rtl)
    
    with open(ltr_path, 'r', encoding='utf-8') as f1, open(rtl_path, 'r', encoding='utf-8') as f2:
        c1 = clean_css_tokens(f1.read())
        c2 = clean_css_tokens(f2.read())
        
    diff = list(difflib.unified_diff(c1, c2, fromfile=ltr, tofile=rtl, n=0))
    
    out.append(f"### Diff for `{ltr}` vs `{rtl}`\n")
    if not diff:
        out.append("No differences found (files are identical).\n")
    else:
        out.append("```diff")
        for line in diff:
            # Skip header lines of diff
            if line.startswith("---") or line.startswith("+++"):
                continue
            out.append(line)
        out.append("```\n")

with open(r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m1\diffs_report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("Diffs report generated successfully!")

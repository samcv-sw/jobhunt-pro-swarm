import os
import glob
import re

template_dir = r"c:\Users\samde\Desktop\cv sam new ma3 kimi\web\templates"
html_files = glob.glob(os.path.join(template_dir, "*.html"))

issues = {}

for filepath in html_files:
    filename = os.path.basename(filepath)
    if filename.startswith("_"):
        continue # skip partials
        
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    file_issues = []
    
    # Check if it's a full HTML page (has <html>)
    if "<html" in content:
        if "cyberpunk-body" not in content:
            file_issues.append("Missing 'cyberpunk-body' class on body tag")
        if "cyberpunk.css" not in content:
            file_issues.append("Missing link to 'cyberpunk.css'")
            
    # Check for hardcoded bright colors
    if re.search(r'background(?:-color)?\s*:\s*(?:#fff|#ffffff|white)\b', content, re.IGNORECASE):
        file_issues.append("Contains hardcoded white background")
        
    if re.search(r'color\s*:\s*(?:#000|#000000|black)\b', content, re.IGNORECASE):
        # some buttons have color: #000 (like btn-cyan-filled), so we need to be careful.
        pass
        
    # Check for unstyled buttons
    # simple heuristic: <button type="submit"> without class="btn"
    if re.search(r'<button[^>]*>[^<]*</button>', content):
        buttons = re.findall(r'<button([^>]*)>', content)
        for b in buttons:
            if 'class=' not in b and 'btn' not in b:
                file_issues.append("Contains unstyled button (missing 'btn' class)")
                break

    # Check for tables without styles
    if "<table" in content and "class=" not in content.split("<table")[1].split(">")[0]:
        file_issues.append("Contains unstyled table")

    if file_issues:
        issues[filename] = file_issues

print(f"Scanned {len(html_files)} files. Found UI consistency issues in {len(issues)} files:")
for filename, file_issues in issues.items():
    print(f"\n--- {filename} ---")
    for iss in file_issues:
        print(f" - {iss}")

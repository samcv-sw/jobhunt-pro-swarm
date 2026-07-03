import os
import re

TEMPLATES_DIR = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"

def analyze():
    files = sorted(os.listdir(TEMPLATES_DIR))
    html_files = [f for f in files if f.endswith('.html')]
    
    print(f"Analyzing {len(html_files)} templates...")
    
    for fname in html_files:
        fpath = os.path.join(TEMPLATES_DIR, fname)
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # 1. Check for empty links
        empty_links = re.findall(r'href=["\'](?:#|\s*)["\']', content)
        # 2. Check for localhost links
        localhost_links = re.findall(r'localhost:\d+', content)
        # 3. Check for hardcoded absolute paths that could be broken
        # 4. Check for broken Jinja tags (e.g. missing spaces or mismatched)
        unclosed_jinja = re.findall(r'\{%[^%]*$|\{\{[^}]*$', content)
        
        # 5. Check for double headers/body tags
        double_body = len(re.findall(r'<body\b', content, re.I)) > 1
        double_html = len(re.findall(r'<html\b', content, re.I)) > 1
        double_head = len(re.findall(r'<head\b', content, re.I)) > 1
        
        # 6. Check for scripts or style blocks that might be duplicated or empty
        # 7. Check if page has navigation or back buttons
        
        issues = []
        if empty_links:
            issues.append(f"{len(empty_links)} empty hrefs (href='#')")
        if localhost_links:
            issues.append(f"{len(localhost_links)} localhost links: {localhost_links}")
        if unclosed_jinja:
            issues.append("Unclosed Jinja tags")
        if double_body:
            issues.append("Multiple <body> tags")
        if double_html:
            issues.append("Multiple <html> tags")
        if double_head:
            issues.append("Multiple <head> tags")
            
        # Check if navbar or sidebar links are broken
        # Check for missing CSRF token in forms
        forms = re.findall(r'<form[^>]*>', content, re.I)
        for form in forms:
            if 'method="post"' in form.lower() or "method='post'" in form.lower():
                # check if form has csrf token
                # In Starlette/FastAPI it might use some token or maybe not
                pass
                
        if issues:
            print(f"\n[{fname}]")
            for issue in issues:
                print(f"  - {issue}")

if __name__ == "__main__":
    analyze()

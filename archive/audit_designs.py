import os
import re

TEMPLATES_DIR = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"

def audit():
    files = sorted(os.listdir(TEMPLATES_DIR))
    html_files = [f for f in files if f.endswith('.html') and not f.startswith('_')]
    
    print(f"{'Template Name':<30} | {'CSS Linked':<35} | {'Body Class':<20} | {'Has Nav/Sidebar':<15}")
    print("-" * 110)
    for fname in html_files:
        fpath = os.path.join(TEMPLATES_DIR, fname)
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        css_links = re.findall(r'<link\s+[^>]*href=["\']([^"\']+\.css(?:\?[^"\']*)?)["\']', content)
        body_class_match = re.search(r'<body\s+class=["\']([^"\']+)["\']', content, re.I)
        body_class = body_class_match.group(1) if body_class_match else "none"
        
        has_nav = "_public_nav.html" in content
        has_sidebar = "_sidebar.html" in content or "_sidebar_head.html" in content
        nav_status = "Nav" if has_nav else ("Sidebar" if has_sidebar else "None")
        
        css_str = ", ".join([os.path.basename(c) for c in css_links]) if css_links else "None"
        print(f"{fname:<30} | {css_str:<35} | {body_class:<20} | {nav_status:<15}")

if __name__ == "__main__":
    audit()

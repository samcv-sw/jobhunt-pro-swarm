import os
import re

TEMPLATES_DIR = r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"

def auto_fix_templates():
    print("==================================================")
    print("  JOBHUNT PRO — AUTOMATED DESIGN REPAIR ENGINE    ")
    print("==================================================")
    
    files = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".html")]
    fixes_applied = 0
    
    for filename in files:
        filepath = os.path.join(TEMPLATES_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        modified = False
        
        # 1. Fix mobile viewport tag in standalone pages
        if "<!DOCTYPE html>" in content or "<html" in content:
            if "<head>" in content and 'name="viewport"' not in content:
                print(f"[{filename}] Fix: Injected viewport meta tag")
                content = content.replace("<head>", '<head>\n    <meta name="viewport" content="width=device-width,initial-scale=1">')
                modified = True
                
            # 2. Fix missing title tag in standalone pages
            if "<head>" in content and "<title>" not in content:
                print(f"[{filename}] Fix: Injected title tag")
                content = content.replace("<head>", "<head>\n    <title>{{ title | default('JobHunt Pro') }}</title>")
                modified = True
                
        # 3. Fix nav offset on standalone pages that include the nav
        # If the page includes _public_nav.html and has a main content section, ensure it has padding-top
        if "_public_nav.html" in content and "padding-top" not in content and "padding:90px" not in content:
            # Let's find the first div or section after the nav include and inject padding-top: 100px
            pattern = re.compile(r'({%\s*include\s*["\']_public_nav\.html["\']\s*%})')
            match = pattern.search(content)
            if match:
                # Let's inspect what comes next
                post_nav = content[match.end():]
                # Look for the next opening div or section
                tag_match = re.search(r'<(div|section|main)([^>]*)>', post_nav)
                if tag_match:
                    tag_type = tag_match.group(1)
                    attrs = tag_match.group(2)
                    
                    # If it already has style, append to it, otherwise add style
                    if 'style=' in attrs:
                        new_attrs = re.sub(r'style=["\']([^"\']*)["\']', r'style="padding-top:100px;\1"', attrs)
                    else:
                        new_attrs = attrs + ' style="padding-top:100px;"'
                        
                    old_tag = f"<{tag_type}{attrs}>"
                    new_tag = f"<{tag_type}{new_attrs}>"
                    
                    print(f"[{filename}] Fix: Added 100px top padding offset for sticky nav")
                    content = content[:match.end()] + post_nav.replace(old_tag, new_tag, 1)
                    modified = True
                    
        # 4. Check for hardcoded plain-text footer and replace with unified footer include
        if "© 2026 JobHunt Pro" in content and "_public_footer.html" not in content:
            # Let's find the footer element and replace it
            pattern = re.compile(r'<footer[^>]*>.*?</footer>', re.DOTALL)
            if pattern.search(content):
                print(f"[{filename}] Fix: Replaced custom footer with unified _public_footer.html include")
                content = pattern.sub('{% include "_public_footer.html" %}', content)
                modified = True
                
        if modified:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            fixes_applied += 1
            
    print(f"\nRepair complete. Modified {fixes_applied} templates.")
    print("==================================================")

if __name__ == "__main__":
    auto_fix_templates()

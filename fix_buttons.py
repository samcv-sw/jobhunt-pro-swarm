"""
Round 7 — Complete Button & Form Fixer
Scans all templates for broken buttons (href='#') and forms without action
"""
import os, re

TEMPLATES_DIR = 'web/templates'

# Map of page-specific anchor fixes
HREF_FIXES = {
    '#pricing': '/pricing',
    '#register': '/register',
    '#login': '/login',
    '#dashboard': '/dashboard',
    '#contact': '/contact',
    '#plans': '/pricing',
    '#start': '/register',
    '#features': '/#features',
    '#how-it-works': '/#how-it-works',
}

issues = []
fixed_buttons = 0
fixed_forms = 0

def fix_empty_hrefs(content, filename):
    """Fix href='#' standalone anchors that should go somewhere"""
    global fixed_buttons
    
    # Find all <a> tags with href="#" only (not #section)
    def fix_anchor(m):
        global fixed_buttons
        tag = m.group(0)
        text = re.search(r'>([^<]+)<', tag)
        text_val = text.group(1).strip() if text else ''
        
        # Route based on button text
        new_href = None
        if any(w in text_val for w in ['مجاناً', 'Free', 'ابدأ', 'Start', 'register', 'تسجيل', 'انضم']):
            new_href = '/register'
        elif any(w in text_val for w in ['سعر', 'Price', 'باقة', 'Plan', 'اشتراك']):
            new_href = '/pricing'
        elif any(w in text_val for w in ['تواصل', 'Contact', 'اتصل']):
            new_href = '/contact'
        elif any(w in text_val for w in ['تسجيل دخول', 'Login', 'دخول', 'Sign in']):
            new_href = '/login'
        elif any(w in text_val for w in ['dashboard', 'لوحة', 'تحكم']):
            new_href = '/dashboard'
            
        if new_href:
            fixed_tag = tag.replace('href="#"', f'href="{new_href}"')
            fixed_buttons += 1
            return fixed_tag
        return tag
    
    # Only fix pure href="#" not href="#section"
    content = re.sub(r'<a\s[^>]*href=["\']#["\'][^>]*>[^<]*</a>', fix_anchor, content)
    return content

def fix_known_hrefs(content):
    """Fix known incorrect href patterns"""
    global fixed_buttons
    for old, new in HREF_FIXES.items():
        pattern = f'href="{old}"'
        if pattern in content:
            content = content.replace(pattern, f'href="{new}"')
            fixed_buttons += 1
    return content

def audit_forms(content, filepath):
    """Report forms without action"""
    forms = re.findall(r'<form[^>]*>', content, re.IGNORECASE)
    for form in forms:
        if 'action=' not in form and 'hx-post=' not in form and 'hx-put=' not in form:
            issues.append(f'Form missing action in {os.path.basename(filepath)}: {form[:100]}')

total_files = 0
for root, dirs, files in os.walk(TEMPLATES_DIR):
    if 'backup' in root.lower():
        continue
    for filename in files:
        if not filename.endswith('.html'):
            continue
        filepath = os.path.join(root, filename)
        try:
            content = open(filepath, encoding='utf-8', errors='ignore').read()
            original = content
            
            content = fix_empty_hrefs(content, filename)
            content = fix_known_hrefs(content)
            audit_forms(content, filepath)
            
            if content != original:
                open(filepath, 'w', encoding='utf-8').write(content)
                total_files += 1
        except Exception as e:
            issues.append(f'Error {filename}: {e}')

print(f'Fixed {fixed_buttons} button hrefs across {total_files} files')
print(f'Issues found: {len(issues)}')
for i in issues[:15]:
    print(f'  {i}')

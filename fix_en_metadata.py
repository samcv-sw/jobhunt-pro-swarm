"""
Fixes localized metadata bugs in English templates where Arabic tags were hardcoded.
"""
import os

files_to_fix = {
    'web/templates/en/login.html': [
        ('content="تسجيل الدخول | JobHunt Pro"', 'content="Login | JobHunt Pro"'),
    ],
    'web/templates/en/login_v2.html': [
        ('content="تسجيل الدخول | JobHunt Pro"', 'content="Login | JobHunt Pro"'),
    ],
    'web/templates/en/register.html': [
        ('content="إنشاء حساب | JobHunt Pro"', 'content="Register | JobHunt Pro"'),
    ],
    'web/templates/en/register_v2.html': [
        ('content="إنشاء حساب | JobHunt Pro"', 'content="Register | JobHunt Pro"'),
    ]
}

fixed = 0
for filepath, replacements in files_to_fix.items():
    if not os.path.exists(filepath):
        continue
    try:
        content = open(filepath, encoding='utf-8', errors='ignore').read()
        original = content
        for old, new in replacements:
            content = content.replace(old, new)
        if content != original:
            open(filepath, 'w', encoding='utf-8').write(content)
            fixed += 1
            print(f"Fixed metadata in {filepath}")
    except Exception as e:
        print(f"Error {filepath}: {e}")

print(f"\nMetadata fixed in {fixed} files.")

#!/usr/bin/env python3
"""
Auto-fix script: Add missing DOCTYPE/html/head/body structure to HTML templates.
Handles two cases:
  1. Files starting with <!-- comment (no html structure at all)
  2. Files starting with <link rel="stylesheet" directly
"""
import os
import re

TEMPLATES_DIR = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"

# Partial templates that should NOT have their own html/head (included by other templates)
SKIP_FILES = {
    '_public_nav.html',
    '_public_shell.html',
    '_sidebar.html',
    '_sidebar_head.html',
}

# Already fixed files (have proper DOCTYPE)
ALREADY_FIXED = {
    'login.html',
    'register_v2.html',
    'dashboard_v3.html',
    'forgot_password.html',
    'reset_password.html',
    'base.html',
}

# Page metadata: (title, description, robots, body_class)
PAGE_META = {
    'ats_scorer.html':        ('ATS Scorer — JobHunt Pro', 'Check your CV ATS compatibility score with AI', 'noindex,nofollow', 'dashboard-body'),
    'battle_station.html':    ('Battle Station — JobHunt Pro', 'Campaign control center for JobHunt Pro', 'noindex,nofollow', 'dashboard-body'),
    'candidate_profile.html': ('Candidate Profile — JobHunt Pro', 'Your candidate profile on JobHunt Pro', 'noindex,nofollow', 'dashboard-body'),
    'checkout_v3.html':       ('Checkout — JobHunt Pro', 'Complete your JobHunt Pro purchase securely.', 'noindex,follow', ''),
    'dashboard_v2.html':      ('Dashboard — JobHunt Pro', 'Monitor your AI job campaigns in real time.', 'noindex,nofollow', 'dashboard-body'),
    'email_test.html':        ('Email Test — JobHunt Pro', 'Test email delivery for JobHunt Pro campaigns.', 'noindex,nofollow', 'dashboard-body'),
    'employer_track.html':    ('Employer Tracker — JobHunt Pro', 'Track employer engagement and responses.', 'noindex,nofollow', 'dashboard-body'),
    'export.html':            ('Export Data — JobHunt Pro', 'Export your job application data.', 'noindex,nofollow', 'dashboard-body'),
    'for_employers.html':     ('For Employers — JobHunt Pro', 'JobHunt Pro solutions for employers and recruiters.', 'index,follow', ''),
    'funnel_analytics.html':  ('Funnel Analytics — JobHunt Pro', 'Analyze your job application funnel performance.', 'noindex,nofollow', 'dashboard-body'),
    'index_v3.html':          ('JobHunt Pro — AI Job Application Automation', 'Let 200 AI agents apply to thousands of jobs for you — automatically.', 'index,follow', ''),
    'index_v4.html':          ('JobHunt Pro — AI Job Application Automation', 'Let 200 AI agents apply to thousands of jobs for you — automatically.', 'index,follow', ''),
    'kanban_board.html':      ('Kanban Board — JobHunt Pro', 'Visualize your job application pipeline.', 'noindex,nofollow', 'dashboard-body'),
    'login_v2.html':          ('Login — JobHunt Pro', 'Login to your JobHunt Pro account.', 'noindex,follow', ''),
    'my_purchases.html':      ('My Purchases — JobHunt Pro', 'View your JobHunt Pro purchase history.', 'noindex,nofollow', 'dashboard-body'),
    'offers.html':            ('Special Offers — JobHunt Pro', 'Exclusive offers and plans for JobHunt Pro.', 'index,follow', ''),
    'pricing_v2.html':        ('Pricing — JobHunt Pro', 'Simple, transparent pricing for AI job applications.', 'index,follow', ''),
    'pricing_v3.html':        ('Pricing — JobHunt Pro', 'Simple, transparent pricing for AI job applications.', 'index,follow', ''),
    'referral.html':          ('Referral Program — JobHunt Pro', 'Earn rewards by referring friends to JobHunt Pro.', 'index,follow', ''),
    'resume_tailor.html':     ('Resume Tailor — JobHunt Pro', 'AI-powered resume tailoring for any job description.', 'noindex,nofollow', 'dashboard-body'),
    'sent_emails.html':       ('Sent Emails — JobHunt Pro', 'View your sent job application emails.', 'noindex,nofollow', 'dashboard-body'),
    'services_new.html':      ('Services — JobHunt Pro', 'Explore all JobHunt Pro AI-powered services.', 'index,follow', ''),
    'services_v2.html':       ('Services — JobHunt Pro', 'Explore all JobHunt Pro AI-powered services.', 'index,follow', ''),
    'stats.html':             ('Stats — JobHunt Pro', 'View your job application statistics.', 'noindex,nofollow', 'dashboard-body'),
    'trust.html':             ('Why Trust Us — JobHunt Pro', 'Why thousands of job seekers trust JobHunt Pro.', 'index,follow', ''),
    'upload_cv_v2.html':      ('Upload CV — JobHunt Pro', 'Upload your CV to start AI-powered job applications.', 'noindex,nofollow', 'dashboard-body'),
    'upload_cv_v3.html':      ('Upload CV — JobHunt Pro', 'Upload your CV to start AI-powered job applications.', 'noindex,nofollow', 'dashboard-body'),
    'wallet.html':            ('Wallet — JobHunt Pro', 'Manage your JobHunt Pro credits and payments.', 'noindex,nofollow', 'dashboard-body'),
}


def build_head(filename):
    meta = PAGE_META.get(filename, (
        'JobHunt Pro',
        'AI-powered job application automation platform.',
        'noindex,nofollow',
        ''
    ))
    title, description, robots, body_class = meta
    body_open = f'<body class="{body_class}">' if body_class else '<body>'
    fonts = '<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@500;600;700;800&display=swap" rel="stylesheet">'
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <link rel="icon" type="image/png" href="/static/favicon.png?v=3">
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{description}">
  <meta name="robots" content="{robots}">
  <title>{title}</title>
  {fonts}
''', body_open


def fix_file(filepath, filename):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if file already has <!DOCTYPE html>
    if content.lstrip().lower().startswith('<!doctype html>'):
        # Check if it also has <html> and <head>
        if '<html' in content[:500] and '<head' in content[:800]:
            print(f'  [OK]  {filename} — already has full structure')
            return False
    
    head_prefix, body_open = build_head(filename)

    # Pattern 1: Starts with <!-- comment (no html structure)
    # We need to find where the first <style> or actual content begins
    # and inject our head before it, then add </head><body> before first content tag
    
    # Find where the actual page content starts (first non-comment, non-link, non-style tag that is body-level)
    # Strategy: inject DOCTYPE + html + head at top, then find </style> and insert </head><body> after it
    
    # First check: does the file have any <html> tag already?
    has_html = bool(re.search(r'<html\b', content, re.IGNORECASE))
    has_head = bool(re.search(r'<head\b', content, re.IGNORECASE))
    has_doctype = bool(re.search(r'<!doctype html>', content, re.IGNORECASE))
    has_body = bool(re.search(r'<body\b', content, re.IGNORECASE))

    if has_doctype and has_html and has_head and has_body:
        print(f'  [OK]  {filename} — already complete')
        return False

    # Remove any existing broken DOCTYPE at top
    content_clean = re.sub(r'^<!DOCTYPE html>\s*', '', content, flags=re.IGNORECASE)
    
    # Find where to inject </head><body>
    # Look for </style> followed by body content
    style_end_match = re.search(r'</style>', content_clean, re.IGNORECASE)
    
    if style_end_match and not has_body:
        # Insert </head><body_open> right after </style>
        end_pos = style_end_match.end()
        content_new = head_prefix + content_clean[:end_pos] + f'\n</head>\n{body_open}\n' + content_clean[end_pos:]
    elif not has_body:
        # No style block — inject head, then body at start of content
        content_new = head_prefix + '\n</head>\n' + body_open + '\n' + content_clean
    else:
        # Has body but no doctype/html/head
        # Just prepend the head structure
        # Find where <body starts
        body_match = re.search(r'<body\b', content_clean, re.IGNORECASE)
        if body_match:
            content_new = head_prefix + content_clean[:body_match.start()] + '</head>\n' + content_clean[body_match.start():]
        else:
            content_new = head_prefix + '\n</head>\n' + body_open + '\n' + content_clean

    # Ensure closing </html> tag
    if not re.search(r'</html>', content_new, re.IGNORECASE):
        content_new = content_new.rstrip() + '\n</html>\n'

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content_new)
    
    print(f'  [FIXED] {filename}')
    return True


def main():
    fixed_count = 0
    skipped_count = 0

    files = sorted(os.listdir(TEMPLATES_DIR))
    for fname in files:
        if not fname.endswith('.html'):
            continue
        if fname in SKIP_FILES:
            print(f'  [SKIP] {fname} — partial template')
            skipped_count += 1
            continue
        if fname in ALREADY_FIXED:
            print(f'  [DONE] {fname} — already fixed in this session')
            skipped_count += 1
            continue
        
        fpath = os.path.join(TEMPLATES_DIR, fname)
        try:
            result = fix_file(fpath, fname)
            if result:
                fixed_count += 1
        except Exception as e:
            print(f'  [ERROR] {fname}: {e}')

    print(f'\n[OK] Done! Fixed {fixed_count} files, skipped {skipped_count}.')


if __name__ == '__main__':
    main()

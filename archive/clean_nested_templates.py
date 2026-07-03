import os
import re

TEMPLATES_DIR = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"

STRIP_TEMPLATES = {
    # Wrapped in Dashboard Shell
    'stats.html',
    'pricing_v3.html',
    'export.html',
    'dashboard_v3.html',
    'new_campaign_v2.html',
    'war_room.html',
    'battle_station.html',
    'wallet.html',
    'services_new.html',
    'my_purchases.html',
    'offers.html',
    'upload_cv_v3.html',
    'email_test.html',
    'referral.html',
    'sent_emails.html',
    'for_employers.html',
    'employer_track.html',
    'ats_scorer.html',
    'funnel_analytics.html',
    'resume_tailor.html',
    
    # Wrapped in Public Shell
    'contact.html',
    
    # Extending base.html
    'intel_view.html',
    'roast.html',
    'kanban_board.html',
    'interview_prep.html',
    'candidate_profile.html',
}

def clean_content(content):
    # Strip DOCTYPE
    content = re.sub(r'<!DOCTYPE html\s*>', '', content, flags=re.I)
    
    # Strip html tag
    content = re.sub(r'<html\b[^>]*>', '', content, flags=re.I)
    content = re.sub(r'</html>', '', content, flags=re.I)
    
    # Strip head tag
    content = re.sub(r'<head\b[^>]*>', '', content, flags=re.I)
    content = re.sub(r'</head>', '', content, flags=re.I)
    
    # Strip body tag
    content = re.sub(r'<body\b[^>]*>', '', content, flags=re.I)
    content = re.sub(r'</body>', '', content, flags=re.I)
    
    # Strip specific meta & link tags
    content = re.sub(r'<meta\s+charset=["\']?utf-8["\']?\s*/?>', '', content, flags=re.I)
    content = re.sub(r'<meta\s+name=["\']viewport["\'][^>]*>', '', content, flags=re.I)
    content = re.sub(r'<meta\s+name=["\']description["\'][^>]*>', '', content, flags=re.I)
    content = re.sub(r'<meta\s+name=["\']robots["\'][^>]*>', '', content, flags=re.I)
    content = re.sub(r'<link\s+rel=["\']icon["\'][^>]*>', '', content, flags=re.I)
    content = re.sub(r'<link\s+href=["\']https://fonts.googleapis.com/[^>]*>', '', content, flags=re.I)
    content = re.sub(r'<link\s+href=["\']https://fonts.gstatic.com/[^>]*>', '', content, flags=re.I)
    content = re.sub(r'<title>[^<]*</title>', '', content, flags=re.I)
    
    # Clean up empty lines
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        if line.strip() or (cleaned_lines and cleaned_lines[-1].strip()):
            cleaned_lines.append(line)
            
    return '\n'.join(cleaned_lines).strip() + '\n'

def process(dry_run=True):
    for fname in sorted(os.listdir(TEMPLATES_DIR)):
        if fname not in STRIP_TEMPLATES:
            continue
            
        fpath = os.path.join(TEMPLATES_DIR, fname)
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        cleaned = clean_content(content)
        
        # Check if changed
        if cleaned != content:
            print(f"{fname:<30} | Status: CHANGED (size: {len(content)} -> {len(cleaned)})")
            if not dry_run:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(cleaned)
        else:
            print(f"{fname:<30} | Status: NO CHANGE")

if __name__ == "__main__":
    import sys
    import difflib
    
    # Test diff on pricing_v3.html
    fpath = os.path.join(TEMPLATES_DIR, 'pricing_v3.html')
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        orig = f.read()
    cl = clean_content(orig)
    diff = difflib.unified_diff(orig.splitlines(), cl.splitlines(), fromfile='original', tofile='cleaned')
    with open(r'c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\scratch\diff.txt', 'w', encoding='utf-8') as df:
        df.write('\n'.join(diff))
    print("Written diff to scratch/diff.txt")
    
    dry = True
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        dry = False
        print("Running in WRITE mode...")
    else:
        print("Running in DRY RUN mode (no changes written)...")
    process(dry)

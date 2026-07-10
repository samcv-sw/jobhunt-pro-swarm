"""
Round 4 — Auto-Fixer Script
Fixes CSS physical property violations and adds missing titles/h1 across all templates.
"""
import os
import re

TEMPLATES_DIR = 'web/templates'

# CSS Logical Property replacements
CSS_REPLACEMENTS = [
    # margin
    (re.compile(r'\bmargin-left\b'), 'margin-inline-start'),
    (re.compile(r'\bmargin-right\b'), 'margin-inline-end'),
    # padding
    (re.compile(r'\bpadding-left\b'), 'padding-inline-start'),
    (re.compile(r'\bpadding-right\b'), 'padding-inline-end'),
    # border
    (re.compile(r'\bborder-left\b'), 'border-inline-start'),
    (re.compile(r'\bborder-right\b'), 'border-inline-end'),
    # text-align
    (re.compile(r'\btext-align:\s*left\b'), 'text-align: start'),
    (re.compile(r'\btext-align:\s*right\b'), 'text-align: end'),
]

# Page-specific titles and h1s for pages missing them
PAGE_META = {
    'contact.html': ('اتصل بنا | JobHunt Pro', 'تواصل معنا'),
    'dashboard_v3.html': ('لوحة التحكم | JobHunt Pro', 'لوحة التحكم'),
    'wallet.html': ('المحفظة | JobHunt Pro', 'محفظتي'),
    'war_room.html': ('غرفة العمليات | JobHunt Pro', 'غرفة العمليات'),
    'sent_emails.html': ('الرسائل المرسلة | JobHunt Pro', 'الرسائل المرسلة'),
    'ats_scorer.html': ('تقييم ATS | JobHunt Pro', 'محلل ATS للسيرة الذاتية'),
    'resume_tailor.html': ('تخصيص السيرة | JobHunt Pro', 'تخصيص السيرة الذاتية'),
    'interview_prep.html': ('التحضير للمقابلة | JobHunt Pro', 'التحضير للمقابلة الوظيفية'),
    'for_employers.html': ('للشركات | JobHunt Pro', 'حلول التوظيف للشركات'),
    'offers.html': ('العروض | JobHunt Pro', 'أفضل العروض الوظيفية'),
    'stats.html': ('الإحصائيات | JobHunt Pro', 'إحصائيات الأداء'),
    'battle_station.html': ('محطة القتال | JobHunt Pro', 'محطة الإدارة'),
    'funnel_analytics.html': ('تحليلات القمع | JobHunt Pro', 'تحليلات قمع التحويل'),
    'employer_track.html': ('تتبع أصحاب العمل | JobHunt Pro', 'تتبع أصحاب العمل'),
    'new_campaign_v2.html': ('حملة جديدة | JobHunt Pro', 'إنشاء حملة تقديم جديدة'),
    'my_purchases.html': ('مشترياتي | JobHunt Pro', 'سجل المشتريات'),
    'export.html': ('تصدير البيانات | JobHunt Pro', 'تصدير البيانات'),
    'pricing_v3.html': ('الأسعار | JobHunt Pro', 'خطط الأسعار'),
    'upload_cv_v3.html': ('رفع السيرة الذاتية | JobHunt Pro', 'رفع سيرتك الذاتية'),
    'roast.html': ('تقييم السيرة | JobHunt Pro', 'تقييم سيرتك الذاتية'),
    'tracking_analytics.html': ('تحليلات التتبع | JobHunt Pro', 'تحليلات التتبع'),
    'referral.html': ('الإحالة | JobHunt Pro', 'برنامج الإحالة'),
    'admin.html': ('الإدارة | JobHunt Pro', 'لوحة الإدارة'),
    'admin_analytics.html': ('تحليلات الإدارة | JobHunt Pro', 'تحليلات المنصة'),
    'admin_user.html': ('إدارة المستخدمين | JobHunt Pro', 'إدارة المستخدمين'),
    'kanban_board.html': ('لوحة كانبان | JobHunt Pro', 'لوحة إدارة الطلبات'),
    'campaign_detail.html': ('تفاصيل الحملة | JobHunt Pro', 'تفاصيل الحملة'),
    'candidate_profile.html': ('الملف الشخصي | JobHunt Pro', 'الملف الشخصي'),
    'intel_view.html': ('عرض الاستخبارات | JobHunt Pro', 'تحليل الاستخبارات الوظيفية'),
    'services_new.html': ('خدماتنا | JobHunt Pro', 'خدمات JobHunt Pro'),
    'email_test.html': ('اختبار البريد | JobHunt Pro', 'اختبار إرسال البريد'),
}

fixed_count = 0
css_fixed_count = 0

for root, dirs, files in os.walk(TEMPLATES_DIR):
    # Skip backup dirs
    if 'backup' in root.lower():
        continue
    for filename in files:
        if not filename.endswith('.html'):
            continue
        filepath = os.path.join(root, filename)
        try:
            content = open(filepath, encoding='utf-8', errors='ignore').read()
            original = content

            # 1. Fix CSS physical properties
            for pattern, replacement in CSS_REPLACEMENTS:
                content = pattern.sub(replacement, content)

            # 2. Add missing <title> if not present and we have metadata
            if '<title>' not in content and filename in PAGE_META:
                title_text, h1_text = PAGE_META[filename]
                # Try to insert after <head> or <meta charset
                if '<head>' in content:
                    content = content.replace('<head>', f'<head>\n<title>{title_text}</title>', 1)
                elif '<meta charset' in content:
                    content = content.replace('<meta charset', f'<title>{title_text}</title>\n<meta charset', 1)
                fixed_count += 1

            # 3. Add missing <h1> if not present — inject into first main content block
            if '<h1' not in content and filename in PAGE_META:
                _, h1_text = PAGE_META[filename]
                # Try to inject after opening <main> or <div class="container" or first <section
                for marker in ['<main', '<div class="container', '<section', '<div id="content']:
                    if marker in content:
                        idx = content.index(marker)
                        # find end of this tag
                        end = content.index('>', idx) + 1
                        content = content[:end] + f'\n<h1 class="sr-only">{h1_text}</h1>' + content[end:]
                        break

            if content != original:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                css_fixed_count += 1
                print(f'Fixed: {os.path.relpath(filepath, TEMPLATES_DIR)}')

        except Exception as e:
            print(f'Error {filename}: {e}')

print(f'\nDone! Fixed {css_fixed_count} files.')

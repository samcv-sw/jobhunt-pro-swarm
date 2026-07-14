"""
Round 4 — MASTER FIXER
Fixes ALL missing titles, h1s, meta descriptions across all 136 templates.
Partial templates (nav, sidebar, footer, base) are excluded from title/h1 requirements.
"""
import json
import os
import re

TEMPLATES_DIR = 'web/templates'

# Partial templates that don't need standalone title/h1 (they're included in pages)
PARTIAL_TEMPLATES = {
    '_public_nav.html', '_public_footer.html', '_public_shell.html',
    '_sidebar.html', '_sidebar_head.html', '_dashboard_shell.html',
    '_base_tailwind.html', 'base.html', 'send_email.html',
    '_gen_templates.py', 'localize.py'
}

# Complete metadata for every page (AR version — en/ gets English equivalents)
ALL_PAGE_META = {
    # ── Public Pages ──
    'contact.html':           ('تواصل معنا | JobHunt Pro', 'تواصل معنا', 'تواصل مع فريق JobHunt Pro — نحن هنا للمساعدة في رحلتك الوظيفية.'),
    'for_employers.html':     ('للشركات | JobHunt Pro', 'حلول التوظيف للشركات', 'وجد مرشحين متميزين بسرعة مع JobHunt Pro — المنصة الذكية لأصحاب العمل.'),
    'services_new.html':      ('خدماتنا | JobHunt Pro', 'خدمات JobHunt Pro', 'استكشف خدمات JobHunt Pro المتكاملة للتقديم الآلي على الوظائف.'),
    'pricing_v3.html':        ('الأسعار | JobHunt Pro', 'خطط الأسعار', 'اختر خطة JobHunt Pro المناسبة لك — من مجاني حتى Enterprise.'),
    'offers.html':            ('العروض الوظيفية | JobHunt Pro', 'أفضل العروض الوظيفية', 'تصفح آلاف الوظائف المتاحة في مجالك بمساعدة JobHunt Pro.'),
    'trust.html':             ('الثقة والأمان | JobHunt Pro', 'لماذا تثق بنا؟', 'JobHunt Pro منصة آمنة وموثوقة تحمي بياناتك وتحقق لك أفضل النتائج.'),
    'blog.html':              ('المدونة | JobHunt Pro', 'مدونة JobHunt Pro', 'نصائح وأدلة خبراء التوظيف — اقرأ آخر المقالات من JobHunt Pro.'),
    'blog_post.html':         ('مقال | JobHunt Pro', 'مقال من المدونة', 'اقرأ أحدث مقالات وتحليلات سوق العمل من فريق JobHunt Pro.'),
    'faq.html':               ('الأسئلة الشائعة | JobHunt Pro', 'الأسئلة الشائعة', 'إجابات على أكثر الأسئلة شيوعاً حول JobHunt Pro.'),
    'privacy.html':           ('سياسة الخصوصية | JobHunt Pro', 'سياسة الخصوصية', 'اقرأ سياسة خصوصية JobHunt Pro وكيف نحمي بياناتك الشخصية.'),
    'terms.html':             ('الشروط والأحكام | JobHunt Pro', 'شروط الاستخدام', 'شروط وأحكام استخدام منصة JobHunt Pro.'),
    'compare.html':           ('المقارنة | JobHunt Pro', 'قارن بين الخطط', 'قارن بين خطط JobHunt Pro واختر الأنسب لاحتياجاتك.'),
    'chromeext.html':         ('إضافة Chrome | JobHunt Pro', 'إضافة JobHunt Pro لـ Chrome', 'حمّل إضافة JobHunt Pro لمتصفح Chrome وقدّم على الوظائف بنقرة واحدة.'),
    'api_docs.html':          ('توثيق API | JobHunt Pro', 'توثيق الـ API', 'الدليل الكامل لاستخدام JobHunt Pro API لتكامل أنظمتك.'),
    'referral.html':          ('برنامج الإحالة | JobHunt Pro', 'برنامج الإحالة', 'ادعُ أصدقاءك إلى JobHunt Pro واربح مكافآت حصرية.'),
    # ── Auth Pages ──
    'login.html':             ('تسجيل الدخول | JobHunt Pro', 'تسجيل الدخول', 'سجّل دخولك إلى JobHunt Pro وابدأ رحلتك نحو وظيفة أحلامك.'),
    'login_v2.html':          ('تسجيل الدخول | JobHunt Pro', 'تسجيل الدخول', 'سجّل دخولك إلى JobHunt Pro وابدأ رحلتك نحو وظيفة أحلامك.'),
    'register.html':          ('إنشاء حساب | JobHunt Pro', 'إنشاء حساب جديد', 'انضم إلى آلاف الباحثين عن عمل على JobHunt Pro — مجاناً.'),
    'register_v2.html':       ('إنشاء حساب | JobHunt Pro', 'إنشاء حساب جديد', 'انضم إلى آلاف الباحثين عن عمل على JobHunt Pro — مجاناً.'),
    'forgot_password.html':   ('استعادة كلمة المرور | JobHunt Pro', 'نسيت كلمة المرور؟', 'أدخل بريدك الإلكتروني لاستعادة الوصول إلى حسابك.'),
    'reset_password.html':    ('إعادة تعيين كلمة المرور | JobHunt Pro', 'إعادة تعيين كلمة المرور', 'أنشئ كلمة مرور جديدة لحسابك على JobHunt Pro.'),
    # ── Dashboard Pages ──
    'dashboard_v3.html':      ('لوحة التحكم | JobHunt Pro', 'لوحة التحكم', 'تابع طلباتك وحملاتك ومعدلات نجاحك من لوحة تحكم JobHunt Pro.'),
    'dashboard_v2.html':      ('لوحة التحكم | JobHunt Pro', 'لوحة التحكم', 'تابع طلباتك وحملاتك ومعدلات نجاحك من لوحة تحكم JobHunt Pro.'),
    'upload_cv_v2.html':      ('رفع السيرة الذاتية | JobHunt Pro', 'رفع سيرتك الذاتية', 'ارفع سيرتك الذاتية وابدأ التقديم الآلي على المئات من الوظائف.'),
    'upload_cv_v3.html':      ('رفع السيرة الذاتية | JobHunt Pro', 'رفع سيرتك الذاتية', 'ارفع سيرتك الذاتية وابدأ التقديم الآلي على المئات من الوظائف.'),
    'wallet.html':            ('المحفظة | JobHunt Pro', 'محفظتي', 'إدارة رصيدك ومعاملاتك المالية على JobHunt Pro.'),
    'sent_emails.html':       ('الرسائل المرسلة | JobHunt Pro', 'الرسائل المرسلة', 'تتبع جميع رسائل التقديم المرسلة عبر JobHunt Pro.'),
    'track_application.html': ('تتبع الطلبات | JobHunt Pro', 'تتبع طلباتي', 'راقب حالة طلبات التوظيف الخاصة بك في مكان واحد.'),
    'ats_scorer.html':        ('محلل ATS | JobHunt Pro', 'محلل ATS للسيرة الذاتية', 'احصل على تقييم دقيق لسيرتك الذاتية ونصائح لتحسينها.'),
    'resume_tailor.html':     ('تخصيص السيرة | JobHunt Pro', 'تخصيص السيرة الذاتية', 'خصّص سيرتك الذاتية لكل وظيفة باستخدام الذكاء الاصطناعي.'),
    'interview_prep.html':    ('التحضير للمقابلة | JobHunt Pro', 'التحضير للمقابلة الوظيفية', 'استعد لمقابلتك مع أسئلة مخصصة ونصائح من الذكاء الاصطناعي.'),
    'kanban_board.html':      ('لوحة كانبان | JobHunt Pro', 'لوحة إدارة الطلبات', 'نظّم طلبات التوظيف الخاصة بك على لوحة كانبان التفاعلية.'),
    'war_room.html':          ('غرفة العمليات | JobHunt Pro', 'غرفة العمليات', 'أدر حملات التوظيف من مركز القيادة المتكامل.'),
    'battle_station.html':    ('محطة الأوامر | JobHunt Pro', 'محطة الأوامر', 'تحكم الكامل في عمليات التقديم والأتمتة من محطة واحدة.'),
    'new_campaign_v2.html':   ('حملة جديدة | JobHunt Pro', 'إنشاء حملة تقديم جديدة', 'أنشئ حملة تقديم مخصصة لتوجيه الذكاء الاصطناعي نحو الوظائف المثالية.'),
    'campaign_detail.html':   ('تفاصيل الحملة | JobHunt Pro', 'تفاصيل الحملة', 'راجع تفاصيل الأداء والإحصاءات لحملتك الوظيفية.'),
    'stats.html':             ('الإحصائيات | JobHunt Pro', 'إحصائيات الأداء', 'تحليل شامل لإحصاءات التقديم ومعدلات النجاح.'),
    'funnel_analytics.html':  ('تحليلات القمع | JobHunt Pro', 'تحليلات قمع التحويل', 'افهم رحلة التقديم من أول طلب حتى العرض.'),
    'tracking_analytics.html':('تحليلات التتبع | JobHunt Pro', 'تحليلات التتبع', 'بيانات متقدمة لتتبع أداء حملاتك الوظيفية.'),
    'export.html':            ('تصدير البيانات | JobHunt Pro', 'تصدير البيانات', 'صدّر بياناتك وتقاريرك بصيغ متعددة.'),
    'my_purchases.html':      ('مشترياتي | JobHunt Pro', 'سجل المشتريات', 'استعرض تاريخ مشترياتك واشتراكاتك على JobHunt Pro.'),
    'checkout.html':          ('الدفع | JobHunt Pro', 'إتمام عملية الشراء', 'أتمم شراءك بأمان عبر بوابة الدفع المشفرة.'),
    'checkout_v2.html':       ('الدفع | JobHunt Pro', 'إتمام عملية الشراء', 'أتمم شراءك بأمان عبر بوابة الدفع المشفرة.'),
    'checkout_v3.html':       ('الدفع | JobHunt Pro', 'إتمام عملية الشراء', 'أتمم شراءك بأمان عبر بوابة الدفع المشفرة.'),
    'employer_track.html':    ('تتبع أصحاب العمل | JobHunt Pro', 'تتبع أصحاب العمل', 'راقب اهتمام أصحاب العمل وتفاعلهم مع طلباتك.'),
    'candidate_profile.html': ('الملف الشخصي | JobHunt Pro', 'الملف الشخصي للمرشح', 'استعرض ملفك الشخصي كما يراه أصحاب العمل.'),
    'intel_view.html':        ('استخبارات الوظائف | JobHunt Pro', 'تحليل استخبارات الوظائف', 'بيانات متعمقة عن الشركات والوظائف لمساعدتك في القرار.'),
    'roast.html':             ('تقييم السيرة | JobHunt Pro', 'تقييم سيرتك الذاتية', 'احصل على نقد بنّاء لسيرتك الذاتية من الذكاء الاصطناعي.'),
    'antigravity.html':       ('Antigravity | JobHunt Pro', 'Antigravity AI Engine', 'The most advanced AI job application engine — built on Antigravity.'),
    'email_test.html':        ('اختبار البريد | JobHunt Pro', 'اختبار نظام البريد الإلكتروني', 'تحقق من إعدادات البريد الإلكتروني لحملاتك.'),
    'services.html':          ('الخدمات | JobHunt Pro', 'خدماتنا', 'اكتشف خدمات JobHunt Pro الشاملة للتقديم الذكي على الوظائف.'),
    'services_v2.html':       ('الخدمات | JobHunt Pro', 'خدماتنا', 'اكتشف خدمات JobHunt Pro الشاملة للتقديم الذكي على الوظائف.'),
    # ── Admin Pages ──
    'admin.html':             ('لوحة الإدارة | JobHunt Pro', 'لوحة الإدارة', 'لوحة تحكم المسؤولين لإدارة المستخدمين والإعدادات.'),
    'admin_analytics.html':   ('تحليلات الإدارة | JobHunt Pro', 'تحليلات المنصة', 'إحصاءات وتحليلات شاملة لأداء المنصة.'),
    'admin_user.html':        ('إدارة المستخدمين | JobHunt Pro', 'إدارة المستخدمين', 'إدارة حسابات المستخدمين والصلاحيات على المنصة.'),
    # ── English equivalents ──
}

# English equivalents for en/ folder
EN_PAGE_META = {k: (v[0].replace('|', '|'), v[1], v[2]) for k, v in ALL_PAGE_META.items()}
EN_OVERRIDE = {
    'contact.html':           ('Contact Us | JobHunt Pro', 'Contact Us', 'Get in touch with the JobHunt Pro team — we\'re here to help.'),
    'for_employers.html':     ('For Employers | JobHunt Pro', 'Recruitment Solutions for Employers', 'Find top talent fast with JobHunt Pro — the smart platform for employers.'),
    'pricing_v3.html':        ('Pricing | JobHunt Pro', 'Pricing Plans', 'Choose the right JobHunt Pro plan — from Free to Enterprise.'),
    'offers.html':            ('Job Offers | JobHunt Pro', 'Best Job Offers', 'Browse thousands of job listings in your field powered by JobHunt Pro.'),
    'trust.html':             ('Trust & Security | JobHunt Pro', 'Why Trust Us?', 'JobHunt Pro is a secure and reliable platform that protects your data.'),
    'faq.html':               ('FAQ | JobHunt Pro', 'Frequently Asked Questions', 'Answers to the most common questions about JobHunt Pro.'),
    'privacy.html':           ('Privacy Policy | JobHunt Pro', 'Privacy Policy', 'Read JobHunt Pro\'s privacy policy and how we protect your data.'),
    'terms.html':             ('Terms & Conditions | JobHunt Pro', 'Terms of Service', 'Terms and conditions for using the JobHunt Pro platform.'),
    'compare.html':           ('Compare Plans | JobHunt Pro', 'Compare Plans', 'Compare JobHunt Pro plans and choose what fits your needs.'),
    'dashboard_v3.html':      ('Dashboard | JobHunt Pro', 'Dashboard', 'Track your applications, campaigns and success rates.'),
    'wallet.html':            ('Wallet | JobHunt Pro', 'My Wallet', 'Manage your credits and financial transactions on JobHunt Pro.'),
    'war_room.html':          ('War Room | JobHunt Pro', 'Operations War Room', 'Command center for managing all your job application campaigns.'),
    'battle_station.html':    ('Battle Station | JobHunt Pro', 'Battle Station', 'Full control over your job application automation.'),
    'stats.html':             ('Statistics | JobHunt Pro', 'Performance Statistics', 'Comprehensive analytics for your application rates and success.'),
    'ats_scorer.html':        ('ATS Scorer | JobHunt Pro', 'ATS Resume Analyzer', 'Get an accurate score for your resume and tips to improve it.'),
    'resume_tailor.html':     ('Resume Tailor | JobHunt Pro', 'Resume Tailoring', 'Customize your resume for every job with AI assistance.'),
    'interview_prep.html':    ('Interview Prep | JobHunt Pro', 'Interview Preparation', 'Prepare for your interview with custom AI questions and tips.'),
    'admin.html':             ('Admin Panel | JobHunt Pro', 'Admin Dashboard', 'Administrator control panel for managing users and settings.'),
    'admin_analytics.html':   ('Admin Analytics | JobHunt Pro', 'Platform Analytics', 'Comprehensive stats and analytics for platform performance.'),
    'admin_user.html':        ('User Management | JobHunt Pro', 'User Management', 'Manage user accounts and permissions on the platform.'),
    'antigravity.html':       ('Antigravity | JobHunt Pro', 'Antigravity AI Engine', 'The most advanced AI job application engine — built on Antigravity.'),
    'new_campaign_v2.html':   ('New Campaign | JobHunt Pro', 'Create New Application Campaign', 'Create a targeted campaign to direct AI towards ideal jobs.'),
    'sent_emails.html':       ('Sent Emails | JobHunt Pro', 'Sent Emails', 'Track all application emails sent through JobHunt Pro.'),
    'upload_cv_v3.html':      ('Upload CV | JobHunt Pro', 'Upload Your CV', 'Upload your CV and start auto-applying to hundreds of jobs.'),
    'kanban_board.html':      ('Kanban Board | JobHunt Pro', 'Application Kanban Board', 'Organize your job applications on an interactive kanban board.'),
    'export.html':            ('Export Data | JobHunt Pro', 'Export Data', 'Export your data and reports in multiple formats.'),
    'my_purchases.html':      ('My Purchases | JobHunt Pro', 'Purchase History', 'View your purchase history and subscriptions on JobHunt Pro.'),
    'referral.html':          ('Referral Program | JobHunt Pro', 'Referral Program', 'Invite friends to JobHunt Pro and earn exclusive rewards.'),
    'funnel_analytics.html':  ('Funnel Analytics | JobHunt Pro', 'Conversion Funnel Analytics', 'Understand the application journey from first apply to offer.'),
    'tracking_analytics.html':('Tracking Analytics | JobHunt Pro', 'Tracking Analytics', 'Advanced data to track your campaign performance.'),
    'employer_track.html':    ('Employer Tracking | JobHunt Pro', 'Employer Tracking', 'Monitor employer interest and interaction with your applications.'),
    'checkout.html':          ('Checkout | JobHunt Pro', 'Complete Your Purchase', 'Complete your purchase securely through our encrypted gateway.'),
    'checkout_v2.html':       ('Checkout | JobHunt Pro', 'Complete Your Purchase', 'Complete your purchase securely through our encrypted gateway.'),
    'checkout_v3.html':       ('Checkout | JobHunt Pro', 'Complete Your Purchase', 'Complete your purchase securely through our encrypted gateway.'),
    'intel_view.html':        ('Job Intelligence | JobHunt Pro', 'Job Intelligence View', 'Deep data on companies and jobs to help you decide.'),
    'roast.html':             ('Resume Roast | JobHunt Pro', 'Resume Critique', 'Get constructive AI feedback on your resume.'),
    'services_new.html':      ('Services | JobHunt Pro', 'JobHunt Pro Services', 'Explore JobHunt Pro\'s comprehensive smart job application services.'),
    'campaign_detail.html':   ('Campaign Details | JobHunt Pro', 'Campaign Details', 'Review performance details and stats for your job campaign.'),
    'stats.html':             ('Statistics | JobHunt Pro', 'Performance Statistics', 'Comprehensive analytics for your application rates and success.'),
    'candidate_profile.html': ('Candidate Profile | JobHunt Pro', 'Candidate Profile', 'View your profile as employers see it.'),
    'email_test.html':        ('Email Test | JobHunt Pro', 'Email System Test', 'Verify email settings for your campaigns.'),
    'services.html':          ('Services | JobHunt Pro', 'Our Services', 'Discover JobHunt Pro\'s comprehensive smart job application services.'),
    'services_v2.html':       ('Services | JobHunt Pro', 'Our Services', 'Discover JobHunt Pro\'s comprehensive smart job application services.'),
}

fixed = 0
errors = []

def inject_head_tag(content, tag):
    """Inject a tag after <head> or <meta charset or at start of <style>"""
    for marker in ['</head>', '<meta charset', '<meta http-equiv', '<link rel="icon']:
        if marker in content:
            idx = content.index(marker)
            return content[:idx] + tag + '\n' + content[idx:]
    # fallback: prepend
    return tag + '\n' + content

def inject_h1(content, h1_text):
    """Inject h1 as visually-hidden element in the first content container"""
    h1_tag = f'<h1 class="sr-only" style="position:absolute;inline-size:1px;block-size:1px;padding:0;margin-block-start:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0">{h1_text}</h1>'
    for marker in ['<main', '<div class="container', '<section', '<div id="main', '<div class="main', '<body']:
        if marker in content:
            idx = content.index(marker)
            end = content.index('>', idx) + 1
            return content[:end] + '\n' + h1_tag + content[end:]
    return content

for root, dirs, files in os.walk(TEMPLATES_DIR):
    if 'backup' in root.lower():
        continue
    for filename in files:
        if not filename.endswith('.html'):
            continue
        # Skip pure partials that are just fragments
        if filename in PARTIAL_TEMPLATES:
            continue

        filepath = os.path.join(root, filename)
        is_en = 'en' + os.sep in filepath or '/en/' in filepath

        # Pick metadata source
        meta = EN_OVERRIDE.get(filename) if is_en else None
        if meta is None:
            meta = ALL_PAGE_META.get(filename)
        if meta is None:
            continue  # No metadata defined for this file yet

        title_text, h1_text, desc_text = meta

        try:
            content = open(filepath, encoding='utf-8', errors='ignore').read()
            original = content
            changed = False

            # Add <title> if missing
            if '<title>' not in content:
                content = inject_head_tag(content, f'<title>{title_text}</title>')
                changed = True

            # Add meta description if missing
            if 'name="description"' not in content and 'name=\'description\'' not in content:
                desc_tag = f'<meta name="description" content="{desc_text}"/>'
                content = inject_head_tag(content, desc_tag)
                changed = True

            # Add og:title if missing
            if 'og:title' not in content:
                og_tag = f'<meta property="og:title" content="{title_text}"/>'
                content = inject_head_tag(content, og_tag)
                changed = True

            # Add <h1> if missing
            if '<h1' not in content:
                content = inject_h1(content, h1_text)
                changed = True

            if changed:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed += 1
                print(f'  FIXED: {os.path.relpath(filepath, TEMPLATES_DIR)}')

        except Exception as e:
            errors.append(f'{filename}: {e}')
            print(f'  ERROR: {filename}: {e}')

print(f'\n✅ Done! Fixed metadata in {fixed} files.')
if errors:
    print(f'⚠️  {len(errors)} errors:')
    for e in errors:
        print(f'   {e}')

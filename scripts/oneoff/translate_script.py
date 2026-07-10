"""
scripts/oneoff/translate_script.py
JobHunt Pro - Translation Script Utility
Processes search-and-replace dictionary translations for index_v3.html template file.
"""
import os
import logging
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_translation() -> None:
    """Run search-and-replace translations for target template file."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        target_path = os.path.join(base_dir, "web", "templates", "index_v3.html")

        if not os.path.exists(target_path):
            logger.warning(f"Target template not found at: {target_path}")
            return

        with open(target_path, "r", encoding="utf-8") as f:
            text = f.read()

        reps: Dict[str, str] = {
            'THE DIFFERENCE': 'الفرق',
            'Job Search: <span class="gradient">Before vs After</span>': 'البحث عن عمل: <span class="gradient">قبل وبعد</span>',
            'What your job hunt looks like with and without JobHunt Pro automation': 'كيف يبدو بحثك عن عمل مع وبدون أتمتة JobHunt Pro',
            'Manual Job Search': 'البحث اليدوي عن وظيفة',
            '40+ hours/week scrolling job boards': 'أكثر من 40 ساعة/أسبوع تصفح لمواقع التوظيف',
            'Copy-pasting the same cover letter': 'نسخ ولصق نفس رسالة التغطية',
            'Missing 80% of new job postings': 'تفويت 80% من الوظائف الجديدة',
            'Emails landing in spam folders': 'الإيميلات تنتهي في مجلد السبام',
            'Zero tracking on sent applications': 'انعدام التتبع للطلبات المرسلة',
            '2-3% interview rate on average': 'نسبة المقابلات 2-3% بالمتوسط',
            'Burnout within 3-4 weeks': 'إرهاق خلال 3-4 أسابيع',
            '<div class="ba-vs">VS</div>': '<div class="ba-vs">ضد</div>',
            '<div class="ba-hint">THE CHOICE IS CLEAR</div>': '<div class="ba-hint">الخيار واضح</div>',
            'JobHunt Pro Automated': 'JobHunt Pro المؤتمت',
            '0 hours/week — fully automated': '0 ساعة/أسبوع — مؤتمت بالكامل',
            'AI writes unique cover letters per company': 'الذكاء الاصطناعي يكتب رسائل تغطية فريدة لكل شركة',
            'Catches every new posting instantly': 'يلتقط كل وظيفة جديدة فوراً',
            '20+ rotating email providers = 99% inbox': '20+ مزود إيميل متناوب = 99% في صندوق الوارد',
            'Real-time dashboard tracks everything': 'لوحة تحكم حية تتبع كل شيء',
            '8-15% interview rate (4x higher)': 'نسبة المقابلات 8-15% (أعلى بـ 4 أضعاف)',
            'Sustainable — runs 24/7 while you sleep': 'مستدام — يعمل 24/7 وأنت نائم',
            
            'PLATFORM FEATURES': 'ميزات المنصة',
            'Everything You <span class="gradient">Need</span>': 'كل ما <span class="gradient">تحتاجه</span>',
            'A complete job application arsenal — every tool you need to automate your entire job search, built right in.': 'ترسانة متكاملة للتقديم على الوظائف — كل أداة تحتاجها لأتمتة بحثك بالكامل مبنية هنا.',
            'AI-Powered Personalization': 'تخصيص بالذكاء الاصطناعي',
            'Advanced AI crafts unique, personalized cover letters for every single company. Reads the job description, understands requirements, and tailors perfectly — never generic, never templated.': 'الذكاء الاصطناعي يصنع رسائل تغطية مخصصة وفريدة لكل شركة. يقرأ الوصف الوظيفي، يفهم المتمت، ويخصص بشكل مثالي — لا توجد قوالب عامة.',
            'Multi-Provider Email System': 'نظام إيميلات متعدد المزودين',
            'Smart rotation across 20+ email providers with intelligent warmup, spam-score checking, and automatic fallback. Your applications always land in the inbox, never in spam.': 'تناوب ذكي بين 20+ مزود إيميل مع إحماء ذكي وفحص لمستوى السبام. طلباتك تصل دائماً لصندوق الوارد، وليس السبام أبداً.',
            'Multi-Engine Job Search': 'بحث متعدد المحركات',
            'We search across all major platforms — every job board, every company career page, every listing worldwide. 50+ countries, all industries, all levels.': 'نبحث في جميع المنصات الكبرى — كل موقع توظيف، وكل صفحة وظائف شركة، وكل إعلان عالمياً. 50+ دولة، كل الصناعات، كل المستويات.',
            'Stealth Protection': 'حماية خفية',
            'Smart delays, human-like timing patterns, and sophisticated anti-detection. Email providers never flag you. Sophisticated algorithms keep you completely under the radar.': 'تأخير ذكي، توقيت يشبه البشر، وتجنب متطور للاكتشاف. خوارزمياتنا تبقيك تحت الرادار تماماً.',
            'Real-Time Analytics': 'تحليلات حية',
            'Visual pipeline tracks every application: Discovered → Applied → Followed Up → Interview → Offer. Track opens, clicks, and responses in real-time with your personal dashboard.': 'خط سير مرئي يتتبع كل طلب: اُكتشف → تم التقديم → تم المتابعة → مقابلة → عرض. تتبع الفتح، النقر، والردود بالوقت الفعلي من لوحة تحكمك الشخصية.',
            'Automatic Follow-Ups': 'متابعات تلقائية',
            'If no response, our system automatically sends polite, personalized follow-up emails. Boosts response rates by up to 40%. Never miss an opportunity because you forgot to follow up.': 'في حال عدم الرد، يقوم نظامنا بإرسال إيميلات متابعة مهذبة ومخصصة. يرفع نسبة الردود حتى 40%. لا تفوت أي فرصة فقط لأنك نسيت المتابعة.',
            
            'ATS RESUME CHECKER': 'فاحص السيرة الذاتية لـ ATS',
            'Is Your Resume <span class="gradient">ATS-Ready?</span>': 'هل سيرتك <span class="gradient">جاهزة لـ ATS؟</span>',
            '99% of Fortune 500 companies use ATS. JobHunt Pro scans your resume against real job descriptions and shows exactly what to fix — <strong style="color:var(--cyan)">free</strong>.': '99% من كبرى الشركات تستخدم نظام تتبع المتقدمين (ATS). يقوم JobHunt Pro بفحص سيرتك مقابل أوصاف وظيفية حقيقية ويوضح لك بالضبط ما يجب إصلاحه — <strong style="color:var(--cyan)">مجاناً</strong>.',
            'Drag your resume here or click to upload': 'اسحب سيرتك الذاتية هنا أو انقر للرفع',
            'PDF, DOCX, or TXT (Max 5MB)': 'PDF, DOCX, أو TXT (الحد الأقصى 5 ميجابايت)',
            'Scan My Resume — Free': 'افحص سيرتي الذاتية — مجاناً',
            'Sample: Senior Network Engineer Resume': 'مثال: سيرة ذاتية لمهندس شبكات أول',
            'Keyword Match': 'تطابق الكلمات المفتاحية',
            'ATS Compatibility': 'التوافق مع ATS',
            'Format Issues': 'مشاكل التنسيق',
            'Missing Skills': 'مهارات مفقودة',
            '3 found': '3 وُجدت',

            "WHY WE'RE #1": 'لماذا نحن في الصدارة',
            'How We <span class="gradient">Compare</span>': 'كيف <span class="gradient">نقارن</span>',
            'JobHunt Pro is the only platform that automates the ENTIRE job application process': 'JobHunt Pro هي المنصة الوحيدة التي تؤتمت عملية التقديم للوظائف بأكملها',
            'Feature': 'الميزة',
            'Fully Automated Applying': 'تقديم آلي بالكامل',
            '✗ (Manual clicks)': '✗ (نقرات يدوية)',
            '✗ (Plugin only)': '✗ (إضافة متصفح فقط)',
            '✓ 100% Auto': '✓ آلي 100%',
            'Unique AI Cover Letters': 'رسائل تغطية ذكية وفريدة',
            '✗ (Generic template)': '✗ (قالب عام)',
            '✓ Every application': '✓ لكل طلب',
            'Email Inbox Delivery': 'التسليم لصندوق الوارد',
            '✗ (Often Spam)': '✗ (غالباً سبام)',
            '✓ 20+ Rotating IPs': '✓ 20+ عنوان IP متناوب',
            'Auto Follow-Ups': 'متابعات تلقائية',
            'Smart Resume Optimization': 'تحسين ذكي للسيرة',
            '✗ (Basic ATS)': '✗ (فحص أساسي)',
            '✓ Custom per job': '✓ مخصص لكل وظيفة',
            'Analytics Dashboard': 'لوحة تحكم تحليلات',
            '✓ Visual Pipeline': '✓ خط سير مرئي',
            'Multi-Engine Search': 'بحث متعدد المحركات',
            '✗ (Only LinkedIn)': '✗ (فقط LinkedIn)',
            '✗ (LinkedIn & Indeed)': '✗ (LinkedIn و Indeed)',
            '✓ 10+ Global Engines': '✓ 10+ محركات عالمية',
            'BanShield Protection': 'حماية من الحظر (BanShield)',
            '★ BanShield': '★ BanShield',
            'Crypto Payments': 'الدفع بالعملات الرقمية',
            '✓ BTC, ETH, USDT': '✓ BTC, ETH, USDT',
            'Free Tier': 'باقة مجانية',
            '★ From $2': '★ من $2',
            'Money-Back Guarantee': 'ضمان استرداد المال',
            '✓ 30-Day': '✓ 30 يوم',
            'Starting Price': 'يبدأ السعر من',
            '$99/yr': '99$/سنة',
            '$15/mo': '15$/شهر',
            'Free+': 'مجاني+',
            '$19/mo': '19$/شهر',
            '$50/mo': '50$/شهر',
            '$2 ONE-TIME': '2$ مرة واحدة',

            'LIVE PLATFORM PREVIEW': 'نظرة حية على المنصة',
            'See The <span class="gradient">Dashboard</span> In Action': 'شاهد <span class="gradient">لوحة التحكم</span> مباشرة',
            'Your personal command center for the entire job search. Real-time tracking, analytics, and insights.': 'مركز قيادتك الشخصي لكامل عملية البحث عن عمل. تتبع، تحليلات، ورؤى في الوقت الفعلي.',
            'Can I target specific companies or industries?': 'هل يمكنني استهداف شركات أو صناعات محددة؟',
            'Yes! You have full control. You can target specific job titles, industries, salary ranges, locations, company sizes, and even specific companies. Want to only apply to Fortune 500 tech companies in Dubai paying $80K+? You can do that. Want to cast a wide net across all engineering roles in the GCC? That works too. Our search filters give you complete flexibility.': 'نعم! لديك السيطرة الكاملة. يمكنك استهداف مسميات وظيفية معينة، صناعات، نطاقات رواتب، مواقع، وحتى شركات محددة. تريد التقديم فقط لشركات التقنية الكبرى في دبي براتب 80 ألف دولار+؟ يمكنك فعل ذلك.',
            'How quickly will I start seeing results?': 'متى سأبدأ في رؤية النتائج؟',
            'Applications begin within minutes of setting up your campaign. Most users see their first email opens within 24-48 hours, and interview invitations typically start arriving within 5-14 days. The speed depends on your industry, location, and target roles — but our users average an 8-15% interview rate, compared to the industry standard of 2-3%.': 'تبدأ الطلبات خلال دقائق من إعداد حملتك. يرى معظم المستخدمين أول فتح للإيميلات خلال 24-48 ساعة، وعادة ما تبدأ دعوات المقابلات بالوصول خلال 5-14 يوماً. متوسط نسبة المقابلات لدينا هو 8-15%، مقارنة بـ 2-3% للمعيار العام.',

            'VALUE ANALYSIS': 'تحليل القيمة',
            'Your <span class="gradient">ROI</span> Calculator': 'حاسبة <span class="gradient">العائد على الاستثمار</span>',
            'See how much you save by automating your job search with AI': 'شاهد كم توفر بأتمتة بحثك عن عمل عبر الذكاء الاصطناعي',
            'Your Target Annual Salary:': 'الراتب السنوي المستهدف:',
            'per month you lose by staying unemployed 1 extra month': 'شهرياً تخسرها ببقائك عاطلاً عن العمل لشهر إضافي',
            'One-Time Cost': 'تكلفة لمرة واحدة',
            'Annual Return': 'العائد السنوي',
            'ROI Multiplier': 'مضاعف العائد',
            '🚀 Invest $5 — Earn $50K+': '🚀 استثمر 5$ — اربح 50,000$+',

            'Jobs Posted Today': 'وظائف نُشرت اليوم',
            'Applications Sent in Last Hour': 'طلبات أُرسلت في آخر ساعة',
            'Limited': 'محدود',
            'Pro Plan Slots Available': 'مقاعد باقة برو المتاحة',

            '&#x1f91d; EARN WHILE YOU SHARE': '&#x1f91d; اكسب بينما تشارك',
            '<span class="gradient">Referral Program</span>': '<span class="gradient">برنامج الإحالة</span>',
            'Share JobHunt Pro with friends. They get <strong style="color:var(--cyan)">20% off</strong> their first plan, and you earn <strong style="color:var(--gold)">$5 credit</strong> for every referral that signs up. No limits.': 'شارك JobHunt Pro مع الأصدقاء. يحصلون على <strong style="color:var(--cyan)">خصم 20%</strong> على باقتهم الأولى، وتكسب أنت <strong style="color:var(--gold)">رصيد 5$</strong> لكل إحالة تسجل. بلا حدود.',
            'Share Your Link': 'شارك رابطك',
            'Copy your unique referral link from the dashboard': 'انسخ رابط الإحالة الخاص بك من لوحة التحكم',
            'They Sign Up': 'هم يسجلون',
            'Friend creates an account with any plan': 'ينشئ صديقك حساباً بأي باقة',
            'You Earn $5': 'أنت تكسب 5$',
            'Credit added instantly to your wallet': 'يُضاف الرصيد فوراً لمحفظتك',
            'Repeat': 'كرر العملية',
            'No limit — refer as many as you want': 'بلا حدود — أحِل قدر ما تشاء',
            '&#x1f517; Get Your Referral Link — Free': '&#x1f517; احصل على رابط الإحالة — مجاناً',

            'Ready to <span class="gradient">Automate</span><br>Your Job Search?': 'جاهز لـ <span class="gradient">أتمتة</span><br>بحثك عن عمل؟',
            'Stop spending hours on manual applications. Let AI do the work while you focus on what matters — preparing for interviews and landing your dream job.': 'توقف عن قضاء ساعات في التقديم اليدوي. دع الذكاء الاصطناعي يقوم بالعمل بينما تركز أنت على الأهم — التحضير للمقابلات والحصول على وظيفة أحلامك.',
            '🚀 Start Your Free Campaign Now →': '🚀 ابدأ حملتك المجانية الآن ←',
            '<strong>⚠️ Only 12 Pro Plan slots remaining this week</strong> • <strong>✓ No credit card required</strong> • Set up in 2 minutes • 30-day money-back guarantee': '<strong>⚠️ يتبقى 12 مقعداً في باقة برو هذا الأسبوع</strong> • <strong>✓ لا حاجة لبطاقة ائتمان</strong> • إعداد في دقيقتين • ضمان استرداد المال لمدة 30 يوم',

            "WAIT! Don't Leave Empty-Handed": 'انتظر! لا تغادر خالي الوفين',
            'Before you go — claim your <strong style="color:var(--cyan)">FREE ATS Resume Scan</strong> and see why your resume might be getting rejected by automated systems.': 'قبل أن تذهب — احصل على <strong style="color:var(--cyan)">فحص ATS مجاني لسيرتك الذاتية</strong> لتعرف سبب رفض الأنظمة الآلية لسيرتك.',
            '&#x2705; Instant ATS Score': '&#x2705; نتيجة ATS فورية',
            '&#x2705; Keyword Gap Analysis': '&#x2705; تحليل فجوات الكلمات المفتاحية',
            '&#x2705; 100% Free — No Card Required': '&#x2705; مجاني 100% — لا حاجة لبطاقة',
            '&#x1f50d; Scan My Resume FREE': '&#x1f50d; افحص سيرتي الذاتية مجاناً',
            'Trusted by professionals in 50+ countries': 'موثوق من المحترفين in 50+ دولة',
            '&#x1f680; Start Applying Free': '&#x1f680; ابدأ التقديم مجاناً'
        }

        for k, v in reps.items():
            text = text.replace(k, v)

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(text)

        logger.info("Successfully translated index_v3.html template.")
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise

if __name__ == "__main__":
    run_translation()

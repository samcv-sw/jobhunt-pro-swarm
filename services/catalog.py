"""
JobHunt Pro — Service Catalog v2
Micro-services priced $2–$25 for instant automated delivery
Each service has: id, name, price, description, delivery_time, features, fulfillment_func
Contains full Arabic & English translations (name_ar, description_ar, etc.)
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

SERVICE_CATALOG = [
    {
        "id": "cv-review",
        "name": "CV Review & Score",
        "price": 2,
        "category": "resume",
        "description": "AI-powered CV analysis — get a score out of 100 with specific improvement tips",
        "delivery": "instant",
        "features": [
            "ATS compatibility score",
            "Keyword gap analysis",
            "Format suggestions",
            "Section-by-section feedback"
        ],
        "what_they_get": "PDF report with score, 10+ improvement suggestions, keyword optimization list",
        "name_ar": "فحص وتقييم السيرة الذاتية",
        "description_ar": "تحليل كامل لسيرتك بالذكاء الاصطناعي مع تقرير درجات من 100 وتوصيات تحسين فورية",
        "features_ar": [
            "نسبة التوافق مع ATS",
            "كشف المهارات المفقودة",
            "تحسين الهيكل والتنسيق",
            "ملاحظات لكل قسم"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "cv-keyword",
        "name": "CV Keyword Optimization",
        "price": 5,
        "category": "resume",
        "description": "Rewrite your CV with recruiter-optimized keywords for ATS scanners",
        "delivery": "instant",
        "features": [
            "ATS keyword injection",
            "Role-specific optimization",
            "Action verb enhancement",
            "Quantified achievements"
        ],
        "what_they_get": "Optimized CV file with ATS score report showing before/after comparison",
        "name_ar": "تحسين الكلمات المفتاحية للـ ATS",
        "description_ar": "إعادة صياغة السيرة الذاتية بحقن الكلمات الأكثر طلباً لدى مسؤولي التوظيف",
        "features_ar": [
            "حقن كلمات ATS",
            "تحسين حسب المسمى الوظيفي",
            "إبراز أفعال الإنجاز",
            "مقارنة قبل وبعد"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "cv-ats-parse",
        "name": "ATS Parsing & Formatting Audit",
        "price": 3,
        "category": "resume",
        "description": "Test how Taleo, Workday, and Greenhouse read your CV layout",
        "delivery": "instant",
        "features": [
            "Multi-ATS parser simulator",
            "Font & table readability test",
            "Unread text warning",
            "Clean layout recommendation"
        ],
        "what_they_get": "ATS parsing simulation report showing exact plain-text extraction",
        "name_ar": "فحص قراءة فلاتر ATS والتنسيق",
        "description_ar": "اختبار مدى قدرة أنظمة Taleo و Workday على قراءة سيرتك الذاتية وتفادي الأخطاء",
        "features_ar": [
            "محاكاة أنظمة ATS الكبرى",
            "فحص الجداول والخطوط",
            "كشف النص المخفي",
            "تقرير التنسيق النظيف"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "cover-letter-basic",
        "name": "Cover Letter (Basic)",
        "price": 3,
        "category": "resume",
        "description": "AI-generated cover letter tailored to your target job title and industry",
        "delivery": "instant",
        "features": [
            "Personalized opening",
            "Skills highlight section",
            "Professional closing",
            "PDF + DOCX format"
        ],
        "what_they_get": "Ready-to-use cover letter in your name, 2-3 paragraphs, PDF format",
        "name_ar": "خطاب تغطية أساسي (Cover Letter)",
        "description_ar": "خطاب تغطية احترافي بالذكاء الاصطناعي مخصص لمجالك والمسمى الوظيفي المستهدف",
        "features_ar": [
            "مقدمة مخصصة",
            "إبراز أهم المهارات",
            "خاتمة احترافية",
            "صيغ PDF + Word"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "cover-letter-pro",
        "name": "Tailored Role Cover Letter",
        "price": 5,
        "category": "resume",
        "description": "High-impact cover letter customized for a specific target company & vacancy",
        "delivery": "instant",
        "features": [
            "Company mission alignment",
            "Pain-point solving pitch",
            "Metric-backed highlights",
            "Editable Word document"
        ],
        "what_they_get": "Custom 1-page cover letter matching the exact job description",
        "name_ar": "خطاب تغطية مخصص لشركة معينة",
        "description_ar": "خطاب قاطر مصمم خصيصاً لشاغر وشركة معينة يربط بين خبراتك ومتطلباتهم",
        "features_ar": [
            "ربط برؤية الشركة",
            "حل نقاط ألم الشاغر",
            "أرقام وإنجازات موثقة",
            "ملف Word قابل للتعديل"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "skill-gap-report",
        "name": "Skills Gap Report",
        "price": 4,
        "category": "resume",
        "description": "AI analyzes your CV against 100+ target job listings to find missing skills",
        "delivery": "instant",
        "features": [
            "Market demand analysis",
            "Missing certification detection",
            "Priority skill ranking",
            "Learning roadmap"
        ],
        "what_they_get": "PDF report with top-10 missing skills, certification recommendations, 3-month learning plan",
        "name_ar": "تقرير المهارات والشهادات المفقودة",
        "description_ar": "مقارنة سيرتك الذاتية مع 100+ شاغر مستهدف لتحديد المهارات الأكثر طلباً بالسوق",
        "features_ar": [
            "تحليل طلبات السوق",
            "اكتشاف الشهادات الناقصة",
            "ترتيب الأولويات",
            "خطة تعلم 3 أشهر"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "cv-translation-ar-en",
        "name": "Bilingual CV Translation (Ar/En)",
        "price": 6,
        "category": "resume",
        "description": "Professional translation & adaptation between Arabic and English for Gulf markets",
        "delivery": "24 hours",
        "features": [
            "Gulf business terminology",
            "RTL/LTR typography",
            "Dual-language export",
            "ATS-compliant formatting"
        ],
        "what_they_get": "Matching Arabic & English CV versions in PDF & Word formats",
        "name_ar": "ترجمة سيرة ذاتية مزدوجة (عربي/إنجليزي)",
        "description_ar": "ترجمة صياغية احترافية ومطابقة لمصطلحات التوظيف بالخليج بين العربية والإنجلتيرية",
        "features_ar": [
            "مصطلحات التوظيف بالخليج",
            "تنسيق RTL/LTR دقيق",
            "تصدير الملفين",
            "توافق كامل مع ATS"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "cv-executive-rebuild",
        "name": "Executive CV & Impact Audit",
        "price": 12,
        "category": "resume",
        "description": "Transform operational bullets into high-level P&L, leadership, and ROI metrics",
        "delivery": "24 hours",
        "features": [
            "C-Suite framing",
            "P&L / Revenue metric emphasis",
            "Board-level bullet points",
            "Executive summary bio"
        ],
        "what_they_get": "Executive level CV rewrite tailored for Director, VP & C-level roles",
        "name_ar": "إعادة صياغة السيرة الذاتية التنفيذية",
        "description_ar": "تحويل نقاط الخبرة التشغيلية إلى لغة قيادية رصينة تركّز على الأرباح والـ ROI",
        "features_ar": [
            "لغة الـ C-Suite",
            "إبراز الميزانيات والأرباح",
            "صياغة إنجازات مجلس الإدارة",
            "ملخص تنفيذي"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "cv-visual-redesign",
        "name": "Modern Minimalist CV PDF",
        "price": 6,
        "category": "resume",
        "description": "Sleek, modern glassmorphic PDF CV template that stands out to human eyes",
        "delivery": "instant",
        "features": [
            "High contrast layout",
            "HR recruiter eye-tracking optimization",
            "Print & screen ready",
            "Vector PDF export"
        ],
        "what_they_get": "Beautiful custom styled PDF version of your CV",
        "name_ar": "تصميم سيرة ذاتية PDF زجاجي حديث",
        "description_ar": "قالب PDF زجاجي عصري يجمع بين الجاذبية البصرية وقابلية القراءة للـ ATS",
        "features_ar": [
            "تباين عالي للعين",
            "تحسين مسار القراءة للـ HR",
            "جاهز للطباعة والشاشة",
            "تصدير PDF عالي الدقة"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "cv-technical-projects",
        "name": "Technical Project Portfolio CV Addon",
        "price": 5,
        "category": "resume",
        "description": "Structured 1-page tech portfolio insert highlighting GitHub, Architecture & Stack",
        "delivery": "instant",
        "features": [
            "Code repository links",
            "Tech stack breakdown",
            "System architecture summary",
            "Impact metrics"
        ],
        "what_they_get": "1-page technical project showcase sheet for software & data roles",
        "name_ar": "ملحق استعراض المشاريع التقنية",
        "description_ar": "صفحة مخصصة للوظائف التقنية تستعرض مشاريع GitHub، المعمارية والـ Stack",
        "features_ar": [
            "روابط الروابِط والـ Repos",
            "تقسيم الـ Tech Stack",
            "مخطط المعمارية",
            "مؤشرات الأداء"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "cv-career-gap",
        "name": "Career Gap Fix & Explanation Script",
        "price": 4,
        "category": "resume",
        "description": "Frame employment gaps into positive sabbatical, upskilling, or consulting stories",
        "delivery": "instant",
        "features": [
            "Gap bridging narrative",
            "Sabbatical framing",
            "Upskilling emphasis",
            "Recruiter objection script"
        ],
        "what_they_get": "CV section update + talking points for recruiter phone screens",
        "name_ar": "معالجة وتبرير فترات الانقطاع",
        "description_ar": "إعادة تأطير فترات الانقطاع عن العمل إلى خبرات استشارية وتعلم وتطوير مهارات",
        "features_ar": [
            "سرد بريجينغ قاطع",
            "تأطير الإجازة الاستكشافية",
            "إبراز تطوير الذات",
            "سيناريو الاتصال الأول"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "cv-canva-ats-converter",
        "name": "Canva CV to Clean ATS Converter",
        "price": 5,
        "category": "resume",
        "description": "Convert unreadable graphic/Canva CVs into 100% ATS compliant text structures",
        "delivery": "instant",
        "features": [
            "Font table cleanup",
            "Multi-column removal",
            "Keyword preservation",
            "Clean PDF export"
        ],
        "what_they_get": "Clean ATS-scannable version of your graphic resume",
        "name_ar": "تحويل سير Canva إلى صيغة ATS مقروءة",
        "description_ar": "تحويل السير الذاتية المصممة على Canva إلى نسق نصي نظيف يقبله فلاتر الشركات",
        "features_ar": [
            "تنظيف الجداول والأعمدة",
            "إزالة الأشكال المعقدة",
            "حفظ الكلمات المفتاحية",
            "تصدير PDF نظيف"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "linkedin-headline",
        "name": "LinkedIn Headline & Bio",
        "price": 3,
        "category": "linkedin",
        "description": "Optimized LinkedIn headline and about section to attract recruiters",
        "delivery": "instant",
        "features": [
            "SEO-optimized headline",
            "Recruiter-focused summary",
            "Keyword rich",
            "Character-count optimized"
        ],
        "what_they_get": "3 headline variants + 150-word About section + hashtag recommendations",
        "name_ar": "عنوان ولخص ملف لينكد إن",
        "description_ar": "كتابة عنوان نبذي ملائم لخوارزميات لينكد إن لجذب مسؤولي التوظيف لحسابك",
        "features_ar": [
            "عنوان محسّن للـ SEO",
            "ملخص محدد للمسؤولين",
            "غني بالكلمات المفتاحية",
            "مبني حسب عدد الحروف"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "linkedin-optimization",
        "name": "LinkedIn Profile Makeover",
        "price": 10,
        "category": "linkedin",
        "description": "Full LinkedIn profile optimization — headline, about, experience, skills, recommendations",
        "delivery": "24 hours",
        "features": [
            "Headline rewrite (SEO)",
            "About section overhaul",
            "Experience bullets optimized",
            "Skill endorsements strategy"
        ],
        "what_they_get": "Complete profile rewrite document + implementation guide you can copy-paste",
        "name_ar": "تحسين ملف لينكد إن الكامل",
        "description_ar": "تطوير كامل لحسابك: العنوان، نبذة عنك، قسم الخبرات، المهارات والتوصيات",
        "features_ar": [
            "إعادة كتابة العنوان (SEO)",
            "تحديث قسم About",
            "تحسين نقاط الخبرة",
            "استراتيجية تثبيت المهارات"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "linkedin-banner-design",
        "name": "Custom LinkedIn Banner Asset",
        "price": 6,
        "category": "linkedin",
        "description": "Professional 1584x396 custom header banner tailored to your industry",
        "delivery": "instant",
        "features": [
            "Industry branding",
            "Custom value proposition text",
            "HD PNG & JPG format",
            "Mobile & Desktop tested"
        ],
        "what_they_get": "3 high-resolution custom LinkedIn header banner images",
        "name_ar": "تصاميم غلاف (Banner) احترافية",
        "description_ar": "غلاف عصري بمقاس 1584x396 يعكس هويتك ومجالك المهني بأعلى جودة",
        "features_ar": [
            "هوية بصرية لمجالك",
            "نص قيمة مضافة مخصص",
            "صيغ HD PNG & JPG",
            "مفحوص للكمبيوتر والجوال"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "linkedin-content-30d",
        "name": "30 Days LinkedIn Post Prompts",
        "price": 8,
        "category": "linkedin",
        "description": "30 thought-leadership post hooks, templates, and industry insights",
        "delivery": "instant",
        "features": [
            "Viral hook formulas",
            "Industry story prompts",
            "Call to action endings",
            "Hashtag strategy"
        ],
        "what_they_get": "30-day content calendar with copy-paste LinkedIn posts",
        "name_ar": "جدول منشورات 30 يوماً للينكد إن",
        "description_ar": "30 خطاف ومنشور جاهز للنسخ واللصق لبناء حضور مهني قوي وتفاعل عالي",
        "features_ar": [
            "صيغ الخطافات الأكثر انتشاراً",
            "نماذج قصص وتجارب",
            "خواتم تدعو للتفاعل",
            "استراتيجية الـ Hashtags"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "linkedin-recommendation",
        "name": "Recommendation Request Scripts",
        "price": 3,
        "category": "linkedin",
        "description": "Scripts & pre-written recommendation templates for managers & peers",
        "delivery": "instant",
        "features": [
            "Manager request script",
            "Peer exchange template",
            "Client review draft",
            "High credibility text"
        ],
        "what_they_get": "5 recommendation request templates and pre-drafted endorsement texts",
        "name_ar": "قوالب طلب وتقديم التوصيات",
        "description_ar": "رسائل ونصوص توصية جاهزة ومصممة لتبادل التوصيات مع المدرين والزملاء",
        "features_ar": [
            "رسالة طلب للمدير",
            "قالب التبادل مع الزملاء",
            "نص مراجعة العميل",
            "مصداقية عالية"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "linkedin-skills-audit",
        "name": "50 Skills Endorsement Strategy",
        "price": 4,
        "category": "linkedin",
        "description": "Reorder and pin top 50 in-demand skills on LinkedIn for Recruiter search rank",
        "delivery": "instant",
        "features": [
            "Recruiter search keyword match",
            "Top-3 pinned skills strategy",
            "Skill assessment quiz tips",
            "Endorsement boost checklist"
        ],
        "what_they_get": "Ranked list of 50 skills for your exact job title",
        "name_ar": "استراتيجية المهارات الـ 50 الأكثر طلباً",
        "description_ar": "ترتيب وتثبيت أفضل 50 مهارة في حسابك لرفع ظهورك في محركات بحث Recruiter",
        "features_ar": [
            "مطابقة كلمات مسؤولي التوظيف",
            "استراتيجية أفضل 3 مهارات",
            "نصائح اختبارات المهارة",
            "دليل زيادة التوصيات"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "linkedin-recruiter-beacon",
        "name": "LinkedIn Recruiter Search Booster",
        "price": 7,
        "category": "linkedin",
        "description": "Tweak Open to Work settings and hidden metadata to top Recruiter search queries",
        "delivery": "instant",
        "features": [
            "Open to Work stealth mode",
            "Recruiter filters alignment",
            "Location radius trick",
            "Salary expectation stealth"
        ],
        "what_they_get": "Step-by-step checklist to appear in 5x more recruiter searches",
        "name_ar": "تصدّر نتائج بحث مسؤولي التوظيف",
        "description_ar": "ضبط إعدادات Open to Work الخفية والميتا داتا لتظهر في أوائل نتائج التوظيف",
        "features_ar": [
            "وضع خفي لـ Open to Work",
            "تطابق مع فلاتر الشركات",
            "حيلة النطاق الجغرافي",
            "حماية خصوصية عملك الحالي"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "linkedin-ssi-score",
        "name": "SSI Score & Profile Authority Audit",
        "price": 3,
        "category": "linkedin",
        "description": "Analyze Social Selling Index (SSI) and unlock algorithm reach bottlenecks",
        "delivery": "instant",
        "features": [
            "SSI benchmark comparison",
            "Network quality score",
            "Engagement rate fix",
            "Algorithm penalty audit"
        ],
        "what_they_get": "Detailed SSI diagnostic report with actionable fix checklist",
        "name_ar": "تحليل مؤشر الفاعلية SSI والانتشار",
        "description_ar": "فحص درجة Social Selling Index ومعالجة حظر الخوارزميات لزيادة الانتشار",
        "features_ar": [
            "مقارنة مع متوسط السوق",
            "درجة جودة الشبكة",
            "إصلاح نسبة التفاعل",
            "كشف عقوبات الخوارزمية"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "linkedin-networking-dm",
        "name": "Recruiter DM Masterclass Scripts",
        "price": 4,
        "category": "linkedin",
        "description": "High-converting InMail and connection message templates for decision-makers",
        "delivery": "instant",
        "features": [
            "Cold InMail templates",
            "Post-application DM",
            "Alumni connection message",
            "Hiring manager intro"
        ],
        "what_they_get": "6 proven message templates with 40%+ response rates",
        "name_ar": "رسائل تواصل مباشرة مع مسؤولي التوظيف",
        "description_ar": "قوالب رسائل InMail وتواصل مباشرة تحقق نسب استجابة تتجاوز 40%",
        "features_ar": [
            "قوالب InMail باردة",
            "رسالة المتابعة بعد التقديم",
            "تواصل مع خريجي جامعتك",
            "رسالة مباشرة لمدير القسم"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "linkedin-creator-mode",
        "name": "Featured Section & Portfolio Setup",
        "price": 5,
        "category": "linkedin",
        "description": "Curate your Featured section with rich media, case studies, and links",
        "delivery": "instant",
        "features": [
            "Featured link curation",
            "Visual thumbnail optimization",
            "Portfolio attachment layout",
            "Lead magnet link"
        ],
        "what_they_get": "Step-by-step guide and graphics for a high-converting Featured section",
        "name_ar": "تنسيق قسم Featured واستعراض الأعمال",
        "description_ar": "ترتيب قسم Featured بروابط مرئية ومشاريع ونماذج تجذب الزوار فوراً",
        "features_ar": [
            "تنظيم الروابط المميزة",
            "تصاميم مصغرة جذابة",
            "عرض ملحقات الـ Portfolio",
            "رابط قمع التواصل"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "linkedin-alumni-connector",
        "name": "Alumni Network Map & Outreach Guide",
        "price": 5,
        "category": "linkedin",
        "description": "Identify university and past company alumni in your target companies",
        "delivery": "instant",
        "features": [
            "Alumni search filters",
            "Common ground opening lines",
            "Warm intro requests",
            "Relationship nurturing"
        ],
        "what_they_get": "Alumni mapping search strings + 3 connection templates",
        "name_ar": "شبكة خريجي الجامعة والزملاء",
        "description_ar": "استخراج زملاء الدراسة والعمل السابقين في الشركات المستهدفة للوصول الدافئ",
        "features_ar": [
            "فلاتر بحث الخريجين",
            "جمل افتتاحية المشترك",
            "طلب التوصية الدافئ",
            "بناء العلاقات المستدامة"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "linkedin-video-pitch",
        "name": "60-Second Video Pitch Script",
        "price": 6,
        "category": "linkedin",
        "description": "Script and teleprompter guide for a profile intro video / elevator pitch",
        "delivery": "instant",
        "features": [
            "60s hook structure",
            "Core value pitch",
            "Lighting & audio tips",
            "Teleprompter scrolling text"
        ],
        "what_they_get": "Custom 60-second video script + recording tips for LinkedIn profile video",
        "name_ar": "فيديو التعريف البصري (60 ثانية)",
        "description_ar": "سيناريو ودليل تسجيل فيديو التعريف الشخصي المرفق بملف لينكد إن",
        "features_ar": [
            "هيكل الخطاف في 60 ثانية",
            "عرض القيمة المضافة",
            "نصائح الإضاءة والصوت",
            "نص مخصص للـ Teleprompter"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "email-template",
        "name": "Professional Cold Email Template",
        "price": 2,
        "category": "email",
        "description": "Custom-written cold email template for job applications that gets responses",
        "delivery": "instant",
        "features": [
            "Subject line A/B tested",
            "Body template",
            "Follow-up template",
            "Call-to-action optimized"
        ],
        "what_they_get": "3 email templates (initial + 2 follow-ups) in plain text + HTML format",
        "name_ar": "قوالب الإيميل البارد الاحترافية",
        "description_ar": "قوالب إيميل مصممة خصيصاً للتقديم على الوظائف وتحقيق نسب استجابة عالية",
        "features_ar": [
            "عنوان إيميل موثوق A/B",
            "محتوى الرسالة",
            "رسائل المتابعة",
            "دعوة لاتخاذ إجراء قاطعة"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "followup-sequence",
        "name": "Automated Follow-up Sequence",
        "price": 5,
        "category": "email",
        "description": "3-email automated follow-up sequence sent over 30 days after each application",
        "delivery": "instant",
        "features": [
            "3 professionally written emails",
            "Timed at 7/14/30 days",
            "Tracked opens/clicks",
            "A/B tested subject lines"
        ],
        "what_they_get": "Lifetime automated follow-ups for ALL your applications",
        "name_ar": "تسلسل المتابعة التلقائي (30 يوماً)",
        "description_ar": "سلسلة من 3 إيميلات متابعة آلية تُرسل على مدار 30 يوماً بعد التقديم",
        "features_ar": [
            "3 إيميلات احترافية",
            "مواعيد 7 / 14 / 30 يوماً",
            "تتبع فتح الإيميلات",
            "عنوان A/B اختبار"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "cold-email-hiring-manager",
        "name": "Hiring Manager Email Finder & Pitch",
        "price": 6,
        "category": "email",
        "description": "Direct email address lookup and tailored pitch for your target department head",
        "delivery": "24 hours",
        "features": [
            "Verified email address",
            "Direct department head pitch",
            "Pain-point trigger line",
            "Zero-bounce guarantee"
        ],
        "what_they_get": "Verified direct email + custom pitch for your target hiring manager",
        "name_ar": "استخراج إيميل وتوجيه رسالة لمدير القسم",
        "description_ar": "استخراج الإيميل المباشر لمدير القسم وكتابة رسالة موجزة تحل نقاط ألم فريقه",
        "features_ar": [
            "إيميل موثق لمدير القسم",
            "محتوى مباشر غير مكرر",
            "تحفيز الاستجابة",
            "ضمان عدم الارتداد"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "email-domain-warmup",
        "name": "Custom Email Domain Warmup Guide",
        "price": 8,
        "category": "email",
        "description": "Set up SPF, DKIM, DMARC, and warmup protocol to avoid spam filters",
        "delivery": "instant",
        "features": [
            "DNS record setup guide",
            "Spam trigger word list",
            "Deliverability audit",
            "Daily sending limits"
        ],
        "what_they_get": "Step-by-step deliverability guide + 100 spam words to avoid",
        "name_ar": "تهيئة دومين الإيميل وتجنب الـ Spam",
        "description_ar": "إعداد إعدادات SPF و DKIM و DMARC لتصل رسائلك لصندوق الوارد الرئيسي",
        "features_ar": [
            "إعدادات الـ DNS",
            "قائمة الكلمات المحظورة",
            "فحص الموثوقية",
            "حدود الإرسال اليومية"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "recruiter-email-blast",
        "name": "50 Niche Recruiter Emails",
        "price": 10,
        "category": "email",
        "description": "Hand-picked verified email directory of 50 active headhunters in your industry",
        "delivery": "24 hours",
        "features": [
            "50 verified corporate emails",
            "Industry matched",
            "Direct contact names",
            "Pre-formatted mail merge CSV"
        ],
        "what_they_get": "CSV file with 50 recruiter emails + personalized mail merge script",
        "name_ar": "50 إيميل موثوق لمسؤولي التوظيف",
        "description_ar": "دليل محدد يحتوي على 50 إيميل مباشر لمسؤولي التوظيف في مجالك وموقعك",
        "features_ar": [
            "50 إيميل شركات موثق",
            "مطابق لمجالك",
            "أسماء الموظفين المباشرين",
            "ملف CSV جاهز للإرسال"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "networking-plan",
        "name": "Personalized Networking Plan",
        "price": 8,
        "category": "email",
        "description": "Custom networking strategy with target companies, events, and connection scripts",
        "delivery": "24 hours",
        "features": [
            "Target company list (20+)",
            "LinkedIn connection scripts",
            "Industry event calendar",
            "Referral request templates"
        ],
        "what_they_get": "PDF networking plan with 20+ target companies, 5 connection scripts, event calendar",
        "name_ar": "خطة شبكة العلاقات المهنية",
        "description_ar": "استراتيجية بناء علاقات مع 20+ شركة مستهدفة وقوالب طلب التوصية",
        "features_ar": [
            "قائمة الشركات (20+)",
            "رسائل لينكد إن",
            "تقويم الفعاليات",
            "نماذج طلب التوصية"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "referral-ask-script",
        "name": "Employee Referral Request Playbook",
        "price": 4,
        "category": "email",
        "description": "Ask current employees for internal referral links without sounding awkward",
        "delivery": "instant",
        "features": [
            "Cold employee script",
            "Warm acquaintance script",
            "Mutual connection intro",
            "Referral bonus incentive line"
        ],
        "what_they_get": "4 referral request scripts with 50%+ success rate",
        "name_ar": "طلب التوصية الداخلية من الموظفين",
        "description_ar": "كيف تطلب من موظفي الشركات التوصية بحسابك داخلياً بدون أحراج",
        "features_ar": [
            "سيناريو موظف غريب",
            "معارف سابقين",
            "تواصل عبر واسطة",
            "تحفيز مكافأة التوصية"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "informational-interview",
        "name": "Informational Interview Request Pack",
        "price": 4,
        "category": "email",
        "description": "Ask industry leaders for 15-minute advice chats that turn into job offers",
        "delivery": "instant",
        "features": [
            "Advice request email",
            "15-min call outline",
            "Question list (10 questions)",
            "Thank-you follow-up"
        ],
        "what_they_get": "Complete informational interview toolkit",
        "name_ar": "طلب واستراتيجية المقابلات الاستكشافية",
        "description_ar": "طلب مكالمات استشارية مدتها 15 دقيقة مع قادة المجال تتحول لفرص عمل",
        "features_ar": [
            "إيميل طلب النصيحة",
            "هيكل مكالمة 15 دقيقة",
            "10 أسئلة ذكية",
            "إيميل الشكر والمتابعة"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "post-interview-thankyou",
        "name": "Post-Interview Thank You & Value Add",
        "price": 3,
        "category": "email",
        "description": "High-impact thank you email sent within 24 hours of interview to seal the offer",
        "delivery": "instant",
        "features": [
            "Key discussion recap",
            "Additional value proposal",
            "Interview feedback fix",
            "Next steps nudge"
        ],
        "what_they_get": "3 thank you email templates for phone, technical & final round interviews",
        "name_ar": "رسالة الشكر وتثبيت الانطباع بعد المقابلة",
        "description_ar": "رسالة شكر عالية التأثير تُرسل خلال 24 ساعة لترجيح كفتك وحسم عرض العمل",
        "features_ar": [
            "ملخص النقاط القوية",
            "تقديم قيمة إضافية",
            "استدراك أخطاء المقابلة",
            "دفعة الخطوة التالية"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "rejection-turnaround",
        "name": "Rejection Email Turnaround Script",
        "price": 3,
        "category": "email",
        "description": "Turn a rejection email into a future opportunity or referral to another team",
        "delivery": "instant",
        "features": [
            "Gracious response script",
            "Feedback request line",
            "Future pipeline request",
            "Talent pool tag"
        ],
        "what_they_get": "2 rejection reply scripts designed to keep doors open",
        "name_ar": "تحويل إيميل الرفض إلى فرصة مستقبلية",
        "description_ar": "الرد الاحترافي على رسائل الاعتذار لإبقائك في قائمة الترشيحات المستقبلية",
        "features_ar": [
            "رد راقي ومرحب",
            "طلب التغذية الراجعة",
            "طلب إبقائك في الأرشيف",
            "الترشيح لفريق آخر"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "agency-headhunter-list",
        "name": "Top 20 Headhunter Agencies Pack",
        "price": 7,
        "category": "email",
        "description": "Direct portal submit links and agency contacts for executive search firms",
        "delivery": "instant",
        "features": [
            "Top 20 regional agencies",
            "Direct portal submit URLs",
            "Senior consultant contacts",
            "Niche sector tag"
        ],
        "what_they_get": "Directory of 20 top recruitment agencies + submission instructions",
        "name_ar": "دليل أفضل 20 شركة توظيف تنفيذية",
        "description_ar": "روابط التقديم المباشرة ومسؤولي التوظيف بأكبر شركات الهيدهانتر الإقليمية",
        "features_ar": [
            "أفضل 20 شركة توظيف",
            "روابط رفع السيرة المباشرة",
            "أسماء المستشارين",
            "تصنيف حسب القطاع"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "coffee-chat-playbook",
        "name": "Coffee Chat Agenda & Script Pack",
        "price": 4,
        "category": "email",
        "description": "How to structure informal coffee chats to get internal job recommendations",
        "delivery": "instant",
        "features": [
            "Conversation starter scripts",
            "Transitioning to job talk",
            "Closing referral ask",
            "Follow-up note"
        ],
        "what_they_get": "1-page coffee chat playbook with scripts and question bank",
        "name_ar": "سيناريو ودليل جلسات القهوة التوجيهية",
        "description_ar": "كيف تدير اللقاءات غير الرسمية للحصول على ترشيحات توظيف داخلية",
        "features_ar": [
            "افتتاحية الحوار",
            "الانتقال للحديث عن الوظيفة",
            "طلب التوصية بلباقة",
            "رسالة الشكر المباشرة"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "interview-prep",
        "name": "AI Interview Coach & Mock Session",
        "price": 12,
        "category": "interview",
        "description": "AI-powered mock interview with real questions tailored to your target role",
        "delivery": "instant",
        "features": [
            "Role-specific questions (20+)",
            "AI evaluates responses",
            "Score with improvement tips",
            "Behavioral + technical"
        ],
        "what_they_get": "20+ practice questions with AI evaluation, personalized improvement plan, confidence score",
        "name_ar": "مدرب المقابلات الذكي (AI Interview Coach)",
        "description_ar": "مقابلة تجريبية بالذكاء الاصطناعي مع أسئلة حقيقية مخصصة لمجالك وشاغرك",
        "features_ar": [
            "20+ سؤال مخصص لمجالك",
            "تقييم الإجابات بالذكاء",
            "درجات وتوصيات تحسين",
            "أسئلة سلوكية وتقنية"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "star-method-builder",
        "name": "10 STAR Behavioral Story Frameworks",
        "price": 6,
        "category": "interview",
        "description": "Format your real accomplishments into Situation-Task-Action-Result stories",
        "delivery": "instant",
        "features": [
            "Leadership story template",
            "Conflict resolution story",
            "Failure & recovery story",
            "Project success story"
        ],
        "what_they_get": "10 structured STAR story templates filled with your career data",
        "name_ar": "صياغة 10 قصص إنجاز وفق نموذج STAR",
        "description_ar": "تحويل إنجازاتك الحقيقية إلى قصص سلوكية ممتازة (الموقف، المهارة، الفعل، النتيجة)",
        "features_ar": [
            "قصة القيادة والتوجيه",
            "قصة حل النزاعات",
            "قصة التعامل مع الفشل",
            "قصة نجاح المشروع"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "technical-interview-prep",
        "name": "Role Technical Question Bank",
        "price": 8,
        "category": "interview",
        "description": "50 role-specific technical questions & model answers for software, data, finance",
        "delivery": "instant",
        "features": [
            "50 technical Q&As",
            "System design concepts",
            "Industry terminology",
            "Common coding/analytical tests"
        ],
        "what_they_get": "PDF question bank with answers and key technical concepts",
        "name_ar": "بنك أسئلة مقابلات تقنية مخصصة",
        "description_ar": "50 سؤالاً وإجابة نموذجية في البرمجة، البيانات، المالية، والهندسة",
        "features_ar": [
            "50 سؤال وإجابة تقنية",
            "مفاهيم معمارية النظام",
            "مصطلحات التخصص",
            "اختبارات التحليل والشيفرة"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "executive-interview-strategy",
        "name": "Executive 30-60-90 Day Plan Deck",
        "price": 15,
        "category": "interview",
        "description": "Impress interviewers with a professional 30-60-90 day strategic onboarding plan",
        "delivery": "24 hours",
        "features": [
            "Phase 1 (Learn/Audit)",
            "Phase 2 (Execute)",
            "Phase 3 (Optimize/Scale)",
            "PowerPoint + PDF template"
        ],
        "what_they_get": "Custom 30-60-90 day plan presentation deck in PPTX & PDF format",
        "name_ar": "خطة عمل 30-60-90 يوماً للمناصب العليا",
        "description_ar": "العرض التقديمي الاستراتيجي الذي يبهر لجنة المقابلات الإدارية والتنفيذية",
        "features_ar": [
            "المرحلة 1 (الاستكشاف والتدقيق)",
            "المرحلة 2 (التنفيذ)",
            "المرحلة 3 (التطوير والتوسع)",
            "صيغ PPTX + PDF"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "system-design-interview",
        "name": "System Design & Case Study Kit",
        "price": 9,
        "category": "interview",
        "description": "Frameworks for tackling system design or business case study interviews",
        "delivery": "instant",
        "features": [
            "Scalability bottlenecks",
            "Database selection matrix",
            "API architecture diagramming",
            "Business case math"
        ],
        "what_they_get": "System design cheat sheet + 5 worked case study examples",
        "name_ar": "دليل المقابلات الهندسية ودراسات الحالة",
        "description_ar": "نماذج وتكتيكات حل مقابلات معمارية الأنظمة ودراسات الجدوى الاقتصادية",
        "features_ar": [
            "معالجة التوسع والأداء",
            "اختيار قواعد البيانات",
            "تخطيط الـ APIs",
            "رياضيات دراسات الحالة"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "culture-fit-audit",
        "name": "Target Company Culture & Values Guide",
        "price": 4,
        "category": "interview",
        "description": "Decode target company leadership principles (Amazon, Google, Aramco, etc.)",
        "delivery": "instant",
        "features": [
            "Leadership principles mapping",
            "Sample questions asked",
            "Model answers per principle",
            "Red-flag traps"
        ],
        "what_they_get": "Company culture prep guide with core values story match",
        "name_ar": "دليل ثقافة وقيم الشركات الكبرى",
        "description_ar": "فك شفرة قيم القيادة في الشركات العالمية والإقليمية (أرامكو، غوغل، أمازون)",
        "features_ar": [
            "ربط قيم القيادة بخبرتك",
            "نماذج الأسئلة المتوقعة",
            "الإجابات النموذجية",
            "كشف فخاخ المقابلين"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "interviewer-stalking-report",
        "name": "Interviewer 360 Profile Audit",
        "price": 5,
        "category": "interview",
        "description": "Deep background check on your interviewers: past papers, career history & interests",
        "delivery": "24 hours",
        "features": [
            "Career trajectory analysis",
            "Shared connections & interests",
            "Publication/talk highlights",
            "Personalized conversation starters"
        ],
        "what_they_get": "1-page briefing report on your interview panel",
        "name_ar": "تقرير شامل عن خلفية المقابلين",
        "description_ar": "تدقيق كامل حول مسؤولي المقابلة: خلفيتهم المهنية، أوراقهم، ومجالات اهتمامهم",
        "features_ar": [
            "مسارهم المهني السابق",
            "الاهتمامات والروابط المشتركة",
            "أبرز الإنجازات والمقالات",
            "مواضيع لفتح الحوار"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "salary-question-deflection",
        "name": "Screening Call Salary Scripts",
        "price": 3,
        "category": "interview",
        "description": "Deflect early salary questions on recruiter phone screens without anchoring low",
        "delivery": "instant",
        "features": [
            "5 deflection scripts",
            "Market range response",
            "Employer-first quote script",
            "Confidence posture tips"
        ],
        "what_they_get": "5 script options to handle initial salary expectations phone call",
        "name_ar": "الإجابة عن توقعات الراتب في الاتصال الأول",
        "description_ar": "كيف تجيب عن سؤال الراتب المتوقع في الاتصال الأولي بدون تحديد رقم منخفض",
        "features_ar": [
            "5 سيناريوهات إجابة",
            "عرض نطاق السوق",
            "حيلة رد السؤال للشركة",
            "ثقة وتوازن في التحدث"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "tell-me-about-yourself",
        "name": "90-Sec 'Tell Me About Yourself' Pitch",
        "price": 4,
        "category": "interview",
        "description": "Perfect 90-second elevator pitch answering the #1 most asked interview question",
        "delivery": "instant",
        "features": [
            "Present-Past-Future framework",
            "Hook sentence",
            "Metric highlights",
            "Seamless transition to job"
        ],
        "what_they_get": "Custom 90-second intro pitch tailored to your resume",
        "name_ar": "صياغة إجابة 'عرّف عن نفسك' (90 ثانية)",
        "description_ar": "الإجابة النموذجية القاطعة لأهم سؤال في المقابلة الوظيفية",
        "features_ar": [
            "هيكل (الحاضر - الماضي - المستقبل)",
            "جملة الخطاف القوية",
            "إبراز الأرقام",
            "ربط سلس بالشاغر"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "weakness-strength-answers",
        "name": "Weakness & Failure Story Scripts",
        "price": 4,
        "category": "interview",
        "description": "Answer 'What is your greatest weakness?' without sounding fake or disqualifying yourself",
        "delivery": "instant",
        "features": [
            "Real weakness framing",
            "Growth & mitigation steps",
            "Failure recovery story",
            "Authenticity calibration"
        ],
        "what_they_get": "3 polished answers for weakness and failure interview questions",
        "name_ar": "صياغة الإجابة عن نقاط الضعف والفشل",
        "description_ar": "كيف تجيب عن نقاط ضعفك بدون تصنع وبدون استبعادك من المنافسة",
        "features_ar": [
            "صياغة نقاط ضعف حقيقية",
            "خطوات المعالجة والتعلم",
            "قصة استدراك الخطأ",
            "توازن المصداقية"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "mock-interview-feedback",
        "name": "Recorded Mock Interview AI Rubric",
        "price": 10,
        "category": "interview",
        "description": "Upload audio or video recording of your practice interview for AI speech & content analysis",
        "delivery": "instant",
        "features": [
            "Filler word frequency",
            "Pacing & tone score",
            "STAR compliance check",
            "Confidence metrics"
        ],
        "what_they_get": "Detailed AI rubric feedback report with timing and speech analysis",
        "name_ar": "تحليل أداء المقابلة بالذكاء الاصطناعي",
        "description_ar": "ارفع تسجيل صوتي أو فيديو لمقابلتك التجريبية لتحصل على تقرير تحليل نبرة الصوت والمحتوى",
        "features_ar": [
            "تكرار كلمات الحشو",
            "درجة السرعة والنبرة",
            "التزام نموذج STAR",
            "مؤشرات الثقة بالنفس"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "on-site-final-round",
        "name": "Final Round Presentation Kit",
        "price": 12,
        "category": "interview",
        "description": "Prep kit for executive presentations, board panels, and final round interviews",
        "delivery": "24 hours",
        "features": [
            "Presentation structure",
            "Q&A handling matrix",
            "Executive presence tips",
            "Follow-up strategy"
        ],
        "what_they_get": "Final round survival guide + presentation template",
        "name_ar": "حقيبة تحضير المقابلة النهائية والعروض",
        "description_ar": "دليل المقابلات النهائية أمام مجلس الإدارة والإدارة العليا",
        "features_ar": [
            "هيكل العرض التقديمي",
            "التعامل مع أسئلة التحدي",
            "نصائح الحضور التنفيذي",
            "استراتيجية المتابعة"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "salary-benchmark",
        "name": "Salary Benchmark Report",
        "price": 7,
        "category": "salary",
        "description": "Personalized salary benchmark report for your role, experience, and location (Gulf/MENA focus)",
        "delivery": "24 hours",
        "features": [
            "Role-specific salary data (10+ companies)",
            "Experience-adjusted range",
            "Location comparison (5+ cities)",
            "Benefits value analysis"
        ],
        "what_they_get": "PDF salary report with range, percentiles, company comparison, and negotiation target number",
        "name_ar": "تقرير مقارنة الراتب المستحق بالخليج",
        "description_ar": "تقرير راتب مخصص لمسمتك وخبرتك وموقعك الجغرافي (تركيز على دول الخليج)",
        "features_ar": [
            "بيانات الراتب لـ 10+ شركات",
            "تعديل حسب سنوات الخبرة",
            "مقارنة المدن (دبي، الرياض...)",
            "قيم البدلات والمزايا"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "salary-negotiation",
        "name": "Salary Negotiation Playbook",
        "price": 15,
        "category": "salary",
        "description": "Data-driven salary negotiation strategy with scripts for every stage",
        "delivery": "24 hours",
        "features": [
            "Market salary data (Gulf/MENA)",
            "Negotiation scripts (5 stages)",
            "Counter-offer strategies",
            "Benefits negotiation tips"
        ],
        "what_they_get": "Complete negotiation playbook with scripts, salary data for 10+ roles, email templates",
        "name_ar": "كتاب سيناريوهات وتكتيكات رفع الراتب",
        "description_ar": "استراتيجية تفاوض مبنية على البيانات مع سيناريوهات كاملة لكل مرحلة",
        "features_ar": [
            "بيانات رواتب الخليج 2026",
            "سيناريوهات 5 مراحل",
            "تكتيكات العروض المضادة",
            "تفاوض بدلات السكن والتعليم"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "equity-stock-analysis",
        "name": "Stock Options & RSUs Explainer",
        "price": 10,
        "category": "salary",
        "description": "Evaluate tech equity grants (RSUs, Options, Vesting schedules & Valuation)",
        "delivery": "24 hours",
        "features": [
            "Option strike price evaluation",
            "Vesting schedule math",
            "Tax impact summary",
            "Negotiating more equity"
        ],
        "what_they_get": "Equity analysis report calculating true dollar value of offer",
        "name_ar": "تقييم الأسهم والحصص (RSUs/Options)",
        "description_ar": "حساب القيمة الحقيقية للأسهم وحصص الملكية والجداول الزمنية للاستحقاق",
        "features_ar": [
            "تقييم سعر ممارسة الخيار",
            "جدول استحقاق الاستثمار",
            "الأثر الضريبي والمالي",
            "تفاوض زيادة الحصص"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "signing-bonus-script",
        "name": "Signing Bonus Request Scripts",
        "price": 5,
        "category": "salary",
        "description": "Request a sign-on bonus or relocation stipend to cover lost unvested equity",
        "delivery": "instant",
        "features": [
            "Unvested equity clawback pitch",
            "Relocation expense gap line",
            "Immediate bonus request script",
            "HR counter script"
        ],
        "what_they_get": "3 signing bonus request scripts + email draft",
        "name_ar": "طلب مكافأة توقيع العقد وبدل الانتقال",
        "description_ar": "طلب مكافأة انضمام فورية لتغطية الحصص المفقودة أو تكاليف الانقال",
        "features_ar": [
            "تعويض الحصص غير المستحقة",
            "تغطية فارق تكلفة الانتقال",
            "سيناريو المكافأة الفورية",
            "ردود على اعتراض الـ HR"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "counter-offer-evaluator",
        "name": "Job Offer A vs B Decision Matrix",
        "price": 8,
        "category": "salary",
        "description": "Compare multiple job offers evaluating salary, bonus, perks, growth & commute",
        "delivery": "instant",
        "features": [
            "Weighted decision scoring",
            "Total compensation calculator",
            "Work-life balance index",
            "Risk assessment"
        ],
        "what_they_get": "Excel/PDF decision matrix showing mathematically superior offer",
        "name_ar": "مصفوفة المفاضلة بين عروض العمل",
        "description_ar": "مقارنة بين أكثر من عرض عمل بناءً على الراتب، البدلات، النمو، والراحة النفسية",
        "features_ar": [
            "تقييم ترجيحي للنقاط",
            "حساب إجمالي التعويضات",
            "مؤشر التوازن والراحة",
            "تقييم مخاطر الشركة"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "remote-pay-parity",
        "name": "Remote Location Salary Calculator",
        "price": 6,
        "category": "salary",
        "description": "Calculate remote pay adjustments when working for US/EU firms from abroad",
        "delivery": "instant",
        "features": [
            "Cost of living offset",
            "USD/EUR to local currency rate",
            "Tax jurisdiction impact",
            "Pay parity pitch"
        ],
        "what_they_get": "Remote salary benchmark report with parity negotiation script",
        "name_ar": "حساب راتب العمل عن بعد مع الشركات الأجنبية",
        "description_ar": "حساب الراتب العادل عند العمل مع شركات أمريكية أو أوروبية من دولتك",
        "features_ar": [
            "فارق تكلفة المعيشة",
            "تحويل العملات USD/EUR",
            "الأثر الضريبي المحلي",
            "تكتيك طلب راتب عادل"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "annual-review-raise",
        "name": "Performance Review Raise Pitch",
        "price": 9,
        "category": "salary",
        "description": "Ask for a 15-30% internal raise or promotion at your current company",
        "delivery": "24 hours",
        "features": [
            "Accomplishment brag sheet",
            "Market salary comparison",
            "Business impact ROI deck",
            "1-on-1 meeting script"
        ],
        "what_they_get": "Raise request package: brag sheet + market proof + meeting script",
        "name_ar": "صياغة طلب الترقية وزيادة الراتب السنوية",
        "description_ar": "طلب زيادة راتب بنسبة 15-30% أو ترقية في عملك الحالي بناءً على إنجازاتك",
        "features_ar": [
            "وثيقة الإنجازات والـ ROI",
            "مقارنة رواتب السوق",
            "عرض القيمة المضافة",
            "سيناريو الاجتماع الفردي"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "benefits-perks-audit",
        "name": "Benefits & Perks Benchmark Guide",
        "price": 5,
        "category": "salary",
        "description": "Benchmark health insurance, education allowances, housing & flight tickets in Gulf",
        "delivery": "instant",
        "features": [
            "Family health coverage check",
            "Child education allowance norm",
            "Annual flight ticket allowance",
            "Housing stipend benchmarks"
        ],
        "what_they_get": "Gulf benefits benchmark checklist to negotiate additional perks",
        "name_ar": "مقارنة بدلات السكن، التعليم والتأمين",
        "description_ar": "مقارنة بدلات التأمين الصحي العائلي، تعليم الأطفال، وتذاكر الطيران بالخليج",
        "features_ar": [
            "فحص التأمين الصحي العائلي",
            "معايير بدلات المدارس",
            "بدل تذاكر الطيران السنوية",
            "بدل السكن والنقل"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "offer-letter-contract-review",
        "name": "Employment Contract Clause Audit",
        "price": 12,
        "category": "salary",
        "description": "Identify non-compete, notice period, and IP clause red flags before signing",
        "delivery": "24 hours",
        "features": [
            "Non-compete clause check",
            "Notice period sanity check",
            "IP assignment clause check",
            "Termination clause audit"
        ],
        "what_they_get": "Contract audit report pointing out 5+ clauses to clarify or amend",
        "name_ar": "فحص بنود عقود التوظيف وتحديد المخاطر",
        "description_ar": "اكتشاف شروط عدم المنافسة، فترة الإخطار، والبنود المجحفة قبل التوقيع",
        "features_ar": [
            "فحص الشرط الجزائي وعدم المنافسة",
            "مدة فترة الإخطار",
            "الملكية الفكرية",
            "بنود إنهاء الخدمة"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "severance-package-negotiator",
        "name": "Severance & Exit Negotiation Guide",
        "price": 10,
        "category": "salary",
        "description": "Negotiate additional months of pay and health coverage during company exits",
        "delivery": "24 hours",
        "features": [
            "Severance pay multiplier",
            "Health insurance extension",
            "COBRA / Expat coverage",
            "Positive reference agreement"
        ],
        "what_they_get": "Severance request playbook with negotiation email templates",
        "name_ar": "تفاوض مكافأة نهاية الخدمة والاستقالة",
        "description_ar": "المطالبة بأشهر إضافية وتمديد التأمين الصحي عند مغادرة الشركة",
        "features_ar": [
            "مضاعف مكافأة الخدمة",
            "تمديد التأمين الصحي",
            "التغطية الطبية بالخارج",
            "اتفاقية التوصية الإيجابية"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "gulf-tech-hiring-map",
        "name": "UAE & KSA Hiring Directory",
        "price": 12,
        "category": "gulf",
        "description": "Directory of 100+ active hiring companies in Dubai, Abu Dhabi & Riyadh",
        "delivery": "instant",
        "features": [
            "100+ company profiles",
            "Direct HR career portal links",
            "Salary scale indicator",
            "Nitaqat & Saudization tags"
        ],
        "what_they_get": "Excel/CSV directory of 100+ Gulf hiring companies",
        "name_ar": "دليل 100+ شركة توظيف في الإمارات والسعودية",
        "description_ar": "دليل شامل لأكثر من 100 شركة توظّف حالياً في دبي، أبوظبي، والرياض",
        "features_ar": [
            "100+ شركة موثوقة",
            "روابط التقديم المباشرة",
            "مؤشر سلم الرواتب",
            "تصنيف السعودة والوطنية"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "saudi-vision-2030-jobs",
        "name": "Saudi Vision 2030 Jobs Access",
        "price": 10,
        "category": "gulf",
        "description": "Access job channels for NEOM, Qiddiya, Red Sea Project, and Diriyah Gate",
        "delivery": "instant",
        "features": [
            "Mega-project hiring portals",
            "Tier-1 contractor contacts",
            "Target skill list",
            "Vendor application links"
        ],
        "what_they_get": "Vision 2030 mega-project recruitment guide + 30 direct links",
        "name_ar": "بوابات التقديم لمشاريع رؤية السعودية 2030",
        "description_ar": "الوصول المباشر لقنوات توظيف نيوم، القدية، مشروع البحر الأحمر، وبوابة الدرعية",
        "features_ar": [
            "بوابات المشاريع الكبرى",
            "جهات المقاولة الرئيسية",
            "المهارات المطلوبة",
            "روابط تقديم الموردين"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "dubai-freezone-job-pack",
        "name": "Dubai Freezone Hiring Guide",
        "price": 8,
        "category": "gulf",
        "description": "DIFC, Internet City, Media City, and DMCC company hiring directory",
        "delivery": "instant",
        "features": [
            "Freezone company list",
            "Direct career pages",
            "Visa sponsorship tag",
            "Industry categorization"
        ],
        "what_they_get": "50+ Dubai Freezone hiring contacts and career URLs",
        "name_ar": "دليل شركات المناطق الحرة في دبي",
        "description_ar": "دليل التوظيف لشركات DIFC، مدينة دبي للإعلام، مدينة دبي للإنترنت، و DMCC",
        "features_ar": [
            "قائمة شركات المناطق الحرة",
            "صفحات التوظيف المباشرة",
            "كفالة الفيزا",
            "تصنيف حسب القطاع"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "gulf-salary-tax-free",
        "name": "Gulf Tax-Free Calculator & Cost",
        "price": 5,
        "category": "gulf",
        "description": "Calculate true take-home pay comparing Western gross pay to Gulf tax-free net",
        "delivery": "instant",
        "features": [
            "Tax-free equivalent math",
            "Dubai vs Riyadh living costs",
            "Schooling & rent estimates",
            "Net savings projection"
        ],
        "what_they_get": "PDF financial comparison report between home country and Gulf offer",
        "name_ar": "حساب الراتب الصافي الخالي من الضرائب بالخليج",
        "description_ar": "مقارنة الراتب الإجمالي في الدول الغربية مع الراتب الصافي المعفي من الضريبة بالخليج",
        "features_ar": [
            "معادلة المعافاة الضريبية",
            "تكاليف المعيشة دبي vs الرياض",
            "تقدير الإيجار والمدارس",
            "توقع التوفير الصافي"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "qatar-kuwait-job-market",
        "name": "Qatar & Kuwait Job Market Directory",
        "price": 8,
        "category": "gulf",
        "description": "Recruitment channels for energy, healthcare, construction & tech in Qatar/Kuwait",
        "delivery": "instant",
        "features": [
            "Qatar Energy & Qatar Airways links",
            "Kuwait Oil & Tech links",
            "Recruiter contacts",
            "Salary expectations"
        ],
        "what_they_get": "30+ verified hiring portals for Qatar and Kuwait",
        "name_ar": "قنوات التوظيف في قطر والكويت",
        "description_ar": "دليل التوظيف في قطاعات الطاقة، الصحة، الإنشاءات، والتكنولوجيا بقطر والكويت",
        "features_ar": [
            "روابط قطر للطاقة والخطوط القطرية",
            "روابط نفط الكويت والتكنولوجيا",
            "جهات التوظيف",
            "رواتب متوقعة"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "arabic-formal-cover-letter",
        "name": "Gulf Arabic Formal Cover Letter",
        "price": 5,
        "category": "gulf",
        "description": "Professional formal Arabic application letter tailored for GCC government & corporate roles",
        "delivery": "instant",
        "features": [
            "Formal Gulf honorifics",
            "High credibility Arabic pitch",
            "ATS-compatible Arabic text",
            "PDF & Word export"
        ],
        "what_they_get": "Custom 1-page formal Arabic cover letter",
        "name_ar": "خطابات رسمية للقطاع الحكومي بالخليج",
        "description_ar": "خطاب تقديم رسمي باللغة العربية مخصص للجهات الحكومية والشركات الكبرى بالخليج",
        "features_ar": [
            "الألقاب الرسمية الخليجية",
            "لغة رصينة عالية المصداقية",
            "نص عربي مقروء للـ ATS",
            "تصدير PDF + Word"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "eu-blue-card-job-finder",
        "name": "European Tech Visa Jobs Pack",
        "price": 10,
        "category": "gulf",
        "description": "Directory of EU companies offering EU Blue Card & Visa Sponsorship (Germany, Netherlands)",
        "delivery": "instant",
        "features": [
            "EU Blue Card eligible firms",
            "English-speaking role tags",
            "Direct application links",
            "Salary threshold guide"
        ],
        "what_they_get": "50+ European hiring companies with active visa sponsorship",
        "name_ar": "دليل شركات ألمانيا وهولندا الكافلة للفيزا",
        "description_ar": "دليل الشركات الأوروبية التي تقدم فيزا العمل EU Blue Card وتدعم الانتقال",
        "features_ar": [
            "شركات داعمة لـ EU Blue Card",
            "وظائف باللغة الإنجليزية",
            "روابط التقديم المباشرة",
            "حدود الراتب الأدنى"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "us-h1b-sponsor-list",
        "name": "US H1B Visa Sponsor Directory",
        "price": 9,
        "category": "gulf",
        "description": "Database of US tech companies with 100+ approved H1B visa petitions in 2025/2026",
        "delivery": "instant",
        "features": [
            "Approved H1B company list",
            "Role titles sponsored",
            "Location breakdown",
            "Green card processing history"
        ],
        "what_they_get": "CSV list of 100+ top US H1B sponsoring employers",
        "name_ar": "دليل الشركات الأمريكية الداعمة لفيزا H1B",
        "description_ar": "قاعدة بيانات الشركات الأمريكية التي أصدرت 100+ فيزا H1B موافق عليها في 2025/2026",
        "features_ar": [
            "قائمة الشركات المعتمدة",
            "المسميات الوظيفية المدعومة",
            "الولايات والمدن",
            "سجل التقديم للـ Green Card"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "uk-skilled-worker-sponsor",
        "name": "UK Skilled Worker Sponsor Database",
        "price": 9,
        "category": "gulf",
        "description": "Searchable list of licensed UK Home Office visa sponsor companies",
        "delivery": "instant",
        "features": [
            "UK Home Office licensed firms",
            "Going rate salary check",
            "Shortage occupation tag",
            "Direct career URLs"
        ],
        "what_they_get": "Filtered list of UK licensed sponsors in your industry",
        "name_ar": "قاعدة بيانات شركات الكفالة البريطانية",
        "description_ar": "قائمة بريطانية معتمدة من وزارة الداخلية للشركات المرخصة لكفالة الفيزا",
        "features_ar": [
            "شركات مرخصة بريطانية",
            "فحص حد الراتب الأدنى",
            "الوظائف المطلوبة بالسوق",
            "روابط التقديم المباشرة"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "canada-express-entry-cv",
        "name": "Canadian Format Resume & NOC Matcher",
        "price": 7,
        "category": "gulf",
        "description": "Format your resume to Canadian standards and map your NOC/TEER code for Express Entry",
        "delivery": "instant",
        "features": [
            "Canadian resume standards",
            "NOC/TEER code assignment",
            "CRS score optimization tips",
            "Work experience bullet rewrites"
        ],
        "what_they_get": "Canadian styled resume + NOC code assignment sheet",
        "name_ar": "تهيئة السيرة للنسق الكندي وتحديد رمز NOC",
        "description_ar": "تعديل سيرتك الذاتية حسب المعايير الكندية وتحديد رمز NOC/TEER للهجرة",
        "features_ar": [
            "معايير السيرة الكندية",
            "تحديد رمز NOC/TEER",
            "تحسين نقاط CRS",
            "صياغة أفعال الخبرة"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "australia-skills-assessment",
        "name": "Australian Skilled Migration CV Audit",
        "price": 8,
        "category": "gulf",
        "description": "Audit your CV against ACS/EA/VETASSESS skills assessment criteria for Australia PR",
        "delivery": "24 hours",
        "features": [
            "ANZSCO code mapping",
            "Skills assessment checklist",
            "Reference letter guidelines",
            "Points calculator overview"
        ],
        "what_they_get": "Australia migration CV audit report + reference letter templates",
        "name_ar": "فحص السيرة الذاتية لمعادلة المهارات بأستراليا",
        "description_ar": "فحص سيرتك الذاتية حسب متطلبات ACS / Engineers Australia لمعادلة الهجرة",
        "features_ar": [
            "تحديد كود ANZSCO",
            "قائمة متطلبات المعادلة",
            "نماذج خطابات الخبرة",
            "حاسبة النقاط للهجرة"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "singapore-asia-exec-jobs",
        "name": "APAC & Singapore Hiring Pack",
        "price": 8,
        "category": "gulf",
        "description": "Directory of tech & regional headquarters hiring in Singapore & Hong Kong",
        "delivery": "instant",
        "features": [
            "EP (Employment Pass) rules check",
            "Singapore regional HQ list",
            "Direct recruiter URLs",
            "Salary benchmarks"
        ],
        "what_they_get": "30+ Singapore & APAC corporate hiring contacts",
        "name_ar": "دليل وظائف سنغافورة وشرق آسيا",
        "description_ar": "دليل المقرات الإقليمية والشركات التكنولوجية في سنغافورة وهونغ كونغ",
        "features_ar": [
            "فحص شروط تصريح العمل EP",
            "قائمة المقرات بسنغافورة",
            "جهات التوظيف المباشرة",
            "مقارنة الرواتب"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "remote-work-contractor",
        "name": "Global Remote Job Board Directory",
        "price": 7,
        "category": "visa",
        "description": "Access 30+ curated remote-first job boards and async hiring networks",
        "delivery": "instant",
        "features": [
            "30+ remote job portals",
            "Worldwide remote filter",
            "Async company tag",
            "USD/EUR salary indicator"
        ],
        "what_they_get": "Curated list of 30+ verified global remote job platforms",
        "name_ar": "دليل 30+ منصة توظيف عالمية عن بعد",
        "description_ar": "قائمة منسقة لأفضل 30 منصة توظيف تتيح التقديم على وظائف عن بعد برواتب عالمية",
        "features_ar": [
            "30+ منصة عمل عن بعد",
            "فلاتر التوظيف العالمي",
            "علامة العمل اللاتزامني",
            "مؤشر الرواتب USD/EUR"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "digital-nomad-visa",
        "name": "Digital Nomad Visa Setup Blueprint",
        "price": 8,
        "category": "visa",
        "description": "Requirements & step-by-step application guide for Spain, Portugal, UAE & Bali nomad visas",
        "delivery": "instant",
        "features": [
            "Income threshold comparison",
            "Tax residency rules",
            "Bank account requirements",
            "Document checklist"
        ],
        "what_they_get": "PDF Digital Nomad Visa guide for top 5 destination countries",
        "name_ar": "دليل فيزا الرحالة الرقمي (إسبانيا، البرتغال، دبي)",
        "description_ar": "الشروط والخطوات التفصيلية للتقديم على فيزا الإقامة عن بعد لـ 5 دول كبرى",
        "features_ar": [
            "مقارنة الحد الأدنى للدخل",
            "قواعد الإقامة الضريبية",
            "متطلبات الحساب البنكي",
            "قائمة الوثائق المطلوبة"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "relocation-cost-calculator",
        "name": "International Relocation Cost Guide",
        "price": 5,
        "category": "visa",
        "description": "Budget breakdown for moving to Dubai, London, Riyadh, Amsterdam, or Toronto",
        "delivery": "instant",
        "features": [
            "Initial deposit costs",
            "Visa & medical fees",
            "Schooling & healthcare estimates",
            "First 90 days cashflow"
        ],
        "what_they_get": "Relocation budget calculator sheet for your destination city",
        "name_ar": "حاسبة تكاليف الانتقال والعيش بالخارج",
        "description_ar": "ميزانية تفصيلية لتكاليف السفر والعيش في دبي، الرياض، لندن، تورونتو، أو أمستردام",
        "features_ar": [
            "ميزانية الدفعة الأولى",
            "رسوم الفيزا والفحوصات",
            "تقدير المدارس والسكن",
            "مصاريف أول 90 يوماً"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "work-from-home-stipend",
        "name": "Remote WFH Stipend Request Script",
        "price": 4,
        "category": "visa",
        "description": "Ask your remote employer for $1,000+ home office equipment & internet stipends",
        "delivery": "instant",
        "features": [
            "Laptop & monitor stipend pitch",
            "Monthly internet reimbursement",
            "Ergonomic chair budget",
            "Co-working space pass"
        ],
        "what_they_get": "3 email request templates to claim remote work stipends",
        "name_ar": "طلب بدلات وتجهيزات العمل من المنزل",
        "description_ar": "كيف تطلب من شركتك بدل تجهيز المكتب المنزلي (1000$+) والإنترنت الشهري",
        "features_ar": [
            "طلب بدل الكمبيوتر والشاشة",
            "تعويض الإنترنت الشهري",
            "ميزانية الكرسي الصحي",
            "بدل مساحات العمل المشتركة"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "cross-border-tax-guide",
        "name": "Employer of Record (EOR) Guide",
        "price": 9,
        "category": "visa",
        "description": "How Deel, Remote.com, and Oyster HR work for foreign remote hires",
        "delivery": "instant",
        "features": [
            "EOR contract structure",
            "Tax compliance explanation",
            "Social security benefits",
            "IP protection terms"
        ],
        "what_they_get": "EOR explainer sheet to share with prospective foreign employers",
        "name_ar": "دليل عقود التوظيف عبر منصات Deel & Remote",
        "description_ar": "شرح كيفية التوظيف القانوني عبر شركات EOR والالتزامات الضريبية والفوائد",
        "features_ar": [
            "هيكل عقود الـ EOR",
            "توضيح الامتثال الضريبي",
            "مستحقات الضمان الاجتماعي",
            "بنود الملكية الفكرية"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "spouse-work-permit",
        "name": "Expat Spouse Work Permit Guide",
        "price": 6,
        "category": "visa",
        "description": "Work rights and visa transition guide for trailing spouses in UAE, KSA & Europe",
        "delivery": "instant",
        "features": [
            "Dependent visa work rules",
            "Freelance permit option",
            "Work permit conversion step",
            "Local sponsorship rules"
        ],
        "what_they_get": "Spouse work permit roadmap for your target country",
        "name_ar": "تصاريح عمل المرافقين والعائلة في الخارج",
        "description_ar": "دليل حقوق العمل وتحويل الفيزا للمرافقين في الخليج وأوروبا",
        "features_ar": [
            "قواعد عمل الفيزا التابعة",
            "خيار التصريح الحر",
            "خطوات تحويل فيزا العمل",
            "قواعد الكفالة المحلية"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "time-zone-async-work",
        "name": "Async Time-Zone Work Toolkit",
        "price": 4,
        "category": "visa",
        "description": "How to manage 6-9 hour time zone gaps when working for US/EU clients",
        "delivery": "instant",
        "features": [
            "Async communication rules",
            "Loom video update template",
            "Daily standup text format",
            "Overlap hours agreement"
        ],
        "what_they_get": "Async work operational playbook & communication templates",
        "name_ar": "أدوات إدارة فروق التوقيت والعمل اللاتزامني",
        "description_ar": "كيف تدير فروق الوقت (6-9 ساعات) عند العمل مع فرق أمريكية أو أوروبية",
        "features_ar": [
            "قواعد التواصل اللاتزامني",
            "قوالب فيديو Loom التوضيحية",
            "صيغة التقرير اليومي",
            "ساعات التداخل المعتمدة"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "embassy-attestation-guide",
        "name": "Degree Attestation Roadmap",
        "price": 5,
        "category": "visa",
        "description": "Step-by-step degree authentication guide for UAE (MOFA), Saudi (SACM) & Qatar",
        "delivery": "instant",
        "features": [
            "Home country notary steps",
            "Ministry of Foreign Affairs step",
            "Embassy stamp procedure",
            "MOFA final attestation"
        ],
        "what_they_get": "Step-by-step document attestation checklist for Gulf employment visas",
        "name_ar": "خطوات تصديق الشهادات والوثائق بالسفارات",
        "description_ar": "دليل خطوة بخطوة لتصديق الشهادات الجامعية للإمارات والسعودية وقطر",
        "features_ar": [
            "تصديق النوتاري بالدولة",
            "تصديق وزارة الخارجية",
            "ختم السفارة المستهدفة",
            "التصديق النهائي بالخليج"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "relocation-negotiation",
        "name": "Relocation Allowance Request Script",
        "price": 6,
        "category": "visa",
        "description": "Negotiate flight tickets, temporary housing, and shipping container allowances",
        "delivery": "instant",
        "features": [
            "Flight ticket family package",
            "30-day hotel/apartment coverage",
            "Shipping container stipend",
            "School search assistance"
        ],
        "what_they_get": "Relocation package request script & email template",
        "name_ar": "طلب بدل تذاكر الطيران وتكاليف الشحن",
        "description_ar": "تفاوض تذاكر السفر العائلية، الإقامة المؤقتة وشحن الأثاث مع العقد",
        "features_ar": [
            "تذاكر السفر للعائلة",
            "إقامة 30 يوماً بالفندق",
            "بدل شحن الحاوية",
            "بدل البحث عن المدارس"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "overseas-background-check",
        "name": "Global Background Check Prep Guide",
        "price": 4,
        "category": "visa",
        "description": "Prepare documents for Hireright, Sterling, and Interpol background checks",
        "delivery": "instant",
        "features": [
            "Police clearance certificate guide",
            "Employment verification letters",
            "Degree verification consent",
            "Reference check warning"
        ],
        "what_they_get": "Pre-employment background check audit & document checklist",
        "name_ar": "تحضير وثائق الفحص الأمني والجنائي العالمي",
        "description_ar": "تجهيز الوثائق لفحوصات التوظيف عبر منصات Sterling & Hireright العالمية",
        "features_ar": [
            "دليل السجل العدلي والجنائي",
            "خطابات التثبت من العمل",
            "الموافقة على التحقق من الشهادة",
            "تنبيهات فحص التوصيات"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "worldwide-visa-sponsorship-swarm",
        "name": "Worldwide Visa Sponsorship Auto-Applier Swarm (Full Package)",
        "price": 25,
        "category": "visa",
        "description": "Autonomous AI swarm targeting verified enterprise sponsors worldwide offering full relocation: visa + flights + accommodation + meals + transit + top-tier salary",
        "delivery": "instant",
        "features": [
            "100% Work Visa Sponsorship Guarantee",
            "Round-Trip Flight Tickets Included",
            "Free Housing / Monthly Accommodation",
            "Meal & Food Per-Diem Allowance",
            "Daily Commute & Transit Coverage",
            "Top-Tier Global High Salary Filtering"
        ],
        "what_they_get": "Autonomous AI swarm dispatch to verified worldwide visa-sponsoring employers offering full relocation packages",
        "name_ar": "سرب التقديم الآلي لكفالة الفيزا العالمية والبكج الكامل",
        "description_ar": "سرب ذكاء اصطناعي يقدم سيرتك آلياً للشركات العالمية المعتمدة التي تقدم كفالة فيزا وبكج انتقال كامل (تذاكر + سكن + أكل + مواصلات + أعلى الرواتب)",
        "features_ar": [
            "كفالة وتأشيرة عمل 100%",
            "تذاكر طيران ذهاب وعودة",
            "سكن مؤثث مجاني أو بدل سكن",
            "بدل طعام ووجبات يومية",
            "بدل مواصلات وتنقل يومي",
            "فلترة أعلى الرواتب العالمية"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "relocation-full-package-hunter",
        "name": "Full Relocation & Benefits Job Matcher (Ticket + Housing + Food + Transit)",
        "price": 15,
        "category": "visa",
        "description": "Scans 150,000+ active global openings to filter only employers providing end-to-end relocation packages and full sponsorship",
        "delivery": "instant",
        "features": [
            "Verified 6-Pillar Relocation Packages",
            "Flight Ticket & Moving Allowance",
            "Furnished Apartment / Housing Stipend",
            "Meal Vouchers & Commute Coverage"
        ],
        "what_they_get": "Curated list of verified full-package relocation job openings with direct application URLs",
        "name_ar": "مطابق الوظائف ذات البكج الكامل (تذاكر + سكن + طعام + مواصلات)",
        "description_ar": "فحص أكثر من 150,000 شاغر عالمي لفلترة الشركات التي توفر بكج انتقال كامل وتأشيرة عمل وتذاكر وسكن",
        "features_ar": [
            "بكجات انتقال متكاملة الأركان",
            "تذاكر سفر وبدل انتقال نقدي",
            "شقة مؤثثة أو بدل سكن شهري",
            "كوبونات طعام وبدل مواصلات"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "global-sponsor-database-access",
        "name": "Direct Global Visa Sponsor Database (5,000+ Verified Enterprise Employers)",
        "price": 19,
        "category": "visa",
        "description": "Direct spreadsheet & verified contact directory of 5,000+ multinational companies with active government visa sponsorship quotas",
        "delivery": "instant",
        "features": [
            "UK Home Office A-Rated Sponsors",
            "Germany & EU Blue Card Direct Sponsors",
            "Gulf (Saudi Qiwa & UAE MOHRE) Quotas",
            "US H1B / O1 & Canada LMIA Whitelist"
        ],
        "what_they_get": "Downloadable verified database of 5,000+ active visa sponsor companies with HR decision-maker emails",
        "name_ar": "قاعدة بيانات 5,000+ شركة عالمية معتمدة لكفالة الفيزا",
        "description_ar": "دليل مباشر وقاعدة بيانات لـ 5,000+ شركة عالمية تمتلك حصص تأشيرات وكفالة حكومية رسمية مع إيميلات مسؤولي التوظيف",
        "features_ar": [
            "شركات بريطانيا المعتمدة من Home Office",
            "رعاة البطاقة الزرقاء للاتحاد الأوروبي وألمانيا",
            "شركات الخليج ذات الحصص المعتمدة (قوى وتسهيل)",
            "القائمة البيضاء للشركات الأمريكية والكندية"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "visa-sponsorship-cover-letter",
        "name": "Sovereign Visa Sponsorship Pitch & Relocation Letter",
        "price": 6,
        "category": "visa",
        "description": "AI-engineered cover letter convincing global recruiters to sponsor your work visa and provide a full relocation package without hesitation",
        "delivery": "instant",
        "features": [
            "Zero-Friction Sponsorship Pitch",
            "Immediate Relocation Readiness",
            "Relocation ROI Justification",
            "Bilingual (English / Destination Country)"
        ],
        "what_they_get": "Custom relocation & visa sponsorship cover letter in PDF + Word format",
        "name_ar": "خطاب طلب كفالة الفيزا وعرض الانتقال العالمي",
        "description_ar": "خطاب تغطية احترافي مصمم لإقناع مسؤولي التوظيف برعاية فيزا العمل وتحمل نفقات السفر والانتقال بالكامل",
        "features_ar": [
            "صياغة مقنعة لطلب كفالة الفيزا",
            "إبراز الجاهزية الفورية للسفر",
            "إثبات القيمة الاستثمارية لتوظيفك",
            "ثنائي اللغة (الإنجليزية واللغة المحلية)"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "high-salary-negotiation-expat",
        "name": "Worldwide Expat High-Salary & Expat Package Negotiator",
        "price": 12,
        "category": "visa",
        "description": "Scripts, data benchmarks, and negotiation strategies to secure top 5% market salaries with full expat benefits worldwide",
        "delivery": "instant",
        "features": [
            "Net vs Gross Tax-Free Modeling",
            "Expat Housing Allowance Benchmark",
            "Annual Family Ticket Negotiation",
            "Relocation Lump-Sum ($10k+) Request"
        ],
        "what_they_get": "Global salary benchmarking report & word-for-word expat package negotiation scripts",
        "name_ar": "مفاوض أعلى الرواتب العالمية وبكجات المغتربين الفاخرة",
        "description_ar": "أدلة ونصوص تفاوض احترافية للحصول على أعلى رواتب السوق العالمي (Top 5%) مع كامل الامتيازات العائلية",
        "features_ar": [
            "حساب الرواتب الصافية المعفاة من الضرائب",
            "معايير بدلات السكن الفاخر للمغتربين",
            "تفاوض تذاكر العائلة السنوية",
            "طلب منحة الانتقال النقدية (10,000$+ )"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "family-relocation-schooling-pack",
        "name": "Family Relocation, Housing & Schooling Support Blueprint",
        "price": 10,
        "category": "visa",
        "description": "Complete roadmap to secure company-paid family visas, children education stipends, and furnished family apartments",
        "delivery": "instant",
        "features": [
            "Spouse & Dependent Visa Roadmap",
            "International School Allowance Pitch",
            "Shipping Container & Pet Relocation",
            "First 60 Days Settling-In Checklist"
        ],
        "what_they_get": "Comprehensive family expat relocation guide + school stipend request templates",
        "name_ar": "دليل انتقال العائلة، السكن وبدلات المدارس الدولية",
        "description_ar": "دليل متكامل لضمان تغطية الشركة لكفالة وتأشيرات العائلة، مصاريف مدارس الأبناء، والسكن العائلي",
        "features_ar": [
            "خارطة طريق فيزا الزوجة والأبناء",
            "طلب بدل المدارس الدولية للأطفال",
            "شحن الأثاث والانتقال العائلي",
            "قائمة أول 60 يوماً للاستقرار"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "sovereign-relocation-citizenship-swarm",
        "name": "Sovereign Relocation, Golden Visa & Full Expat Swarm (All-Inclusive)",
        "price": 25,
        "category": "visa",
        "description": "Autonomous AI dispatch targeting 12,000+ verified governments, megaprojects, and multinational sponsors offering full relocation: Flight + Visa + Luxury Villa + Meals + Car + Lucrative Salary + Citizenship/PR Track",
        "delivery": "instant",
        "features": [
            "100% Work Visa Sponsorship & Citizenship/PR Track",
            "First-Class / Business Moving Tickets & Family Flights",
            "Luxury Furnished Villa / Apartment (Zero Rent)",
            "Comprehensive Living & Daily Dining Allowance",
            "Executive Transportation / Company Vehicle",
            "Lucrative High-Net / Tax-Free Wealth Multiplier"
        ],
        "what_they_get": "Autonomous AI swarm dispatch to verified worldwide employers and sovereign regional development zones offering the complete 7-Pillar Relocation & Wealth Package",
        "name_ar": "سرب الهجرة الشاملة، الفيزا الذهبية ومسار الجنسية (البكج المتكامل)",
        "description_ar": "سرب ذكاء اصطناعي يقدم سيرتك آلياً لـ 12,000+ جهة حكومية وشركات عملاقة تقدم بكج انتقال كامل (فيزا + إقامة دائمة ومسار جنسية + تذاكر + فيلا فاخرة + طعام + سيارة + رواتب ضخمة)",
        "features_ar": [
            "كفالة فيزا 100% ومسار للحصول على الجنسية / الإقامة الدائمة",
            "تذاكر سفر وانتقال لك ولعائلتك بالكامل",
            "سكن مؤثث فاخر أو فيلا بدون تكاليف إيجار",
            "بدل معيشة ووجبات طعام يومية متكاملة",
            "سيارة خاصة أو بدل مواصلات تنفيذي",
            "رواتب ضخمة معفاة من الضرائب لبناء ثروة حقيقية"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "citizenship-pr-fast-track-matcher",
        "name": "Citizenship & Fast-Track Permanent Residency (PR) Pathway Matcher",
        "price": 19,
        "category": "visa",
        "description": "Match your exact career & profession with countries and economic zones offering fast-track permanent residency and passport citizenship after 3-5 years of qualifying employment",
        "delivery": "instant",
        "features": [
            "Global Citizenship by Employment Matrix",
            "3 to 5 Year Permanent Residency Roadmaps",
            "Direct Regional Government Quota Whitelist",
            "Profession-Specific Legal Pathway Reports"
        ],
        "what_they_get": "Comprehensive legal roadmap & verified list of countries granting citizenship/PR based on your exact profession and employment track",
        "name_ar": "مطابق مسارات الجنسية والإقامة الدائمة السريعة حسب المهنة",
        "description_ar": "مطابقة مهنتك وتخصصك بالدول والمناطق الاقتصادية التي تمنح إقامة دائمة وجواز سفر / جنسية بعد 3 إلى 5 سنوات من العمل",
        "features_ar": [
            "مصفوفة الجنسية العالمية عبر العمل والمهارة",
            "خارطة طريق الإقامة الدائمة خلال 3-5 سنوات",
            "القائمة البيضاء للمناطق الاقتصادية ذات الحصص الحكومية",
            "تقرير قانوني مفصل مخصص لمسارك المهني"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "luxury-relocation-lump-sum-negotiator",
        "name": "$25k+ Relocation Lump-Sum, Luxury Villa & Executive Car Negotiator",
        "price": 14,
        "category": "visa",
        "description": "Proven negotiation scripts and benchmarks to secure $15,000–$50,000 upfront relocation signing bonuses, company-paid luxury villas, and private vehicle stipends",
        "delivery": "instant",
        "features": [
            "$15k-$50k Relocation Bonus Negotiation Scripts",
            "Compound / Luxury Villa Allowance Justification",
            "Company Car & Fuel Coverage Request Clause",
            "Annual Family Holiday Flight Contracts"
        ],
        "what_they_get": "Battle-tested legal clauses & negotiation scripts to demand and secure maximum expat luxury benefits from hiring directors",
        "name_ar": "مفاوض منحة الانتقال ($25k+)، الفيلا الفاخرة والسيارة الخاصة",
        "description_ar": "نصوص وصيغ تفاوض معتمدة لطلب والحصول على بونص انتقال نقدي (15,000$ إلى 50,000$)، فيلا سكنية فاخرة وبدل سيارة خاصة",
        "features_ar": [
            "نصوص تفاوض منحة الانتقال النقدية الكبرى",
            "شروط توفير فيلا في المجمعات السكنية الراقية",
            "بند توفير سيارة خاصة وتغطية الوقود",
            "عقود تذاكر الإجازة السنوية لكافة أفراد العائلة"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "profession-based-regional-shortage-finder",
        "name": "Profession-Based Regional Shortage & Sovereign Quota Finder",
        "price": 15,
        "category": "visa",
        "description": "Maps your exact job title and skills to high-demand regional shortage lists across 45+ countries where governments fast-track visas and sponsor full relocation to revitalize their regions",
        "delivery": "instant",
        "features": [
            "45+ Country Critical Shortage Database",
            "Regional Economic Revitalization Zones (Zero Competition)",
            "Government Sponsored Fast-Track Quota Match",
            "Direct Contact Directory of Regional Hiring Boards"
        ],
        "what_they_get": "Customized shortage matching report linking your skills to countries actively paying bonuses to attract your profession",
        "name_ar": "كاشف المهن المطلوبة في المناطق الاقتصادية ذات الكفالة الحكومية",
        "description_ar": "مطابقة مهاراتك مع قوائم النقص الحرج في 45+ دولة ومناطق التطوير الإقليمي التي تقدم تسهيلات وكفالة كاملة لجذب الكفاءات وتنشيط اقتصادها",
        "features_ar": [
            "قاعدة بيانات 45+ دولة للمهن الحرجة",
            "مناطق التطوير الاقتصادي (فرص توظيف فورية)",
            "مطابقة الحصص الحكومية السريعة",
            "دليل التواصل المباشر مع لجان التوظيف الإقليمية"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "sovereign-wealth-taxfree-calculator",
        "name": "Tax-Free Expat Wealth Accumulation & Savings Blueprint",
        "price": 9,
        "category": "visa",
        "description": "Interactive wealth accumulation model showing how 3 years in a tax-free / high-subsidy expat zone creates $150,000+ in net liquid savings through free housing, food, and high salaries",
        "delivery": "instant",
        "features": [
            "Zero-Expense Expat Lifestyle Budgeting",
            "Net Savings Projection (1, 3 & 5 Years)",
            "Tax Optimization & Asset Protection Guide",
            "Expat Wealth Acceleration Multipliers"
        ],
        "what_they_get": "Custom financial blueprint showing how your relocation package turns into substantial generational wealth",
        "name_ar": "خطة بناء الثروة والادخار المعفى من الضرائب للمغتربين",
        "description_ar": "نموذج مالي تفاعلي يوضح كيف يحقق الانتقال لباقة متكاملة (سكن + طعام + مواصلات مغطاة) وفر مالي يتجاوز 150,000$ صافي خلال 3 سنوات",
        "features_ar": [
            "حساب المعيشة بصفر مصاريف سكن وتنقل",
            "توقعات الوفر المالي لـ 1 و 3 و 5 سنوات",
            "دليل حماية الأصول والتخطيط الضريبي المعفى",
            "مضاعفات نمو الثروة للمغتربين"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "response-tracker",
        "name": "Application Response Tracker",
        "price": 4,
        "category": "ai",
        "description": "Track every application, follow-up, and response in a dashboard",
        "delivery": "instant",
        "features": [
            "Real-time status tracking",
            "Follow-up reminders",
            "Response analytics",
            "Export to CSV"
        ],
        "what_they_get": "7 days access to tracking dashboard with all your applications monitored",
        "name_ar": "لوحة تتبع حالة الطلبات والمتابعات",
        "description_ar": "متابعة جميع طلبات التقديم والمتابعات والردود في لوحة تحكم واحدة",
        "features_ar": [
            "تتبع الحالة مباشرة",
            "تنبيهات المتابعة",
            "تحليلات معدل الاستجابة",
            "تصدير الملف لـ CSV"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "job-alert-setup",
        "name": "Job Alert Automation",
        "price": 4,
        "category": "ai",
        "description": "Set up 24/7 automated job alerts across multiple platforms",
        "delivery": "1 hour",
        "features": [
            "Monitors 5+ job boards",
            "Real-time notifications",
            "Apply-ready alerts",
            "Filters by salary/location"
        ],
        "what_they_get": "30 days of automated job monitoring with daily email digests",
        "name_ar": "أتمتة التنبيهات على مدار 24 ساعة",
        "description_ar": "ضبط تنبيهات آلية 24/7 عبر منصات التوظيف المتعددة للتقديم السريع",
        "features_ar": [
            "مراقبة 5+ منصات توظيف",
            "إشعارات فورية للفرص",
            "تنبيهات جاهزة للتقديم",
            "فلترة حسب الراتب والمدينة"
        ],
        "delivery_ar": "خلال ساعة"
    },
    {
        "id": "vip-support-month",
        "name": "VIP Support — 1 Month",
        "price": 20,
        "category": "ai",
        "description": "30 days of priority support: daily applications, daily follow-ups, weekly reports",
        "delivery": "instant (30-day access)",
        "features": [
            "Daily automated applications (100+/day)",
            "Daily follow-up sending",
            "Weekly progress reports",
            "Priority email support"
        ],
        "what_they_get": "30 days of FULL automation: 3000+ applications sent, all follow-ups managed",
        "name_ar": "اشتراك الدعم الفني والأتمتة (30 يوماً)",
        "description_ar": "30 يوماً من الأتمتة الكاملة: تقديم يومي، متابعات آلية وتقارير أسبوعية",
        "features_ar": [
            "تقديم تلقائي يومي (100+/يوم)",
            "إرسال المتابعات اليومية",
            "تقارير أسبوعية تفصيلية",
            "دعم فني ذو أولوية"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "ai-tailored-resume-generator",
        "name": "AI Tailored CV Generator (1-Click)",
        "price": 8,
        "category": "ai",
        "description": "Generate a custom tailored CV version matching any pasted Job Description in 10 seconds",
        "delivery": "instant",
        "features": [
            "Instant JD keyword extraction",
            "Bullet point re-alignment",
            "ATS score 90+ guarantee",
            "Instant PDF download"
        ],
        "what_they_get": "10 tailored CV generations for target job descriptions",
        "name_ar": "توليد سيرة ذاتية مطابقة للوصف بضغطة زر",
        "description_ar": "توليد نسخة سيرة ذاتية مخصصة ومطابقة لأي وصف وظيفي خلال 10 ثوانٍ",
        "features_ar": [
            "استخراج كلمات الوصف فوراً",
            "إعادة ترتيب النقاط",
            "ضمان نسبة توافق 90%+",
            "تحميل PDF فوري"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "auto-fill-browser-extension",
        "name": "Workday & Greenhouse Auto-Fill Kit",
        "price": 6,
        "category": "ai",
        "description": "Auto-fill complex 10-page application forms on Workday, Taleo & Greenhouse instantly",
        "delivery": "instant",
        "features": [
            "Workday 1-click fill profile",
            "Greenhouse auto-uploader",
            "EEOC & salary default fills",
            "Custom answer library"
        ],
        "what_they_get": "Auto-fill JSON profile script + browser extension guide",
        "name_ar": "التعبئة التلقائية لنماذج Workday & Greenhouse",
        "description_ar": "تعبئة نماذج التقديم الطويلة على منصات Workday و Taleo و Greenhouse بضغطة زر",
        "features_ar": [
            "تعبئة ملخص Workday بضغطة",
            "رفع سير Greenhouse آلياً",
            "تعبئة خيارات التوظيف",
            "مكتبة الإجابات المخصصة"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "hidden-job-market-scraper",
        "name": "AI Unlisted Role & Hidden Job Scraper",
        "price": 10,
        "category": "ai",
        "description": "Scrape startup career pages & unlisted vacancies before they reach public job boards",
        "delivery": "24 hours",
        "features": [
            "Series A/B startup career pages",
            "Direct founder email matches",
            "Unlisted vacancy detector",
            "Early applicant advantage"
        ],
        "what_they_get": "List of 20 unlisted job vacancies with direct contact emails",
        "name_ar": "سحب الفرص غير المعلنة في الشركات الناشئة",
        "description_ar": "اكتشاف الوظائف الشاغرة في صفحات الشركات قبل نشرها على المنصات العامة",
        "features_ar": [
            "صفحات شركات Series A/B",
            "مطابقة إيميلات المؤسسين",
            "كشف الوظائف غير المعلنة",
            "أسبقية التقديم المبكر"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "recruiter-ghosting-detector",
        "name": "Recruiter Ghosting & Probability Bot",
        "price": 4,
        "category": "ai",
        "description": "AI predicts if a company is ghosting based on application age and activity signals",
        "delivery": "instant",
        "features": [
            "Response probability score",
            "Average company hire speed",
            "Optimal nudge timing",
            "Re-engagement trigger email"
        ],
        "what_they_get": "Ghosting probability report + automated nudge script",
        "name_ar": "مؤشر توقع تجاهل مسؤولي التوظيف",
        "description_ar": "الذكاء الاصطناعي يتوقع نسبة التجاوب والتجاهل بناءً على عمر الشاغر والنشاط",
        "features_ar": [
            "نسبة التجاوب المتوقعة",
            "متوسط سرعة التوظيف بالشركة",
            "توقيت النكز المثالي",
            "إيميل إعادة التفاعل"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "applicant-ranking-checker",
        "name": "AI ATS Applicant Rank Simulator",
        "price": 5,
        "category": "ai",
        "description": "Simulate where your CV lands (Top 5%, Top 20%, or Rejected) in a pool of 200 candidates",
        "delivery": "instant",
        "features": [
            "Candidate pool ranking",
            "Top-percentile score",
            "Competitive gap analysis",
            "Rank boosting recommendations"
        ],
        "what_they_get": "ATS rank report showing candidate percentile & fixes",
        "name_ar": "محاكاة ترتيب السيرة الذاتية بين المتقدمين",
        "description_ar": "محاكاة الترتيب التنافسي لسيرتك (أفضل 5% أو 20%) بين 200 متقدم للوظيفة",
        "features_ar": [
            "ترتيب بين المتقدمين",
            "النسبة المئوية التنافسية",
            "تحليل الفجوة مع المنافسين",
            "توصيات رفع الترتيب"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "job-description-decoder",
        "name": "Job Description Red-Flag Decoder",
        "price": 3,
        "category": "ai",
        "description": "AI analyzes job posts for hidden red flags (overtime trap, vague duties, high turnover)",
        "delivery": "instant",
        "features": [
            "Toxic culture detector",
            "Hidden workload warning",
            "Salary transparency score",
            "Realistic scope rating"
        ],
        "what_they_get": "1-page job description breakdown highlighting 5+ hidden traps",
        "name_ar": "كشف فخاخ الوظائف وبيئة العمل غير الصحية",
        "description_ar": "تحليل الوصف الوظيفي لاكتشاف الساعات الإضافية المجانية، ضبابية المهام، ومعدل دوران الموظفين",
        "features_ar": [
            "كشف البيئة غير الصحية",
            "تنبيهات ساعات العمل الزائدة",
            "مؤشر شفافية الراتب",
            "تقييم واقعية الشاغر"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "career-pivot-ai-advisor",
        "name": "AI Career Pivot & Skills Transfer",
        "price": 8,
        "category": "ai",
        "description": "Map your skills to pivot into a new higher-paying industry (e.g. Sales to Tech)",
        "delivery": "instant",
        "features": [
            "Transferable skills map",
            "Target role alignment",
            "Industry jargon translator",
            "CV conversion template"
        ],
        "what_they_get": "Career pivot blueprint with transferable skills resume template",
        "name_ar": "تحويل المهارات وتغيير المجال المهني",
        "description_ar": "مطابقة مهاراتك للانتقال إلى مجال جديد أعلى أجراً (مثال: الانتقال من المبيعات للتكنولوجيا)",
        "features_ar": [
            "خريطة المهارات القابلة للنقل",
            "مطابقة الشاغر الجديد",
            "ترجمة المصطلحات للقطاع الجديد",
            "قالب السيرة التحويلية"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "company-research",
        "name": "Company Research Report",
        "price": 5,
        "category": "freelance",
        "description": "Deep-dive research on 5 target companies including culture, hiring, and decision-makers",
        "delivery": "24 hours",
        "features": [
            "Company culture analysis",
            "Hiring team identified",
            "Recent news/trends",
            "Interview question prep"
        ],
        "what_they_get": "5 company profiles with key contacts, recent hiring patterns, and tailored interview tips",
        "name_ar": "تقرير أبحاث شامل عن 5 شركات",
        "description_ar": "بحث تفصيلي عن 5 شركات مستهدفة يشمل ثقافة العمل، مسؤولي التوظيف والفرص",
        "features_ar": [
            "تحليل ثقافة الشركة",
            "تحديد أسماء مسؤولي التوظيف",
            "أحدث الأخبار والاتجاهات",
            "تحضير أسئلة المقابلة"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "full-application-pack",
        "name": "Complete Application Pack",
        "price": 15,
        "category": "freelance",
        "description": "Everything: optimized CV, cover letter, email templates, follow-ups, company research",
        "delivery": "24 hours",
        "features": [
            "ATS-optimized CV",
            "Custom cover letter",
            "5 email templates",
            "Follow-up sequence",
            "3 company research reports"
        ],
        "what_they_get": "Full application kit: CV + cover letter + templates + follow-ups + research",
        "name_ar": "الحقيبة الكاملة للتقديم الوظيفي",
        "description_ar": "تتضمن كل شيء: سيرة ذاتية، خطاب تغطية، إيميلات تقديم ومتابعة وأبحاث شركات",
        "features_ar": [
            "سيرة ذاتية متوافقة مع ATS",
            "خطاب تغطية مخصص",
            "5 قوالب إيميل",
            "تسلسل المتابعة التلقائي",
            "3 تقارير أبحاث"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "job-search-plan",
        "name": "90-Day Job Search Plan",
        "price": 15,
        "category": "freelance",
        "description": "Structured 90-day job search plan with weekly goals, targets, and tracking",
        "delivery": "24 hours",
        "features": [
            "Week-by-week action plan",
            "Application targets (100/day)",
            "Progress tracking template",
            "Milestone checkpoints"
        ],
        "what_they_get": "PDF 90-day plan with weekly checklists, application tracker, accountability system",
        "name_ar": "خطة البحث عن عمل لـ 90 يوماً",
        "description_ar": "خطة عمل أسبوعية محددة بالأهداف والمهام اليومية للوصول للعرض المناسب",
        "features_ar": [
            "خطة عمل أسبوعية",
            "أهداف التقديم اليومي",
            "قالب التتبع والمتابعة",
            "نقاط مراجعة الإنجاز"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "career-consultation",
        "name": "Career Strategy Session",
        "price": 15,
        "category": "freelance",
        "description": "Comprehensive career roadmap with salary benchmarks, growth path, and action plan",
        "delivery": "48 hours",
        "features": [
            "5-year career roadmap",
            "Salary benchmarking (Gulf/MENA)",
            "Certification roadmap",
            "Action plan with timeline"
        ],
        "what_they_get": "PDF career roadmap with salary data for 10+ roles, certification path, 90-day action plan",
        "name_ar": "جلسة الاستراتيجية والمسار المهني",
        "description_ar": "خارطة طريق مهنية لـ 5 سنوات تشمل مقارنة الرواتب وخطوات النمو والشهادات",
        "features_ar": [
            "خارطة طريق 5 سنوات",
            "مقارنة الرواتب بالخليج",
            "مسار الشهادات المطلوبة",
            "خطة عمل مع جدول زمني"
        ],
        "delivery_ar": "خلال 48 ساعة"
    },
    {
        "id": "freelance-rate-calculator",
        "name": "Hourly to Retainer Rate Calculator",
        "price": 6,
        "category": "freelance",
        "description": "Calculate your freelance hourly rate, day rate, and monthly retainer pricing model",
        "delivery": "instant",
        "features": [
            "Billable hours formula",
            "Tax & overhead buffer",
            "Retainer discount model",
            "Client proposal pricing pitch"
        ],
        "what_they_get": "Freelance rate calculator sheet + 1-page pricing proposal template",
        "name_ar": "حاسبة تسعير ساعات المستشار والعقود",
        "description_ar": "حساب السعر العادل لساعتك وعقود الاستشارات الشهرية للعملاء",
        "features_ar": [
            "معادلة الساعات السنوية",
            "تغطية الضرائب والمصاريف",
            "نموذج الخصم للعقود",
            "قالب تسعير العرض"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "upwork-fiverr-profile-boost",
        "name": "Upwork & Freelance Profile Kit",
        "price": 8,
        "category": "freelance",
        "description": "Optimize your Upwork overview, portfolio items, and proposal pitch letters",
        "delivery": "instant",
        "features": [
            "Top-rated overview template",
            "Proposal proposal hook formula",
            "Portfolio item tags",
            "Client video intro script"
        ],
        "what_they_get": "Complete Upwork profile makeover guide + 3 proposal templates",
        "name_ar": "حقيبة تحسين حسابات Upwork والتقديم",
        "description_ar": "تحسين نبذة حسابك على Upwork وقوالب تقديم العروض لفرص العمل المستقل",
        "features_ar": [
            "قالب النبذة الأعلى تقييماً",
            "صيغة خطاف العروض القاطعة",
            "وسوم معارض الأعمال",
            "سيناريو فيديو العميل"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "consulting-proposal-deck",
        "name": "1-Page Consulting Pitch Deck",
        "price": 10,
        "category": "freelance",
        "description": "High-converting 1-page proposal layout to land B2B consulting clients",
        "delivery": "instant",
        "features": [
            "Problem statement framework",
            "Scope of work breakdown",
            "Milestone payment structure",
            "Client sign-off block"
        ],
        "what_they_get": "Editable 1-page consulting proposal template in Canva & PowerPoint",
        "name_ar": "نموذج العرض الاستشاري لصفقات الشركات",
        "description_ar": "قالب عرض استشاري مخصص في صفحة واحدة لإغلاق صفقات الخدمات مع الشركات",
        "features_ar": [
            "صياغة مشكلة العميل",
            "تقسيم نطاق العمل",
            "هيكل الدفعات والشهور",
            "صيغة التوقيع والموافقة"
        ],
        "delivery_ar": "فوري"
    },
    {
        "id": "executive-bio-one-pager",
        "name": "Executive 1-Page Biography",
        "price": 12,
        "category": "freelance",
        "description": "Polished 1-page executive bio for advisory boards, speaking gigs, and press",
        "delivery": "24 hours",
        "features": [
            "Executive narrative",
            "Core competency matrix",
            "Board & media highlights",
            "High-res PDF format"
        ],
        "what_they_get": "1-page executive bio document formatted for senior leadership",
        "name_ar": "السيرة الذاتية الموجزة للقياديين",
        "description_ar": "سيرة ذاتية تنفذية في صفحة واحدة مخصصة لمجالس الإدارة واللقاءات الصحفية",
        "features_ar": [
            "السرد القيادي التنفيذي",
            "مصفوفة المهارات الرئيسية",
            "سجل مجالس الإدارة والإعلام",
            "تصدير PDF عالي الجودة"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "board-member-resume",
        "name": "Board of Directors CV Format",
        "price": 15,
        "category": "freelance",
        "description": "Format your CV for Non-Executive Director (NED) and Board Advisory positions",
        "delivery": "24 hours",
        "features": [
            "Governance & oversight framing",
            "P&L governance experience",
            "Committee expertise tags",
            "Board bio summary"
        ],
        "what_they_get": "Board-level resume template + board value proposition pitch",
        "name_ar": "سيرة ذاتية مخصصة لأعضاء مجالس الإدارة",
        "description_ar": "صياغة سيرتك الذاتية للترشح لمناصب أعضاء مجالس الإدارة غير التنفيذيين (NED)",
        "features_ar": [
            "لغة الحوكمة والإشراف",
            "خبرة إدارة الميزانيات",
            "لجان المراجعة والمخاطر",
            "ملخص قيمة عضو المجلس"
        ],
        "delivery_ar": "خلال 24 ساعة"
    },
    {
        "id": "fractional-exec-proposal",
        "name": "Fractional Executive Retainer Deck",
        "price": 18,
        "category": "freelance",
        "description": "Pitch yourself as a Fractional CMO, CTO, CFO, or COO to startups & SMEs",
        "delivery": "24 hours",
        "features": [
            "Fractional model ROI pitch",
            "Weekly hours allocation",
            "Monthly retainer agreement",
            "Deliverables roadmap"
        ],
        "what_they_get": "Fractional executive retainer deck + proposal contract template",
        "name_ar": "عرض تقديم الخدمات التنفيذية الجزئية",
        "description_ar": "تقديم خدماتك كـ Fractional CMO أو CTO أو CFO للشركات الناشئة والمصانع",
        "features_ar": [
            "عرض ROI النموذج الجزئي",
            "توزيع الساعات الأسبوعية",
            "اتفاقية الاشتراك الشهري",
            "خارطة تسليم المخرجات"
        ],
        "delivery_ar": "خلال 24 ساعة"
    }
]

# Bouquet packages (bundles for better value)
BOUQUET_CATALOG = [
    {
        "id": "starter-pack",
        "name": "Starter Pack",
        "price": 5,
        "services": [
            "cv-review",
            "cover-letter-basic",
            "email-template"
        ],
        "savings": "33%",
        "description": "Everything to start: CV review + cover letter + email template"
    },
    {
        "id": "linkedin-pack",
        "name": "LinkedIn Optimization Pack",
        "price": 12,
        "services": [
            "linkedin-headline",
            "linkedin-optimization"
        ],
        "savings": "15%",
        "description": "Full LinkedIn transformation: headline + complete profile makeover"
    },
    {
        "id": "application-pack",
        "name": "Complete Application Pack",
        "price": 18,
        "services": [
            "full-application-pack",
            "response-tracker",
            "followup-sequence"
        ],
        "savings": "25%",
        "description": "Everything application-related: pack + tracker + follow-ups"
    },
    {
        "id": "premium-pack",
        "name": "Premium Career Pack",
        "price": 20,
        "services": [
            "full-application-pack",
            "linkedin-optimization",
            "career-consultation",
            "interview-prep"
        ],
        "savings": "35%",
        "description": "Full career transformation: applications + LinkedIn + strategy + interview prep"
    },
    {
        "id": "vip-month",
        "name": "VIP Month",
        "price": 20,
        "services": [
            "vip-support-month"
        ],
        "savings": "0% (already best price)",
        "description": "30 days of FULL automation — 3000+ applications, all follow-ups, weekly reports"
    },
    {
        "id": "worldwide-visa-sponsorship-bundle",
        "name": "Worldwide Visa Sponsorship & Full Relocation Mega Pack",
        "price": 39,
        "services": [
            "worldwide-visa-sponsorship-swarm",
            "relocation-full-package-hunter",
            "global-sponsor-database-access",
            "visa-sponsorship-cover-letter",
            "high-salary-negotiation-expat",
            "family-relocation-schooling-pack"
        ],
        "savings": "55%",
        "description": "Ultimate Global Mobility Suite: Visa Swarm + 5,000+ Sponsor Directory + Flight & Housing Matcher + Expat Salary Negotiator + Family Blueprint"
    },
    {
        "id": "sovereign-relocation-citizenship-bundle",
        "name": "Sovereign Relocation, Golden Visa & Fast-Track Citizenship Flagship Pack",
        "price": 49,
        "services": [
            "sovereign-relocation-citizenship-swarm",
            "citizenship-pr-fast-track-matcher",
            "luxury-relocation-lump-sum-negotiator",
            "profession-based-regional-shortage-finder",
            "sovereign-wealth-taxfree-calculator",
            "worldwide-visa-sponsorship-swarm",
            "relocation-full-package-hunter",
            "family-relocation-schooling-pack"
        ],
        "savings": "65%",
        "description": "The Master Global Relocation & Wealth Suite: Sovereign AI Swarm + 3-5 Year Citizenship & PR Pathways + $25k+ Relocation Bonus & Villa Negotiator + Tax-Free Wealth Engine + 100% Visa & Family Sponsorship"
    }
]


def get_service(service_id: str) -> dict[str, Any] | None:
    for s in SERVICE_CATALOG:
        if s["id"] == service_id:
            return s
    return None


def get_bouquet(bouquet_id: str) -> dict[str, Any] | None:
    for b in BOUQUET_CATALOG:
        if b["id"] == bouquet_id:
            return b
    return None

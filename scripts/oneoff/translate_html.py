"""
scripts/oneoff/translate_html.py
JobHunt Pro - HTML Translation & RTL Logic Injection Utility
"""
import os
import re
import logging
from typing import List, Tuple, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

css_replacements: List[Tuple[str, str]] = [
    (r"margin-left\b", "margin-inline-start"),
    (r"margin-right\b", "margin-inline-end"),
    (r"padding-left\b", "padding-inline-start"),
    (r"padding-right\b", "padding-inline-end"),
    (r"border-left\b", "border-inline-start"),
    (r"border-right\b", "border-inline-end"),
    (r"(?<!-)left\s*:", "inset-inline-start:"),
    (r"(?<!-)right\s*:", "inset-inline-end:"),
    (r"text-align\s*:\s*left\b", "text-align: start"),
    (r"text-align\s*:\s*right\b", "text-align: end"),
    (r"font-family\s*:\s*'Inter'[^;]*;", "font-family: 'Cairo', 'IBM Plex Arabic', 'Tajawal', sans-serif;"),
    (r"font-family\s*:\s*'Space Grotesk'[^;]*;", "font-family: 'Cairo', 'IBM Plex Arabic', 'Tajawal', sans-serif;"),
    (r"font-family\s*:\s*'Orbitron'[^;]*;", "font-family: 'Cairo', 'IBM Plex Arabic', 'Tajawal', sans-serif;"),
]

text_replacements: Dict[str, str] = {
    # Head and meta
    "JobHunt Pro — Land Your Dream Job. Automatically.": "جوب هانت برو — لاقي وظيفة أحلامك. تلقائياً.",
    "The most advanced job hunting platform. Apply to thousands of jobs, track every application, and get hired faster. Trusted by thousands of job seekers worldwide.": "أكثر منصة متطورة للتدوير ع شغل. قدم ع آلاف الوظائف، تابع كل طلب، وتوظف أسرع. موثوقة من آلاف الباحثين عن عمل بكل العالم.",
    "Apply to thousands of jobs, track every application, and get hired faster. The smartest way to job hunt.": "قدم ع آلاف الوظائف، تابع كل طلب، وتوظف أسرع. أذكى طريقة لتلاقي شغل.",
    "Apply to thousands of jobs, track every application, and get hired faster.": "قدم ع آلاف الوظائف، تابع كل طلب، وتوظف أسرع.",
    "JobHunt Pro — AI-Powered Automated Job Applications": "جوب هانت برو — تقديم ع الوظائف تلقائياً بالذكاء الاصطناعي",
    "Your personal AI job-hunting engine works 24/7 — searching thousands of jobs, crafting personalized applications, and sending them through smart email rotation. Less than 7 cents per application.": "محركك الشخصي للبحث عن عمل بالذكاء الاصطناعي شغال 24/7 — بيفتش بآلاف الوظائف، بيكتب طلبات مخصصة، وبيبعتها عبر نظام تدوير الإيميلات. أقل من 7 سنت للطلب.",
    "Your personal AI job-hunting engine works 24/7. Get hired faster. Less than 7 cents per application.": "محركك الشخصي شغال 24/7. توظف أسرع. أقل من 7 سنت للطلب.",
    "AI-Powered Automated Job Application Engine with 200 AI agents, multi-engine job search, and smart email rotation.": "محرك تقديم ع الوظائف بالذكاء الاصطناعي مع 200 عميل ذكي، بحث متعدد المحركات، وتدوير ذكي للإيميلات.",
    "AI-Powered Automated Job Applications | 200 AI Agents, 24/7": "تقديم ع الوظائف بالذكاء الاصطناعي | 200 عميل ذكي، 24/7",

    # Nav and Header
    "Smart Job Applications": "تقديم ذكي ع الوظائف",
    "Home": "الرئيسية",
    "Pricing": "الأسعار",
    "Login": "تسجيل الدخول",
    "Get Started": "بلّش هلأ",
    "View Plans": "شوف الخطط",
    "Get Started Free": "بلش مجاناً",
    "View Pricing Plans": "شوف خطط الأسعار",
    "See How It Works": "شوف كيف بتشتغل",
    
    # Hero
    "Processing Applications Now": "عم نعالج الطلبات هلأ",
    "AI SYSTEM ONLINE — v{{ VERSION }}": "نظام الذكاء الاصطناعي شغال — الإصدار {{ VERSION }}",
    "Apply to <span class=\"cyan\">Thousands</span> of Jobs<br>": "قدم ع <span class=\"cyan\">آلاف</span> الوظائف<br>",
    "While You <span class=\"magenta\">Sleep</span>": "وإنت <span class=\"magenta\">نايم</span>",
    "Stop spending hours on job boards. Our intelligent platform applies to the right jobs for you &mdash; personalized applications, real-time tracking, and zero manual work.": "حاج تضيع ساعات ع مواقع التوظيف. منصتنا الذكية بتقدم ع الوظائف المناسبة إلك — طلبات مخصصة، تتبع مباشر، وبدون أي تعب يدوي.",
    "Start Free Trial": "جرب مجاناً",
    "Start Applying Now — It's Free": "بلّش تقديم هلأ — مجاناً",
    
    # Stats
    "Active Users": "مستخدم نشط",
    "And growing daily": "وعم نكبر كل يوم",
    "Applications Sent": "طلبات انبعتت",
    "In the last 30 days": "بآخر 30 يوم",
    "Interview Rate": "نسبة المقابلات",
    "3&times; industry average": "3 أضعاف المعدل الطبيعي",
    "User Rating": "تقييم المستخدمين",
    "Jobs Landed": "وظائف حصلوا عليها",
    "And counting": "والعدد عم يزيد",
    "Daily Applications": "طلبات يومية",
    "Email Providers": "مزودي إيميلات",
    "AI Agents": "عملاء ذكاء اصطناعي",
    "Countries": "بلدان",

    # Guarantee
    "30-Day Money-Back Guarantee": "ضمان استرجاع المصاري خلال 30 يوم",
    "No interviews? Get a full refund. No questions asked. Your risk is ZERO.": "ما إجاك مقابلات؟ منرجعلك كل مصرياتك. بدون أي أسئلة. الخطر صفر.",

    # Trusted by / Integrations
    "Trusted by Job Seekers Worldwide": "موثوقة من الباحثين عن عمل بكل العالم",
    "SEARCHING ACROSS THESE PLATFORMS + MORE": "عم نفتش بهالمواقع وأكتر",
    "LEBANON": "لبنان",
    "UAE": "الإمارات",
    "SAUDI": "السعودية",
    "QATAR": "قطر",
    "KUWAIT": "الكويت",
    "REMOTE": "عن بُعد",

    # How it works
    "How It Works": "كيف بتشتغل",
    "THE PROCESS": "العملية",
    "4 Simple Steps to<br>Your Next Job": "4 خطوات بسيطة<br>لوظيفتك الجاية",
    "Four simple steps from uploading your resume to landing interviews. Zero manual work required.": "أربع خطوات بسيطة من رفع سيرتك الذاتية لتحصل ع مقابلات. بدون أي تعب يدوي.",
    "Getting hired has never been easier. Set it up once, and let the system do the heavy lifting.": "التوظيف صار أسهل من قبل. ضبطها مرة وحدة وخلي النظام يشتغل عنك.",
    "Create Your Profile": "اعمل بروفايلك",
    "Upload Your CV": "ارفع سيرتك الذاتية",
    "Upload your CV, set your preferences, and tell us what kind of jobs you're looking for. Takes less than 5 minutes.": "ارفع سيرتك الذاتية، حط تفضيلاتك، وقولنا شو نوع الوظايف يلي عم تفتش عليها. بتاخد أقل من 5 دقايق.",
    "Drop your PDF or paste your CV text. Our AI instantly extracts your skills, experience, education, and career preferences.": "حط ملف الـ PDF أو انسخ نص سيرتك. الذكاء الاصطناعي بيستخرج مهاراتك وخبرتك وتفضيلاتك فوراً.",
    "Jobs Are Scanned": "مسح الوظائف",
    "Set Your Target": "حدد هدفك",
    "Our platform scans thousands of job listings across multiple sources, finding the best matches for your skills and goals.": "منصتنا بتمسح آلاف الوظائف من مصادر كتيرة لتلاقي الأنسب لمهاراتك وأهدافك.",
    "Choose job titles, locations, and salary range. We search across multiple engines in 50+ countries worldwide.": "نقي المسميات الوظيفية، الأماكن، ونطاق المعاش. منفتش عبر محركات كتيرة بـ 50+ بلد بالعالم.",
    "Auto Applications": "تقديم تلقائي",
    "30 Days": "30 يوم",
    "24 Hours": "24 ساعة",
    "Package Orders": "طلبات الباقات",
    "Redeem Codes": "أكواد مستخدمة",
    "Manual Emails": "إيميلات يدوية",
    "sales": "مبيعات",
    "used": "مستخدمة",
    "sent": "انبعتت",

    # Testimonials
    "What Our Users Say": "شو بيقولوا مستخدمينا",
    "Real results from real job seekers who transformed their job hunt.": "نتائج حقيقية من باحثين عن عمل غيروا طريقتهم بالبحث.",
    "I was spending 4 hours a day applying to jobs manually. This platform did more in one week than I did in three months. Landed two interviews in the first 10 days.": "كنت ضيع 4 ساعات كل يوم عم قدم ع الوظايف يدوياً. هالمنصة عملت بأسبوع أكتر من يلي عملته بـ 3 شهور. حصلت ع مقابلتين بأول 10 أيام.",
    "FAQ": "الأسئلة الشائعة",
    "All rights reserved.": "جميع الحقوق محفوظة.",
    "Payments:": "المدفوعات:",
}

def translate_html(filepath: str) -> None:
    """Read, parse, replace CSS/Logical properties, and translate HTML templates."""
    try:
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            return
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Replace CSS logical properties and fonts
        for pat, rep in css_replacements:
            content = re.sub(pat, rep, content)
            
        # Inject inputs dir="auto"
        content = re.sub(r'(<input[^>]+?)(/?>)', r'\1 dir="auto"\2', content)
        content = re.sub(r'(<textarea[^>]+?)(/?>)', r'\1 dir="auto"\2', content)

        # Replace specific text nodes
        for eng, arab in text_replacements.items():
            content = content.replace(eng, arab)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Successfully processed and translated {filepath}")
    except Exception as e:
        logger.error(f"Failed to process and translate {filepath}: {e}")
        raise

def main() -> None:
    """Run translation process for targeted template files."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        files_to_process: List[str] = [
            os.path.join(base_dir, "web", "templates", "index_v2.html"),
            os.path.join(base_dir, "web", "templates", "index_v3.html")
        ]
        for fp in files_to_process:
            translate_html(fp)
    except Exception as e:
        logger.error(f"Global HTML translation task failed: {e}")
        raise

if __name__ == "__main__":
    main()

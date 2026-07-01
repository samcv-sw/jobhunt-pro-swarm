import os
import re

files_to_process = [
    r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\index_v2.html",
    r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\index_v3.html"
]

css_replacements = [
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

text_replacements = {
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

    # Hero
    "Processing Applications Now": "عم نعالج الطلبات هلأ",
    "AI SYSTEM ONLINE — v{{ VERSION }}": "نظام الذكاء الاصطناعي شغال — الإصدار {{ VERSION }}",
    "Apply to <span class=\"cyan\">Thousands</span> of Jobs<br>": "قدم ع <span class=\"cyan\">آلاف</span> الوظائف<br>",
    "While You <span class=\"magenta\">Sleep</span>": "وإنت <span class=\"magenta\">نايم</span>",
    "Stop spending hours on job boards. Our intelligent platform applies to the right jobs for you &mdash; personalized applications, real-time tracking, and zero manual work.": "حاج تضيع ساعات ع مواقع التوظيف. منصتنا الذكية بتقدم ع الوظائف المناسبة إلك — طلبات مخصصة، تتبع مباشر، وبدون أي تعب يدوي.",
    "Your personal AI job-hunting engine works <strong style=\"color:var(--cyan)\">24/7</strong> — searching thousands of jobs, \n  crafting personalized applications, and sending them through smart email rotation. \n  <strong style=\"color:var(--gold)\">Less than 7 cents per application.</strong> Get hired or your money back.": "محركك الشخصي للبحث عن عمل شغال <strong style=\"color:var(--cyan)\">24/7</strong> — بيفتش بآلاف الوظائف،\n بيكتب طلبات مخصصة، وبيبعتها عبر نظام تدوير الإيميلات.\n <strong style=\"color:var(--gold)\">أقل من 7 سنت للطلب.</strong> توظف أو منرجعلك مصرياتك.",
    "Start Free Trial": "جرب مجاناً",
    "Start Applying Now — It's Free": "بلّش تقديم هلأ — مجاناً",
    "View Pricing Plans": "شوف خطط الأسعار",
    "See How It Works": "شوف كيف بتشتغل",
    
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
    "AI Does The Work": "الذكاء الاصطناعي بيشتغل عنك",
    "Personalized applications are sent automatically. Each one is unique &mdash; tailored to the company and role you're targeting.": "الطلبات المخصصة بتنبعت تلقائياً. كل طلب فريد — ومفصل ع قياس الشركة والوظيفة يلي عم تستهدفها.",
    "Hundreds of AI agents craft unique cover letters for each company and send through smart email rotation. Zero spam flags.": "مئات العملاء الذكيين بيكتبوا رسائل تغطية فريدة لكل شركة وبيبعتوها عبر تدوير ذكي للإيميلات. مستحيل تنزل بالسبام.",
    "Track & Follow Up": "تتبع وتابع",
    "Get Interviews": "احصل ع مقابلات",
    "Monitor every application, track email opens, and get automatic follow-ups. Never miss an opportunity.": "راقب كل طلب، تابع فتح الإيميلات، واحصل ع متابعات تلقائية. ما تضيع ولا فرصة.",
    "Track opens, clicks, and responses in real-time. Automatic follow-ups ensure maximum response rates. Land the job.": "تابع الفتح، الكبسات، والردود بالوقت الفعلي. المتابعات التلقائية بتضمن أعلى نسبة ردود. وحصل ع الوظيفة.",

    # Features
    "Features": "الميزات",
    "PLATFORM FEATURES": "ميزات المنصة",
    "Everything You Need<br>to Get Hired": "كل شي بتحتاجه<br>لتتوظف",
    "Everything You <span class=\"gradient\">Need</span>": "كل شي <span class=\"gradient\">بتحتاجه</span>",
    "A complete job hunting toolkit &mdash; from application to interview, all in one place.": "مجموعة أدوات متكاملة للبحث عن عمل — من التقديم للمقابلة، كله بمكان واحد.",
    "A complete job application arsenal — every tool you need to automate your entire job search, built right in.": "ترسانة كاملة للتقديم ع الوظائف — كل أداة بتحتاجها لأتمتة بحثك عن عمل، موجودة هون.",
    "Smart Cover Letters": "رسائل تغطية ذكية",
    "Every application gets a unique, personalized cover letter that highlights your strengths for that specific role.": "كل طلب بياخد رسالة تغطية فريدة ومخصصة بتبرز نقاط قوتك لهالوظيفة بالذات.",
    "AI-Powered Personalization": "تخصيص بالذكاء الاصطناعي",
    "Advanced AI crafts unique, personalized cover letters for every single company. Reads the job description, understands requirements, and tailors perfectly — never generic, never templated.": "ذكاء اصطناعي متطور بيكتب رسائل تغطية فريدة ومخصصة لكل شركة. بيقرا الوصف الوظيفي وبيفهم المتطلبات وبيفصلها ع القد — مش قوالب جاهزة.",
    "Multi-Source Search": "بحث متعدد المصادر",
    "Jobs are sourced from multiple platforms simultaneously &mdash; you get maximum coverage without lifting a finger.": "الوظايف بتنجاب من منصات كتيرة بنفس الوقت — لتحصل ع أكبر تغطية بدون ما تحرك إصبعك.",
    "Multi-Engine Job Search": "بحث بمحركات متعددة",
    "We search across all major platforms — every job board, every company career page, every listing worldwide. 50+ countries, all industries, all levels.": "منفتش بكل المنصات الكبيرة — كل مواقع التوظيف، صفحات الشركات، وكل الإعلانات بالعالم. 50+ بلد، كل المجالات وكل المستويات.",
    "High-Speed Processing": "معالجة سريعة",
    "Hundreds of applications processed in parallel. What used to take weeks now takes hours.": "مئات الطلبات بتتعالج بنفس الوقت. يلي كان ياخد أسابيع صار ياخد ساعات.",
    "Multi-Provider Email System": "نظام إيميلات متعدد",
    "Smart rotation across 20+ email providers with intelligent warmup, spam-score checking, and automatic fallback. Your applications always land in the inbox, never in spam.": "تدوير ذكي بين 20+ مزود إيميل مع تحمية ذكية وفحص للسبام وتراجع تلقائي. طلباتك دايماً بتوصل للإنبوكس، مش للسبام.",
    "Real-Time Dashboard": "لوحة تحكم مباشرة",
    "Track every application, email open, and response from a beautiful live dashboard. Full visibility at all times.": "تابع كل طلب، وكل فتح إيميل، والردود من لوحة تحكم حية وحلوة. رؤية كاملة بكل الأوقات.",
    "Real-Time Analytics": "تحليلات بالوقت الفعلي",
    "Visual pipeline tracks every application: Discovered → Applied → Followed Up → Interview → Offer. Track opens, clicks, and responses in real-time with your personal dashboard.": "مسار مرئي بيتابع كل طلب: اكتشفناه → قدمنا → تابعنا → مقابلة → عرض. تابع الفتح والكبسات والردود مباشرة من لوحتك الشخصية.",
    "Auto Follow-Ups": "متابعات تلقائية",
    "Automatic Follow-Ups": "متابعات تلقائية",
    "Never miss a lead. Automated follow-up emails sent at optimal intervals to keep you top of mind with recruiters.": "ما تضيع ولا فرصة. إيميلات متابعة تلقائية بتنبعت بأوقات مدروسة لتخليك ببال مسؤولي التوظيف.",
    "If no response, our system automatically sends polite, personalized follow-up emails. Boosts response rates by up to 40%. Never miss an opportunity because you forgot to follow up.": "إذا ما في رد، نظامنا بيبعت إيميلات متابعة مهذبة ومخصصة تلقائياً. بترفع نسبة الرد لـ 40%. ما رح تضيع أي فرصة بس لأنك نسيت تتابع.",
    "Human-Like Delivery": "توصيل متل البشر",
    "Applications are sent naturally with intelligent timing &mdash; looks like a real person, not a robot.": "الطلبات بتنبعت بشكل طبيعي مع توقيت ذكي — بتبين كأنها من شخص حقيقي، مش روبوت.",
    "Stealth Protection": "حماية مخفية",
    "Smart delays, human-like timing patterns, and sophisticated anti-detection. Email providers never flag you. Sophisticated algorithms keep you completely under the radar.": "تأخير ذكي، وتوقيت متل البشر، وتفادي متطور للكشف. مزودين الإيميلات ما رح يعطوك فلاج أبدًا. خوارزميات متطورة بتخليك تحت الرادار تماماً.",

    # Stats / Social Proof
    "By The Numbers": "بالأرقام",
    "Trusted by Thousands<br>of Job Seekers": "موثوقة من آلاف<br>الباحثين عن عمل",

    # Pricing
    "Choose Your Plan": "نقي خطتك",
    "One-time payment. No subscriptions. Pay with crypto or card. Simple, transparent, effective.": "دفعة وحدة. ما في اشتراكات. ادفع بالكريبتو أو بالبطاقة. بسيطة، شفافة، وفعالة.",
    "PRICING PLANS": "خطط الأسعار",
    "Simple, <span class=\"gradient\">Transparent</span> Pricing": "أسعار بسيطة و<span class=\"gradient\">شفافة</span>",
    "One-time payment. No subscription. No hidden fees. Pay with crypto.": "دفعة وحدة. ما في اشتراك. ما في رسوم مخفية. ادفع بالكريبتو.",
    "Professional": "محترف",
    "PRO": "برو",
    "Unlimited": "غير محدود",
    "UNLIMITED": "أنليميتد",
    "Enterprise": "شركات",
    "ENTERPRISE": "إنتربرايز",
    "STARTER": "ستارتر",
    "Starter": "بداية",
    "BASIC": "بيسك",
    "Basic": "أساسي",
    "PROFESSIONAL": "احترافي",
    "Pro": "برو",
    "companies": "شركات",
    "applications": "طلبات",
    "per company": "لكل شركة",
    "SAVE 64% VS PRO": "وفر 64% عن البرو",
    "MOST POPULAR": "الأكثر طلباً",
    "BEST VALUE": "أفضل قيمة",
    "MOST APPLICATIONS": "أكبر عدد طلبات",
    "Get Started": "بلّش هلأ",
    "Unlock Unlimited &#9889;": "افتح الأنليميتد &#9889;",
    "Contact Sales": "تواصل مع المبيعات",
    "Get Basic Now": "خد البيسك هلأ",
    "Get Pro Now": "خد البرو هلأ",
    "company applications": "طلبات شركات",
    "Smart cover letters": "رسائل تغطية ذكية",
    "Email tracking": "تتبع الإيميلات",
    "Follow-up automation": "أتمتة المتابعات",
    "Basic analytics": "تحليلات أساسية",
    "Personalized cover letters": "رسائل تغطية مخصصة",
    "Real-time email tracking": "تتبع إيميلات مباشر",
    "Auto follow-ups (7 + 14 days)": "متابعات تلقائية (7 + 14 يوم)",
    "Advanced analytics dashboard": "لوحة تحليلات متطورة",
    "Full-speed processing": "معالجة بأقصى سرعة",
    "Multi-email rotation": "تدوير إيميلات متعدد",
    "Company research": "أبحاث عن الشركات",
    "Interview prep generator": "توليد تحضيرات للمقابلة",
    "Priority support": "دعم أولوية",
    "Everything in Unlimited": "كل شي بالأنليميتد",
    "Custom training": "تدريب مخصص",
    "Dedicated account manager": "مدير حساب مخصص",
    "SLA guarantee": "ضمان مستوى الخدمة (SLA)",
    "White-label option": "خيار العلامة البيضاء",

    # Earnings Tracker
    "Live Revenue Tracker": "تتبع الأرباح المباشر",
    "Total Revenue Generated": "إجمالي الأرباح المحققة",
    "All Time": "كل الوقت",
    "This Year": "هالسنة",
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
    "The quality of cover letters blew me away. Each one felt hand-written and specific to the company. Got a response rate I never thought possible. Absolutely worth every penny.": "نوعية رسائل التغطية فاجأتني. كل رسالة بتبين كأنها مكتوبة بالإيد ومخصصة للشركة. حصلت ع نسبة ردود ما كنت بحلم فيها. بتستاهل كل قرش.",
    "Applied to 500 companies in the Gulf region in one go. The tracking dashboard is incredible &mdash; I know exactly who opened my emails and when to follow up. Game changer.": "قدمت لـ 500 شركة بالخليج بكبسة وحدة. لوحة التتبع خرافية — بعرف بالضبط مين فتح إيميلاتي وإيمتى لازم تابع. هالمنصة غيرت اللعبة.",
    
    # FAQ
    "Frequently Asked<br>Questions": "الأسئلة<br>الشائعة",
    "Frequently <span class=\"gradient\">Asked</span> Questions": "الأسئلة <span class=\"gradient\">الشائعة</span>",
    "How does the application process work?": "كيف بتم عملية التقديم؟",
    "You upload your CV, tell us what kind of jobs you want (role, location, industry), and our platform handles the rest. It searches for matching jobs across multiple sources, generates personalized cover letters, and sends applications on your behalf. You can monitor everything from your dashboard.": "بترفع سيرتك الذاتية، بتقولنا شو نوع الوظايف يلي بدك ياها (الدور، المكان، المجال)، ومنصتنا بتتكفل بالباقي. بتفتش ع الوظايف المناسبة من مصادر كتيرة، بتعمل رسائل تغطية مخصصة، وبتبعت الطلبات بالنيابة عنك. وفيك تراقب كل شي من لوحة التحكم تبعك.",
    "Is this safe? Will my email get blocked?": "هل هيدا آمن؟ رح ينعمل بلوك لإيميلي؟",
    "Yes, it's completely safe. Applications are sent with natural timing and intelligent scheduling &mdash; exactly like a real person would. We use multiple email rotation and follow sending best practices to keep your deliverability high and avoid spam filters.": "أكيد آمن. الطلبات بتنبعت بتوقيت طبيعي وجدولة ذكية — تماماً متل أي شخص حقيقي. منستخدم تدوير لعدة إيميلات ومنتبع أفضل الطرق لنحافظ ع نسبة وصول عالية ونتجنب فلاتر السبام.",
    "What regions and countries do you cover?": "شو هي المناطق والبلدان يلي بتغطوها؟",
    "We cover jobs worldwide, with strong coverage in Lebanon, UAE, Saudi Arabia, Qatar, Kuwait, and remote positions globally. You can target any country or combination of countries you prefer.": "منغطي وظايف بكل العالم، مع تركيز قوي ع لبنان، الإمارات، السعودية، قطر، الكويت، والوظايف عن بُعد. فيك تستهدف أي بلد أو مجموعة بلدان بدك ياها.",
    "How are the cover letters personalized?": "كيف بتتخصص رسائل التغطية؟",
    "Every cover letter is generated fresh for each application. The system analyzes the company name, job title, your skills, and work history to create a unique, compelling letter that highlights why you're the right fit for that specific role.": "كل رسالة تغطية بتنعمل من الصفر لكل طلب. النظام بيحلل اسم الشركة، المسمى الوظيفي، مهاراتك، وتاريخك المهني ليعمل رسالة فريدة ومقنعة بتوضح ليش إنت الشخص المناسب لهالدور.",
    "Can I track my applications?": "فيني تابع طلباتي؟",
    "Absolutely. Your dashboard shows every application sent, email open rates, click tracking, and response monitoring. You'll also get automatic follow-ups sent at optimal intervals to maximize your chances of getting noticed.": "أكيد. لوحتك بتفرجيك كل طلب انبعت، نسبة فتح الإيميلات، تتبع الكبسات، ومراقبة الردود. كمان رح تحصل ع متابعات تلقائية بتنبعت بأوقات مناسبة لتزيد فرصك تنشاف.",
    "What payment methods do you accept?": "شو هي طرق الدفع يلي بتقبلوها؟",
    "We accept cryptocurrency (BTC, ETH, USDT, LTC) and credit/debit cards. All plans are one-time payments &mdash; no recurring subscriptions or hidden fees. What you see is what you pay.": "منقبل العملات الرقمية (BTC, ETH, USDT, LTC) وبطاقات الائتمان. كل الخطط عبارة عن دفعة وحدة — ما في اشتراكات ولا رسوم مخفية. يلي بتشوفه هو يلي بتدفعه.",

    # CTA
    "Ready to Land Your<br><span class=\"gradient-text\">Dream Job?</span>": "جاهز تلاقي<br><span class=\"gradient-text\">وظيفة أحلامك؟</span>",
    "Join thousands of job seekers who have already transformed their job hunt. Stop applying manually and start getting results.": "انضم لآلاف الباحثين عن عمل يلي غيروا طريقتهم بالبحث. حاج تقدم يدوياً وبلش احصد نتائج.",
    "Get Started Free": "بلش مجاناً",

    # Footer
    "The smartest way to job hunt. Thousands of applications, zero manual work. Your career deserves better.": "أذكى طريقة للبحث عن عمل. آلاف الطلبات، وبدون تعب يدوي. مستقبلك المهني بيستاهل أحسن.",
    "Product": "المنتج",
    "Resources": "المصادر",
    "Contact": "تواصل معنا",
    "Email Support": "الدعم عبر الإيميل",
    "Telegram": "تيليغرام",
    "All rights reserved.": "جميع الحقوق محفوظة.",
    "Payments:": "المدفوعات:"
}

def translate_html(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
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
    print(f"Processed {filepath}")

for fp in files_to_process:
    translate_html(fp)

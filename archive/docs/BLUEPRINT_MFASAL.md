# 🚀 المخطط المعماري الشامل والدقيق (Detailed Master Blueprint) 
**نظام JobHunt Pro - إصدار The Final Boss (Always-On God-Mode V2)**

هذا المستند يمثل التشريح الهندسي العميق والمفصل (مفصل تفصيل) لكل سطر كود وكل قاعدة بيانات وكل آلية عمل داخل مشروعك.

---

## 🗄️ 1. هندسة قواعد البيانات (Database Architecture)
النظام يعتمد على قاعدة بيانات **Neon PostgreSQL** كسيرفر أساسي، مع طبقة حماية (Shim) تسمى `pg_sqlite_shim.py` تحول أوامر SQLite القديمة إلى PostgreSQL تلقائياً، ما يسمح للكود بالعمل على السحابة بدون أخطاء.

### الجداول الأساسية (Tables Schema):
1. **جدول المستخدمين `users`**:
   - `user_id` (المعرف الأساسي)
   - `email`, `password_hash`, `name`, `phone`, `company_name`
   - `api_key`, `tokens` (رصيد المستخدم)
   - `subscription_status`, `subscription_end_date` (للتحكم بالباقات)
   - `squad_id`, `referral_code` (لبرنامج الإحالة والنمو الفيروسي).

2. **جدول الوظائف `jobs`**:
   - يخزن الوظائف المسحوبة: `job_id`, `title`, `company`, `location`, `url`, `description`, `source`, `salary_range`, `posted_date`.

3. **جدول التقديمات `applications`**:
   - `user_id`, `job_id` (ربط المستخدم بالوظيفة)
   - `status`: (pending, applied, failed, followed_up)
   - `ai_cover_letter`: (رسالة التغطية المولدة بالذكاء الاصطناعي)
   - `retry_count`, `locked_at` (لمنع التكرار في المعالجة المتوازية).

4. **جدول الفرق الفيروسية `job_squads`**:
   - مقتبس من نظام Pinduoduo الصيني للنمو السريع، يحتوي على: `squad_id`, `owner_id`, `member_count`, `is_complete`.

5. **جدول ذكاء السرب `swarm_intelligence`**:
   - يحفظ الكلمات المفتاحية الناجحة التي أدت لمقابلات: `company`, `successful_keywords`, `interview_rate`.

---

## ⚙️ 2. دورة العمليات الأساسية (Core Engine & Orchestration)
القلب النابض للنظام موجود في مجلد `core/` ويعمل بالترتيب التالي:

### أ. السحب والبحث (Scraping & Harvesting)
- **`multi_source_scraper.py` و `pa_job_scraper.py`**: يعملان بتقنية (Concurrent Threads) للبحث في 7 مصادر بنفس الوقت (LinkedIn, Indeed, Glassdoor, Remotive, Arbeitnow, hh.ru, JSearch).
- **الجلب الذكي للمخفيين (Shadow HR)**: عبر `linkedin_engine.py`، حيث يتم تخمين بريد مسؤول التوظيف من خلال اسم الشركة بعد إزالة اللواحق القانونية (مثل Inc, LLC) للحصول على نطاق صحيح (Domain Guessing).

### ب. فلترة وتقييم السيرة الذاتية (ATS Cracking)
- **`ats_matcher.py` و `ats_scorer.py`**: يتم تحليل الوصف الوظيفي (Description) باستخدام `Regex` مُجمَّع مسبقاً (Precompiled) لسحب الكلمات المفتاحية ومطابقتها مع السيرة الذاتية.
- **`ai_tailor.py` و `resume_optimizer.py`**: إذا كانت المطابقة ضعيفة، يتدخل الذكاء الاصطناعي (عبر API مثل Groq/Llama-3) لتعديل خبرات المستخدم ودمج الكلمات المفتاحية الناقصة لتخطي الـ ATS.

### ج. محرك الإرسال والتدوير (Email Rotator Engine)
- **`email_engine.py` و `email_rotator_pool.py`**: لا يتم إرسال الإيميلات من حساب واحد! النظام يمتلك 19 مزود إيميل (Gmail, Outlook, Zoho, SendGrid, Mailgun, إلخ).
- **الخوارزمية**: يتم إرسال الدفعات (Batches) بشكل متوازٍ باستخدام `asyncio.gather`، مع تبديل الإيميل المرسل (Round-Robin) لتفادي الحظر (Spam Filters).

### د. المتابعة ومقاومة التجاهل (Anti-Ghosting Follow-up)
- **`response_parser.py`**: عندما يرد مسؤول التوظيف، يقرأ السكريبت الرد. باستخدام تقنيات (Regex Negation Look-behind)، يميز بين (رفض، مقابلة، عرض). فمثلاً لو احتوى الرد على "not proceed"، لن يعتبره مقابلة بالرغم من وجود كلمة "proceed".
- **الجدولة العشوائية**: المتابعات التلقائية لا ترسل بعد 3 أيام بالضبط لتفادي كشفها كبوت، بل تستخدم تشفير MD5 لبريد الشركة لإضافة تأخير عشوائي (Delay Offset) من 0 إلى يومين.

---

## 🛡️ 3. تقنيات التخفي العميقة (Stealth & Anti-Ban Protocols)
كيف تمنع المواقع من حظر السيرفر؟
1. **تزييف الهاردوير (WebGL/GPU Spoofing)**: `stealth.py` يخدع المواقع ليظنوا أنك تستخدم جهاز `Apple M3 Max`.
2. **تشويش البصمة (Canvas Micro-noise)**: إضافة تشويش غير مرئي لصور الكانفاس لمنع تقفي أثر الجهاز (Fingerprinting).
3. **توليد IP لجوجل بوت**: السكريبت يولد آيبيات عشوائية تقع حصراً ضمن نطاق عناوين خوادم جوجل الرسمية (`66.249.64.0/19`)، ثم يحقنها في هيدر `X-Forwarded-For` لتبدو الزيارات وكأنها زحف شرعي من محرك بحث Google.
4. **قاهر الكابتشا (Gemini Vision)**: `captcha_solver.py` يلتقط صورة للكابتشا، يرسلها لـ Gemini 2.0 Flash لتحديد إحداثيات (X, Y)، ثم يقوم `human_mouse.py` بتحريك الفأرة بانسيابية بشرية للنقر عليها.

---

## 🌐 4. واجهة الويب والخوادم (Web Server & FastAPI)
- الملف الرئيسي هو `web/app_v2.py` (يحتوي على آلاف الأسطر البرمجية).
- **المصادقة (Auth)**: تعتمد على الـ Cookies المشفرة (بصلاحية 30 يوماً) باستخدام `URLSafeTimedSerializer`.
- **نظام التمويه (Iron Cloak)**: عند تفعيل `PANIC_MODE=1`، يقوم `iron_cloak.py` باعتراض أي زائر ويظهر له "مدونة بريئة لكتابة السير الذاتية" بدلاً من لوحة تحكم الاختراق الأوتوماتيكية، لحماية النظام من المراجعين البشريين (Auditors).
- **جدار الحماية (Aegis WAF)**: يقوم `aegis_shield.py` بفلترة أي طلبات خبيثة (مثل SQL Injection أو XSS) قبل أن تصل للخادم الأساسي.

---

## 🔌 5. الإضافات وأدوات الوصول (Extensions & Miniapps)
- **إضافة كروم (Chrome Extension)**: موجودة في `chrome_extension/`، تحقن أوامر برمجية (`scraper-content.js`) في المواقع وتتواصل مع الخادم المحلي.
- **تطبيق تليجرام (Telegram Miniapp)**: موجود في `telegram_miniapp/` (HTML/JS/CSS)، يفتح لوحة التحكم الخاصة بالمستخدمين مباشرة داخل تطبيق تليجرام بدون الحاجة لمتصفح.

---

## ☁️ 6. الاستضافة المجانية الأبدية (Hugging Face Infinite Loop)
- **المشكلة**: استضافة Hugging Face المجانية (2vCPU / 16GB RAM) تنام إذا لم يكن هناك زيارات.
- **الحل السحري**: ملف `auto_apply.yml` (عبر GitHub Actions) يستيقظ كل 20 دقيقة، يرسل `Ping` (طلب شبكة خفيف) إلى السيرفر ليقول له "لا تنم"، ثم يغلق. هذا يضمن عمل السيرفر 24/7 بتكلفة صفر دولار للأبد.

---

هذا المخطط يغطي الهيكل التنظيمي، الأمان، الذكاء الاصطناعي، وقواعد البيانات بالتفصيل الدقيق الذي طلبته! 🚀

# Form and Button Audit Report — JobHunt Pro

This report details the baseline audit of all forms, buttons, inputs, textareas, and selects in the application's Jinja2 templates (`web/templates/`) and the Next.js frontend dashboard (`frontend/src/app/page.tsx`).

## Executive Summary
- **Total Files Audited**: 139
- **Total Endpoint Mappings Found in Backend/Web Routers**: 375
- **Files with Issues**: 89
  
### Key Compliance Checks Performed:
1. **Unique HTML IDs**: Every form, button, and input control must have a unique HTML `id` attribute.
2. **Proper Visual States**: Form elements and buttons must have proper `:hover`, `:focus`, and `:active` CSS styling (or class representation).
3. **Bi-directional Support**: All text inputs and textareas must have `dir="auto"` to automatically detect and support Arabic (RTL) vs. English (LTR) script directions.
4. **Localization Compliance**: Placeholders must use dynamic translation templates/variables, avoiding hardcoded static placeholders.
5. **Backend Endpoint Verification**: Form action destinations must correspond to active REST or web page router routes.

---

## Overall Summary of Violations by File

| File | Forms | Inputs | Textareas | Buttons | Selects | Duplicate IDs |
|---|---|---|---|---|---|---|
| `frontend/src/app/page.tsx` | 1 | 3 | 0 | 1 | 0 | 0 |
| `templates/_dashboard_shell.html` | 0 | 0 | 0 | 1 | 0 | 0 |
| `templates/_public_shell.html` | 1 | 1 | 0 | 2 | 0 | 0 |
| `templates/_sidebar.html` | 0 | 0 | 0 | 2 | 0 | 0 |
| `templates/admin.html` | 8 | 17 | 1 | 9 | 1 | 0 |
| `templates/admin_user.html` | 1 | 3 | 0 | 1 | 0 | 0 |
| `templates/antigravity.html` | 0 | 0 | 0 | 6 | 0 | 0 |
| `templates/ats_scorer.html` | 0 | 2 | 1 | 5 | 0 | 0 |
| `templates/battle_station.html` | 0 | 0 | 0 | 3 | 0 | 0 |
| `templates/candidate_profile.html` | 0 | 0 | 0 | 1 | 0 | 0 |
| `templates/checkout_v2.html` | 0 | 2 | 0 | 3 | 0 | 0 |
| `templates/checkout_v3.html` | 0 | 2 | 0 | 3 | 0 | 0 |
| `templates/contact.html` | 1 | 2 | 1 | 1 | 0 | 0 |
| `templates/dashboard_v3.html` | 1 | 2 | 0 | 7 | 0 | 0 |
| `templates/email_test.html` | 0 | 3 | 3 | 7 | 0 | 0 |
| `templates/employer_track.html` | 0 | 2 | 0 | 1 | 0 | 0 |
| `templates/en/_base_tailwind.html` | 0 | 0 | 0 | 1 | 0 | 0 |
| `templates/en/_public_shell.html` | 1 | 1 | 0 | 2 | 0 | 0 |
| `templates/en/_sidebar.html` | 0 | 0 | 0 | 2 | 0 | 0 |
| `templates/en/admin.html` | 8 | 17 | 1 | 9 | 1 | 0 |
| `templates/en/admin_user.html` | 1 | 3 | 0 | 1 | 0 | 0 |
| `templates/en/antigravity.html` | 0 | 0 | 0 | 6 | 0 | 0 |
| `templates/en/ats_scorer.html` | 0 | 2 | 2 | 5 | 0 | 0 |
| `templates/en/battle_station.html` | 0 | 0 | 0 | 3 | 0 | 0 |
| `templates/en/candidate_profile.html` | 0 | 0 | 0 | 1 | 0 | 0 |
| `templates/en/checkout_v2.html` | 0 | 2 | 0 | 3 | 0 | 0 |
| `templates/en/checkout_v3.html` | 0 | 2 | 0 | 3 | 0 | 0 |
| `templates/en/contact.html` | 1 | 2 | 1 | 1 | 0 | 0 |
| `templates/en/dashboard_v3.html` | 1 | 2 | 0 | 7 | 0 | 0 |
| `templates/en/email_test.html` | 0 | 3 | 3 | 7 | 0 | 0 |
| `templates/en/employer_track.html` | 0 | 2 | 0 | 1 | 0 | 0 |
| `templates/en/export.html` | 0 | 2 | 0 | 6 | 0 | 0 |
| `templates/en/for_employers.html` | 0 | 7 | 1 | 10 | 0 | 0 |
| `templates/en/forgot_password.html` | 0 | 1 | 0 | 1 | 0 | 0 |
| `templates/en/funnel_analytics.html` | 0 | 0 | 0 | 4 | 0 | 0 |
| `templates/en/growth_station.html` | 0 | 4 | 0 | 7 | 0 | 0 |
| `templates/en/index_v2.html` | 0 | 0 | 0 | 5 | 0 | 0 |
| `templates/en/index_v3.html` | 0 | 0 | 0 | 5 | 0 | 0 |
| `templates/en/index_v4.html` | 0 | 2 | 0 | 11 | 0 | 0 |
| `templates/en/login.html` | 1 | 2 | 0 | 1 | 0 | 0 |
| `templates/en/login_v2.html` | 0 | 3 | 0 | 2 | 0 | 0 |
| `templates/en/my_purchases.html` | 0 | 0 | 0 | 1 | 0 | 0 |
| `templates/en/new_campaign_v2.html` | 0 | 2 | 0 | 3 | 0 | 0 |
| `templates/en/offers.html` | 3 | 12 | 7 | 16 | 0 | 0 |
| `templates/en/pricing_v2.html` | 0 | 0 | 0 | 1 | 0 | 0 |
| `templates/en/pricing_v3.html` | 0 | 0 | 0 | 1 | 0 | 0 |
| `templates/en/register.html` | 1 | 5 | 0 | 1 | 0 | 0 |
| `templates/en/register_v2.html` | 0 | 5 | 0 | 2 | 0 | 0 |
| `templates/en/reset_password.html` | 0 | 3 | 0 | 3 | 0 | 0 |
| `templates/en/resume_tailor.html` | 0 | 1 | 2 | 5 | 0 | 0 |
| `templates/en/roast.html` | 0 | 0 | 0 | 1 | 0 | 0 |
| `templates/en/sent_emails.html` | 0 | 1 | 0 | 2 | 0 | 0 |
| `templates/en/services.html` | 3 | 9 | 0 | 8 | 0 | 0 |
| `templates/en/services_new.html` | 0 | 0 | 0 | 10 | 0 | 0 |
| `templates/en/services_v2.html` | 0 | 2 | 0 | 9 | 0 | 0 |
| `templates/en/track_application.html` | 1 | 1 | 0 | 1 | 0 | 0 |
| `templates/en/upload_cv_v2.html` | 0 | 12 | 2 | 12 | 0 | 0 |
| `templates/en/upload_cv_v3.html` | 0 | 7 | 0 | 5 | 0 | 0 |
| `templates/en/wallet.html` | 2 | 1 | 0 | 18 | 0 | 0 |
| `templates/en/war_room.html` | 0 | 0 | 1 | 4 | 0 | 0 |
| `templates/export.html` | 0 | 2 | 0 | 6 | 0 | 0 |
| `templates/for_employers.html` | 0 | 7 | 1 | 10 | 0 | 0 |
| `templates/forgot_password.html` | 0 | 1 | 0 | 1 | 0 | 0 |
| `templates/funnel_analytics.html` | 0 | 0 | 0 | 4 | 0 | 0 |
| `templates/growth_station.html` | 0 | 4 | 0 | 7 | 0 | 0 |
| `templates/index_v2.html` | 0 | 0 | 0 | 5 | 0 | 0 |
| `templates/index_v3.html` | 0 | 0 | 0 | 5 | 0 | 0 |
| `templates/index_v4.html` | 0 | 2 | 0 | 11 | 0 | 0 |
| `templates/login.html` | 1 | 2 | 0 | 1 | 0 | 0 |
| `templates/login_v2.html` | 0 | 3 | 0 | 2 | 0 | 0 |
| `templates/my_purchases.html` | 0 | 0 | 0 | 1 | 0 | 0 |
| `templates/new_campaign_v2.html` | 0 | 2 | 0 | 3 | 0 | 0 |
| `templates/offers.html` | 3 | 12 | 7 | 16 | 0 | 0 |
| `templates/pricing_v2.html` | 0 | 0 | 0 | 1 | 0 | 0 |
| `templates/pricing_v3.html` | 0 | 0 | 0 | 1 | 0 | 0 |
| `templates/register.html` | 1 | 5 | 0 | 1 | 0 | 0 |
| `templates/register_v2.html` | 0 | 5 | 0 | 2 | 0 | 0 |
| `templates/reset_password.html` | 0 | 3 | 0 | 3 | 0 | 0 |
| `templates/resume_tailor.html` | 0 | 1 | 2 | 5 | 0 | 0 |
| `templates/roast.html` | 0 | 0 | 0 | 1 | 0 | 0 |
| `templates/sent_emails.html` | 0 | 1 | 0 | 2 | 0 | 0 |
| `templates/services.html` | 3 | 9 | 0 | 8 | 0 | 0 |
| `templates/services_new.html` | 0 | 0 | 0 | 10 | 0 | 0 |
| `templates/services_v2.html` | 0 | 2 | 0 | 9 | 0 | 0 |
| `templates/track_application.html` | 1 | 1 | 0 | 1 | 0 | 0 |
| `templates/upload_cv_v2.html` | 0 | 13 | 2 | 12 | 0 | 0 |
| `templates/upload_cv_v3.html` | 0 | 7 | 0 | 5 | 0 | 0 |
| `templates/wallet.html` | 2 | 1 | 0 | 18 | 0 | 0 |
| `templates/war_room.html` | 0 | 0 | 1 | 4 | 0 | 0 |

---

## Detailed File-by-File Breakdown of Issues

### File: `frontend/src/app/page.tsx`

#### Form Elements:
- **Line 430**: Form (Action: `None`) → *Issues: Missing ID*

#### Input Elements:
- **Line 254**: Input (ID: `tenant-name-input`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. Demo User"*
- **Line 436**: Input (ID: `smtp-email-input`, Type: `email`) → *Issues: Hardcoded placeholder: "name@domain.com"*
- **Line 450**: Input (ID: `smtp-pass-input`, Type: `password`) → *Issues: Hardcoded placeholder: "••••••••••••••••"*

#### Button Elements:
- **Line 411**: Button (ID: `clear-db-btn`, Class: `py-2 px-3 border border-red-500/20 text-red-400 text-sm font-semibold rounded-lg hover:bg-red-500/10 transition cursor-pointer leading-[1.8]`) → *Issues: Missing proper hover/focus classes (class: "py-2 px-3 border border-red-500/20 text-red-400 text-sm font-semibold rounded-lg hover:bg-red-500/10 transition cursor-pointer leading-[1.8]")*

---

### File: `templates/_dashboard_shell.html`

#### Button Elements:
- **Line 86**: Button (ID: `None`, Class: `md:hidden`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "md:hidden")*

---

### File: `templates/_public_shell.html`

#### Form Elements:
- **Line 184**: Form (Action: `None`) → *Issues: Missing ID*

#### Input Elements:
- **Line 185**: Input (ID: `None`, Type: `email`) → *Issues: Missing ID; Hardcoded placeholder: "أدخل بريدك الإلكتروني"*

#### Button Elements:
- **Line 181**: Button (ID: `None`, Class: `None`) → *Issues: Missing ID; No classes defined (missing hover/focus states)*
- **Line 186**: Button (ID: `None`, Class: `None`) → *Issues: Missing ID; No classes defined (missing hover/focus states)*

---

### File: `templates/_sidebar.html`

#### Button Elements:
- **Line 235**: Button (ID: `None`, Class: `hamburger`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "hamburger")*
- **Line 300**: Button (ID: `notif-mark-all-btn`, Class: `notif-mark-all`) → *Issues: Missing proper hover/focus classes (class: "notif-mark-all")*

---

### File: `templates/admin.html`

#### Form Elements:
- **Line 147**: Form (Action: `/admin/add-credits`) → *Issues: Missing ID*
- **Line 161**: Form (Action: `/admin/generate-code`) → *Issues: Missing ID*
- **Line 176**: Form (Action: `/admin/generate-code`) → *Issues: Missing ID*
- **Line 191**: Form (Action: `/admin/free-campaign`) → *Issues: Missing ID*
- **Line 202**: Form (Action: `/admin/send-manual-email`) → *Issues: Missing ID*
- **Line 217**: Form (Action: `/admin/create-flash-sale`) → *Issues: Missing ID*
- **Line 255**: Form (Action: `/admin/end-flash-sale`) → *Issues: Missing ID*
- **Line 334**: Form (Action: `/admin/toggle-user`) → *Issues: Missing ID*

#### Input Elements:
- **Line 149**: Input (ID: `None`, Type: `email`) → *Issues: Missing ID; Hardcoded placeholder: "user@email.com"*
- **Line 152**: Input (ID: `None`, Type: `number`) → *Issues: Missing ID; Hardcoded placeholder: "المبلغ $"*
- **Line 153**: Input (ID: `None`, Type: `text`) → *Issues: Missing ID*
- **Line 163**: Input (ID: `None`, Type: `number`) → *Issues: Missing ID; Hardcoded placeholder: "القيمة $"*
- **Line 164**: Input (ID: `None`, Type: `number`) → *Issues: Missing ID; Hardcoded placeholder: "العدد"*
- **Line 178**: Input (ID: `None`, Type: `number`) → *Issues: Missing ID; Hardcoded placeholder: "القيمة $"*
- **Line 179**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 180**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 193**: Input (ID: `None`, Type: `email`) → *Issues: Missing ID; Hardcoded placeholder: "user@email.com"*
- **Line 194**: Input (ID: `None`, Type: `number`) → *Issues: Missing ID*
- **Line 204**: Input (ID: `None`, Type: `email`) → *Issues: Missing ID; Hardcoded placeholder: "recipient@email.com"*
- **Line 205**: Input (ID: `None`, Type: `text`) → *Issues: Missing ID; Hardcoded placeholder: "موضوع الرسالة"*
- **Line 219**: Input (ID: `None`, Type: `text`) → *Issues: Missing ID; Hardcoded placeholder: "عنوان التخفيض (مثل: عرض نهاية الأسبوع)"*
- **Line 220**: Input (ID: `None`, Type: `number`) → *Issues: Missing ID; Hardcoded placeholder: "نسبة الخصم %"*
- **Line 221**: Input (ID: `None`, Type: `number`) → *Issues: Missing ID; Hardcoded placeholder: "ساعات"*
- **Line 256**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 335**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*

#### Textarea Elements:
- **Line 208**: Textarea (ID: `None`) → *Issues: Missing ID; Hardcoded placeholder: "محتوى الرسالة (HTML أو نص عادي)..."*

#### Button Elements:
- **Line 155**: Button (ID: `None`, Class: `btn btn-green`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-green")*
- **Line 170**: Button (ID: `None`, Class: `btn btn-purple`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-purple")*
- **Line 182**: Button (ID: `None`, Class: `btn btn-green`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-green")*
- **Line 196**: Button (ID: `None`, Class: `btn btn-blue`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-blue")*
- **Line 210**: Button (ID: `None`, Class: `btn btn-green`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-green")*
- **Line 223**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*
- **Line 257**: Button (ID: `None`, Class: `btn btn-red`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-red")*
- **Line 283**: Button (ID: `None`, Class: `copy-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "copy-btn")*
- **Line 336**: Button (ID: `None`, Class: `btn {% if u.is_active %}btn-red{% else %}btn-green{% endif %}`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn {% if u.is_active %}btn-red{% else %}btn-green{% endif %}")*

#### Select Elements:
- **Line 165**: Select (ID: `None`) → *Issues: Missing ID*

---

### File: `templates/admin_user.html`

#### Form Elements:
- **Line 48**: Form (Action: `/admin/add-credits`) → *Issues: Missing ID*

#### Input Elements:
- **Line 49**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 50**: Input (ID: `None`, Type: `number`) → *Issues: Missing ID; Hardcoded placeholder: "$"*
- **Line 51**: Input (ID: `None`, Type: `text`) → *Issues: Missing ID*

#### Button Elements:
- **Line 52**: Button (ID: `None`, Class: `btn btn-green`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-green")*

---

### File: `templates/antigravity.html`

#### Button Elements:
- **Line 248**: Button (ID: `btn-antigravity`, Class: `ctrl-btn active`) → *Issues: Missing proper hover/focus classes (class: "ctrl-btn active")*
- **Line 249**: Button (ID: `btn-gravity`, Class: `ctrl-btn`) → *Issues: Missing proper hover/focus classes (class: "ctrl-btn")*
- **Line 250**: Button (ID: `None`, Class: `ctrl-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "ctrl-btn")*
- **Line 251**: Button (ID: `None`, Class: `ctrl-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "ctrl-btn")*
- **Line 252**: Button (ID: `None`, Class: `ctrl-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "ctrl-btn")*
- **Line 253**: Button (ID: `None`, Class: `ctrl-btn danger`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "ctrl-btn danger")*

---

### File: `templates/ats_scorer.html`

#### Input Elements:
- **Line 107**: Input (ID: `ats-url`, Type: `url`) → *Issues: Hardcoded placeholder: "أو الصق رابط إعلان الوظيفة..."*
- **Line 125**: Input (ID: `ats-job-title`, Type: `text`) → *Issues: Hardcoded placeholder: "المسمى الوظيفي (اختياري، مثال: مهندس شبكات أول)"*

#### Textarea Elements:
- **Line 83**: Textarea (ID: `ats-resume`) → *Issues: Hardcoded placeholder: "الصق نص سيرتك الذاتية الكاملة هنا...

مثال:
سام سلامة
مهندس شبكات أول | CCNA، Fortinet NSE، MikroTik MTCNA
samsalameh.cv@gmail.com | +961 70 841 1009
linkedin.com/in/sam-salameh

ملخص مهني:
أكثر من 15 سنة خبرة في هندسة الشبكات المتخصصة في تصميم البنية التحتية..."*

#### Button Elements:
- **Line 109**: Button (ID: `btn-url-import`, Class: `ats-btn-secondary`) → *Issues: Missing proper hover/focus classes (class: "ats-btn-secondary")*
- **Line 132**: Button (ID: `btn-score`, Class: `ats-btn-primary`) → *Issues: Missing proper hover/focus classes (class: "ats-btn-primary")*
- **Line 135**: Button (ID: `btn-bulk-toggle`, Class: `ats-btn-secondary`) → *Issues: Missing proper hover/focus classes (class: "ats-btn-secondary")*
- **Line 152**: Button (ID: `btn-bulk-score`, Class: `ats-btn-primary`) → *Issues: Missing proper hover/focus classes (class: "ats-btn-primary")*
- **Line 157**: Button (ID: `None`, Class: `mt-4 px-4 py-2 border border-dashed border-slate-600 text-slate-400 hover:text-white hover:border-slate-400 hover:bg-slate-800/50 rounded-lg text-sm font-medium transition-all flex items-center gap-2 w-full justify-center`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "mt-4 px-4 py-2 border border-dashed border-slate-600 text-slate-400 hover:text-white hover:border-slate-400 hover:bg-slate-800/50 rounded-lg text-sm font-medium transition-all flex items-center gap-2 w-full justify-center")*

---

### File: `templates/battle_station.html`

#### Button Elements:
- **Line 246**: Button (ID: `None`, Class: `bs-btn green`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "bs-btn green")*
- **Line 247**: Button (ID: `None`, Class: `bs-btn red`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "bs-btn red")*
- **Line 248**: Button (ID: `None`, Class: `bs-btn green`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "bs-btn green")*

---

### File: `templates/candidate_profile.html`

#### Button Elements:
- **Line 24**: Button (ID: `None`, Class: `btn-primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-primary")*

---

### File: `templates/checkout_v2.html`

#### Input Elements:
- **Line 363**: Input (ID: `paymentCode`, Type: `text`) → *Issues: Hardcoded placeholder: "رمز الدفع (مثل A1B2C3D4)"*
- **Line 364**: Input (ID: `txHash`, Type: `text`) → *Issues: Hardcoded placeholder: "معرف المعاملة / TX ID"*

#### Button Elements:
- **Line 328**: Button (ID: `None`, Class: `btn-nowpayments`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-nowpayments")*
- **Line 341**: Button (ID: `None`, Class: `crypto-tab {% if loop.first %}active{% endif %}`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "crypto-tab {% if loop.first %}active{% endif %}")*
- **Line 365**: Button (ID: `verifyBtn`, Class: `btn-verify`) → *Issues: Missing proper hover/focus classes (class: "btn-verify")*

---

### File: `templates/checkout_v3.html`

#### Input Elements:
- **Line 584**: Input (ID: `paymentCodeV3`, Type: `text`) → *Issues: Hardcoded placeholder: "رمز الدفع (مثل A1B2C3D4)"*
- **Line 585**: Input (ID: `txHashV3`, Type: `text`) → *Issues: Hardcoded placeholder: "تجزئة المعاملة / TX ID"*

#### Button Elements:
- **Line 544**: Button (ID: `None`, Class: `btn-nowpayments-v3`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-nowpayments-v3")*
- **Line 557**: Button (ID: `None`, Class: `crypto-tab-v3 {% if loop.first %}active{% endif %}`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "crypto-tab-v3 {% if loop.first %}active{% endif %}")*
- **Line 586**: Button (ID: `verifyBtnV3`, Class: `btn-verify-v3`) → *Issues: Missing proper hover/focus classes (class: "btn-verify-v3")*

---

### File: `templates/contact.html`

#### Form Elements:
- **Line 91**: Form (Action: `/contact`) → *Issues: Missing ID*

#### Input Elements:
- **Line 95**: Input (ID: `name`, Type: `text`) → *Issues: Hardcoded placeholder: "اسمك الكريم"*
- **Line 99**: Input (ID: `email`, Type: `email`) → *Issues: Hardcoded placeholder: "you@example.com"*

#### Textarea Elements:
- **Line 117**: Textarea (ID: `message`) → *Issues: Hardcoded placeholder: "خبرنا شو ببالك... فيك تحط تفاصيل قد ما بدك — منقرا كل كلمة."*

#### Button Elements:
- **Line 119**: Button (ID: `None`, Class: `btn-submit`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-submit")*

---

### File: `templates/dashboard_v3.html`

#### Form Elements:
- **Line 294**: Form (Action: `None`) → *Issues: Missing ID*

#### Input Elements:
- **Line 492**: Input (ID: `smtpEmail`, Type: `email`) → *Issues: Hardcoded placeholder: "you@domain.com"*
- **Line 496**: Input (ID: `smtpPass`, Type: `password`) → *Issues: Hardcoded placeholder: "16-digit App Password"*

#### Button Elements:
- **Line 85**: Button (ID: `None`, Class: `flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-slate-300 transition-colors hover:bg-white/10 hover:text-white`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-slate-300 transition-colors hover:bg-white/10 hover:text-white")*
- **Line 168**: Button (ID: `None`, Class: `rounded-md px-3 py-1.5 text-sm font-medium transition-colors bg-indigo-500/20 text-indigo-300`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "rounded-md px-3 py-1.5 text-sm font-medium transition-colors bg-indigo-500/20 text-indigo-300")*
- **Line 169**: Button (ID: `None`, Class: `rounded-md px-3 py-1.5 text-sm font-medium text-slate-400 transition-colors hover:text-white`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "rounded-md px-3 py-1.5 text-sm font-medium text-slate-400 transition-colors hover:text-white")*
- **Line 170**: Button (ID: `None`, Class: `rounded-md px-3 py-1.5 text-sm font-medium text-slate-400 transition-colors hover:text-white`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "rounded-md px-3 py-1.5 text-sm font-medium text-slate-400 transition-colors hover:text-white")*
- **Line 295**: Button (ID: `None`, Class: `rounded-lg p-1 text-slate-400 hover:bg-white/10 hover:text-white`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "rounded-lg p-1 text-slate-400 hover:bg-white/10 hover:text-white")*
- **Line 479**: Button (ID: `None`, Class: `text-slate-400 hover:text-white`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "text-slate-400 hover:text-white")*
- **Line 499**: Button (ID: `smtpConnectBtn`, Class: `w-full rounded-lg bg-indigo-600 py-3 font-bold text-white transition-all hover:bg-indigo-500 mt-4 flex justify-center items-center gap-2`) → *Issues: Missing proper hover/focus classes (class: "w-full rounded-lg bg-indigo-600 py-3 font-bold text-white transition-all hover:bg-indigo-500 mt-4 flex justify-center items-center gap-2")*

---

### File: `templates/email_test.html`

#### Input Elements:
- **Line 105**: Input (ID: `fldTo`, Type: `email`) → *Issues: Hardcoded placeholder: "hr@company.com"*
- **Line 109**: Input (ID: `fldCompany`, Type: `text`) → *Issues: Hardcoded placeholder: "الشركة المستهدفة"*
- **Line 113**: Input (ID: `fldJob`, Type: `text`) → *Issues: Hardcoded placeholder: "مهندس شبكات"*

#### Textarea Elements:
- **Line 127**: Textarea (ID: `fldCV`) → *Issues: Hardcoded placeholder: "سيظهر نص سيرتك الذاتية هنا بعد رفع ملف PDF..."*
- **Line 140**: Textarea (ID: `fldCover`) → *Issues: Hardcoded placeholder: "سيتم إنشاء رسالة التغطية تلقائياً..."*
- **Line 150**: Textarea (ID: `fldEmail`) → *Issues: Hardcoded placeholder: "سيتم إنشاء محتوى البريد الإلكتروني تلقائياً..."*

#### Button Elements:
- **Line 122**: Button (ID: `None`, Class: `btn btn-xs btn-ai`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-xs btn-ai")*
- **Line 123**: Button (ID: `None`, Class: `btn btn-xs btn-pdf`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-xs btn-pdf")*
- **Line 135**: Button (ID: `None`, Class: `btn btn-xs btn-ai`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-xs btn-ai")*
- **Line 136**: Button (ID: `None`, Class: `btn btn-xs btn-pdf`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-xs btn-pdf")*
- **Line 147**: Button (ID: `None`, Class: `btn btn-xs btn-ai`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-xs btn-ai")*
- **Line 155**: Button (ID: `None`, Class: `btn btn-lg btn-primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-lg btn-primary")*
- **Line 156**: Button (ID: `None`, Class: `btn btn-md btn-outline`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-md btn-outline")*

---

### File: `templates/employer_track.html`

#### Input Elements:
- **Line 90**: Input (ID: `trackEmail`, Type: `email`) → *Issues: Hardcoded placeholder: "hr@yourcompany.com"*
- **Line 94**: Input (ID: `trackJobId`, Type: `text`) → *Issues: Hardcoded placeholder: "job_xxxxxxxxxxxx"*

#### Button Elements:
- **Line 96**: Button (ID: `None`, Class: `track-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "track-btn")*

---

### File: `templates/en/_base_tailwind.html`

#### Button Elements:
- **Line 136**: Button (ID: `None`, Class: `md:hidden p-2 text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors focus:outline-none`) → *Issues: Missing ID*

---

### File: `templates/en/_public_shell.html`

#### Form Elements:
- **Line 162**: Form (Action: `None`) → *Issues: Missing ID*

#### Input Elements:
- **Line 163**: Input (ID: `None`, Type: `email`) → *Issues: Missing ID; Hardcoded placeholder: "Enter your best email"*

#### Button Elements:
- **Line 159**: Button (ID: `None`, Class: `None`) → *Issues: Missing ID; No classes defined (missing hover/focus states)*
- **Line 164**: Button (ID: `None`, Class: `None`) → *Issues: Missing ID; No classes defined (missing hover/focus states)*

---

### File: `templates/en/_sidebar.html`

#### Button Elements:
- **Line 1**: Button (ID: `None`, Class: `hamburger`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "hamburger")*
- **Line 49**: Button (ID: `notif-mark-all-btn`, Class: `notif-mark-all`) → *Issues: Missing proper hover/focus classes (class: "notif-mark-all")*

---

### File: `templates/en/admin.html`

#### Form Elements:
- **Line 100**: Form (Action: `/admin/add-credits`) → *Issues: Missing ID*
- **Line 115**: Form (Action: `/admin/generate-code`) → *Issues: Missing ID*
- **Line 131**: Form (Action: `/admin/generate-code`) → *Issues: Missing ID*
- **Line 147**: Form (Action: `/admin/free-campaign`) → *Issues: Missing ID*
- **Line 159**: Form (Action: `/admin/send-manual-email`) → *Issues: Missing ID*
- **Line 176**: Form (Action: `/admin/create-flash-sale`) → *Issues: Missing ID*
- **Line 216**: Form (Action: `/admin/end-flash-sale`) → *Issues: Missing ID*
- **Line 296**: Form (Action: `/admin/toggle-user`) → *Issues: Missing ID*

#### Input Elements:
- **Line 102**: Input (ID: `None`, Type: `email`) → *Issues: Missing ID; Hardcoded placeholder: "user@email.com"*
- **Line 105**: Input (ID: `None`, Type: `number`) → *Issues: Missing ID; Hardcoded placeholder: "Amount $"*
- **Line 106**: Input (ID: `None`, Type: `text`) → *Issues: Missing ID*
- **Line 117**: Input (ID: `None`, Type: `number`) → *Issues: Missing ID; Hardcoded placeholder: "Value $"*
- **Line 118**: Input (ID: `None`, Type: `number`) → *Issues: Missing ID; Hardcoded placeholder: "Count"*
- **Line 133**: Input (ID: `None`, Type: `number`) → *Issues: Missing ID; Hardcoded placeholder: "Value $"*
- **Line 134**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 135**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 149**: Input (ID: `None`, Type: `email`) → *Issues: Missing ID; Hardcoded placeholder: "user@email.com"*
- **Line 150**: Input (ID: `None`, Type: `number`) → *Issues: Missing ID*
- **Line 161**: Input (ID: `None`, Type: `email`) → *Issues: Missing ID; Hardcoded placeholder: "recipient@email.com"*
- **Line 162**: Input (ID: `None`, Type: `text`) → *Issues: Missing ID; Hardcoded placeholder: "Email Subject"*
- **Line 178**: Input (ID: `None`, Type: `text`) → *Issues: Missing ID; Hardcoded placeholder: "Sale title (e.g. Weekend Blast)"*
- **Line 179**: Input (ID: `None`, Type: `number`) → *Issues: Missing ID; Hardcoded placeholder: "Discount %"*
- **Line 180**: Input (ID: `None`, Type: `number`) → *Issues: Missing ID; Hardcoded placeholder: "Hours"*
- **Line 217**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 297**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*

#### Textarea Elements:
- **Line 165**: Textarea (ID: `None`) → *Issues: Missing ID; Hardcoded placeholder: "Email body (HTML or plain text)..."*

#### Button Elements:
- **Line 108**: Button (ID: `None`, Class: `btn btn-green`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-green")*
- **Line 124**: Button (ID: `None`, Class: `btn btn-purple`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-purple")*
- **Line 137**: Button (ID: `None`, Class: `btn btn-green`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-green")*
- **Line 152**: Button (ID: `None`, Class: `btn btn-blue`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-blue")*
- **Line 168**: Button (ID: `None`, Class: `btn btn-green`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-green")*
- **Line 182**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*
- **Line 218**: Button (ID: `None`, Class: `btn btn-red`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-red")*
- **Line 244**: Button (ID: `None`, Class: `copy-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "copy-btn")*
- **Line 298**: Button (ID: `None`, Class: `btn {% if u.is_active %}btn-red{% else %}btn-green{% endif %}`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn {% if u.is_active %}btn-red{% else %}btn-green{% endif %}")*

#### Select Elements:
- **Line 119**: Select (ID: `None`) → *Issues: Missing ID*

---

### File: `templates/en/admin_user.html`

#### Form Elements:
- **Line 51**: Form (Action: `/admin/add-credits`) → *Issues: Missing ID*

#### Input Elements:
- **Line 52**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 53**: Input (ID: `None`, Type: `number`) → *Issues: Missing ID; Hardcoded placeholder: "$"*
- **Line 54**: Input (ID: `None`, Type: `text`) → *Issues: Missing ID*

#### Button Elements:
- **Line 55**: Button (ID: `None`, Class: `btn btn-green`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-green")*

---

### File: `templates/en/antigravity.html`

#### Button Elements:
- **Line 251**: Button (ID: `btn-antigravity`, Class: `ctrl-btn active`) → *Issues: Missing proper hover/focus classes (class: "ctrl-btn active")*
- **Line 252**: Button (ID: `btn-gravity`, Class: `ctrl-btn`) → *Issues: Missing proper hover/focus classes (class: "ctrl-btn")*
- **Line 253**: Button (ID: `None`, Class: `ctrl-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "ctrl-btn")*
- **Line 254**: Button (ID: `None`, Class: `ctrl-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "ctrl-btn")*
- **Line 255**: Button (ID: `None`, Class: `ctrl-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "ctrl-btn")*
- **Line 256**: Button (ID: `None`, Class: `ctrl-btn danger`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "ctrl-btn danger")*

---

### File: `templates/en/ats_scorer.html`

#### Input Elements:
- **Line 48**: Input (ID: `ats-url`, Type: `url`) → *Issues: Hardcoded placeholder: "Or paste a job posting URL..."*
- **Line 70**: Input (ID: `ats-job-title`, Type: `text`) → *Issues: Hardcoded placeholder: "Job title (optional, e.g. Senior Network Engineer)"*

#### Textarea Elements:
- **Line 22**: Textarea (ID: `ats-resume`) → *Issues: Hardcoded placeholder: "Paste your full resume text here...

Example:
SAM SALAMEH
Senior Network Engineer | CCNA, Fortinet NSE, MikroTik MTCNA
samsalameh.cv@gmail.com | +961 70 841 1009
linkedin.com/in/sam-salameh

PROFESSIONAL SUMMARY
15+ years as a Network Engineer specializing in...
..."*
- **Line 55**: Textarea (ID: `ats-job-desc`) → *Issues: Hardcoded placeholder: "Paste the job description here...

Example:
Network Engineer
Company XYZ — Beirut, Lebanon

Requirements:
- 5+ years experience with Cisco/Juniper
- CCNP or equivalent certification
- Strong knowledge of BGP, OSPF, MPLS
- Experience with Fortinet firewalls
..."*

#### Button Elements:
- **Line 50**: Button (ID: `btn-url-import`, Class: `px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 border border-slate-700 whitespace-nowrap`) → *Issues: Missing proper hover/focus classes (class: "px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 border border-slate-700 whitespace-nowrap")*
- **Line 77**: Button (ID: `btn-score`, Class: `px-8 py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-base font-black tracking-wide shadow-[0_0_20px_rgba(79,70,229,0.3)] transition-all flex items-center gap-3 border border-indigo-400/30`) → *Issues: Missing proper hover/focus classes (class: "px-8 py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-base font-black tracking-wide shadow-[0_0_20px_rgba(79,70,229,0.3)] transition-all flex items-center gap-3 border border-indigo-400/30")*
- **Line 80**: Button (ID: `btn-bulk-toggle`, Class: `px-5 py-3.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-sm font-bold transition-all flex items-center gap-2 border border-slate-700`) → *Issues: Missing proper hover/focus classes (class: "px-5 py-3.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-sm font-bold transition-all flex items-center gap-2 border border-slate-700")*
- **Line 97**: Button (ID: `btn-bulk-score`, Class: `px-5 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-sm font-bold tracking-wide shadow-[0_0_15px_rgba(147,51,234,0.3)] transition-all flex items-center gap-2 border border-purple-400/50`) → *Issues: Missing proper hover/focus classes (class: "px-5 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-sm font-bold tracking-wide shadow-[0_0_15px_rgba(147,51,234,0.3)] transition-all flex items-center gap-2 border border-purple-400/50")*
- **Line 106**: Button (ID: `None`, Class: `mt-4 px-4 py-2 border border-dashed border-slate-600 text-slate-400 hover:text-white hover:border-slate-400 hover:bg-slate-800/50 rounded-lg text-sm font-medium transition-all flex items-center gap-2 w-full justify-center`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "mt-4 px-4 py-2 border border-dashed border-slate-600 text-slate-400 hover:text-white hover:border-slate-400 hover:bg-slate-800/50 rounded-lg text-sm font-medium transition-all flex items-center gap-2 w-full justify-center")*

---

### File: `templates/en/battle_station.html`

#### Button Elements:
- **Line 251**: Button (ID: `None`, Class: `bs-btn green`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "bs-btn green")*
- **Line 252**: Button (ID: `None`, Class: `bs-btn red`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "bs-btn red")*
- **Line 253**: Button (ID: `None`, Class: `bs-btn green`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "bs-btn green")*

---

### File: `templates/en/candidate_profile.html`

#### Button Elements:
- **Line 27**: Button (ID: `None`, Class: `btn-primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-primary")*

---

### File: `templates/en/checkout_v2.html`

#### Input Elements:
- **Line 380**: Input (ID: `paymentCode`, Type: `text`) → *Issues: Hardcoded placeholder: "Payment Code (e.g. A1B2C3D4)"*
- **Line 381**: Input (ID: `txHash`, Type: `text`) → *Issues: Hardcoded placeholder: "Transaction hash / TX ID"*

#### Button Elements:
- **Line 335**: Button (ID: `None`, Class: `btn-nowpayments`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-nowpayments")*
- **Line 355**: Button (ID: `None`, Class: `crypto-tab {% if loop.first %}active{% endif %}`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "crypto-tab {% if loop.first %}active{% endif %}")*
- **Line 382**: Button (ID: `verifyBtn`, Class: `btn-verify`) → *Issues: Missing proper hover/focus classes (class: "btn-verify")*

---

### File: `templates/en/checkout_v3.html`

#### Input Elements:
- **Line 594**: Input (ID: `paymentCodeV3`, Type: `text`) → *Issues: Hardcoded placeholder: "Payment Code (e.g. A1B2C3D4)"*
- **Line 595**: Input (ID: `txHashV3`, Type: `text`) → *Issues: Hardcoded placeholder: "Transaction hash / TX ID"*

#### Button Elements:
- **Line 544**: Button (ID: `None`, Class: `btn-nowpayments-v3`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-nowpayments-v3")*
- **Line 564**: Button (ID: `None`, Class: `crypto-tab-v3 {% if loop.first %}active{% endif %}`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "crypto-tab-v3 {% if loop.first %}active{% endif %}")*
- **Line 596**: Button (ID: `verifyBtnV3`, Class: `btn-verify-v3`) → *Issues: Missing proper hover/focus classes (class: "btn-verify-v3")*

---

### File: `templates/en/contact.html`

#### Form Elements:
- **Line 96**: Form (Action: `/contact`) → *Issues: Missing ID*

#### Input Elements:
- **Line 100**: Input (ID: `name`, Type: `text`) → *Issues: Hardcoded placeholder: "John Doe"*
- **Line 104**: Input (ID: `email`, Type: `email`) → *Issues: Hardcoded placeholder: "you@example.com"*

#### Textarea Elements:
- **Line 122**: Textarea (ID: `message`) → *Issues: Hardcoded placeholder: "Tell us what's on your mind... Be as detailed as you like — we read every word."*

#### Button Elements:
- **Line 124**: Button (ID: `None`, Class: `btn-submit`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-submit")*

---

### File: `templates/en/dashboard_v3.html`

#### Form Elements:
- **Line 240**: Form (Action: `None`) → *Issues: Missing ID*

#### Input Elements:
- **Line 442**: Input (ID: `smtpEmail`, Type: `email`) → *Issues: Hardcoded placeholder: "you@domain.com"*
- **Line 446**: Input (ID: `smtpPass`, Type: `password`) → *Issues: Hardcoded placeholder: "16-digit App Password"*

#### Button Elements:
- **Line 33**: Button (ID: `None`, Class: `flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-slate-300 transition-colors hover:bg-white/10 hover:text-white`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-slate-300 transition-colors hover:bg-white/10 hover:text-white")*
- **Line 107**: Button (ID: `None`, Class: `rounded-md px-3 py-1.5 text-xs font-medium transition-colors bg-indigo-500/20 text-indigo-300`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "rounded-md px-3 py-1.5 text-xs font-medium transition-colors bg-indigo-500/20 text-indigo-300")*
- **Line 108**: Button (ID: `None`, Class: `rounded-md px-3 py-1.5 text-xs font-medium text-slate-400 transition-colors hover:text-white`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "rounded-md px-3 py-1.5 text-xs font-medium text-slate-400 transition-colors hover:text-white")*
- **Line 109**: Button (ID: `None`, Class: `rounded-md px-3 py-1.5 text-xs font-medium text-slate-400 transition-colors hover:text-white`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "rounded-md px-3 py-1.5 text-xs font-medium text-slate-400 transition-colors hover:text-white")*
- **Line 241**: Button (ID: `None`, Class: `rounded-lg p-1 text-slate-400 hover:bg-white/10 hover:text-white`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "rounded-lg p-1 text-slate-400 hover:bg-white/10 hover:text-white")*
- **Line 428**: Button (ID: `None`, Class: `text-slate-400 hover:text-white`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "text-slate-400 hover:text-white")*
- **Line 449**: Button (ID: `smtpConnectBtn`, Class: `w-full rounded-lg bg-indigo-600 py-3 font-bold text-white transition-all hover:bg-indigo-500 mt-4 flex justify-center items-center gap-2`) → *Issues: Missing proper hover/focus classes (class: "w-full rounded-lg bg-indigo-600 py-3 font-bold text-white transition-all hover:bg-indigo-500 mt-4 flex justify-center items-center gap-2")*

---

### File: `templates/en/email_test.html`

#### Input Elements:
- **Line 109**: Input (ID: `fldTo`, Type: `email`) → *Issues: Hardcoded placeholder: "hr@company.com"*
- **Line 113**: Input (ID: `fldCompany`, Type: `text`) → *Issues: Hardcoded placeholder: "Target Company"*
- **Line 117**: Input (ID: `fldJob`, Type: `text`) → *Issues: Hardcoded placeholder: "Network Engineer"*

#### Textarea Elements:
- **Line 132**: Textarea (ID: `fldCV`) → *Issues: Hardcoded placeholder: "Your CV text will appear here after uploading PDF..."*
- **Line 146**: Textarea (ID: `fldCover`) → *Issues: Hardcoded placeholder: "Cover letter will be auto-generated..."*
- **Line 157**: Textarea (ID: `fldEmail`) → *Issues: Hardcoded placeholder: "Email body will be auto-generated..."*

#### Button Elements:
- **Line 127**: Button (ID: `None`, Class: `btn btn-xs btn-ai`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-xs btn-ai")*
- **Line 128**: Button (ID: `None`, Class: `btn btn-xs btn-pdf`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-xs btn-pdf")*
- **Line 141**: Button (ID: `None`, Class: `btn btn-xs btn-ai`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-xs btn-ai")*
- **Line 142**: Button (ID: `None`, Class: `btn btn-xs btn-pdf`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-xs btn-pdf")*
- **Line 154**: Button (ID: `None`, Class: `btn btn-xs btn-ai`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-xs btn-ai")*
- **Line 163**: Button (ID: `None`, Class: `btn btn-lg btn-primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-lg btn-primary")*
- **Line 164**: Button (ID: `None`, Class: `btn btn-md btn-outline`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-md btn-outline")*

---

### File: `templates/en/employer_track.html`

#### Input Elements:
- **Line 90**: Input (ID: `trackEmail`, Type: `email`) → *Issues: Hardcoded placeholder: "hr@yourcompany.com"*
- **Line 94**: Input (ID: `trackJobId`, Type: `text`) → *Issues: Hardcoded placeholder: "job_xxxxxxxxxxxx"*

#### Button Elements:
- **Line 96**: Button (ID: `None`, Class: `track-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "track-btn")*

---

### File: `templates/en/export.html`

#### Input Elements:
- **Line 82**: Input (ID: `None`, Type: `radio`) → *Issues: Missing ID*
- **Line 89**: Input (ID: `None`, Type: `radio`) → *Issues: Missing ID*

#### Button Elements:
- **Line 34**: Button (ID: `None`, Class: `pill`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "pill")*
- **Line 35**: Button (ID: `None`, Class: `pill`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "pill")*
- **Line 36**: Button (ID: `None`, Class: `pill active`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "pill active")*
- **Line 37**: Button (ID: `None`, Class: `pill`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "pill")*
- **Line 38**: Button (ID: `None`, Class: `pill`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "pill")*
- **Line 98**: Button (ID: `None`, Class: `btn btn-export`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-export")*

---

### File: `templates/en/for_employers.html`

#### Input Elements:
- **Line 364**: Input (ID: `company_name`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. Murex, Bank Audi..."*
- **Line 368**: Input (ID: `job_title`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. Senior Network Engineer"*
- **Line 372**: Input (ID: `location`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. Beirut, Lebanon"*
- **Line 390**: Input (ID: `salary`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. $2,500 - $3,500/month"*
- **Line 394**: Input (ID: `contact_email`, Type: `email`) → *Issues: Hardcoded placeholder: "hr@yourcompany.com"*
- **Line 403**: Input (ID: `apply_url`, Type: `url`) → *Issues: Hardcoded placeholder: "https://yourcompany.com/careers/..."*
- **Line 407**: Input (ID: `logo_url`, Type: `url`) → *Issues: Hardcoded placeholder: "https://yourcompany.com/logo.png"*

#### Textarea Elements:
- **Line 399**: Textarea (ID: `description`) → *Issues: Hardcoded placeholder: "Describe the role, responsibilities, requirements, and why your company is a great place to work...

💡 Tip: Include benefits, culture, and growth opportunities for 2x more applicants!"*

#### Button Elements:
- **Line 211**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*
- **Line 227**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*
- **Line 243**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*
- **Line 260**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*
- **Line 268**: Button (ID: `None`, Class: `duration-btn selected`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "duration-btn selected")*
- **Line 271**: Button (ID: `None`, Class: `duration-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "duration-btn")*
- **Line 274**: Button (ID: `None`, Class: `duration-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "duration-btn")*
- **Line 277**: Button (ID: `None`, Class: `duration-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "duration-btn")*
- **Line 280**: Button (ID: `None`, Class: `duration-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "duration-btn")*
- **Line 434**: Button (ID: `submitBtn`, Class: `submit-btn`) → *Issues: Missing proper hover/focus classes (class: "submit-btn")*

---

### File: `templates/en/forgot_password.html`

#### Input Elements:
- **Line 310**: Input (ID: `email`, Type: `email`) → *Issues: Hardcoded placeholder: "you@example.com"*

#### Button Elements:
- **Line 315**: Button (ID: `forgotBtn`, Class: `btn-submit`) → *Issues: Missing proper hover/focus classes (class: "btn-submit")*

---

### File: `templates/en/funnel_analytics.html`

#### Button Elements:
- **Line 285**: Button (ID: `None`, Class: `funnel-filter-btn active`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "funnel-filter-btn active")*
- **Line 286**: Button (ID: `None`, Class: `funnel-filter-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "funnel-filter-btn")*
- **Line 287**: Button (ID: `None`, Class: `funnel-filter-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "funnel-filter-btn")*
- **Line 288**: Button (ID: `None`, Class: `funnel-filter-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "funnel-filter-btn")*

---

### File: `templates/en/growth_station.html`

#### Input Elements:
- **Line 203**: Input (ID: `keyword`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. React Developer or ATS"*
- **Line 208**: Input (ID: `location`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. Lebanon or Dubai"*
- **Line 304**: Input (ID: `search-input`, Type: `text`) → *Issues: Hardcoded placeholder: "Search name/email..."*
- **Line 355**: Input (ID: `campaign-name`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. React Developers Beirut"*

#### Button Elements:
- **Line 221**: Button (ID: `None`, Class: `btn-premium w-full flex items-center justify-center gap-2 mt-4`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-premium w-full flex items-center justify-center gap-2 mt-4")*
- **Line 306**: Button (ID: `None`, Class: `btn-premium flex items-center gap-1.5 text-sm`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-premium flex items-center gap-1.5 text-sm")*
- **Line 339**: Button (ID: `prev-btn`, Class: `btn-secondary-premium px-3 py-1.5 text-xs`) → *Issues: Missing proper hover/focus classes (class: "btn-secondary-premium px-3 py-1.5 text-xs")*
- **Line 340**: Button (ID: `next-btn`, Class: `btn-secondary-premium px-3 py-1.5 text-xs`) → *Issues: Missing proper hover/focus classes (class: "btn-secondary-premium px-3 py-1.5 text-xs")*
- **Line 360**: Button (ID: `None`, Class: `btn-secondary-premium`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-secondary-premium")*
- **Line 361**: Button (ID: `None`, Class: `btn-premium`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-premium")*
- **Line 372**: Button (ID: `None`, Class: `btn-premium`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-premium")*

---

### File: `templates/en/index_v2.html`

#### Button Elements:
- **Line 661**: Button (ID: `None`, Class: `mobile-menu-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "mobile-menu-btn")*
- **Line 914**: Button (ID: `None`, Class: `active`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "active")*
- **Line 915**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*
- **Line 916**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*
- **Line 917**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*

---

### File: `templates/en/index_v3.html`

#### Button Elements:
- **Line 1203**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*
- **Line 1667**: Button (ID: `None`, Class: `calc-tab active`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "calc-tab active")*
- **Line 1668**: Button (ID: `None`, Class: `calc-tab`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "calc-tab")*
- **Line 1669**: Button (ID: `None`, Class: `calc-tab`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "calc-tab")*
- **Line 2380**: Button (ID: `None`, Class: `exit-close`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "exit-close")*

---

### File: `templates/en/index_v4.html`

#### Input Elements:
- **Line 346**: Input (ID: `atsJobTitle`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. Software Engineer"*
- **Line 350**: Input (ID: `atsSkills`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. Python, React, AWS"*

#### Button Elements:
- **Line 96**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*
- **Line 352**: Button (ID: `None`, Class: `primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "primary")*
- **Line 481**: Button (ID: `None`, Class: `primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "primary")*
- **Line 741**: Button (ID: `None`, Class: `faq-question`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "faq-question")*
- **Line 750**: Button (ID: `None`, Class: `faq-question`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "faq-question")*
- **Line 759**: Button (ID: `None`, Class: `faq-question`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "faq-question")*
- **Line 768**: Button (ID: `None`, Class: `faq-question`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "faq-question")*
- **Line 777**: Button (ID: `None`, Class: `faq-question`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "faq-question")*
- **Line 786**: Button (ID: `None`, Class: `faq-question`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "faq-question")*
- **Line 795**: Button (ID: `None`, Class: `faq-question`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "faq-question")*
- **Line 804**: Button (ID: `None`, Class: `faq-question`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "faq-question")*

---

### File: `templates/en/login.html`

#### Form Elements:
- **Line 146**: Form (Action: `/login`) → *Issues: Missing ID*

#### Input Elements:
- **Line 149**: Input (ID: `email`, Type: `email`) → *Issues: Hardcoded placeholder: "you@example.com"*
- **Line 153**: Input (ID: `password`, Type: `password`) → *Issues: Hardcoded placeholder: "●●●●●●●●"*

#### Button Elements:
- **Line 158**: Button (ID: `loginBtn`, Class: `btn-submit`) → *Issues: Missing proper hover/focus classes (class: "btn-submit")*

---

### File: `templates/en/login_v2.html`

#### Input Elements:
- **Line 123**: Input (ID: `email`, Type: `email`) → *Issues: Hardcoded placeholder: "you@example.com"*
- **Line 128**: Input (ID: `password`, Type: `password`) → *Issues: Hardcoded placeholder: "●●●●●●●●"*
- **Line 139**: Input (ID: `None`, Type: `checkbox`) → *Issues: Missing ID*

#### Button Elements:
- **Line 129**: Button (ID: `pwToggle`, Class: `pw-toggle-btn`) → *Issues: Missing proper hover/focus classes (class: "pw-toggle-btn")*
- **Line 143**: Button (ID: `loginBtn`, Class: `btn-submit`) → *Issues: Missing proper hover/focus classes (class: "btn-submit")*

---

### File: `templates/en/my_purchases.html`

#### Button Elements:
- **Line 118**: Button (ID: `None`, Class: `btn-copy`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-copy")*

---

### File: `templates/en/new_campaign_v2.html`

#### Input Elements:
- **Line 98**: Input (ID: `None`, Type: `radio`) → *Issues: Missing ID*
- **Line 146**: Input (ID: `None`, Type: `checkbox`) → *Issues: Missing ID*

#### Button Elements:
- **Line 56**: Button (ID: `None`, Class: `px-5 py-3.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded-xl transition-all flex items-center justify-center gap-2`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "px-5 py-3.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded-xl transition-all flex items-center justify-center gap-2")*
- **Line 167**: Button (ID: `None`, Class: `text-xs font-bold text-red-400 hover:text-red-300 transition-colors uppercase tracking-wider flex items-center gap-1`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "text-xs font-bold text-red-400 hover:text-red-300 transition-colors uppercase tracking-wider flex items-center gap-1")*
- **Line 199**: Button (ID: `submitBtn`, Class: `w-full md:w-auto px-10 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-lg font-black tracking-wide shadow-[0_0_20px_rgba(79,70,229,0.3)] hover:shadow-[0_0_30px_rgba(79,70,229,0.5)] transition-all flex items-center justify-center gap-3 border border-indigo-400/30 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none`) → *Issues: Missing proper hover/focus classes (class: "w-full md:w-auto px-10 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-lg font-black tracking-wide shadow-[0_0_20px_rgba(79,70,229,0.3)] hover:shadow-[0_0_30px_rgba(79,70,229,0.5)] transition-all flex items-center justify-center gap-3 border border-indigo-400/30 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none")*

---

### File: `templates/en/offers.html`

#### Form Elements:
- **Line 192**: Form (Action: `/api/v2/offers/import-keys`) → *Issues: Missing ID*
- **Line 301**: Form (Action: `/api/v2/offers/delete/{{ offer.offer_id }}`) → *Issues: Missing ID*
- **Line 402**: Form (Action: `/api/v2/offers/delete-key/{{ k.key_id }}`) → *Issues: Missing ID*

#### Input Elements:
- **Line 136**: Input (ID: `offerTitle`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. Executive CV Makeover + 100 Companies"*
- **Line 140**: Input (ID: `offerPrice`, Type: `number`) → *Issues: Hardcoded placeholder: "e.g. 19.99"*
- **Line 144**: Input (ID: `offerOriginalPrice`, Type: `number`) → *Issues: Hardcoded placeholder: "e.g. 49.99"*
- **Line 152**: Input (ID: `offerImage`, Type: `text`) → *Issues: Hardcoded placeholder: "Paste image link URL or upload below..."*
- **Line 170**: Input (ID: `offerApiUrl`, Type: `url`) → *Issues: Hardcoded placeholder: "https://api.provider.com/v1/generate"*
- **Line 174**: Input (ID: `offerApiKey`, Type: `text`) → *Issues: Hardcoded placeholder: "API Secret Key Token"*
- **Line 456**: Input (ID: `editOfferTitle`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. Executive CV Makeover + 100 Companies"*
- **Line 460**: Input (ID: `editOfferPrice`, Type: `number`) → *Issues: Hardcoded placeholder: "e.g. 19.99"*
- **Line 464**: Input (ID: `editOfferOriginalPrice`, Type: `number`) → *Issues: Hardcoded placeholder: "e.g. 49.99"*
- **Line 472**: Input (ID: `editOfferImage`, Type: `text`) → *Issues: Hardcoded placeholder: "Paste image link URL or upload below..."*
- **Line 490**: Input (ID: `editOfferApiUrl`, Type: `url`) → *Issues: Hardcoded placeholder: "https://api.provider.com/v1/generate"*
- **Line 494**: Input (ID: `editOfferApiKey`, Type: `text`) → *Issues: Hardcoded placeholder: "API Secret Key Token"*

#### Textarea Elements:
- **Line 148**: Textarea (ID: `offerDesc`) → *Issues: Hardcoded placeholder: "Explain what is included in this offer in detail..."*
- **Line 179**: Textarea (ID: `offerNote`) → *Issues: Hardcoded placeholder: "e.g. Note: Delivery takes 48 hours and requires your current CV."*
- **Line 205**: Textarea (ID: `importKeysText`) → *Issues: Hardcoded placeholder: "Paste your keys, account credentials, or links here.
One item per line.
e.g. USER:PASS-IPTV-123
e.g. https://vpn.com/claim?code=abc"*
- **Line 433**: Textarea (ID: `modalReqs`) → *Issues: Hardcoded placeholder: "Specify your preferences, target industries, links, email text guidelines, or details of what you need..."*
- **Line 468**: Textarea (ID: `editOfferDesc`) → *Issues: Hardcoded placeholder: "Explain what is included in this offer in detail..."*
- **Line 499**: Textarea (ID: `editOfferNote`) → *Issues: Hardcoded placeholder: "e.g. Note: Delivery takes 48 hours."*
- **Line 804**: Textarea (ID: `fulfillCredentials`) → *Issues: Hardcoded placeholder: "Paste IPTV logins, premium license key, account details, or instructions here..."*

#### Button Elements:
- **Line 155**: Button (ID: `None`, Class: `btn-cyber secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber secondary")*
- **Line 182**: Button (ID: `None`, Class: `btn-cyber primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber primary")*
- **Line 208**: Button (ID: `None`, Class: `btn-cyber primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber primary")*
- **Line 283**: Button (ID: `None`, Class: `btn-cyber primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber primary")*
- **Line 290**: Button (ID: `None`, Class: `btn-cyber secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber secondary")*
- **Line 302**: Button (ID: `None`, Class: `btn-cyber secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber secondary")*
- **Line 356**: Button (ID: `None`, Class: `btn-cyber secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber secondary")*
- **Line 403**: Button (ID: `None`, Class: `None`) → *Issues: Missing ID; No classes defined (missing hover/focus states)*
- **Line 437**: Button (ID: `None`, Class: `btn-cyber secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber secondary")*
- **Line 438**: Button (ID: `None`, Class: `btn-cyber primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber primary")*
- **Line 475**: Button (ID: `None`, Class: `btn-cyber secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber secondary")*
- **Line 505**: Button (ID: `None`, Class: `btn-cyber secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber secondary")*
- **Line 507**: Button (ID: `None`, Class: `btn-cyber secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber secondary")*
- **Line 508**: Button (ID: `None`, Class: `btn-cyber primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber primary")*
- **Line 808**: Button (ID: `None`, Class: `btn-cyber secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber secondary")*
- **Line 809**: Button (ID: `None`, Class: `btn-cyber primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber primary")*

---

### File: `templates/en/pricing_v2.html`

#### Button Elements:
- **Line 679**: Button (ID: `None`, Class: `toast-close`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "toast-close")*

---

### File: `templates/en/pricing_v3.html`

#### Button Elements:
- **Line 682**: Button (ID: `None`, Class: `toast-close-v3`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "toast-close-v3")*

---

### File: `templates/en/register.html`

#### Form Elements:
- **Line 174**: Form (Action: `/register`) → *Issues: Missing ID*

#### Input Elements:
- **Line 182**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 185**: Input (ID: `None`, Type: `text`) → *Issues: Missing ID; Hardcoded placeholder: "e.g. Sam Salameh"*
- **Line 189**: Input (ID: `None`, Type: `email`) → *Issues: Missing ID; Hardcoded placeholder: "you@example.com"*
- **Line 193**: Input (ID: `None`, Type: `tel`) → *Issues: Missing ID; Hardcoded placeholder: "e.g. +961 70 000 000"*
- **Line 197**: Input (ID: `None`, Type: `password`) → *Issues: Missing ID; Hardcoded placeholder: "Min. 8 characters"*

#### Button Elements:
- **Line 204**: Button (ID: `None`, Class: `btn-submit`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-submit")*

---

### File: `templates/en/register_v2.html`

#### Input Elements:
- **Line 190**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 194**: Input (ID: `regName`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. Sam Salameh"*
- **Line 200**: Input (ID: `regEmail`, Type: `email`) → *Issues: Hardcoded placeholder: "you@example.com"*
- **Line 206**: Input (ID: `regPhone`, Type: `tel`) → *Issues: Hardcoded placeholder: "e.g. +961 70 000 000"*
- **Line 212**: Input (ID: `regPassword`, Type: `password`) → *Issues: Hardcoded placeholder: "Min. 8 characters"*

#### Button Elements:
- **Line 213**: Button (ID: `regPwToggle`, Class: `pw-toggle-btn`) → *Issues: Missing proper hover/focus classes (class: "pw-toggle-btn")*
- **Line 236**: Button (ID: `registerBtn`, Class: `btn-solid`) → *Issues: Missing proper hover/focus classes (class: "btn-solid")*

---

### File: `templates/en/reset_password.html`

#### Input Elements:
- **Line 234**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 239**: Input (ID: `password`, Type: `password`) → *Issues: Hardcoded placeholder: "Min. 8 characters"*
- **Line 266**: Input (ID: `confirmPassword`, Type: `password`) → *Issues: Hardcoded placeholder: "Repeat new password"*

#### Button Elements:
- **Line 246**: Button (ID: `pwToggle`, Class: `pw-toggle-btn`) → *Issues: Missing proper hover/focus classes (class: "pw-toggle-btn")*
- **Line 270**: Button (ID: `confirmToggle`, Class: `pw-toggle-btn`) → *Issues: Missing proper hover/focus classes (class: "pw-toggle-btn")*
- **Line 275**: Button (ID: `resetBtn`, Class: `btn-submit`) → *Issues: Missing proper hover/focus classes (class: "btn-submit")*

---

### File: `templates/en/resume_tailor.html`

#### Input Elements:
- **Line 346**: Input (ID: `tailor-job-title`, Type: `text`) → *Issues: Hardcoded placeholder: "Job title (optional, helps AI context)"*

#### Textarea Elements:
- **Line 323**: Textarea (ID: `tailor-resume`) → *Issues: Hardcoded placeholder: "Paste your full resume / CV text here...

SAM SALAMEH
Senior Network Engineer | CCNA, Fortinet NSE, MikroTik MTCNA
samsalameh.cv@gmail.com | +961 70 841 1009

PROFESSIONAL SUMMARY
15+ years as a Network Engineer specializing in enterprise network design..."*
- **Line 336**: Textarea (ID: `tailor-job`) → *Issues: Hardcoded placeholder: "Paste the job description you want to tailor for...

Network Engineer — Beirut, Lebanon

Requirements:
• 5+ years Cisco/Juniper experience
• CCNP or equivalent
• Strong BGP, OSPF, MPLS knowledge
• Fortinet firewall experience
..."*

#### Button Elements:
- **Line 361**: Button (ID: `btn-tailor`, Class: `btn btn-ai`) → *Issues: Missing proper hover/focus classes (class: "btn btn-ai")*
- **Line 391**: Button (ID: `toggle-tailored`, Class: `diff-toggle-btn active`) → *Issues: Missing proper hover/focus classes (class: "diff-toggle-btn active")*
- **Line 392**: Button (ID: `toggle-diff`, Class: `diff-toggle-btn`) → *Issues: Missing proper hover/focus classes (class: "diff-toggle-btn")*
- **Line 412**: Button (ID: `None`, Class: `btn btn-outline btn-sm`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-outline btn-sm")*
- **Line 413**: Button (ID: `None`, Class: `btn btn-primary btn-sm`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-primary btn-sm")*

---

### File: `templates/en/roast.html`

#### Button Elements:
- **Line 17**: Button (ID: `roastBtn`, Class: `btn-primary`) → *Issues: Missing proper hover/focus classes (class: "btn-primary")*

---

### File: `templates/en/sent_emails.html`

#### Input Elements:
- **Line 38**: Input (ID: `searchInput`, Type: `text`) → *Issues: Hardcoded placeholder: "Search by company, title, or email..."*

#### Button Elements:
- **Line 46**: Button (ID: `None`, Class: `px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-semibold transition-all border border-slate-700 flex items-center gap-2 whitespace-nowrap`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-semibold transition-all border border-slate-700 flex items-center gap-2 whitespace-nowrap")*
- **Line 95**: Button (ID: `loadMoreBtn`, Class: `px-6 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-xl text-sm font-semibold transition-all inline-flex items-center gap-2`) → *Issues: Missing proper hover/focus classes (class: "px-6 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-xl text-sm font-semibold transition-all inline-flex items-center gap-2")*

---

### File: `templates/en/services.html`

#### Form Elements:
- **Line 436**: Form (Action: `/services/purchase`) → *Issues: Missing ID*
- **Line 468**: Form (Action: `/services/purchase`) → *Issues: Missing ID*
- **Line 502**: Form (Action: `/services/purchase`) → *Issues: Missing ID*

#### Input Elements:
- **Line 424**: Input (ID: `None`, Type: `checkbox`) → *Issues: Missing ID*
- **Line 437**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 438**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 457**: Input (ID: `None`, Type: `checkbox`) → *Issues: Missing ID*
- **Line 469**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 470**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 490**: Input (ID: `None`, Type: `checkbox`) → *Issues: Missing ID*
- **Line 503**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 504**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*

#### Button Elements:
- **Line 346**: Button (ID: `None`, Class: `hamburger`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "hamburger")*
- **Line 440**: Button (ID: `None`, Class: `btn btn-secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-secondary")*
- **Line 442**: Button (ID: `None`, Class: `btn btn-primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-primary")*
- **Line 472**: Button (ID: `None`, Class: `btn btn-secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-secondary")*
- **Line 474**: Button (ID: `None`, Class: `btn btn-primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-primary")*
- **Line 506**: Button (ID: `None`, Class: `btn btn-secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-secondary")*
- **Line 508**: Button (ID: `None`, Class: `btn btn-magenta`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-magenta")*
- **Line 522**: Button (ID: `bulkBtn`, Class: `btn-bulk-buy`) → *Issues: Missing proper hover/focus classes (class: "btn-bulk-buy")*

---

### File: `templates/en/services_new.html`

#### Button Elements:
- **Line 148**: Button (ID: `None`, Class: `cat-tab active`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "cat-tab active")*
- **Line 149**: Button (ID: `None`, Class: `cat-tab`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "cat-tab")*
- **Line 150**: Button (ID: `None`, Class: `cat-tab`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "cat-tab")*
- **Line 151**: Button (ID: `None`, Class: `cat-tab`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "cat-tab")*
- **Line 152**: Button (ID: `None`, Class: `cat-tab`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "cat-tab")*
- **Line 153**: Button (ID: `None`, Class: `cat-tab`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "cat-tab")*
- **Line 197**: Button (ID: `cartFab`, Class: `cart-badge-btn`) → *Issues: Missing proper hover/focus classes (class: "cart-badge-btn")*
- **Line 207**: Button (ID: `None`, Class: `cart-close`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "cart-close")*
- **Line 220**: Button (ID: `checkoutBtn`, Class: `cart-checkout`) → *Issues: Missing proper hover/focus classes (class: "cart-checkout")*
- **Line 233**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*

---

### File: `templates/en/services_v2.html`

#### Input Elements:
- **Line 1001**: Input (ID: `customerName`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. John Doe"*
- **Line 1004**: Input (ID: `customerEmail`, Type: `email`) → *Issues: Hardcoded placeholder: "e.g. john@example.com"*

#### Button Elements:
- **Line 814**: Button (ID: `None`, Class: `btn-buy btn-buy-micro`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-buy btn-buy-micro")*
- **Line 844**: Button (ID: `None`, Class: `btn-buy btn-buy-standard`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-buy btn-buy-standard")*
- **Line 874**: Button (ID: `None`, Class: `btn-buy btn-buy-premium`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-buy btn-buy-premium")*
- **Line 905**: Button (ID: `None`, Class: `btn-bouquet`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-bouquet")*
- **Line 961**: Button (ID: `cartToggle`, Class: `cart-toggle`) → *Issues: Missing proper hover/focus classes (class: "cart-toggle")*
- **Line 973**: Button (ID: `None`, Class: `cart-close`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "cart-close")*
- **Line 983**: Button (ID: `None`, Class: `cart-checkout`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "cart-checkout")*
- **Line 991**: Button (ID: `None`, Class: `modal-close`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "modal-close")*
- **Line 1008**: Button (ID: `submitBtn`, Class: `btn-submit`) → *Issues: Missing proper hover/focus classes (class: "btn-submit")*

---

### File: `templates/en/track_application.html`

#### Form Elements:
- **Line 156**: Form (Action: `/track-application`) → *Issues: Missing ID*

#### Input Elements:
- **Line 159**: Input (ID: `None`, Type: `email`) → *Issues: Missing ID; Hardcoded placeholder: "you@email.com"*

#### Button Elements:
- **Line 161**: Button (ID: `None`, Class: `btn btn-search`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-search")*

---

### File: `templates/en/upload_cv_v2.html`

#### Input Elements:
- **Line 575**: Input (ID: `fullName`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. Sam Salameh"*
- **Line 576**: Input (ID: `email`, Type: `email`) → *Issues: Hardcoded placeholder: "your@email.com"*
- **Line 579**: Input (ID: `phone`, Type: `text`) → *Issues: Hardcoded placeholder: "+961 3 123 456"*
- **Line 580**: Input (ID: `location`, Type: `text`) → *Issues: Hardcoded placeholder: "Beirut, Lebanon"*
- **Line 583**: Input (ID: `currentTitle`, Type: `text`) → *Issues: Hardcoded placeholder: "Senior Network Engineer"*
- **Line 587**: Input (ID: `education`, Type: `text`) → *Issues: Hardcoded placeholder: "Bachelor of Engineering"*
- **Line 588**: Input (ID: `linkedin`, Type: `url`) → *Issues: Hardcoded placeholder: "https://linkedin.com/in/..."*
- **Line 591**: Input (ID: `certsInput`, Type: `text`) → *Issues: Hardcoded placeholder: "CCNA, NSE, MTCNA..."*
- **Line 592**: Input (ID: `langsInput`, Type: `text`) → *Issues: Hardcoded placeholder: "English, Arabic, French..."*
- **Line 600**: Input (ID: `targetCompany`, Type: `text`) → *Issues: Hardcoded placeholder: "Murex, Cisco, Bank Audi..."*
- **Line 601**: Input (ID: `targetJobTitle`, Type: `text`) → *Issues: Hardcoded placeholder: "Senior Network Engineer"*
- **Line 616**: Input (ID: `targetTitles`, Type: `text`) → *Issues: Hardcoded placeholder: "Senior Network Engineer, IT Manager..."*

#### Textarea Elements:
- **Line 550**: Textarea (ID: `cvText`) → *Issues: Hardcoded placeholder: "Paste your entire CV / resume text here...

Include: Full Name, Contact Info, Work Experience, Education, Skills, Certifications, Languages...

Then click ✨ Auto-Fill to let AI extract everything automatically."*
- **Line 593**: Textarea (ID: `summary`) → *Issues: Hardcoded placeholder: "Brief professional summary..."*

#### Button Elements:
- **Line 556**: Button (ID: `parseBtn`, Class: `btn btn-ai pulse-btn`) → *Issues: Missing proper hover/focus classes (class: "btn btn-ai pulse-btn")*
- **Line 710**: Button (ID: `None`, Class: `btn btn-ai`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-ai")*
- **Line 711**: Button (ID: `None`, Class: `btn btn-sm btn-outline`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-sm btn-outline")*
- **Line 729**: Button (ID: `None`, Class: `btn pulse-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn pulse-btn")*
- **Line 732**: Button (ID: `None`, Class: `btn btn-outline`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-outline")*
- **Line 735**: Button (ID: `None`, Class: `btn btn-sm btn-outline`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-sm btn-outline")*
- **Line 748**: Button (ID: `None`, Class: `modal-close`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "modal-close")*
- **Line 751**: Button (ID: `None`, Class: `preview-tab active`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "preview-tab active")*
- **Line 752**: Button (ID: `None`, Class: `preview-tab`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "preview-tab")*
- **Line 753**: Button (ID: `None`, Class: `preview-tab`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "preview-tab")*
- **Line 759**: Button (ID: `None`, Class: `btn btn-outline btn-sm`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-outline btn-sm")*
- **Line 760**: Button (ID: `None`, Class: `btn btn-ai btn-sm`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-ai btn-sm")*

---

### File: `templates/en/upload_cv_v3.html`

#### Input Elements:
- **Line 114**: Input (ID: `None`, Type: `text`) → *Issues: Missing ID; Hardcoded placeholder: "e.g. Sam Salameh"*
- **Line 118**: Input (ID: `None`, Type: `email`) → *Issues: Missing ID; Hardcoded placeholder: "you@example.com"*
- **Line 124**: Input (ID: `None`, Type: `tel`) → *Issues: Missing ID; Hardcoded placeholder: "+961 70 000 000"*
- **Line 128**: Input (ID: `None`, Type: `text`) → *Issues: Missing ID; Hardcoded placeholder: "e.g. Beirut, Lebanon"*
- **Line 133**: Input (ID: `None`, Type: `url`) → *Issues: Missing ID; Hardcoded placeholder: "https://linkedin.com/in/yourprofile"*
- **Line 144**: Input (ID: `skillsInput`, Type: `text`) → *Issues: Hardcoded placeholder: "Python, JavaScript, Project Management, ..."*
- **Line 180**: Input (ID: `None`, Type: `text`) → *Issues: Missing ID; Hardcoded placeholder: "e.g. $60,000 - $90,000"*

#### Button Elements:
- **Line 15**: Button (ID: `None`, Class: `px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 border border-slate-700`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 border border-slate-700")*
- **Line 18**: Button (ID: `None`, Class: `px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-400 hover:to-emerald-500 text-white shadow-[0_0_15px_rgba(34,197,94,0.3)] rounded-lg text-sm font-bold transition-all flex items-center gap-2 border border-green-400/50`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-400 hover:to-emerald-500 text-white shadow-[0_0_15px_rgba(34,197,94,0.3)] rounded-lg text-sm font-bold transition-all flex items-center gap-2 border border-green-400/50")*
- **Line 91**: Button (ID: `None`, Class: `ms-auto px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-lg text-xs font-semibold text-slate-300 transition-colors`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "ms-auto px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-lg text-xs font-semibold text-slate-300 transition-colors")*
- **Line 242**: Button (ID: `None`, Class: `px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-sm font-bold transition-all border border-slate-700 flex items-center gap-2`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-sm font-bold transition-all border border-slate-700 flex items-center gap-2")*
- **Line 245**: Button (ID: `None`, Class: `px-6 py-2.5 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-400 hover:to-emerald-500 text-white rounded-xl text-sm font-black tracking-wide shadow-[0_0_20px_rgba(34,197,94,0.3)] transition-all flex items-center gap-2 border border-green-400/50`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "px-6 py-2.5 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-400 hover:to-emerald-500 text-white rounded-xl text-sm font-black tracking-wide shadow-[0_0_20px_rgba(34,197,94,0.3)] transition-all flex items-center gap-2 border border-green-400/50")*

---

### File: `templates/en/wallet.html`

#### Form Elements:
- **Line 144**: Form (Action: `/wallet/regenerate-key`) → *Issues: Missing ID*
- **Line 238**: Form (Action: `/redeem`) → *Issues: Missing ID*

#### Input Elements:
- **Line 239**: Input (ID: `None`, Type: `text`) → *Issues: Missing ID; Hardcoded placeholder: "XXXX-XXXX-XXXX"*

#### Button Elements:
- **Line 111**: Button (ID: `None`, Class: `btn-wallet`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-wallet")*
- **Line 138**: Button (ID: `toggleKeyBtn`, Class: `btn-wallet`) → *Issues: Missing proper hover/focus classes (class: "btn-wallet")*
- **Line 143**: Button (ID: `None`, Class: `btn-wallet`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-wallet")*
- **Line 145**: Button (ID: `None`, Class: `btn-wallet`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-wallet")*
- **Line 170**: Button (ID: `None`, Class: `preset-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "preset-btn")*
- **Line 171**: Button (ID: `None`, Class: `preset-btn selected`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "preset-btn selected")*
- **Line 172**: Button (ID: `None`, Class: `preset-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "preset-btn")*
- **Line 173**: Button (ID: `None`, Class: `preset-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "preset-btn")*
- **Line 183**: Button (ID: `None`, Class: `coin-btn selected`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "coin-btn selected")*
- **Line 184**: Button (ID: `None`, Class: `coin-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "coin-btn")*
- **Line 185**: Button (ID: `None`, Class: `coin-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "coin-btn")*
- **Line 186**: Button (ID: `None`, Class: `coin-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "coin-btn")*
- **Line 187**: Button (ID: `None`, Class: `coin-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "coin-btn")*
- **Line 188**: Button (ID: `None`, Class: `coin-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "coin-btn")*
- **Line 191**: Button (ID: `btnTopup`, Class: `btn-topup`) → *Issues: Missing proper hover/focus classes (class: "btn-topup")*
- **Line 206**: Button (ID: `None`, Class: `btn-close`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-close")*
- **Line 224**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*
- **Line 240**: Button (ID: `None`, Class: `btn-redeem`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-redeem")*

---

### File: `templates/en/war_room.html`

#### Textarea Elements:
- **Line 197**: Textarea (ID: `None`) → *Issues: Missing ID*

#### Button Elements:
- **Line 138**: Button (ID: `None`, Class: `bg-green-500/10 text-green-400 border border-green-500/20 px-3 py-1.5 rounded-lg text-xs font-bold font-mono tracking-wider hover:bg-green-500/20 hover:border-green-400 transition-all flex items-center gap-2`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "bg-green-500/10 text-green-400 border border-green-500/20 px-3 py-1.5 rounded-lg text-xs font-bold font-mono tracking-wider hover:bg-green-500/20 hover:border-green-400 transition-all flex items-center gap-2")*
- **Line 166**: Button (ID: `None`, Class: `bg-green-500/10 text-green-400 border border-green-500/20 px-3 py-1.5 rounded-lg text-xs font-bold font-mono tracking-wider hover:bg-green-500/20 hover:border-green-400 transition-all flex items-center gap-2`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "bg-green-500/10 text-green-400 border border-green-500/20 px-3 py-1.5 rounded-lg text-xs font-bold font-mono tracking-wider hover:bg-green-500/20 hover:border-green-400 transition-all flex items-center gap-2")*
- **Line 199**: Button (ID: `None`, Class: `bg-green-500/10 text-green-400 border border-green-500/20 px-3 py-1.5 rounded-lg text-xs font-bold font-mono tracking-wider hover:bg-green-500/20 hover:border-green-400 transition-all flex items-center gap-2`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "bg-green-500/10 text-green-400 border border-green-500/20 px-3 py-1.5 rounded-lg text-xs font-bold font-mono tracking-wider hover:bg-green-500/20 hover:border-green-400 transition-all flex items-center gap-2")*
- **Line 202**: Button (ID: `None`, Class: `bg-slate-800 text-slate-300 border border-slate-700 px-3 py-1.5 rounded-lg text-xs font-bold font-mono tracking-wider hover:bg-slate-700 hover:text-white transition-all flex items-center gap-2`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "bg-slate-800 text-slate-300 border border-slate-700 px-3 py-1.5 rounded-lg text-xs font-bold font-mono tracking-wider hover:bg-slate-700 hover:text-white transition-all flex items-center gap-2")*

---

### File: `templates/export.html`

#### Input Elements:
- **Line 78**: Input (ID: `None`, Type: `radio`) → *Issues: Missing ID*
- **Line 85**: Input (ID: `None`, Type: `radio`) → *Issues: Missing ID*

#### Button Elements:
- **Line 32**: Button (ID: `None`, Class: `pill`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "pill")*
- **Line 33**: Button (ID: `None`, Class: `pill`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "pill")*
- **Line 34**: Button (ID: `None`, Class: `pill active`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "pill active")*
- **Line 35**: Button (ID: `None`, Class: `pill`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "pill")*
- **Line 36**: Button (ID: `None`, Class: `pill`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "pill")*
- **Line 93**: Button (ID: `None`, Class: `btn btn-export`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-export")*

---

### File: `templates/for_employers.html`

#### Input Elements:
- **Line 348**: Input (ID: `company_name`, Type: `text`) → *Issues: Hardcoded placeholder: "مثال: Murex, Bank Audi..."*
- **Line 352**: Input (ID: `job_title`, Type: `text`) → *Issues: Hardcoded placeholder: "مثال: مهندس شبكات أول"*
- **Line 356**: Input (ID: `location`, Type: `text`) → *Issues: Hardcoded placeholder: "مثال: بيروت، لبنان"*
- **Line 374**: Input (ID: `salary`, Type: `text`) → *Issues: Hardcoded placeholder: "مثال: 2,500$ - 3,500$/شهر"*
- **Line 378**: Input (ID: `contact_email`, Type: `email`) → *Issues: Hardcoded placeholder: "hr@yourcompany.com"*
- **Line 389**: Input (ID: `apply_url`, Type: `url`) → *Issues: Hardcoded placeholder: "https://yourcompany.com/careers/..."*
- **Line 393**: Input (ID: `logo_url`, Type: `url`) → *Issues: Hardcoded placeholder: "https://yourcompany.com/logo.png"*

#### Textarea Elements:
- **Line 383**: Textarea (ID: `description`) → *Issues: Hardcoded placeholder: "اشرح الدور، المسؤوليات، المتطلبات، وليش شركتك مكان رائع للعمل...

💡 نصيحة: اذكر الفوائد، بيئة العمل، وفرص التطور لتحصل على ضعف المتقدمين!"*

#### Button Elements:
- **Line 202**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*
- **Line 217**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*
- **Line 232**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*
- **Line 248**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*
- **Line 255**: Button (ID: `None`, Class: `duration-btn selected`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "duration-btn selected")*
- **Line 258**: Button (ID: `None`, Class: `duration-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "duration-btn")*
- **Line 261**: Button (ID: `None`, Class: `duration-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "duration-btn")*
- **Line 264**: Button (ID: `None`, Class: `duration-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "duration-btn")*
- **Line 267**: Button (ID: `None`, Class: `duration-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "duration-btn")*
- **Line 417**: Button (ID: `submitBtn`, Class: `submit-btn`) → *Issues: Missing proper hover/focus classes (class: "submit-btn")*

---

### File: `templates/forgot_password.html`

#### Input Elements:
- **Line 312**: Input (ID: `email`, Type: `email`) → *Issues: Hardcoded placeholder: "you@example.com"*

#### Button Elements:
- **Line 314**: Button (ID: `forgotBtn`, Class: `btn-submit`) → *Issues: Missing proper hover/focus classes (class: "btn-submit")*

---

### File: `templates/funnel_analytics.html`

#### Button Elements:
- **Line 285**: Button (ID: `None`, Class: `funnel-filter-btn active`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "funnel-filter-btn active")*
- **Line 286**: Button (ID: `None`, Class: `funnel-filter-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "funnel-filter-btn")*
- **Line 287**: Button (ID: `None`, Class: `funnel-filter-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "funnel-filter-btn")*
- **Line 288**: Button (ID: `None`, Class: `funnel-filter-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "funnel-filter-btn")*

---

### File: `templates/growth_station.html`

#### Input Elements:
- **Line 203**: Input (ID: `keyword`, Type: `text`) → *Issues: Hardcoded placeholder: "مثال: React Developer أو ATS"*
- **Line 208**: Input (ID: `location`, Type: `text`) → *Issues: Hardcoded placeholder: "مثال: Lebanon أو Dubai"*
- **Line 304**: Input (ID: `search-input`, Type: `text`) → *Issues: Hardcoded placeholder: "ابحث بالاسم أو البريد..."*
- **Line 355**: Input (ID: `campaign-name`, Type: `text`) → *Issues: Hardcoded placeholder: "مثال: React Developers Lebanon"*

#### Button Elements:
- **Line 221**: Button (ID: `None`, Class: `btn-premium w-full flex items-center justify-center gap-2 mt-4`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-premium w-full flex items-center justify-center gap-2 mt-4")*
- **Line 306**: Button (ID: `None`, Class: `btn-premium flex items-center gap-1.5 text-sm`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-premium flex items-center gap-1.5 text-sm")*
- **Line 339**: Button (ID: `prev-btn`, Class: `btn-secondary-premium px-3 py-1.5 text-xs`) → *Issues: Missing proper hover/focus classes (class: "btn-secondary-premium px-3 py-1.5 text-xs")*
- **Line 340**: Button (ID: `next-btn`, Class: `btn-secondary-premium px-3 py-1.5 text-xs`) → *Issues: Missing proper hover/focus classes (class: "btn-secondary-premium px-3 py-1.5 text-xs")*
- **Line 360**: Button (ID: `None`, Class: `btn-secondary-premium`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-secondary-premium")*
- **Line 361**: Button (ID: `None`, Class: `btn-premium`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-premium")*
- **Line 372**: Button (ID: `None`, Class: `btn-premium`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-premium")*

---

### File: `templates/index_v2.html`

#### Button Elements:
- **Line 651**: Button (ID: `None`, Class: `mobile-menu-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "mobile-menu-btn")*
- **Line 897**: Button (ID: `None`, Class: `active`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "active")*
- **Line 898**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*
- **Line 899**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*
- **Line 900**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*

---

### File: `templates/index_v3.html`

#### Button Elements:
- **Line 2307**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*
- **Line 2750**: Button (ID: `None`, Class: `calc-tab active`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "calc-tab active")*
- **Line 2751**: Button (ID: `None`, Class: `calc-tab`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "calc-tab")*
- **Line 2752**: Button (ID: `None`, Class: `calc-tab`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "calc-tab")*
- **Line 3732**: Button (ID: `None`, Class: `exit-close`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "exit-close")*

---

### File: `templates/index_v4.html`

#### Input Elements:
- **Line 329**: Input (ID: `atsJobTitle`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. Software Engineer"*
- **Line 333**: Input (ID: `atsSkills`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. Python, React, AWS"*

#### Button Elements:
- **Line 89**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*
- **Line 335**: Button (ID: `None`, Class: `primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "primary")*
- **Line 460**: Button (ID: `None`, Class: `primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "primary")*
- **Line 711**: Button (ID: `None`, Class: `faq-question`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "faq-question")*
- **Line 720**: Button (ID: `None`, Class: `faq-question`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "faq-question")*
- **Line 729**: Button (ID: `None`, Class: `faq-question`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "faq-question")*
- **Line 738**: Button (ID: `None`, Class: `faq-question`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "faq-question")*
- **Line 747**: Button (ID: `None`, Class: `faq-question`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "faq-question")*
- **Line 756**: Button (ID: `None`, Class: `faq-question`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "faq-question")*
- **Line 765**: Button (ID: `None`, Class: `faq-question`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "faq-question")*
- **Line 774**: Button (ID: `None`, Class: `faq-question`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "faq-question")*

---

### File: `templates/login.html`

#### Form Elements:
- **Line 146**: Form (Action: `/login`) → *Issues: Missing ID*

#### Input Elements:
- **Line 149**: Input (ID: `email`, Type: `email`) → *Issues: Hardcoded placeholder: "اسمك@مثال.com"*
- **Line 153**: Input (ID: `password`, Type: `password`) → *Issues: Hardcoded placeholder: "●●●●●●●●"*

#### Button Elements:
- **Line 158**: Button (ID: `loginBtn`, Class: `btn-submit`) → *Issues: Missing proper hover/focus classes (class: "btn-submit")*

---

### File: `templates/login_v2.html`

#### Input Elements:
- **Line 187**: Input (ID: `email`, Type: `email`) → *Issues: Hardcoded placeholder: "you@example.com"*
- **Line 192**: Input (ID: `password`, Type: `password`) → *Issues: Hardcoded placeholder: "●●●●●●●●"*
- **Line 203**: Input (ID: `None`, Type: `checkbox`) → *Issues: Missing ID*

#### Button Elements:
- **Line 193**: Button (ID: `pwToggle`, Class: `pw-toggle-btn`) → *Issues: Missing proper hover/focus classes (class: "pw-toggle-btn")*
- **Line 207**: Button (ID: `loginBtn`, Class: `btn-submit`) → *Issues: Missing proper hover/focus classes (class: "btn-submit")*

---

### File: `templates/my_purchases.html`

#### Button Elements:
- **Line 119**: Button (ID: `None`, Class: `btn-copy`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-copy")*

---

### File: `templates/new_campaign_v2.html`

#### Input Elements:
- **Line 98**: Input (ID: `None`, Type: `radio`) → *Issues: Missing ID*
- **Line 146**: Input (ID: `None`, Type: `checkbox`) → *Issues: Missing ID*

#### Button Elements:
- **Line 56**: Button (ID: `None`, Class: `px-5 py-3.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded-xl transition-all flex items-center justify-center gap-2`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "px-5 py-3.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded-xl transition-all flex items-center justify-center gap-2")*
- **Line 167**: Button (ID: `None`, Class: `text-xs font-bold text-red-400 hover:text-red-300 transition-colors uppercase tracking-wider flex items-center gap-1`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "text-xs font-bold text-red-400 hover:text-red-300 transition-colors uppercase tracking-wider flex items-center gap-1")*
- **Line 199**: Button (ID: `submitBtn`, Class: `w-full md:w-auto px-10 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-lg font-black tracking-wide shadow-[0_0_20px_rgba(79,70,229,0.3)] hover:shadow-[0_0_30px_rgba(79,70,229,0.5)] transition-all flex items-center justify-center gap-3 border border-indigo-400/30 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none`) → *Issues: Missing proper hover/focus classes (class: "w-full md:w-auto px-10 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-lg font-black tracking-wide shadow-[0_0_20px_rgba(79,70,229,0.3)] hover:shadow-[0_0_30px_rgba(79,70,229,0.5)] transition-all flex items-center justify-center gap-3 border border-indigo-400/30 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none")*

---

### File: `templates/offers.html`

#### Form Elements:
- **Line 188**: Form (Action: `/api/v2/offers/import-keys`) → *Issues: Missing ID*
- **Line 289**: Form (Action: `/api/v2/offers/delete/{{ offer.offer_id }}`) → *Issues: Missing ID*
- **Line 389**: Form (Action: `/api/v2/offers/delete-key/{{ k.key_id }}`) → *Issues: Missing ID*

#### Input Elements:
- **Line 134**: Input (ID: `offerTitle`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. Executive CV Makeover + 100 Companies"*
- **Line 138**: Input (ID: `offerPrice`, Type: `number`) → *Issues: Hardcoded placeholder: "e.g. 19.99"*
- **Line 142**: Input (ID: `offerOriginalPrice`, Type: `number`) → *Issues: Hardcoded placeholder: "e.g. 49.99"*
- **Line 150**: Input (ID: `offerImage`, Type: `text`) → *Issues: Hardcoded placeholder: "Paste image link URL or upload below..."*
- **Line 168**: Input (ID: `offerApiUrl`, Type: `url`) → *Issues: Hardcoded placeholder: "https://api.provider.com/v1/generate"*
- **Line 172**: Input (ID: `offerApiKey`, Type: `text`) → *Issues: Hardcoded placeholder: "API Secret Key Token"*
- **Line 439**: Input (ID: `editOfferTitle`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. Executive CV Makeover + 100 Companies"*
- **Line 443**: Input (ID: `editOfferPrice`, Type: `number`) → *Issues: Hardcoded placeholder: "e.g. 19.99"*
- **Line 447**: Input (ID: `editOfferOriginalPrice`, Type: `number`) → *Issues: Hardcoded placeholder: "e.g. 49.99"*
- **Line 455**: Input (ID: `editOfferImage`, Type: `text`) → *Issues: Hardcoded placeholder: "Paste image link URL or upload below..."*
- **Line 473**: Input (ID: `editOfferApiUrl`, Type: `url`) → *Issues: Hardcoded placeholder: "https://api.provider.com/v1/generate"*
- **Line 477**: Input (ID: `editOfferApiKey`, Type: `text`) → *Issues: Hardcoded placeholder: "API Secret Key Token"*

#### Textarea Elements:
- **Line 146**: Textarea (ID: `offerDesc`) → *Issues: Hardcoded placeholder: "Explain what is included in this offer in detail..."*
- **Line 177**: Textarea (ID: `offerNote`) → *Issues: Hardcoded placeholder: "e.g. Note: Delivery takes 48 hours and requires your current CV."*
- **Line 201**: Textarea (ID: `importKeysText`) → *Issues: Hardcoded placeholder: "Paste your keys, account credentials, or links here.
One item per line.
e.g. USER:PASS-IPTV-123
e.g. https://vpn.com/claim?code=abc"*
- **Line 418**: Textarea (ID: `modalReqs`) → *Issues: Hardcoded placeholder: "Specify your preferences, target industries, links, email text guidelines, or details of what you need..."*
- **Line 451**: Textarea (ID: `editOfferDesc`) → *Issues: Hardcoded placeholder: "Explain what is included in this offer in detail..."*
- **Line 482**: Textarea (ID: `editOfferNote`) → *Issues: Hardcoded placeholder: "e.g. Note: Delivery takes 48 hours."*
- **Line 785**: Textarea (ID: `fulfillCredentials`) → *Issues: Hardcoded placeholder: "الصق بيانات دخول IPTV، مفتاح الترخيص، تفاصيل الحساب، أو التعليمات هنا..."*

#### Button Elements:
- **Line 153**: Button (ID: `None`, Class: `btn-cyber secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber secondary")*
- **Line 180**: Button (ID: `None`, Class: `btn-cyber primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber primary")*
- **Line 207**: Button (ID: `None`, Class: `btn-cyber primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber primary")*
- **Line 281**: Button (ID: `None`, Class: `btn-cyber primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber primary")*
- **Line 288**: Button (ID: `None`, Class: `btn-cyber secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber secondary")*
- **Line 290**: Button (ID: `None`, Class: `btn-cyber secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber secondary")*
- **Line 344**: Button (ID: `None`, Class: `btn-cyber secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber secondary")*
- **Line 390**: Button (ID: `None`, Class: `None`) → *Issues: Missing ID; No classes defined (missing hover/focus states)*
- **Line 422**: Button (ID: `None`, Class: `btn-cyber secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber secondary")*
- **Line 423**: Button (ID: `None`, Class: `btn-cyber primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber primary")*
- **Line 458**: Button (ID: `None`, Class: `btn-cyber secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber secondary")*
- **Line 488**: Button (ID: `None`, Class: `btn-cyber secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber secondary")*
- **Line 490**: Button (ID: `None`, Class: `btn-cyber secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber secondary")*
- **Line 491**: Button (ID: `None`, Class: `btn-cyber primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber primary")*
- **Line 789**: Button (ID: `None`, Class: `btn-cyber secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber secondary")*
- **Line 790**: Button (ID: `None`, Class: `btn-cyber primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-cyber primary")*

---

### File: `templates/pricing_v2.html`

#### Button Elements:
- **Line 659**: Button (ID: `None`, Class: `toast-close`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "toast-close")*

---

### File: `templates/pricing_v3.html`

#### Button Elements:
- **Line 669**: Button (ID: `None`, Class: `toast-close-v3`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "toast-close-v3")*

---

### File: `templates/register.html`

#### Form Elements:
- **Line 168**: Form (Action: `/register`) → *Issues: Missing ID*

#### Input Elements:
- **Line 175**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 178**: Input (ID: `None`, Type: `text`) → *Issues: Missing ID; Hardcoded placeholder: "مثال: سام سلامة"*
- **Line 182**: Input (ID: `None`, Type: `email`) → *Issues: Missing ID; Hardcoded placeholder: "you@example.com"*
- **Line 186**: Input (ID: `None`, Type: `tel`) → *Issues: Missing ID; Hardcoded placeholder: "مثال: +961 70 000 000"*
- **Line 190**: Input (ID: `None`, Type: `password`) → *Issues: Missing ID; Hardcoded placeholder: "8 أحرف على الأقل"*

#### Button Elements:
- **Line 197**: Button (ID: `None`, Class: `btn-submit`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-submit")*

---

### File: `templates/register_v2.html`

#### Input Elements:
- **Line 225**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 228**: Input (ID: `regName`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. Sam Salameh"*
- **Line 233**: Input (ID: `regEmail`, Type: `email`) → *Issues: Hardcoded placeholder: "you@example.com"*
- **Line 238**: Input (ID: `regPhone`, Type: `tel`) → *Issues: Hardcoded placeholder: "e.g. +961 70 000 000"*
- **Line 243**: Input (ID: `regPassword`, Type: `password`) → *Issues: Hardcoded placeholder: "Min. 8 characters"*

#### Button Elements:
- **Line 244**: Button (ID: `regPwToggle`, Class: `pw-toggle-btn`) → *Issues: Missing proper hover/focus classes (class: "pw-toggle-btn")*
- **Line 267**: Button (ID: `registerBtn`, Class: `btn-solid`) → *Issues: Missing proper hover/focus classes (class: "btn-solid")*

---

### File: `templates/reset_password.html`

#### Input Elements:
- **Line 237**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 242**: Input (ID: `password`, Type: `password`) → *Issues: Hardcoded placeholder: "8 أحرف على الأقل"*
- **Line 269**: Input (ID: `confirmPassword`, Type: `password`) → *Issues: Hardcoded placeholder: "Repeat new password"*

#### Button Elements:
- **Line 249**: Button (ID: `pwToggle`, Class: `pw-toggle-btn`) → *Issues: Missing proper hover/focus classes (class: "pw-toggle-btn")*
- **Line 273**: Button (ID: `confirmToggle`, Class: `pw-toggle-btn`) → *Issues: Missing proper hover/focus classes (class: "pw-toggle-btn")*
- **Line 278**: Button (ID: `resetBtn`, Class: `btn-submit`) → *Issues: Missing proper hover/focus classes (class: "btn-submit")*

---

### File: `templates/resume_tailor.html`

#### Input Elements:
- **Line 334**: Input (ID: `tailor-job-title`, Type: `text`) → *Issues: Hardcoded placeholder: "المسمى الوظيفي (اختياري، يساعد في سياق الذكاء الاصطناعي)"*

#### Textarea Elements:
- **Line 312**: Textarea (ID: `tailor-resume`) → *Issues: Hardcoded placeholder: "الصق نص سيرتك الذاتية بالكامل هنا...

SAM SALAMEH
Senior Network Engineer | CCNA, Fortinet NSE, MikroTik MTCNA
samsalameh.cv@gmail.com | +961 70 841 1009

PROFESSIONAL SUMMARY
15+ years as a Network Engineer specializing in enterprise network design..."*
- **Line 324**: Textarea (ID: `tailor-job`) → *Issues: Hardcoded placeholder: "الصق الوصف الوظيفي الذي تريد التخصيص له...

Network Engineer — Beirut, Lebanon

Requirements:
• 5+ years Cisco/Juniper experience
• CCNP or equivalent
• Strong BGP, OSPF, MPLS knowledge
• Fortinet firewall experience
..."*

#### Button Elements:
- **Line 346**: Button (ID: `btn-tailor`, Class: `btn btn-ai`) → *Issues: Missing proper hover/focus classes (class: "btn btn-ai")*
- **Line 371**: Button (ID: `toggle-tailored`, Class: `diff-toggle-btn active`) → *Issues: Missing proper hover/focus classes (class: "diff-toggle-btn active")*
- **Line 372**: Button (ID: `toggle-diff`, Class: `diff-toggle-btn`) → *Issues: Missing proper hover/focus classes (class: "diff-toggle-btn")*
- **Line 390**: Button (ID: `None`, Class: `btn btn-outline btn-sm`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-outline btn-sm")*
- **Line 391**: Button (ID: `None`, Class: `btn btn-primary btn-sm`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-primary btn-sm")*

---

### File: `templates/roast.html`

#### Button Elements:
- **Line 16**: Button (ID: `roastBtn`, Class: `btn-primary`) → *Issues: Missing proper hover/focus classes (class: "btn-primary")*

---

### File: `templates/sent_emails.html`

#### Input Elements:
- **Line 38**: Input (ID: `searchInput`, Type: `text`) → *Issues: Hardcoded placeholder: "ابحث باسم الشركة، المسمى الوظيفي، أو البريد الإلكتروني..."*

#### Button Elements:
- **Line 46**: Button (ID: `None`, Class: `px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-semibold transition-all border border-slate-700 flex items-center gap-2 whitespace-nowrap`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-semibold transition-all border border-slate-700 flex items-center gap-2 whitespace-nowrap")*
- **Line 95**: Button (ID: `loadMoreBtn`, Class: `px-6 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-xl text-sm font-semibold transition-all inline-flex items-center gap-2`) → *Issues: Missing proper hover/focus classes (class: "px-6 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-xl text-sm font-semibold transition-all inline-flex items-center gap-2")*

---

### File: `templates/services.html`

#### Form Elements:
- **Line 427**: Form (Action: `/services/purchase`) → *Issues: Missing ID*
- **Line 458**: Form (Action: `/services/purchase`) → *Issues: Missing ID*
- **Line 489**: Form (Action: `/services/purchase`) → *Issues: Missing ID*

#### Input Elements:
- **Line 416**: Input (ID: `None`, Type: `checkbox`) → *Issues: Missing ID*
- **Line 428**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 429**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 447**: Input (ID: `None`, Type: `checkbox`) → *Issues: Missing ID*
- **Line 459**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 460**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 478**: Input (ID: `None`, Type: `checkbox`) → *Issues: Missing ID*
- **Line 490**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*
- **Line 491**: Input (ID: `None`, Type: `hidden`) → *Issues: Missing ID*

#### Button Elements:
- **Line 341**: Button (ID: `None`, Class: `hamburger`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "hamburger")*
- **Line 431**: Button (ID: `None`, Class: `btn btn-secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-secondary")*
- **Line 433**: Button (ID: `None`, Class: `btn btn-primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-primary")*
- **Line 462**: Button (ID: `None`, Class: `btn btn-secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-secondary")*
- **Line 464**: Button (ID: `None`, Class: `btn btn-primary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-primary")*
- **Line 493**: Button (ID: `None`, Class: `btn btn-secondary`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-secondary")*
- **Line 495**: Button (ID: `None`, Class: `btn btn-magenta`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-magenta")*
- **Line 508**: Button (ID: `bulkBtn`, Class: `btn-bulk-buy`) → *Issues: Missing proper hover/focus classes (class: "btn-bulk-buy")*

---

### File: `templates/services_new.html`

#### Button Elements:
- **Line 144**: Button (ID: `None`, Class: `cat-tab active`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "cat-tab active")*
- **Line 145**: Button (ID: `None`, Class: `cat-tab`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "cat-tab")*
- **Line 146**: Button (ID: `None`, Class: `cat-tab`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "cat-tab")*
- **Line 147**: Button (ID: `None`, Class: `cat-tab`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "cat-tab")*
- **Line 148**: Button (ID: `None`, Class: `cat-tab`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "cat-tab")*
- **Line 149**: Button (ID: `None`, Class: `cat-tab`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "cat-tab")*
- **Line 193**: Button (ID: `cartFab`, Class: `cart-badge-btn`) → *Issues: Missing proper hover/focus classes (class: "cart-badge-btn")*
- **Line 203**: Button (ID: `None`, Class: `cart-close`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "cart-close")*
- **Line 216**: Button (ID: `checkoutBtn`, Class: `cart-checkout`) → *Issues: Missing proper hover/focus classes (class: "cart-checkout")*
- **Line 229**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*

---

### File: `templates/services_v2.html`

#### Input Elements:
- **Line 978**: Input (ID: `customerName`, Type: `text`) → *Issues: Hardcoded placeholder: "مثال: فلان الفلاني"*
- **Line 980**: Input (ID: `customerEmail`, Type: `email`) → *Issues: Hardcoded placeholder: "مثال: flan@example.com"*

#### Button Elements:
- **Line 806**: Button (ID: `None`, Class: `btn-buy btn-buy-micro`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-buy btn-buy-micro")*
- **Line 835**: Button (ID: `None`, Class: `btn-buy btn-buy-standard`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-buy btn-buy-standard")*
- **Line 864**: Button (ID: `None`, Class: `btn-buy btn-buy-premium`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-buy btn-buy-premium")*
- **Line 894**: Button (ID: `None`, Class: `btn-bouquet`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-bouquet")*
- **Line 944**: Button (ID: `cartToggle`, Class: `cart-toggle`) → *Issues: Missing proper hover/focus classes (class: "cart-toggle")*
- **Line 954**: Button (ID: `None`, Class: `cart-close`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "cart-close")*
- **Line 964**: Button (ID: `None`, Class: `cart-checkout`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "cart-checkout")*
- **Line 970**: Button (ID: `None`, Class: `modal-close`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "modal-close")*
- **Line 982**: Button (ID: `submitBtn`, Class: `btn-submit`) → *Issues: Missing proper hover/focus classes (class: "btn-submit")*

---

### File: `templates/track_application.html`

#### Form Elements:
- **Line 149**: Form (Action: `/track-application`) → *Issues: Missing ID*

#### Input Elements:
- **Line 152**: Input (ID: `None`, Type: `email`) → *Issues: Missing ID; Hardcoded placeholder: "you@email.com"*

#### Button Elements:
- **Line 154**: Button (ID: `None`, Class: `btn btn-search`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-search")*

---

### File: `templates/upload_cv_v2.html`

#### Input Elements:
- **Line 569**: Input (ID: `fullName`, Type: `text`) → *Issues: Hardcoded placeholder: "e.g. Sam Salameh"*
- **Line 570**: Input (ID: `email`, Type: `email`) → *Issues: Hardcoded placeholder: "your@email.com"*
- **Line 573**: Input (ID: `phone`, Type: `text`) → *Issues: Hardcoded placeholder: "+961 3 123 456"*
- **Line 574**: Input (ID: `location`, Type: `text`) → *Issues: Hardcoded placeholder: "بيروت، لبنان"*
- **Line 577**: Input (ID: `currentTitle`, Type: `text`) → *Issues: Hardcoded placeholder: "مهندس شبكات أول"*
- **Line 581**: Input (ID: `education`, Type: `text`) → *Issues: Hardcoded placeholder: "بكالوريوس هندسة"*
- **Line 582**: Input (ID: `linkedin`, Type: `url`) → *Issues: Hardcoded placeholder: "https://linkedin.com/in/..."*
- **Line 585**: Input (ID: `certsInput`, Type: `text`) → *Issues: Hardcoded placeholder: "CCNA, NSE, MTCNA..."*
- **Line 586**: Input (ID: `langsInput`, Type: `text`) → *Issues: Hardcoded placeholder: "English, Arabic, French..."*
- **Line 587**: Input (ID: `experienceInput`, Type: `text`) → *Issues: Hardcoded placeholder: "Ogero (2020-2023), Touch (2018-2020)..."*
- **Line 594**: Input (ID: `targetCompany`, Type: `text`) → *Issues: Hardcoded placeholder: "Murex, Cisco, Bank Audi..."*
- **Line 595**: Input (ID: `targetJobTitle`, Type: `text`) → *Issues: Hardcoded placeholder: "Senior Network Engineer"*
- **Line 610**: Input (ID: `targetTitles`, Type: `text`) → *Issues: Hardcoded placeholder: "Senior Network Engineer, IT Manager..."*

#### Textarea Elements:
- **Line 546**: Textarea (ID: `cvText`) → *Issues: Hardcoded placeholder: "Paste your entire CV / resume text here...

Include: Full Name, Contact Info, Work Experience, Education, Skills, Certifications, Languages...

Then click ✨ Auto-Fill to let AI extract everything automatically."*
- **Line 588**: Textarea (ID: `summary`) → *Issues: Hardcoded placeholder: "ملخص مهني قصير..."*

#### Button Elements:
- **Line 552**: Button (ID: `parseBtn`, Class: `btn btn-ai pulse-btn`) → *Issues: Missing proper hover/focus classes (class: "btn btn-ai pulse-btn")*
- **Line 702**: Button (ID: `None`, Class: `btn btn-ai`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-ai")*
- **Line 703**: Button (ID: `None`, Class: `btn btn-sm btn-outline`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-sm btn-outline")*
- **Line 720**: Button (ID: `None`, Class: `btn pulse-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn pulse-btn")*
- **Line 723**: Button (ID: `None`, Class: `btn btn-outline`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-outline")*
- **Line 726**: Button (ID: `None`, Class: `btn btn-sm btn-outline`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-sm btn-outline")*
- **Line 738**: Button (ID: `None`, Class: `modal-close`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "modal-close")*
- **Line 741**: Button (ID: `None`, Class: `preview-tab active`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "preview-tab active")*
- **Line 742**: Button (ID: `None`, Class: `preview-tab`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "preview-tab")*
- **Line 743**: Button (ID: `None`, Class: `preview-tab`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "preview-tab")*
- **Line 749**: Button (ID: `None`, Class: `btn btn-outline btn-sm`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-outline btn-sm")*
- **Line 750**: Button (ID: `None`, Class: `btn btn-ai btn-sm`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn btn-ai btn-sm")*

---

### File: `templates/upload_cv_v3.html`

#### Input Elements:
- **Line 182**: Input (ID: `None`, Type: `text`) → *Issues: Missing ID; Hardcoded placeholder: "مثال: سام سلامة"*
- **Line 186**: Input (ID: `None`, Type: `email`) → *Issues: Missing ID; Hardcoded placeholder: "you@example.com"*
- **Line 192**: Input (ID: `None`, Type: `tel`) → *Issues: Missing ID; Hardcoded placeholder: "+961 70 000 000"*
- **Line 196**: Input (ID: `None`, Type: `text`) → *Issues: Missing ID; Hardcoded placeholder: "مثال: بيروت، لبنان"*
- **Line 201**: Input (ID: `None`, Type: `url`) → *Issues: Missing ID; Hardcoded placeholder: "https://linkedin.com/in/yourprofile"*
- **Line 212**: Input (ID: `skillsInput`, Type: `text`) → *Issues: Hardcoded placeholder: "Python، JavaScript، إدارة المشاريع، ..."*
- **Line 248**: Input (ID: `None`, Type: `text`) → *Issues: Missing ID; Hardcoded placeholder: "مثال: $60,000 - $90,000"*

#### Button Elements:
- **Line 89**: Button (ID: `None`, Class: `btn-secondary-cv`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-secondary-cv")*
- **Line 92**: Button (ID: `btnAIAnalysis`, Class: `btn-primary-cv`) → *Issues: Missing proper hover/focus classes (class: "btn-primary-cv")*
- **Line 159**: Button (ID: `None`, Class: `ms-auto px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-lg text-xs font-semibold text-slate-300 transition-colors`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "ms-auto px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-lg text-xs font-semibold text-slate-300 transition-colors")*
- **Line 308**: Button (ID: `None`, Class: `btn-secondary-cv`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-secondary-cv")*
- **Line 311**: Button (ID: `btnLaunch`, Class: `btn-primary-cv`) → *Issues: Missing proper hover/focus classes (class: "btn-primary-cv")*

---

### File: `templates/wallet.html`

#### Form Elements:
- **Line 151**: Form (Action: `/wallet/regenerate-key`) → *Issues: Missing ID*
- **Line 240**: Form (Action: `/redeem`) → *Issues: Missing ID*

#### Input Elements:
- **Line 241**: Input (ID: `None`, Type: `text`) → *Issues: Missing ID; Hardcoded placeholder: "XXXX-XXXX-XXXX"*

#### Button Elements:
- **Line 119**: Button (ID: `None`, Class: `btn-wallet`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-wallet")*
- **Line 145**: Button (ID: `toggleKeyBtn`, Class: `btn-wallet`) → *Issues: Missing proper hover/focus classes (class: "btn-wallet")*
- **Line 150**: Button (ID: `None`, Class: `btn-wallet`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-wallet")*
- **Line 152**: Button (ID: `None`, Class: `btn-wallet`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-wallet")*
- **Line 175**: Button (ID: `None`, Class: `preset-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "preset-btn")*
- **Line 176**: Button (ID: `None`, Class: `preset-btn selected`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "preset-btn selected")*
- **Line 177**: Button (ID: `None`, Class: `preset-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "preset-btn")*
- **Line 178**: Button (ID: `None`, Class: `preset-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "preset-btn")*
- **Line 188**: Button (ID: `None`, Class: `coin-btn selected`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "coin-btn selected")*
- **Line 189**: Button (ID: `None`, Class: `coin-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "coin-btn")*
- **Line 190**: Button (ID: `None`, Class: `coin-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "coin-btn")*
- **Line 191**: Button (ID: `None`, Class: `coin-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "coin-btn")*
- **Line 192**: Button (ID: `None`, Class: `coin-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "coin-btn")*
- **Line 193**: Button (ID: `None`, Class: `coin-btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "coin-btn")*
- **Line 196**: Button (ID: `btnTopup`, Class: `btn-topup`) → *Issues: Missing proper hover/focus classes (class: "btn-topup")*
- **Line 210**: Button (ID: `None`, Class: `btn-close`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-close")*
- **Line 227**: Button (ID: `None`, Class: `btn`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn")*
- **Line 242**: Button (ID: `None`, Class: `btn-redeem`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "btn-redeem")*

---

### File: `templates/war_room.html`

#### Textarea Elements:
- **Line 189**: Textarea (ID: `None`) → *Issues: Missing ID*

#### Button Elements:
- **Line 132**: Button (ID: `None`, Class: `bg-green-500/10 text-green-400 border border-green-500/20 px-3 py-1.5 rounded-lg text-base font-bold font-mono hover:bg-green-500/20 hover:border-green-400 transition-all flex items-center gap-2`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "bg-green-500/10 text-green-400 border border-green-500/20 px-3 py-1.5 rounded-lg text-base font-bold font-mono hover:bg-green-500/20 hover:border-green-400 transition-all flex items-center gap-2")*
- **Line 159**: Button (ID: `None`, Class: `bg-green-500/10 text-green-400 border border-green-500/20 px-3 py-1.5 rounded-lg text-base font-bold font-mono hover:bg-green-500/20 hover:border-green-400 transition-all flex items-center gap-2`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "bg-green-500/10 text-green-400 border border-green-500/20 px-3 py-1.5 rounded-lg text-base font-bold font-mono hover:bg-green-500/20 hover:border-green-400 transition-all flex items-center gap-2")*
- **Line 191**: Button (ID: `None`, Class: `bg-green-500/10 text-green-400 border border-green-500/20 px-3 py-1.5 rounded-lg text-base font-bold font-mono hover:bg-green-500/20 hover:border-green-400 transition-all flex items-center gap-2`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "bg-green-500/10 text-green-400 border border-green-500/20 px-3 py-1.5 rounded-lg text-base font-bold font-mono hover:bg-green-500/20 hover:border-green-400 transition-all flex items-center gap-2")*
- **Line 194**: Button (ID: `None`, Class: `bg-slate-800 text-slate-300 border border-slate-700 px-3 py-1.5 rounded-lg text-base font-bold font-mono hover:bg-slate-700 hover:text-white transition-all flex items-center gap-2`) → *Issues: Missing ID; Missing proper hover/focus classes (class: "bg-slate-800 text-slate-300 border border-slate-700 px-3 py-1.5 rounded-lg text-base font-bold font-mono hover:bg-slate-700 hover:text-white transition-all flex items-center gap-2")*

---


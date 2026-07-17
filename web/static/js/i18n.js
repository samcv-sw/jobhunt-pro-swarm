/**
* JobHunt Pro i18n — Arabic/English Translation Engine
* v1.0 — Auto-translates UI via data-i18n attributes + text scanning
*/
(function() {
const LANG_KEY = 'jobhunt_lang';
const DICT = {
'Home': 'الرئيسية',
'Dashboard': 'لوحة التحكم',
'Upload CV': 'رفع السيرة الذاتية',
'Pricing': 'الأسعار',
'Services': 'الخدمات',
'Wallet': 'المحفظة',
'Stats': 'الإحصائيات',
'Email Test': 'اختبار البريد',
'Sent Emails': 'البريد المرسل',
'Login': 'تسجيل الدخول',
'Register': 'إنشاء حساب',
'Logout': 'تسجيل الخروج',
'Profile': 'الملف الشخصي',
'Admin': 'المشرف',
'Settings': 'الإعدادات',
'Help': 'مساعدة',
'About': 'حول',
'Contact': 'اتصل بنا',
'Privacy': 'الخصوصية',
'Terms': 'الشروط',
'Save': 'حفظ',
'Cancel': 'إلغاء',
'Delete': 'حذف',
'Edit': 'تعديل',
'Submit': 'إرسال',
'Send': 'إرسال',
'Upload': 'رفع',
'Download': 'تحميل',
'Search': 'بحث',
'Filter': 'تصفية',
'Reset': 'إعادة تعيين',
'Confirm': 'تأكيد',
'Back': 'رجوع',
'Next': 'التالي',
'Previous': 'السابق',
'Close': 'إغلاق',
'Copy': 'نسخ',
'Share': 'مشاركة',
'Export': 'تصدير',
'Import': 'استيراد',
'Refresh': 'تحديث',
'View': 'عرض',
'Preview': 'معاينة',
'Apply': 'تطبيق',
'Buy': 'شراء',
'Pay': 'دفع',
'Checkout': 'الدفع',
'Add to Cart': 'أضف إلى السلة',
'Name': 'الاسم',
'Full Name': 'الاسم الكامل',
'Email': 'البريد الإلكتروني',
'Password': 'كلمة المرور',
'Phone': 'الهاتف',
'Location': 'الموقع',
'Country': 'البلد',
'City': 'المدينة',
'Skills': 'المهارات',
'Experience': 'الخبرة',
'Education': 'التعليم',
'Certifications': 'الشهادات',
'Languages': 'اللغات',
'Summary': 'الملخص',
'Title': 'العنوان',
'Description': 'الوصف',
'Date': 'التاريخ',
'Status': 'الحالة',
'Amount': 'المبلغ',
'Price': 'السعر',
'Total': 'المجموع',
'Balance': 'الرصيد',
'Type': 'النوع',
'Category': 'الفئة',
'All': 'الكل',
'None': 'لا شيء',
'Loading...': 'جاري التحميل...',
'Loading': 'جاري التحميل',
'Processing...': 'جاري المعالجة...',
'Please wait...': 'الرجاء الانتظار...',
'Success': 'نجاح',
'Error': 'خطأ',
'Warning': 'تحذير',
'Info': 'معلومة',
'No data': 'لا توجد بيانات',
'No results': 'لا توجد نتائج',
'Not found': 'غير موجود',
'Coming soon': 'قريباً',
'Empty': 'فارغ',
'Offline': 'غير متصل',
'Online': 'متصل',
'Sign In': 'تسجيل الدخول',
'Sign Up': 'إنشاء حساب',
'Create Account': 'إنشاء حساب',
'Already have an account?': 'لديك حساب بالفعل؟',
"Don't have an account?": 'ليس لديك حساب؟',
'Forgot Password?': 'نسيت كلمة المرور؟',
'Forgot Password': 'نسيت كلمة المرور',
'Reset Password': 'إعادة تعيين كلمة المرور',
'Remember me': 'تذكرني',
'Welcome back': 'مرحباً بعودتك',
'Enter your credentials': 'أدخل بيانات الدخول',
'User Dashboard': 'لوحة تحكم المستخدم',
'CV Profiles': 'ملفات السيرة الذاتية',
'Active Campaigns': 'الحملات النشطة',
'Applications Sent': 'الطلبات المرسلة',
'Total Applications': 'إجمالي الطلبات',
'Active': 'نشط',
'Inactive': 'غير نشط',
'Completed': 'مكتمل',
'Pending': 'قيد الانتظار',
'Failed': 'فشل',
'Today': 'اليوم',
'This Week': 'هذا الأسبوع',
'This Month': 'هذا الشهر',
'Quick Actions': 'إجراءات سريعة',
'New Campaign': 'حملة جديدة',
'View All': 'عرض الكل',
'Recent Activity': 'آخر النشاطات',
'Upload Your CV': 'ارفع سيرتك الذاتية',
'Upload CV / Create Profile': 'رفع السيرة الذاتية / إنشاء ملف',
'Choose File': 'اختر ملفاً',
'Drag & drop your CV here': 'اسحب وأفلت سيرتك الذاتية هنا',
'or click to browse': 'أو انقر للتصفح',
'Supported formats': 'الصيغ المدعومة',
'PDF, DOCX, TXT': 'PDF, DOCX, TXT',
'Select CV Style': 'اختر نمط السيرة الذاتية',
'Select Email Style': 'اختر نمط البريد الإلكتروني',
'Select Cover Letter Style': 'اختر نمط رسالة التغطية',
'Professional': 'احترافي',
'Modern': 'حديث',
'Executive': 'تنفيذي',
'Technical': 'تقني',
'Friendly': 'ودود',
'Confident': 'واثق',
'Storytelling': 'سرد قصصي',
'Bullet Points': 'نقاط',
'Traditional': 'تقليدي',
'Generate Preview': 'إنشاء معاينة',
'CV Preview': 'معاينة السيرة الذاتية',
'Email Preview': 'معاينة البريد الإلكتروني',
'Cover Letter Preview': 'معاينة رسالة التغطية',
'Personal Information': 'معلومات شخصية',
'Professional Summary': 'ملخص مهني',
'Work Experience': 'الخبرة العملية',
'years': 'سنوات',
'Target Job Titles': 'المسميات الوظيفية المستهدفة',
'Target Locations': 'المواقع المستهدفة',
'Expected Salary (Local)': 'الراتب المتوقع (محلي)',
'Expected Salary (International)': 'الراتب المتوقع (دولي)',
'Save Profile': 'حفظ الملف',
'My Wallet': 'محفظتي',
'Wallet Balance': 'رصيد المحفظة',
'Add Funds': 'إضافة رصيد',
'Deposit': 'إيداع',
'Withdraw': 'سحب',
'Transaction History': 'سجل المعاملات',
'Recent Transactions': 'آخر المعاملات',
'Payment Methods': 'طرق الدفع',
'Redeem Code': 'رمز الاسترداد',
'Contact Admin': 'الاتصال بالمشرف',
'Cryptocurrency': 'عملات رقمية',
'Credit Card': 'بطاقة ائتمان',
'Enter amount': 'أدخل المبلغ',
'Enter redeem code': 'أدخل رمز الاسترداد',
'Redeem': 'استرداد',
'Balance: $': 'الرصيد: $',
'CHOOSE YOUR': 'اختر مستوى',
'POWER LEVEL': 'القوة',
'Free': 'مجاني',
'Basic': 'أساسي',
'Pro': 'محترف',
'Enterprise': 'مؤسسات',
'Starter': 'مبتدئ',
'Growth': 'نمو',
'per campaign': 'لكل حملة',
'campaigns': 'حملات',
'What\'s Included': 'ما هو متضمن',
'BUY MULTIPLE CAMPAIGNS AND SAVE BIG': 'اشترِ حملات متعددة ووفّر الكثير',
'Choose Plan': 'اختر الباقة',
'Campaign': 'حملة',
'Campaigns': 'حملات',
'Create Campaign': 'إنشاء حملة',
'Email Body': 'نص البريد الإلكتروني',
'Subject': 'الموضوع',
'To': 'إلى',
'From': 'من',
'CC': 'نسخة',
'BCC': 'نسخة مخفية',
'Attachments': 'المرفقات',
'Send Test Email': 'إرسال بريد تجريبي',
'Email sent successfully': 'تم إرسال البريد بنجاح',
'Failed to send email': 'فشل إرسال البريد',
'No profiles yet': 'لا توجد ملفات بعد',
'Create one first': 'أنشئ واحداً أولاً',
'Select CV Profile': 'اختر ملف السيرة الذاتية',
'Target Companies': 'الشركات المستهدفة',
'Company': 'شركة',
'Companies': 'شركات',
'Applications': 'طلبات',
'Sent': 'تم الإرسال',
'Delivered': 'تم التسليم',
'Opened': 'تم الفتح',
'Clicked': 'تم النقر',
'Bounced': 'مرتجع',
'Pipeline': 'خط الأنابيب',
'Status Breakdown': 'تقسيم الحالة',
'Pipeline Overview': 'نظرة عامة على خط الأنابيب',
'Total Pipeline': 'إجمالي خط الأنابيب',
'Conversion Rate': 'معدل التحويل',
'Today\'s Stats': 'إحصائيات اليوم',
'Email Analytics': 'تحليلات البريد',
'Powered by': 'مدعوم من',
'All rights reserved': 'جميع الحقوق محفوظة',
'Terms of Service': 'شروط الخدمة',
'Privacy Policy': 'سياسة الخصوصية',
'Contact Us': 'اتصل بنا',
'FAQ': 'الأسئلة الشائعة',
'Support': 'الدعم',
'English': 'English',
'Arabic': 'العربية',
'Switch to Arabic': 'التبديل إلى العربية',
'Switch to English': 'Switch to English',
'Language': 'اللغة',
'Select Language': 'اختر اللغة',
'Sending...': 'جاري الإرسال...',
'Saved!': 'تم الحفظ!',
'Deleted!': 'تم الحذف!',
'Copied!': 'تم النسخ!',
'Are you sure?': 'هل أنت متأكد؟',
'Yes': 'نعم',
'No': 'لا',
'OK': 'موافق',
'Continue': 'متابعة',
'Skip': 'تخطي',
'Try Again': 'حاول مرة أخرى',
'Retry': 'إعادة المحاولة',
'and': 'و',
'or': 'أو',
'by': 'بواسطة',
'for': 'لـ',
'in': 'في',
'on': 'على',
'at': 'في',
'with': 'مع',
};
const langToggle = document.createElement('div');
langToggle.id = 'lang-switcher';
langToggle.innerHTML = '<button id="lang-btn" type="button" title="Switch language / العربية">🇱🇧 العربية</button>';
langToggle.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:10000001;display:flex;align-items:center;pointer-events:auto;max-width:calc(100vw - 48px);';
const btn = langToggle.querySelector('#lang-btn');
btn.style.cssText = 'background:linear-gradient(135deg,#0d0d1a,#1a1a30);color:#fff;border:1px solid rgba(0,242,255,.35);padding:10px 18px;border-radius:24px;cursor:pointer;font-size:13px;font-weight:700;box-shadow:0 4px 24px rgba(0,0,0,.65);transition:all .3s;font-family:\'Inter\',sans-serif;display:inline-flex;align-items:center;gap:8px;letter-spacing:.3px;white-space:nowrap;min-width:120px;justify-content:center;backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);outline:none;line-height:1.2;';
btn.onmouseenter = () => btn.style.transform = 'scale(1.05)';
btn.onmouseleave = () => btn.style.transform = 'scale(1)';
function getLang() {
const url = new URL(window.location);
const param = url.searchParams.get('lang');
if (param === 'ar' || param === 'en') {
localStorage.setItem(LANG_KEY, param);
return param;
}
return localStorage.getItem(LANG_KEY) || 'en';
}
function setLang(lang) {
localStorage.setItem(LANG_KEY, lang);
const url = new URL(window.location);
url.searchParams.set('lang', lang);
window.history.replaceState({}, '', url);
applyLang(lang);
}
const origTextNodes = new WeakMap();
function applyLang(lang) {
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
  btn.innerHTML = lang === 'ar' ? '🇬🇧 English' : '🇱🇧 العربية';
  btn.title = lang === 'ar' ? 'Switch to English' : 'التبديل إلى العربية';
  if (lang === 'ar') {
    document.body.style.direction = 'rtl';
    document.body.style.textAlign = 'right';
    document.documentElement.classList.add('lang-ar');
    document.documentElement.classList.remove('lang-en');
  } else {
    document.body.style.direction = 'ltr';
    document.body.style.textAlign = 'left';
    document.documentElement.classList.add('lang-en');
    document.documentElement.classList.remove('lang-ar');
  }
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (el.children.length > 0) return;
    if (!el.hasAttribute('data-i18n-orig')) {
      el.setAttribute('data-i18n-orig', el.tagName === 'INPUT' && (el.type === 'text' || el.type === 'search') ? (el.placeholder || '') : el.textContent);
    }
    const orig = el.getAttribute('data-i18n-orig');
    if (lang === 'ar' && DICT[key]) {
      if (el.tagName === 'INPUT' && (el.type === 'text' || el.type === 'search')) el.placeholder = DICT[key];
      else el.textContent = DICT[key];
    } else {
      if (el.tagName === 'INPUT' && (el.type === 'text' || el.type === 'search')) el.placeholder = orig;
      else el.textContent = orig;
    }
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    if (!el.hasAttribute('data-i18n-ph-orig')) el.setAttribute('data-i18n-ph-orig', el.placeholder || '');
    const orig = el.getAttribute('data-i18n-ph-orig');
    el.placeholder = (lang === 'ar' && DICT[key]) ? DICT[key] : orig;
  });
  const walker = document.createTreeWalker(
    document.body,
    NodeFilter.SHOW_TEXT,
    { acceptNode: n => n.textContent.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP }
  );
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  const keys = Object.keys(DICT).filter(k => k.trim().length > 1).sort((a, b) => b.length - a.length);
  const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const re = new RegExp('\\b(' + keys.map(esc).join('|') + ')\\b', 'g');
  for (const node of nodes) {
    const parent = node.parentElement;
    if (!parent || ['SCRIPT','STYLE','CODE','PRE'].includes(parent.tagName)) continue;
    if (!origTextNodes.has(node)) origTextNodes.set(node, node.textContent);
    const orig = origTextNodes.get(node);
    node.textContent = lang === 'ar' ? orig.replace(re, m => DICT[m] || m) : orig;
  }
}
btn.onclick = () => {
  const current = getLang();
  setLang(current === 'ar' ? 'en' : 'ar');
};
document.addEventListener('DOMContentLoaded', () => {
document.body.appendChild(langToggle);
if (window.innerWidth <= 480) {
langToggle.style.right = '12px';
langToggle.style.bottom = '12px';
}
applyLang(getLang());
});
window.jobhuntI18n = { getLang, setLang, applyLang, DICT };
})();

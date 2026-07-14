
file_path = r'C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\register.html'
with open(file_path, encoding='utf-8') as f:
    content = f.read()

replacements = {
    'Create Account': 'إنشاء حساب جديد',
    'Start applying to 1000s of jobs with AI': 'ابدأ التقديم لآلاف الوظائف باستخدام الذكاء الاصطناعي',
    'Choose Your Plan': 'اختر باقتك',
    '>Starter<': '>المبدئية<',
    '>Basic<': '>الأساسية<',
    '>Pro 🚀<': '>الاحترافية 🚀<',
    '>Full Name<': '>الاسم الكامل<',
    '>Email Address<': '>البريد الإلكتروني<',
    '>Password<': '>كلمة المرور<',
    'Create Free Account': 'إنشاء حساب مجاني',
    'Already have an account?': 'لديك حساب بالفعل؟',
    '>Login<': '>دخول<',
    'Min. 8 characters': '8 أحرف على الأقل',
    'one-time': 'مرة واحدة',
    'applications': 'تقديم',
    'Continue with Google': 'متابعة باستخدام جوجل',
    'Continue with Microsoft': 'متابعة باستخدام مايكروسوفت',
    'OR': 'أو',
    'POPULAR': 'الأكثر طلباً',
    'Secure Checkout': 'دفع آمن',
    '100% Satisfaction': 'رضا مضمون 100%',
    'No spam': 'لا رسائل مزعجة',
    '200+ AI Agents': '200+ وكيل ذكي',
    'Deep Match': 'تطابق دقيق',
    'Smart rotation keeps your emails out of spam folders': 'نظام التدوير الذكي يبقي رسائلك بعيدة عن البريد المزعج',
    '20+ Email Providers': 'أكثر من 20 مزود بريد',
    'Real-Time Dashboard': 'لوحة تحكم فورية',
    'Track opens, clicks, responses & pipeline progress live': 'تتبع الفتح، النقرات، الردود وتقدمك بشكل مباشر',
    'Custom Cover Letters': 'رسائل تغطية مخصصة',
    'Our agents analyze your CV and craft unique cover letters for each job': 'وكلاؤنا يحللون سيرتك ويكتبون رسالة فريدة لكل وظيفة'
}

for k, v in replacements.items():
    content = content.replace(k, v)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

logger.info('register.html translated successfully.')

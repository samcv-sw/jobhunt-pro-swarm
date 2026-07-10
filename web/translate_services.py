
file_path = r'C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\services.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'The Arsenal': 'الترسانة',
    'Meet the AI agents working 24/7 to get you hired.': 'تعرف على وكلاء الذكاء الاصطناعي الذين يعملون 24/7 للحصول على وظيفة لك.',
    'Scout Agent': 'وكيل البحث (Scout)',
    'Scours 50+ job boards daily to find the perfect matches for your profile before anyone else.': 'يبحث في 50+ منصة توظيف يومياً للعثور على أفضل الوظائف المطابقة لملفك قبل أي شخص آخر.',
    'Tailor Agent': 'وكيل التخصيص (Tailor)',
    'Rewrites your resume and cover letter for EVERY single application to beat the ATS.': 'يعيد كتابة سيرتك الذاتية ورسالة التغطية لكل وظيفة لضمان تخطي نظام الـ ATS.',
    'Delivery Agent': 'وكيل الإرسال (Delivery)',
    'Rotates through 20+ email IPs to ensure your application lands in the primary inbox, not spam.': 'يقوم بالتدوير بين 20+ عنوان IP لضمان وصول طلبك إلى البريد الوارد الأساسي، وليس المزعج.',
    'Follow-up Agent': 'وكيل المتابعة (Follow-up)',
    '''Automatically sends polite bump emails to recruiters if they haven't replied in 4 days.''': 'يرسل تلقائياً رسائل متابعة مهذبة لمسؤولي التوظيف إذا لم يردوا خلال 4 أيام.',
    'Negotiator Agent': 'وكيل التفاوض (Negotiator)',
    'Analyzes market data to help you negotiate up to 20% higher salary when the offer comes.': 'يحلل بيانات السوق لمساعدتك في التفاوض على راتب أعلى بنسبة تصل إلى 20% عند تلقي العرض.'
}

for k, v in replacements.items():
    content = content.replace(k, v)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

logger.info('services.html translated successfully.')

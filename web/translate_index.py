import sys
import re

file_path = r'C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\index_v4.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'Automatically': 'تلقائياً',
    'While You': 'وأنت',
    'Your personal AI job-hunting engine works <strong style="color:var(--cyan)">24/7</strong> - searching thousands of jobs,': 'محرك بحث الوظائف بالذكاء الاصطناعي يعمل <strong style="color:var(--cyan)">24/7</strong> - يبحث في آلاف الوظائف،',
    'Less than 7 cents per application.': 'أقل من 7 سنتات لكل تقديم.',
    'Get hired or your money back.': 'احصل على وظيفة أو استرد أموالك.',
    '''Start Applying Now - It's Free''': 'ابدأ التقديم الآن - مجاناً',
    'View Pricing Plans': 'عرض باقات الأسعار',
    '>Daily Applications<': '>تقديمات يومية<',
    '>Email Providers<': '>مزود بريد<',
    '>AI Agents<': '>وكيل ذكي<',
    '>Countries<': '>دولة<',
    '>Interview Rate<': '>نسبة المقابلات<',
    '30-Day Money-Back Guarantee': 'ضمان استرداد الأموال لمدة 30 يوم',
    'No interviews? Get a full refund. No questions asked. Your risk is ZERO.': 'لم تحصل على مقابلات؟ استرد أموالك بالكامل. بدون أي أسئلة. نسبة المخاطرة صفر.',
    'SEARCHING ACROSS THESE PLATFORMS + MORE': 'نبحث في هذه المنصات وأكثر',
    'Why JobHunt Pro?': 'لماذا جوب هانت برو؟',
    'We automate the impossible.': 'نحن نؤتمت المستحيل.',
    'Human Search': 'البحث البشري',
    'AI Swarm Search': 'بحث الذكاء الاصطناعي',
    '10 applications / day': '10 تقديمات / يوم',
    '2,000+ applications / day': '2000+ تقديم / يوم',
    'Limited by time & energy': 'محدود بالوقت والطاقة',
    'Infinite scaling & zero fatigue': 'توسع لا نهائي وبدون تعب',
    'Single email provider': 'مزود بريد إلكتروني واحد',
    'Smart rotation across 20+ IPs': 'تدوير ذكي بين 20+ IP',
    'Generic resume sent everywhere': 'نفس السيرة الذاتية لكل مكان',
    'Dynamic CV tailored per job': 'سيرة ذاتية مخصصة لكل وظيفة',
    'See How It Works': 'شاهد كيف يعمل',
    'Frequently Asked Questions': 'الأسئلة الشائعة'
}

for k, v in replacements.items():
    content = content.replace(k, v)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('index_v4.html core translation successful.')

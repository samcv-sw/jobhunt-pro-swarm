
file_path = r'C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\pricing_v3.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'Choose Your Plan': 'اختر باقتك',
    'Supercharge your job hunt with AI': 'عزز بحثك عن وظيفة بالذكاء الاصطناعي',
    'Monthly': 'شهري',
    'Lifetime': 'مدى الحياة',
    'Save 40%': 'وفر 40%',
    'Most Popular': 'الأكثر طلباً',
    'Select Plan': 'اختر الباقة',
    'Current Plan': 'الباقة الحالية',
    'Custom Cover Letters': 'رسائل تغطية مخصصة',
    'Email Tracking': 'تتبع البريد',
    'Automated Follow-ups': 'متابعة آلية',
    'Priority Support': 'أولوية الدعم',
    'Buy Now': 'اشترِ الآن'
}

for k, v in replacements.items():
    content = content.replace(k, v)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

logger.info('pricing_v3.html translated successfully.')


file_path = r'C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\upload_cv_v3.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'Upload CV': 'رفع السيرة الذاتية',
    'Upload your resume in PDF, DOCX, or TXT format': 'ارفع سيرتك الذاتية بصيغة PDF أو DOCX أو TXT',
    'Upload Your Resume': 'ارفع سيرتك الذاتية',
    'Choose File': 'اختر ملف',
    'No file chosen': 'لم يتم اختيار ملف',
    'We extract skills, experience, and job preferences automatically.': 'نحن نستخرج المهارات والخبرات والتفضيلات الوظيفية تلقائياً.',
    'Extract Profile': 'استخراج الملف الشخصي',
    'Parsing your resume...': 'جاري تحليل سيرتك الذاتية...',
    'Or Paste Resume Text': 'أو انسخ والصق نص سيرتك الذاتية',
    'Paste your full resume text here...': 'انسخ نص سيرتك الذاتية بالكامل هنا...',
    'Review Profile': 'مراجعة الملف الشخصي',
    'Name': 'الاسم',
    'Job Title / Headline': 'المسمى الوظيفي / العنوان الرئيسي',
    'Summary / Objective': 'الملخص / الهدف',
    'Years of Experience': 'سنوات الخبرة',
    'Skills': 'المهارات',
    'Top skills separated by commas': 'أهم المهارات مفصولة بفواصل',
    'Save Profile & Proceed': 'حفظ الملف الشخصي والمتابعة'
}

for k, v in replacements.items():
    content = content.replace(k, v)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

logger.info('upload_cv_v3.html translated successfully.')

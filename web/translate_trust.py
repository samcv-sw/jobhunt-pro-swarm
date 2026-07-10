
file_path = r'C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\trust.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'Trust & Security': 'الثقة والأمان',
    'Enterprise-Grade Security': 'أمان بمستوى الشركات',
    'Your data is encrypted and protected.': 'بياناتك مشفرة ومحمية.',
    '256-bit Encryption': 'تشفير 256-بت',
    'Data Privacy': 'خصوصية البيانات',
    'Strict No-Spam Policy': 'سياسة صارمة ضد البريد المزعج'
}

for k, v in replacements.items():
    content = content.replace(k, v)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

logger.info('trust.html translated successfully.')

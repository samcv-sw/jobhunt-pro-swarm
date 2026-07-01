import sys

file_path = r'C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\faq.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'Frequently Asked Questions': 'الأسئلة الشائعة',
    'How does JobHunt Pro work?': 'كيف يعمل JobHunt Pro؟',
    'Is there a guarantee?': 'هل يوجد ضمان؟',
    'How many jobs do you apply to?': 'كم عدد الوظائف التي يتم التقديم لها؟'
}

for k, v in replacements.items():
    content = content.replace(k, v)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('faq.html translated successfully.')

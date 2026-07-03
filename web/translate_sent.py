
file_path = r'C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\sent_emails.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    '>Total Sent<': '>إجمالي المرسل<',
    '>Delivered<': '>تم التسليم<',
    '>Opened<': '>تم الفتح<',
    '>Bounced<': '>مرفوض<',
    '>All Status<': '>كل الحالات<',
    '>To<': '>إلى<',
    '>Company<': '>الشركة<',
    '>Status<': '>الحالة<',
    '>Date<': '>التاريخ<',
    'No emails sent yet.': 'لم يتم إرسال أي رسائل بعد.'
}

for k, v in replacements.items():
    content = content.replace(k, v)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('sent_emails.html translated successfully.')

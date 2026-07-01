import sys

file_path = r'C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\wallet.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'Wallet & Credits': 'المحفظة والرصيد',
    'Manage your balance, buy credits, and view transaction history.': 'إدارة رصيدك، شراء رصيد إضافي، وعرض سجل المعاملات.',
    'Current Balance': 'الرصيد الحالي',
    'Total Credits': 'إجمالي الرصيد',
    'Available for AI campaigns': 'متاح لحملات الذكاء الاصطناعي',
    'Add Funds': 'إضافة رصيد',
    'Transaction History': 'سجل المعاملات',
    'Date': 'التاريخ',
    'Type': 'النوع',
    'Amount': 'المبلغ',
    'Description': 'الوصف',
    'No transactions found.': 'لا توجد معاملات.',
    'Credit Added': 'تم إضافة رصيد',
    'Campaign Cost': 'تكلفة الحملة'
}

for k, v in replacements.items():
    content = content.replace(k, v)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('wallet.html translated successfully.')

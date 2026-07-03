
file_path = r'C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\reset_password.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'Reset Password': 'استعادة كلمة المرور',
    'Set a new password for your JobHunt Pro account.': 'قم بتعيين كلمة مرور جديدة لحسابك.',
    'Create New Password': 'إنشاء كلمة مرور جديدة',
    'Enter your new password below.': 'أدخل كلمة المرور الجديدة أدناه.',
    '>New Password<': '>كلمة المرور الجديدة<',
    '>Confirm Password<': '>تأكيد كلمة المرور<',
    'Update Password': 'تحديث كلمة المرور',
    'Remember your password?': 'هل تتذكر كلمة المرور؟',
    '>Login<': '>دخول<',
    'Min. 8 characters': '8 أحرف على الأقل'
}

for k, v in replacements.items():
    content = content.replace(k, v)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('reset_password.html translated successfully.')

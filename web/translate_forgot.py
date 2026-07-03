
file_path = r'C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\forgot_password.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'Forgot Password': 'نسيت كلمة المرور',
    'Reset your JobHunt Pro password.': 'استعادة كلمة مرور حسابك.',
    "No worries! Enter your email and we'll send you a reset link.": "لا تقلق! أدخل بريدك الإلكتروني وسنرسل لك رابط الاستعادة.",
    '>Email Address<': '>البريد الإلكتروني<',
    'Send Reset Link': 'إرسال رابط الاستعادة',
    'Remember your password?': 'هل تتذكر كلمة المرور؟',
    '>Login<': '>دخول<',
    'Enter your account email': 'أدخل بريد حسابك'
}

for k, v in replacements.items():
    content = content.replace(k, v)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('forgot_password.html translated successfully.')

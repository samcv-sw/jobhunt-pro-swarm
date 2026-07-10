import os
import re
import glob

TARGET_DIR = r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"

files_to_process = []
files_to_process.extend(glob.glob(os.path.join(TARGET_DIR, "admin*.html")))
for f in glob.glob(os.path.join(TARGET_DIR, "login*.html")):
    if not f.endswith("login.html"):
        files_to_process.append(f)
files_to_process.extend(glob.glob(os.path.join(TARGET_DIR, "register*.html")))
files_to_process.extend(glob.glob(os.path.join(TARGET_DIR, "forgot_password.html")))
files_to_process.extend(glob.glob(os.path.join(TARGET_DIR, "reset_password.html")))
files_to_process.extend(glob.glob(os.path.join(TARGET_DIR, "email_test.html")))
files_to_process.extend(glob.glob(os.path.join(TARGET_DIR, "send_email.html")))
files_to_process.extend(glob.glob(os.path.join(TARGET_DIR, "checkout*.html")))

replacements = {
    "Admin Panel": "لوحة الإدارة",
    "JobHunt Pro — Full Control": "جوب هانت برو — تحكم كامل",
    "My Dashboard": "لوحة التحكم",
    ">Users<": ">المستخدمين<",
    ">Campaigns<": ">الحملات<",
    ">Emails<": ">الرسائل<",
    ">Sent<": ">المرسلة<",
    ">Revenue<": ">الأرباح<",
    ">Wallets<": ">المحافظ<",
    "Crypto Payments": "مدفوعات الكريبتو",
    "Crypto Received": "الكريبتو المستلم",
    "Admin Actions": "إجراءات الإدارة",
    "Add Credits to User": "إضافة رصيد للمستخدم",
    "Manually credit any user's wallet": "إضافة رصيد يدوياً لأي مستخدم",
    "Amount $": "المبلغ $",
    "Add Credits": "إضافة رصيد",
    "Generate Redeem Codes": "إنشاء أكواد شحن",
    "Codes appear in the table below": "تظهر الأكواد في الجدول أدناه",
    "Value $": "القيمة $",
    ">Count<": ">العدد<",
    "Generate Codes": "إنشاء أكواد",
    "Welcome Back": "أهلاً وسهلاً بيك",
    "Login to manage your AI job campaigns": "سجل دخولك لتتحكم بحملاتك",
    "Email Address": "البريد الإلكتروني",
    ">Password<": ">كلمة المرور<",
    "Remember me": "تذكرني",
    "Forgot password?": "نسيت كلمة المرور؟",
    "Login to Dashboard": "دخول للوحة التحكم",
    "New to JobHunt Pro?": "جديد عنا؟",
    "Create free account": "أنشئ حساب مجاني",
    "No worries — enter your email and we'll send you a reset link in seconds.": "ولا يهمك — دخل بريدك ورح نبعتلك رابط استعادة بثواني.",
    "Your password reset link is ready:": "رابط استعادة كلمة المرور جاهز:",
    "Reset Password Now": "استعادة كلمة المرور الآن",
    "How it works": "كيف بتشتغل",
    "Check your inbox for the reset link": "شيك صندوق الوارد للرابط",
    "Click the link and set your new password": "اضغط عالرابط وحط كلمة مرور جديدة",
    "Back to Login": "رجوع للدخول",
    "Create new account": "إنشاء حساب جديد",
    "Create your JobHunt Pro account.": "أنشئ حسابك في جوب هانت برو.",
    "What You Get": "شو بتحصل",
    "200 AI Agents 24/7": "200 وكيل ذكاء اصطناعي 24/7",
    "Hundreds of AI agents work around the clock": "مئات الوكلاء شغالين على مدار الساعة",
    "Unique Cover Letters": "رسائل تغطية مميزة",
    "Each application gets a personalized AI-written cover letter": "كل تقديم إله رسالة تغطية مخصصة ومكتوبة بالذكاء الاصطناعي",
    "50+ Countries": "أكثر من 50 دولة",
    "Search across Lebanon, UAE, Saudi, Qatar, Kuwait, remote & more": "بحث في لبنان، الإمارات، السعودية، قطر، الكويت، عن بعد وغيرها",
    "30-Day Money Back": "استرجاع فلوسك خلال 30 يوم",
    "No interviews? Full refund. Zero risk guarantee": "ما في مقابلات؟ بنرجعلك فلوسك. ضمان بدون مخاطر",
    "256-Bit Encryption": "تشفير 256-بت",
    "Your CV and data are locked down": "سيرتك الذاتية وبياناتك محمية",
    "Pay with BTC, ETH, USDT": "ادفع بـ BTC, ETH, USDT",
    "Full Name": "الاسم الكامل",
    "Phone (optional)": "رقم الهاتف (اختياري)",
    "margin-left": "margin-inline-start",
    "margin-right": "margin-inline-end",
    "padding-left": "padding-inline-start",
    "padding-right": "padding-inline-end"
}

for filepath in set(files_to_process):
    if not os.path.exists(filepath): continue
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Apply RTL logic
    if "<html" in content and "dir=\"rtl\"" not in content:
        content = re.sub(r"<html([^>]*)>", r'<html\1 lang="ar" dir="rtl">', content)
    
    # Text replacements
    for eng, ar in replacements.items():
        content = content.replace(eng, ar)
        
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
        
logger.debug(f"Processed {len(set(files_to_process))} files.")

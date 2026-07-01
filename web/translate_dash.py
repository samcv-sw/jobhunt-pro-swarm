import sys

file_path = r'C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\dashboard_v3.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'Welcome back,': 'أهلاً بعودتك،',
    'AI is working in the background. Your job hunt is on autopilot.': 'الذكاء الاصطناعي يعمل في الخلفية. رحلة بحثك عن وظيفة على نظام الطيار الآلي.',
    'Ready for Deployment': 'جاهز للانطلاق',
    'Total Balance': 'الرصيد الإجمالي',
    'Pending Analysis': 'قيد التحليل',
    'Active Campaigns': 'الحملات النشطة',
    'Wallet': 'المحفظة',
    'Credits Available': 'الرصيد المتاح',
    'Total Sent': 'الإرساليات',
    'Sent Today': 'تم الإرسال اليوم',
    'Global Inbox Placement': 'معدل وصول البريد',
    'View All Analytics': 'عرض التحليلات',
    'Pipeline Overview': 'نظرة على مسار العمل',
    'Discovered': 'تم الاستكشاف',
    'Applied': 'تم التقديم',
    'Followed Up': 'تمت المتابعة',
    'Interview': 'المقابلات',
    'Offer': 'العروض',
    'No Activity Yet': 'لا يوجد نشاط بعد',
    'Start a campaign to see pipeline data.': 'ابدأ حملة لرؤية بيانات المسار.',
    'Recent Dispatches': 'أحدث الإرساليات',
    'No Dispatches Yet': 'لا توجد إرساليات بعد',
    '''Your AI agents haven't sent any applications yet.''': 'وكلاؤك لم يرسلوا أي طلبات تقديم بعد.',
    'Standard delivery queue': 'طابور الإرسال العادي',
    'Applications sent over the last 7 days': 'طلبات التقديم خلال الـ 7 أيام الماضية'
}

for k, v in replacements.items():
    content = content.replace(k, v)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('dashboard_v3.html translated successfully.')

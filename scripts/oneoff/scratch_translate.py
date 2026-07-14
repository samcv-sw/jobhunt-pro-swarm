"""
scripts/oneoff/scratch_translate.py
JobHunt Pro - Batch Translation Utility
"""
import logging
import os
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

replacements: Dict[str, List[Tuple[str, str]]] = {
    'web/templates/admin.html': [
        ('Manual Emails</div>', 'رسائل يدوية</div>'),
        ('Manual Revenue</div>', 'الأرباح اليدوية</div>'),
        ('Received</div>', 'مستلم</div>'),
        ('تظهر الأكواد في الجدول أدناه — click to copy and share with users', 'تظهر الأكواد في الجدول أدناه — انقر للنسخ والمشاركة مع المستخدمين'),
        ('placeholder="Count"', 'placeholder="العدد"'),
        ('Sale (counts as revenue)', 'بيع (يُحسب كإيرادات)'),
        ('🆓 Admin Free (no revenue)', '🆓 مجاني للإدارة (بدون إيرادات)'),
        ('🆓 Admin Free Credit', '🆓 رصيد مجاني للإدارة'),
        ('Add free credits to your own wallet (not counted in revenue)', 'أضف رصيدًا مجانيًا إلى محفظتك الخاصة (لا يُحسب ضمن الإيرادات)'),
        ('🆓 Generate Admin Free Code', '🆓 إنشاء كود مجاني للإدارة'),
        ('Use at /wallet &#x2192; Redeem Code. This credit will NOT appear in profit/sales reports.', 'استخدم في /wallet &#x2192; استرداد الكود. لن يظهر هذا الرصيد في تقارير الأرباح/المبيعات.'),
        ('<h3> Give Free Campaign</h3>', '<h3> حملة مجانية</h3>'),
        ('Create a campaign for a user without charging their wallet', 'إنشاء حملة لمستخدم دون خصم من محفظته'),
        ('Give Free Campaign</button>', 'منح حملة مجانية</button>'),
        ('Send Manual Email', 'إرسال رسالة يدوية'),
        ('$0.10/email', '0.10$/رسالة'),
        ('Type any email address, subject & body — send manually via Brevo', 'اكتب أي بريد إلكتروني، موضوع، ومحتوى — للإرسال يدويًا عبر Brevo'),
        ('placeholder="Email Subject"', 'placeholder="موضوع الرسالة"'),
        ('placeholder="Email body (HTML or plain text)..."', 'placeholder="محتوى الرسالة (HTML أو نص عادي)..."'),
        ('Send Email ($0.10)', 'إرسال رسالة (0.10$)'),
        ('Flash Sale Manager', 'إدارة مبيعات الفلاش'),
        ('Create limited-time discounts to boost sales (shown as countdown timers to users)', 'إنشاء خصومات لفترة محدودة لزيادة المبيعات (تظهر كمؤقتات عد تنازلي للمستخدمين)'),
        ('placeholder="Sale title (e.g. Weekend Blast)" value="Flash Sale"', 'placeholder="عنوان التخفيض (مثل: عرض نهاية الأسبوع)" value="تخفيض فلاش"'),
        ('placeholder="Discount %"', 'placeholder="نسبة الخصم %"'),
        ('placeholder="Hours"', 'placeholder="ساعات"'),
        ('Start Flash Sale', 'بدء التخفيض'),
        ('Flash Sales (', 'مبيعات الفلاش ('),
        ('<th>ID</th><th>Title</th><th>Discount</th><th>Status</th><th>Ends</th><th>Action</th>', '<th>المعرف</th><th>العنوان</th><th>الخصم</th><th>الحالة</th><th>ينتهي</th><th>إجراء</th>'),
        ('% OFF', '% خصم'),
        ('&#x1F7E2; Active', '&#x1F7E2; نشط'),
        ('&#x1F534; Expired', '&#x1F534; منتهي'),
        ('&#x26AB; Ended', '&#x26AB; انتهى'),
        ('>End<', '>إنهاء<'),
        ('Redeem Codes (', 'أكواد الاسترداد ('),
        ('<th>Code</th><th>Value</th><th>Type</th><th>Status</th><th>Used By</th><th>Created</th>', '<th>الكود</th><th>القيمة</th><th>النوع</th><th>الحالة</th><th>استخدم بواسطة</th><th>تاريخ الإنشاء</th>'),
        ('> Copy<', '> نسخ<'),
        ('Copied!', 'تم النسخ!'),
        ('color:#fff;">🆓 Free', 'color:#fff;">🆓 مجاني'),
        ('badge-blue"> Sale', 'badge-blue"> بيع'),
        ('badge-gray">Used', 'badge-gray">مُستخدم'),
        ('badge-green">Available', 'badge-green">متاح'),
        ('No codes yet. Generate some above.', 'لا توجد أكواد بعد. قم بإنشاء البعض أعلاه.'),
        ('Users (', 'المستخدمون ('),
        ('<th>Email</th><th>Name</th><th>Type</th><th>Balance</th><th>Spent</th><th>Status</th><th>Joined</th><th>Actions</th>', '<th>البريد الإلكتروني</th><th>الاسم</th><th>النوع</th><th>الرصيد</th><th>المنفق</th><th>الحالة</th><th>انضم في</th><th>إجراءات</th>'),
        ('badge-green">Active', 'badge-green">نشط'),
        ('badge-red">Disabled', 'badge-red">معطل'),
        ('{% if u.is_active %}Disable{% else %}Enable{% endif %}', '{% if u.is_active %}تعطيل{% else %}تفعيل{% endif %}'),
        ('Recent Campaigns (', 'الحملات الأخيرة ('),
        ('<th>ID</th><th>User</th><th>Status</th><th>Companies</th><th>المرسلة</th><th>Date</th>', '<th>المعرف</th><th>المستخدم</th><th>الحالة</th><th>الشركات</th><th>المرسلة</th><th>التاريخ</th>'),
        ('No campaigns yet.', 'لا توجد حملات بعد.'),
        ('Recent Manual Emails (', 'الرسائل اليدوية الأخيرة ('),
        ('<th>To</th><th>Subject</th><th>Price</th><th>Status</th><th>Date</th>', '<th>إلى</th><th>الموضوع</th><th>السعر</th><th>الحالة</th><th>التاريخ</th>'),
        ('badge-red">Failed', 'badge-red">فشل'),
        ('Recent مدفوعات الكريبتو', 'مدفوعات الكريبتو الأخيرة'),
        ('<th>Payment ID</th><th>Order ID</th><th>Currency</th><th>Amount</th><th>TX Hash</th><th>Customer</th><th>Date</th>', '<th>معرف الدفع</th><th>معرف الطلب</th><th>العملة</th><th>المبلغ</th><th>تجزئة التحويل</th><th>العميل</th><th>التاريخ</th>'),
        ('Recent Orders (', 'الطلبات الأخيرة ('),
        ('<th>Order ID</th><th>User</th><th>Type</th><th>Amount</th><th>Status</th><th>Date</th>', '<th>معرف الطلب</th><th>المستخدم</th><th>النوع</th><th>المبلغ</th><th>الحالة</th><th>التاريخ</th>'),
        ('No orders yet.', 'لا توجد طلبات بعد.'),
        ('<h3> إضافة رصيد للمستخدم</h3>', '<h3> إضافة رصيد للمستخدم</h3>'),
        ('إضافة رصيد يدوياً لأي مستخدم', 'إضافة رصيد يدوياً لأي مستخدم')
    ],
    'web/templates/admin_analytics.html': [
        ('Admin Analytics — JobHunt Pro', 'تحليلات الإدارة — جوب هانت برو'),
        ('📊 Admin Analytics', '📊 تحليلات الإدارة'),
        ('Real-time revenue, user, and campaign metrics', 'مقاييس الأرباح، المستخدمين، والحملات في الوقت الفعلي'),
        ('Total Revenue', 'إجمالي الأرباح'),
        ('% this month', '% هذا الشهر'),
        ('Total Users', 'إجمالي المستخدمين'),
        ('new today', 'مستخدم جديد اليوم'),
        ('Campaigns Running', 'حملات قيد التشغيل'),
        ('% active rate', '% نسبة النشاط'),
        ('Emails Sent Today', 'رسائل مُرسلة اليوم'),
        ('deliverability', 'معدل التوصيل'),
        ('📈 Monthly Revenue (Last 12 Months)', '📈 الأرباح الشهرية (آخر 12 شهراً)'),
        ('💎 Revenue by Plan Tier', '💎 الأرباح حسب مستوى الخطة'),
        (' sales &middot;', ' مبيعات &middot;'),
        (' sales ·', ' مبيعات ·'),
        ('🌍 Top Markets', '🌍 أبرز الأسواق'),
        (' users &middot;', ' مستخدمين &middot;'),
        (' users ·', ' مستخدمين ·'),
        ('🧪 A/B Subject Line Testing', '🧪 اختبار أ/ب لعناوين الرسائل'),
        ('Test different email subjects to maximize open rates', 'اختبر عناوين مختلفة للرسائل لزيادة معدل الفتح'),
        ('Subject A', 'العنوان أ'),
        ('open rate &middot;', 'معدل الفتح &middot;'),
        ('open rate ·', 'معدل الفتح ·'),
        (' sent', ' مرسلة'),
        ('Subject B', 'العنوان ب')
    ],
    'web/templates/admin_user.html': [
        ('User Detail — Admin', 'تفاصيل المستخدم — الإدارة'),
        ('User: {{ user.email }}', 'مستخدم: {{ user.email }}'),
        ('Back to Admin', 'العودة للإدارة'),
        ('<h2>User Info</h2>', '<h2>معلومات المستخدم</h2>'),
        ('<label>Name</label>', '<label>الاسم</label>'),
        ('<label>Email</label>', '<label>البريد الإلكتروني</label>'),
        ('<label>Type</label>', '<label>النوع</label>'),
    ],
    'web/templates/base.html': [
        ('JobHunt Pro - Enterprise AI Job Application Automator', 'جوب هانت برو - أداة أتمتة تقديم الوظائف بالذكاء الاصطناعي'),
        ('UPLINK: SECURE', 'الاتصال: آمن'),
        ('UPLINK SEVERED: RECONNECTING...', 'انقطع الاتصال: جاري إعادة الاتصال...')
    ]
}

def main() -> None:
    """Read target files, apply translations via search-and-replace, and write back."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        for filepath, reps in replacements.items():
            full_path = os.path.join(base_dir, filepath)
            if not os.path.exists(full_path):
                logger.warning(f"File not found: {full_path}")
                continue
                
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for old, new in reps:
                content = content.replace(old, new)
                
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Processed and translated: {full_path}")
    except Exception as e:
        logger.error(f"Failed during scratch translation run: {e}")
        raise

if __name__ == "__main__":
    main()

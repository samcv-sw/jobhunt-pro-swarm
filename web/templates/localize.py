import os
import re

d = r'C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates'
files = [
    'dashboard_v2.html', 'dashboard_v3.html',
    'war_room.html', 'battle_station.html',
    'resume_tailor.html', 'kanban_board.html', 'stats.html',
    'wallet.html', 'my_purchases.html', 'new_campaign_v2.html',
    'upload_cv_v2.html', 'upload_cv_v3.html',
    'roast.html', 'interview_prep.html'
]
trans = {
    r'>\s*Submit\s*<': '>إرسال<',
    r'>\s*Save\s*<': '>حفظ<',
    r'>\s*Cancel\s*<': '>إلغاء<',
    r'>\s*Delete\s*<': '>حذف<',
    r'>\s*Edit\s*<': '>تعديل<',
    r'>\s*Update\s*<': '>تحديث<',
    r'>\s*Close\s*<': '>إغلاق<',
    r'>\s*Upload\s*<': '>رفع<',
    r'>\s*Download\s*<': '>تنزيل<',
    r'>\s*Search\s*<': '>بحث<',
    r'>\s*Add\s*<': '>إضافة<',
    r'>\s*Create\s*<': '>إنشاء<',
    r'>\s*Next\s*<': '>التالي<',
    r'>\s*Previous\s*<': '>السابق<',
    r'>\s*Back\s*<': '>رجوع<',
}
for f in files:
    p = os.path.join(d, f)
    if not os.path.exists(p): continue
    with open(p, encoding='utf-8') as file:
        c = file.read()

    c = re.sub(r'<input([^>]*?)(?<!dir="auto")([^>]*?)>', lambda m: f'<input{m.group(1)}{m.group(2)} dir="auto">' if 'dir=' not in m.group(0) else m.group(0), c)
    c = re.sub(r'<textarea([^>]*?)(?<!dir="auto")([^>]*?)>', lambda m: f'<textarea{m.group(1)}{m.group(2)} dir="auto">' if 'dir=' not in m.group(0) else m.group(0), c)

    # Flip directional icons
    c = re.sub(r'(<i[^>]*class="[^"]*(?:right|left|forward|backward|chevron)[^"]*"[^>]*>)(?!.*?style="transform)', r'\1<style>transform: scaleX(var(--text-x-direction, -1));</style>', c)

    for k, v in trans.items():
        c = re.sub(k, v, c, flags=re.IGNORECASE)

    with open(p, 'w', encoding='utf-8') as file:
        file.write(c)
    logger.debug(f"Processed {f}")

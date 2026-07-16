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
    def replace_icon(match):
        tag = match.group(1)
        style_match = re.search(r'style\s*=\s*"([^"]*)"', tag)
        if style_match:
            style_val = style_match.group(1)
            if 'transform' not in style_val:
                new_style_val = style_val.rstrip('; ') + '; transform: scaleX(var(--text-x-direction, 1));'
                return tag.replace(style_match.group(0), f'style="{new_style_val}"')
            return tag
        else:
            if tag.endswith('/>'):
                return tag[:-2] + ' style="transform: scaleX(var(--text-x-direction, 1));"/>'
            elif tag.endswith('>'):
                return tag[:-1] + ' style="transform: scaleX(var(--text-x-direction, 1));">'
            return tag

    c = re.sub(r'(<i[^>]*class="[^"]*(?:right|left|forward|backward|chevron)[^"]*"[^>]*>)', replace_icon, c)

    for k, v in trans.items():
        c = re.sub(k, v, c, flags=re.IGNORECASE)

    with open(p, 'w', encoding='utf-8') as file:
        file.write(c)
    print(f"Processed {f}")

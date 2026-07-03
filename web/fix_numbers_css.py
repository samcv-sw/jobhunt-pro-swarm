
css_rule = """
/* Fix RTL Numbers */
[dir="rtl"] .num, 
[dir="rtl"] .stat-num,
[dir="rtl"] .stat-item .num,
[dir="rtl"] .price,
[dir="rtl"] .currency {
    direction: ltr;
    display: inline-block;
    unicode-bidi: isolate;
}
"""

filepath = r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\static\css\style.css"
with open(filepath, "a", encoding="utf-8") as f:
    f.write(css_rule)
print("Appended number fix to style.css")

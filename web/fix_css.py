import os

css_rule = """
/* FIX: Arabic Shaping */
[dir="rtl"] *, :lang(ar) *, :lang(ar) {
    letter-spacing: normal !important;
}
"""

css_dir = r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\static\css"
files = ["landing-v4.css", "auth-v2.css", "dashboard-v4.css", "style.css"]

for filename in files:
    filepath = os.path.join(css_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(css_rule)
        print(f"Appended to {filename}")

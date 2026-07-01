import os

css_rule = """
/* Fix Hero Spacing */
.hero {
    padding-top: 140px !important; 
}
"""

filepath = r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\static\css\landing-v4.css"
with open(filepath, "a", encoding="utf-8") as f:
    f.write(css_rule)
print("Appended hero fix to landing-v4.css")

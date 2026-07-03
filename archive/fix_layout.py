import re

with open("web/templates/pricing_v3.html", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("inset-inline-start: -100%", "left: -100%; inset-inline-start: -100%")
content = content.replace("inset-inline-start: 150%", "left: 150%; inset-inline-start: 150%")
content = content.replace("inset-inline-start: 50%", "left: 50%; inset-inline-start: 50%")
content = content.replace("inset-inline-start: 0", "left: 0; inset-inline-start: 0")
content = content.replace("inset-inline-end: 0", "right: 0; inset-inline-end: 0")
content = content.replace("inset-inline-end: 10px", "right: 10px; inset-inline-end: 10px")
content = content.replace("inset-inline-end: 20px", "right: 20px; inset-inline-end: 20px")
content = content.replace("text-align: start", "text-align: left; text-align: start")

with open("web/templates/pricing_v3.html", "w", encoding="utf-8") as f:
    f.write(content)

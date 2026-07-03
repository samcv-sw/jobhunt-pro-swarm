import re

with open("web/templates/pricing_v3.html", "r", encoding="utf-8") as f:
    content = f.read()

# Fix conflicting position properties
content = content.replace("left: -100%; inset-inline-start: -100%;", "inset-inline-start: -100%;")
content = content.replace("left: 150%; inset-inline-start: 150%;", "inset-inline-start: 150%;")
content = content.replace("left: 0; inset-inline-start: 0; right: 0; inset-inline-end: 0;", "inset-inline-start: 0; inset-inline-end: 0;")
content = content.replace("left: 50%; inset-inline-start: 50%;", "inset-inline-start: 50%;")

# Ensure text-x-direction is defined if not inherited
if "--text-x-direction" not in content[:500]:
    content = content.replace("/* ── Animations ── */", ":root {\n  --text-x-direction: 1;\n}\n[dir=\"rtl\"] {\n  --text-x-direction: -1;\n}\n\n/* ── Animations ── */")

# Fix overlapping grid issue: repeat(auto-fit, minmax(260px, 1fr)) is safer than repeat(4, 1fr) for preventing overflow
content = content.replace("grid-template-columns: repeat(4, 1fr);", "grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));")

with open("web/templates/pricing_v3.html", "w", encoding="utf-8") as f:
    f.write(content)

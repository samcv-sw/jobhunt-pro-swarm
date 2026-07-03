with open("web/templates/pricing_v3.html", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('data-tier="{{ tier.id }}"', 'data-tier="{{ tier.get(\'tier\', \'\') }}"')

with open("web/templates/pricing_v3.html", "w", encoding="utf-8") as f:
    f.write(content)

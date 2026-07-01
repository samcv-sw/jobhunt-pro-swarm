import re

with open("app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "templates.TemplateResponse(" in line:
        # We know it looks like: return templates.TemplateResponse("foo.html", {
        # We want to change to: return templates.TemplateResponse(request=request, name="foo.html", context={
        match = re.search(r'templates\.TemplateResponse\(\s*(["\'][^"\']+["\'])\s*,\s*(\{.*)', line)
        if match:
            name_val = match.group(1)
            rest = match.group(2)
            # Reconstruct the line
            prefix = line[:match.start()]
            new_line = f"{prefix}templates.TemplateResponse(request=request, name={name_val}, context={rest}\n"
            new_lines.append(new_line)
            continue
    new_lines.append(line)

with open("app.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)
print("Done")

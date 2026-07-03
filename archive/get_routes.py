import re
with open('web/app_v2.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
routes = []
for line in lines:
    m = re.search(r'@app\.(?:get|post|api_route)\([\'"]([^\'"]+)[\'"]', line)
    if m:
        route = m.group(1)
        if '/api/' not in route and 'HTMLResponse' in line:
            routes.append(route)
print('\n'.join(sorted(set(routes))))

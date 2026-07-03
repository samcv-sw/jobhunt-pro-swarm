import re

APP_FILE = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\app_v2.py"

def audit():
    with open(APP_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    # Find all route definitions
    # E.g., @app.get("/route") or @app.post("/route")
    route_pattern = r'(@app\.(?:get|post|route|put|delete)\("([^"]+)"[^)]*\)\s*def\s+([a-zA-Z0-9_]+)\([^)]*\):)'
    
    matches = re.finditer(route_pattern, content)
    
    print(f"{'Path':<50} | {'Template':<30} | {'Wrapping Mode':<30}")
    print("-" * 116)
    
    for m in matches:
        full_def, path, func_name = m.groups()
        # Find the function body (roughly scan up to the next route or def)
        start_idx = m.end()
        # Find next @app. or def at the start of line (indent 0)
        next_match = re.search(r'\n@app\.|\ndef\s+', content[start_idx:])
        end_idx = start_idx + next_match.start() if next_match else len(content)
        func_body = content[start_idx:end_idx]
        
        # Search for template rendering and returning in this function
        # E.g., TemplateResponse(..., "name.html", ...)
        # or render_template("name.html", ...)
        template_matches = re.findall(r'["\']([a-zA-Z0-9_-]+\.html)["\']', func_body)
        
        # Check if wrapped
        is_dashboard_wrapped = "_build_dashboard_shell" in func_body
        is_public_wrapped = "_public_shell" in func_body
        
        mode = "Direct TemplateResponse"
        if is_dashboard_wrapped:
            mode = "Wrapped in Dashboard Shell"
        elif is_public_wrapped:
            mode = "Wrapped in Public Shell"
            
        templates_used = list(set(template_matches))
        # Filter out partials
        templates_used = [t for t in templates_used if not t.startswith('_')]
        
        if templates_used:
            for t in templates_used:
                print(f"{path:<50} | {t:<30} | {mode:<30}")

if __name__ == "__main__":
    audit()

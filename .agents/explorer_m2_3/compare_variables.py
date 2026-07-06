import re

OUTPUT_FILE = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m2_3\audit_output.txt"

def parse_audit():
    templates = {}
    render_calls = []
    
    section = None
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("--- Extracting template undeclared variables ---"):
                section = "templates"
                continue
            elif line.startswith("--- Extracting backend render calls ---"):
                section = "calls"
                continue
            elif line.startswith("--- render_template Calls ---"):
                section = "render_calls"
                continue
            elif line.startswith("--- _build_dashboard_shell Calls ---"):
                section = "dash_calls"
                continue
            elif line.startswith("--- _public_shell Calls ---"):
                section = "public_calls"
                continue
            
            if section == "templates":
                # e.g., _base_tailwind.html: ['description', 'lang', 'request', 'title']
                m = re.match(r"^([^:]+):\s*(.*)$", line)
                if m:
                    tmpl_name = m.group(1).strip()
                    vars_str = m.group(2).strip()
                    if vars_str.startswith("ERROR"):
                        templates[tmpl_name] = vars_str
                    else:
                        # eval the list string safely
                        try:
                            templates[tmpl_name] = eval(vars_str)
                        except Exception:
                            templates[tmpl_name] = []
            elif section == "render_calls":
                # e.g., Line 189: render_template('_public_shell.html', content=content, ...)
                m = re.match(r"^Line (\d+):\s*render_template\(([^,]+),\s*(.*)\)$", line)
                if m:
                    line_num = int(m.group(1))
                    tmpl_name = m.group(2).strip().strip("'\"")
                    kwargs_str = m.group(3).strip()
                    
                    # Parse kwargs
                    kwargs = {}
                    # We can split by comma, but be careful with nested commas. Let's do a simple split or regex
                    # Since it is a representation, let's parse keys from key=val
                    pairs = re.findall(r"([a-zA-Z0-9_]+)=([^,]+)", kwargs_str)
                    for k, v in pairs:
                        kwargs[k] = v.strip()
                    
                    render_calls.append({
                        "line": line_num,
                        "template": tmpl_name,
                        "kwargs": kwargs
                    })
    return templates, render_calls

def main():
    templates, render_calls = parse_audit()
    
    print("=== TEMPLATE VARIABLE MISMATCH AUDIT ===")
    for call in render_calls:
        tmpl = call["template"]
        line = call["line"]
        passed_vars = set(call["kwargs"].keys())
        
        # Add implicitly injected variables by render_template function:
        # VERSION, lang, dir, _
        passed_vars.update(["VERSION", "lang", "dir", "_"])
        
        # Check standard template
        expected_vars = templates.get(tmpl)
        
        # Also look in "en/" prefix if applicable, or check if both exists
        if expected_vars is None:
            # Maybe the template is just templates/something.html
            # Let's try matching filename
            for k in templates.keys():
                if k.endswith(tmpl):
                    expected_vars = templates[k]
                    break
        
        if expected_vars is None:
            print(f"Line {line}: Template '{tmpl}' not found in templates directory.")
            continue
            
        if isinstance(expected_vars, str) and expected_vars.startswith("ERROR"):
            print(f"Line {line}: Template '{tmpl}' failed to compile: {expected_vars}")
            continue
            
        expected_set = set(expected_vars)
        
        # Variables that are expected but NOT passed (missing context)
        missing = expected_set - passed_vars
        # Remove request if it's not strictly required or if it's optional, but wait, request is in expected
        
        # Variables passed but NOT expected (unused context)
        unused = passed_vars - expected_set - {"VERSION", "lang", "dir", "_", "request"} # request is optional
        
        if missing or unused:
            print(f"\nLine {line}: render_template('{tmpl}')")
            if missing:
                print(f"  [-] MISSING variables (in Jinja but NOT in backend context): {sorted(list(missing))}")
            if unused:
                print(f"  [+] UNUSED variables (passed in backend but NOT used in Jinja): {sorted(list(unused))}")

if __name__ == "__main__":
    main()

import os
import re
import sys

# Reconfigure stdout to use utf-8 if possible to avoid Windows cp1252 encoding issues
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def parse_css_declarations(css_content):
    # Replace comments with spaces to preserve indices/line numbers
    def comment_replacer(match):
        return re.sub(r'[^\r\n]', ' ', match.group(0))
    
    clean_content = re.sub(r'/\*.*?\*/', comment_replacer, css_content, flags=re.DOTALL)
    
    # Track line starts for line number lookup
    line_starts = [0]
    for i, char in enumerate(clean_content):
        if char == '\n':
            line_starts.append(i + 1)
            
    def get_line_no(index):
        for line_no, start in enumerate(line_starts):
            if start > index:
                return line_no
        return len(line_starts)

    # Parse braces to find leaf blocks (blocks containing declarations, not nested rules)
    stack = []
    blocks = []
    for i, char in enumerate(clean_content):
        if char == '{':
            stack.append(i)
        elif char == '}':
            if stack:
                start = stack.pop()
                inner_text = clean_content[start+1:i]
                if '{' not in inner_text:
                    # Find the selector for this block
                    prev_bracket = clean_content.rfind('}', 0, start)
                    if prev_bracket == -1:
                        prev_bracket = clean_content.rfind('{', 0, start)
                    selector_start = prev_bracket + 1 if prev_bracket != -1 else 0
                    selector = clean_content[selector_start:start].strip()
                    blocks.append((start+1, i, inner_text, selector))
                    
    declarations = []
    for start_idx, end_idx, block_text, selector in blocks:
        # Split declarations by ';' while ignoring quotes
        in_quote = None
        current_decl_chars = []
        decl_start_idx = start_idx
        
        for offset, char in enumerate(block_text):
            idx = start_idx + offset
            if char in ('"', "'"):
                if in_quote == char:
                    in_quote = None
                elif in_quote is None:
                    in_quote = char
                current_decl_chars.append(char)
            elif char == ';' and in_quote is None:
                decl_str = ''.join(current_decl_chars).strip()
                if decl_str:
                    declarations.append((decl_start_idx, decl_str, selector))
                current_decl_chars = []
                decl_start_idx = idx + 1
            else:
                current_decl_chars.append(char)
        if current_decl_chars:
            decl_str = ''.join(current_decl_chars).strip()
            if decl_str:
                declarations.append((decl_start_idx, decl_str, selector))
                
    parsed_decls = []
    for idx, decl, selector in declarations:
        if ':' in decl:
            prop, val = decl.split(':', 1)
            prop = prop.strip()
            val = val.strip()
            line_no = get_line_no(idx)
            parsed_decls.append({
                'property': prop,
                'value': val,
                'raw': decl,
                'line_number': line_no,
                'index': idx,
                'selector': selector
            })
    return parsed_decls

def clean_value(val):
    # Strip url(...) and var(...) functions
    val = re.sub(r'url\s*\([^)]*\)', ' ', val, flags=re.IGNORECASE)
    val = re.sub(r'var\s*\([^)]*\)', ' ', val, flags=re.IGNORECASE)
    return val

def check_font_size_violation(val):
    # E.g. "12px", "0.75rem", "80%"
    match = re.match(r'^([\d.]+)\s*(px|rem|em|%|pt|vh|vw|er|ch)?$', val.strip().lower())
    if not match:
        return False
    num = float(match.group(1))
    unit = match.group(2) or 'px'
    
    if unit == 'px':
        return num < 14
    elif unit in ('rem', 'em'):
        return num < 0.875  # 0.875 * 16 = 14px
    elif unit == '%':
        return num < 87.5
    elif unit == 'pt':
        return num < 10.5
    return False

def check_font_shorthand_size_violation(val):
    sizes = re.findall(r'\b([\d.]+)(px|rem|em|%|pt)\b', val.lower())
    for num_str, unit in sizes:
        num = float(num_str)
        if unit == 'px' and num < 14:
            return True
        elif unit in ('rem', 'em') and num < 0.875:
            return True
        elif unit == '%' and num < 87.5:
            return True
        elif unit == 'pt' and num < 10.5:
            return True
    return False

def check_line_height_violation(val):
    # E.g. "1.5", "150%", "24px"
    match = re.match(r'^([\d.]+)\s*(%|px|rem|em)?$', val.strip().lower())
    if not match:
        return False
    num = float(match.group(1))
    unit = match.group(2) or ''
    
    if unit == '':
        return num < 1.6 or num > 2.0
    elif unit == '%':
        return num < 160 or num > 200
    elif unit == 'px':
        return num < 22
    elif unit in ('rem', 'em'):
        return num < 1.6 or num > 2.0
    return False

def check_letter_spacing_violation(val):
    # Letter-spacing should be normal, 0, none, inherit, initial, unset
    val_clean = val.strip().lower().replace('!important', '').strip()
    if val_clean in ('normal', '0', '0px', 'none', 'inherit', 'initial', 'unset'):
        return False
    return True

def run_audit(target_dir):
    css_dir = os.path.join(target_dir, 'web', 'static', 'css')
    
    focus_files = ['style.css', 'index.css', 'tailwind_overrides.css', 'premium-ui.css']
    # Include their -rtl variants too
    focus_files += [f.replace('.css', '-rtl.css') for f in focus_files]
    
    files_to_check = []
    for file in focus_files:
        path = os.path.join(css_dir, file)
        if os.path.exists(path):
            files_to_check.append(path)
            
    report_lines = []
    def rprint(text):
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode('ascii', errors='backslashreplace').decode('ascii'))
        report_lines.append(text)

    rprint(f"Found {len(files_to_check)} specific refactored CSS files to audit in web/static/css:")
    rprint("\n".join([f" - {os.path.basename(f)}" for f in files_to_check]))
    rprint("=" * 80)
    
    results = {}
    
    for filepath in files_to_check:
        filename = os.path.basename(filepath)
        is_rtl_file = filename.endswith('-rtl.css') or 'rtl' in filename.lower()
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            rprint(f"Error reading {filename}: {e}")
            continue
            
        decls = parse_css_declarations(content)
        
        physical_props = []
        typography_violations = []
        has_global_reset = False
        
        # Check global letter-spacing reset
        for d in decls:
            sel = d['selector'].lower()
            prop = d['property'].lower()
            val = d['value'].lower()
            
            if ('[dir="rtl"]' in sel or ':lang(ar)' in sel) and '*' in sel:
                if prop == 'letter-spacing' and 'normal' in val and 'important' in val:
                    has_global_reset = True
                    
        for d in decls:
            prop = d['property'].lower()
            val = d['value'].lower()
            sel = d['selector'].lower()
            
            # --- Physical Properties Check ---
            is_physical = False
            reason = ""
            
            # Property name check
            if not prop.startswith('--'):
                if prop in ('left', 'right'):
                    is_physical = True
                    reason = f"Property '{prop}' is physical layout positioning"
                elif '-left' in prop or '-right' in prop:
                    is_physical = True
                    reason = f"Property '{prop}' is physical (contains -left or -right)"
            
            # Value check
            if not is_physical and prop != 'content' and not prop.startswith('--'):
                val_clean = clean_value(val)
                words = re.findall(r'\b(left|right)\b', val_clean)
                if words:
                    is_physical = True
                    reason = f"Value '{val}' contains physical direction word(s): {', '.join(words)}"
            
            if is_physical:
                physical_props.append({
                    'line': d['line_number'],
                    'selector': d['selector'],
                    'property': d['property'],
                    'value': d['value'],
                    'reason': reason
                })
                
            # --- Arabic / RTL Typography Constraints Check ---
            is_rtl_context = False
            if '[dir="rtl"]' in sel or ':lang(ar)' in sel or '.rtl' in sel or '.arabic' in sel:
                is_rtl_context = True
            elif is_rtl_file and '[dir="ltr"]' not in sel and ':lang(en)' not in sel:
                is_rtl_context = True
                
            if is_rtl_context:
                # Check line-height
                if prop == 'line-height':
                    if check_line_height_violation(val):
                        typography_violations.append({
                            'line': d['line_number'],
                            'selector': d['selector'],
                            'property': prop,
                            'value': d['value'],
                            'constraint': "line-height must be 1.6 to 2.0",
                            'severity': 'MEDIUM'
                        })
                # Check font-size
                elif prop == 'font-size':
                    if check_font_size_violation(val):
                        typography_violations.append({
                            'line': d['line_number'],
                            'selector': d['selector'],
                            'property': prop,
                            'value': d['value'],
                            'constraint': "font-size must be >= 14px",
                            'severity': 'HIGH'
                        })
                # Check font shorthand
                elif prop == 'font':
                    if check_font_shorthand_size_violation(val):
                        typography_violations.append({
                            'line': d['line_number'],
                            'selector': d['selector'],
                            'property': prop,
                            'value': d['value'],
                            'constraint': "font-size in font shorthand must be >= 14px",
                            'severity': 'HIGH'
                        })
                # Check letter-spacing
                elif prop == 'letter-spacing' and not has_global_reset:
                    if check_letter_spacing_violation(val):
                        typography_violations.append({
                            'line': d['line_number'],
                            'selector': d['selector'],
                            'property': prop,
                            'value': d['value'],
                            'constraint': "letter-spacing must be reset to normal/0 for RTL",
                            'severity': 'HIGH'
                        })
                        
        results[filename] = {
            'physical_props': physical_props,
            'typography_violations': typography_violations,
            'has_global_reset': has_global_reset,
            'is_rtl_file': is_rtl_file
        }
        
    # Print report
    total_violations = 0
    total_physical = 0
    
    rprint("\nAUDIT REPORT BY FILE:\n")
    for file, data in results.items():
        rprint(f"File: {file}")
        rprint(f"RTL Specific File: {data['is_rtl_file']}")
        rprint(f"Global RTL letter-spacing reset found: {data['has_global_reset']}")
        
        phys_count = len(data['physical_props'])
        typo_count = len(data['typography_violations'])
        total_violations += typo_count
        total_physical += phys_count
        
        rprint(f" - Physical properties / values: {phys_count}")
        rprint(f" - RTL typography violations: {typo_count}")
        
        if phys_count > 0:
            rprint("   [Physical Property Violations]")
            for p in data['physical_props']:
                rprint(f"     Line {p['line']}: selector `{p['selector']}` -> `{p['property']}: {p['value']}`")
                rprint(f"       Reason: {p['reason']}")
                
        if typo_count > 0:
            rprint("   [RTL Typography Violations]")
            for t in data['typography_violations']:
                rprint(f"     Line {t['line']}: selector `{t['selector']}` -> `{t['property']}: {t['value']}`")
                rprint(f"       Reason: {t['constraint']} (severity: {t['severity']})")
        rprint("-" * 50)
        
    rprint(f"\nSUMMARY:")
    rprint(f"Total Physical Directional Property violations: {total_physical}")
    rprint(f"Total RTL/Arabic Typography violations: {total_violations}")
    
    # Save report to UTF-8 file
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_report.txt")
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write("\n".join(report_lines))
    
    rprint(f"\nSaved report to: audit_report.txt")
    
    if total_physical > 0 or total_violations > 0:
        return 1
    return 0

if __name__ == '__main__':
    target = r'c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi'
    sys.exit(run_audit(target))

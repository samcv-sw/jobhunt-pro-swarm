import os
import re
import sys

# Reconfigure stdout/stderr to use UTF-8 to prevent encoding errors on Windows terminal
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Color output helpers (clean text for file, colors for stdout)
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Files to verify specifically, but we'll scan all CSS files in the dir
TARGET_DIR = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\static\css"
REPORT_PATH = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\challenger_m2_1\challenge_report.txt"

PHYSICAL_PATTERNS = {
    'margin-left': re.compile(r'\bmargin-left\b', re.IGNORECASE),
    'margin-right': re.compile(r'\bmargin-right\b', re.IGNORECASE),
    'padding-left': re.compile(r'\bpadding-left\b', re.IGNORECASE),
    'padding-right': re.compile(r'\bpadding-right\b', re.IGNORECASE),
    'left-property': re.compile(r'\bleft\s*:', re.IGNORECASE),
    'right-property': re.compile(r'\bright\s*:', re.IGNORECASE),
    'border-left': re.compile(r'\bborder-left\b', re.IGNORECASE),
    'border-right': re.compile(r'\bborder-right\b', re.IGNORECASE),
    'border-radius-physical': re.compile(r'\bborder-(top|bottom)-(left|right)-radius\b', re.IGNORECASE),
    'text-align-left': re.compile(r'\btext-align\s*:\s*left\b', re.IGNORECASE),
    'text-align-right': re.compile(r'\btext-align\s*:\s*right\b', re.IGNORECASE),
    'float-left-right': re.compile(r'\bfloat\s*:\s*(left|right)\b', re.IGNORECASE),
    'clear-left-right': re.compile(r'\bclear\s*:\s*(left|right)\b', re.IGNORECASE),
}

SHORTHAND_PATTERN = re.compile(r'\b(margin|padding)\s*:\s*([^;}\n]+)', re.IGNORECASE)

def strip_comments_keep_line_numbers(content):
    def replacer(match):
        s = match.group(0)
        return re.sub(r'[^\n]', ' ', s)
    return re.sub(r'/\*.*?\*/', replacer, content, flags=re.DOTALL)

def check_asymmetric_shorthand(prop, value):
    # Split shorthand values by whitespace, ignoring spaces inside CSS functions like calc() or var()
    parts = []
    current = []
    paren_depth = 0
    for char in value:
        if char == '(':
            paren_depth += 1
            current.append(char)
        elif char == ')':
            paren_depth -= 1
            current.append(char)
        elif char.isspace():
            if paren_depth == 0:
                if current:
                    parts.append(''.join(current).strip())
                    current = []
            else:
                current.append(char)
        else:
            current.append(char)
    if current:
        parts.append(''.join(current).strip())
        
    # Clean empty values
    parts = [p for p in parts if p]
    
    # 4-value shorthand: top right bottom left
    if len(parts) == 4:
        top, right, bottom, left = parts
        if right != left:
            return f"Asymmetric 4-value {prop}: right ({right}) != left ({left})"
    return None

def parse_rules_recursive(content, file_name, parent_context=""):
    rules = []
    i = 0
    n = len(content)
    selector_start = 0
    brace_level = 0
    block_start = 0
    current_selector = ""
    
    line_number = 1
    selector_line = 1
    block_line = 1
    
    while i < n:
        char = content[i]
        if char == '\n':
            line_number += 1
            
        if char == '{':
            if brace_level == 0:
                current_selector = content[selector_start:i].strip()
                block_start = i + 1
                block_line = line_number
                selector_line = max(1, line_number - current_selector.count('\n'))
            brace_level += 1
        elif char == '}':
            brace_level -= 1
            if brace_level == 0:
                block_content = content[block_start:i].strip()
                if current_selector.startswith('@'):
                    rules.extend(parse_rules_recursive(block_content, file_name, current_selector))
                else:
                    full_selector = f"{parent_context} -> {current_selector}" if parent_context else current_selector
                    rules.append((full_selector, block_content, block_line))
                selector_start = i + 1
        i += 1
    return rules

def check_arabic_constraints(selector, block_content, line_start, file_name):
    violations = []
    
    is_rtl_selector = any(x in selector.lower() for x in ['[dir="rtl"]', '[dir=\'rtl\']', '.rtl', ':lang(ar)'])
    is_rtl_file = file_name.lower().endswith('-rtl.css')
    
    if not (is_rtl_selector or is_rtl_file):
        return violations
        
    declarations = [d.strip() for d in block_content.split(';') if d.strip()]
    
    for decl in declarations:
        if ':' not in decl:
            continue
        prop, val = decl.split(':', 1)
        prop = prop.strip().lower()
        val = val.strip().lower()
        
        if prop == 'letter-spacing':
            if not any(ok in val for ok in ['normal', '0', 'initial', 'inherit', 'unset']):
                violations.append({
                    'line': line_start,
                    'type': 'ARABIC_LETTER_SPACING',
                    'detail': f"Violated letter-spacing constraint on RTL selector '{selector}': '{decl}'"
                })
                
        if prop == 'line-height':
            if val not in ['inherit', 'initial', 'unset', 'normal']:
                try:
                    clean_val = re.sub(r'[a-zA-Z%]', '', val).strip()
                    lh_float = float(clean_val)
                    if lh_float < 1.6 or lh_float > 2.0:
                        violations.append({
                            'line': line_start,
                            'type': 'ARABIC_LINE_HEIGHT',
                            'detail': f"Violated line-height (1.6 - 2.0) on RTL selector '{selector}': '{decl}' (parsed as {lh_float})"
                        })
                except ValueError:
                    if 'var(' not in val and 'calc(' not in val:
                        violations.append({
                            'line': line_start,
                            'type': 'ARABIC_LINE_HEIGHT_UNPARSABLE',
                            'detail': f"RTL line-height requires manual review on selector '{selector}': '{decl}'"
                        })
                        
        if prop == 'font-size':
            if val not in ['inherit', 'initial', 'unset']:
                try:
                    px_match = re.search(r'(\d+(?:\.\d+)?)\s*px', val)
                    rem_match = re.search(r'(\d+(?:\.\d+)?)\s*rem', val)
                    em_match = re.search(r'(\d+(?:\.\d+)?)\s*em', val)
                    
                    if px_match:
                        size = float(px_match.group(1))
                        if size < 14:
                            violations.append({
                                'line': line_start,
                                'type': 'ARABIC_FONT_SIZE_PX',
                                'detail': f"Violated font-size constraint (>=14px) on RTL selector '{selector}': '{decl}' (parsed as {size}px)"
                            })
                    elif rem_match:
                        size = float(rem_match.group(1))
                        if size < 0.875:
                            violations.append({
                                'line': line_start,
                                'type': 'ARABIC_FONT_SIZE_REM',
                                'detail': f"Violated font-size constraint (>=14px / >=0.875rem) on RTL selector '{selector}': '{decl}' (parsed as {size}rem)"
                            })
                    elif em_match:
                        size = float(em_match.group(1))
                        if size < 0.875:
                            violations.append({
                                'line': line_start,
                                'type': 'ARABIC_FONT_SIZE_EM',
                                'detail': f"Violated font-size constraint (>=14px / >=0.875em) on RTL selector '{selector}': '{decl}' (parsed as {size}em)"
                            })
                except ValueError:
                    pass
                    
    return violations

def analyze_css_file(filepath):
    file_name = os.path.basename(filepath)
    with open(filepath, 'r', encoding='utf-8') as f:
        original_content = f.read()
        
    clean_content = strip_comments_keep_line_numbers(original_content)
    lines = clean_content.splitlines()
    original_lines = original_content.splitlines()
    
    physical_violations = []
    arabic_violations = []
    
    for idx, line in enumerate(lines):
        line_num = idx + 1
        for key, pattern in PHYSICAL_PATTERNS.items():
            match = pattern.search(line)
            if match:
                if ':' in line:
                    physical_violations.append({
                        'line': line_num,
                        'type': key,
                        'content': original_lines[idx].strip(),
                        'detail': f"Found physical property/value matching '{key}': '{original_lines[idx].strip()}'"
                    })
                    
        shorthand_matches = SHORTHAND_PATTERN.finditer(line)
        for match in shorthand_matches:
            prop = match.group(1)
            val = match.group(2)
            asym_detail = check_asymmetric_shorthand(prop, val)
            if asym_detail:
                physical_violations.append({
                    'line': line_num,
                    'type': f'{prop}-asymmetric-shorthand',
                    'content': original_lines[idx].strip(),
                    'detail': asym_detail
                })
                
    rules = parse_rules_recursive(clean_content, file_name)
    for selector, block_content, block_line in rules:
        violations = check_arabic_constraints(selector, block_content, block_line, file_name)
        arabic_violations.extend(violations)
        
    return physical_violations, arabic_violations

def main():
    if not os.path.exists(TARGET_DIR):
        print(f"Error: Target directory does not exist: {TARGET_DIR}")
        sys.exit(1)
        
    css_files = [f for f in os.listdir(TARGET_DIR) if f.endswith('.css')]
    css_files.sort()
    
    requested_filenames = ['style.css', 'index.css', 'tailwind_overrides.css', 'premium-ui.css',
                           'style-rtl.css', 'index-rtl.css', 'tailwind_overrides-rtl.css', 'premium-ui-rtl.css']
    
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("CSS STYLING ADVERSARIAL CHALLENGE REPORT")
    report_lines.append(f"Target Directory: {TARGET_DIR}")
    report_lines.append("=" * 80)
    
    total_physical_violations = 0
    total_arabic_violations = 0
    
    for file_name in css_files:
        filepath = os.path.join(TARGET_DIR, file_name)
        is_requested = file_name in requested_filenames
        
        status_tag = "[REQUESTED]" if is_requested else "[OPTIONAL ]"
        report_lines.append(f"\nAnalyzing file: {status_tag} {file_name}")
        
        physical_v, arabic_v = analyze_css_file(filepath)
        
        if not physical_v and not arabic_v:
            report_lines.append("  PASS: No physical directional properties or Arabic typography violations found.")
        else:
            if physical_v:
                report_lines.append(f"  FAIL: Found {len(physical_v)} physical directional layout properties:")
                for v in physical_v:
                    report_lines.append(f"    Line {v['line']}: {v['detail']}")
                total_physical_violations += len(physical_v)
                
            if arabic_v:
                report_lines.append(f"  FAIL: Found {len(arabic_v)} Arabic typography constraint violations:")
                for v in arabic_v:
                    report_lines.append(f"    Line {v['line']}: {v['detail']}")
                total_arabic_violations += len(arabic_v)
                
    report_lines.append("\n" + "=" * 80)
    report_lines.append("CHALLENGE SUMMARY")
    report_lines.append(f"Total Physical Violations: {total_physical_violations}")
    report_lines.append(f"Total Arabic Typography Violations: {total_arabic_violations}")
    report_lines.append("=" * 80)
    
    # Print report to stdout as well
    for line in report_lines:
        print(line)
        
    # Write report to file in UTF-8
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines) + '\n')
        
    requested_violations = 0
    for file_name in requested_filenames:
        filepath = os.path.join(TARGET_DIR, file_name)
        if os.path.exists(filepath):
            p, a = analyze_css_file(filepath)
            requested_violations += len(p) + len(a)
            
    if requested_violations > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()

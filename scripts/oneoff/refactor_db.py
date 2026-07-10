import os
import re

def refactor_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.splitlines()
    modified = False
    
    i = len(lines) - 1
    while i >= 0:
        line = lines[i]
        # Match active (not commented) lines like: conn = get_db() or db = get_db() or _conn = get_db()
        match = re.match(r'^(\s*)(conn|db|_conn)\s*=\s*(?:Database\.)?get_db\(\)', line)
        if match:
            indent = match.group(1)
            var_name = match.group(2)
            indent_len = len(indent)
            
            # Find the end of the block/function.
            end_idx = i + 1
            while end_idx < len(lines):
                next_line = lines[end_idx]
                if next_line.strip():
                    next_indent_len = len(next_line) - len(next_line.lstrip())
                    if next_indent_len <= indent_len:
                        break
                end_idx += 1
            
            new_lines = []
            for idx in range(i + 1, end_idx):
                curr_line = lines[idx]
                if not curr_line.strip():
                    new_lines.append(curr_line)
                    continue
                
                close_pattern = rf'\b{var_name}\.close\(\)'
                if re.search(close_pattern, curr_line):
                    # Replace close call with pass or clean it up
                    cleaned = re.sub(rf'^\s*{var_name}\.close\(\)\s*$', '', curr_line)
                    if not cleaned.strip():
                        curr_line = indent + "    pass"
                    else:
                        curr_line = re.sub(rf';?\s*\b{var_name}\.close\(\)', '', curr_line)
                        curr_line = re.sub(rf'\b{var_name}\.close\(\);?\s*', '', curr_line)
                        curr_line = "    " + curr_line
                else:
                    curr_line = "    " + curr_line
                new_lines.append(curr_line)
            
            lines[i] = f"{indent}with get_db() as {var_name}:"
            lines[i+1:end_idx] = new_lines
            modified = True
            
        i -= 1
        
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        print(f"Refactored {filepath}")

if __name__ == "__main__":
    refactor_file("web/app_v2.py")
    for root, _, files in os.walk("web/routers"):
        for file in files:
            if file.endswith(".py"):
                refactor_file(os.path.join(root, file))

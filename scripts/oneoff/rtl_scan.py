import os
import re

templates_dir = r'web\templates'
physical_props = re.compile(r'(margin-left|margin-right|padding-left|padding-right)\s*:')
input_no_dir = re.compile(r'<input(?![^>]*\bdir=)[^>]*>')
textarea_no_dir = re.compile(r'<textarea(?![^>]*\bdir=)[^>]*>')
left_right_inline = re.compile(r"style=[\"'][^\"']*\b(left|right)\s*:", re.IGNORECASE)

results_physical = []
results_input = []
results_textarea = []
results_inline = []

for root, dirs, files in os.walk(templates_dir):
    for f in files:
        if not f.endswith('.html'):
            continue
        path = os.path.join(root, f)
        rel = os.path.relpath(path, templates_dir)
        try:
            content = open(path, encoding='utf-8', errors='replace').readlines()
        except Exception:
            continue
        for i, line in enumerate(content, 1):
            if physical_props.search(line):
                results_physical.append((rel, i, line.rstrip()[:150]))
            if input_no_dir.search(line):
                results_input.append((rel, i, line.rstrip()[:150]))
            if textarea_no_dir.search(line):
                results_textarea.append((rel, i, line.rstrip()[:150]))
            if left_right_inline.search(line):
                results_inline.append((rel, i, line.rstrip()[:150]))

print("=== PHYSICAL CSS PROPERTIES (margin/padding -left/-right) ===")
for rel, i, line in results_physical:
    print(f"  {rel}:{i}: {line}")
print(f"\nTotal: {len(results_physical)}")

print("\n=== INPUTS MISSING dir= ===")
for rel, i, line in results_input:
    print(f"  {rel}:{i}: {line}")
print(f"\nTotal: {len(results_input)}")

print("\n=== TEXTAREAS MISSING dir= ===")
for rel, i, line in results_textarea:
    print(f"  {rel}:{i}: {line}")
print(f"\nTotal: {len(results_textarea)}")

print("\n=== INLINE LEFT/RIGHT STYLES ===")
for rel, i, line in results_inline:
    print(f"  {rel}:{i}: {line}")
print(f"\nTotal: {len(results_inline)}")

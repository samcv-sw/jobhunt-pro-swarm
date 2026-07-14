# -*- coding: utf-8 -*-
# Fix the broken return statement in test_stealth_parser_and_fallbacks.py
# Replace lines 247-249 with a valid single-line return

with open('tests/test_stealth_parser_and_fallbacks.py', 'rb') as f:
    lines = f.read().split(b'\n')

print("Before fix:")
for i in range(244, 254):
    print(f"  Line {i+1} (idx {i}): {lines[i]!r}")

# The replacement needs to be the complete valid Python line:
# return '[{"title": "Python Developer LLM", "url": "https://example.com/python-llm", ...}]'
# To write this as a Python literal inside a byte string, we escape each " as \"

# Method: build the target line character by character
target_line = "        return " + chr(39) + '[{"title": "Python Developer LLM", "url": "https://example.com/python-llm", "company": "LLM Corp", "description_snippet": "Extracted via LLM fallback"}]' + chr(39)
target_bytes = target_line.encode('utf-8')
print("\nTarget line bytes:", target_bytes)

# Replace lines 247-249 (0-idx 246-248)
new_lines = lines[:246] + [target_bytes] + lines[249:]

with open('tests/test_stealth_parser_and_fallbacks.py', 'wb') as f:
    f.write(b'\n'.join(new_lines))

print("\nAfter fix:")
with open('tests/test_stealth_parser_and_fallbacks.py', 'rb') as f:
    new_content = f.read()
new_lines_check = new_content.split(b'\n')
for i in range(244, 250):
    print(f"  Line {i+1} (idx {i}): {new_lines_check[i]!r}")

# Verify syntax
import ast

with open('tests/test_stealth_parser_and_fallbacks.py', 'r', encoding='utf-8') as f:
    src = f.read()
try:
    ast.parse(src)
    print("\nAST OK - no syntax errors!")
except SyntaxError as e:
    print(f"\nLine {e.lineno}: {e.msg}")
    src_lines = src.split('\n')
    for i in range(max(0, e.lineno - 3), min(len(src_lines), e.lineno + 3)):
        print(f"  {i+1}: {src_lines[i][:120]}")

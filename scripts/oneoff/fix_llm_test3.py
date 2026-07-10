# -*- coding: utf-8 -*-
with open('tests/test_stealth_parser_and_fallbacks.py', 'rb') as f:
    lines = f.read().split(b'\n')

# Lines to replace: 247-249 (0-indexed: 246-248)
# Old broken lines:
#   247: return '[
#   248:     {...dict...}
#   249: ]'
# New working lines: implicit string concatenation
new_lines_247_to_249 = [
    b"        return '[{\"title\": \"Python Developer LLM\", "
    b"\"url\": \"https://example.com/python-llm\", "
    b"\"company\": \"LLM Corp\", "
    b"\"description_snippet\": \"Extracted via LLM fallback\"}]'",
]

new_lines = lines[:246] + new_lines_247_to_249 + lines[249:]

with open('tests/test_stealth_parser_and_fallbacks.py', 'wb') as f:
    f.write(b'\n'.join(new_lines))
print("Written OK")

# Verify syntax
import ast
with open('tests/test_stealth_parser_and_fallbacks.py', 'r', encoding='utf-8') as f:
    src = f.read()
try:
    ast.parse(src)
    print("AST parse OK - no syntax errors!")
except SyntaxError as e:
    print(f"SYNTAX ERROR at line {e.lineno}: {e.msg}")
    lines2 = src.split('\n')
    for i in range(max(0,e.lineno-3), min(len(lines2), e.lineno+2)):
        print(f"  {i+1}: {lines2[i]}")

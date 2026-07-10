# -*- coding: utf-8 -*-
import sys

with open('tests/test_stealth_parser_and_fallbacks.py', 'rb') as f:
    lines = f.read().split(b'\n')

# Replace the broken return statement (lines 247-249, 0-idx 246-248)
# Old lines:
#   247 (idx 246): return '[
#   248 (idx 247): {...dict...}
#   249 (idx 248): ]'
# New: a complete single-line return statement

new_return = (
    b"        return \'[{\\\"title\\\": \\\"Python Developer LLM\\\", "
    b"\\\"url\\\": \\\"https://example.com/python-llm\\\", "
    b"\\\"company\\\": \\\"LLM Corp\\\", "
    b"\\\"description_snippet\\\": \\\"Extracted via LLM fallback\\\"}]\'"
)

new_lines = lines[:246] + [new_return] + lines[249:]

with open('tests/test_stealth_parser_and_fallbacks.py', 'wb') as f:
    f.write(b'\n'.join(new_lines))

print('Written OK, total lines:', len(new_lines))

# Verify syntax
import ast
with open('tests/test_stealth_parser_and_fallbacks.py', 'r', encoding='utf-8') as f:
    src = f.read()
try:
    ast.parse(src)
    print('AST OK - no syntax errors!')
except SyntaxError as e:
    print(f'Line {e.lineno}: {e.msg}')
    src_lines = src.split('\n')
    for i in range(max(0, e.lineno - 3), min(len(src_lines), e.lineno + 3)):
        print(f"  {i+1}: {src_lines[i][:100]}")

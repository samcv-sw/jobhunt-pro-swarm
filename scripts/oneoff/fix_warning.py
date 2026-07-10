# -*- coding: utf-8 -*-
with open('tests/test_stealth_parser_and_fallbacks.py', 'rb') as f:
    lines = f.read().split(b'\n')

# Fix line 237 (idx 236): raw-string escape in docstring comment
# r'\[.*\]' causes SyntaxWarning, change to use double-backslash
old = b"    stripping whitespace \xe2\x80\x94 otherwise _extract_json's regex r'\\[.*\\]'"
new = b"    stripping whitespace \xe2\x80\x94 otherwise _extract_json's regex r'\\\\[.*\\\\]'"

if lines[236] == old:
    lines[236] = new
    with open('tests/test_stealth_parser_and_fallbacks.py', 'wb') as f:
        f.write(b'\n'.join(lines))
    print("Fixed!")
else:
    print("Not found:", repr(lines[236]))

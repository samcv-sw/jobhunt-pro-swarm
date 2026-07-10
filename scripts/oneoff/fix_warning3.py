# -*- coding: utf-8 -*-
with open('tests/test_stealth_parser_and_fallbacks.py', 'rb') as f:
    raw = f.read()

# Fix the SyntaxWarning on line 237: r'\[.*\]' in docstring is invalid escape
# Change the comment to avoid the problematic raw-string pattern
# Target: b"    stripping whitespace \xe2\x80\x94 otherwise _extract_json's regex r'\\[.*\\]'"
old = (
    b"    stripping whitespace \xe2\x80\x94 otherwise _extract_json's regex r'\\[.*\\]'"
    b" may fail\r\n"
)
new = (
    b"    stripping whitespace \xe2\x80\x94 otherwise _extract_json's regex pattern"
    b" may fail\r\n"
)

if old in raw:
    raw = raw.replace(old, new)
    with open('tests/test_stealth_parser_and_fallbacks.py', 'wb') as f:
        f.write(raw)
    print("Fixed!")
else:
    print("Not found. Showing lines 234-242:")
    lines = raw.split(b'\r\n')
    for i in range(233, 242):
        print(f"  {i+1}: {lines[i]!r}")

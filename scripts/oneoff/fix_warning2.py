# -*- coding: utf-8 -*-
with open('tests/test_stealth_parser_and_fallbacks.py', 'rb') as f:
    raw = f.read()

# Fix the SyntaxWarning on line 237 (idx 236 in 0-based, line 237 in 1-based)
# File uses \r\n line endings
old = (
    b"    stripping whitespace \xe2\x80\x94 otherwise _extract_json's regex r'\\[.*\\]'"
    b" may fail\r\n"
)
new = (
    b"    stripping whitespace \xe2\x80\x94 otherwise _extract_json's regex r'[' * r'.*]'\r\n"
    # Use r'[' and r']' to avoid \r warning while still showing the intent
)

if old in raw:
    raw = raw.replace(old, new)
    with open('tests/test_stealth_parser_and_fallbacks.py', 'wb') as f:
        f.write(raw)
    print("Fixed!")
else:
    print("Not found. Showing lines around 237:")
    lines = raw.split(b'\r\n')
    for i in range(234, 242):
        print(f"  {i+1}: {lines[i]!r}")

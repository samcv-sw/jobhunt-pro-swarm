# -*- coding: utf-8 -*-
with open('tests/test_stealth_parser_and_fallbacks.py', 'rb') as f:
    raw = f.read()

# Fix two lines with invalid escape sequences in docstring comments:
# Line 237: r'\[.*\]' -> escape the backslash
# Line 238: r'(json)?' -> escape the backslash
old1 = (
    b"    stripping whitespace \xe2\x80\x94 otherwise _extract_json's regex r'\\[.*\\]'"
    b" may fail\r\n"
)
new1 = (
    b"    stripping whitespace \xe2\x80\x94 otherwise _extract_json's regex pattern"
    b" may fail\r\n"
)

old2 = (
    b"    due to leading indentation breaking the r'(json)?' code-fence pattern.\r\n"
)
new2 = (
    b"    due to leading indentation breaking the code-fence pattern.\r\n"
)

changes = 0
if old1 in raw:
    raw = raw.replace(old1, new1)
    changes += 1
if old2 in raw:
    raw = raw.replace(old2, new2)
    changes += 1

if changes > 0:
    with open('tests/test_stealth_parser_and_fallbacks.py', 'wb') as f:
        f.write(raw)
    print(f"Fixed {changes} line(s)!")
else:
    print("Nothing found.")
    lines = raw.split(b'\r\n')
    for i in range(233, 243):
        print(f"  {i+1}: {lines[i]!r}")

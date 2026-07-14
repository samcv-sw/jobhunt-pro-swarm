# -*- coding: utf-8 -*-
with open('tests/test_stealth_parser_and_fallbacks.py', 'rb') as f:
    data = f.read()

# The broken section spans lines 247-251 (0-indexed: 246-250)
# Replace with proper multi-line return statement
lines = data.split(b'\n')
# lines[246] = comment (good)
# lines[247] = "        return '["  <- BROKEN, missing closing quote
# lines[248] = dict JSON
# lines[249] = "        ]'"  <- this is a standalone string, not a continuation
# lines[250] = empty line

# Build the replacement: lines 247-250
replacement = [
    b"        # Return JSON starting with [ — avoids _extract_json regex issue",
    b"        return (",
    b'            \'[{"title": "Python Developer LLM", "url": "https://example.com/python-llm",\' ',
    b'             \'"company": "LLM Corp", "description_snippet": "Extracted via LLM fallback"}]\'',
    b"        )",
    b"",
]

new_lines = lines[:247] + replacement + lines[251:]
with open('tests/test_stealth_parser_and_fallbacks.py', 'wb') as f:
    f.write(b'\n'.join(new_lines))

import os

# Verify it parses
import py_compile
import tempfile

tmp = tempfile.mktemp(suffix='.py')
with open(tmp, 'wb') as f:
    f.write(b'\n'.join(new_lines))

try:
    py_compile.compile(tmp, doraise=True)
    print("SYNTAX OK!")
finally:
    os.unlink(tmp)

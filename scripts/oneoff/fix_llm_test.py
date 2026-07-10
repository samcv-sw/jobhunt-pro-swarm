# -*- coding: utf-8 -*-
with open('tests/test_stealth_parser_and_fallbacks.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the broken LLM return statement
old = """        # Return clean JSON with no leading indentation - matches r'\\[.*\\]' regex
        return '[
            {"title": "Python Developer LLM", "url": "https://example.com/python-llm", "company": "LLM Corp", "description_snippet": "Extracted via LLM fallback"}
        ]'"""

new = """        # Return clean JSON starting with '[' — matches r"[.*]" regex in _extract_json
        return (
            '[{"title": "Python Developer LLM", '
            '"url": "https://example.com/python-llm", '
            '"company": "LLM Corp", '
            '"description_snippet": "Extracted via LLM fallback"}]'
        )"""

if old in content:
    content = content.replace(old, new)
    with open('tests/test_stealth_parser_and_fallbacks.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed!")
else:
    print("Pattern not found. Current content around line 247:")
    lines = content.split('\n')
    for i, line in enumerate(lines[244:256], start=245):
        print(f"{i}: {repr(line)}")

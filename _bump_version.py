"""Bump version in config.py"""
with open('config.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = 'VERSION = "16.165"'
new = 'VERSION = "16.174"'
content = content.replace(old, new)

with open('config.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Version bumped: {old} -> {new}')

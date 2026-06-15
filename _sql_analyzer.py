import ast
import os

def check_sql(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read())
        except Exception:
            return
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr in ('execute', 'executescript'):
                if node.args:
                    arg = node.args[0]
                    if isinstance(arg, ast.JoinedStr):
                        print(f"[F-String SQL] {filepath}:{node.lineno}")

for root, _, files in os.walk('.'):
    if 'venv' in root or '.git' in root or '__pycache__' in root:
        continue
    for f in files:
        if f.endswith('.py'):
            check_sql(os.path.join(root, f))

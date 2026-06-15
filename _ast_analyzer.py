import ast
import os

def analyze_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        try:
            content = f.read()
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"Syntax error in {filepath}: {e}")
            return
    
    for node in ast.walk(tree):
        # Check for empty except Exception:
        if isinstance(node, ast.ExceptHandler):
            if isinstance(node.type, ast.Name) and node.type.id == "Exception":
                # Check if it just passes
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    print(f"[Swallowed Exception] {filepath}:{node.lineno}")

        # Check for print statements
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "print":
                print(f"[Print Statement] {filepath}:{node.lineno}")

for root, _, files in os.walk('.'):
    if 'venv' in root or '.git' in root or '__pycache__' in root:
        continue
    for f in files:
        if f.endswith('.py'):
            analyze_file(os.path.join(root, f))

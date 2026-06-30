import os, ast, sys

PROJ = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJ)

std_lib = {
    'os', 'sys', 'json', 'datetime', 'time', 're', 'math', 'random',
    'typing', 'collections', 'functools', 'itertools', 'hashlib', 'hmac',
    'base64', 'urllib', 'io', 'pathlib', 'threading', 'inspect',
    'copy', 'enum', 'string', 'csv', 'logging', 'uuid', 'ast',
    'http', 'socket', 'ssl', 'email', 'xml', 'html', 'traceback',
    'pickle', 'struct', 'warnings', 'zlib', 'tempfile',
    'binascii', 'textwrap', 'argparse', 'subprocess', 'dataclasses',
    'decimal', 'fractions', 'statistics', 'bisect', 'heapq',
    'operator', 'sqlite3', 'calendar', 'locale',
    'getpass', 'platform', 'errno', 'atexit', 'signal',
    'contextlib', 'weakref', 'numbers', 'dis', 'tokenize',
    '__future__', 'builtins', '__main__', 'configparser',
    'filecmp', 'fnmatch', 'glob', 'linecache',
    'mimetypes', 'netrc', 'pprint', 'config', 'payments', 'services',
}

imports = {}
core_files = []
total_files = 0
third_party = set()

for root, dirs, files in os.walk(PROJ):
    dirs[:] = [d for d in dirs if not d.startswith('__') and d not in ('__pycache__', '.git', 'node_modules', 'venv', '.gitignore')]
    for f in files:
        if not f.endswith('.py'):
            continue
        total_files += 1
        fp = os.path.join(root, f)
        rel = os.path.relpath(fp, PROJ)
        if rel.startswith('_') or rel.startswith('backup') or 'temp' in rel:
            continue
        try:
            with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
                tree = ast.parse(fh.read())
            mod_imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        mod_imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        mod_imports.add(node.module.split('.')[0])
            imports[rel] = sorted(mod_imports)
            for imp in mod_imports:
                if imp not in std_lib and not imp.startswith('_'):
                    third_party.add(imp)
            core_files.append(rel)
        except Exception as e:
            imports[rel] = [f'[ERR:{str(e)[:30]}]']
            core_files.append(rel)

print(f'Total .py files: {total_files}')
print(f'Core files scanned: {len(core_files)}')
print(f'\n=== Third-party dependencies needed ===')
for dep in sorted(third_party):
    print(f'  {dep}')
print(f'\nTotal unique third-party deps: {len(third_party)}')

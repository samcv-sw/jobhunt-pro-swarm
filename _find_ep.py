import config
# Find where EMAIL_PROVIDERS is defined in config.py
with open('config.py', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'EMAIL_PROVIDERS' in line:
        print(f'L{i+1}: {line.rstrip()[:120]}')
        # Print next few lines
        for j in range(i+1, min(i+5, len(lines))):
            print(f'  L{j+1}: {lines[j].rstrip()[:120]}')

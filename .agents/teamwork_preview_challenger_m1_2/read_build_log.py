import sys

# Set standard output encoding to utf-8
sys.stdout.reconfigure(encoding='utf-8')

with open('../../frontend/build_out.log', encoding='utf-16') as f:
    print(f.read())

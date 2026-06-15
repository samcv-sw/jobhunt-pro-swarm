#!/usr/bin/env python3
"""Read register handler from app_v2.py"""
import re

with open(r'C:\Users\samde\Desktop\cv sam new ma3 kimi\web\app_v2.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find register POST handler
for i, line in enumerate(lines):
    if line.strip().startswith('@app.post') and '/register' in line:
        print(f"Found at line {i+1}")
        for j in range(i, min(i+100, len(lines))):
            line = lines[j].rstrip()
            print(f"{j+1}: {line}")
            # Stop at the return statement that redirects
            if line.strip().startswith('return') and ('Redirect' in line or 'HTMLResponse' in line or 'JSONResponse' in line):
                if j < i+40:
                    pass  # keep going to see the full function
                else:
                    break
        break

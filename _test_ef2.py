# -*- coding: utf-8 -*-
import re
import sys
sys.path.insert(0, r'C:\Users\samde\Desktop\cv sam new ma3 kimi')
from core.email_finder import COMPANY_SUFFIXES

company = 'Network Solutions Inc'
print('Testing COMPANY_SUFFIXES on:', repr(company))
for suffix in COMPANY_SUFFIXES:
    result = re.sub(suffix, '', company, flags=re.IGNORECASE)
    if result != company:
        print(f'  MATCH: {suffix} -> {repr(result)}')

# Test specific patterns
for suffix in [r'\bInc\b', r'\bInc\.?\b', r'Inc\.?', r'Inc']:
    r = re.sub(suffix, 'XXX', company, flags=re.IGNORECASE)
    print(f'  pattern="{suffix}": {repr(r)}')

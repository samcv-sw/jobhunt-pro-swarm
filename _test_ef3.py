# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'C:\Users\samde\Desktop\cv sam new ma3 kimi')
from core.email_finder import EmailFinder as EF

tests = [
    ('careers@networksolutionsinc.com', 'Network Solutions Inc', True),
    ('careers@harrywinston.com', 'Harry Winston', False),
    ('hr@techcorpllc.com', 'Tech Corp LLC', True),
    ('careers@murex.com', 'Murex', False),
    ('john@realcompany.com', 'Real Company', False),
    ('', 'Some Co', True),
    ('careers@bankaudi.com', 'Bank Audi', False),
    ('careers@azadeagroup.com', 'Azadea Group', False),
    ('careers@blominvestbank.com', 'BLOM Invest Bank', False),
]

all_ok = True
for email, company, expected in tests:
    result = EF.is_placeholder_email(email, company)
    status = 'OK' if result == expected else f'FAIL (expected {expected})'
    if result != expected:
        all_ok = False
    print(f'  [{status}] is_placeholder({repr(email)}, {repr(company)}) = {result}')

print(f'\nAll passed: {all_ok}')

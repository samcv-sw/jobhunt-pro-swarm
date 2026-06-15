# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'C:\Users\samde\Desktop\cv sam new ma3 kimi')
from core.global_scraper import _clean_company_for_domain

tests = [
    ('Network Solutions Inc', 'networksolutions'),
    ('Harry Winston', 'harrywinston'),
    ('Tech Corp LLC', 'tech'),
    ('Murex', 'murex'),
    ('Bank Audi SAL', 'bankaudi'),
    ('Azadea Group', 'azadea'),
    ('BLOM Invest Bank SAL', 'blominvestbank'),
    ('Alfa Telecommunications', 'alfatelecommunications'),
    ('Touch Lebanon', 'touchlebanon'),
    ('Malia Group', 'malia'),
    ('Murex SAS', 'murex'),
]

all_ok = True
for company, expected in tests:
    result = _clean_company_for_domain(company)
    status = 'OK' if result == expected else f'FAIL'
    if result != expected:
        all_ok = False
    print(f'  [{status}] {repr(company)} -> "{result}" (expected "{expected}")')

print(f'\nAll passed: {all_ok}')

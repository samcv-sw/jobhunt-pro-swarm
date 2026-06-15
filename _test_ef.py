import sys
sys.path.insert(0, r'C:\Users\samde\Desktop\cv sam new ma3 kimi')
from core.email_finder import _clean_company_name, EmailFinder
import re

# Debug case 1
company = 'Network Solutions Inc'
clean = _clean_company_name(company)
clean_domain = re.sub(r'[\s-]+', '', clean.lower())
naive = re.sub(r'[^a-z0-9]', '', company.lower())
print(f'clean_name="{clean}"')
print(f'clean_domain="{clean_domain}" len={len(clean_domain)}')
print(f'naive_domain="{naive}" len={len(naive)}')
print(f'delta={len(naive)-len(clean_domain)}')

domain_part = 'networksolutionsinc.com'
print(f'naive_domain in domain_part: {naive in domain_part}')
print(f'Final result: {EmailFinder.is_placeholder_email("careers@networksolutionsinc.com", "Network Solutions Inc")}')

# Debug case 8  
company2 = 'Azadea Group'
clean2 = _clean_company_name(company2)
clean_domain2 = re.sub(r'[\s-]+', '', clean2.lower())
naive2 = re.sub(r'[^a-z0-9]', '', company2.lower())
print(f'\nAzadea: clean="{clean2}" clean_domain="{clean_domain2}" naive="{naive2}"')
print(f'is_placeholder: {EmailFinder.is_placeholder_email("careers@azadea.com", "Azadea Group")}')

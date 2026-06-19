"""Test full stack - simpler version."""
import requests, urllib3
urllib3.disable_warnings()

worker = 'https://jobhunt-pro-router.samsalameh-cv.workers.dev'
pages = 'https://jobhunt-9d1.pages.dev'

# Wake PA
r = requests.get(f'{worker}/_/pa/api/health', timeout=30)
print(f'PA wake: {r.status_code}')

# Worker PA proxy
r = requests.get(f'{worker}/_/pa/api/cloud-health', timeout=30)
print(f'Worker->CloudHealth: {r.status_code} {r.text[:100]}')

# Worker Stats Daily
r = requests.get(f'{worker}/_/pa/api/stats/daily?days=7', timeout=30)
print(f'Worker->StatsDaily: {r.status_code} {r.text[:100]}')

# Pages PA proxy
r = requests.get(f'{pages}/_/pa/api/cloud-health', timeout=30)
print(f'Pages->CloudHealth: {r.status_code} {r.text[:100]}')

# Pages register
r = requests.post(f'{pages}/_/pa/api/register-fast', json={'name':'Full Test','email':'fulltest@pa.com','roles':['Engineer']}, timeout=30)
print(f'Pages->Register: {r.status_code} {r.text[:100]}')

# Pages lookup
r = requests.get(f'{pages}/_/pa/api/user/by-email?email=fulltest@pa.com', timeout=30)
print(f'Pages->Lookup: {r.status_code} {r.text[:100]}')

print('')
print('=== DONE ===')

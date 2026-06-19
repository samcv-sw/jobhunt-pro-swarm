"""Simulate a full user flow through the Pages frontend."""
import requests, urllib3, time, sys, json
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = 'https://jobhunt-9d1.pages.dev'
passed = 0
total = 0

def check(step, condition, detail=''):
    global passed, total
    total += 1
    if condition:
        passed += 1
        print(f'[{total}] OK  -> {step}')
    else:
        print(f'[{total}] FAIL -> {step}: {str(detail)[:80]}')

# Wake PA
print('Waking PA...')
r = requests.get(f'{BASE}/api/health', timeout=30)
print(f'  Health: {r.status_code}')
time.sleep(2)

# 1. Frontend loads
r = requests.get(f'{BASE}/', timeout=30)
check('Frontend loads', r.status_code == 200 and len(r.text) > 10000)

# 2. Register
reg_data = {
    'name': 'Sam Salameh',
    'email': 'sam.userflow.test@gmail.com',
    'phone': '+96170841100',
    'roles': ['Network Engineer', 'DevOps Engineer', 'IT Manager'],
    'locations': ['Beirut', 'Dubai', 'Remote'],
    'salary': 2500
}
r = requests.post(f'{BASE}/_/pa/api/register-fast', json=reg_data, timeout=45)
data = r.json()
check('Register ok', data.get('ok') == True, str(data))
user_id = data.get('user_id', '')
check('Has user_id', len(user_id) > 0, user_id)
time.sleep(1)

# 3. Lookup
r = requests.get(f'{BASE}/_/pa/api/user/by-email?email=sam.userflow.test@gmail.com', timeout=30)
data = r.json()
check('Lookup ok', data.get('user_id') == user_id, data.get('name',''))

# 4. Stats
r = requests.get(f'{BASE}/_/pa/api/user/stats?user_id=' + user_id, timeout=30)
data = r.json()
check('Stats returns', 'apps_sent' in data, str(data.get('apps_sent','?')))

# 5. SMTP test (fake creds -> expected fail)
r = requests.post(f'{BASE}/_/pa/api/byo-smtp/test', json={
    'email': 'sam.userflow.test@gmail.com',
    'password': 'badpassword123'
}, timeout=30)
data = r.json()
check('SMTP test returns', 'success' in data, data.get('message','')[:40])

# 6. SMTP save
r = requests.post(f'{BASE}/_/pa/api/byo-smtp/save', json={
    'email': 'sam.userflow.test@gmail.com',
    'password': 'xxxx yyyy zzzz wwww',
    'user_id': user_id
}, timeout=30)
data = r.json()
check('SMTP save ok', data.get('ok') == True, str(data.get('message',''))[:40])

# 7. Daily stats
r = requests.get(f'{BASE}/_/pa/api/stats/daily?days=7', timeout=30)
data = r.json()
check('Daily stats', 'stats' in data, str(len(data.get('stats',[]))) + ' entries')

# 8. Cloud health
r = requests.get(f'{BASE}/_/pa/api/cloud-health', timeout=30)
data = r.json()
check('Cloud health', data.get('status') == 'ok', data.get('api',''))

print()
print(f'= RESULT: {passed}/{total} passed =')
if passed == total:
    print('USER FLOW 100% OPERATIONAL!')
else:
    print(f'{total-passed} FAILURES')

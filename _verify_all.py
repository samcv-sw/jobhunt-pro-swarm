"""Full end-to-end verification of JobHunt Pro cloud stack."""
import requests, urllib3, time, sys, os
urllib3.disable_warnings()

# Set console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WORKER = 'https://jobhunt-pro-router.samsalameh-cv.workers.dev'
PAGES = 'https://jobhunt-9d1.pages.dev'
PA = 'https://jhfguf.pythonanywhere.com'

passed = 0
failed = 0

def test(name, url, method='GET', body=None, expect=200):
    global passed, failed
    try:
        if method == 'POST':
            r = requests.post(url, json=body, timeout=45)
        else:
            r = requests.get(url, timeout=45)
        
        if r.status_code == expect:
            print(f'[PASS] {name} (HTTP {r.status_code})')
            passed += 1
        else:
            try:
                data = r.json()
                error = data.get('error', str(data)[:80])
            except:
                error = r.text[:80]
            print(f'[FAIL] {name} -- Expected {expect}, got {r.status_code}: {error}')
            failed += 1
    except Exception as e:
        print(f'[FAIL] {name} -- Exception: {e}')
        failed += 1

print('=' * 50)
print('VERIFICATION -- JobHunt Pro Cloud')
print('=' * 50)

print('\n[1] WORKER (D1)')
test('Worker Health', f'{WORKER}/api/health')
test('Worker Route List', f'{WORKER}/')

print('\n[2] PAGES (Frontend)')
test('Pages Health (Worker)', f'{PAGES}/api/health')
test('Pages Index', f'{PAGES}/')

print('\n[3] PA HEALTH (via Worker proxy)')
test('PA Wake', f'{PA}/healthz')
time.sleep(2)
test('PA Health via Worker', f'{WORKER}/_/pa/api/health')
test('PA CloudHealth', f'{PA}/api/cloud-health')
test('PA CloudHealth via Worker', f'{WORKER}/_/pa/api/cloud-health')
test('PA CloudHealth via Pages', f'{PAGES}/_/pa/api/cloud-health')

print('\n[4] USER REGISTRATION')
r = requests.get(f'{PA}/api/health', timeout=30)  # wake PA
test('Register (PA direct)', f'{PA}/api/register-fast', 'POST', {
    'name': 'Sam Salameh',
    'email': 'samtest.end2end@gmail.com',
    'phone': '+96170123456',
    'roles': ['Network Engineer', 'DevOps'],
    'locations': ['Beirut', 'Dubai', 'Remote'],
    'salary': 2000
})
test('Register (via Worker)', f'{WORKER}/_/pa/api/register-fast', 'POST', {
    'name': 'Worker Test',
    'email': 'worker.test@gmail.com',
    'roles': ['Engineer'],
    'locations': ['Remote'],
    'salary': 1500
})
test('Register (via Pages)', f'{PAGES}/_/pa/api/register-fast', 'POST', {
    'name': 'Pages Test',
    'email': 'pages.test@gmail.com',
    'roles': ['Developer'],
    'locations': ['Beirut'],
    'salary': 1000
})
time.sleep(1)

print('\n[5] USER LOOKUP')
test('Lookup (PA direct)', f'{PA}/api/user/by-email?email=samtest.end2end@gmail.com')
test('Lookup (via Worker)', f'{WORKER}/_/pa/api/user/by-email?email=worker.test@gmail.com')
test('Lookup (via Pages)', f'{PAGES}/_/pa/api/user/by-email?email=pages.test@gmail.com')

print('\n[6] USER STATS')
test('Stats (PA direct)', f'{PA}/api/user/stats?user_id=test')
test('Stats (via Worker)', f'{WORKER}/_/pa/api/user/stats?user_id=test')

print('\n[7] SMTP')
test('SMTP Test', f'{PA}/api/byo-smtp/test', 'POST', {
    'email': 'test@gmail.com',
    'password': 'test123'
})
test('SMTP Save', f'{PA}/api/byo-smtp/save', 'POST', {
    'email': 'saved@gmail.com',
    'password': 'saved123',
    'user_id': 'test123'
})

print('\n[8] GLOBAL STATS')
test('Daily Stats (PA direct)', f'{PA}/api/stats/daily?days=7')
test('Daily Stats (via Worker)', f'{WORKER}/_/pa/api/stats/daily?days=7')
test('Daily Stats (via Pages)', f'{PAGES}/_/pa/api/stats/daily?days=7')

print()
print('=' * 50)
print(f'RESULT: {passed} PASS  |  {failed} FAIL  |  Total: {passed+failed}')
if failed == 0:
    print('100% PASSED -- Full Stack Operational!')
else:
    print(f'WARN: {failed} test(s) failed')
print('=' * 50)

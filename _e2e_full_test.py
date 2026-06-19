#!/usr/bin/env python3
"""Complete E2E test of the JobHunt Pro system"""
import requests, urllib3, json
urllib3.disable_warnings()

FRONTEND = 'https://9eba9dcc.jobhunt-9d1.pages.dev'
WORKER = 'https://jobhunt-pro-router.samsalameh-cv.workers.dev'
PA = 'https://jhfguf.pythonanywhere.com'

results = []

def test(name, url, method='GET', data=None, expect_code=200):
    try:
        if method == 'POST':
            r = requests.post(url, json=data, timeout=30)
        else:
            r = requests.get(url, timeout=30)
        
        status = 'PASS' if r.status_code == expect_code else 'FAIL'
        detail = r.text[:120] if r.status_code != expect_code else 'OK'
        label = '+' if status == 'PASS' else 'x'
        print('  [%s] %s: %d (expected %d)' % (status, name, r.status_code, expect_code))
        if status == 'FAIL':
            print('       %s' % detail)
        results.append({'name': name, 'status': status, 'code': r.status_code})
        return r
    except Exception as e:
        print('  [FAIL] %s: ERROR - %s' % (name, e))
        results.append({'name': name, 'status': 'FAIL', 'code': 0})
        return None

print('=' * 50)
print('COMPREHENSIVE E2E TEST - JobHunt Pro v3.0')
print('=' * 50)

# 1. INFRASTRUCTURE
print('\n*** INFRASTRUCTURE ***')
test('Worker Health', WORKER + '/health')
test('Worker D1 Health', WORKER + '/api/cloud-health')
test('PA Health', PA + '/api/cloud-health')
test('Frontend Pages', FRONTEND)
test('Frontend Proxy Health', FRONTEND + '/api/cloud-health')

# 2. USER FLOW
print('\n*** USER REGISTRATION ***')
r = test('Register User', WORKER + '/api/register-fast', 'POST', 
    {'name':'E2E Test User','email':'e2e.test@demo.com','roles':['Network Engineer','DevOps'],
     'locations':['Beirut','Dubai','Remote'],'salary':2500})
uid = str(r.json().get('user_id','')) if r and r.status_code == 200 else '1'
print('   User ID: %s' % uid)

test('Lookup by Email', WORKER + '/api/user/by-email?email=e2e.test@demo.com')

# 3. CAMPAIGN
print('\n*** CAMPAIGN MANAGEMENT ***')
r = test('Create Campaign', WORKER + '/api/campaign/create', 'POST', {'user_id': uid})
test('List Campaigns', WORKER + '/api/campaign/list?user_id=' + str(uid))

# 4. STATS
print('\n*** STATISTICS ***')
test('User Stats', WORKER + '/api/user/stats?user_id=' + str(uid))
test('Daily Stats', WORKER + '/api/stats/daily?days=30')

# 5. SMTP
print('\n*** SMTP CONFIG ***')
test('Save SMTP', WORKER + '/api/byo-smtp/save', 'POST',
    {'user_id': uid, 'email': 'e2etest@gmail.com', 'password': 'abcd efgh ijkl mnop'})

# 6. JOBS
print('\n*** JOBS ***')
test('User Jobs', WORKER + '/api/jobs/user?user_id=' + str(uid) + '&limit=10')

# 7. FRONTEND ACCESS
print('\n*** FRONTEND ACCESS ***')
test('Frontend via Hash', FRONTEND + '/#register')
test('Frontend Stats', FRONTEND + '/api/stats/daily?days=7')

# 8. PA BACKWARD COMPATIBILITY
print('\n*** PA BACKWARD COMPAT ***')
test('PA Proxy Health (backward)', FRONTEND + '/_/pa/api/cloud-health')

# SUMMARY
print('\n' + '=' * 50)
passed = sum(1 for r in results if r['status'] == 'PASS')
failed = sum(1 for r in results if r['status'] == 'FAIL')
print('RESULTS: %d passed, %d failed out of %d tests' % (passed, failed, len(results)))
print('=' * 50)

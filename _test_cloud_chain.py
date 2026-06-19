"""Test full stack through Pages and Worker."""
import requests, urllib3, time
urllib3.disable_warnings()

# Wake PA
r = requests.get('https://jhfguf.pythonanywhere.com/healthz', timeout=30)
print(f'PA wake: {r.status_code}')
time.sleep(2)

pages = 'https://jobhunt-9d1.pages.dev/_/pa/api'
worker = 'https://jobhunt-pro-router.samsalameh-cv.workers.dev/_/pa/api'

tests = [
    ('Pages CloudHealth', f'{pages}/cloud-health'),
    ('Worker CloudHealth', f'{worker}/cloud-health'),
    ('Pages StatsDaily', f'{pages}/stats/daily?days=7'),
    ('Pages Register', 'POST', f'{pages}/register-fast',
     {'name':'Cloud Test','email':'ctest@cloud.com','roles':['Engineer'],'locations':['Dubai'],'salary':2500}),
    ('Pages Lookup', 'GET', f'{pages}/user/by-email?email=ctest@cloud.com'),
]

for test in tests:
    name = test[0]
    try:
        if test[1] == 'POST':
            r = requests.post(test[2], json=test[3], timeout=30)
        else:
            r = requests.get(test[2], timeout=30)
        data = r.json()
        ok = data.get('status', data.get('ok', data.get('message', 'ok')))
        print(f'{name}: {r.status_code} -> {str(ok)[:60]}')
    except Exception as e:
        print(f'{name}: ERROR {type(e).__name__}: {str(e)[:80]}')

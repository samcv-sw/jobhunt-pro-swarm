"""Test frontend API routes."""
import requests, urllib3, json
urllib3.disable_warnings()

# Wake PA
print("Waking PA...")
requests.get('https://jhfguf.pythonanywhere.com/healthz', timeout=30)

# Test new routes
tests = [
    ('Cloud Health', 'GET', 'https://jhfguf.pythonanywhere.com/api/cloud-health'),
    ('Stats Daily', 'GET', 'https://jhfguf.pythonanywhere.com/api/stats/daily?days=7'),
    ('Register', 'POST', 'https://jhfguf.pythonanywhere.com/api/register-fast', {'name':'Test User','email':'t1@test.com','roles':['Engineer'],'locations':['Remote'],'salary':1500}),
    ('User Lookup', 'GET', 'https://jhfguf.pythonanywhere.com/api/user/by-email?email=t1@test.com'),
    ('User Stats', 'GET', 'https://jhfguf.pythonanywhere.com/api/user/stats?user_id=test'),
    ('SMTP Test', 'POST', 'https://jhfguf.pythonanywhere.com/api/byo-smtp/test', {'email':'test@gmail.com','password':'test123'}),
    ('SMTP Save', 'POST', 'https://jhfguf.pythonanywhere.com/api/byo-smtp/save', {'email':'test@gmail.com','password':'test123','user_id':'test123'}),
]

for name, method, url, *body in tests:
    try:
        if method == 'POST':
            r = requests.post(url, json=body[0], timeout=30)
        else:
            r = requests.get(url, timeout=30)
        data = r.json() if r.text else {}
        if r.status_code == 200:
            ok = data.get('ok', data.get('status', 'ok'))
            print(f'OK {name}: {ok}')
        elif r.status_code == 404:
            print(f'NOT FOUND {name}: 404')
        else:
            error = data.get('error', r.text[:100])
            print(f'ERROR {name}: {r.status_code} -> {error}')
    except Exception as e:
        print(f'FAIL {name}: {e}')

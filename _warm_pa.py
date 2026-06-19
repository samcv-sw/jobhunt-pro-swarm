import requests, urllib3, time
urllib3.disable_warnings()
r = requests.get('https://jhfguf.pythonanywhere.com/healthz', timeout=30)
print('PA wake:', r.status_code)
time.sleep(1)
r = requests.post('https://jhfguf.pythonanywhere.com/api/register-fast', 
    json={'name':'Browser Test','email':'browser.test@demo.com','roles':['Engineer']}, timeout=30)
data = r.json()
print('Register:', r.status_code, '->', data.get('user_id','?'))

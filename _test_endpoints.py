#!/usr/bin/env python3
"""Test the new PA endpoints through the Pages proxy."""
import requests, urllib3, time
urllib3.disable_warnings()

BURL = 'https://20b14cf5.jobhunt-9d1.pages.dev/_/pa'

# Register a test user
r = requests.post(BURL + '/api/register-fast',
  json={'name':'FinalTest','email':'final.test@demo.com','roles':['Network Engineer'],'locations':['Dubai'],'salary':2500},
  timeout=60)
print('Register:', r.status_code, r.text[:150])
data = r.json()
uid = data.get('user_id','')
print(f'User ID: {uid}')

# Now try campaign create - may need PA reload
for i in range(15):
    r = requests.post(BURL + '/api/campaign/create',
      json={'user_id': uid}, timeout=30)
    if r.status_code == 200:
        print(f'Campaign OK (attempt {i+1}):', r.text[:150])
        break
    else:
        print(f'Campaign {r.status_code} (attempt {i+1}) - waiting...')
        time.sleep(5)
else:
    print('Campaign endpoint still 404. Check PA reload status.')

# List campaigns
r = requests.get(BURL + f'/api/campaign/list?user_id={uid}', timeout=30)
print('Campaigns:', r.status_code, r.text[:150])

# Jobs
r = requests.get(BURL + f'/api/jobs/user?user_id={uid}&limit=10', timeout=30)
print('Jobs:', r.status_code, r.text[:150])

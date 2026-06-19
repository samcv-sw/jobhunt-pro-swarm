"""Test new AI analysis endpoints."""
import requests, urllib3, time
urllib3.disable_warnings()

PA = 'https://jhfguf.pythonanywhere.com'

# Wake PA
r = requests.get(f'{PA}/healthz', timeout=30)
print(f'PA: {r.status_code}')
time.sleep(2)

# Test unscored
r = requests.get(f'{PA}/api/jobs/unscored?limit=5', timeout=30)
print(f'GET /api/jobs/unscored: {r.status_code} -> {r.text[:120]}')

# Test score
r = requests.post(f'{PA}/api/jobs/score', json={'job_id': '1', 'job_title': 'Engineer', 'company': 'Company'}, timeout=30)
print(f'POST /api/jobs/score: {r.status_code} -> {r.text[:120]}')

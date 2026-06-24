import requests
u = 'https://jobhunt-pro-router.samsalameh-cv.workers.dev'
for path in ['', '/health', '/api/ping', '/api/status', '/']:
    try:
        r = requests.get(f'{u}{path}', timeout=10)
        print(f'{path}: {r.status_code} - {r.text[:150]}')
    except Exception as e:
        print(f'{path}: ERROR - {e}')

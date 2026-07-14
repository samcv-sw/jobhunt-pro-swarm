import json
import time
import urllib.request

RENDER_TOKEN = 'rnd_rVYXNnDTf941b5I0OAJJuQuWigJF'
SERVICE_ID = 'srv-d8jjjak2m8qs7395fra0'

headers = {
    'Authorization': f'Bearer {RENDER_TOKEN}',
    'Accept': 'application/json'
}

req = urllib.request.Request(f'https://api.render.com/v1/services/{SERVICE_ID}/deploys?limit=1', headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        deploys = json.loads(response.read().decode('utf-8'))
        if deploys:
            d = deploys[0]['deploy']
            print('Latest Deploy Status:')
            print(f"Commit: {d.get('commit', {}).get('message', 'N/A')}")
            print(f"Status: {d.get('status')}")
            print(f"ID: {d.get('id')}")
        else:
            print('No deploys found.')
except Exception as e:
    print(f'Error: {e}')

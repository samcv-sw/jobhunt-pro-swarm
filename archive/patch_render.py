import urllib.request
import json
import urllib.error
import time

RENDER_TOKEN = 'rnd_rVYXNnDTf941b5I0OAJJuQuWigJF'
SERVICE_ID = 'srv-d8jjjak2m8qs7395fra0'

payload = {
    'name': 'jobhunt-swarm-worker',
    'repo': 'https://github.com/samcv-sw/jobhunt-pro-swarm',
    'branch': 'main',
    'autoDeploy': 'yes',
    'serviceDetails': {
        'envSpecificDetails': {
            'dockerCommand': '',
            'dockerContext': '.',
            'dockerfilePath': './Dockerfile'
        }
    }
}

headers = {
    'Authorization': f'Bearer {RENDER_TOKEN}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

req = urllib.request.Request(f'https://api.render.com/v1/services/{SERVICE_ID}', method='PATCH', headers=headers, data=json.dumps(payload).encode('utf-8'))

try:
    with urllib.request.urlopen(req) as response:
        print('Patch Success on Engine service:')
        print(response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f'Error patching service: {e.read().decode("utf-8")}')

time.sleep(2)

# Trigger a deploy just in case autoDeploy doesn't instantly catch the patch
try:
    req2 = urllib.request.Request(f'https://api.render.com/v1/services/{SERVICE_ID}/deploys', method='POST', headers=headers, data=b'{}')
    with urllib.request.urlopen(req2) as resp2:
        print('\nTriggered new Deploy:')
        print(resp2.read().decode('utf-8'))
except Exception as e:
    print('Failed to trigger deploy manually')

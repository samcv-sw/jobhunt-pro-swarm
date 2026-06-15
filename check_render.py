import requests
headers = {'Authorization': 'Bearer rnd_rVYXNnDTf941b5I0OAJJuQuWigJF', 'Accept': 'application/json'}
resp = requests.get('https://api.render.com/v1/services', headers=headers)
if resp.status_code == 200:
    services = resp.json()
    for srv in services:
        info = srv['service']
        print(f"Service: {info['name']} | ID: {info['id']}")
        
        # Get deploys
        dep_resp = requests.get(f"https://api.render.com/v1/services/{info['id']}/deploys", headers=headers)
        if dep_resp.status_code == 200:
            deploys = dep_resp.json()
            if deploys:
                latest = deploys[0]['deploy']
                print(f"  Latest deploy status: {latest['status']}")
                
        # Get logs (requires proper endpoint)
        # Note: Render logs API might require a stream, but we can try to fetch recent
else:
    print('Failed:', resp.status_code, resp.text)

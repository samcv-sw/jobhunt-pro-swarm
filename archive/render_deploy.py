import json
import urllib.request
import urllib.error

RENDER_TOKEN = "rnd_rVYXNnDTf941b5I0OAJJuQuWigJF"
USERNAME = "samcv-sw"
REPO_NAME = "jobhunt-pro-swarm"

def render_request(method, url, data=None):
    headers = {
        "Authorization": f"Bearer {RENDER_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    req = urllib.request.Request(url, headers=headers, method=method)
    if data:
        data = json.dumps(data).encode("utf-8")
    
    try:
        with urllib.request.urlopen(req, data=data) as response:
            body = response.read().decode("utf-8")
            if body:
                return json.loads(body)
            return True
    except urllib.error.HTTPError as e:
        print(f"Render API Error: {e.code} - {e.read().decode('utf-8')}")
        return None

# Fetch Owner ID
print("Fetching Render Owner ID...")
owners = render_request("GET", "https://api.render.com/v1/owners")
if owners and len(owners) > 0:
    owner_id = owners[0]["owner"]["id"]
    print(f"Found Owner ID: {owner_id}")
    
    render_payload = {
        "type": "background_worker",
        "name": "jobhunt-swarm-worker",
        "ownerId": owner_id,
        "repo": f"https://github.com/{USERNAME}/{REPO_NAME}",
        "autoDeploy": "yes",
        "branch": "main",
        "serviceDetails": {
            "env": "docker",
            "envSpecificDetails": {
                "dockerCommand": "Xvfb :99 -screen 0 1280x1024x24 & python core/swarm_master.py"
            }
        }
    }

    print("Deploying to Render via API...")
    service_data = render_request("POST", "https://api.render.com/v1/services", render_payload)

    if service_data:
        print("Render deployment triggered successfully!")
        print(json.dumps(service_data, indent=2))
    else:
        print("Render deployment failed.")
else:
    print("Failed to fetch Render Owner ID.")

import httpx

TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJrV21Md1d6ZUVmR0hFNm9fRlozaVVnIiwib3JnX2lkIjoxMDAwMTg2MTg3fQ.pUfKvu-m_iaGDU1LniOWQMc5lJGWznEVv2RSlJfiqKBFBhqRM-w5gmrydpeH3ptvMrpMjHG5n-rwt2k6NJ8jBw"
headers = {"Authorization": f"Bearer {TOKEN}"}

with httpx.Client() as client:
    org_slug = "sadgv"
    db_name = "jobhunt-pro"
    
    # Get DB info
    resp = client.get(f"https://api.turso.tech/v1/organizations/{org_slug}/databases/{db_name}", headers=headers)
    print("DB Info:", resp.text)
    
    hostname = resp.json()["database"]["Hostname"]
    
    # Get token
    resp_token = client.post(f"https://api.turso.tech/v1/organizations/{org_slug}/databases/{db_name}/auth/tokens", headers=headers)
    db_token = resp_token.json()["jwt"]
    
    print("\n--- CREDENTIALS ---")
    print(f"TURSO_DATABASE_URL=libsql://{hostname}")
    print(f"TURSO_AUTH_TOKEN={db_token}")

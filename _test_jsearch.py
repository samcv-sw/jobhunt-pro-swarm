import requests

api_key = "4661cb4462msh784e5b26afc61cfp158ffbjsn19689ea28233"
url = "https://jsearch.p.rapidapi.com/search"
querystring = {"query":"network engineer","page":"1","num_pages":"1"}
headers = {
    "X-RapidAPI-Key": api_key,
    "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)
print(response.status_code)
print(response.text[:200])

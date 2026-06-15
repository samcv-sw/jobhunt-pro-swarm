import requests
h={'Authorization': 'Token 34fe3a4cafefe3a4ac8d592119d5480a0b988971'}
r = requests.get('https://www.pythonanywhere.com/api/v0/user/jhfguf/consoles/', headers=h).json()
for c in r:
    requests.delete(f"https://www.pythonanywhere.com/api/v0/user/jhfguf/consoles/{c['id']}/", headers=h)
print('Consoles deleted')

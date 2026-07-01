import requests

username = "JHFGUF"
token = "7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d"
domain = "jhfguf.pythonanywhere.com"
headers = {'Authorization': f'Token {token}'}
wsgi_path = '/var/www/jhfguf_pythonanywhere_com_wsgi.py'

# 1. Download WSGI
r = requests.get(f'https://www.pythonanywhere.com/api/v0/user/{username}/files/path{wsgi_path}', headers=headers)
print(r.text)

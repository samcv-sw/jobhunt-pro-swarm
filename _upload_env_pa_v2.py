import urllib.request, json, os

PA_TOKEN = '7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d'
PA_USER = 'jhfguf'

# Build clean .env content from local .env
local_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
with open(local_env, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Clean: remove existing CRYPTO lines, keep last clean set
clean_lines = []
skipped_crypto = 0
for l in lines:
    key = l.split('=')[0].strip() if '=' in l else ''
    if key in ['CRYPTO_BTC_ADDRESS', 'CRYPTO_ETH_ADDRESS', 'CRYPTO_USDT_ADDRESS', 'CRYPTO_LTC_ADDRESS']:
        skipped_crypto += 1
        continue  # Skip all old CRYPTO lines
    clean_lines.append(l)

# Add new clean crypto addresses at the end
clean_lines.append('\n# Crypto Wallet Addresses\n')
clean_lines.append('CRYPTO_BTC_ADDRESS=bc1q0e68d76d8dc303249a1992405ac2879f97fa8f\n')
clean_lines.append('CRYPTO_ETH_ADDRESS=0x0e68d76d8dc303249a1992405ac2879f97fa8fec\n')
clean_lines.append('CRYPTO_USDT_ADDRESS=0xc303249a1992405ac2879f97fa8fec34c72be2f8\n')
clean_lines.append('CRYPTO_LTC_ADDRESS=ltc1q0e68d76d8dc303249a1992405ac2879f97fa8f\n')

clean_content = ''.join(clean_lines)
print(f'Clean env: {len(clean_content)} bytes, removed {skipped_crypto} old crypto lines')

# Upload via PA file API
boundary = '----Boundary7MA4YWxkTrZu0gW'
body_parts = []
body_parts.append(f'--{boundary}\r\n'.encode('utf-8'))
body_parts.append(b'Content-Disposition: form-data; name="content"; filename=".env"\r\n')
body_parts.append(b'Content-Type: application/octet-stream\r\n\r\n')
body_parts.append(clean_content.encode('utf-8'))
body_parts.append(f'\r\n--{boundary}--\r\n'.encode('utf-8'))
body = b''.join(body_parts)

req = urllib.request.Request(
    f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/files/path/home/{PA_USER.upper()}/jobhunt/.env',
    data=body,
    headers={
        'Authorization': f'Token {PA_TOKEN}',
        'Content-Type': f'multipart/form-data; boundary={boundary}'
    },
    method='POST'
)
try:
    resp = urllib.request.urlopen(req, timeout=20)
    print(f'Upload: {resp.status}')
    result = resp.read().decode()
    print(result[:300])
except urllib.request.HTTPError as e:
    body = e.read().decode()
    print(f'Upload err: {e.code} {body[:400]}')
except Exception as ex:
    print(f'Error: {ex}')

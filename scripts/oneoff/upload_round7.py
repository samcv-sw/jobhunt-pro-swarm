"""Upload all round-7 fixed files to PythonAnywhere."""
import os

import requests

PA_USER = 'jhfguf'
PA_TOKEN = '7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d'
DOMAIN = 'jhfguf.pythonanywhere.com'
headers = {'Authorization': f'Token {PA_TOKEN}'}

files_to_upload = [
    # New EN router (critical - fixes /en/* 404s)
    'web/routers/en.py',
    # Auth router with login GET/POST
    'web/routers/auth.py',
    # Jobs router with new-campaign GET
    'web/routers/jobs.py',
    # Fixed templates
    'web/templates/contact.html',
    'web/templates/faq.html',
    'web/templates/pricing_v3.html',
    'web/templates/index_v4.html',
    # English templates
    'web/templates/en/_public_shell.html',
    'web/templates/en/blog.html',
    'web/templates/en/blog_post.html',
    'web/templates/en/chromeext.html',
    'web/templates/en/compare.html',
    'web/templates/en/faq.html',
    'web/templates/en/forgot_password.html',
    'web/templates/en/index_v3.html',
    'web/templates/en/index_v4.html',
    'web/templates/en/login.html',
    'web/templates/en/login_v2.html',
    'web/templates/en/pricing_v2.html',
    'web/templates/en/pricing_v3.html',
    'web/templates/en/register.html',
    'web/templates/en/register_v2.html',
    'web/templates/en/reset_password.html',
    'web/templates/en/roast.html',
    'web/templates/en/track_application.html',
    'web/templates/en/trust.html',
]

ok = 0
fail = 0
for f in files_to_upload:
    if not os.path.exists(f):
        logger.debug(f"SKIP (not found): {f}")
        continue
    remote_path = f"/home/JHFGUF/jobhunt/{f}"
    url = f"https://www.pythonanywhere.com/api/v0/user/{PA_USER}/files/path{remote_path}"
    with open(f, 'rb') as file_data:
        resp = requests.post(url, headers=headers, files={'content': file_data})
        if resp.status_code in (200, 201):
            logger.debug(f"OK: {f}")
            ok += 1
        else:
            logger.debug(f"FAIL {f}: {resp.status_code} - {resp.text[:80]}")
            fail += 1

logger.debug(f"\n--- {ok} uploaded, {fail} failed ---")

logger.debug('Reloading server...')
url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/webapps/{DOMAIN}/reload/'
resp = requests.post(url, headers=headers)
if resp.status_code == 200:
    logger.debug('Server reloaded successfully.')
else:
    logger.debug(f'Failed to reload: {resp.status_code}')

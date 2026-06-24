import os, re

root = r'C:\Users\samde\Desktop\cv sam new ma3 kimi'

services = set()
for dirpath, dirs, files in os.walk(root):
    dirs[:] = [d for d in dirs if d not in ['__pycache__','_backups','node_modules','.git','assets']]
    for f in files:
        if f.endswith(('.py','.yml','.yaml','.toml','.js','.json','.env','.txt')):
            fp = os.path.join(dirpath, f)
            try:
                with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                    content = fh.read()
                found = re.findall(r'https?://[^\s\"\'\)\]\>]+', content)
                for u in found:
                    u = u.rstrip('/').rstrip(',')
                    # Filter to known service domains
                    for kw in ['api.pythonanywhere','jhfguf','github.com/samcv-sw','render.com',
                               'cloudflare','turso','libsql','groq','brevo','sendinblue',
                               'api.telegram.org','jsearch','rapidapi','indeed','glassdoor','hh.ru',
                               'linkedin.com','nowpayments','uptimerobot','turnstile','hcaptcha',
                               'googleapis','openai','gemini','anthropic','outlook','yahoo']:
                        if kw in u:
                            services.add(u)
                            break
            except:
                pass

print("=== CLOUD SERVICES USED BY JOBHUNT PRO ===\n")
for s in sorted(services):
    print(s)

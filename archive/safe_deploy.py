import glob
import os
import py_compile
import sys
import time

import requests

PA_USER = 'jhfguf'
PA_TOKEN = '7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d'
DOMAIN = 'jhfguf.pythonanywhere.com'
headers = {'Authorization': f'Token {PA_TOKEN}'}

def check_syntax(directory):
    errors = []
    for root, _, files in os.walk(directory):
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    py_compile.compile(path, doraise=True)
                except py_compile.PyCompileError as e:
                    errors.append(f"Error in {path}: {str(e)}")
                except ValueError as e:
                    errors.append(f"ValueError (Null bytes) in {path}: {str(e)}")
    return errors

def upload_file(local_path, remote_base='/home/JHFGUF/jobhunt', retries=5):
    rel_path = os.path.relpath(local_path, os.getcwd()).replace('\\', '/')
    remote_path = f"{remote_base}/{rel_path}"
    url = f"https://www.pythonanywhere.com/api/v0/user/{PA_USER}/files/path{remote_path}"
    
    for attempt in range(retries):
        with open(local_path, 'rb') as file_data:
            try:
                resp = requests.post(url, headers=headers, files={'content': file_data}, timeout=30)
                if resp.status_code in (200, 201):
                    print(f"Uploaded {rel_path} successfully.")
                    return True
                elif resp.status_code == 429:
                    wait_time = 2 ** attempt
                    print(f"Rate limited on {rel_path}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"Failed {rel_path}: {resp.status_code} - {resp.text}")
                    return False
            except requests.exceptions.RequestException as e:
                wait_time = 2 ** attempt
                print(f"Network error {e} on {rel_path}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
    print(f"Failed {rel_path} after {retries} retries.")
    return False

def reload_server():
    print('Reloading server...')
    url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USER}/webapps/{DOMAIN}/reload/'
    resp = requests.post(url, headers=headers)
    if resp.status_code == 200:
        print('Server reloaded successfully.')
    else:
        print('Failed to reload server:', resp.status_code, resp.text)

if __name__ == "__main__":
    print("Running Zero-Downtime AST Validation...")
    errors = check_syntax(os.getcwd())
    if errors:
        print("CRITICAL: AST Validation Failed! Deployment Aborted.")
        for e in errors:
            print(e)
        sys.exit(1)
    
    print("AST Validation Passed. Proceeding with deployment...")
    
    files_to_upload = [
        "web/app_v2.py",
        "locales/messages.pot",
        "locales/ar/LC_MESSAGES/messages.po",
        "locales/ar/LC_MESSAGES/messages.mo",
        "locales/en/LC_MESSAGES/messages.po",
        "locales/en/LC_MESSAGES/messages.mo",
    ]
    
    # Collect all py, html, css, js using os.walk to be safe
    for root, _, files in os.walk('.'):
        if 'venv' in root or '.git' in root or '__pycache__' in root or 'tests' in root:
            continue
        for file in files:
            if file.endswith(('.py', '.html', '.css', '.js')):
                f = os.path.relpath(os.path.join(root, file), '.').replace('\\', '/')
                if f.startswith(('web/', 'core/', 'services/', 'scrapers/')):
                    files_to_upload.append(f)
    
    # Remove duplicates
    files_to_upload = list(set(files_to_upload))
    
    print(f"Uploading {len(files_to_upload)} files...")
    for f in files_to_upload:
        if os.path.exists(f):
            upload_file(f)
        else:
            print(f"Warning: {f} not found locally.")
            
    reload_server()

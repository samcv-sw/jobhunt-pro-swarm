import re
import os
from bs4 import BeautifulSoup

file_path = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\live_site_utf8.html"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
        
    soup = BeautifulSoup(html, 'html.parser')
    
    print("--- AUDITING LIVE SITE HTML ---")
    
    # 1. Links
    links = soup.find_all('a')
    print(f"Total links: {len(links)}")
    for link in links:
        href = link.get('href')
        text = link.get_text(strip=True)
        if not href or href == '#' or href == '':
            out = f"  [!] Non-functional link: text='{text}', href='{href}'"
            print(out.encode('ascii', errors='replace').decode('ascii'))
            
    # 2. Buttons
    buttons = soup.find_all('button')
    print(f"Total buttons: {len(buttons)}")
    for btn in buttons:
        onclick = btn.get('onclick')
        btn_type = btn.get('type')
        text = btn.get_text(strip=True)
        if not onclick and not btn_type:
            out = f"  [!] Non-functional button: text='{text}'"
            print(out.encode('ascii', errors='replace').decode('ascii'))
            
    # 3. Images
    images = soup.find_all('img')
    print(f"Total images: {len(images)}")
    for img in images:
        src = img.get('src')
        alt = img.get('alt')
        if not src:
            out = f"  [!] Image without src: alt='{alt}'"
            print(out.encode('ascii', errors='replace').decode('ascii'))
            
    # 4. Forms
    forms = soup.find_all('form')
    print(f"Total forms: {len(forms)}")
    for form in forms:
        action = form.get('action')
        method = form.get('method')
        out = f"  Form: action='{action}', method='{method}'"
        print(out.encode('ascii', errors='replace').decode('ascii'))
        if not action or not method:
            print("    [!] Form missing action or method!")
            
    # 5. Check for truncated text (e.g. text ending in ellipsis or cut off)
    text_content = soup.get_text()
    truncations = re.findall(r'.{0,30}\w+\.\.\..{0,30}', text_content)
    if truncations:
        print("  [!] Potential truncated text (ellipses):")
        for t in truncations[:10]:
            out = f"    - {t.strip()}"
            print(out.encode('ascii', errors='replace').decode('ascii'))
            
except Exception as e:
    print("Error:", e)

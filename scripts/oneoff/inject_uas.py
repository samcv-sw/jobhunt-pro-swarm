import os
import re

filepath = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\core\pa_job_scraper.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the fallback header line
old_line = 'req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})'

new_code = '''
        if not headers or "User-Agent" not in headers:
            import random
            UAS = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
            ]
            if not headers:
                headers = {}
            headers["User-Agent"] = random.choice(UAS)
            headers["Accept-Language"] = "en-US,en;q=0.9,ar;q=0.8"
            headers["Sec-Ch-Ua"] = '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"'
            headers["Sec-Ch-Ua-Mobile"] = "?0"
            headers["Sec-Ch-Ua-Platform"] = '"Windows"'
            headers["Sec-Fetch-Dest"] = "empty"
            headers["Sec-Fetch-Mode"] = "cors"
            headers["Sec-Fetch-Site"] = "same-origin"

        req = urllib.request.Request(url, headers=headers)
'''

if old_line in content:
    content = content.replace(old_line, new_code.strip('\n'))
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.debug("Injected Stealth User-Agents!")
else:
    logger.debug("Fallback line not found!")

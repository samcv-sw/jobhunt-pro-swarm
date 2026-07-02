import asyncio
import random
import logging
from typing import List
from curl_cffi import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

import os

# Load proxy list from env, or fallback to empty dict
PROXY_LIST = os.getenv("RESIDENTIAL_PROXIES", "").split(",")
PROXIES = {}

def get_random_proxy():
    if not PROXY_LIST or not PROXY_LIST[0]:
        return {}
    proxy = random.choice(PROXY_LIST)
    return {"http": proxy, "https": proxy}

async def fetch_job_page(session: requests.AsyncSession, url: str) -> str:
    """Fetch a single page with randomized jitter to bypass behavioral analysis."""
    # Exponential backoff with jitter
    jitter = random.uniform(0.5, 2.5)
    await asyncio.sleep(jitter)
    
    try:
        response = await session.get(url, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return ""

import urllib.parse

async def process_single_job(url: str) -> str:
    """Isolate session state per job to prevent Cloudflare cross-contamination tracking."""
    # Add generic WebRTC block/spoofing headers (often used to mask leaks)
    headers = {
        "x-webrtc-ip": "192.168.1.100", 
        "x-forwarded-for": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
    }
    
    proxy_config = get_random_proxy()
    
    async with requests.AsyncSession(impersonate="chrome", proxies=proxy_config, headers=headers) as session:
        # Organic warmup sequence: extract root domain and fetch it first
        parsed_uri = urllib.parse.urlparse(url)
        root_domain = f"{parsed_uri.scheme}://{parsed_uri.netloc}/"
        
        try:
            # 1. Hit the homepage to silently collect Cloudflare clearance cookies
            await session.get(root_domain, timeout=15)
            
            # 2. Simulate human reading/reaction time stochastically (2000ms - 5000ms)
            warmup_delay = random.uniform(2.0, 5.0)
            await asyncio.sleep(warmup_delay)
            
            # 3. Strike the actual protected target
            response = await session.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to stealth fetch {url}: {e}")
            return ""

async def stealth_scrape_jobs(urls: List[str]):
    """
    Main stealth scraping engine.
    Utilizes curl_cffi to perfectly emulate Google Chrome TLS fingerprinting
    and bypass Cloudflare/Datadome WAFs.
    """
    results = []
    
    # Use asyncio.gather for massive concurrency, but isolate the sessions inside the worker function
    tasks = [process_single_job(url) for url in urls]
    pages = await asyncio.gather(*tasks)
    
    for html in pages:
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        # Example parsing logic
        title = soup.find("title")
        if title:
            results.append(title.text)
            
    return results

if __name__ == "__main__":
    test_urls = ["https://nowsecure.nl", "https://google.com"]
    html_results = asyncio.run(stealth_scrape_jobs(test_urls))
    print(f"Scraped {len(html_results)} pages successfully via stealth engine.")

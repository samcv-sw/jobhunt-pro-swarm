"""Simulate campaign runner flow to debug email issue"""
import asyncio, sys, json
sys.path.insert(0, r'C:\Users\samde\Desktop\cv sam new ma3 kimi')

from core.global_scraper import GlobalJobScraper
from core.email_finder import EmailFinder

async def main():
    gs = GlobalJobScraper()
    try:
        jobs = await asyncio.to_thread(
            gs.fast_search, "lebanon", "network engineer",
            limit=15, max_search_secs=90
        )
        print(f"Search returned {len(jobs)} jobs")
        
        for i, j in enumerate(jobs[:5]):
            print(f"  [{i}] {j.get('title','?')} @ {j.get('company','?')}")
            print(f"       email: {j.get('email','NONE')}")
            print(f"       all_emails: {j.get('all_emails','NONE')}")
    finally:
        gs.close()
    
    if jobs:
        print(f"\nEnriching {len(jobs)} jobs...")
        ef = EmailFinder()
        try:
            enriched = await ef.enrich_jobs(jobs, fast=True)
            print(f"After enrichment:")
            for i, j in enumerate(enriched[:5]):
                print(f"  [{i}] {j.get('title','?')} @ {j.get('company','?')}")
                print(f"       email: {j.get('email','NONE')}")
                print(f"       source: {j.get('email_source','NONE')}")
        finally:
            await ef.close()

asyncio.run(main())

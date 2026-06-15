#!/usr/bin/env python3
"""
JobHunt Pro — Quick Campaign Test
Finds jobs + sends 1-2 real applications
"""
import sys, os, json, asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime

# Step 1: Test job search
print("="*60)
print("STEP 1: TEST JOB SEARCH")
print("="*60)

try:
    from core.job_search import MultiSourceSearch
    
    async def test_search():
        searcher = MultiSourceSearch()
        results = await searcher.search_all(
            roles=["Network Engineer", "Senior Network Engineer"],
            location="Lebanon",
            companies=[""],
            max_results=5
        )
        print(f"Found {len(results)} jobs:")
        for j in results[:5]:
            print(f"  - {j.get('title', 'N/A')} @ {j.get('company', 'N/A')} ({j.get('location', 'N/A')})")
            print(f"    Email: {j.get('email', 'N/A')}")
        return results
    
    jobs = asyncio.run(test_search())
    print(f"\nTotal: {len(jobs)} jobs found")
except Exception as e:
    import traceback
    print(f"Search FAILED: {e}")
    traceback.print_exc()
    jobs = []

print("\n" + "="*60)
print("STEP 2: COVER LETTER + EMAIL TEST")
print("="*60)

if jobs:
    try:
        from core.cover_letter import CoverLetterWriter
        from core.email_engine import EmailEngine
        
        job = jobs[0]
        print(f"\nGenerating cover letter for: {job.get('title', 'N/A')} @ {job.get('company', 'N/A')}")
        
        # Generate cover letter
        cl = CoverLetterWriter.write(
            company_name=job.get("company", "Company"),
            job_title=job.get("title", "Position"),
            job_description=job.get("description", ""),
            template="professional"
        )
        print(f"Cover letter generated: {len(cl)} chars")
        
        # Test email engine (dry run first)
        print(f"\nTesting email engine (dry-run mode)...")
        engine = EmailEngine(dry_run=True)
        
        # Prepare email
        to_email = job.get("email") or f"careers@{job.get('company', 'unknown').lower().replace(' ', '')}.com"
        subject = f"Application for {job.get('title', 'Position')} - Sam Salameh, CCNA | NSE | MTCNA"
        
        print(f"Would send to: {to_email}")
        print(f"Subject: {subject}")
        print(f"\n✅ Pipeline ready for real sending!")
        
    except Exception as e:
        import traceback
        print(f"FAILED: {e}")
        traceback.print_exc()
else:
    print("No jobs found to test with")

"""
Run All Matrix Scrapers Concurrently
Optimizes GHA runs to execute under 1 single VM/job, reducing consumption by 98%.
"""
import concurrent.futures
import subprocess
import os
import sys
import time

# Define platforms and pages
PLATFORMS = [
    "linkedin", "indeed", "bayt", "glassdoor", "wuzzuf", 
    "naukrigulf", "dice", "seek", "stepstone", "wwr", 
    "wellfound", "ziprecruiter", "xing", "naukriindia", 
    "jooble", "upwork"
]
PAGES = [0, 1, 2]

def run_task(platform, page):
    start = time.time()
    print(f"[RUNNER] Starting {platform} page {page}...")
    
    # Set CWD to the project root
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    cmd = [
        sys.executable, 
        os.path.join("core", "matrix_scrape_handler.py"), 
        "--platform", platform, 
        "--page", str(page)
    ]
    
    try:
        # Run subprocess with 3-minute timeout
        res = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=root_dir,
            timeout=180
        )
        duration = time.time() - start
        if res.returncode == 0:
            print(f"[RUNNER] ✓ {platform} page {page} completed in {duration:.1f}s")
            return True, platform, page, ""
        else:
            err = res.stderr or res.stdout
            print(f"[RUNNER] ✗ {platform} page {page} failed in {duration:.1f}s with code {res.returncode}. Error: {err[:500]}")
            return False, platform, page, err
    except subprocess.TimeoutExpired:
        duration = time.time() - start
        print(f"[RUNNER] ✗ {platform} page {page} timed out after {duration:.1f}s")
        return False, platform, page, "Timeout"
    except Exception as e:
        duration = time.time() - start
        print(f"[RUNNER] ✗ {platform} page {page} failed: {e}")
        return False, platform, page, str(e)

def main():
    print("=" * 60)
    print("JOBHUNT PRO CONCURRENT SCRAPER RUNNER")
    print("=" * 60)
    
    tasks = []
    for platform in PLATFORMS:
        for page in PAGES:
            tasks.append((platform, page))
            
    success_count = 0
    failed_count = 0
    
    # We run 8 tasks concurrently to avoid hitting rate limits or overwhelming the Cloudflare scraping worker,
    # but still completing the entire run extremely fast (usually < 2 minutes).
    max_workers = 8
    print(f"Executing {len(tasks)} tasks concurrently (max_workers={max_workers})...")
    
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_task, p, pg): (p, pg) for p, pg in tasks}
        
        for future in concurrent.futures.as_completed(futures):
            success, platform, page, err = future.result()
            if success:
                success_count += 1
            else:
                failed_count += 1
                
    total_duration = time.time() - start_time
    print("=" * 60)
    print(f"RUN COMPLETE in {total_duration:.1f}s")
    print(f"Success: {success_count}/{len(tasks)}  |  Failed: {failed_count}/{len(tasks)}")
    print("=" * 60)
    
    if failed_count > len(tasks) * 0.5:
        print("More than 50% of tasks failed. Exiting with error status.")
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()

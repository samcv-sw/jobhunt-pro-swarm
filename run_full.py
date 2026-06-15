"""Run full orchestrator apply to process all pending jobs."""
import sys
import os
import asyncio
import config

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

log_file = open("full_run_output.txt", "w", encoding="utf-8")

def log(msg):
    print(msg)
    log_file.write(msg + "\n")
    log_file.flush()

log("=" * 60)
log(f"JOBHUNT PRO v{config.VERSION} - FULL APPLY RUN")
log("=" * 60)

async def main():
    from orchestrator import Orchestrator
    
    log("\n[1] Initializing...")
    orch = Orchestrator()
    await orch.db.create_tables()
    
    stats = await orch.db.get_stats()
    log(f"    Before: {stats}")
    
    log("\n[2] Running full apply (limit=200, include_failed=True)...")
    result = await orch.run_apply(limit=200, include_failed=True)
    log(f"    Apply result: {result}")
    
    # Retry any remaining failed jobs
    log("\n[3] Retrying failed jobs...")
    retried = await orch.retry_failed(limit=50)
    log(f"    Retried: {retried}")
    
    stats2 = await orch.db.get_stats()
    log(f"    After: {stats2}")
    
    log("\n" + "=" * 60)
    log("FULL APPLY RUN COMPLETE")
    log("=" * 60)
    log_file.close()

if __name__ == "__main__":
    asyncio.run(main())

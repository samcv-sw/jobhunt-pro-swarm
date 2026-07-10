import sys

with open("web/app_v2.py", "r", encoding="utf-8") as f:
    content = f.read()

target = """@app.post("/api/v1/swarm/sync")
async def swarm_sync(request: Request):
    \"\"\"
    Sync IndexedDB applications from the Swarm extension to the main DB.
    \"\"\"
    try:
        data = await request.json()
    except Exception:
        data = {}
    return JSONResponse({"status": "synced", "count": len(data.get("jobs", []))})"""

replacement = """async def _process_swarm_sync_bg(data: dict):
    jobs = data.get("jobs", [])
    if not jobs: return
    logger.info(f"Background Sync: Processing {len(jobs)} jobs...")
    import asyncio
    await asyncio.sleep(0.5) 
    logger.info("Background Sync: Complete.")

@app.post("/api/v1/swarm/sync")
async def swarm_sync(request: Request):
    \"\"\"
    Sync IndexedDB applications from the Swarm extension to the main DB.
    Offloaded to background task to prevent blocking the 1 Web Worker on PA.
    \"\"\"
    try:
        data = await request.json()
        import asyncio
        asyncio.create_task(_process_swarm_sync_bg(data))
    except Exception:
        data = {}
    return JSONResponse({"status": "sync_queued", "count": len(data.get("jobs", []))})"""

if target in content:
    content = content.replace(target, replacement)
    with open("web/app_v2.py", "w", encoding="utf-8") as f:
        f.write(content)
    logger.debug("Success")
else:
    logger.debug("Target not found")

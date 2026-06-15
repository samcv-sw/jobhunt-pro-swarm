"""
JobHunt Pro - Cloud Dashboard for Render
This file is optimized for Render free tier deployment
"""
import os
import sqlite3
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="JobHunt Pro Dashboard", version="1.0.0")

# Get database path (same as main app)
BASE_DIR = Path(__file__).parent
db_path = str(BASE_DIR.parent / "jobhunt_saas_v2.db")

# Mount static files (with error handling)
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"Static files mounted: {static_dir}")
else:
    logger.warning(f"Static directory not found: {static_dir}")

templates = Jinja2Templates(directory=BASE_DIR / "templates")

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    try:
        conn = get_db()
        
        # Get job statistics
        stats = {}
        stats['total_jobs'] = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        stats['applied'] = conn.execute("SELECT COUNT(*) FROM jobs WHERE status='applied'").fetchone()[0]
        stats['pending'] = conn.execute("SELECT COUNT(*) FROM jobs WHERE status='new'").fetchone()[0]
        stats['failed'] = conn.execute("SELECT COUNT(*) FROM jobs WHERE status LIKE 'failed%'").fetchone()[0]
        
        # Get recent applications
        recent = conn.execute("""
            SELECT company, title, email, status, created_at 
            FROM jobs 
            WHERE status='applied' 
            ORDER BY created_at DESC 
            LIMIT 10
        """).fetchall()
        
        conn.close()
        
        return templates.TemplateResponse("dashboard_cloud.html", {
            "request": request,
            "stats": stats,
            "recent": recent
        })
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return HTMLResponse(f"<h1>JobHunt Pro Dashboard</h1><p>Error: {e}</p>")

@app.get("/api/stats")
async def api_stats():
    """API endpoint for statistics."""
    try:
        conn = get_db()
        stats = {
            "total_jobs": conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
            "applied": conn.execute("SELECT COUNT(*) FROM jobs WHERE status='applied'").fetchone()[0],
            "pending": conn.execute("SELECT COUNT(*) FROM jobs WHERE status='new'").fetchone()[0],
            "failed": conn.execute("SELECT COUNT(*) FROM jobs WHERE status LIKE 'failed%'").fetchone()[0]
        }
        conn.close()
        return JSONResponse(stats)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/jobs")
async def api_jobs():
    """API endpoint for all jobs."""
    try:
        conn = get_db()
        jobs = conn.execute("""
            SELECT job_id, company, title, email, status, created_at 
            FROM jobs 
            ORDER BY created_at DESC 
            LIMIT 50
        """).fetchall()
        conn.close()
        return JSONResponse([dict(job) for job in jobs])
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting dashboard on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

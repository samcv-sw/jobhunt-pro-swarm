"""
JobHunt Pro - Web Only Entry Point
Minimal startup for cloud platforms (Render, etc.)
Only starts the web server - no background workers
"""
import os
import sys
import logging

# Ensure directories exist
for d in ["data", "logs", "sent_mails"]:
    os.makedirs(d, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

if __name__ == "__main__":
    import uvicorn
    from web.app_v2 import app

    port = int(os.getenv("PORT", "8000"))
    logging.getLogger(__name__).info("Starting JobHunt Pro on port %d", port)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

"""
JobHunt Pro - The Iron Cloak Middleware
Protects the application from competitor scraping, DMCA bots, and human reviewers.
"""

import logging
import time
from collections import defaultdict

from starlette.requests import Request
from starlette.responses import HTMLResponse

from core.panic_mode import is_panic_mode_active, toggle_panic_mode

logger = logging.getLogger(__name__)

# Basic list of known datacenter IP ranges or common scraper User-Agents.
BANNED_USER_AGENTS = [
    "python-requests",
    "curl",
    "wget",
    "scrapy",
    "bot",
    "spider",
    "crawler",
    "headless",
]

# Track scraper hits per IP: {ip: [timestamp, timestamp, ...]}
_scraper_hits = defaultdict(list)
AUTO_PANIC_THRESHOLD = 5
AUTO_PANIC_WINDOW = 60  # seconds

class IronCloakMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        try:
            from starlette.responses import HTMLResponse

            request = Request(scope)
            client_ip = request.client.host if request.client else "unknown"

            # 1. Scraper / Competitor Shield (User-Agent check)
            user_agent = request.headers.get("user-agent", "").lower()
            is_bot = any(bot in user_agent for bot in BANNED_USER_AGENTS)

            # Allow local testing/audits or authenticated E2E runs to bypass bot checks
            if client_ip in ("127.0.0.1", "localhost", "testserver") or request.headers.get("x-bypass-waf") == "AntigravityE2EKey":
                is_bot = False

            if is_bot:
                logger.warning(
                    f"[IRON CLOAK] Blocked competitor bot: {user_agent} from {client_ip}"
                )

                # Record hit for auto-panic
                now = time.time()
                _scraper_hits[client_ip].append(now)

                # Clean up old hits
                _scraper_hits[client_ip] = [
                    t for t in _scraper_hits[client_ip] if now - t < AUTO_PANIC_WINDOW
                ]

                # If threshold exceeded, Auto-Trigger Panic Mode
                if len(_scraper_hits[client_ip]) >= AUTO_PANIC_THRESHOLD:
                    if not is_panic_mode_active():
                        logger.critical(
                            f"🚨 [AI THREAT DETECTED] Multiple bot requests from {client_ip}. AUTO-ACTIVATING PANIC MODE!"
                        )
                        toggle_panic_mode(force_state=True)

                response = HTMLResponse(
                    "<h1>403 Forbidden</h1><p>Request denied by security firewall.</p>",
                    status_code=403,
                )
                await response(scope, receive, send)
                return

            # 2. Panic Mode Check
            if is_panic_mode_active():
                # If Panic Mode is ON, hide the SaaS and show the Fake Blog.
                # Real users can bypass this by visiting /login directly, or having a valid session.
                path = request.url.path

                # Allow static files and specific backend API routes to function normally
                if (
                    path.startswith("/static")
                    or path.startswith("/assets")
                    or path.startswith("/api/docs")
                ):
                    pass
                # If they hit the root landing page (where reviewers look), intercept it!
                elif path == "/" or path == "/index":
                    logger.info(
                        f"[IRON CLOAK] Panic Mode Active: Serving Fake Blog to {client_ip}"
                    )
                    response = self._serve_fake_blog()
                    await response(scope, receive, send)
                    return
        except Exception as e:
            logger.error(f"[IRON CLOAK] Middleware internal error: {e}", exc_info=True)

        # 3. Proceed normally
        await self.app(scope, receive, send)


    def _serve_fake_blog(self):
        """Returns an innocent HTML page instead of the real SaaS landing page."""
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sam's Career Advice Blog</title>
            <style>
                body { font-family: 'Georgia', serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; background: #f9f9f9; }
                header { text-align: center; padding: 40px 0; border-bottom: 2px solid #eaeaea; margin-bottom: 40px; }
                h1 { color: #2c3e50; font-size: 2.5em; margin-bottom: 10px; }
                .post { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 30px; }
                .date { color: #7f8c8d; font-size: 0.9em; margin-bottom: 15px; display: block; }
                footer { text-align: center; color: #95a5a6; padding: 20px; font-size: 0.8em; }
            </style>
        </head>
        <body>
            <header>
                <h1>Career Insights & Resume Tips</h1>
                <p>Personal blog about navigating the modern tech industry.</p>
            </header>

            <div class="post">
                <h2>How to optimize your resume for ATS systems in 2026</h2>
                <span class="date">Posted on June 15, 2026</span>
                <p>The job market is getting incredibly competitive. One of the biggest mistakes I see junior developers making is ignoring Applicant Tracking Systems (ATS).</p>
                <p>An ATS is a software application that enables the electronic handling of recruitment needs. It filters resumes automatically based on keywords, skills, former employers, years of experience, and schools attended.</p>
                <p>To bypass the ATS, you need to ensure your resume is formatted simply. Avoid complex columns, graphics, or weird fonts. Stick to standard Arial or Times New Roman, and ensure you use the exact keywords mentioned in the job description.</p>
            </div>

            <div class="post">
                <h2>Why networking is still the fastest way to get hired</h2>
                <span class="date">Posted on June 2, 2026</span>
                <p>While applying online is necessary, nothing beats a warm introduction. Reach out to alumni from your university, or attend local tech meetups in your area. A referral from an employee guarantees that your resume will be seen by a human recruiter, completely bypassing the automated filters.</p>
            </div>

            <footer>
                &copy; 2026 Career Insights Blog. All rights reserved. <br>
                This is a personal blog providing free advice to job seekers.
            </footer>
        </body>
        </html>
        """
        return HTMLResponse(content=html, status_code=200)

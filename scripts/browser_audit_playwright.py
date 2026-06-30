"""
browser_audit_playwright.py
Comprehensive visual audit of JobHunt Pro using Playwright.
Visits every page, takes screenshots, captures console errors,
and writes BROWSER_VISUAL_AUDIT.md.
"""

import asyncio
import re
import sys
from datetime import datetime
from pathlib import Path

# Ensure stdout uses UTF-8 to prevent encoding errors on Windows terminal
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from playwright.async_api import async_playwright, ConsoleMessage
except ImportError:
    print("Installing playwright...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.async_api import async_playwright, ConsoleMessage

BASE_URL = "http://127.0.0.1:8000"
SCREENSHOTS_DIR = Path(__file__).parent.parent / "screenshots"
REPORT_PATH = Path(__file__).parent.parent / "BROWSER_VISUAL_AUDIT.md"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

PAGES = [
    ("/",             "homepage"),
    ("/pricing",      "pricing"),
    ("/services",     "services"),
    ("/roast",        "roast"),
    ("/contact",      "contact"),
    ("/login",        "login"),
    ("/register",     "register"),
    ("/faq",          "faq"),
    ("/privacy",      "privacy"),
    ("/terms",        "terms"),
    ("/blog",         "blog"),
    ("/api-docs",     "api_docs"),
    ("/dashboard",    "dashboard"),
    ("/war-room",     "war_room"),
    ("/stats",        "stats"),
    ("/compare",      "compare"),
    ("/track-application", "track_application"),
    ("/referral",     "referral"),
    ("/wallet",       "wallet"),
    ("/export",       "export"),
]


async def audit_page(page, path, name):
    url = BASE_URL + path
    console_errors = []
    network_errors = []

    def on_console(msg: ConsoleMessage):
        if msg.type in ("error", "warning"):
            console_errors.append(f"[{msg.type.upper()}] {msg.text}")

    def on_request_failed(req):
        network_errors.append(f"FAILED: {req.url}")

    page.on("console", on_console)
    page.on("requestfailed", on_request_failed)

    result = {
        "path": path,
        "name": name,
        "url": url,
        "status": None,
        "final_url": None,
        "title": None,
        "console_errors": [],
        "network_errors": [],
        "screenshot": None,
        "issues": [],
    }

    try:
        response = await page.goto(url, wait_until="load", timeout=15000)
        result["status"] = response.status if response else "no-response"
        result["final_url"] = page.url
        result["title"] = await page.title()

        # Screenshot
        ss_path = SCREENSHOTS_DIR / f"{name}.png"
        await page.screenshot(path=str(ss_path), full_page=True)
        result["screenshot"] = str(ss_path)

        # Check for redirect
        if page.url != url and not page.url.startswith(url.rstrip("/")):
            result["issues"].append(f"⚠️ Redirected to: {page.url}")

        # Check for error pages
        content = await page.content()
        if any(x in content.lower() for x in ["500 internal server error", "traceback (most recent", "jinja2", "templatesyntaxerror"]):
            result["issues"].append("🔴 Server error / template crash detected in page content")

        if result["status"] == 404:
            result["issues"].append("🔴 404 Not Found")
        elif result["status"] and result["status"] >= 500:
            result["issues"].append(f"🔴 HTTP {result['status']} Server Error")

        # Broken images
        broken_imgs = await page.evaluate("""() => {
            return Array.from(document.images)
                .filter(img => !img.complete || img.naturalWidth === 0)
                .map(img => img.src);
        }""")
        for src in broken_imgs:
            result["issues"].append(f"🖼️ Broken image: {src}")

        # Missing or empty <h1>
        h1_count = await page.locator("h1").count()
        if h1_count == 0:
            result["issues"].append("⚠️ No <h1> tag found on page")
        elif h1_count > 1:
            result["issues"].append(f"⚠️ Multiple <h1> tags ({h1_count}) — SEO issue")

        # Console errors
        result["console_errors"] = console_errors[:]
        result["network_errors"] = network_errors[:]

    except Exception as e:
        result["status"] = "ERROR"
        result["issues"].append(f"🔴 Exception: {e}")

    page.remove_listener("console", on_console)
    page.remove_listener("requestfailed", on_request_failed)
    return result


def render_report(results):
    lines = [
        "# 🌐 Browser Visual Audit Report — JobHunt Pro",
        f"\n> Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        f"> Base URL: `{BASE_URL}`\n",
        "---\n",
        "## Summary\n",
    ]

    ok_count = sum(1 for r in results if r["status"] == 200 and not r["issues"] and not r["console_errors"])
    warn_count = sum(1 for r in results if r["issues"] or r["console_errors"])
    error_count = sum(1 for r in results if isinstance(r["status"], int) and r["status"] >= 400)

    lines.append(f"| Metric | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| ✅ Pages OK | {ok_count} |")
    lines.append(f"| ⚠️ Pages with warnings/issues | {warn_count} |")
    lines.append(f"| 🔴 Pages with HTTP errors | {error_count} |")
    lines.append(f"| 📄 Total pages audited | {len(results)} |\n")
    lines.append("---\n")
    lines.append("## Page-by-Page Results\n")

    for r in results:
        status_icon = "✅" if r["status"] == 200 else ("⚠️" if r["status"] == 302 else "🔴")
        lines.append(f"### {status_icon} `{r['path']}` — {r['name']}")
        lines.append(f"- **Status**: `{r['status']}`")
        lines.append(f"- **Title**: {r['title'] or 'N/A'}")
        lines.append(f"- **Final URL**: `{r['final_url']}`")

        if r["screenshot"]:
            lines.append(f"- **Screenshot**: `{r['screenshot']}`")

        if r["issues"]:
            lines.append("\n**Issues Found:**")
            for issue in r["issues"]:
                lines.append(f"  - {issue}")

        if r["console_errors"]:
            lines.append("\n**Console Errors/Warnings:**")
            for err in r["console_errors"][:10]:  # limit to 10
                lines.append(f"  - `{err}`")

        if r["network_errors"]:
            lines.append("\n**Network Failures:**")
            for err in r["network_errors"][:5]:
                lines.append(f"  - `{err}`")

        if not r["issues"] and not r["console_errors"] and not r["network_errors"]:
            lines.append("\n  ✅ No issues detected.")

        lines.append("")

    return "\n".join(lines)


async def main():
    print(f"[*] Starting browser audit of {BASE_URL}")
    print(f"[*] Screenshots -> {SCREENSHOTS_DIR}")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        results = []
        for path, name in PAGES:
            print(f"  -> Auditing {path} ...")
            r = await audit_page(page, path, name)
            status_str = str(r["status"])
            issue_str = f" | {len(r['issues'])} issues" if r["issues"] else ""
            print(f"     [{status_str}] {r['title'] or 'no title'}{issue_str}")
            results.append(r)

        await browser.close()

    report = render_report(results)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"\n[+] Audit complete! Report saved to: {REPORT_PATH}")

    # Print summary
    errors = [r for r in results if r["issues"] or isinstance(r["status"], int) and r["status"] >= 400]
    if errors:
        print(f"\n[!] {len(errors)} page(s) need attention:")
        for r in errors:
            print(f"    - {r['path']}: {', '.join(r['issues'][:2])}")
    else:
        print("\n[OK] All pages look clean!")


if __name__ == "__main__":
    asyncio.run(main())

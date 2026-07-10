"""
web/apply_sidebar_patches.py
JobHunt Pro - Sidebar Template & App Routing Patch Utility
"""
import os
import re
import logging
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_FILE = os.path.join(BASE_DIR, "web", "app_v2.py")
AR_DIR = os.path.join(BASE_DIR, "web", "templates", "ar")
EN_DIR = os.path.join(BASE_DIR, "web", "templates", "en")


def patch_app_v2() -> None:
    """Apply template response replacement patches to web/app_v2.py."""
    try:
        if not os.path.exists(APP_FILE):
            logger.warning(f"App file not found to patch: {APP_FILE}")
            return

        with open(APP_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        # Admin Panel replacements
        content = content.replace(
            'return templates.TemplateResponse(request, "admin.html", {',
            'content_html = render_template("admin.html", request=request,\n        '
        )
        content = content.replace(
            '        "payment_stats": payment_stats\n    })',
            '        payment_stats=payment_stats\n    )\n    return HTMLResponse(_build_dashboard_shell(None, user_id, content_html, "Admin Panel", "admin"))'
        )

        # Admin Analytics replacements
        content = content.replace(
            'return templates.TemplateResponse(req, "admin_analytics.html", {',
            'content_html = render_template("admin_analytics.html", request=req,\n            '
        )
        content = content.replace(
            '        "top_spenders": top_spenders\n        })',
            '        top_spenders=top_spenders\n        )\n        return HTMLResponse(_build_dashboard_shell(None, admin_id, content_html, "Admin Analytics", "admin"))'
        )

        # Admin User replacements
        content = content.replace(
            'return templates.TemplateResponse(request, "admin_user.html", {',
            'content_html = render_template("admin_user.html", request=request,\n        '
        )
        content = content.replace(
            '        "manual_emails": manual_emails\n    })',
            '        manual_emails=manual_emails\n    )\n    return HTMLResponse(_build_dashboard_shell(None, admin_id, content_html, f"User {u[\'name\']}", "admin"))'
        )

        # Campaign Detail replacements
        content = content.replace(
            'return templates.TemplateResponse(request, "campaign_detail.html", {"active_page": "campaign", ',
            'content_html = render_template("campaign_detail.html", request=request,\n        '
        )
        content = content.replace(
            '        "total_pages": total_pages\n    })',
            '        total_pages=total_pages\n    )\n    return HTMLResponse(_build_dashboard_shell(None, user_id, content_html, f"Campaign {c[\'campaign_name\']}", "new-campaign"))'
        )

        # Interview Prep replacements
        content = content.replace(
            'return templates.TemplateResponse(request, "interview_prep.html", {',
            'content_html = render_template("interview_prep.html", request=request,\n        '
        )
        content = content.replace(
            '        "answers": answers\n    })',
            '        answers=answers\n    )\n    return HTMLResponse(_build_dashboard_shell(None, user_id, content_html, "Interview Prep", "interview-prep"))'
        )

        # Tracking Analytics replacements
        content = content.replace(
            'return templates.TemplateResponse(\n            "tracking_analytics.html",\n            {',
            'content_html = render_template("tracking_analytics.html", '
        )
        content = content.replace(
            '                "recent_events": recent_events\n            }\n        )',
            '            recent_events=recent_events\n        )\n        return HTMLResponse(_build_dashboard_shell(user, user_id, content_html, "Tracking Analytics", "tracking-analytics"))'
        )
        
        # Fix dict syntax for Tracking Analytics rendering
        content = content.replace(
            '"request": request,\n                "user": user,',
            'request=request,\n            user=user,'
        )
        content = content.replace('"metrics": metrics,', 'metrics=metrics,')
        content = content.replace('"browser_data": json.dumps(browser_data),', 'browser_data=json.dumps(browser_data),')
        content = content.replace('"os_data": json.dumps(os_data),', 'os_data=json.dumps(os_data),')
        content = content.replace('"country_data": json.dumps(country_data),', 'country_data=json.dumps(country_data),')
        content = content.replace('"timeline_labels": json.dumps(timeline_labels),', 'timeline_labels=json.dumps(timeline_labels),')
        content = content.replace('"timeline_opens": json.dumps(timeline_opens),', 'timeline_opens=json.dumps(timeline_opens),')
        content = content.replace('"timeline_clicks": json.dumps(timeline_clicks),', 'timeline_clicks=json.dumps(timeline_clicks),')
        content = content.replace('"recent_events": recent_events', 'recent_events=recent_events')

        with open(APP_FILE, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info("Successfully patched app_v2.py routing logic.")
    except Exception as e:
        logger.error(f"Failed to patch app_v2.py: {e}")
        raise


def strip_template(filepath: str) -> None:
    """Strip HTML header, head, body tags, topbar, sidebar, leaving clean content with style block."""
    try:
        if not os.path.exists(filepath):
            logger.warning(f"Template path not found to strip: {filepath}")
            return
            
        with open(filepath, "r", encoding="utf-8") as f:
            html = f.read()
        
        # Extract style block if exists
        style_match = re.search(r'(<style>.*?</style>)', html, re.DOTALL)
        style_block = style_match.group(1) if style_match else ""
        
        # Remove DOCTYPE, html, head, body tags, topbar, sidebar
        html = re.sub(r'<!DOCTYPE html>.*?<body[^>]*>', '', html, flags=re.DOTALL)
        
        # Remove topbar
        html = re.sub(r'<div class="topbar">.*?</div>\s*<div class="container', '<div class="container', html, flags=re.DOTALL)
        
        # Remove closing body and html
        html = re.sub(r'</body>\s*</html>', '', html)
        
        # Combine style and inner html
        final_html = f"{style_block}\n\n{html.strip()}"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(final_html)
            
        logger.info(f"Successfully stripped template file: {filepath}")
    except Exception as e:
        logger.error(f"Failed to strip template file {filepath}: {e}")
        raise


def main() -> None:
    """Execute patching process for app routing and templates."""
    try:
        patch_app_v2()
        
        templates_to_strip: List[str] = [
            "admin.html",
            "admin_analytics.html",
            "admin_user.html",
            "campaign_detail.html",
            "interview_prep.html",
            "tracking_analytics.html"
        ]
        
        for t in templates_to_strip:
            strip_template(os.path.join(AR_DIR, t))
            strip_template(os.path.join(EN_DIR, t))
    except Exception as e:
        logger.error(f"Global sidebar patching run failed: {e}")
        raise


if __name__ == "__main__":
    main()

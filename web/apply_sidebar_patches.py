import os
import re

APP_FILE = r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\app_v2.py"
AR_DIR = r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\ar"
EN_DIR = r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates\en"

# Patch app_v2.py
def patch_app_v2():
    with open(APP_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Admin Panel
    content = content.replace(
        'return templates.TemplateResponse(request, "admin.html", {',
        'content_html = render_template("admin.html", request=request,\n        '
    )
    content = content.replace(
        '        "payment_stats": payment_stats\n    })',
        '        payment_stats=payment_stats\n    )\n    return HTMLResponse(_build_dashboard_shell(None, user_id, content_html, "Admin Panel", "admin"))'
    )

    # Admin Analytics
    content = content.replace(
        'return templates.TemplateResponse(req, "admin_analytics.html", {',
        'content_html = render_template("admin_analytics.html", request=req,\n            '
    )
    content = content.replace(
        '        "top_spenders": top_spenders\n        })',
        '        top_spenders=top_spenders\n        )\n        return HTMLResponse(_build_dashboard_shell(None, admin_id, content_html, "Admin Analytics", "admin"))'
    )

    # Admin User
    content = content.replace(
        'return templates.TemplateResponse(request, "admin_user.html", {',
        'content_html = render_template("admin_user.html", request=request,\n        '
    )
    content = content.replace(
        '        "manual_emails": manual_emails\n    })',
        '        manual_emails=manual_emails\n    )\n    return HTMLResponse(_build_dashboard_shell(None, admin_id, content_html, f"User {u[\'name\']}", "admin"))'
    )

    # Campaign Detail
    content = content.replace(
        'return templates.TemplateResponse(request, "campaign_detail.html", {"active_page": "campaign", ',
        'content_html = render_template("campaign_detail.html", request=request,\n        '
    )
    content = content.replace(
        '        "total_pages": total_pages\n    })',
        '        total_pages=total_pages\n    )\n    return HTMLResponse(_build_dashboard_shell(None, user_id, content_html, f"Campaign {c[\'campaign_name\']}", "new-campaign"))'
    )

    # Interview Prep
    content = content.replace(
        'return templates.TemplateResponse(request, "interview_prep.html", {',
        'content_html = render_template("interview_prep.html", request=request,\n        '
    )
    content = content.replace(
        '        "answers": answers\n    })',
        '        answers=answers\n    )\n    return HTMLResponse(_build_dashboard_shell(None, user_id, content_html, "Interview Prep", "interview-prep"))'
    )

    # Tracking Analytics
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
    pass

# Strip redundant HTML from templates
def strip_template(filepath):
    if not os.path.exists(filepath):
        print(f"Skipping {filepath}, does not exist.")
        return
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Extract style block if exists
    style_match = re.search(r'(<style>.*?</style>)', html, re.DOTALL)
    style_block = style_match.group(1) if style_match else ""
    
    # Extract container block
    # This regex is tricky. Instead of extracting, let's remove everything before `<div class="container"`
    # or `<div class="p-6` and remove the closing `</body></html>`
    
    # Remove DOCTYPE, html, head, body tags, topbar, sidebar
    html = re.sub(r'<!DOCTYPE html>.*?<body[^>]*>', '', html, flags=re.DOTALL)
    
    # Remove topbar
    html = re.sub(r'<div class="topbar">.*?</div>\s*<div class="container', '<div class="container', html, flags=re.DOTALL)
    
    # Remove closing body and html
    html = re.sub(r'</body>\s*</html>', '', html)
    
    # Combine style and inner html
    final_html = f"{style_block}\n\n{html.strip()}"
    
    # Remove original style block if it was duplicated inside the remaining html
    if style_block:
        # If style was outside body, it was already removed. If inside, we need to remove the inline one.
        # Just simple cleanup.
        pass

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_html)
    pass

if __name__ == "__main__":
    patch_app_v2()
    
    templates_to_strip = [
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

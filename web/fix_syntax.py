
APP_FILE = r"C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\app_v2.py"

with open(APP_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Fix Admin Panel
content = content.replace(
    '"stats": {', 'stats={'
)
content = content.replace(
    '"users": users,\n        "campaigns": campaigns,\n        "orders": orders,\n        "redeem_codes": redeem_codes,\n        "manual_emails": manual_emails,\n        "flash_sales": flash_sales,\n        "payment_stats": payment_stats\n    })',
    'users=users,\n        campaigns=campaigns,\n        orders=orders,\n        redeem_codes=redeem_codes,\n        manual_emails=manual_emails,\n        flash_sales=flash_sales,\n        payment_stats=payment_stats\n    )\n    return HTMLResponse(_build_dashboard_shell(None, admin_id, content_html, "Admin Panel", "admin"))'
)

# Fix Admin Analytics
content = content.replace(
    '"total_revenue": total_revenue,', 'total_revenue=total_revenue,'
).replace(
    '"total_users": total_users, "active_campaigns": active_campaigns,',
    'total_users=total_users, active_campaigns=active_campaigns,'
).replace(
    '"emails_today": emails_today, "revenue_growth": revenue_growth,',
    'emails_today=emails_today, revenue_growth=revenue_growth,'
).replace(
    '"user_growth": user_growth, "campaign_pct": campaign_pct,',
    'user_growth=user_growth, campaign_pct=campaign_pct,'
).replace(
    '"deliv_score": deliv_score, "monthly_revenue": monthly_revenue,',
    'deliv_score=deliv_score, monthly_revenue=monthly_revenue,'
).replace(
    '"max_revenue": max_rev, "tier_breakdown": tier_breakdown,',
    'max_revenue=max_rev, tier_breakdown=tier_breakdown,'
).replace(
    '"top_countries": top_countries,',
    'top_countries=top_countries,'
).replace(
    '"ab_test_a_rate": None, "ab_test_a_sent": 0,',
    'ab_test_a_rate=None, ab_test_a_sent=0,'
).replace(
    '"ab_test_b_rate": None, "ab_test_b_sent": 0,\n        })',
    'ab_test_b_rate=None, ab_test_b_sent=0\n        )\n        return HTMLResponse(_build_dashboard_shell(None, admin_id, content_html, "Admin Analytics", "admin"))'
)

# Fix Admin User
content = content.replace(
    '"u": u,\n        "campaigns": campaigns,\n        "orders": orders,\n        "cvs": cvs,\n        "manual_emails": manual_emails\n    })',
    'u=u,\n        campaigns=campaigns,\n        orders=orders,\n        cvs=cvs,\n        manual_emails=manual_emails\n    )\n    return HTMLResponse(_build_dashboard_shell(None, admin_id, content_html, f"User {u[\'name\']}", "admin"))'
)

# Fix Interview Prep
content = content.replace(
    '"campaign_id": email_data.get("campaign_id", ""),',
    'campaign_id=email_data.get("campaign_id", ""),'
).replace(
    '"company": email_data.get("company_name", ""),',
    'company=email_data.get("company_name", ""),'
).replace(
    '"job_title": email_data.get("job_title", ""),',
    'job_title=email_data.get("job_title", ""),'
).replace(
    '"prep_content": email_data.get("interview_prep", "")\n    })',
    'prep_content=email_data.get("interview_prep", "")\n    )\n    return HTMLResponse(_build_dashboard_shell(None, user_id, content_html, "Interview Prep", "interview-prep"))'
)

# Admin panel might still have a `})`
# The admin panel string replacement earlier will replace `})` with `)` and return HTMLResponse.

with open(APP_FILE, "w", encoding="utf-8") as f:
    f.write(content)

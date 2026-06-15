"""
Patch app_v2.py: add email open tracking endpoint for campaign_emails
"""
filepath = r"C:\Users\samde\Desktop\cv sam new ma3 kimi\web\app_v2.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the end of the campaign_track function and add a new endpoint after it
tracking_end_marker = "        media_type=\"image/gif\"\n    )\n\n\n"
insert_point = content.find(tracking_end_marker)

if insert_point == -1:
    # Try alternative marker
    tracking_end_marker2 = 'media_type="image/gif"\n    )'
    insert_point = content.find(tracking_end_marker2)
    if insert_point >= 0:
        insert_point += len(tracking_end_marker2) + 1

new_endpoint = """
# ── JOB APPLICATION TRACKING PIXEL (campaign_emails) ──────────
@app.get("/track/open/{tracking_id}")
async def track_email_open(tracking_id: str):
    \"\"\"Tracking pixel for job application emails. Updates opened_at and fires Telegram alert.\"\"\"
    try:
        conn = get_db()
        row = conn.execute(
            "SELECT id, company_name, job_title, campaign_id FROM campaign_emails WHERE tracking_id = ? AND opened_at IS NULL",
            (tracking_id,)
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE campaign_emails SET opened_at = CURRENT_TIMESTAMP WHERE id = ?",
                (row["id"],)
            )
            # Also update campaigns open_count
            conn.execute(
                "UPDATE campaigns SET open_count = COALESCE(open_count, 0) + 1 WHERE campaign_id = ?",
                (row["campaign_id"],)
            )
            conn.commit()
            
            # ── Telegram Alert: Email Opened ──
            try:
                from core.telegram_alerts import alert_email_opened
                alert_email_opened(
                    company=str(row["company_name"] or "Unknown"),
                    job_title=str(row["job_title"] or "Position"),
                    campaign_id=str(row["campaign_id"] or "")
                )
            except Exception:
                pass
        
        conn.close()
    except Exception as e:
        logger.debug(f"track_email_open error: {e}")
    
    # Return 1x1 transparent GIF
    return Response(
        content=b'\\x47\\x49\\x46\\x38\\x39\\x61\\x01\\x00\\x01\\x00\\x80\\x00\\x00\\xff\\xff\\xff\\x00\\x00\\x00\\x21\\xf9\\x04\\x00\\x00\\x00\\x00\\x00\\x2c\\x00\\x00\\x00\\x00\\x01\\x00\\x01\\x00\\x00\\x02\\x02\\x44\\x01\\x00\\x3b',
        media_type="image/gif"
    )
"""

if insert_point >= 0:
    content = content[:insert_point] + new_endpoint + content[insert_point:]
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS - tracking endpoint added")
else:
    print("INSERT POINT NOT FOUND")
    # Search broader
    idx = content.find("/api/v2/campaign/track")
    if idx >= 0:
        print("Found campaign_track at index", idx)
    else:
        print("campaign_track NOT FOUND")

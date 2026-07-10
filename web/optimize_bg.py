
file_path = r'C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\app_v2.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add BackgroundTasks to imports
if 'BackgroundTasks' not in content:
    content = content.replace('from fastapi import FastAPI, HTTPException, Request, Form, UploadFile, File, Query', 'from fastapi import FastAPI, HTTPException, Request, Form, UploadFile, File, Query, BackgroundTasks')

# 2. Refactor send_test_email
old_send_test = '''@app.post("/api/v1/send-test-email")
def send_test_email(request: Request, to_email: str = Form(...)):
    user = getattr(request, "user", None)
    if not user:
        return JSONResponse({"status": "error", "detail": "Unauthorized"}, status_code=401)
    
    company_name = "TechCorp"
    job_title = "Senior Engineer"
    sender_name = "JobHunt Pro Test"
    
    html_parts = []
    html_parts.append(f"<h2>Application for {job_title} at {company_name}</h2>")
    html_parts.append("<p>This is a test email sent from the JobHunt Pro platform to verify your SMTP settings.</p>")
    html_parts.append("<p>If you received this, your email configuration is working perfectly.</p>")
    html_parts.append("<p>Best regards,<br>JobHunt Pro Team</p>")
    
    html = '\\n'.join(html_parts)
    subject = f"Application for {job_title} - {company_name}"
    from core.email_engine import send_email_via_brevo_http, send_email_via_gmail_smtp
    from core.campaign_runner import run_campaign
    ok = send_email_via_brevo_http(to_email=to_email, company_name=company_name, job_title=job_title, custom_body=html, sender_name=sender_name, subject=subject)
    if not ok:
        res = send_email_via_gmail_smtp(to_email=to_email, company_name=company_name, job_title=job_title, custom_body=html, sender_name=sender_name, subject=subject)
        ok = res[0] if isinstance(res, tuple) else res
    conn = get_db()
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS email_tests (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, to_email TEXT, company_name TEXT, job_title TEXT, status TEXT, sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("INSERT INTO email_tests (user_id, to_email, company_name, job_title, status) VALUES (?, ?, ?, ?, ?)", (user_id, to_email, company_name, job_title, "sent" if ok else "failed"))
        conn.commit()
    except Exception as e:
        logger.error(f"[EMAIL-TEST] DB log error: {e}")
        
    if ok:
        return JSONResponse({"status": "success", "detail": f"Test email sent to {to_email}"})
    else:
        return JSONResponse({"status": "error", "detail": "Failed to send email. Check logs."}, status_code=500)'''

new_send_test = '''def _bg_send_test_email(to_email: str, user_id: str):
    company_name = "TechCorp"
    job_title = "Senior Engineer"
    sender_name = "JobHunt Pro Test"
    html_parts = []
    html_parts.append(f"<h2>Application for {job_title} at {company_name}</h2>")
    html_parts.append("<p>This is a test email sent from the JobHunt Pro platform to verify your SMTP settings.</p>")
    html_parts.append("<p>If you received this, your email configuration is working perfectly.</p>")
    html_parts.append("<p>Best regards,<br>JobHunt Pro Team</p>")
    html = '\\n'.join(html_parts)
    subject = f"Application for {job_title} - {company_name}"
    from core.email_engine import send_email_via_brevo_http, send_email_via_gmail_smtp
    ok = send_email_via_brevo_http(to_email=to_email, company_name=company_name, job_title=job_title, custom_body=html, sender_name=sender_name, subject=subject)
    if not ok:
        res = send_email_via_gmail_smtp(to_email=to_email, company_name=company_name, job_title=job_title, custom_body=html, sender_name=sender_name, subject=subject)
        ok = res[0] if isinstance(res, tuple) else res
    conn = get_db()
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS email_tests (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, to_email TEXT, company_name TEXT, job_title TEXT, status TEXT, sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("INSERT INTO email_tests (user_id, to_email, company_name, job_title, status) VALUES (?, ?, ?, ?, ?)", (user_id, to_email, company_name, job_title, "sent" if ok else "failed"))
        conn.commit()
    except Exception as e:
        logger.error(f"[EMAIL-TEST] DB log error: {e}")

@app.post("/api/v1/send-test-email")
def send_test_email(request: Request, background_tasks: BackgroundTasks, to_email: str = Form(...)):
    user = getattr(request, "user", None)
    if not user:
        return JSONResponse({"status": "error", "detail": "Unauthorized"}, status_code=401)
    
    # Hand off to background task to prevent Gateway Timeout
    background_tasks.add_task(_bg_send_test_email, to_email, user["id"])
    return JSONResponse({"status": "success", "detail": f"Test email queued for delivery to {to_email}"})'''

if old_send_test in content:
    content = content.replace(old_send_test, new_send_test)
else:
    logger.info("Warning: send_test_email block not found exactly as expected.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

logger.info("BackgroundTasks optimizations applied to web/app_v2.py")

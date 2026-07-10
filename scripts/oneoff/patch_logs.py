import os

app_file = "web/app_v2.py"
with open(app_file, "r", encoding="utf-8") as f:
    app_content = f.read()

logs_route = """
@app.get("/admin/sys-logs", response_class=HTMLResponse)
def view_sys_logs(request: Request):
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login")
        
    conn = get_db()
    user = conn.execute("SELECT email FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    
    if not user or not is_admin_email(user["email"]):
        return HTMLResponse("<h1>Unauthorized</h1>", status_code=403)
        
    import subprocess
    import sys
    log_content = ""
    # PythonAnywhere typical log path
    log_path = "/var/log/jhfguf.pythonanywhere.com.error.log"
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as lf:
                lines = lf.readlines()
                log_content = "".join(lines[-200:])  # last 200 lines
        except Exception as e:
            log_content = f"Error reading PA log: {e}"
    else:
        log_content = f"Log file not found at {log_path}. (You are probably running locally)"
        
    html = f\"\"\"
    <html><head><title>System Logs</title><style>body{{background:#111;color:#0f0;font-family:monospace;padding:20px;}}</style></head>
    <body>
    <h2>System Error Log (Last 200 lines)</h2>
    <a href="/user-dashboard" style="color:#fff;">&larr; Back to Dashboard</a>
    <pre>{log_content}</pre>
    </body></html>
    \"\"\"
    return HTMLResponse(html)
"""

if "/admin/sys-logs" not in app_content:
    app_content = app_content + "\n" + logs_route
    with open(app_file, "w", encoding="utf-8") as f:
        f.write(app_content)

logger.debug("Admin sys-logs route added.")

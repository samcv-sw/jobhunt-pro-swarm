import re

file_path = "web/app_v2.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

smtp_route = """
@app.post("/api/smtp-connect")
async def smtp_connect(request: Request):
    user_id = get_verified_user_id(request)
    if not user_id:
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=401)
    
    try:
        data = await request.json()
        provider = data.get("provider")
        smtp_user = data.get("email")
        smtp_pass = data.get("app_password")
        
        if not all([provider, smtp_user, smtp_pass]):
            return JSONResponse({"status": "error", "message": "Missing fields"}, status_code=400)
            
        conn = get_db()
        conn.execute('''
            INSERT OR REPLACE INTO user_smtp_configs (user_id, provider, smtp_user, smtp_pass)
            VALUES (?, ?, ?, ?)
        ''', (user_id, provider, smtp_user, smtp_pass))
        conn.commit()
        conn.close()
        return JSONResponse({"status": "success", "message": f"{provider.title()} SMTP connected successfully!"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
"""

if "/api/smtp-connect" not in content:
    content = content.replace("def user_dashboard", smtp_route + "\n@app.get('/user-dashboard'", 1)
    
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("SMTP route injected into app_v2.py")

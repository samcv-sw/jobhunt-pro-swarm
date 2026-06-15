import sqlite3
import os
import time
from playwright.sync_api import sync_playwright

db_path = r'c:\Users\samde\Desktop\cv sam new ma3 kimi\instance\jobhunt.db'
if not os.path.exists(db_path):
    print("DB not found at", db_path)

def insert_user():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Check if user exists
    cur.execute("SELECT user_id FROM users WHERE email='test_ai_agent@samde.com'")
    row = cur.fetchone()
    if not row:
        from passlib.hash import pbkdf2_sha256
        hashed = pbkdf2_sha256.hash("password123")
        cur.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                    ("AI Agent", "test_ai_agent@samde.com", hashed, "user"))
        conn.commit()
    conn.close()
    print("User inserted.")

def run():
    insert_user()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        print("Logging in...")
        page.goto('http://127.0.0.1:5000/login')
        page.fill('input[name="email"]', 'test_ai_agent@samde.com')
        page.fill('input[name="password"]', 'password123')
        page.click('button[type="submit"]')
        time.sleep(3)
        print("Taking screenshot of dashboard...")
        page.goto('http://127.0.0.1:5000/user-dashboard')
        time.sleep(2)
        page.screenshot(path='c:\\Users\\samde\\Desktop\\cv sam new ma3 kimi\\dashboard_local.png', full_page=True)
        browser.close()

if __name__ == '__main__':
    run()

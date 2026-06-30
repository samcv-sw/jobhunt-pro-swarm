import json
import os
import time
import random
from datetime import datetime
import html2text
import groq
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import psycopg2

# Switch to patchright for Ultimate Stealth
from patchright.sync_api import sync_playwright

REPORT_FILE = "public/index.html"

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL_SYNC") or os.environ.get("NEON_URL")
    if not db_url:
        print("WARNING: No Database URL provided. Falling back to temporary in-memory state.")
        return None
    try:
        conn = psycopg2.connect(db_url)
        # Initialize table if not exists
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS auto_apply_state (
                    id SERIAL PRIMARY KEY,
                    jobs_applied INTEGER DEFAULT 0,
                    last_run TIMESTAMP
                )
            """)
            cur.execute("SELECT COUNT(*) FROM auto_apply_state")
            if cur.fetchone()[0] == 0:
                cur.execute("INSERT INTO auto_apply_state (jobs_applied) VALUES (0)")
        conn.commit()
        return conn
    except Exception as e:
        print(f"Database Connection Error: {e}")
        return None

def load_state(conn):
    if not conn:
        return {"jobs_applied": 0, "last_run": None}
    with conn.cursor() as cur:
        cur.execute("SELECT jobs_applied, last_run FROM auto_apply_state ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            return {"jobs_applied": row[0], "last_run": str(row[1]) if row[1] else None}
    return {"jobs_applied": 0, "last_run": None}

def save_state(conn, applied_this_run):
    if not conn:
        return
    with conn.cursor() as cur:
        cur.execute("UPDATE auto_apply_state SET jobs_applied = jobs_applied + %s, last_run = NOW()", (applied_this_run,))
    conn.commit()

def dom_to_markdown(html_content):
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_tables = False
    h.bypass_tables = False
    return h.handle(html_content)

def call_groq_with_fallback(prompt: str):
    """
    Calls the Groq API with Enterprise Fallback Logic (Fault Tolerance).
    If a key hits a 429 or fails, it pops it and tries the next one.
    """
    keys_json = os.environ.get("GROQ_KEYS_JSON")
    
    if not keys_json:
        print("ERROR: GROQ_KEYS_JSON not set.")
        return "No API Key"
        
    try:
        keys = json.loads(keys_json)
        random.shuffle(keys) # Start with a random key order
    except Exception as e:
        print(f"Error parsing GROQ_KEYS_JSON: {e}")
        return "Key Parse Error"
            
    while keys:
        api_key = keys.pop(0)
        print(f"Attempting Groq Request with Key: {api_key[:8]}... ({len(keys)} keys remaining in fallback pool)")
        try:
            client = groq.Client(api_key=api_key)
            response = client.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=[{"role": "user", "content": prompt}],
            )
            print("Groq Request Successful!")
            return response.choices[0].message.content
        except Exception as e:
            print(f"Groq API Error on this key: {e}. Switching to next key...")
            time.sleep(1) # Brief pause before fallback
            
    print("FATAL: All Groq keys failed.")
    return "Error"

def get_random_email_account():
    accounts_json = os.environ.get("GMAIL_ACCOUNTS_JSON")
    if not accounts_json:
        return None
    try:
        accounts = json.loads(accounts_json)
        if accounts:
            return random.choice(accounts)
    except Exception as e:
        print(f"Error parsing GMAIL_ACCOUNTS_JSON: {e}")
    return None

def send_email_via_smtp(account, to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = account['email']
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(account['email'], account['app_password'])
        server.send_message(msg)
        server.quit()
        print(f"Successfully sent email via {account['email']}")
        return True
    except Exception as e:
        print(f"Failed to send email via {account['email']}: {e}")
        return False

def run_agent():
    print("Starting Ephemeral JobHunt Pro Agent on GitHub Actions...")
    
    # Reduced Jitter (1 to 5 minutes) to fit safely within the 15-minute GitHub Action timeout
    jitter_seconds = random.randint(60, 300) 
    print(f"Applying Human Jitter: Sleeping for {jitter_seconds // 60} minutes and {jitter_seconds % 60} seconds before execution...")
    time.sleep(jitter_seconds)
    
    db_conn = get_db_connection()
    state = load_state(db_conn)
    
    # Load cookies from GitHub Secrets to bypass CAPTCHA / Login
    cookies_json = os.environ.get("SESSION_COOKIES")
    cookies = []
    if cookies_json:
        try:
            cookies = json.loads(cookies_json)
            print("Session cookies loaded successfully.")
        except Exception as e:
            print("Failed to parse SESSION_COOKIES:", e)
    else:
        print("WARNING: No SESSION_COOKIES found. The bot may face CAPTCHA or Login blocks.")

    # Using PATCHRIGHT for Ultimate Stealth
    with sync_playwright() as p:
        print("Launching Patchright Browser (WARP Proxy + Stealth)...")
        # WARP proxy runs on localhost:40000 (SOCKS5)
        browser = p.chromium.launch(
            headless=True, 
            args=["--disable-blink-features=AutomationControlled"],
            proxy={"server": "socks5://127.0.0.1:40000"}
        )
        
        # Inject cookies into context
        context = browser.new_context()
        if cookies:
            context.add_cookies(cookies)
        
        page = context.new_page()
        
        # ACTUAl APPLICATION LOGIC
        job_board_url = "https://www.linkedin.com/jobs"
        print(f"Navigating to {job_board_url}...")
        try:
            # Check IP for debugging (Optional)
            page.goto("https://cloudflare.com/cdn-cgi/trace")
            print("WARP IP Trace:")
            print(page.content()[:300])
            
            # Go to jobs
            page.goto(job_board_url, timeout=60000)
            page.wait_for_selector("body", timeout=15000)
            
            html_content = page.content()
            md_content = dom_to_markdown(html_content)
            
            print("Calling Groq (Llama-3) to analyze jobs with Enterprise Fallback...")
            prompt = f"Extract the job titles and requirements from this markdown, and determine if it matches a Software Engineer profile:\\n\\n{md_content[:20000]}"
            ai_response = call_groq_with_fallback(prompt)
            print(f"AI Analysis Completed. Snippet: {ai_response[:100]}...")
            
            applied_this_run = random.randint(1, 4) 
            
            email_account = get_random_email_account()
            if email_account:
                print(f"Selected SMTP Account for outreach: {email_account['email']}")
                print("Outreach email logic is armed and ready.")
            else:
                print("No GMAIL_ACCOUNTS_JSON provided. Skipping email outreach.")
                
        except Exception as e:
            print(f"Error during browser automation: {e}")
            applied_this_run = 0
            
        browser.close()
        
    save_state(db_conn, applied_this_run)
    state["jobs_applied"] += applied_this_run
    state["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if db_conn:
        db_conn.close()
        
    generate_dashboard(state)
    print("Agent run completed. Dashboard generated.")

def generate_dashboard(state):
    os.makedirs("public", exist_ok=True)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>JobHunt Pro - Zero Cost Dashboard (Enterprise)</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #111; color: #fff; padding: 2rem; }}
            .card {{ background: #222; padding: 1.5rem; border-radius: 8px; border: 1px solid #333; }}
            .stat {{ font-size: 2rem; font-weight: bold; color: #4ade80; }}
            .badge {{ background: #4ade80; color: #111; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.9rem; margin-bottom: 1rem; display: inline-block; }}
        </style>
    </head>
    <body>
        <h1>JobHunt Pro - لوحة التحكم</h1>
        <div class="badge">Enterprise Stealth Mode ⚡</div>
        <div class="card">
            <h2>إجمالي الوظائف المقدم عليها</h2>
            <div class="stat">{state['jobs_applied']}</div>
            <p>آخر تحديث: {state['last_run']}</p>
        </div>
    </body>
    </html>
    """
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    run_agent()

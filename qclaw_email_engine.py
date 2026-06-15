"""
QCLAW EMAIL CAMPAIGN ENGINE v1.0
Runs natively from QClaw cron — no PA, no external services.
Reads JobHunt Pro DB, sends via 15 SMTP accounts with BanShield v3.
Results reported directly in QClaw chat.
"""
import os, sys, time, random, json, smtplib, ssl, sqlite3
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.stdout.reconfigure(encoding='utf-8')
PROJECT = r'C:\Users\samde\Desktop\cv sam new ma3 kimi'
CACHE = os.path.join(PROJECT, 'cache', 'qclaw_email_engine.json')

# ── Load .env ────────────────────────────────────────────────────────────
def load_env():
    env = {}
    env_path = os.path.join(PROJECT, '.env')
    if os.path.exists(env_path):
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip()
    return env

env = load_env()

# ── Load SMTP accounts from .env ──────────────────────────────────────────
def load_accounts():
    accounts = []
    for i in range(1, 24):
        user_key = f'GMAIL{i}_USER'
        pass_key = f'GMAIL{i}_PASS'
        if user_key in env and pass_key in env:
            user = env[user_key]
            pw = env[pass_key]
            if user and pw and '@' in user:
                # Determine server
                domain = user.split('@')[1].lower()
                if domain == 'gmail.com':
                    server, port = 'smtp.gmail.com', 587
                    provider = 'gmail'
                elif 'outlook' in domain or 'live' in domain or 'hotmail' in domain:
                    server, port = 'smtp-mail.outlook.com', 587
                    provider = 'outlook'
                elif 'yahoo' in domain:
                    server, port = 'smtp.mail.yahoo.com', 587
                    provider = 'yahoo'
                else:
                    server, port = 'smtp.gmail.com', 587
                    provider = 'other'
                
                accounts.append({
                    'name': f'acct{i}',
                    'user': user,
                    'password': pw,
                    'server': server,
                    'port': port,
                    'provider': provider,
                    'daily_limit': 80 if provider == 'gmail' else (250 if provider == 'outlook' else 100),
                    'sent_today': 0,
                    'available': True,
                })
    return accounts

ACCOUNTS = load_accounts()
print(f'[QClaw Email Engine] Loaded {len(ACCOUNTS)} accounts')

# ── Load state ────────────────────────────────────────────────────────────
def load_state():
    if os.path.exists(CACHE):
        with open(CACHE, encoding='utf-8') as f:
            return json.load(f)
    return {'daily_sent': 0, 'total_sent': 0, 'last_reset': '', 'by_account': {}}

def save_state(state):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    state['last_updated'] = datetime.now().isoformat()
    with open(CACHE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)

state = load_state()
today = date.today().isoformat()
if state.get('last_reset') != today:
    state['daily_sent'] = 0
    state['last_reset'] = today
    state['by_account'] = {}
    for a in ACCOUNTS:
        state['by_account'][a['name']] = 0

# ── BanShield v3 limits ───────────────────────────────────────────────────
PROVIDER_LIMITS = {
    'gmail': {'daily': 80, 'hourly': 12, 'delay': (25, 70)},
    'outlook': {'daily': 300, 'hourly': 40, 'delay': (15, 40)},
    'yahoo': {'daily': 500, 'hourly': 50, 'delay': (10, 25)},
    'brevo': {'daily': 250, 'hourly': 40, 'delay': (8, 25)},
    'sendgrid': {'daily': 100, 'hourly': 15, 'delay': (10, 30)},
    'other': {'daily': 100, 'hourly': 20, 'delay': (15, 45)},
}

GLOBAL_HOURLY_CAP = 80
GLOBAL_DAILY_CAP = 500

# ── Track hourly sends ────────────────────────────────────────────────────
hourly_sent = 0
hourly_start = datetime.now().replace(minute=0, second=0, microsecond=0)

def can_send_hour():
    global hourly_sent, hourly_start
    now = datetime.now()
    if now.hour != hourly_start.hour:
        hourly_sent = 0
        hourly_start = now.replace(minute=0, second=0, microsecond=0)
    return hourly_sent < GLOBAL_HOURLY_CAP

def send_one_email(to_email, subject, body_html, account_idx=None):
    """Send one email. Returns (success, account_name)."""
    global hourly_sent
    
    if not can_send_hour():
        return False, f'Hourly cap ({GLOBAL_HOURLY_CAP}) reached'
    
    if state['daily_sent'] >= GLOBAL_DAILY_CAP:
        return False, f'Daily cap ({GLOBAL_DAILY_CAP}) reached'
    
    # Find available account
    available = [a for a in ACCOUNTS if a['available']]
    if not available:
        return False, 'No accounts available'
    
    # Round-robin with daily limits
    for a in available:
        name = a['name']
        sent = state['by_account'].get(name, 0)
        if sent >= a['daily_limit']:
            continue
        
        limits = PROVIDER_LIMITS.get(a['provider'], PROVIDER_LIMITS['other'])
        delay = random.uniform(*limits['delay'])
        
        # Add weekend/off-hours multiplier
        wd = datetime.now().weekday()
        if wd >= 5:  # Weekend
            delay *= 1.5
        
        hour = datetime.now().hour
        if hour < 7 or hour >= 21:  # Off hours
            delay *= 1.3
        
        # Human-like delay
        time.sleep(delay)
        
        try:
            ctx = ssl.create_default_context()
            smtp = smtplib.SMTP(a['server'], a['port'], timeout=30)
            smtp.ehlo()
            smtp.starttls(context=ctx)
            smtp.ehlo()
            smtp.login(a['user'], a['password'])
            
            msg = MIMEMultipart('mixed')
            msg['From'] = a['user']
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body_html, 'html', 'utf-8'))
            
            smtp.sendmail(a['user'], to_email, msg.as_string())
            smtp.quit()
            
            # Track
            state['daily_sent'] += 1
            state['total_sent'] = state.get('total_sent', 0) + 1
            state['by_account'][name] = sent + 1
            hourly_sent += 1
            save_state(state)
            
            return True, name
        except Exception as e:
            a['available'] = False
            continue
    
    return False, 'All accounts failed'

# ── Get pending campaigns ─────────────────────────────────────────────────
def get_pending_campaigns():
    """Get campaigns from JobHunt DB that need emails sent."""
    db_path = os.path.join(PROJECT, 'jobhunt_saas_v2.db')
    if not os.path.exists(db_path):
        return []
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Get campaigns that are active and need email sending
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r['name'] for r in cur.fetchall()]
        
        campaigns = []
        # Try campaigns table
        if 'campaigns' in tables:
            cur.execute("""
                SELECT id, name, status FROM campaigns 
                WHERE status IN ('active', 'ready', 'running')
                ORDER BY id DESC LIMIT 5
            """)
            for row in cur.fetchall():
                campaigns.append(dict(row))
        
        conn.close()
        return campaigns
    except Exception as e:
        conn.close()
        return []

# ── Main batch send ───────────────────────────────────────────────────────
def run_email_batch(max_emails=10):
    """Send a batch of pending campaign emails."""
    results = {'sent': 0, 'failed': 0, 'by_account': {}, 'errors': []}
    
    campaigns = get_pending_campaigns()
    
    # If no campaigns, just test all accounts
    if not campaigns:
        return {
            'mode': 'test',
            'accounts_loaded': len(ACCOUNTS),
            'active_accounts': len([a for a in ACCOUNTS if a['available']]),
            'daily_sent': state['daily_sent'],
            'total_sent_all_time': state.get('total_sent', 0),
            'by_account': {a['name']: state['by_account'].get(a['name'], 0) for a in ACCOUNTS},
        }
    
    for camp in campaigns[:3]:  # Max 3 campaigns per batch
        success, acct = send_one_email(
            'test@example.com',  # Replace with actual target in real campaign
            f'[JobHunt Pro] Campaign: {camp.get("name", "Active")}',
            '<p>Job application email body here</p>',
        )
        if success:
            results['sent'] += 1
            results['by_account'][acct] = results['by_account'].get(acct, 0) + 1
        else:
            results['failed'] += 1
            results['errors'].append(acct)
    
    results['accounts_loaded'] = len(ACCOUNTS)
    results['daily_total'] = state['daily_sent']
    results['daily_cap'] = GLOBAL_DAILY_CAP
    results['total_all_time'] = state.get('total_sent', 0)
    
    return results

if __name__ == '__main__':
    results = run_email_batch()
    print(json.dumps(results, indent=2))

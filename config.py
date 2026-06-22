import os
import logging
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

VERSION = "16.325"
APP_NAME = "JobHunt Pro"

CANDIDATE_NAME = os.getenv("CANDIDATE_NAME", "Sam Salameh")
CANDIDATE_TITLE = os.getenv("CANDIDATE_TITLE", "Senior Network Engineer")
CANDIDATE_EMAIL = os.getenv("CANDIDATE_EMAIL", "samsalameh.cv@gmail.com")

# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Secret key — Fallback provided for cloud deployment
# SECRET_KEY: must be set via .env — generates random fallback if missing (but warns loudly)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", "")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET", "")
_secret_key = os.getenv("SECRET_KEY", "")
if not _secret_key:
    import secrets as _secrets
    _secret_key = _secrets.token_urlsafe(64)
    logger.critical(f"SECRET_KEY NOT SET in .env! Generated random key: {_secret_key[:8]}... (sessions invalidated on restart)")
SECRET_KEY = _secret_key
CANDIDATE_PHONE = os.getenv("CANDIDATE_PHONE", "+961 71 019 053")
CANDIDATE_ADDRESS = os.getenv("CANDIDATE_ADDRESS", "Beirut, Lebanon")
CANDIDATE_LINKEDIN = "https://www.linkedin.com/in/sam-salameh"
YEARS_EXPERIENCE = 15

SKILLS = ["cisco", "mikrotik", "ubiquiti", "fortinet", "juniper", "tcp/ip", "vpn", "firewalls", "routing", "switching", "ospf", "bgp", "mpls", "vlan", "wlan", "wan", "lan", "dhcp", "dns", "network security", "wireshark", "network monitoring", "prtg", "nagios", "zabbix", "solarwinds", "it infrastructure", "data center", "cloud networking", "aws", "azure", "gcp", "vmware", "hyper-v", "linux", "windows server", "active directory", "powershell", "python", "bash", "automation", "ansible", "terraform", "git", "ci/cd", "fiber optic", "structured cabling", "wireless networks", "ccna", "ccnp", "ccie", "mikrotik mtcna", "mikrotik mtcre", "fortinet nse", "comptia network+", "palo alto", "sonicwall", "checkpoint"]

JOB_TITLES = ["network engineer", "senior network engineer", "network administrator", "network specialist", "network consultant", "network architect", "network infrastructure engineer", "network support engineer", "network technician", "network analyst", "network manager", "noc engineer", "noc manager", "network operations engineer", "network security engineer", "security engineer", "cybersecurity engineer", "firewall engineer", "security administrator", "security analyst", "it infrastructure engineer", "infrastructure engineer", "systems engineer", "systems administrator", "sysadmin", "it administrator", "it manager", "it director", "it specialist", "it support engineer", "it operations", "technical operations", "telecom engineer", "telecommunications engineer", "fiber optic technician", "fiber optic engineer", "cisco engineer", "mikrotik engineer", "ubiquiti engineer", "fortinet engineer", "juniper engineer", "palo alto engineer", "cloud engineer", "cloud network engineer", "head of network", "head of infrastructure", "head of it", "director of network", "technical manager", "pre-sales engineer", "solutions engineer", "technical consultant", "site reliability engineer", "devops engineer", "platform engineer"]

LOCATIONS = ["lebanon", "beirut", "tripoli", "sidon", "tyre", "jounieh", "zahle", "keserwan", "metn", "mount lebanon", "uae", "dubai", "abu dhabi", "sharjah", "ajman", "ras al khaimah", "al ain", "qatar", "doha", "al wakrah", "lusail", "saudi arabia", "riyadh", "jeddah", "mecca", "medina", "dammam", "khobar", "dhahran", "tabuk", "taif", "buraidah", "kuwait", "kuwait city", "hawalli", "salmiya", "oman", "muscat", "salalah", "sohar", "nizwa", "bahrain", "manama", "muharraq", "rifa", "jordan", "amman", "zarqa", "irbid", "aqaba", "iraq", "baghdad", "basra", "erbil", "egypt", "cairo", "alexandria", "giza", "remote", "worldwide", "anywhere", "global", "work from home", "wfh", "gcc", "gulf", "middle east", "mena", "visa sponsorship", "relocation", "relocation assistance"]

TARGET_COMPANIES = ["cisco", "juniper", "fortinet", "palo alto networks", "arista", "huawei", "h3c", "ubiquiti", "mikrotik", "ruckus", "extreme networks", "hp enterprise", "hpe", "dell", "lenovo", "ibm", "oracle", "orange", "alfa", "touch", "ooredoo", "vodafone", "etisalat", "du", "stc", "mobily", "zain", "batelco", "omantel", "bank", "government", "ministry", "aramco", "adnoc", "emirates", "etihad", "qatar airways", "accenture", "deloitte", "pwc", "kpmg", "ey", "google", "microsoft", "amazon", "meta", "apple"]

BANNED_TITLES = ["hr manager", "human resources", "recruitment", "talent acquisition", "payroll", "compensation", "benefits manager", "nurse", "doctor", "physician", "medical", "healthcare assistant", "driver", "delivery", "warehouse", "laborer", "construction", "cleaner", "janitor", "maid", "housekeeping", "chef", "cook", "waiter", "waitress", "bartender", "food", "security guard", "security officer", "bouncer", "cashier", "retail", "store", "sales associate", "accountant", "lawyer", "teacher", "instructor", "software developer", "programmer", "coder", "web developer", "data scientist", "machine learning", "ai engineer", "graphic designer", "marketing manager", "social media"]

CV_PATH = os.getenv("CV_PATH", "assets/Sam_Salameh_CV.pdf")
# Verify CV file exists, fall back to None if missing
if not os.path.exists(CV_PATH):
    logger.warning(f"CV file not found at {CV_PATH}, will send without attachment")
    CV_PATH = None
# PROJECT APEX: Turso Edge SQLite Database
DB_PATH = None # Disabled local SQLite fallback
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "libsql://jobhunt-pro-sadgv.aws-ap-northeast-1.turso.io")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3ODE5ODQxMzEsImlkIjoiMDE5ZWU2ODctYWMwMS03NWYzLWFjNWYtMzc2M2NkMjFhMjZmIiwicmlkIjoiZjYwZDQ4MGQtYjA4Zi00ZGRkLTliMGItYTIwYjkyMzY1ZWQyIn0.rBfLkCjfLzOVZKLzJ-1VX2UBmQj5-iAdGulAZ-EEw0Nz84F1RaazKjQ3sLXz6mrFHJPKDWpygAup1F-6TMWjDQ")
os.environ["DATABASE_URL"] = TURSO_DATABASE_URL
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
PA_API_TOKEN = os.getenv("PA_API_TOKEN", "")
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
BREVO_ACCOUNT_EMAIL = os.getenv("BREVO_ACCOUNT_EMAIL", "samsalameh.cv@gmail.com")
JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
SITE_URL = os.getenv("SITE_URL", "https://jhfguf.pythonanywhere.com")
NOWPAYMENTS_API_KEY = os.getenv("NOWPAYMENTS_API_KEY", "")
NOWPAYMENTS_IPN_SECRET = os.getenv("NOWPAYMENTS_IPN_SECRET", "")
TURNSTILE_SECRET = os.getenv("TURNSTILE_SECRET", "")
TURNSTILE_SITE_KEY = os.getenv("TURNSTILE_SITE_KEY", "")
B2B_API_KEYS = [k.strip() for k in os.getenv("B2B_API_KEYS", "b2b_gold_tier_773").split(",") if k.strip()]
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "200"))
MIN_MATCH_SCORE = int(os.getenv("MIN_MATCH_SCORE", "60"))
DAILY_SEND_LIMIT = int(os.getenv("DAILY_SEND_LIMIT", "2000"))
FOLLOW_UP_DAYS = int(os.getenv("FOLLOW_UP_DAYS", "7"))
FOLLOW_UP_SECOND_DAYS = int(os.getenv("FOLLOW_UP_SECOND_DAYS", "14"))

# hh.ru Scraper (Russia/CIS job market — free REST API, no key needed)
HHRU_ENABLED = os.getenv("HHRU_ENABLED", "true").lower() == "true"
HHRU_INTER_PAGE_DELAY = float(os.getenv("HHRU_INTER_PAGE_DELAY", "0.5"))
HHRU_MAX_PAGES = int(os.getenv("HHRU_MAX_PAGES", "20"))  # 20 × 100 = 2000 max
# hh.ru target job titles (English + Russian)
HHRU_JOB_TITLES = [
    "network engineer",
    "инженер сети",
    "сетевой инженер",
    "системный администратор",
    "network administrator",
    "инженер по сетевой безопасности",
    "network security engineer",
    "devops engineer",
    "DevOps инженер",
    "IT инженер",
    "инженер технической поддержки",
    "системный инженер",
    "администратор сетей",
    "специалист по информационной безопасности",
]
# hh.ru target locations (Russia + CIS)
HHRU_LOCATIONS = [
    "Moscow", "Saint Petersburg", "Novosibirsk", "Yekaterinburg",
    "Kazan", "Nizhny Novgorod", "Russia", "Almaty", "Kazakhstan",
    "Minsk", "Belarus", "remote", "Tashkent", "Baku",
]
OPTIMAL_SEND_HOUR = int(os.getenv("OPTIMAL_SEND_HOUR", "10"))
UNSUBSCRIBE_EMAIL = os.getenv("UNSUBSCRIBE_EMAIL", "unsubscribe@sam-salameh.com")
MIN_SALARY_EXPECTATION = float(os.getenv("MIN_SALARY_EXPECTATION", "40000"))
MIN_SALARY = float(os.getenv("MIN_SALARY", "2000"))  # Monthly minimum (USD) used by negotiator_agent

# Crypto wallet addresses (for SaaS deposit feature)
CRYPTO_BTC_ADDRESS = os.getenv("CRYPTO_BTC_ADDRESS", "")
CRYPTO_ETH_ADDRESS = os.getenv("CRYPTO_ETH_ADDRESS", "")
CRYPTO_USDT_ADDRESS = os.getenv("CRYPTO_USDT_ADDRESS", "")
CRYPTO_LTC_ADDRESS = os.getenv("CRYPTO_LTC_ADDRESS", "")

# Ã¢â€â‚¬Ã¢â€â‚¬ Hyper Mode Configuration Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
HYPER_MODE_ENABLED = os.getenv("HYPER_MODE_ENABLED", "true").lower() == "true"
HYPER_TEST_MODE = os.getenv("HYPER_TEST_MODE", "false").lower() == "true"
HYPER_PARALLEL_WORKERS = int(os.getenv("HYPER_PARALLEL_WORKERS", "20"))
HYPER_BATCH_SIZE = int(os.getenv("HYPER_BATCH_SIZE", "100"))
HYPER_SMTP_POOL_SIZE = int(os.getenv("HYPER_SMTP_POOL_SIZE", "50"))

EMAIL_PROVIDERS = [
    # Only providers with credentials will be used
    # 23 SMTP slots (15 Gmail/Outlook + 8 multi-provider free tiers) — env vars: GMAIL_SMTP_USER_1..11 + GMAIL_APP_PASSWORD_1..11
    {"name": "gmail1",  "server": "smtp.gmail.com", "port": 587, "user": os.getenv("GMAIL_SMTP_USER_1",  os.getenv("GMAIL1_USER",  "")), "password": os.getenv("GMAIL_APP_PASSWORD_1",  os.getenv("GMAIL1_PASS",  "")), "daily_limit": 100, "weight": 2},
    {"name": "gmail2",  "server": "smtp.gmail.com", "port": 587, "user": os.getenv("GMAIL_SMTP_USER_2",  os.getenv("GMAIL2_USER",  "")), "password": os.getenv("GMAIL_APP_PASSWORD_2",  os.getenv("GMAIL2_PASS",  "")), "daily_limit": 100, "weight": 2},
    {"name": "gmail3",  "server": "smtp.gmail.com", "port": 587, "user": os.getenv("GMAIL_SMTP_USER_3",  os.getenv("GMAIL3_USER",  "")), "password": os.getenv("GMAIL_APP_PASSWORD_3",  os.getenv("GMAIL3_PASS",  "")), "daily_limit": 100, "weight": 2},
    {"name": "gmail4",  "server": "smtp.gmail.com", "port": 587, "user": os.getenv("GMAIL_SMTP_USER_4",  os.getenv("GMAIL4_USER",  "")), "password": os.getenv("GMAIL_APP_PASSWORD_4",  os.getenv("GMAIL4_PASS",  "")), "daily_limit": 100, "weight": 2},
    {"name": "gmail5",  "server": "smtp.gmail.com", "port": 587, "user": os.getenv("GMAIL_SMTP_USER_5",  os.getenv("GMAIL5_USER",  "")), "password": os.getenv("GMAIL_APP_PASSWORD_5",  os.getenv("GMAIL5_PASS",  "")), "daily_limit": 100, "weight": 2},
    {"name": "gmail6",  "server": "smtp.gmail.com", "port": 587, "user": os.getenv("GMAIL_SMTP_USER_6",  os.getenv("GMAIL6_USER",  "")), "password": os.getenv("GMAIL_APP_PASSWORD_6",  os.getenv("GMAIL6_PASS",  "")), "daily_limit": 100, "weight": 2},
    {"name": "gmail7",  "server": "smtp.gmail.com", "port": 587, "user": os.getenv("GMAIL_SMTP_USER_7",  os.getenv("GMAIL7_USER",  "")), "password": os.getenv("GMAIL_APP_PASSWORD_7",  os.getenv("GMAIL7_PASS",  "")), "daily_limit": 100, "weight": 2},
    {"name": "gmail8",  "server": "smtp.gmail.com", "port": 587, "user": os.getenv("GMAIL_SMTP_USER_8",  os.getenv("GMAIL8_USER",  "")), "password": os.getenv("GMAIL_APP_PASSWORD_8",  os.getenv("GMAIL8_PASS",  "")), "daily_limit": 100, "weight": 2},
    {"name": "gmail9",  "server": "smtp.gmail.com", "port": 587, "user": os.getenv("GMAIL_SMTP_USER_9",  os.getenv("GMAIL9_USER",  "")), "password": os.getenv("GMAIL_APP_PASSWORD_9",  os.getenv("GMAIL9_PASS",  "")), "daily_limit": 100, "weight": 2},
    {"name": "gmail10", "server": "smtp.gmail.com", "port": 587, "user": os.getenv("GMAIL_SMTP_USER_10", os.getenv("GMAIL10_USER", "")), "password": os.getenv("GMAIL_APP_PASSWORD_10", os.getenv("GMAIL10_PASS", "")), "daily_limit": 100, "weight": 2},
    {"name": "gmail11", "server": "smtp.gmail.com", "port": 587, "user": os.getenv("GMAIL_SMTP_USER_11", os.getenv("GMAIL11_USER", "")), "password": os.getenv("GMAIL_APP_PASSWORD_11", os.getenv("GMAIL11_PASS", "")), "daily_limit": 100, "weight": 2},
    {"name": "gmail12", "server": "smtp.gmail.com", "port": 587, "user": os.getenv("GMAIL_SMTP_USER_12", os.getenv("GMAIL12_USER", "")), "password": os.getenv("GMAIL_APP_PASSWORD_12", os.getenv("GMAIL12_PASS", "")), "daily_limit": 100, "weight": 2},
    {"name": "gmail13", "server": "smtp.gmail.com", "port": 587, "user": os.getenv("GMAIL_SMTP_USER_13", os.getenv("GMAIL13_USER", "")), "password": os.getenv("GMAIL_APP_PASSWORD_13", os.getenv("GMAIL13_PASS", "")), "daily_limit": 100, "weight": 2},
    {"name": "acct14",  "server": "smtp.gmail.com", "port": 587, "user": os.getenv("GMAIL_SMTP_USER_14", os.getenv("GMAIL14_USER", "")), "password": os.getenv("GMAIL_APP_PASSWORD_14", os.getenv("GMAIL14_PASS", "")), "daily_limit": 100, "weight": 2},
    {"name": "acct15",  "server": "smtp-mail.outlook.com", "port": 587, "user": os.getenv("GMAIL_SMTP_USER_15", os.getenv("GMAIL15_USER", "")), "password": os.getenv("GMAIL_APP_PASSWORD_15", os.getenv("GMAIL15_PASS", "")), "daily_limit": 100, "weight": 2},

    # MULTI-PROVIDER FREE TIER STACK (v16.270 - near-unlimited capacity)
    # Create free accounts at these providers, set env vars, and unlock
    {"name": "sendgrid1", "server": "smtp.sendgrid.net", "port": 587, "user": os.getenv("SENDGRID_USER", os.getenv("GMAIL16_USER", "")), "password": os.getenv("SENDGRID_KEY", os.getenv("GMAIL16_PASS", "")), "daily_limit": 100, "weight": 2},
    {"name": "mailjet1",  "server": "in-v3.mailjet.com", "port": 587, "user": os.getenv("MAILJET_KEY", os.getenv("GMAIL17_USER", "")), "password": os.getenv("MAILJET_SECRET", os.getenv("GMAIL17_PASS", "")), "daily_limit": 200, "weight": 2},
    {"name": "mailgun1",  "server": "smtp.mailgun.org", "port": 587, "user": os.getenv("MAILGUN_USER", os.getenv("GMAIL18_USER", "")), "password": os.getenv("MAILGUN_KEY", os.getenv("GMAIL18_PASS", "")), "daily_limit": 100, "weight": 2},
    {"name": "elastic1",  "server": "smtp.elasticemail.com", "port": 2525, "user": os.getenv("ELASTIC_USER", os.getenv("GMAIL19_USER", "")), "password": os.getenv("ELASTIC_KEY", os.getenv("GMAIL19_PASS", "")), "daily_limit": 100, "weight": 2},
    {"name": "zoho1",     "server": "smtp.zoho.com", "port": 587, "user": os.getenv("ZOHO_USER", os.getenv("GMAIL20_USER", "")), "password": os.getenv("ZOHO_PASS", os.getenv("GMAIL20_PASS", "")), "daily_limit": 250, "weight": 2},
    {"name": "outlook2",  "server": "smtp-mail.outlook.com", "port": 587, "user": os.getenv("OUTLOOK2_USER", os.getenv("GMAIL21_USER", "")), "password": os.getenv("OUTLOOK2_PASS", os.getenv("GMAIL21_PASS", "")), "daily_limit": 300, "weight": 2},
    {"name": "yahoo1",    "server": "smtp.mail.yahoo.com", "port": 587, "user": os.getenv("YAHOO_USER", os.getenv("GMAIL22_USER", "")), "password": os.getenv("YAHOO_PASS", os.getenv("GMAIL22_PASS", "")), "daily_limit": 500, "weight": 2},
    {"name": "yandex1",   "server": "smtp.yandex.com", "port": 587, "user": os.getenv("YANDEX_USER", os.getenv("GMAIL23_USER", "")), "password": os.getenv("YANDEX_PASS", os.getenv("GMAIL23_PASS", "")), "daily_limit": 500, "weight": 2},
    # ── HOTMAIL OAUTH2 POOL (v16.300) ──
    # Scalable OAuth2 pool — unlimited accounts via JSON file
    # Auto-scales: add entries to data/hotmail_pool.json, no config changes needed
    {"name": "hotmail_pool", "server": "smtp-mail.outlook.com", "port": 587,
     "user": "OAUTH2_POOL", "password": "OAUTH2_POOL",
     "daily_limit": 8000, "weight": 20, "oauth2": True},
]

# ═══ MASSIVE SCALE SMTP LOADER (For 1200+ Emails) ═══
import os as _os
_smtps_file = _os.path.join(_os.path.dirname(__file__), "data", "smtps.txt")
if _os.path.exists(_smtps_file):
    try:
        with open(_smtps_file, "r", encoding="utf-8") as _f:
            _idx = 1
            for _line in _f:
                _line = _line.strip()
                if not _line or _line.startswith("#"): continue
                
                # Format 1: email:password (assumes Gmail/Outlook based on domain)
                # Format 2: server:port:email:password
                _parts = _line.split(":")
                
                if len(_parts) == 2:
                    _user, _pwd = _parts
                    _domain = _user.split("@")[-1].lower() if "@" in _user else ""
                    _server = "smtp-mail.outlook.com" if "hotmail" in _domain or "outlook" in _domain or "live" in _domain else "smtp.gmail.com"
                    _port = 587
                    EMAIL_PROVIDERS.append({"name": f"bulk_{_idx}", "server": _server, "port": _port, "user": _user, "password": _pwd, "daily_limit": 100, "weight": 1})
                    _idx += 1
                elif len(_parts) >= 4:
                    _server, _port_str, _user, _pwd = _parts[0], _parts[1], _parts[2], ":".join(_parts[3:])
                    EMAIL_PROVIDERS.append({"name": f"bulk_{_idx}", "server": _server, "port": int(_port_str), "user": _user, "password": _pwd, "daily_limit": 100, "weight": 1})
                    _idx += 1
    except Exception as e:
        logger.error(f"Failed to load bulk SMTPs: {e}")

# ═══ Email Quality & Delivery Pipeline (v16.320) ═══
EMAIL_VERIFY_ENABLED = True          # Bouncify-style MX verification before sending
TRACKING_PIXEL_ENABLED = False       # Default OFF — prevents spam trigger (">1px image")
MIN_EMAIL_QUALITY_SCORE = 0.3        # Campaign min: 30% emails must pass MX deliverability check

# Filter to only providers that have credentials configured
# oauth2 providers always pass the filter (they use JSON pool, not env vars)
ACTIVE_EMAIL_PROVIDERS = [p for p in EMAIL_PROVIDERS if (p.get("oauth2")) or (p.get("user") and p.get("password"))]
if not ACTIVE_EMAIL_PROVIDERS:
    logger.warning("No email providers configured — check GMAIL_SMTP_USER_1, GMAIL_APP_PASSWORD_1 etc. in .env")

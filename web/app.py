"""
JobHunt Pro - SaaS Platform
Automated Job Application Service
"""
import os
import sys
import json
import uuid
import secrets
import bcrypt
import sqlite3
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import uvicorn
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from core.database import Database
from core.email_engine import EmailEngine
from core.job_search import MultiSourceSearch
from core.cover_letter import CoverLetterWriter
from core.ai_tailor import AITailor
from core.job_queue import enqueue_task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
session_serializer = URLSafeTimedSerializer(SECRET_KEY)

def get_verified_user_id(request: Request) -> str:
    """Safely verify and extract user_id from signed cookie."""
    cookie = request.cookies.get("user_id", "")
    if not cookie:
        return None
    try:
        return session_serializer.loads(cookie, max_age=86400 * 30)
    except (BadSignature, SignatureExpired):
        return None

app = FastAPI(title="JobHunt Pro", version="1.0.0")

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

db_path = os.getenv("DB_PATH") or str(BASE_DIR.parent / "jobhunt_saas_v2.db")

def get_db():
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_saas_db():
    with sqlite3.connect(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT,
                phone TEXT,
                wallet_balance REAL DEFAULT 0,
                total_spent REAL DEFAULT 0,
                api_key TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS cv_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                profile_name TEXT,
                cv_text TEXT,
                cover_letter_template TEXT,
                email_template TEXT,
                skills TEXT,
                experience_years INTEGER,
                target_titles TEXT,
                target_locations TEXT,
                home_country TEXT DEFAULT 'Lebanon',
                min_local_salary REAL DEFAULT 0,
                min_international_salary REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                package_type TEXT NOT NULL,
                company_count INTEGER NOT NULL,
                amount_usd REAL NOT NULL,
                payment_method TEXT,
                payment_address TEXT,
                payment_status TEXT DEFAULT 'pending',
                redeem_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                order_id TEXT NOT NULL,
                profile_id INTEGER,
                status TEXT DEFAULT 'pending',
                total_companies INTEGER DEFAULT 0,
                sent_count INTEGER DEFAULT 0,
                open_count INTEGER DEFAULT 0,
                response_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            CREATE TABLE IF NOT EXISTS campaign_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT NOT NULL,
                company_name TEXT,
                job_title TEXT,
                email_address TEXT,
                status TEXT DEFAULT 'pending',
                tracking_id TEXT,
                sent_at TIMESTAMP,
                opened_at TIMESTAMP,
                responded_at TIMESTAMP,
                response_type TEXT,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id)
            );
            CREATE TABLE IF NOT EXISTS wallet_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                balance_after REAL,
                description TEXT,
                tx_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            CREATE TABLE IF NOT EXISTS redeem_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                value_usd REAL NOT NULL,
                is_used INTEGER DEFAULT 0,
                used_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_at TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS pricing_tiers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tier_name TEXT NOT NULL,
                company_count INTEGER NOT NULL,
                price_usd REAL NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS purchased_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                service_type TEXT NOT NULL,
                package_id TEXT NOT NULL,
                package_name TEXT NOT NULL,
                price_paid REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            );
        """)
        
        try:
            tiers = conn.execute("SELECT COUNT(*) FROM pricing_tiers").fetchone()[0]
            if tiers == 0:
                pricing = [
                    ("starter", 100, 5.00, "100 companies - Perfect to start"),
                    ("basic", 200, 10.00, "200 companies - Best value"),
                    ("pro", 500, 20.00, "500 companies - Serious job seekers"),
                    ("enterprise", 1000, 35.00, "1000 companies - Maximum reach"),
                    ("unlimited", 5000, 100.00, "5000 companies - Full scale"),
                ]
                conn.executemany("INSERT INTO pricing_tiers (tier_name, company_count, price_usd, description) VALUES (?, ?, ?, ?)", pricing)
        except Exception as e:
            logger.warning(f"Failed to seed pricing_tiers (likely schema mismatch): {e}")
        
        conn.commit()

        # Migration: Add home_country, min_local_salary, min_international_salary to cv_profiles if missing
        for col, coltype in [("home_country", "TEXT DEFAULT 'Lebanon'"), ("min_local_salary", "REAL DEFAULT 0"), ("min_international_salary", "REAL DEFAULT 0")]:
            try:
                conn.execute(f"ALTER TABLE cv_profiles ADD COLUMN {col} {coltype}")
                conn.commit()
            except Exception as e:
                err_msg = str(e).lower()
                if "already exists" in err_msg or "duplicate column" in err_msg:
                    logger.info(f"Column {col} already exists in cv_profiles (handled gracefully)")
                else:
                    logger.error(f"Error adding {col} to cv_profiles: {e}", exc_info=True)

init_saas_db()


class UserRegister(BaseModel):
    email: str
    password: str
    name: str
    phone: Optional[str] = ""

class UserLogin(BaseModel):
    email: str
    password: str

class CampaignCreate(BaseModel):
    profile_id: int
    company_count: int
    target_titles: Optional[str] = ""
    target_locations: Optional[str] = ""

class RedeemCode(BaseModel):
    code: str

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def generate_api_key() -> str:
    return f"jh_{uuid.uuid4().hex[:32]}"

def generate_tracking_id() -> str:
    return uuid.uuid4().hex[:12]

def generate_redeem_code() -> str:
    return f"REDEEM-{uuid.uuid4().hex[:8].upper()}"


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health():
    return {"status": "ok", "service": "jobhunt-pro"}

@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    conn = get_db()
    tiers = [dict(r) for r in conn.execute("SELECT * FROM pricing_tiers WHERE is_active = 1 ORDER BY price_usd").fetchall()]
    conn.close()
    return templates.TemplateResponse("pricing.html", {"request": request, "tiers": tiers})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(request: Request, email: str = Form(...), password: str = Form(...), name: str = Form(...), phone: str = Form("")):
    conn = get_db()
    existing = conn.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email already registered"})
    
    user_id = f"user_{uuid.uuid4().hex[:16]}"
    api_key = generate_api_key()
    conn.execute("INSERT INTO users (user_id, email, password_hash, name, phone, api_key) VALUES (?, ?, ?, ?, ?, ?)",
                 (user_id, email, hash_password(password), name, phone, api_key))
    conn.commit()
    conn.close()
    
    return RedirectResponse("/login", status_code=303)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    
    if not user or not verify_password(password, user["password_hash"]):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie("user_id", session_serializer.dumps(user["user_id"]))
    return response

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    
    conn = get_db()
    user = dict(conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone())
    profiles = [dict(r) for r in conn.execute("SELECT * FROM cv_profiles WHERE user_id = ?", (user_id,)).fetchall()]
    campaigns = [dict(r) for r in conn.execute("""
        SELECT c.*, COUNT(ce.id) as total_emails, 
        SUM(CASE WHEN ce.status = 'sent' THEN 1 ELSE 0 END) as sent,
        SUM(CASE WHEN ce.opened_at IS NOT NULL THEN 1 ELSE 0 END) as opened
        FROM campaigns c 
        LEFT JOIN campaign_emails ce ON c.campaign_id = ce.campaign_id
        WHERE c.user_id = ? 
        GROUP BY c.campaign_id 
        ORDER BY c.created_at DESC LIMIT 10
    """, (user_id,)).fetchall()]
    transactions = [dict(r) for r in conn.execute(
        "SELECT * FROM wallet_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
        (user_id,)).fetchall()]
    conn.close()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "user": user, "profiles": profiles,
        "campaigns": campaigns, "transactions": transactions
    })

@app.get("/upload-cv", response_class=HTMLResponse)
async def upload_cv_page(request: Request):
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse("upload_cv.html", {"request": request})

@app.post("/upload-cv")
async def upload_cv(request: Request, profile_name: str = Form(...), cv_text: str = Form(...),
                    skills: str = Form(""), experience_years: int = Form(5),
                    target_titles: str = Form(""), target_locations: str = Form(""),
                    cover_letter_template: str = Form(""), email_template: str = Form(""),
                    home_country: str = Form("Lebanon"),
                    min_local_salary: float = Form(0),
                    min_international_salary: float = Form(0)):
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    
    conn = get_db()
    conn.execute("""INSERT INTO cv_profiles 
                    (user_id, profile_name, cv_text, cover_letter_template, email_template, 
                     skills, experience_years, target_titles, target_locations,
                     home_country, min_local_salary, min_international_salary)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                 (user_id, profile_name, cv_text, cover_letter_template, email_template,
                  skills, experience_years, target_titles, target_locations,
                  home_country, min_local_salary, min_international_salary))
    conn.commit()
    conn.close()
    
    return RedirectResponse("/dashboard", status_code=303)

@app.get("/new-campaign", response_class=HTMLResponse)
async def new_campaign_page(request: Request):
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    
    conn = get_db()
    profiles = [dict(r) for r in conn.execute("SELECT * FROM cv_profiles WHERE user_id = ?", (user_id,)).fetchall()]
    tiers = [dict(r) for r in conn.execute("SELECT * FROM pricing_tiers WHERE is_active = 1 ORDER BY price_usd").fetchall()]
    user = dict(conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)).fetchone())
    conn.close()
    
    return templates.TemplateResponse("new_campaign.html", {
        "request": request, "profiles": profiles, "tiers": tiers, "balance": user["wallet_balance"]
    })

@app.post("/create-campaign")
async def create_campaign(request: Request, profile_id: int = Form(...), company_count: int = Form(...)):
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    
    conn = get_db()
    user = dict(conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)).fetchone())
    tier = conn.execute("SELECT * FROM pricing_tiers WHERE company_count = ?", (company_count,)).fetchone()
    
    if not tier:
        conn.close()
        return RedirectResponse("/new-campaign", status_code=303)
    
    price = tier["price_usd"]
    if user["wallet_balance"] < price:
        conn.close()
        return RedirectResponse("/wallet", status_code=303)
    
    campaign_id = f"camp_{uuid.uuid4().hex[:16]}"
    order_id = f"ord_{uuid.uuid4().hex[:16]}"
    
    conn.execute("INSERT INTO orders (order_id, user_id, package_type, company_count, amount_usd, payment_method, payment_status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (order_id, user_id, tier["tier_name"], company_count, price, "wallet", "completed"))
    conn.execute("INSERT INTO campaigns (campaign_id, user_id, order_id, profile_id, total_companies) VALUES (?, ?, ?, ?, ?)",
                 (campaign_id, user_id, order_id, profile_id, company_count))
    
    new_balance = user["wallet_balance"] - price
    conn.execute("UPDATE users SET wallet_balance = ?, total_spent = total_spent + ? WHERE user_id = ?",
                 (new_balance, price, user_id))
    conn.execute("INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description) VALUES (?, ?, ?, ?, ?)",
                 (user_id, "spend", -price, new_balance, f"Campaign: {company_count} companies"))
    
    conn.commit()
    conn.close()
    
    enqueue_task("run_campaign", {"campaign_id": campaign_id})
    
    return RedirectResponse(f"/campaign/{campaign_id}", status_code=303)

@app.get("/campaign/{campaign_id}", response_class=HTMLResponse)
async def campaign_detail(request: Request, campaign_id: str):
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    
    conn = get_db()
    campaign = dict(conn.execute("SELECT * FROM campaigns WHERE campaign_id = ? AND user_id = ?",
                                 (campaign_id, user_id)).fetchone())
    emails = [dict(r) for r in conn.execute(
        "SELECT * FROM campaign_emails WHERE campaign_id = ? ORDER BY sent_at DESC",
        (campaign_id,)).fetchall()]
    conn.close()
    
    return templates.TemplateResponse("campaign_detail.html", {
        "request": request, "campaign": campaign, "emails": emails
    })

@app.get("/wallet", response_class=HTMLResponse)
async def wallet_page(request: Request):
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    
    conn = get_db()
    user = dict(conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone())
    transactions = [dict(r) for r in conn.execute(
        "SELECT * FROM wallet_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
        (user_id,)).fetchall()]
    conn.close()
    
    crypto_addresses = {
        "BTC": os.getenv("CRYPTO_BTC_ADDRESS", ""),
        "ETH": os.getenv("CRYPTO_ETH_ADDRESS", ""),
        "USDT": os.getenv("CRYPTO_USDT_ADDRESS", ""),
        "LTC": os.getenv("CRYPTO_LTC_ADDRESS", ""),
    }
    
    return templates.TemplateResponse("wallet.html", {
        "request": request, "user": user, "transactions": transactions,
        "crypto_addresses": crypto_addresses
    })

@app.get("/services", response_class=HTMLResponse)
async def services_page(request: Request):
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    
    from core.pricing_manager import SERVICE_PACKAGES, BOUQUET_PACKAGES
    
    conn = get_db()
    user = dict(conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone())
    
    # Fetch all purchased services
    purchased = [dict(r) for r in conn.execute(
        "SELECT * FROM purchased_services WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)).fetchall()]
    conn.close()
    
    # Build a lookup set of purchased package ids
    active_ids = {p["package_id"] for p in purchased if p["status"] == "active"}
    
    return templates.TemplateResponse("services.html", {
        "request": request,
        "user": user,
        "services": SERVICE_PACKAGES,
        "bouquets": BOUQUET_PACKAGES,
        "purchased": purchased,
        "active_ids": active_ids
    })

@app.post("/services/purchase")
async def purchase_service(request: Request, package_id: str = Form(...), service_type: str = Form(...)):
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    
    import uuid
    from core.pricing_manager import SERVICE_PACKAGES, BOUQUET_PACKAGES
    
    # 1. Find the service/bouquet name and price
    price = None
    name = None
    if service_type == "service":
        for s in SERVICE_PACKAGES:
            if s["package"] == package_id:
                price = s["price_usd"]
                name = s["name"]
                break
    elif service_type == "bouquet":
        for b in BOUQUET_PACKAGES:
            if b["bouquet"] == package_id:
                price = b["price_usd"]
                name = b["name"]
                break
                
    if price is None or name is None:
        return RedirectResponse("/services?error=invalid_package", status_code=303)
        
    conn = get_db()
    user = dict(conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)).fetchone())
    
    if user["wallet_balance"] < price:
        conn.close()
        return RedirectResponse("/services?error=insufficient_funds", status_code=303)
        
    # 2. Process purchase transactionally
    new_balance = user["wallet_balance"] - price
    conn.execute("UPDATE users SET wallet_balance = ?, total_spent = total_spent + ? WHERE user_id = ?",
                 (new_balance, price, user_id))
                 
    order_id = f"ord_{uuid.uuid4().hex[:16]}"
    conn.execute("""INSERT INTO orders (order_id, user_id, package_type, company_count, amount_usd, payment_method, payment_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                 (order_id, user_id, service_type, 0, price, "wallet", "completed"))
                 
    conn.execute("""INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description) 
                    VALUES (?, ?, ?, ?, ?)""",
                 (user_id, "spend", -price, new_balance, f"Purchase {service_type}: {name}"))
                 
    conn.execute("""INSERT INTO purchased_services (user_id, service_type, package_id, package_name, price_paid, status) 
                    VALUES (?, ?, ?, ?, ?, 'active')""",
                 (user_id, service_type, package_id, name, price))
                 
    conn.commit()
    conn.close()
    
    return RedirectResponse(f"/services?success=purchased&package={name}", status_code=303)

@app.post("/redeem")
async def redeem_code(request: Request, code: str = Form(...)):
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    
    conn = get_db()
    redeem = conn.execute("SELECT * FROM redeem_codes WHERE code = ? AND is_used = 0", (code,)).fetchone()
    
    if not redeem:
        conn.close()
        return RedirectResponse("/wallet?error=invalid_code", status_code=303)
    
    value = redeem["value_usd"]
    conn.execute("UPDATE redeem_codes SET is_used = 1, used_by = ?, used_at = CURRENT_TIMESTAMP WHERE code = ?",
                 (user_id, code))
    
    user = dict(conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)).fetchone())
    new_balance = user["wallet_balance"] + value
    conn.execute("UPDATE users SET wallet_balance = ? WHERE user_id = ?", (new_balance, user_id))
    conn.execute("INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description) VALUES (?, ?, ?, ?, ?)",
                 (user_id, "redeem", value, new_balance, f"Redeem code: {code}"))
    
    conn.commit()
    conn.close()
    
    return RedirectResponse("/wallet?success=redeemed", status_code=303)

@app.get("/api/docs", response_class=HTMLResponse)
async def api_docs(request: Request):
    return templates.TemplateResponse("api_docs.html", {"request": request})

@app.post("/api/v1/campaign")
async def api_create_campaign(api_key: str = Form(...), profile_cv: str = Form(...),
                               company_count: int = Form(...), target_titles: str = Form(""),
                               target_locations: str = Form("")):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE api_key = ? AND is_active = 1", (api_key,)).fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    user = dict(user)
    tier = conn.execute("SELECT * FROM pricing_tiers WHERE company_count = ?", (company_count,)).fetchone()
    if not tier:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid company count")
    
    if user["wallet_balance"] < tier["price_usd"]:
        conn.close()
        raise HTTPException(status_code=402, detail="Insufficient balance")
    
    profile_id = conn.execute(
        "INSERT INTO cv_profiles (user_id, profile_name, cv_text) VALUES (?, ?, ?)",
        (user["user_id"], f"API Profile {datetime.now().strftime('%Y%m%d%H%M')}", profile_cv)
    ).lastrowid
    
    campaign_id = f"camp_{uuid.uuid4().hex[:16]}"
    order_id = f"ord_{uuid.uuid4().hex[:16]}"
    
    conn.execute("INSERT INTO orders (order_id, user_id, package_type, company_count, amount_usd, payment_method, payment_status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (order_id, user["user_id"], tier["tier_name"], company_count, tier["price_usd"], "wallet", "completed"))
    conn.execute("INSERT INTO campaigns (campaign_id, user_id, order_id, profile_id, total_companies) VALUES (?, ?, ?, ?, ?)",
                 (campaign_id, user["user_id"], order_id, profile_id, company_count))
    
    new_balance = user["wallet_balance"] - tier["price_usd"]
    conn.execute("UPDATE users SET wallet_balance = ? WHERE user_id = ?", (new_balance, user["user_id"]))
    conn.execute("INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description) VALUES (?, ?, ?, ?, ?)",
                 (user["user_id"], "spend", -tier["price_usd"], new_balance, f"API Campaign: {company_count} companies"))
    
    conn.commit()
    conn.close()
    
    enqueue_task("run_campaign", {"campaign_id": campaign_id})
    
    return {"campaign_id": campaign_id, "status": "queued", "companies": company_count}

@app.get("/api/v1/campaign/{campaign_id}")
async def api_campaign_status(campaign_id: str, api_key: str = ""):
    if not api_key:
        raise HTTPException(status_code=400, detail="api_key required")
    conn = get_db()
    user = conn.execute("SELECT user_id FROM users WHERE api_key = ?", (api_key,)).fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    campaign = conn.execute("SELECT * FROM campaigns WHERE campaign_id = ? AND user_id = ?",
                            (campaign_id, user["user_id"])).fetchone()
    if not campaign:
        conn.close()
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = dict(campaign)
    stats = dict(conn.execute("""
        SELECT COUNT(*) as total,
        SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
        SUM(CASE WHEN opened_at IS NOT NULL THEN 1 ELSE 0 END) as opened,
        SUM(CASE WHEN responded_at IS NOT NULL THEN 1 ELSE 0 END) as responded
        FROM campaign_emails WHERE campaign_id = ?
    """, (campaign_id,)).fetchone())
    
    conn.close()
    return {**campaign, **stats}


async def run_campaign(campaign_id: str):
    """Background task to run a campaign."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        campaign = dict(conn.execute("SELECT * FROM campaigns WHERE campaign_id = ?", (campaign_id,)).fetchone())
        profile = dict(conn.execute("SELECT * FROM cv_profiles WHERE id = ?", (campaign["profile_id"],)).fetchone())
        
        user_row = conn.execute("SELECT * FROM users WHERE user_id = ?", (campaign["user_id"],)).fetchone()
        user = dict(user_row) if user_row else {}
        
        # Build user details for dynamic email personalization
        profession = "Senior Network Engineer"
        if profile.get("target_titles"):
            titles = [t.strip() for t in profile["target_titles"].split(",") if t.strip()]
            if titles:
                profession = titles[0]
                
        user_details = {
            "name": user.get("name") or config.CANDIDATE_NAME,
            "email": user.get("email") or config.CANDIDATE_EMAIL,
            "phone": user.get("phone") or config.CANDIDATE_PHONE,
            "linkedin": config.CANDIDATE_LINKEDIN,
            "profession": profession,
            "skills": profile.get("skills") or ""
        }
        
        conn.execute("UPDATE campaigns SET status = 'running', started_at = CURRENT_TIMESTAMP WHERE campaign_id = ?", (campaign_id,))
        conn.commit()
        
        search = MultiSourceSearch()
        email_engine = EmailEngine()
        
        jobs = search.search_all_sources(query=campaign.get('job_title', 'network engineer'), location=campaign.get('location', 'Dubai'), limit=campaign["total_companies"] * 2)
        
        sent_count = 0
        for job in jobs:
            if sent_count >= campaign["total_companies"]:
                break
            
            email_addr = job.get("email", "")
            if not email_addr:
                continue
            
            company = job.get("company", "Unknown")
            title = job.get("title", "Position")
            
            cover_html = CoverLetterWriter.write_html(company, title, {})
            
            success, result = await email_engine.send_application(
                email_addr, company, title, cover_html, config.CV_PATH,
                user_details=user_details
            )
            
            if success:
                tracking_id = generate_tracking_id()
                conn.execute("""INSERT INTO campaign_emails 
                              (campaign_id, company_name, job_title, email_address, status, tracking_id, sent_at)
                              VALUES (?, ?, ?, ?, 'sent', ?, CURRENT_TIMESTAMP)""",
                           (campaign_id, company, title, email_addr, tracking_id))
                sent_count += 1
                
                conn.execute("UPDATE campaigns SET sent_count = ? WHERE campaign_id = ?",
                           (sent_count, campaign_id))
                conn.commit()
            
            await asyncio.sleep(1)
        
        conn.execute("UPDATE campaigns SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE campaign_id = ?", (campaign_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"Campaign {campaign_id} completed: {sent_count} emails sent")
        
    except Exception as e:
        logger.error(f"Campaign {campaign_id} failed: {e}")
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("UPDATE campaigns SET status = 'failed' WHERE campaign_id = ?", (campaign_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(e, exc_info=True)


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)


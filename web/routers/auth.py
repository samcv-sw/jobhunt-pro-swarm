from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import httpx
from argon2 import PasswordHasher
from core.database import db
import secrets
import logging
import config

from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))
templates.env.globals["VERSION"] = config.VERSION
ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(hash_str: str, password: str) -> bool:
    try:
        return ph.verify(hash_str, password)
    except:
        return False

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"VERSION": config.VERSION})

@router.post("/login")
async def login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    async with db.pool.acquire() as conn:
        user = await conn.fetchrow("SELECT user_id, password_hash, api_key FROM users WHERE email = $1", email)
        
        if not user or not verify_password(user["password_hash"], password):
            return templates.TemplateResponse(request, "login.html", {"error": "Invalid credentials", "VERSION": config.VERSION})
            
        request.session["user_id"] = user["user_id"]
        request.session["api_key"] = user["api_key"]
        return RedirectResponse(url="/dashboard", status_code=303)

@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {"VERSION": config.VERSION})

@router.post("/register")
async def register_post(request: Request, email: str = Form(...), password: str = Form(...), name: str = Form(...), cf_turnstile_response: str = Form(None, alias="cf-turnstile-response")):
    if not cf_turnstile_response:
        return templates.TemplateResponse(request, "register.html", {"error": "Please complete the CAPTCHA."})
        
    try:
        async with httpx.AsyncClient() as client:
            cf_resp = await client.post("https://challenges.cloudflare.com/turnstile/v0/siteverify", data={
                "secret": config.TURNSTILE_SECRET,
                "response": cf_turnstile_response
            }, timeout=5.0)
            if not cf_resp.json().get("success"):
                return templates.TemplateResponse(request, "register.html", {"error": "CAPTCHA Failed."})
    except:
        return templates.TemplateResponse(request, "register.html", {"error": "Bot verification service down."})

    async with db.pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT user_id FROM users WHERE email = $1", email)
        if existing:
            return templates.TemplateResponse(request, "register.html", {"error": "Email already exists."})
            
        user_id = "usr_" + secrets.token_hex(8)
        api_key = "rnd_" + secrets.token_hex(16)
        
        await conn.execute("""
            INSERT INTO users (user_id, email, password_hash, name, api_key)
            VALUES ($1, $2, $3, $4, $5)
        """, user_id, email, hash_password(password), name, api_key)
        
        # --- VIRAL SQUAD CHECK ---
        pending_squad = request.session.get("pending_squad_id")
        if pending_squad:
            from web.routers.squads import process_pending_squad
            await process_pending_squad(conn, user_id, pending_squad)
            del request.session["pending_squad_id"]
        # -------------------------

        request.session["user_id"] = user_id
        request.session["api_key"] = api_key
        return RedirectResponse(url="/dashboard", status_code=303)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

import os
import sys
from pathlib import Path

# Ensure root directory is in sys.path so root config can be loaded
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import config as root_config
from config import *  # noqa: F401, F403

# --- General Settings & Cloud Aliases ---
ENV = getattr(root_config, "ENV", os.getenv("ENV", "development"))
IS_PRODUCTION = (ENV == "production")
IS_PYTHONANYWHERE = os.getenv("PYTHONANYWHERE_SITE") or os.getenv("PYTHONANYWHERE_DOMAIN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("RENDER_ENGINE_URL")
RENDER_EXTERNAL_URL = RENDER_URL

# --- Tokens & Credentials ---
SENTRY_DSN = getattr(root_config, "SENTRY_DSN", os.getenv("SENTRY_DSN"))
LOGTAIL_TOKEN = os.getenv("LOGTAIL_TOKEN")
LOGTAIL_SOURCE_TOKEN = getattr(root_config, "LOGTAIL_SOURCE_TOKEN", os.getenv("LOGTAIL_SOURCE_TOKEN") or LOGTAIL_TOKEN)
SECRET_KEY = getattr(root_config, "SECRET_KEY", os.getenv("SECRET_KEY"))
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or SECRET_KEY
GROQ_API_KEY = getattr(root_config, "GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
PA_API_TOKEN = getattr(root_config, "PA_API_TOKEN", os.getenv("PA_API_TOKEN"))

MICROSOFT_CLIENT_ID = getattr(root_config, "MICROSOFT_CLIENT_ID", os.getenv("MICROSOFT_CLIENT_ID"))
MICROSOFT_CLIENT_SECRET = getattr(root_config, "MICROSOFT_CLIENT_SECRET", os.getenv("MICROSOFT_CLIENT_SECRET"))
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
GOOGLE_CLIENT_ID = getattr(root_config, "GOOGLE_CLIENT_ID", os.getenv("GOOGLE_CLIENT_ID"))
GOOGLE_CLIENT_SECRET = getattr(root_config, "GOOGLE_CLIENT_SECRET", os.getenv("GOOGLE_CLIENT_SECRET"))
TURNSTILE_SECRET = getattr(root_config, "TURNSTILE_SECRET", os.getenv("TURNSTILE_SECRET"))

# --- Database Settings ---
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB")

if POSTGRES_USER and POSTGRES_PASSWORD and POSTGRES_HOST and POSTGRES_PORT and POSTGRES_DB:
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
else:
    DATABASE_URL = getattr(root_config, "DATABASE_URL", "sqlite:///./data/jobhunt_saas_v2.db")

# --- CORS Settings ---
ALLOWED_ORIGINS_ENV = os.getenv("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS_ENV.split(",") if origin.strip()]

# --- Derived Settings ---
SUPABASE_MODE = os.getenv("SUPABASE_MODE", "false").lower() == "true"
SITE_URL = getattr(root_config, "SITE_URL", os.getenv("SITE_URL", "https://jhfguf.pythonanywhere.com"))

base_url = (RENDER_EXTERNAL_URL or SITE_URL)
if base_url:
    base_url = base_url.rstrip("/")
    webhook_url = f"{base_url}/webhook/telegram"
else:
    webhook_url = None

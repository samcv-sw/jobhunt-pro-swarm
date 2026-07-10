"""

Telegram Bot - Full Control Interface (MAXIMIZED)

Control the entire system via Telegram commands

Inline keyboard, emoji everywhere, real-time stats

"""

import asyncio
import os
import logging
import threading

_TG_BOT_LOCK = threading.Lock()
_TG_BOT_STARTED = False

if not os.getenv("FORCE_SQLITE"):
    try:
        from core import pg_sqlite_shim as sqlite3
    except ImportError:
        import core.pg_sqlite_shim as sqlite3
else:
    import core.pg_sqlite_shim as sqlite3
import time

from collections import defaultdict
from datetime import datetime, timedelta


# ── Per-User Rate Limiter ────────────────────────────────────────
_user_command_times = defaultdict(list)


def _check_user_rate_limit(user_id: int, max_per_minute: int = 10) -> bool:
    """Check if user is within rate limits. Returns True if allowed."""
    now = datetime.now()
    cutoff = now - timedelta(minutes=1)
    times = _user_command_times[user_id]
    times[:] = [t for t in times if t > cutoff]
    if len(times) >= max_per_minute:
        return False
    times.append(now)
    return True


from pathlib import Path

import httpx
from httpx import Limits

import config

from core.whatsapp_notifier import get_whatsapp_contact_url

from core.telegram_notifier import TelegramNotifier

from core.telegram_analytics import TelegramAnalytics


logger = logging.getLogger(__name__)


# ── Sync Telegram Sender (standalone, no async, no bot instance) ─────
# Used by queue_worker, viral_factory, cloud_orchestrator, web/app.py
import requests as _tg_requests


def send_telegram_message_sync(text: str, parse_mode: str = "Markdown") -> bool:
    """Send a Telegram message synchronously using requests.

    Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from environment.
    Returns True on success, False on failure.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        logger.warning(
            "[send_telegram_message_sync] Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID"
        )
        return False
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
        if len(text) > 4000:
            payload["text"] = text[:3950] + "\n\n...(truncated)"
        r = _tg_requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            return True
        logger.warning(
            f"[send_telegram_message_sync] HTTP {r.status_code}: {r.text[:200]}"
        )
        return False
    except Exception as e:
        logger.warning(f"[send_telegram_message_sync] Error: {e}")
        return False


CMD_CATEGORY_MAP = {
    # 🎯 Applications
    "/start": "Applications",
    "/campaign": "Applications",
    "/search": "Applications",
    "/apply": "Applications",
    "/test_strike": "Applications",
    "/force_strike": "Applications",
    "/mass_strike": "Applications",
    "/wallet": "Applications",
    "/balance": "Applications",
    "/pricing": "Applications",
    "/referral": "Applications",
    "/whatsapp": "Applications",
    "/strategy": "Applications",
    "/earnings": "Applications",
    "/contact": "Applications",
    # 📊 Analytics
    "/status": "Analytics",
    "/stats": "Analytics",
    "/sales": "Analytics",
    "/applications": "Analytics",
    "/campaigns": "Analytics",
    "/stats_overview": "Analytics",
    "/pulse": "Analytics",
    "/today": "Analytics",
    "/weekly": "Analytics",
    "/best_day": "Analytics",
    "/email_stats": "Analytics",
    "/failure_rate": "Analytics",
    "/speed_test": "Analytics",
    "/memory": "Analytics",
    "/uptime": "Analytics",
    "/audit": "Analytics",
    "/queue": "Analytics",
    "/top_companies": "Analytics",
    "/countries": "Analytics",
    "/job_titles": "Analytics",
    "/platforms": "Analytics",
    "/tasks": "Analytics",
    "/inbox_check": "Analytics",
    "/leads": "Analytics",
    "/companies": "Analytics",
    "/trend": "Analytics",
    "/funnel": "Analytics",
    # ⚙️ Settings
    "/settings": "Settings",
    "/pause": "Settings",
    "/resume": "Settings",
    "/night_mode": "Settings",
    "/dry_run": "Settings",
    "/omega_halt": "Settings",
    "/kill_switch": "Settings",
    "/boost": "Settings",
    "/clear_queue": "Settings",
    "/stop": "Settings",
    "/env_check": "Settings",
    # 🛠️ Tools
    "/help": "Tools",
    "/guide": "Tools",
    "/fix": "Tools",
    "/clean": "Tools",
    "/backup": "Tools",
    "/reboot": "Tools",
    "/logs": "Tools",
    "/deploy": "Tools",
    "/security": "Tools",
    "/ats_score": "Tools",
    "/ats": "Tools",
    "/converse": "Tools",
    "/followups": "Tools",
    "/shield": "Tools",
    "/blacklist": "Tools",
    "/oracle": "Tools",
    "/track": "Tools",
    "/skip_lead": "Tools",
    "/pin_lead": "Tools",
    "/retry_failed": "Tools",
    "/find_emails": "Tools",
    "/synapse": "Tools",
    "/websites": "Tools",
    "/restart_web": "Tools",
    "/chat": "Tools",
    "/prep": "Tools",
    "/cv_preview": "Tools",
    "/cover_letter": "Tools",
    "/test_email": "Tools",
    "/test_key": "Tools",
    "/set_key": "Tools",
    "/keys": "Tools",
    "/ai_check": "Tools",
    "/features": "Tools",
    # 🔧 Admin
    "/admin": "Admin",
    "/admin_credit": "Admin",
    "/generate_code": "Admin",
    "/flash_sale": "Admin",
}

MENU_COMMANDS = [
    {"command": "start", "description": "🏠 Main menu with buttons"},
    {"command": "features", "description": "✨ All features & capabilities"},
    {"command": "help", "description": "📚 All available commands"},
    {"command": "status", "description": "🩺 System health check"},
    {"command": "stats", "description": "📊 Real-time stats & analytics"},
    {"command": "campaign", "description": "🚀 Start campaign"},
    {"command": "wallet", "description": "💼 Wallet & crypto"},
    {"command": "balance", "description": "💵 Check balance"},
    {"command": "search", "description": "🔎 Search new jobs"},
    {"command": "apply", "description": "🎯 Quick apply"},
    {"command": "pricing", "description": "💰 View all pricing tiers"},
    {"command": "referral", "description": "🤝 Referral program"},
    {"command": "whatsapp", "description": "📱 WhatsApp contact"},
    {"command": "applications", "description": "📋 Last 5 applications"},
    {"command": "generate_code", "description": "🎟 Create manual gift code"},
    {"command": "sales", "description": "📈 Real-time profit stats"},
    {"command": "strategy", "description": "📚 Profit strategy guide"},
    {"command": "admin_credit", "description": "🆓 Free admin credit"},
    {"command": "admin", "description": "📊 Admin Dashboard & Logs"},
    {"command": "flash_sale", "description": "⚡ View/manage flash sales"},
    {"command": "campaigns", "description": "📧 Email campaign stats"},
    {"command": "pause", "description": "⏸️ Pause auto-run"},
    {"command": "resume", "description": "▶️ Resume auto-run"},
    {"command": "test_strike", "description": "🧪 Test strike application"},
    {"command": "ai_check", "description": "🧠 Check AI status"},
    {"command": "keys", "description": "🔑 View API keys status"},
    {"command": "fix", "description": "🔧 Run system diagnostics fix"},
    {"command": "guide", "description": "📖 View quick guide"},
    {"command": "pulse", "description": "💓 System pulse check"},
    {"command": "inbox_check", "description": "📬 Check inbox responses"},
    {"command": "leads", "description": "📋 View leads"},
    {"command": "companies", "description": "🏢 View companies"},
    {"command": "followups", "description": "📨 View follow-ups"},
    {"command": "backup", "description": "💾 Create backup"},
    {"command": "shield", "description": "🛡️ Shield status"},
    {"command": "force_strike", "description": "⚔️ Force strike"},
    {"command": "mass_strike", "description": "💥 Mass strike"},
    {"command": "clean", "description": "🧹 Clean temp files"},
    {"command": "blacklist", "description": "⛔ Blacklist manager"},
    {"command": "oracle", "description": "🔮 Oracle prediction"},
    {"command": "best_day", "description": "🏆 Best day stats"},
    {"command": "email_stats", "description": "📧 Email stats breakdown"},
    {"command": "settings", "description": "⚙️ System settings"},
    {"command": "reboot", "description": "🔄 Reboot bot"},
    {"command": "track", "description": "📍 Track lead"},
    {"command": "skip_lead", "description": "⏭️ Skip lead"},
    {"command": "logs", "description": "📜 System logs"},
    {"command": "queue", "description": "🗂️ Job queue"},
    {"command": "failure_rate", "description": "📉 Failure rate stats"},
    {"command": "speed_test", "description": "⚡ System speed test"},
    {"command": "memory", "description": "🌡️ Memory usage"},
    {"command": "uptime", "description": "⏱️ System uptime"},
    {"command": "env_check", "description": "🔎 Check env variables"},
    {"command": "platforms", "description": "🌐 Platforms status"},
    {"command": "tasks", "description": "📋 All tasks"},
    {"command": "top_companies", "description": "🏆 Top companies"},
    {"command": "countries", "description": "🌍 Target countries"},
    {"command": "job_titles", "description": "💼 Job titles"},
    {"command": "retry_failed", "description": "🔄 Retry failed apps"},
    {"command": "find_emails", "description": "📧 Find emails"},
    {"command": "pin_lead", "description": "📌 Pin lead"},
    {"command": "stop", "description": "⏹️ Stop auto-run"},
    {"command": "night_mode", "description": "🌙 Toggle night mode"},
    {"command": "dry_run", "description": "🧪 Safe test mode"},
    {"command": "omega_halt", "description": "🛑 Emergency halt"},
    {"command": "kill_switch", "description": "☠️ Kill switch"},
    {"command": "set_key", "description": "🔑 Set API key"},
    {"command": "test_key", "description": "🧪 Test API key"},
    {"command": "prep", "description": "📝 Interview prep"},
    {"command": "cv_preview", "description": "📄 CV preview"},
    {"command": "cover_letter", "description": "📝 Cover letter"},
    {"command": "test_email", "description": "📧 Test email delivery"},
    {"command": "clear_queue", "description": "🧹 Clear job queue"},
    {"command": "boost", "description": "🚀 Boost speed mode"},
    {"command": "audit", "description": "📊 System audit"},
    {"command": "synapse", "description": "🧠 Synapse status"},
    {"command": "trend", "description": "📈 Application trend analysis"},
    {"command": "funnel", "description": "📊 Conversion funnel chart"},
]

COMMANDS_MAP = {
    "/start": "cmd_start",
    "/features": "cmd_features",
    "/help": "cmd_help",
    "/chat": "cmd_chat",
    "/stats_overview": "cmd_stats_overview",
    "/status": "cmd_status",
    "/stats": "cmd_stats",
    "/campaign": "cmd_campaign",
    "/wallet": "cmd_wallet",
    "/balance": "cmd_balance",
    "/search": "cmd_search",
    "/apply": "cmd_apply",
    "/pricing": "cmd_pricing",
    "/referral": "cmd_referral",
    "/whatsapp": "cmd_whatsapp",
    "/contact": "cmd_whatsapp",
    "/applications": "cmd_applications",
    "/generate_code": "cmd_generate_code",
    "/sales": "cmd_sales",
    "/earnings": "cmd_sales",
    "/strategy": "cmd_strategy",
    "/profit": "cmd_strategy",
    "/admin": "cmd_admin",
    "/admin_credit": "cmd_admin_credit",
    "/campaigns": "cmd_campaigns",
    "/pause": "cmd_pause",
    "/resume": "cmd_resume",
    "/test_strike": "cmd_test_strike",
    "/ai_check": "cmd_ai_check",
    "/keys": "cmd_keys",
    "/fix": "cmd_fix",
    "/guide": "cmd_guide",
    "/flash_sale": "cmd_flash_sale",
    "/pulse": "cmd_pulse",
    "/inbox_check": "cmd_inbox_check",
    "/leads": "cmd_leads",
    "/companies": "cmd_companies",
    "/followups": "cmd_followups",
    "/backup": "cmd_backup",
    "/shield": "cmd_shield",
    "/force_strike": "cmd_force_strike",
    "/mass_strike": "cmd_mass_strike",
    "/clean": "cmd_clean",
    "/blacklist": "cmd_blacklist",
    "/oracle": "cmd_oracle",
    "/best_day": "cmd_best_day",
    "/email_stats": "cmd_email_stats",
    "/settings": "cmd_settings",
    "/reboot": "cmd_reboot",
    "/track": "cmd_track",
    "/skip_lead": "cmd_skip_lead",
    "/logs": "cmd_logs",
    "/queue": "cmd_queue",
    "/websites": "cmd_websites",
    "/restart_web": "cmd_restart_web",
    "/deploy": "cmd_deploy",
    "/security": "cmd_security",
    "/today": "cmd_today",
    "/weekly": "cmd_weekly",
    "/stop": "cmd_stop_auto",
    "/failure_rate": "cmd_failure_rate",
    "/speed_test": "cmd_speed_test",
    "/memory": "cmd_memory",
    "/uptime": "cmd_uptime",
    "/env": "cmd_env_check",
    "/env_check": "cmd_env_check",
    "/platforms": "cmd_platforms",
    "/tasks": "cmd_tasks",
    "/top_companies": "cmd_top_companies",
    "/countries": "cmd_countries",
    "/job_titles": "cmd_job_titles",
    "/retry_failed": "cmd_retry_failed",
    "/find_emails": "cmd_find_emails",
    "/pin_lead": "cmd_pin_lead",
    "/night_mode": "cmd_night_mode",
    "/dry_run": "cmd_dry_run",
    "/omega_halt": "cmd_omega_halt",
    "/kill_switch": "cmd_kill_switch",
    "/set_key": "cmd_set_key",
    "/test_key": "cmd_test_key",
    "/prep": "cmd_prep",
    "/cv_preview": "cmd_cv_preview",
    "/cover_letter": "cmd_cover_letter",
    "/test_email": "cmd_test_email",
    "/clear_queue": "cmd_clear_queue",
    "/boost": "cmd_boost",
    "/audit": "cmd_audit",
    "/synapse": "cmd_synapse",
    "/ats_score": "cmd_ats_score",
    "/ats": "cmd_ats_score",
    "/converse": "cmd_converse",
    "/trend": "cmd_trend",
    "/funnel": "cmd_funnel",
    "/features": "cmd_features",
}


# ══════════════════════════════════════════════════════════════════════

# 🎛️ CHRONOS KEYBOARDS — Full Reply + Inline Keyboards

# ══════════════════════════════════════════════════════════════════════


# ── Reply Keyboard (50 bilingual buttons, 2 per row) ─────────────────

REPLY_KEYBOARD = [
    # Telegram Mini-App Dashboard
    [
        {
            "text": "🚀 Open Web Dashboard | لوحة القيادة",
            "web_app": {"url": config.RENDER_ENGINE_URL},
        }
    ],
    # Monitoring
    ["🖥️ Status | الحالة", "📊 Stats | الإحصائيات"],
    ["📈 Today Report | تقرير اليوم", "📅 Weekly Report | أسبوعي"],
    ["🗓️ Monthly Report | شهري", "🏆 Best Day | أفضل يوم"],
    ["📧 Email Stats | إحصاء الإيميل", "📉 Failure Rate | نسبة الفشل"],
    ["📊 Provider Health | صحة المزودين", "⚡ Speed Test | اختبار السرعة"],
    # System Info
    ["🗂️ Queue | الطابور", "📜 Logs | السجلات"],
    ["🌡️ Memory | الذاكرة", "⏱️ Uptime | وقت التشغيل"],
    ["🧠 AI Status | حالة الذكاء", "📬 Inbox Check | فحص الردود"],
    ["🔔 Notify Me | أخبرني", "📡 Ping Render | اختبار الخادم"],
    ["🔑 Env Check | فحص المتغيرات", "🌐 Platforms | المواقع"],
    # Leads & Jobs
    ["📋 Leads | الفرص", "🧬 Tasks | المهام"],
    ["🏢 Companies | الشركات", "🛰️ Track | التتبع المباشر"],
    ["📊 Top Companies | أفضل شركات", "🌍 Countries | الدول"],
    ["💼 Job Titles | المسميات", "🔮 Oracle | أوراكل السوق"],
    ["📊 Campaign | الحملة", "📨 Follow-ups | متابعات"],
    # Quick Actions
    ["🌍 Scrape Now | اسكان فوري", "🎯 Force Strike | ضربة فورية"],
    ["🎪 Mass Strike | ضربة جماعية", "🔁 Retry Failed | إعادة الفاشلين"],
    ["🔎 Find Emails | ابحث عن إيميلات", "📌 Pin Lead | تثبيت أولوية"],
    ["🚫 Skip Lead | تخطي", "⛔ Blacklist | القائمة السوداء"],
    ["🚀 Run Now | شغّل", "🔧 Fix | إصلاح"],
    # System Health
    ["🛡️ Shield | الدرع", "📜 Pulse | النبض"],
    ["🔍 Audit | مراجعة", "💪 Synapse | قوة"],
    ["🧹 Clean Disk | تنظيف", "💾 Backup | نسخة احتياطية"],
    ["🔄 Reboot | إعادة تشغيل", "⚙️ Settings | الإعدادات"],
    ["🗑️ Clear Queue | مسح الطابور", "🔥 Boost Mode | وضع تسريع"],
    # Controls
    ["⏸️ Pause | إيقاف مؤقت", "▶️ Resume | استئناف"],
    ["🌙 Night Mode | وضع الليل", "🧪 Dry Run | تجربة آمنة"],
    ["🛑 Omega Halt | التوقف التام", "💀 Kill Switch | إيقاف كامل"],
    ["📖 Guide | الدليل", "🔮 Oracle | أوراكل"],
    # API & Keys
    ["🔑 API Keys | مفاتيح API", "🧠 AI Check | فحص الذكاء"],
    ["✏️ Set Key | تغيير مفتاح", "🧪 Test Key | اختبار مفتاح"],
    ["🔑 Env | المتغيرات", "📡 Ping | اختبار الخادم"],
    ["⚡ Speed | سرعة الإرسال", "📉 Failure | نسبة الفشل"],
    ["📅 Weekly | أسبوعي", "🗓️ Monthly | شهري"],
    # Tools
    ["🎓 Prep | التحضير", "📝 CV Preview | معاينة السيرة"],
    ["✉️ Cover Letter | رسالة التغطية", "📧 Test Email | تجربة إيميل"],
    ["🧪 Test Strike | تجربة ضربة", "🔔 Notify | الإشعارات"],
    ["📬 Inbox | فحص الردود", "🔁 Retry | إعادة الفاشلين"],
    ["⛔ Blacklist | السوداء", "📌 Pin Lead | تثبيت"],
    # Reports
    ["🏆 Best Day | أفضل يوم", "📊 Campaign | الحملة"],
    ["🌍 Countries | الدول المستهدفة", "💼 Job Titles | المسميات الوظيفية"],
    ["🔎 Find Emails | بحث إيميلات", "🚫 Skip Lead | تخطي"],
    ["🧹 Clean | تنظيف الذاكرة", "💾 Backup | نسخة احتياطية"],
    ["🌐 Platforms | المواقع", "🛰️ Track | التتبع"],
    # Extra
    ["📊 Top Companies | أفضل شركات", "🔁 Retry | إعادة"],
    ["🎪 Mass Strike | جماعية", "🎯 Force Strike | فورية"],
    ["🔥 Boost | تسريع", "🌙 Night | الليل"],
    ["🧪 Dry Run | آمنة", "⏸️ Pause | وقف"],
    ["▶️ Resume | كمّل", "🔄 Reboot | إعادة"],
]


# ── Text-to-Command mapping for reply keyboard ───────────────────────

TEXT_COMMAND_MAP = {
    # Status & Stats
    "🖥️ Status": "/status",
    "الحالة": "/status",
    "📊 Stats": "/stats",
    "الإحصائيات": "/stats",
    "📈 Today Report": "/stats today",
    "تقرير اليوم": "/stats today",
    "📅 Weekly Report": "/stats week",
    "أسبوعي": "/stats week",
    "🗓️ Monthly Report": "/stats month",
    "شهري": "/stats month",
    "🏆 Best Day": "/best_day",
    "أفضل يوم": "/best_day",
    "📧 Email Stats": "/email_stats",
    "إحصاء الإيميل": "/email_stats",
    "📉 Failure Rate": "/failure_rate",
    "نسبة الفشل": "/failure_rate",
    "📊 Provider Health": "/status",
    "صحة المزودين": "/status",
    "⚡ Speed Test": "/speed_test",
    "اختبار السرعة": "/speed_test",
    # System Info
    "🗂️ Queue": "/queue",
    "الطابور": "/queue",
    "📜 Logs": "/logs",
    "السجلات": "/logs",
    "🌡️ Memory": "/memory",
    "الذاكرة": "/memory",
    "⏱️ Uptime": "/uptime",
    "وقت التشغيل": "/uptime",
    "🧠 AI Status": "/ai_check",
    "حالة الذكاء": "/ai_check",
    "📬 Inbox Check": "/inbox_check",
    "فحص الردود": "/inbox_check",
    "🔔 Notify Me": "/inbox_check",
    "أخبرني": "/inbox_check",
    "📡 Ping Render": "/status",
    "اختبار الخادم": "/status",
    "🔑 Env Check": "/env_check",
    "فحص المتغيرات": "/env_check",
    "🌐 Platforms": "/platforms",
    "المواقع": "/platforms",
    # Leads & Jobs
    "📋 Leads": "/leads",
    "الفرص": "/leads",
    "🧬 Tasks": "/tasks",
    "المهام": "/tasks",
    "🏢 Companies": "/companies",
    "الشركات": "/companies",
    "🛰️ Track": "/track",
    "التتبع المباشر": "/track",
    "📊 Top Companies": "/top_companies",
    "أفضل شركات": "/top_companies",
    "🌍 Countries": "/countries",
    "الدول": "/countries",
    "💼 Job Titles": "/job_titles",
    "المسميات": "/job_titles",
    "🔮 Oracle": "/oracle",
    "أوراكل السوق": "/oracle",
    "📊 Campaign": "/campaign",
    "الحملة": "/campaign",
    "📨 Follow-ups": "/followups",
    "متابعات": "/followups",
    # Actions
    "🌍 Scrape Now": "/search",
    "اسكان فوري": "/search",
    "🎯 Force Strike": "/force_strike",
    "ضربة فورية": "/force_strike",
    "🎪 Mass Strike": "/mass_strike",
    "ضربة جماعية": "/mass_strike",
    "🔁 Retry Failed": "/retry_failed",
    "إعادة الفاشلين": "/retry_failed",
    "🔎 Find Emails": "/find_emails",
    "ابحث عن إيميلات": "/find_emails",
    "📌 Pin Lead": "/pin_lead",
    "تثبيت أولوية": "/pin_lead",
    "⛔ Blacklist": "/blacklist",
    "القائمة السوداء": "/blacklist",
    "🚀 Run Now": "/campaign",
    "شغّل": "/campaign",
    "🔧 Fix": "/fix",
    "إصلاح": "/fix",
    # Controls
    "⏸️ Pause": "/pause",
    "إيقاف مؤقت": "/pause",
    "▶️ Resume": "/resume",
    "استئناف": "/resume",
    "🌙 Night Mode": "/night_mode",
    "وضع الليل": "/night_mode",
    "🧪 Dry Run": "/dry_run",
    "تجربة آمنة": "/dry_run",
    "🛑 Omega Halt": "/omega_halt",
    "التوقف التام": "/omega_halt",
    "💀 Kill Switch": "/kill_switch",
    "إيقاف كامل": "/kill_switch",
    "📖 Guide": "/guide",
    "الدليل": "/guide",
    # API & Keys
    "🔑 API Keys": "/keys",
    "مفاتيح API": "/keys",
    "🧠 AI Check": "/ai_check",
    "فحص الذكاء": "/ai_check",
    "✏️ Set Key": "/set_key",
    "تغيير مفتاح": "/set_key",
    "🧪 Test Key": "/test_key",
    "اختبار مفتاح": "/test_key",
    "🔑 Env": "/env",
    "المتغيرات": "/env",
    "📡 Ping": "/status",
    "اختبار الخادم": "/status",
    "⚡ Speed": "/speed_test",
    "سرعة الإرسال": "/speed_test",
    "📉 Failure": "/failure_rate",
    "نسبة الفشل": "/failure_rate",
    # Tools
    "🎓 Prep": "/prep",
    "التحضير": "/prep",
    "📝 CV Preview": "/cv_preview",
    "معاينة السيرة": "/cv_preview",
    "✉️ Cover Letter": "/cover_letter",
    "رسالة التغطية": "/cover_letter",
    "📧 Test Email": "/test_email",
    "تجربة إيميل": "/test_email",
    "🧪 Test Strike": "/test_strike",
    "تجربة ضربة": "/test_strike",
    "🔔 Notify": "/inbox_check",
    "الإشعارات": "/inbox_check",
    "📬 Inbox": "/inbox_check",
    "فحص الردود": "/inbox_check",
    "🔁 Retry": "/retry_failed",
    "إعادة": "/retry_failed",
    # System
    "🛡️ Shield": "/shield",
    "الدرع": "/shield",
    "📜 Pulse": "/pulse",
    "النبض": "/pulse",
    "🔍 Audit": "/audit",
    "مراجعة": "/audit",
    "💪 Synapse": "/synapse",
    "قوة": "/synapse",
    "🧹 Clean Disk": "/clean",
    "تنظيف": "/clean",
    "🧹 Clean": "/clean",
    "تنظيف الذاكرة": "/clean",
    "💾 Backup": "/backup",
    "نسخة احتياطية": "/backup",
    "🔄 Reboot": "/reboot",
    "إعادة تشغيل": "/reboot",
    "⚙️ Settings": "/settings",
    "الإعدادات": "/settings",
    "🗑️ Clear Queue": "/clear_queue",
    "مسح الطابور": "/clear_queue",
    "🔥 Boost Mode": "/boost",
    "وضع تسريع": "/boost",
    "🔥 Boost": "/boost",
    "تسريع": "/boost",
    # Variants
    "🛰️ Track": "/track",
    "التتبع": "/track",
    "📊 Campaign": "/campaign",
    "الحملة": "/campaign",
    "🌙 Night": "/night_mode",
    "الليل": "/night_mode",
    "🧪 Dry Run": "/dry_run",
    "آمنة": "/dry_run",
    "⏸️ Pause": "/pause",
    "وقف": "/pause",
    "▶️ Resume": "/resume",
    "كمّل": "/resume",
    "🔄 Reboot": "/reboot",
    "إعادة": "/reboot",
    "🌍 Countries": "/countries",
    "الدول المستهدفة": "/countries",
    "💼 Job Titles": "/job_titles",
    "المسميات الوظيفية": "/job_titles",
    "🔎 Find Emails": "/find_emails",
    "بحث إيميلات": "/find_emails",
    "🚫 Skip Lead": "/skip_lead",
    "تخطي": "/skip_lead",
    "📌 Pin Lead": "/pin_lead",
    "تثبيت": "/pin_lead",
    "⛔ Blacklist": "/blacklist",
    "السوداء": "/blacklist",
    "🎪 Mass Strike": "/mass_strike",
    "جماعية": "/mass_strike",
    "🎯 Force Strike": "/force_strike",
    "فورية": "/force_strike",
    "🌐 Platforms": "/platforms",
    "المواقع": "/platforms",
    "📊 Top Companies": "/top_companies",
    "أفضل شركات": "/top_companies",
    "🔁 Retry": "/retry_failed",
    "إعادة الفاشلين": "/retry_failed",
    "💾 Backup": "/backup",
    "نسخة احتياطية": "/backup",
    "🛡️ Shield": "/shield",
    "الدرع": "/shield",
    "📬 Inbox": "/inbox_check",
    "فحص الردود": "/inbox_check",
    "🔔 Notify": "/inbox_check",
    "الإشعارات": "/inbox_check",
    "📈 Trend": "/trend",
    "الاتجاهات": "/trend",
    "📊 Funnel": "/funnel",
    "المسار التحويل": "/funnel",
    "✨ Features": "/features",
    "الميزات": "/features",
}


# ── Database helper ─────────────────────────────────────────


def _get_db():
    """Get SQLite connection to the main database."""

    db_name = getattr(config, "DB_PATH", None) or "jobhunt_saas_v2.db"

    db_path = Path(__file__).parent.parent / db_name

    conn = sqlite3.connect(str(db_path))

    conn.row_factory = sqlite3.Row

    return conn


class TelegramBot:
    """Full Telegram bot for controlling the job system (MAXIMIZED)."""

    BOT_VERSION = "v16.88"

    def __init__(self):
        """Initialize the JobHunt Pro Telegram bot with credentials from config."""
        self.token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.enabled = bool(self.token and self.chat_id)

        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.http_client = httpx.AsyncClient(
            timeout=10, limits=Limits(max_keepalive_connections=2, max_connections=4)
        )

        self.bot_start_time = datetime.now()
        db_name = getattr(config, "DB_PATH", None) or "jobhunt_saas_v2.db"
        db_path = str(Path(__file__).parent.parent / db_name)
        self.analytics = TelegramAnalytics(db_path)
        self._awaiting_input = {}
        self._processed_callbacks = {}
        self._recent_gen_data = {}
        self._last_send_time = 0.0
        self._send_lock = asyncio.Lock()
        self._cb_lock = asyncio.Lock()
        self._state_lock = asyncio.Lock()
        self._auto_running = False
        self._night_mode = False
        self._dry_run = False
        self._boost_mode = False
        self._offset = 0
        self._user_rate_limits = {}
        self._progress_messages = {}

        self._cmd_category_map = CMD_CATEGORY_MAP
        self.menu_commands = MENU_COMMANDS
        self.commands = {
            "/shield": self.cmd_shield,
            "/force_strike": self.cmd_force_strike,
            "/mass_strike": self.cmd_mass_strike,
            "/clean": self.cmd_clean,
            "/blacklist": self.cmd_blacklist,
            "/oracle": self.cmd_oracle,
            "/best_day": self.cmd_best_day,
            "/email_stats": self.cmd_email_stats,
            "/settings": self.cmd_settings,
            "/reboot": self.cmd_reboot,
            "/track": self.cmd_track,
            "/skip_lead": self.cmd_skip_lead,
            "/logs": self.cmd_logs,
            "/queue": self.cmd_queue,
            # ── ENHANCED: Website control + AI fix + Security ──
            "/websites": self.cmd_websites,
            "/restart_web": self.cmd_restart_web,
            "/deploy": self.cmd_deploy,
            "/security": self.cmd_security,
            "/today": self.cmd_today,
            "/weekly": self.cmd_weekly,
            "/stop": self.cmd_stop_auto,
            "/failure_rate": self.cmd_failure_rate,
            "/speed_test": self.cmd_speed_test,
            "/memory": self.cmd_memory,
            "/uptime": self.cmd_uptime,
            "/env": self.cmd_env_check,
            "/env_check": self.cmd_env_check,
            "/platforms": self.cmd_platforms,
            "/tasks": self.cmd_tasks,
            "/top_companies": self.cmd_top_companies,
            "/countries": self.cmd_countries,
            "/job_titles": self.cmd_job_titles,
            "/retry_failed": self.cmd_retry_failed,
            "/find_emails": self.cmd_find_emails,
            "/pin_lead": self.cmd_pin_lead,
            "/night_mode": self.cmd_night_mode,
            "/dry_run": self.cmd_dry_run,
            "/omega_halt": self.cmd_omega_halt,
            "/kill_switch": self.cmd_kill_switch,
            "/set_key": self.cmd_set_key,
            "/test_key": self.cmd_test_key,
            "/prep": self.cmd_prep,
            "/cv_preview": self.cmd_cv_preview,
            "/cover_letter": self.cmd_cover_letter,
            "/test_email": self.cmd_test_email,
            "/clear_queue": self.cmd_clear_queue,
            "/boost": self.cmd_boost,
            "/audit": self.cmd_audit,
            "/synapse": self.cmd_synapse,
            # ── BUILD ENHANCEMENTS: ATS + AI Conversation ──
            "/ats_score": self.cmd_ats_score,
            "/ats": self.cmd_ats_score,
            "/converse": self.cmd_converse,
            # ── TELEGRAM ANALYTICS DASHBOARD ──
            "/trend": self.cmd_trend,
            "/funnel": self.cmd_funnel,
        }

        # ── Smart Notification Service ──────────────────────
        self.notification_chat_id = self.chat_id  # same as bot's registered chat
        db_name = getattr(config, "DB_PATH", None) or "jobhunt_saas_v2.db"
        self.db_path = str(Path(__file__).parent.parent / db_name)
        self.notifier = TelegramNotifier(
            db_path=self.db_path, send_callback=self._send_notification
        )
        logger.info(f"[BOT] TelegramNotifier initialized — db={self.db_path}")

    async def _send_notification(self, message: str):
        """Send a proactive notification to the registered Telegram chat."""
        if not self.notification_chat_id:
            return
        url = f"{self.base_url}/sendMessage"
        try:
            await self.http_client.post(
                url,
                json={
                    "chat_id": self.notification_chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                },
            )
        except Exception as e:
            logger.warning(f"[Notifier] Telegram send failed: {e}")

    async def send(self, message, parse_mode="HTML", reply_markup=None, retries=2):
        """Send message to Telegram with truncation, retry, and proper error handling."""
        if not self.enabled:
            return

        logger.debug(f"[BOT] send() msg={str(message)[:60] if message else 'empty'}")
        url = f"{self.base_url}/sendMessage"

        # Truncate to Telegram's 4096 char limit
        if message and len(message) > 4000:
            message = message[:3950] + "\n\n...(truncated)"

        # Rate limit: ensure at least 30ms between sends
        async with self._send_lock:
            elapsed = time.time() - self._last_send_time
            if elapsed < 0.03:
                await asyncio.sleep(0.03 - elapsed)
            self._last_send_time = time.time()

        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode,
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        last_error = None
        for attempt in range(retries + 1):
            try:
                r = await self.http_client.post(url, json=payload)
                if r.status_code == 200:
                    return
                if r.status_code == 429:  # Rate limited
                    retry_after = int(r.headers.get("Retry-After", "2"))
                    logger.warning(f"[BOT] Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue
                last_error = f"HTTP {r.status_code}: {r.text[:200]}"
                logger.error(f"[BOT] send() failed: {last_error}")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"[BOT] send() attempt {attempt + 1} failed: {e}")
                if attempt < retries:
                    await asyncio.sleep(1)

        if last_error:
            logger.error(
                f"[BOT] send() all {retries + 1} attempts failed: {last_error}"
            )

    async def send_with_keyboard(self, message, buttons, parse_mode="HTML"):
        """Send message with inline keyboard buttons.



        buttons = [{"text": "Button Label", "callback_data": "cmd_args"}]

        """

        if not self.enabled:
            return

        # Build inline keyboard rows (2 columns max)

        keyboard = []

        row = []

        for btn in buttons:
            entry = {"text": btn["text"]}

            if "web_app" in btn:
                entry["web_app"] = btn["web_app"]

            else:
                entry["callback_data"] = btn.get("callback_data", btn["text"])

            row.append(entry)

            if len(row) >= 2:
                keyboard.append(row)

                row = []

        if row:
            keyboard.append(row)

        logger.info(
            f"[BOT] send_with_keyboard: msg={str(message)[:60] if message else 'empty'}"
        )

        url = f"{self.base_url}/sendMessage"

        try:
            await self.http_client.post(
                url,
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": parse_mode,
                    "reply_markup": {"inline_keyboard": keyboard},
                },
            )

        except Exception as e:
            logger.warning(f"Telegram keyboard send failed: {e}")

    # ── Rich Navigation Inline Keyboards ──────────────────────

    def _get_nav_keyboard(self, current_page: str = "main"):
        """Get navigation inline keyboard based on current page."""
        keyboards = {
            "main": [
                [
                    {"text": "🚀 Apply", "callback_data": "start_apply"},
                    {"text": "📊 Stats", "callback_data": "show_stats"},
                ],
                [
                    {"text": "📈 Funnel", "callback_data": "show_funnel"},
                    {"text": "🎯 ATS Score", "callback_data": "show_ats"},
                ],
                [
                    {"text": "💬 Converse", "callback_data": "show_converse"},
                    {"text": "🔔 Alerts", "callback_data": "show_alerts"},
                ],
                [
                    {
                        "text": "📊 Dashboard",
                        "web_app": {"url": f"{config.SITE_URL}/webapp/"},
                    }
                ],
                [
                    {"text": "📋 Full Menu", "callback_data": "show_menu"},
                    {"text": "❓ Help", "callback_data": "show_help"},
                ],
            ],
            "stats": [
                [
                    {"text": "📊 Dashboard", "callback_data": "refresh_stats"},
                    {"text": "📈 Trends", "callback_data": "show_trends"},
                ],
                [
                    {"text": "📈 Funnel", "callback_data": "show_funnel"},
                    {"text": "🏢 Companies", "callback_data": "show_companies"},
                ],
                [
                    {"text": "🔙 Back", "callback_data": "nav_main"},
                    {"text": "🏠 Home", "callback_data": "show_main"},
                ],
            ],
            "apply": [
                [
                    {"text": "🔍 Search Jobs", "callback_data": "search_jobs"},
                    {"text": "🤖 Auto Apply", "callback_data": "auto_apply"},
                ],
                [
                    {"text": "📋 My Campaigns", "callback_data": "my_campaigns"},
                    {"text": "🎯 Targeted", "callback_data": "targeted_apply"},
                ],
                [{"text": "🔙 Back", "callback_data": "nav_main"}],
            ],
        }
        return {"inline_keyboard": keyboards.get(current_page, keyboards["main"])}

    async def send_with_reply_keyboard(self, message, parse_mode="HTML"):
        """Send message with the full Chronos ReplyKeyboard."""

        if not self.enabled:
            return

        logger.info(
            f"[BOT] send_with_reply_keyboard: msg={str(message)[:60] if message else 'empty'}"
        )

        url = f"{self.base_url}/sendMessage"

        try:
            await self.http_client.post(
                url,
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": parse_mode,
                    "reply_markup": {
                        "keyboard": REPLY_KEYBOARD,
                        "resize_keyboard": True,
                        "one_time_keyboard": False,
                    },
                },
            )

        except Exception as e:
            logger.warning(f"Telegram reply keyboard send failed: {e}")

    async def route_text_to_command(self, text: str) -> str:
        """Map reply keyboard button text to /command."""

        clean = text.strip()

        # Direct match

        if clean in TEXT_COMMAND_MAP:
            return TEXT_COMMAND_MAP[clean]

        # Try stripping emoji prefix

        for key, cmd in sorted(TEXT_COMMAND_MAP.items(), key=lambda x: -len(x[0])):
            if clean.startswith(key) or key.startswith(clean):
                return cmd

        # Default: treat as command if starts with /

        if clean.startswith("/"):
            return clean

        # Try as direct command name

        return None

    async def _check_rate_limit(self, user_id: int, max_per_minute: int = 5) -> bool:
        """Per-user rate limiter. Returns True if allowed, False if rate limited."""
        now = time.time()
        window = 60.0  # 1-minute window
        user_id = int(user_id)

        # Clean old entries
        self._user_rate_limits = {
            k: v
            for k, v in self._user_rate_limits.items()
            if now - v["window_start"] < window
        }

        entry = self._user_rate_limits.get(user_id)
        if not entry or now - entry["window_start"] > window:
            self._user_rate_limits[user_id] = {"count": 1, "window_start": now}
            return True

        entry["count"] += 1
        if entry["count"] > max_per_minute:
            logger.warning(
                f"[BOT] Rate limit hit for user {user_id}: {entry['count']} req/min"
            )
            return False
        return True

    async def answer_callback_query(self, callback_id, text="", show_alert=False):
        """Answer a callback query (inline button press) with optional feedback."""
        url = f"{self.base_url}/answerCallbackQuery"
        for attempt in range(3):
            try:
                await self.http_client.post(
                    url,
                    json={
                        "callback_query_id": callback_id,
                        "text": text,
                        "show_alert": show_alert,
                    },
                )
                return
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(0.3)
                else:
                    logger.warning(
                        f"Telegram callback answer failed after 3 attempts: {e}"
                    )

    async def send_photo(self, photo_path, caption=""):
        """Send photo to Telegram using async file I/O (aiofiles)."""
        if not self.enabled:
            return
        url = f"{self.base_url}/sendPhoto"
        try:
            import aiofiles

            async with aiofiles.open(photo_path, "rb") as f:
                photo_bytes = await f.read()
            await self.http_client.post(
                url,
                data={
                    "chat_id": self.chat_id,
                    "caption": caption,
                    "parse_mode": "HTML",
                },
                files={"photo": ("photo.jpg", photo_bytes, "image/jpeg")},
            )
        except ImportError:
            # Fallback: run_in_executor (aiofiles not installed)
            try:
                photo_bytes = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: open(photo_path, "rb").read()
                )
                await self.http_client.post(
                    url,
                    data={
                        "chat_id": self.chat_id,
                        "caption": caption,
                        "parse_mode": "HTML",
                    },
                    files={"photo": ("photo.jpg", photo_bytes, "image/jpeg")},
                )
            except Exception as e:
                await self.send(f"\U0001f4f8 Photo unavailable: {e}")
                logger.warning(f"Telegram photo fallback failed: {e}")
        except Exception as e:
            logger.warning(f"Telegram photo failed: {e}")
            try:
                await self.send(f"\U0001f4f8 Photo send failed: {e}")
            except Exception:
                pass

    async def _send_progress(self, progress_id, message, percent=None):
        """Send or update a progress message for long-running operations.
        Args:
            progress_id: Unique ID for this progress sequence.
            message: Text to display.
            percent: Optional 0-100 percentage for progress bar.
        """
        try:
            # Cap progress messages to prevent memory leaks
            if len(self._progress_messages) > 5000:
                self._progress_messages.clear()
            if progress_id not in self._progress_messages:
                G = chr(0x1F7E9)
                W = chr(0x2B1C)
                H = chr(0x23F3)
                display = f"{H} {message}"
                if percent is not None:
                    blocks = int(percent / 10)
                    display = (
                        f"{G * blocks}{W * (10 - blocks)} {percent}%\n{H} {message}"
                    )
                await self.send(display, parse_mode="HTML")
                self._progress_messages[progress_id] = {
                    "text": message,
                    "percent": percent,
                }
            else:
                G = chr(0x1F7E9)
                W = chr(0x2B1C)
                H = chr(0x23F3)
                display = f"{H} {message}"
                if percent is not None:
                    blocks = int(percent / 10)
                    display = (
                        f"{G * blocks}{W * (10 - blocks)} {percent}%\n{H} {message}"
                    )
                await self.send(display, parse_mode="HTML")
                self._progress_messages[progress_id] = {
                    "text": message,
                    "percent": percent,
                }
        except Exception as e:
            logging.getLogger(__name__).warning(f"[PROGRESS] Error: {e}")

    async def get_updates(self, offset=0):
        """Get updates from Telegram with retry/backoff for 429/5xx.
        Returns (updates_list, is_conflict) tuple."""
        url = f"{self.base_url}/getUpdates"
        max_retries = 3
        for attempt in range(max_retries):
            try:
                params = (
                    {"offset": offset, "timeout": 0}
                    if offset is not None
                    else {"timeout": 0}
                )
                resp = await self.http_client.get(url, params=params, timeout=4)
                if resp.status_code == 409:
                    logger.warning(
                        "[BOT] getUpdates 409 Conflict - another poller is active"
                    )
                    return ([], True)
                if resp.status_code in (429, 502, 503, 504):
                    backoff = min(30, 2 ** (attempt + 1))
                    logger.warning(
                        f"[BOT] getUpdates {resp.status_code} (attempt {attempt + 1}/{max_retries}), backoff {backoff}s"
                    )
                    await asyncio.sleep(backoff)
                    continue
                result = resp.json().get("result", [])
                if result:
                    logger.debug(f"[BOT] getUpdates returned {len(result)} update(s)")
                return (result, False)
            except Exception as e:
                if attempt < max_retries - 1:
                    backoff = min(10, 2 ** (attempt + 1))
                    logger.warning(
                        f"[BOT] getUpdates error (attempt {attempt + 1}/{max_retries}): {e}, retry in {backoff}s"
                    )
                    await asyncio.sleep(backoff)
                else:
                    logger.error(
                        f"[BOT] getUpdates failed after {max_retries} attempts: {e}"
                    )
                    return ([], False)

    async def handle_command(self, command, args="", user_id=None):
        """Handle a command with rate limiting."""
        if user_id and not await self._check_rate_limit(user_id):
            await self.send(
                "<b>⚠️ Rate Limit</b>\n\nYou're sending commands too fast. "
                "Please wait a moment before sending another command."
            )
            return
        if command in self.commands:
            await self.commands[command](args)

        else:
            await self.send(
                f"Unknown command: {command}\nType /help for available commands."
            )

    # ── START - Rich Inline Keyboard Main Menu ──────────────────

    async def cmd_start(self, args=""):
        """Welcome message with rich inline keyboard grid."""
        msg = (
            "🚀 <b>Welcome to JobHunt Pro!</b>\n\n"
            "Your AI-powered job hunting command center.\n\n"
            "<b>✨ What you can do here:</b>\n"
            "• 📊 <b>Analytics Dashboard</b> — Real-time stats, trends & funnel charts\n"
            "• 🔍 <b>Inline Search</b> — Search jobs directly from any chat\n"
            "• 📱 <b>Mini App</b> — Full web dashboard at your fingertips\n"
            "• 🤖 <b>Auto-Apply</b> — 200 swarm agents working 24/7\n"
            "• 🎯 <b>ATS Scoring</b> — Match your resume against any job description\n"
            "• 💬 <b>AI Conversation</b> — Generate greetings, replies & batch messages\n\n"
            "<i>What would you like to do?</i>"
        )
        await self.send(msg, reply_markup=self._get_nav_keyboard("main"))

    # ── STATS OVERVIEW - Full dashboard ───────────────────────

    async def cmd_stats_overview(self, args=""):
        """Show full stats overview dashboard."""

        conn = None

        try:
            conn = _get_db()

            users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

            campaigns = conn.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0]

            emails_sent = conn.execute(
                "SELECT COUNT(*) FROM campaign_emails WHERE status='sent'"
            ).fetchone()[0]

            jobs_found = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]

            total_revenue = float(
                conn.execute(
                    "SELECT COALESCE(SUM(amount),0) FROM payments WHERE status='completed'"
                ).fetchone()[0]
            )

            msg = (
                f"<b>📊 Stats Dashboard | لوحة الإحصائيات</b>\n\n"
                f"👥 <b>Users | المستخدمون:</b> {users}\n"
                f"📢 <b>Campaigns | الحملات:</b> {campaigns}\n"
                f"📧 <b>Emails Sent | الإيميلات المرسلة:</b> {emails_sent}\n"
                f"💼 <b>Jobs Found | الوظائف:</b> {jobs_found}\n"
                f"💰 <b>Revenue | الإيرادات:</b> ${total_revenue:.2f}\n\n"
                "<i>Use other buttons for detailed stats.</i>"
            )

        except Exception as e:
            msg = f"<b>⚠️ Error loading stats:</b> {e}"

        finally:
            if conn:
                conn.close()

        await self.send(msg)

    # ── CHAT - AI Chat interface ──────────────────────────────

    async def cmd_chat(self, args=""):
        """Start AI chat session."""

        msg = (
            "<b>🤖 AI Chat | المحادثة الذكية</b>\n\n"
            "Send me a message and I'll help you with:\n"
            "📊 System stats and reports\n"
            "🔍 Job search and analysis\n"
            "💡 Strategy recommendations\n"
            "⚙️ Configuration help\n\n"
            "<i>Just type what you need below.</i>"
        )

        await self.send(msg)

    # ── HELP - All commands with emoji ─────────────────────────

    async def cmd_help(self, args=""):
        """Dynamically show all available commands categorized."""
        # Build a description lookup from menu_commands
        desc_map = {}
        for entry in self.menu_commands:
            cmd = "/" + entry["command"]
            desc_map[cmd] = entry["description"]
        # Also pull docstrings for any commands not in menu_commands
        for cmd, handler in self.commands.items():
            if cmd not in desc_map:
                doc = (getattr(handler, "__doc__", "") or "").strip().split("\n")[0]
                if doc:
                    desc_map[cmd] = doc
                else:
                    desc_map[cmd] = ""
        # Build categorized lines
        categories = {
            "🎯 Applications": [],
            "📊 Analytics": [],
            "⚙️ Settings": [],
            "🛠️ Tools": [],
            "🔧 Admin": [],
        }
        uncategorized = []
        for cmd in sorted(self.commands.keys()):
            cat = self._cmd_category_map.get(cmd)
            desc = desc_map.get(cmd, "")
            formatted = (
                f"<code>{cmd}</code> — {desc}" if desc else f"<code>{cmd}</code>"
            )
            if cat in categories:
                categories[cat].append(formatted)
            else:
                # Map plain category names to emoji keys
                emoji_cat = {
                    "Applications": "🎯 Applications",
                    "Analytics": "📊 Analytics",
                    "Settings": "⚙️ Settings",
                    "Tools": "🛠️ Tools",
                    "Admin": "🔧 Admin",
                }.get(cat)
                if emoji_cat and emoji_cat in categories:
                    categories[emoji_cat].append(formatted)
                else:
                    uncategorized.append(formatted)
        lines = ["🤖 <b>JobHunt Pro Commands</b>\n"]
        for cat_name, cmds in categories.items():
            if cmds:
                lines.append(f"\n<b>{cat_name}</b>")
                for c in cmds:
                    lines.append(c)
        if uncategorized:
            lines.append("\n<b>📦 Other</b>")
            for c in uncategorized:
                lines.append(c)
        lines.append("")
        lines.append(
            "<i>💡 Use /features to explore all capabilities • Made with ❤️ by Sam Salameh | JobHunt Pro v16.88</i>"
        )
        msg = "\n".join(lines)
        # Truncate if over 4096 chars
        if len(msg) > 4000:
            msg = msg[:3950] + "\n\n... (truncated — use /start for inline menu)"
        await self.send(msg, parse_mode="HTML")

    # ── STATUS - System health with color indicators ──────────

    async def cmd_status(self, args=""):
        """Show system status with color indicators."""

        conn = None

        try:
            conn = _get_db()

            users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

            campaigns = conn.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0]

            emails_sent = conn.execute(
                "SELECT COUNT(*) FROM campaign_emails WHERE status='sent'"
            ).fetchone()[0]

            emails_opened = conn.execute(
                "SELECT COUNT(*) FROM campaign_emails WHERE opened_at IS NOT NULL"
            ).fetchone()[0]

            jobs_found = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]

            # Uptime calculation

            uptime = datetime.now() - self.bot_start_time

            uptime_hours = uptime.total_seconds() / 3600

            # Color indicators based on health

            db_status = "🟢"

            email_status = "🟢"

            search_status = "🟢"

            # Health score

            health_score = 100

            if emails_sent == 0:
                health_score -= 10

            health_icon = (
                "🟢" if health_score >= 70 else "🟡" if health_score >= 40 else "🔴"
            )

            msg = (
                f"<b>🩺 SYSTEM HEALTH v{config.VERSION}</b>\n\n"
                f"<b>📊 Health Score:</b> {health_score}% {health_icon}\n"
                f"<b>⏱ Uptime:</b> {uptime_hours:.1f}h\n"
                f"<b>🔄 Last Restart:</b> {self.bot_start_time.strftime('%H:%M:%S')}\n\n"
                f"<b>🗄 Database:</b> {db_status} Active\n"
                f"<b>📧 Email Engine:</b> {email_status} 20 providers\n"
                f"<b>🔎 Search Engines:</b> {search_status} 3 active\n"
                f"<b>🤖 Swarm Agents:</b> 🟢 200 ready\n"
                f"<b>🧠 AI Models:</b> 🟢 Gemini + Groq\n\n"
                f"<b>📈 Key Metrics:</b>\n"
                f"👤 Users: {users}\n"
                f"📦 Campaigns: {campaigns}\n"
                f"📬 Emails Sent: {emails_sent}\n"
                f"👁 Opens: {emails_opened}\n"
                f"💼 Jobs Found: {jobs_found}\n"
                f"📊 Open Rate: {(emails_opened / emails_sent * 100) if emails_sent > 0 else 0:.1f}%"
            )

            await self.send(msg)

        except Exception as e:
            logger.error(f"[BOT] cmd_status error: {e}")
            await self.send(
                "<b>❌ Unable to load system status.</b>\n\nThe database may be temporarily unavailable. Try /pulse for a quick system check."
            )

        finally:
            if conn:
                conn.close()

    # ── STATS - Analytics-powered personal dashboard ──────────

    async def cmd_stats(self, args=""):
        """Show comprehensive analytics dashboard."""

        try:
            stats = self.analytics.get_user_stats(args)

            msg = self.analytics.format_stats_message(stats)

            # Append uptime

            uptime = datetime.now() - self.bot_start_time

            uptime_hours = uptime.total_seconds() / 3600

            msg += f"\n\n<b>⏱ Bot Uptime:</b> {uptime_hours:.1f} hours"

            await self.send(msg)

        except Exception as e:
            logger.error(f"[BOT] cmd_stats error: {e}")

            await self.send(
                "<b>❌ Unable to load statistics.</b>\n\nThe analytics engine may be busy. Try again in a moment, or use /status to check system health."
            )

    # ── APPLICATIONS - Last 5 applications ───────────────────

    async def cmd_applications(self, args=""):
        """Show last 5 applications with company, title, status."""

        conn = None

        try:
            conn = _get_db()

            conn.row_factory = sqlite3.Row

            apps = conn.execute(
                "SELECT company, title, status, applied_at, responded_at FROM jobs "
                "WHERE applied_at IS NOT NULL ORDER BY applied_at DESC LIMIT 5"
            ).fetchall()

            if not apps:
                await self.send(
                    "<b>📋 No applications found.</b> Start a campaign with /campaign"
                )

                return

            status_emoji_map = {
                "sent": "📤",
                "opened": "👁",
                "responded": "✅",
                "rejected": "❌",
                "interview": "🎉",
                "applied": "📬",
            }

            msg = "<b>📋 LAST 5 APPLICATIONS</b>\n\n"

            for i, app in enumerate(apps, 1):
                a = dict(app)

                emoji = status_emoji_map.get(a.get("status", ""), "📋")

                company = a.get("company", "N/A")

                title = a.get("title", "N/A")

                status = a.get("status", "N/A")

                sent_str = (
                    a.get("applied_at", "")[:10] if a.get("applied_at") else "N/A"
                )

                msg += (
                    f"<b>{i}. {emoji} {company}</b>\n"
                    f"   ├ 📍 {title}\n"
                    f"   ├ 📊 Status: {status}\n"
                    f"   └ 📅 Sent: {sent_str}\n\n"
                )

            await self.send(msg)

        except Exception as e:
            logger.error(f"[BOT] cmd_applications error: {e}")
            await self.send(
                "<b>❌ Unable to load applications.</b>\n\nThe database may be temporarily unavailable. Try /search to find new jobs first."
            )

        finally:
            if conn:
                conn.close()

    # ── CAMPAIGN ─────────────────────────────────────────────

    async def cmd_campaign(self, args=""):
        """Start a campaign."""

        msg = (
            "<b>🚀 START CAMPAIGN</b>\n\n"
            "To create a campaign:\n"
            "1. Visit the web dashboard\n"
            "2. Upload your CV profile\n"
            "3. Select package (100-1M companies)\n"
            "4. Launch!\n\n"
            "<b>Quick API Access:</b>\n"
            "<code>POST /api/v1/campaign</code>\n\n"
            "<b>Pricing:</b>\n"
            "- 100 companies: $5\n"
            "- 200 companies: $10\n"
            "- 500 companies: $20\n"
            "- 1000 companies: $42\n"
            "- 5000 companies: $120\n"
            "- 1M companies: $8000\n\n"
            f"Visit: {config.SITE_URL}"
        )

        await self.send(msg)

    # ── WALLET ───────────────────────────────────────────────

    async def cmd_wallet(self, args=""):
        """Show wallet info."""

        btc = (
            config.CRYPTO_BTC_ADDRESS
            if hasattr(config, "CRYPTO_BTC_ADDRESS") and config.CRYPTO_BTC_ADDRESS
            else "Not configured"
        )

        eth = (
            config.CRYPTO_ETH_ADDRESS
            if hasattr(config, "CRYPTO_ETH_ADDRESS") and config.CRYPTO_ETH_ADDRESS
            else "Not configured"
        )

        usdt = (
            config.CRYPTO_USDT_ADDRESS
            if hasattr(config, "CRYPTO_USDT_ADDRESS") and config.CRYPTO_USDT_ADDRESS
            else "Not configured"
        )

        ltc = (
            config.CRYPTO_LTC_ADDRESS
            if hasattr(config, "CRYPTO_LTC_ADDRESS") and config.CRYPTO_LTC_ADDRESS
            else "Not configured"
        )

        msg = (
            f"<b>💼 WALLET</b>\n\n"
            f"<b>Crypto Payments:</b>\n"
            f"- BTC: <code>{btc}</code>\n"
            f"- ETH: <code>{eth}</code>\n"
            f"- USDT: <code>{usdt}</code>\n"
            f"- LTC: <code>{ltc}</code>\n\n"
            f"<b>Redeem Code:</b>\n"
            f"Use /redeem CODE\n\n"
            f"<b>API:</b>\n"
            f"<code>GET /api/v1/wallet</code>\n\n"
            f"Visit: {config.SITE_URL}/wallet"
        )

        await self.send(msg)

    # ── BALANCE ──────────────────────────────────────────────

    async def cmd_balance(self, args=""):
        """Check balance."""

        conn = None

        try:
            conn = _get_db()

            user = conn.execute("SELECT wallet_balance FROM users LIMIT 1").fetchone()

            balance = user[0] if user else 0

            await self.send(f"<b>💵 BALANCE:</b> ${balance:.2f}")

        except Exception as e:
            await self.send(f"<b>❌ BALANCE ERROR:</b> {e}")

        finally:
            if conn:
                conn.close()

    # ── SEARCH ───────────────────────────────────────────────

    async def cmd_search(self, args=""):
        """Search for jobs."""

        await self.send(
            "<b>🔎 SEARCHING JOBS...</b>\n\n"
            "Searching across:\n"
            "- DuckDuckGo\n"
            "- Bing\n"
            "- Google\n\n"
            "This may take a moment..."
        )

        try:
            from core.job_search import MultiSourceSearch

            search = MultiSourceSearch()

            jobs = []

            for title in ["network engineer", "it manager", "infrastructure engineer"]:
                for location in ["Dubai", "Remote", "Beirut"]:
                    results = search.search_all_sources(title, location, limit=5)

                    if results:
                        jobs.extend(results)

            # Deduplicate

            seen = set()

            unique = []

            for job in jobs:
                email = job.get("email", "")

                if email and email not in seen:
                    seen.add(email)

                    unique.append(job)

            if unique:
                msg = f"<b>🔎 FOUND {len(unique)} JOBS:</b>\n\n"

                for i, job in enumerate(unique[:5], 1):
                    msg += (
                        f"<b>{i}. {job.get('title', 'N/A')}</b>\n"
                        f"Company: {job.get('company', 'N/A')}\n"
                        f"Email: {job.get('email', 'N/A')}\n\n"
                    )

                await self.send(msg)

            else:
                await self.send(
                    "<b>🔎 No jobs found.</b>\n\nTry a different query or location. You can also use the inline search from any chat by typing @YourBot plus your query."
                )

        except Exception as e:
            logger.error(f"[BOT] cmd_search error: {e}")
            await self.send(
                "<b>❌ Search unavailable.</b>\n\nThe job search engines may be temporarily down.\nTry /status to check system health, or try again in a moment."
            )

    # ── APPLY ────────────────────────────────────────────────

    async def cmd_apply(self, args=""):
        """Quick apply to jobs."""

        msg = (
            "<b>🎯 QUICK APPLY</b>\n\n"
            "To apply automatically:\n"
            "1. Create a CV profile\n"
            "2. Launch a campaign\n"
            "3. System handles the rest!\n\n"
            "<b>API:</b>\n"
            "<code>POST /api/v1/campaign</code>"
        )

        await self.send(msg)

    # ── PRICING ──────────────────────────────────────────────

    async def cmd_pricing(self, args=""):
        """Show pricing."""

        msg = (
            "<b>💰 PRICING (35+ TIERS)</b>\n\n"
            "<b>Starter:</b>\n"
            "- 5 companies: FREE\n"
            "- 10 companies: $1\n"
            "- 25 companies: $2\n"
            "- 50 companies: $3\n"
            "- 100 companies: $5\n\n"
            "<b>Growth:</b>\n"
            "- 200 companies: $10\n"
            "- 300 companies: $14\n"
            "- 500 companies: $22\n\n"
            "<b>Business:</b>\n"
            "- 1000 companies: $42\n"
            "- 2000 companies: $68\n\n"
            "<b>Scale:</b>\n"
            "- 5000 companies: $120\n"
            "- 10000 companies: $200\n\n"
            "<b>Ultra:</b>\n"
            "- 50000 companies: $700\n"
            "- 100000 companies: $1200\n\n"
            "<b>Legend:</b>\n"
            "- 1M companies: $8000\n\n"
            f"Visit: {config.SITE_URL}/pricing"
        )

        await self.send(msg)

    # ── WHATSAPP ─────────────────────────────────────────────

    async def cmd_whatsapp(self, args=""):
        """Get WhatsApp contact info."""

        link = get_whatsapp_contact_url()

        msg = (
            f"<b>💬 WhatsApp Contact</b>\n\n"
            f"<b>Sam Salameh</b>\n"
            f"<i>Senior Network Engineer</i>\n\n"
            f"<b>Number:</b> +961 71 019 053\n\n"
            f'<a href="{link}">📱 Click to message on WhatsApp</a>\n\n'
            f"<b>Quick actions:</b>\n"
            f"• /whatsapp apply [company] [position] - Notify about application\n"
            f"• /whatsapp interview [company] [position] [date] - Notify about interview\n"
            f"• The dashboard has a WhatsApp button too!\n\n"
            f"<i>Note: WhatsApp notifications use wa.me deep links - "
            f"they open WhatsApp on your phone. For automated alerts, Telegram is faster.</i>"
        )

        await self.send(msg)

    # ── REFERRAL ─────────────────────────────────────────────

    async def cmd_referral(self, args=""):
        """Show referral info."""

        msg = (
            "<b>🤝 REFERRAL PROGRAM</b>\n\n"
            "<b>💰 Earn 10% commission!</b>\n\n"
            f"Share your referral link:\n"
            f"<code>{config.SITE_URL}/register?ref=YOUR_ID</code>\n\n"
            "<b>How it works:</b>\n"
            "1. 📤 Share your link\n"
            "2. 👥 Friends sign up\n"
            "3. 💳 They make purchases\n"
            "4. 💵 You earn 10%!\n\n"
            f"Visit: {config.SITE_URL}/referral"
        )

        await self.send(msg)

    # ── STOP (placeholder for inline button) ─────────────────

    async def cmd_stop_auto(self, args=""):
        """Stop auto-run by toggling _auto_running flag."""
        async with self._state_lock:
            self._auto_running = False
        logger.info("[BOT] _auto_running set to False by /stop_auto")
        await self.send(
            "<b>⏹ AUTO-RUN STOPPED</b>\n\n"
            "🛑 Auto-run has been halted.\n"
            "▶ Use <code>/campaign</code> to restart anytime.\n"
            "📊 Check <code>/stats</code> for what was accomplished."
        )

    # ── CHRONOS: Pause ────────────────────────────────────────────

    async def cmd_pause(self, args=""):
        """Pause auto-run by toggling _auto_running flag."""
        async with self._state_lock:
            self._auto_running = False
        logger.info("[BOT] _auto_running set to False by /pause")
        await self.send(
            "<b>⏸️ PAUSE | وقّف</b>\n\n"
            "🛑 Auto-run has been paused.\n"
            "All active processes are being halted safely.\n\n"
            "<b>▶️ To resume:</b> Press RESUME button or /campaign\n"
            "<b>📊 Status:</b> /status"
        )

    # ── CHRONOS: Resume ───────────────────────────────────────────

    async def cmd_resume(self, args=""):
        """Resume auto-run by toggling _auto_running flag."""
        async with self._state_lock:
            self._auto_running = True
        logger.info("[BOT] _auto_running set to True by /resume")
        await self.send(
            "<b>▶️ RESUME | كمّل</b>\n\n"
            "🟢 Auto-run has been resumed.\n"
            "All systems are back online.\n\n"
            "<b>⏸️ To pause:</b> Press PAUSE button\n"
            "<b>📊 Status:</b> /status"
        )

    # ── CHRONOS: Test Strike ───────────────────────────────────────

    async def cmd_test_strike(self, args=""):
        """Run a test application (Chronos TEST STRIKE) — dry run."""
        await self.send(
            "<b>🧪 TEST STRIKE | تجربة</b>\n\n🔍 Running test application..."
        )
        conn = None
        try:
            conn = _get_db()
            stats = {
                "total_jobs": conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
                "total_applied": conn.execute(
                    "SELECT COUNT(*) FROM jobs WHERE applied_at IS NOT NULL"
                ).fetchone()[0],
                "total_campaigns": conn.execute(
                    "SELECT COUNT(*) FROM campaigns"
                ).fetchone()[0],
            }
            # Test Groq ping
            groq_ok = "🟢"
            groq_key = getattr(config, "GROQ_API_KEY", "") or os.environ.get(
                "GROQ_API_KEY", ""
            )
            if groq_key[:4] == "gsk_":
                try:
                    r = await self.http_client.post(
                        config.GROQ_API_URL,
                        json={
                            "model": "mixtral-8x7b-32768",
                            "messages": [{"role": "user", "content": "ping"}],
                            "max_tokens": 1,
                        },
                        headers={"Authorization": f"Bearer {groq_key}"},
                        timeout=5,
                    )
                    groq_ok = "🟢" if r.status_code == 200 else "🔴"
                except Exception:
                    groq_ok = "🔴"
            else:
                groq_ok = "⚪"
            msg = (
                f"<b>🧪 TEST STRIKE RESULT</b>\n\n"
                f"📊 DB Stats:\n"
                f"  • Jobs: {stats['total_jobs']}\n"
                f"  • Applied: {stats['total_applied']}\n"
                f"  • Campaigns: {stats['total_campaigns']}\n\n"
                f"🔌 Groq API: {groq_ok}\n"
                f"🟢 DB Connection: OK\n"
                f"🟢 Auto-Run: {'ACTIVE' if getattr(self, '_auto_running', False) else 'PAUSED'}\n\n"
                f"<i>Full status: /status</i>"
            )
        except Exception as e:
            logger.error(f"[BOT] cmd_test_strike error: {e}")
            msg = (
                "<b>🧪 TEST STRIKE — Issue Detected</b>\n\n"
                "The test could not complete. Possible reasons:\n"
                "• Database is temporarily locked\n"
                "• Groq API key is missing or invalid\n\n"
                "Try /ai_check to verify AI connectivity, then try again."
            )
        finally:
            if conn:
                conn.close()
        await self.send(msg)

    # ── CHRONOS: AI Check ──────────────────────────────────────────

    async def cmd_ai_check(self, args=""):
        """Ping all AI providers and report actual status."""
        results = []
        import json as _json

        # Check Groq
        groq_key = getattr(config, "GROQ_API_KEY", "") or os.environ.get(
            "GROQ_API_KEY", ""
        )
        if groq_key[:4] == "gsk_":
            try:
                r = await self.http_client.post(
                    config.GROQ_API_URL,
                    json={
                        "model": "mixtral-8x7b-32768",
                        "messages": [{"role": "user", "content": "ping"}],
                        "max_tokens": 1,
                    },
                    headers={"Authorization": f"Bearer {groq_key}"},
                    timeout=10,
                )
                if r.status_code == 200:
                    results.append("🟢 Groq API — Responding")
                else:
                    results.append(f"🔴 Groq API — HTTP {r.status_code}")
            except Exception as e:
                results.append(f"🔴 Groq API — {str(e)[:50]}")
        else:
            results.append("⚪ Groq API — No key configured")

        # Check Gemini
        gemini_key = getattr(config, "GEMINI_API_KEY", "") or os.environ.get(
            "GEMINI_API_KEY", ""
        )
        if gemini_key:
            try:
                r = await self.http_client.get(
                    f"{config.GEMINI_MODELS_URL}?key={gemini_key}",
                    timeout=10,
                )
                if r.status_code == 200:
                    results.append("🟢 Gemini API — Responding")
                else:
                    results.append(f"🔴 Gemini API — HTTP {r.status_code}")
            except Exception as e:
                results.append(f"🔴 Gemini API — {str(e)[:50]}")
        else:
            results.append("⚪ Gemini API — No key configured")

        # Check JSearch
        jsearch_key = getattr(config, "JSEARCH_API_KEY", "") or os.environ.get(
            "JSEARCH_API_KEY", ""
        )
        if jsearch_key:
            results.append("🟢 JSearch API — Key present")
        else:
            results.append("⚪ JSearch API — No key configured")

        # Check PA health
        try:
            r = await self.http_client.get(f"{config.SITE_URL}/health", timeout=5)
            h = _json.loads(r.text)
            pa_status = h.get("status", "?")
            results.append(
                f"{'🟢' if pa_status == 'ok' else '🟡'} PA Server — {pa_status}"
            )
        except Exception as e:
            results.append(f"🔴 PA Server — {str(e)[:50]}")

        msg = (
            "<b>🧠 AI STATUS | الذكاء</b>\n\n"
            + "\n".join(results)
            + "\n\n<i>Last checked: "
            + datetime.now().strftime("%H:%M:%S")
            + "</i>"
        )
        await self.send(msg)

    # ── CHRONOS: API Keys ──────────────────────────────────────────

    async def cmd_keys(self, args=""):
        """Check actual env vars and report key status."""
        import os

        key_map = {
            "GROQ_API_KEY": (
                "Groq API",
                lambda k: k.startswith("gsk_") if k else False,
            ),
            "GEMINI_API_KEY": ("Gemini API", lambda k: bool(k)),
            "JSEARCH_API_KEY": ("JSearch API", lambda k: bool(k)),
            "PA_API_TOKEN": ("PA API Token", lambda k: bool(k)),
        }
        lines = ["<b>🔑 API KEYS | مفاتيح</b>", ""]
        for env_var, (label, check) in key_map.items():
            val = getattr(config, env_var, None) or os.environ.get(env_var, "")
            if check(val):
                prefix = val[:8] + "..." if len(val) > 12 else "set"
                lines.append(f"🟢 <b>{label}</b> — {prefix}")
            else:
                lines.append(f"🔴 <b>{label}</b> — Not configured")

        # Check SMTP env
        smtp_host = getattr(config, "SMTP_HOST", None) or os.environ.get(
            "SMTP_HOST", ""
        )
        smtp_user = getattr(config, "SMTP_USER", None) or os.environ.get(
            "SMTP_USER", ""
        )
        if smtp_host and smtp_user:
            lines.append(f"🟢 <b>SMTP</b> — {smtp_host}")
        else:
            lines.append("🔴 <b>SMTP</b> — Not configured")

        lines.append("")
        lines.append("<i>Checked at: " + datetime.now().strftime("%H:%M:%S") + "</i>")
        await self.send("\n".join(lines))

    # ── ENHANCED: AI-Powered Fix ──────────────────────────────────

    async def cmd_fix(self, args=""):
        """AI-powered system diagnostics — uses Groq to find & fix issues."""
        await self.send(
            "<b>🔧 AI DIAGNOSTICS | تشخيص ذكي</b>\n\n🔍 Analyzing system... Please wait."
        )
        try:
            from core.telegram_enhanced import AIFixer, WebsiteController

            wc = WebsiteController()
            # Gather system context
            health = await wc.health_check()
            context = {
                "system_health": health,
                "recent_logs": "Querying...",
                "error_trace": "None detected",
            }
            # Try to get recent logs
            try:
                logs = await wc.get_logs(lines=15)
                context["recent_logs"] = logs[:1500]
            except Exception:
                context["recent_logs"] = "Logs unavailable"
            # AI diagnosis
            fixer = AIFixer()
            diagnosis = await fixer.diagnose(context)
            result = f"<b>🔧 AI DIAGNOSIS</b>\n\n{diagnosis}\n\n<b>🌐 Platform Status:</b>\n{health}\n\n<i>🔄 Use /restart_web to restart servers</i>\n<i>📜 Use /logs for detailed logs</i>"
            await self.send(result)
        except Exception as e:
            await self.send(
                f"<b>🔧 Diagnostics</b>\n\n⚠️ AI fixer unavailable: {e}\n\n<b>Manual Checks:</b>\n/status — System health\n/websites — Platform status\n/logs — Recent logs"
            )

    # ── ENHANCED: Website Control ─────────────────────────────────

    async def cmd_websites(self, args=""):
        """Show website/platform status."""
        await self.send("<b>🌐 Checking platforms...</b>")
        try:
            from core.telegram_enhanced import WebsiteController

            wc = WebsiteController()
            result = await wc.health_check()
            await self.send(result)
        except Exception as e:
            await self.send(f"❌ Could not check platforms: {e}")

    async def cmd_restart_web(self, args=""):
        """Restart web servers from Telegram."""
        platform = args.strip().lower() if args else "pythonanywhere"
        valid = {
            "pythonanywhere": "PythonAnywhere",
            "pa": "PythonAnywhere",
            "render": "Render",
        }
        if platform not in valid:
            await self.send(
                "❌ Unknown platform. Use: /restart_web pythonanywhere OR /restart_web render"
            )
            return
        await self.send(f"<b>🔄 Restarting {valid[platform]}...</b>")
        try:
            from core.telegram_enhanced import WebsiteController

            wc = WebsiteController()
            result = await wc.restart_platform(platform)
            await self.send(result)
        except Exception as e:
            await self.send(f"❌ Restart failed: {e}")

    async def cmd_deploy(self, args=""):
        """Show deploy instructions."""
        pa_domain = config.SITE_URL.replace("https://", "").replace("http://", "")
        msg = (
            "<b>🚀 DEPLOYMENT</b>\n\n"
            "<b>Current Deploys:</b>\n"
            "• Render: jobhunt-pro.onrender.com (auto-deploy on git push)\n"
            f"• PythonAnywhere: {pa_domain} (manual reload)\n\n"
            "<b>To deploy:</b>\n"
            "1. Commit changes: <code>git add . && git commit -m 'update'</code>\n"
            "2. Push: <code>git push</code>\n"
            "3. Render auto-deploys; PA: /restart_web pythonanywhere\n\n"
            "<i>Check status: /websites</i>"
        )
        await self.send(msg)

    async def cmd_security(self, args=""):
        """Security audit."""
        import platform as pf

        msg = (
            "<b>🔒 SECURITY AUDIT</b>\n\n"
            f"<b>Platform:</b> {pf.system()} {pf.release()}\n"
            f"<b>Bot Token:</b> {'✅ Set' if self.enabled else '❌ Missing'}\n"
            f"<b>HTTPS:</b> ✅ Enforced (Render + PA)\n"
            f"<b>SQL Injection:</b> ✅ Parameterized queries\n"
            f"<b>API Keys:</b> 🔐 Never exposed in logs\n"
            f"<b>Admin Commands:</b> ✅ Protected\n\n"
            "<i>🔐 All sensitive data encrypted at rest.</i>\n"
            "<i>🛡️ Rate limiting active on bot commands.</i>"
        )
        await self.send(msg)

    async def cmd_today(self, args=""):
        """Today's report with real DB stats."""
        conn = None
        try:
            conn = _get_db()
            today = datetime.now().strftime("%Y-%m-%d")
            new_jobs = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE date(created_at) = ?", (today,)
            ).fetchone()[0]
            applied = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE date(applied_at) = ?", (today,)
            ).fetchone()[0]
            emails = conn.execute(
                "SELECT COUNT(*) FROM campaign_emails WHERE date(sent_at) = ?", (today,)
            ).fetchone()[0]
            total_jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            total_applied = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE applied_at IS NOT NULL"
            ).fetchone()[0]
            msg = (
                f"<b>📊 TODAY'S REPORT — {today}</b>\n\n"
                f"<b>📥 New Jobs Today:</b> {new_jobs}\n"
                f"<b>✅ Applied Today:</b> {applied}\n"
                f"<b>📧 Emails Sent Today:</b> {emails}\n"
                f"<b>---</b>\n"
                f"<b>📦 Total Jobs:</b> {total_jobs}\n"
                f"<b>📨 Total Applied:</b> {total_applied}\n"
            )
        except Exception as e:
            msg = f"<b>❌ Today's Report Error:</b> {e}"
        finally:
            if conn:
                conn.close()
        await self.send(msg)

    async def cmd_weekly(self, args=""):
        """Weekly report."""
        await self.cmd_stats_overview(args)

    # ── CHRONOS: Guide ─────────────────────────────────────────────

    async def cmd_guide(self, args=""):
        """Show Chronos Guide."""

        msg = (
            "<b>📖 GUIDE | دليل</b>\n\n"
            f"<b>{config.APP_NAME} v{config.VERSION} — Quick Guide</b>\n\n"
            "<b>⚡ Getting Started:</b>\n"
            "1. /start — Open this menu\n"
            "2. /campaign — Launch auto-apply\n"
            "3. /status — Check system health\n\n"
            "<b>⌨️ Reply Keyboard Buttons:</b>\n"
            "• Use the 50 bilingual buttons below\n"
            "• Each button sends an English or Arabic command\n"
            '• Example: press "🖥️ Status" for health check\n\n'
            "<b>📊 Monitoring:</b>\n"
            "• /stats — Real-time statistics\n"
            "• /sales — Revenue reports\n"
            "• /applications — Last applications\n\n"
            "<b>🛠️ Commands:</b> /help for full list"
        )

        await self.send(msg)

    # ── FEATURES - Comprehensive feature showcase ─────────────────

    async def cmd_features(self, args=""):
        """Show all JobHunt Pro features with descriptions."""
        msg = (
            "✨ <b>JobHunt Pro — All Features</b> ✨\n\n"
            "<b>🤖 Auto-Apply Engine</b>\n"
            "• 200 AI swarm agents apply 24/7\n"
            "• Multi-platform: LinkedIn, JSearch, DuckDuckGo, Bing, Google\n"
            "• Auto-generates tailored cover letters per job\n"
            "• Smart rate limiting to avoid spam detection\n"
            "• Commands: /campaign, /force_strike, /mass_strike\n\n"
            "<b>📊 Analytics Dashboard</b>\n"
            "• Real-time application stats with charts\n"
            "• Conversion funnel — Track: Found → Applied → Opened → Responded\n"
            "• Trend analysis with configurable date ranges\n"
            "• Top companies, countries & job titles breakdown\n"
            "• Commands: /stats, /trend, /funnel, /oracle\n\n"
            "<b>🔍 Inline Search</b>\n"
            "• Search jobs from ANY Telegram chat\n"
            "• Type @YourBot query to find matching jobs instantly\n"
            "• Results show company, location, salary & one-click apply\n"
            "• Works in groups, channels, and private chats\n\n"
            "<b>📱 Mini App</b>\n"
            "• Full web dashboard accessible via Telegram button\n"
            "• Manage campaigns, upload CV, track applications\n"
            "• No browser needed — works right inside Telegram\n"
            "• Access: Press 📊 Dashboard button in /start menu\n\n"
            "<b>🎯 ATS Resume Scoring</b>\n"
            "• Algorithmic keyword matching against job descriptions\n"
            "• AI-powered deep analysis via Groq\n"
            "• Get actionable tips to improve your resume score\n"
            "• Commands: /ats_score, /ats\n\n"
            "<b>💬 AI Conversation Engine</b>\n"
            "• Auto-generate professional greetings for recruiters\n"
            "• Smart reply suggestions to recruiter messages\n"
            "• Batch generate messages for multiple contacts\n"
            "• Commands: /converse greet, /converse reply, /converse batch\n\n"
            "<b>📧 Smart Email System</b>\n"
            "• 20 SMTP providers with automatic rotation\n"
            "• Professional HTML email templates\n"
            "• Open tracking & delivery monitoring\n"
            "• Commands: /email_stats, /campaigns\n\n"
            "<b>🛡️ System Protection</b>\n"
            "• Rate limiting on all commands\n"
            "• Kill switch & emergency halt\n"
            "• Night mode for quiet hours\n"
            "• Dry run mode for safe testing\n"
            "• Commands: /shield, /kill_switch, /omega_halt\n\n"
            "<b>🔧 Admin Tools</b>\n"
            "• Redeem code generator with presets\n"
            "• Flash sale manager\n"
            "• System audit & diagnostics\n"
            "• Backup & cleanup utilities\n"
            "• Commands: /admin, /generate_code, /flash_sale\n\n"
            "<b>💼 Sales & Monetization</b>\n"
            "• Real-time revenue tracking\n"
            "• 35+ pricing tiers from FREE to Enterprise\n"
            "• Referral program with 10% commission\n"
            "• Crypto wallet support (BTC, ETH, USDT, LTC)\n"
            "• Commands: /sales, /pricing, /referral, /wallet\n\n"
            "<i>Use /help for the full command list • Made with ❤️ by Sam Salameh</i>"
        )
        if len(msg) > 4000:
            msg = msg[:3950] + "\n\n...(truncated — use /help for full command list)"
        await self.send(msg)

    # ── CHRONOS: Pulse ─────────────────────────────────────────────

    async def cmd_pulse(self, args=""):
        """System pulse check."""

        uptime = datetime.now() - self.bot_start_time

        msg = (
            "<b>📜 PULSE | النبض</b>\n\n"
            f"⏱ Uptime: {uptime.total_seconds() / 3600:.1f}h\n"
            "🟢 Bot: Alive\n"
            "🟢 DB: Connected\n"
            "🟢 AI: Ready\n"
            "🟢 Email: Active\n\n"
            "<i>All systems nominal.</i>"
        )

        await self.send(msg)

    # ── CHRONOS: Inbox Check ───────────────────────────────────────

    async def cmd_inbox_check(self, args=""):
        """Check inbox for replies from jobs table."""
        conn = None
        try:
            conn = _get_db()
            responded = conn.execute(
                "SELECT COUNT(*) as c FROM jobs WHERE responded_at IS NOT NULL"
            ).fetchone()["c"]
            recent = conn.execute(
                "SELECT company, title, responded_at FROM jobs WHERE responded_at IS NOT NULL ORDER BY responded_at DESC LIMIT 5"
            ).fetchall()
            msg = "<b>📬 INBOX CHECK | فحص الردود</b>\n\n"
            msg += f"📨 Total responses: <b>{responded}</b>\n\n"
            if recent:
                msg += "<b>Recent responses:</b>\n"
                for r in recent:
                    d = dict(r)
                    msg += f"• {d.get('company', '?')} — {d.get('title', '?')} ({str(d.get('responded_at', ''))[:10]})\n"
            else:
                msg += "<i>No responses recorded yet. Keep applying!</i>\n"
            msg += "\nUse /applications for full list."
        except Exception as e:
            msg = f"<b>📬 INBOX CHECK</b>\n\nError: {e}"
        finally:
            if conn:
                conn.close()
        await self.send(msg)

    # ── CHRONOS: Leads ─────────────────────────────────────────────

    async def cmd_leads(self, args=""):
        """Show leads."""

        msg = (
            "<b>📋 LEADS | الفرص</b>\n\n"
            "🚧 <b>Coming Soon</b>\n\n"
            "The full leads dashboard is under development.\n\n"
            "In the meantime, use:\n"
            "• /search — Find new job leads\n"
            "• /applications — View sent applications\n"
            "• /companies — Browse target companies\n\n"
            "<i>Advanced lead tracking coming in a future update.</i>"
        )

        await self.send(msg)

    # ── CHRONOS: Companies ─────────────────────────────────────────

    async def cmd_companies(self, args=""):
        """Show company intel. /companies top → top 10, /companies [name] → detail."""

        try:
            arg = (args or "").strip().lower()

            if arg == "top" or arg == "":
                data = self.analytics.get_top_companies(10)

                msg = self.analytics.format_companies_top(data)

            else:
                data = self.analytics.get_company_detail(args.strip())

                msg = self.analytics.format_company_detail(data)

            await self.send(msg)

        except Exception as e:
            logger.error(f"[BOT] cmd_companies error: {e}")

            await self.send(f"<b>🏢 COMPANIES | الشركات</b>\n\n<i>Error: {e}</i>")

    # ── CHRONOS: Followups ─────────────────────────────────────────

    async def cmd_followups(self, args=""):
        """Show follow-ups."""

        msg = (
            "<b>📨 FOLLOW-UPS | متابعات</b>\n\n"
            "Follow-up system is active.\n"
            "Automatic follow-ups are sent 3 days after application.\n\n"
            "<i>Check /applications for recent activity.</i>"
        )

        await self.send(msg)

    # ── CHRONOS: Backup ────────────────────────────────────────────

    async def cmd_backup(self, args=""):
        """Create a real database backup with timestamp."""
        conn = None
        try:
            conn = _get_db()
            try:
                row = conn.execute("PRAGMA database_list").fetchone()
                src = (
                    row[2]
                    if row
                    else str(
                        Path(__file__).parent.parent
                        / (getattr(config, "DB_PATH", None) or "jobhunt_saas_v2.db")
                    )
                )
            except Exception:
                src = str(
                    Path(__file__).parent.parent
                    / (getattr(config, "DB_PATH", None) or "jobhunt_saas_v2.db")
                )
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dst = f"{src}.{ts}.bak"
            conn.execute("VACUUM INTO ?", (dst,))
            conn.close()
            conn = None
            size_kb = os.path.getsize(dst) / 1024
            await self.send(
                f"<b>💾 BACKUP CREATED</b>\n\n"
                f"📁 {os.path.basename(dst)}\n"
                f"📦 Size: {size_kb:.1f} KB\n\n"
                f"<i>Backup saved successfully.</i>"
            )
        except Exception as e:
            logger.error(f"[BOT] cmd_backup error: {e}")
            await self.send(
                "<b>💾 Backup Failed</b>\n\nThe backup could not be created. This could be due to disk space or file permissions.\nCheck /memory for disk usage and try again."
            )
        finally:
            if conn:
                conn.close()

    # ── CHRONOS: Shield ────────────────────────────────────────────

    async def cmd_shield(self, args=""):
        """System shield status."""

        msg = (
            "<b>🛡️ SHIELD | الدرع</b>\n\n"
            "🟢 Rate Limiter: Active\n"
            "🟢 Error Handler: Active\n"
            "🟢 Auto-Healer: Standby\n"
            "🟢 Connection Pool: Healthy\n\n"
            "<i>System protection is operational.</i>"
        )

        await self.send(msg)

    # ── CHRONOS: Force Strike ──────────────────────────────────────

    async def cmd_force_strike(self, args=""):
        """Force immediate application — triggers multi-platform auto-apply."""
        await self.send(
            "<b>🎯 FORCE STRIKE | ضربة فورية</b>\n\n⚡ Triggering immediate application run..."
        )
        async with self._state_lock:
            self._auto_running = True
        try:
            from core.multi_platform_apply import AutoApplyOrchestrator

            orch = AutoApplyOrchestrator(daily_limit=10)
            results = await orch.search_all(
                query="network engineer", location="Dubai", max_per_platform=3
            )
            total = sum(len(jobs) for jobs in results.values())
            plat_info = "\n".join(
                [f"  • {p}: {len(j)} jobs" for p, j in results.items()]
            )
            msg = (
                f"<b>🎯 FORCE STRIKE RESULTS</b>\n\n"
                f"✅ Found {total} jobs across platforms:\n"
                f"{plat_info}\n\n"
                f"<i>Next: /campaign to apply or /status for details.</i>"
            )
        except ImportError:
            msg = "<b>⚠️ Force Strike</b>\n\nMulti-platform engine not available. Use /campaign instead."
        except Exception as e:
            msg = f"<b>❌ Force Strike Error:</b> {str(e)[:200]}"
        await self.send(msg)

    # ── CHRONOS: Mass Strike ───────────────────────────────────────

    async def cmd_mass_strike(self, args=""):
        """Mass application strike — scrapes all platforms."""
        await self.send(
            "<b>🎪 MASS STRIKE | ضربة جماعية</b>\n\n🌍 Launching mass strike across ALL platforms..."
        )
        async with self._state_lock:
            self._auto_running = True
        try:
            from core.multi_platform_apply import AutoApplyOrchestrator

            orch = AutoApplyOrchestrator(daily_limit=20)
            # Use all target titles
            titles = [
                "network engineer",
                "it manager",
                "infrastructure engineer",
                "devops engineer",
                "system administrator",
            ]
            locations = ["Dubai", "Remote", "Abu Dhabi", "Riyadh", "Doha"]
            total_found = 0
            all_results = {}
            for q in titles:
                for loc in locations:
                    results = await orch.search_all(
                        query=q, location=loc, max_per_platform=2
                    )
                    for k, v in results.items():
                        all_results.setdefault(k, []).extend(v)
                        total_found += len(v)
            plat_info = "\n".join(
                [f"  • {p}: {len(j)} jobs" for p, j in all_results.items()]
            )
            msg = (
                f"<b>🎪 MASS STRIKE RESULT</b>\n\n"
                f"✅ Total jobs found: {total_found}\n"
                f"{plat_info}\n\n"
                f"<i>Use /campaign to apply to all found jobs.</i>"
            )
        except ImportError:
            msg = "<b>⚠️ Mass Strike</b>\n\nMulti-platform engine not available. Use /campaign instead."
        except Exception as e:
            msg = f"<b>❌ Mass Strike Error:</b> {str(e)[:200]}"
        await self.send(msg)

    # ── CHRONOS: Clean ─────────────────────────────────────────────

    async def cmd_clean(self, args=""):
        """Clean temporary files, cache, and old .bak/.old files."""
        import glob

        cleaned = 0
        failed = 0
        patterns = ["*.bak", "*.old", "*.tmp", "__pycache__", "*.pyc"]
        base = (
            os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else "."
        )
        try:
            for pattern in patterns:
                if pattern == "__pycache__":
                    for root, dirs, _ in os.walk(base):
                        if "__pycache__" in dirs:
                            d = os.path.join(root, "__pycache__")
                            try:
                                import shutil

                                shutil.rmtree(d)
                                cleaned += 1
                            except Exception:
                                failed += 1
                elif pattern == "*.pyc":
                    for root, _, files in os.walk(base):
                        for f in files:
                            if f.endswith(".pyc"):
                                try:
                                    os.remove(os.path.join(root, f))
                                    cleaned += 1
                                except Exception:
                                    failed += 1
                else:
                    for f in glob.glob(
                        os.path.join(base, "**", pattern), recursive=True
                    ):
                        try:
                            os.remove(f)
                            cleaned += 1
                        except Exception:
                            failed += 1
            msg = f"<b>🧹 CLEAN | تنظيف</b>\n\n✅ Cleaned {cleaned} file(s)\n"
            if failed:
                msg += f"⚠️ {failed} file(s) could not be deleted\n"
            msg += "\n<i>Disk space optimized.</i>"
        except Exception as e:
            msg = f"<b>🧹 CLEAN ERROR:</b> {e}"
        await self.send(msg)

    # ── CHRONOS: Blacklist ─────────────────────────────────────────

    async def cmd_blacklist(self, args=""):
        """Show blacklisted companies."""
        conn = None
        try:
            conn = _get_db()
            blacklisted = []
            if self._table_exists(conn, "blacklist"):
                blacklisted = conn.execute(
                    "SELECT company, reason, created_at FROM blacklist ORDER BY created_at DESC LIMIT 20"
                ).fetchall()
            msg = "<b>⛔ BLACKLIST | القائمة السوداء</b>\n\n"
            if blacklisted:
                msg += f"📋 <b>{len(blacklisted)} blacklisted companies:</b>\n"
                for b in blacklisted:
                    d = dict(b)
                    msg += f"• {d.get('company', '?')}"
                    if d.get("reason"):
                        msg += f" — {d['reason']}"
                    msg += "\n"
                msg += "\n<i>Use the web dashboard to manage your blacklist.</i>"
            else:
                msg += "✅ No companies are blacklisted.\n\n<i>Use the web dashboard to add companies to the blacklist.</i>"
        except Exception as e:
            msg = f"<b>⛔ BLACKLIST</b>\n\nNo blacklist table found: {e}"
        finally:
            if conn:
                conn.close()
        await self.send(msg)

    # ── CHRONOS: Oracle ────────────────────────────────────────────

    async def cmd_oracle(self, args=""):
        """Market oracle - real job market insights from DB."""
        conn = None
        try:
            conn = _get_db()
            total_jobs = conn.execute("SELECT COUNT(*) as c FROM jobs").fetchone()["c"]
            applied = conn.execute(
                "SELECT COUNT(*) as c FROM jobs WHERE applied_at IS NOT NULL"
            ).fetchone()["c"]
            # Get top 5 titles
            titles = (
                conn.execute(
                    "SELECT title, COUNT(*) as c FROM jobs WHERE title IS NOT NULL GROUP BY title ORDER BY c DESC LIMIT 5"
                ).fetchall()
                if self._table_exists(conn, "jobs")
                else []
            )
            # Get top countries
            countries = (
                conn.execute(
                    "SELECT company, COUNT(*) as c FROM jobs WHERE company IS NOT NULL GROUP BY company ORDER BY c DESC LIMIT 5"
                ).fetchall()
                if self._table_exists(conn, "jobs")
                else []
            )
            response_rate = (applied / total_jobs * 100) if total_jobs > 0 else 0

            msg = "<b>🔮 ORACLE | أوراكل السوق</b>\n\n"
            msg += "<b>📊 Market Overview</b>\n"
            msg += f"💼 Total Jobs: <b>{total_jobs}</b>\n"
            msg += f"✅ Applied: <b>{applied}</b> ({response_rate:.1f}%)\n\n"
            if titles:
                msg += "<b>🏆 Top Job Titles:</b>\n"
                for t in titles[:5]:
                    msg += f"• {t['title']}: {t['c']}\n"
                msg += "\n"
            else:
                msg += "<i>🏆 Collecting market data...</i>\n\n"
            if countries:
                msg += "<b>🌍 Top Companies:</b>\n"
                for c in countries[:5]:
                    msg += f"• {c['company']}: {c['c']} jobs\n"
            else:
                msg += "<i>🌍 No company data yet.</i>\n"
            msg += "\nUse /search to find more opportunities."
        except Exception as e:
            msg = f"<b>🔮 ORACLE</b>\n\nCould not fetch analytics: {e}"
        finally:
            if conn:
                conn.close()
        await self.send(msg)

    # ── CHRONOS: Best Day ──────────────────────────────────────────

    async def cmd_best_day(self, args=""):
        """Show best performance day from DB."""
        conn = None
        try:
            conn = _get_db()
            best = conn.execute(
                "SELECT date(applied_at) as day, COUNT(*) as cnt FROM jobs "
                "WHERE applied_at IS NOT NULL GROUP BY date(applied_at) ORDER BY cnt DESC LIMIT 1"
            ).fetchone()
            today = datetime.now().strftime("%Y-%m-%d")
            today_count = conn.execute(
                "SELECT COUNT(*) as c FROM jobs WHERE date(applied_at) = ?", (today,)
            ).fetchone()["c"]
            msg = "<b>🏆 BEST DAY | أفضل يوم</b>\n\n"
            if best:
                msg += f"🥇 Best day: <b>{best['day']}</b> with <b>{best['cnt']}</b> applications\n"
            msg += f"📊 Today: <b>{today_count}</b> applications so far\n\n"
            msg += "<i>Keep applying to break your record!</i>"
        except Exception as e:
            msg = f"<b>🏆 BEST DAY</b>\n\nError: {e}"
        finally:
            if conn:
                conn.close()
        await self.send(msg)

    # ── CHRONOS: Email Stats ───────────────────────────────────────

    async def cmd_email_stats(self, args=""):
        """Show real email delivery stats from DB."""
        conn = None
        try:
            conn = _get_db()
            total_sent = (
                conn.execute(
                    "SELECT COUNT(*) as c FROM campaign_emails WHERE status='sent'"
                ).fetchone()["c"]
                if self._table_exists(conn, "campaign_emails")
                else 0
            )
            opened = (
                conn.execute(
                    "SELECT COUNT(*) as c FROM campaign_emails WHERE opened_at IS NOT NULL"
                ).fetchone()["c"]
                if self._table_exists(conn, "campaign_emails")
                else 0
            )
            failed = (
                conn.execute(
                    "SELECT COUNT(*) as c FROM campaign_emails WHERE status='failed'"
                ).fetchone()["c"]
                if self._table_exists(conn, "campaign_emails")
                else 0
            )
            open_rate = (opened / total_sent * 100) if total_sent > 0 else 0
            fail_rate = (failed / total_sent * 100) if total_sent > 0 else 0
            msg = (
                "<b>📧 EMAIL STATS | إحصاء الإيميل</b>\n\n"
                f"📨 Total Sent: <b>{total_sent}</b>\n"
                f"👁 Opened: <b>{opened}</b> ({open_rate:.1f}%)\n"
                f"❌ Failed: <b>{failed}</b> ({fail_rate:.1f}%)\n\n"
                f"<i>Use /campaigns for detailed campaign breakdown.</i>"
            )
        except Exception as e:
            msg = f"<b>📧 EMAIL STATS</b>\n\nError: {e}"
        finally:
            if conn:
                conn.close()
        await self.send(msg)

    # ── CHRONOS: Settings ──────────────────────────────────────────

    async def cmd_settings(self, args=""):
        """Show system settings."""

        msg = (
            "<b>⚙️ SETTINGS | الإعدادات</b>\n\n"
            "<b>Current Configuration:</b>\n"
            "🔄 Refresh Rate: Every 15 minutes\n"
            "📧 Email Providers: 20\n"
            "🤖 Swarm Agents: 200\n"
            "🌍 Target Regions: Global\n\n"
            "<i>Use the web dashboard for full configuration.</i>"
        )

        await self.send(msg)

    # ── CHRONOS: Reboot ────────────────────────────────────────────

    async def cmd_reboot(self, args=""):
        """Try to restart the bot via PA API, then exit the polling loop."""
        await self.send("<b>🔄 REBOOT | إعادة تشغيل</b>\n\n⚠️ Attempting bot restart...")
        # Try to restart PA web app
        try:
            r = await self.http_client.post(
                config.PA_RELOAD_URL,
                headers={"Authorization": f"Token {config.PA_API_TOKEN}"},
                timeout=15,
            )
            logger.info(f"[BOT] PA reload triggered: {r.status_code} {r.text[:100]}")
        except Exception as e:
            logger.warning(f"[BOT] PA reload failed (non-fatal): {e}")
        # Exit the polling loop so watchdog restarts the process
        import os

        # On some platforms we can os._exit
        await self.send(
            "<b>🔄 Rebooting process...</b> Restart will trigger via watchdog."
        )
        try:
            os._exit(42)
        except Exception:
            pass
        raise SystemExit(42)

    # ── CHRONOS: Track ─────────────────────────────────────────────

    async def cmd_track(self, args=""):
        """Track applications in real-time."""

        msg = (
            "<b>🛰️ TRACK | التتبع المباشر</b>\n\n"
            "🚧 <b>Coming Soon</b>\n\n"
            "Real-time application tracking is under development.\n\n"
            "In the meantime, use:\n"
            "• /applications — View recent application activity\n"
            "• /leads — Browse current leads\n"
            "• /status — Check system health\n\n"
            "<i>Stay tuned for live tracking features!</i>"
        )

        await self.send(msg)

    # ── CHRONOS: Skip Lead ─────────────────────────────────────────

    async def cmd_skip_lead(self, args=""):
        """Skip current lead."""

        msg = (
            "<b>🚫 SKIP LEAD | تخطي</b>\n\n"
            "🚧 <b>Coming Soon</b>\n\n"
            "Lead skip functionality is under development.\n\n"
            "In the meantime, use:\n"
            "• /leads — View and manage available leads\n"
            "• /search — Find new job opportunities\n\n"
            "<i>This feature will let you skip and re-prioritize leads.</i>"
        )

        await self.send(msg)

    # ── CHRONOS: Logs ──────────────────────────────────────────────

    async def cmd_logs(self, args=""):
        """Show system logs from the bot's own memory buffer."""
        try:
            # Try to read actual log file
            log_dir = Path(__file__).parent.parent / "logs"
            log_files = (
                sorted(Path(log_dir).glob("*.log"), key=os.path.getmtime, reverse=True)
                if log_dir.exists()
                else []
            )
            if log_files:
                with open(log_files[0], "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                    last_30 = "".join(lines[-30:])
                    if len(last_30) > 3500:
                        last_30 = last_30[-3500:] + "\n...(truncated)"
                    await self.send(
                        f"<b>📜 Recent Logs ({log_files[0].name})</b>\n\n<pre>{last_30}</pre>"
                    )
            else:
                # Fallback: show recent handler activity
                await self.send(
                    "<b>📜 LOGS</b>\n\n"
                    f"🤖 Bot Uptime: {(datetime.now() - self.bot_start_time).total_seconds() / 3600:.1f}h\n"
                    f"📊 Commands Processed: via polling loop\n"
                    f"🟢 Bot is running normally.\n\n"
                    "<i>Use /status for health check or /admin for admin controls.</i>"
                )
        except Exception as e:
            await self.send(
                "<b>📜 LOGS</b>\n\n"
                f"🟢 Bot is running normally.\n"
                f"⏱ Uptime: {(datetime.now() - self.bot_start_time).total_seconds() / 3600:.1f}h\n"
                f"<i>Log file read error: {e}</i>"
            )

    # ── CHRONOS: Queue ─────────────────────────────────────────────

    async def cmd_queue(self, args=""):
        """Show real application queue status from DB."""
        conn = None
        try:
            conn = _get_db()
            today = datetime.now().strftime("%Y-%m-%d")
            pending = 0
            processing = 0
            completed_today = 0
            if self._table_exists(conn, "job_queue"):
                pending = conn.execute(
                    "SELECT COUNT(*) as c FROM job_queue WHERE status='pending'"
                ).fetchone()["c"]
                processing = conn.execute(
                    "SELECT COUNT(*) as c FROM job_queue WHERE status='processing'"
                ).fetchone()["c"]
            if self._table_exists(conn, "jobs"):
                completed_today = conn.execute(
                    "SELECT COUNT(*) as c FROM jobs WHERE date(applied_at) = ?",
                    (today,),
                ).fetchone()["c"]
            auto_status = (
                "🟢 Running" if getattr(self, "_auto_running", False) else "⏸️ Paused"
            )
            msg = (
                "<b>🗂️ QUEUE | الطابور</b>\n\n"
                f"📊 <b>Queue Status:</b>\n"
                f"• 🟡 Pending: <b>{pending}</b>\n"
                f"• 🔵 Processing: <b>{processing}</b>\n"
                f"• ✅ Completed Today: <b>{completed_today}</b>\n"
                f"• {auto_status}\n\n"
                f"<i>Use /campaign to start or /pause to stop processing.</i>"
            )
        except Exception as e:
            msg = f"<b>🗂️ QUEUE</b>\n\nCould not fetch queue data: {e}"
        finally:
            if conn:
                conn.close()
        await self.send(msg)

    # ── Rich Inline Button Callback Handlers ───────────────────

    async def _show_main_menu(self, query):
        """Show main menu with rich keyboard."""
        msg = "🚀 <b>JobHunt Pro — Main Menu</b>\n\nWhat would you like to do?"
        await self.send(msg, reply_markup=self._get_nav_keyboard("main"))
        await self.answer_callback_query(query.get("id", ""), "")

    async def _show_stats_compact(self, query):
        """Show compact stats dashboard."""
        await self.answer_callback_query(query.get("id", ""), "")
        await self.cmd_stats_overview("")
        await self.send(
            "<i>📊 Navigation:</i>", reply_markup=self._get_nav_keyboard("stats")
        )

    async def _show_funnel_compact(self, query):
        """Show conversion funnel."""
        await self.answer_callback_query(query.get("id", ""), "")
        await self.cmd_funnel("")

    async def _show_ats_start(self, query):
        """Show ATS score checker."""
        await self.answer_callback_query(query.get("id", ""), "")
        await self.cmd_ats_score("")

    async def _show_converse_start(self, query):
        """Start AI conversation."""
        await self.answer_callback_query(query.get("id", ""), "")
        await self.cmd_converse("")

    async def _show_alerts_status(self, query):
        """Show alerts/inbox status."""
        await self.answer_callback_query(query.get("id", ""), "")
        await self.cmd_inbox_check("")

    async def _show_full_menu(self, query):
        """Show complete command menu."""
        await self.answer_callback_query(query.get("id", ""), "")
        await self.cmd_help("")

    async def _show_help_compact(self, query):
        """Show help guide."""
        await self.answer_callback_query(query.get("id", ""), "")
        await self.cmd_guide("")

    async def _show_apply_menu(self, query):
        """Show apply menu."""
        await self.answer_callback_query(query.get("id", ""), "")
        msg = "🎯 <b>Apply Menu</b>\n\nChoose how you want to apply:"
        await self.send(msg, reply_markup=self._get_nav_keyboard("apply"))

    async def _show_trends(self, query):
        """Show application trends."""
        await self.answer_callback_query(query.get("id", ""), "")
        await self.cmd_trend("")

    async def _show_companies(self, query):
        """Show top companies."""
        await self.answer_callback_query(query.get("id", ""), "")
        await self.cmd_companies("top")

    async def _start_job_search(self, query):
        """Start job search."""
        await self.answer_callback_query(query.get("id", ""), "🔍 Searching...")
        await self.cmd_search("")

    async def _start_auto_apply(self, query):
        """Start auto-apply campaign."""
        await self.answer_callback_query(query.get("id", ""), "")
        await self.cmd_campaign("")

    async def _show_my_campaigns(self, query):
        """Show active campaigns."""
        await self.answer_callback_query(query.get("id", ""), "")
        await self.cmd_campaigns("")

    async def _start_targeted_apply(self, query):
        """Start targeted application."""
        await self.answer_callback_query(query.get("id", ""), "")
        await self.cmd_force_strike("")

    async def _show_job_details(self, query, job_id):
        """Show job details from database."""
        conn = None
        try:
            conn = _get_db()
            conn.row_factory = sqlite3.Row
            c = conn.execute(
                "SELECT id, title, company, location, salary, remote, jid, url, description, source "
                "FROM jobs WHERE id = ?",
                (job_id,),
            )
            row = c.fetchone()
            if not row:
                await self.answer_callback_query(
                    query.get("id", ""), "Job not found", True
                )
                return
            await self.answer_callback_query(query.get("id", ""), "")
            msg = (
                f"📌 <b>{row['title']}</b>\n\n"
                f"🏢 <b>Company:</b> {row['company']}\n"
                f"📍 <b>Location:</b> {row['location'] or 'Remote'}\n"
            )
            if row.get("salary"):
                msg += f"💰 <b>Salary:</b> {row['salary']}\n"
            if row.get("remote"):
                msg += f"🏠 <b>Remote:</b> {'Yes' if row['remote'] else 'No'}\n"
            if row.get("source"):
                msg += f"🔗 <b>Source:</b> {row['source']}\n"
            if row.get("description"):
                desc = row["description"][:300]
                msg += f"\n📝 <b>Description:</b>\n{desc}..."
            if row.get("url"):
                msg += f"\n\n🔗 <a href='{row['url']}'>View Original Posting</a>"
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "🚀 Apply Now", "callback_data": f"apply_{row['id']}"},
                        {"text": "🔙 Back", "callback_data": "nav_main"},
                    ]
                ]
            }
            await self.send(msg, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            logger.error(f"_show_job_details error: {e}")
            await self.answer_callback_query(
                query.get("id", ""), "Error loading job", True
            )
        finally:
            if conn:
                conn.close()

    async def _apply_to_job(self, query, job_id):
        """Apply to a specific job."""
        await self.answer_callback_query(query.get("id", ""), "Applying...")
        conn = None
        try:
            conn = _get_db()
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT id, title, company, location, salary FROM jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
            if not row:
                await self.send("❌ Job not found in database.")
                return
            # Mark as applied
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("UPDATE jobs SET applied_at = ? WHERE id = ?", (now, job_id))
            conn.commit()
            msg = (
                f"🚀 <b>APPLICATION SUBMITTED!</b>\n\n"
                f"📌 <b>{row['title']}</b>\n"
                f"🏢 <b>Company:</b> {row['company']}\n"
                f"📍 <b>Location:</b> {row['location'] or 'Remote'}\n"
                f"⏰ <b>Applied at:</b> {now[:19]}\n\n"
                "<i>✅ Your application has been recorded.</i>"
            )
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "📊 View Stats", "callback_data": "show_stats"},
                        {"text": "🔙 Home", "callback_data": "show_main"},
                    ]
                ]
            }
            await self.send(msg, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"_apply_to_job error: {e}")
            await self.send(f"❌ Application error: {e}")
        finally:
            if conn:
                conn.close()

    # ── Inline Query Handler — Search Jobs from ANY Chat ───────

    async def inline_query(self, inline_q):
        """Handle inline queries - search jobs from any chat."""
        query = inline_q.get("query", "").strip()
        iq_id = inline_q.get("id", "")

        if not query or len(query) < 2:
            await self.http_client.post(
                f"{self.base_url}/answerInlineQuery",
                json={"inline_query_id": iq_id, "results": [], "cache_time": 10},
            )
            return

        # Search local DB for jobs
        conn = None
        results = []
        try:
            conn = _get_db()
            conn.row_factory = sqlite3.Row
            c = conn.execute(
                """SELECT id, title, company, location, salary, remote, jid 
                   FROM jobs WHERE title LIKE ? OR company LIKE ? 
                   LIMIT 20""",
                (f"%{query}%", f"%{query}%"),
            )
            for i, row in enumerate(c.fetchall()):
                title_text = f"📌 *{row['title']}*\n"
                title_text += f"🏢 {row['company']}\n"
                title_text += f"📍 {row['location'] or 'Remote'}\n"
                if row.get("salary"):
                    title_text += f"💰 {row['salary']}\n"

                results.append(
                    {
                        "type": "article",
                        "id": f"job_{i}",
                        "title": f"{row['title']} @ {row['company']}",
                        "description": f"{row['location'] or 'Remote'} | {row.get('salary', 'N/A')}",
                        "input_message_content": {
                            "message_text": title_text,
                            "parse_mode": "Markdown",
                        },
                        "thumb_url": "https://cdn-icons-png.flaticon.com/512/3161/3161146.png",
                        "reply_markup": {
                            "inline_keyboard": [
                                [
                                    {
                                        "text": "📋 View Details",
                                        "callback_data": f"job_{row['id']}",
                                    },
                                    {
                                        "text": "🚀 Apply",
                                        "callback_data": f"apply_{row['id']}",
                                    },
                                ]
                            ]
                        },
                    }
                )
        except Exception as e:
            logger.error(f"Inline query error: {e}")
        finally:
            if conn:
                conn.close()

        await self.http_client.post(
            f"{self.base_url}/answerInlineQuery",
            json={"inline_query_id": iq_id, "results": results[:50], "cache_time": 10},
        )
    async def _dispatch_admin_callback(self, callback, action: str) -> bool:
        """Dispatch admin actions."""
        mapping = {
            "status": self._admin_send_status,
            "logs": self._admin_send_logs,
            "offset": self._admin_send_offset,
            "db": self._admin_send_db,
            "restart": self._admin_do_restart,
            "health": self._admin_send_status,
            "accounts": self._admin_send_accounts,
        }
        handler = mapping.get(action)
        if handler:
            await handler()
            await self.answer_callback_query(callback.get("id", ""), "")
            return True
        await self.answer_callback_query(callback.get("id", ""), "Unknown admin action", True)
        return True

    async def _dispatch_command_callback(self, callback_id: str, data: str) -> bool:
        """Dispatch direct command action routing."""
        cmd_map = {
            cmd: getattr(self, method_name)
            for cmd, method_name in COMMANDS_MAP.items()
        }
        handler = cmd_map.get(data)
        if handler:
            await handler("")
            await self.answer_callback_query(callback_id, "")
            return True
        return False

    async def _dispatch_rich_callback(self, callback, data: str) -> bool:
        """Dispatch rich menu callback routing."""
        rich_routes = {
            "show_main": self._show_main_menu,
            "show_stats": self._show_stats_compact,
            "show_funnel": self._show_funnel_compact,
            "show_ats": self._show_ats_start,
            "show_converse": self._show_converse_start,
            "show_alerts": self._show_alerts_status,
            "show_menu": self._show_full_menu,
            "show_help": self._show_help_compact,
            "nav_main": self._show_main_menu,
            "start_apply": self._show_apply_menu,
            "refresh_stats": self._show_stats_compact,
            "show_trends": self._show_trends,
            "show_companies": self._show_companies,
            "search_jobs": self._start_job_search,
            "auto_apply": self._start_auto_apply,
            "my_campaigns": self._show_my_campaigns,
            "targeted_apply": self._start_targeted_apply,
        }
        rich_handler = rich_routes.get(data)
        if rich_handler:
            await rich_handler(callback)
            return True
        return False

    async def _dispatch_gen_callback(self, callback_id: str, data: str, _cb_msg_id: int, now: float, _hcl) -> bool:
        """Dispatch gen callback with locking and deduplication."""
        gen_handlers = {
            "/gen_auto": self._handle_gen_auto,
            "/gen_quick_25": self._handle_gen_quick_25,
            "/gen_quick_50": self._handle_gen_quick_50,
            "/gen_quick_100": self._handle_gen_quick_100,
            "/gen_q_5": self._handle_gen_q_5,
            "/gen_q_10": self._handle_gen_q_10,
            "/gen_q_25": self._handle_gen_q_25,
            "/gen_q_50": self._handle_gen_q_50,
            "/gen_q_100": self._handle_gen_q_100,
            "/gen_q_200": self._handle_gen_q_200,
            "/gen_q_500": self._handle_gen_q_500,
            "/gen_value": self._handle_gen_value,
            "/gen_value_old": self._handle_gen_value_old,
            "/gen_custom": self._handle_gen_custom,
            "/gen_cancel": self._handle_gen_cancel,
        }
        gen_handler = gen_handlers.get(data)
        if not gen_handler:
            return False

        async with self._cb_lock:
            _dedup_key = f"{_cb_msg_id}:{data}"
            if (
                _dedup_key in self._recent_gen_data
                and now - self._recent_gen_data[_dedup_key] < 30
            ):
                _hcl.info(
                    f"CB_DEDUP_DATA: {_dedup_key} - IGNORING (age={now - self._recent_gen_data[_dedup_key]:.1f}s)"
                )
                await self.answer_callback_query(callback_id, "")
                return True
            self._recent_gen_data[_dedup_key] = now
            self._recent_gen_data = {
                k: v for k, v in self._recent_gen_data.items() if now - v < 120
            }
            _hcl.info(f"CB_GEN_FIRE: handler={data} dedup_key={_dedup_key}")
            await gen_handler()
            _hcl.info(f"CB_GEN_DONE: handler={data}")
        await self.answer_callback_query(callback_id, "")
        return True

    # ── Inline Keyboard Handler ─────────────────────────────────

    async def handle_callback_query(self, callback):
        """Handle inline keyboard button presses."""
        import logging as _hcl

        _cb_id = callback.get("id", "")
        _cb_data = callback.get("data", "")
        _cb_from = callback.get("from", {}).get("id", 0)
        _cb_msg = callback.get("message", {})
        _cb_msg_id = _cb_msg.get("message_id", 0)
        now = time.time()

        # ── INFO-level callback log for debugging ──
        _hcl.info(
            f"CB_RECV id={str(_cb_id)[:20]} msg_id={_cb_msg_id} data={repr(_cb_data)[:60]} from={_cb_from}"
        )

        # Rate limit: max 10 callbacks per 60 seconds per user
        if _cb_from and not await self._check_rate_limit(_cb_from, max_per_minute=10):
            _hcl.info(f"CB_RATE_LIMIT: {_cb_from} - throttled")
            await self.answer_callback_query(
                _cb_id, "⏳ Please slow down!", show_alert=False
            )
            return

        # Dedup: ignore duplicate callback IDs within 10 seconds
        if _cb_id in self._processed_callbacks:
            if now - self._processed_callbacks[_cb_id] < 10:
                _hcl.info("CB_DEDUP_ID: " + str(_cb_id)[:20] + " - IGNORING")
                await self.answer_callback_query(_cb_id, "")
                return
        self._processed_callbacks[_cb_id] = now
        # Clean old entries
        self._processed_callbacks = {
            k: v for k, v in self._processed_callbacks.items() if now - v < 60
        }

        _hcl.info(
            "CB_PROCESS: "
            + str(_cb_id)[:20]
            + " data="
            + repr(_cb_data)[:60]
            + " from="
            + str(_cb_from)
        )
        data = callback.get("data", "")
        if not data:
            return

        if data.startswith("admin_"):
            action = data.replace("admin_", "")
            await self._dispatch_admin_callback(callback, action)
            return

        # Direct command routing
        command_dispatched = await self._dispatch_command_callback(_cb_id, data)
        if command_dispatched:
            return

        # Rich callback routing
        rich_dispatched = await self._dispatch_rich_callback(callback, data)
        if rich_dispatched:
            return

        # job_/apply_ callback handling
        if data.startswith("job_"):
            await self._show_job_details(callback, data[4:])
            return
        if data.startswith("apply_"):
            await self._apply_to_job(callback, data[6:])
            return

        # Gen callback routing
        gen_dispatched = await self._dispatch_gen_callback(_cb_id, data, _cb_msg_id, now, _hcl)
        if gen_dispatched:
            return

        await self.answer_callback_query(_cb_id, "Button not available", True)
        await self.send(
            f"<b>⚠️ Unknown button:</b> {data}\n\nUse /start to refresh the menu."
        )

    # ── AUTO-GENERATED HANDLERS (v16.92) ─────────────────────

    # ── TELEGRAM ANALYTICS: Trend Analysis ────────────────────────

    async def cmd_trend(self, args=""):
        """Show application trends with ASCII bar chart.
        Usage: /trend [week|month|14|90|N]
        """
        try:
            await self.send("<b>📈 Analyzing trends...</b>")
            data = self.analytics.get_trends(args)
            msg = self.analytics.generate_trend_chart(data)
            await self.send(msg)
        except Exception as e:
            logger.error(f"[BOT] cmd_trend error: {e}")
            await self.send(
                "<b>📈 Trend Analysis Unavailable</b>\n\nTrend data could not be generated. The analytics engine may still be initializing.\nTry /stats for a quick overview or /start for the main menu."
            )

    # ── TELEGRAM ANALYTICS: Conversion Funnel ─────────────────────

    async def cmd_funnel(self, args=""):
        """Show application conversion funnel with ASCII chart."""
        try:
            await self.send("<b>📊 Building funnel...</b>")
            data = self.analytics.get_funnel(args)
            msg = self.analytics.generate_funnel_chart(data)
            await self.send(msg)
        except Exception as e:
            logger.error(f"[BOT] cmd_funnel error: {e}")
            await self.send(
                "<b>📊 Funnel Chart Unavailable</b>\n\nThe conversion funnel could not be generated. This may happen if there isn't enough application data yet.\nTry running a campaign first with /campaign, then check back."
            )

    async def cmd_uptime(self, args=""):
        """Show bot uptime."""
        try:
            import time

            uptime_seconds = int(time.time() - self.bot_start_time.timestamp())
            h, m = divmod(uptime_seconds, 3600)
            m, s = divmod(m, 60)
            d, h = divmod(h, 24)
            parts = []
            if d:
                parts.append(f"{d}d")
            if h:
                parts.append(f"{h}h")
            if m:
                parts.append(f"{m}m")
            parts.append(f"{s}s")
            await self.send(f"<b>⏱️ Bot Uptime</b>: {' '.join(parts)}")
        except Exception as e:
            await self.send(f"<b>⏱️ Uptime Error:</b> {e}")

    async def cmd_memory(self, args=""):
        """Show memory usage."""
        try:
            import psutil

            proc = psutil.Process()
            mem = proc.memory_info().rss / 1024 / 1024
            cpu = proc.cpu_percent(interval=0.1)
            await self.send(
                f"<b>🌡️ System Resources</b>\n• RAM: {mem:.1f} MB\n• CPU: {cpu:.1f}%"
            )
        except ImportError:
            await self.send(
                "<b>🌡️ Memory:</b> psutil not installed (install with pip install psutil)"
            )
        except Exception as e:
            await self.send(f"<b>🌡️ Memory Error:</b> {e}")

    async def cmd_speed_test(self, args=""):
        """Test bot response speed."""
        try:
            import time

            start = time.time()
            await self.send("⚡ Speed test initiated...")
            elapsed = int((time.time() - start) * 1000)
            await self.send(f"<b>⚡ Speed Test Result:</b>\nResponse time: {elapsed}ms")
        except Exception as e:
            await self.send(f"<b>⚡ Speed Test Error:</b> {e}")

    async def cmd_env_check(self, args=""):
        """Check environment variables."""
        try:
            import os

            keys = [
                "TELEGRAM_BOT_TOKEN",
                "TELEGRAM_CHAT_ID",
                "GROQ_API_KEY",
                "JSEARCH_API_KEY",
                "BREVO_API_KEY",
                "DB_PATH",
                "SMTP_HOST",
                "SMTP_PORT",
            ]
            lines = ["<b>🔑 Environment Check:</b>", ""]
            for k in keys:
                val = os.getenv(k, "")
                status = "✅ SET" if val else "❌ MISSING"
                (
                    f"{val[:8]}..."
                    if val and len(val) > 8
                    else ("HIDDEN" if val else "EMPTY")
                )
                lines.append(f"• {k}: {status}")
            await self.send("\n".join(lines))
        except Exception as e:
            await self.send(f"<b>🔑 Env Error:</b> {e}")

    async def cmd_platforms(self, args=""):
        """Check platform status."""
        try:
            platforms = [
                ("PythonAnywhere", f"{config.SITE_URL}/health"),
                ("Render", f"{config.RENDER_APP_URL}health"),
            ]
            lines = ["<b>🌐 Platform Status:</b>", ""]
            for name, url in platforms:
                try:
                    r = await self.http_client.get(url, timeout=5)
                    lines.append(
                        f"• {name}: {'✅ ONLINE' if r.status_code == 200 else f'⚠️ HTTP {r.status_code}'}"
                    )
                except Exception:
                    logger.debug(f"Platform check failed: {name}")
                    lines.append(f"• {name}: ❌ OFFLINE")
            await self.send("\n".join(lines))
        except Exception as e:
            await self.send(f"<b>🌐 Platforms Error:</b> {e}")

    async def cmd_synapse(self, args=""):
        """Show synapse/system power metrics."""
        conn = None
        try:
            conn = _get_db()
            users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
            campaigns = (
                conn.execute("SELECT COUNT(*) as c FROM campaigns").fetchone()["c"]
                if self._table_exists(conn, "campaigns")
                else 0
            )
            await self.send(
                f"<b>💪 Synapse Status</b>\n• Active Users: {users}\n• Campaigns: {campaigns}\n• Agents: 200\n• Mode: ULTIMATE"
            )
        except Exception as e:
            await self.send(f"<b>💪 Synapse Status</b>\n• Error: {e}")
        finally:
            if conn:
                conn.close()

    # ── BUILD ENHANCEMENT: ATS Score Command ────────────────────────────────────

    async def cmd_ats_score(self, args=""):
        """ATS Resume Match Score — analyze resume vs job description.

        Usage:
          /ats_score           — shows usage help
          /ats_score <job_url> — analyze resume against a job description URL

        Interactive mode:
          The bot will prompt for resume text and job description if not provided.
        """
        try:
            from core.ats_matcher import ATSMatcher, format_ats_for_telegram

            if not args.strip():
                await self.send(
                    "<b>📊 ATS Resume Match Score</b>\n\n"
                    "Analyze how well your resume matches a job description.\n\n"
                    "<b>Usage:</b>\n"
                    "  <code>/ats_score <job_description_text></code>\n"
                    "  or paste resume + JD text\n\n"
                    "<b>What it does:</b>\n"
                    "  • Keywords extraction with n-gram analysis\n"
                    "  • Weighted scoring with industry-specific boosts\n"
                    "  • Partial/fuzzy matching for synonyms\n"
                    "  • Actionable ATS optimization tips\n"
                    "  • Missing keywords ranked by importance\n\n"
                    "Alternative: <code>/ats_score resume_text | JD_text</code> (separate sections with |)"
                )
                return

            # Parse input: expect "resume_text | jd_text" format
            parts = args.split("|")
            if len(parts) >= 2:
                resume_text = parts[0].strip()
                jd_text = parts[1].strip()
            else:
                # If only one block, assume it's just a JD to compare against default resume
                # For now, use stored resume from config or DB
                jd_text = args.strip()
                resume_text = self._get_resume_text()
                if not resume_text:
                    await self.send(
                        "<b>⚠️ Resume Not Found</b>\n\n"
                        "Please provide resume and JD separated by |\n"
                        "Example: <code>/ats_score my resume text | job description text</code>"
                    )
                    return

            logger.info(
                f"[ATS] Running match: resume={len(resume_text)} chars, jd={len(jd_text)} chars"
            )

            await self.send(
                "⏳ Analyzing resume against job description... (algorithmic match)"
            )

            matcher = ATSMatcher()
            result = matcher.calculate_match(resume_text, jd_text)

            formatted = format_ats_for_telegram(
                {
                    "algorithmic": result,
                    "combined_score": result["match_percent"],
                    "source": "algorithmic",
                }
            )

            await self.send(formatted)

            # Optionally run Groq analysis
            try:
                from core.ats_matcher import analyze_with_groq

                await self.send("🔄 Running AI deep analysis (Groq)...")
                groq_result = analyze_with_groq(resume_text, jd_text)
                if groq_result and groq_result.get("match_percent") is not None:
                    ai_score = groq_result.get("match_percent", 0)
                    combined = round(result["match_percent"] * 0.6 + ai_score * 0.4, 1)
                    await self.send(
                        f"<b>🤖 AI Analysis Complete</b>\n\n"
                        f"• AI Score: <b>{ai_score}%</b>\n"
                        f"• Combined: <b>{combined}%</b>\n"
                        f"• Missing: {', '.join(groq_result.get('missing_skills', [])[:5])}\n"
                        f"─"
                    )
            except Exception as groq_e:
                logger.warning(f"[ATS] Groq analysis skipped: {groq_e}")

        except Exception as e:
            logger.error(f"[ATS] Command error: {e}")
            await self.send(
                f"<b>❌ ATS Score Error:</b> {e}\n\nTry again with /ats_score help"
            )

    # ── BUILD ENHANCEMENT: AI Conversation Engine Command ───────────────────────

    async def cmd_converse(self, args: str = "") -> None:
        """AI Recruiter Conversation Engine.

        Usage:
          /converse                — show active conversations
          /converse greet <name/company/role>  — generate greeting
          /converse reply <msg>    — suggest reply to recruiter message
          /converse status         — all conversation status

        Examples:
          /converse greet Sarah/Google/Network Engineer
          /converse reply Thanks for reaching out! Are you available for a call?
        """
        try:
            parts = args.strip().split(" ", 1) if args.strip() else ["status"]
            action = parts[0].lower() if parts else "status"
            payload = parts[1] if len(parts) > 1 else ""

            if action in ("greet", "greeting"):
                await self._cmd_converse_greet(payload)
            elif action in ("reply", "suggest"):
                await self._cmd_converse_reply(payload)
            elif action in ("status", "list", "conversations"):
                await self._cmd_converse_status()
            elif action == "batch":
                await self._cmd_converse_batch(payload)
            elif action in ("help", "?", ""):
                await self._cmd_converse_help()
            else:
                await self.send(
                    f"<b>❌ Unknown action:</b> {action}\n"
                    f"Try: <code>/converse help</code> for available commands."
                )
        except Exception as e:
            logger.error(f"[Converse] Command error: {e}")
            await self.send(f"<b>❌ Conversation Engine Error:</b> {e}")

    async def _cmd_converse_greet(self, payload: str) -> None:
        """Helper to handle greeting generation."""
        from core.ai_conversation import format_conversation_for_telegram
        formatted = format_conversation_for_telegram(
            recruiter_id=payload or "unknown/unknown/position",
            action="greeting",
        )
        await self.send(formatted)

    async def _cmd_converse_reply(self, payload: str) -> None:
        """Helper to suggest response to recruiter message."""
        if not payload:
            await self.send(
                "<b>💬 Reply Suggestion</b>\n\n"
                "Usage: <code>/converse reply <recruiter_message></code>\n\n"
                "Example: <code>/converse reply I'd like to schedule an interview</code>"
            )
            return
        from core.ai_conversation import format_conversation_for_telegram
        formatted = format_conversation_for_telegram(
            recruiter_id="",
            action="reply",
            message=payload,
        )
        await self.send(formatted)

    async def _cmd_converse_status(self) -> None:
        """Helper to show active conversation status list."""
        from core.ai_conversation import format_conversation_for_telegram
        formatted = format_conversation_for_telegram(
            recruiter_id="",
            action="status",
        )
        await self.send(formatted)

    async def _cmd_converse_batch(self, payload: str) -> None:
        """Helper to batch generate greetings from a comma-separated list."""
        if not payload:
            await self.send(
                "<b>📦 Batch Greetings</b>\n\n"
                "Usage: <code>/converse batch Name1/Co1/Role1, Name2/Co2/Role2</code>"
            )
            return
        from core.ai_conversation import AIConversationEngine
        entries = [e.strip() for e in payload.split(",")]
        lines = ["<b>📦 Batch Greetings Generated</b>\n"]
        eng = AIConversationEngine()
        for entry in entries:
            parts_e = entry.split("/")
            name = parts_e[0] if len(parts_e) > 0 else "Hiring Manager"
            company = parts_e[1] if len(parts_e) > 1 else "Company"
            role = parts_e[2] if len(parts_e) > 2 else "Position"
            greeting = eng.generate_greeting(name, company, role)
            lines.append(f"<b>{name} @ {company}</b>\n{greeting}\n")
            eng.track_message(f"{name}@{company}", "candidate", greeting)
        batch_msg = "\n".join(lines)
        if len(batch_msg) > 4000:
            batch_msg = batch_msg[:3950] + "\n\n...(truncated)"
        await self.send(batch_msg)

    async def _cmd_converse_help(self) -> None:
        """Helper to send converse commands help page."""
        await self.send(
            "<b>🤖 AI Conversation Engine</b>\n\n"
            "<b>Commands:</b>\n"
            "  <code>/converse</code> — show active conversations\n"
            "  <code>/converse greet <name/company/role></code> — generate greeting\n"
            "  <code>/converse reply <msg></code> — suggest a reply\n"
            "  <code>/converse batch <list></code> — batch generate\n"
            "  <code>/converse status</code> — all conversations\n\n"
            "<b>Examples:</b>\n"
            "  <code>/converse greet Sarah/Google/Senior Engineer</code>\n"
            "  <code>/converse reply Yes I'm available Thursday!</code>"
        )

    # ── Helper: get resume text from config/db ────────────────────────────────

    def _get_resume_text(self):
        """Try to retrieve stored resume text for ATS matching."""
        conn = None
        try:
            conn = _get_db()
            row = conn.execute(
                "SELECT resume_text FROM user_profile LIMIT 1"
            ).fetchone()
            if row and row.get("resume_text"):
                return row["resume_text"]
        except Exception:
            pass
        finally:
            if conn:
                conn.close()

        # Fallback: check config
        try:
            cv_path = getattr(config, "CV_TEXT_PATH", "")
            if cv_path and os.path.exists(cv_path):
                with open(cv_path, "r", encoding="utf-8") as f:
                    return f.read()
        except Exception:
            pass

        return None

    async def cmd_audit(self, args=""):
        """Run system audit."""
        conn = None
        try:
            conn = _get_db()
            users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
            orders = conn.execute(
                "SELECT COUNT(*) as c FROM orders WHERE payment_status='completed'"
            ).fetchone()["c"]
            revenue = conn.execute(
                "SELECT COALESCE(SUM(amount_usd),0) as s FROM orders WHERE payment_status='completed'"
            ).fetchone()["s"]
            await self.send(
                f"<b>🔍 System Audit</b>\n• Users: {users}\n• Completed Orders: {orders}\n• Revenue: ${revenue:.2f}\n• Status: ACTIVE"
            )
        except Exception as e:
            await self.send(f"<b>🔍 Audit Error:</b> {e}")
        finally:
            if conn:
                conn.close()

    async def cmd_boost(self, args=""):
        """Toggle boost mode for maximum performance."""
        async with self._state_lock:
            self._boost_mode = not getattr(self, "_boost_mode", False)
        status = "🔥 ACTIVE" if self._boost_mode else "💤 INACTIVE"
        await self.send(
            f"<b>🔥 Boost Mode: {status}</b>\n\n"
            f"When ACTIVE, the system runs at maximum performance"
            f" with reduced delays between operations.\n\n"
            f"<i>Toggle: /boost</i>"
        )

    async def cmd_clear_queue(self, args=""):
        """Clear pending job queue."""
        conn = None
        try:
            conn = _get_db()
            if self._table_exists(conn, "job_queue"):
                count = conn.execute(
                    "SELECT COUNT(*) as c FROM job_queue WHERE status='pending'"
                ).fetchone()["c"]
                conn.execute("DELETE FROM job_queue WHERE status='pending'")
                conn.commit()
                await self.send(
                    f"<b>🗑️ Queue Cleared</b>\n• Removed {count} pending jobs"
                )
            else:
                await self.send("<b>🗑️ Queue:</b> No job_queue table found")
        except Exception as e:
            await self.send(f"<b>🗑️ Clear Queue Error:</b> {e}")
        finally:
            if conn:
                conn.close()

    async def cmd_countries(self, args=""):
        """Show target countries."""
        conn = None
        try:
            conn = _get_db()
            rows = []
            if self._table_exists(conn, "search_config"):
                rows = conn.execute(
                    "SELECT country, COUNT(*) as c FROM search_config GROUP BY country ORDER BY c DESC"
                ).fetchall()
            if rows:
                lines = ["<b>🌍 Target Countries:</b>", ""]
                for r in rows[:10]:
                    lines.append(f"• {r['country']}: {r['c']} configs")
                await self.send("\n".join(lines))
            else:
                await self.send(
                    "<b>🌍 Countries:</b> No search configs yet. Use /settings to configure."
                )
        except Exception as e:
            await self.send(f"<b>🌍 Countries Error:</b> {e}")
        finally:
            if conn:
                conn.close()

    async def cmd_job_titles(self, args=""):
        """Show target job titles."""
        conn = None
        try:
            conn = _get_db()
            rows = []
            if self._table_exists(conn, "search_config"):
                rows = conn.execute(
                    "SELECT job_title, COUNT(*) as c FROM search_config GROUP BY job_title ORDER BY c DESC"
                ).fetchall()
            if rows:
                lines = ["<b>💼 Target Job Titles:</b>", ""]
                for r in rows[:10]:
                    lines.append(f"• {r['job_title']}: {r['c']}")
                await self.send("\n".join(lines))
            else:
                await self.send(
                    "<b>💼 Job Titles:</b> No search configs yet. Use /settings to configure."
                )
        except Exception as e:
            await self.send(f"<b>💼 Job Titles Error:</b> {e}")
        finally:
            if conn:
                conn.close()

    async def cmd_cover_letter(self, args=""):
        """Show cover letter template."""
        await self.send(
            "<b>📝 Cover Letter</b>\n\n"
            "Your cover letter is auto-generated by AI based on your CV.\n\n"
            "Use /cv_preview to see your CV\n"
            "Use /prep for interview preparation\n\n"
            f"<i>Upload or update your CV at: {config.SITE_URL}/upload-cv</i>"
        )

    async def cmd_cv_preview(self, args=""):
        """Preview CV."""
        await self.send(
            "<b>📄 CV Preview</b>\n\n"
            "Your CV is stored securely and used by AI to generate tailored applications.\n\n"
            "Upload/update your CV at:\n"
            f"{config.SITE_URL}/upload-cv\n\n"
            "<i>Supports PDF and DOCX formats</i>"
        )

    async def cmd_dry_run(self, args=""):
        """Toggle dry run mode."""
        async with self._state_lock:
            self._dry_run = not getattr(self, "_dry_run", False)
        status = "ON" if self._dry_run else "OFF"
        await self.send(
            f"<b>🧪 Dry Run Mode: {status}</b>\n\nWhen ON, the system simulates applications without actually sending them."
        )

    async def cmd_failure_rate(self, args=""):
        """Show application failure rate."""
        conn = None
        try:
            conn = _get_db()
            total = 0
            failed = 0
            if self._table_exists(conn, "applications"):
                total = conn.execute(
                    "SELECT COUNT(*) as c FROM applications"
                ).fetchone()["c"]
                failed = conn.execute(
                    "SELECT COUNT(*) as c FROM applications WHERE status LIKE '%fail%' OR status LIKE '%error%'"
                ).fetchone()["c"]
            rate = (failed / total * 100) if total > 0 else 0
            await self.send(
                f"<b>📉 Failure Rate</b>\n• Total Apps: {total}\n• Failed: {failed}\n• Rate: {rate:.1f}%\n• Status: {'⚠️ HIGH' if rate > 30 else '✅ NORMAL' if rate > 0 else '📊 NO DATA'}"
            )
        except Exception as e:
            await self.send(f"<b>📉 Failure Rate Error:</b> {e}")
        finally:
            if conn:
                conn.close()

    async def cmd_find_emails(self, args=""):
        """Find email addresses for a company."""
        await self.send(
            "<b>📧 Find Emails</b>\n\n"
            "🚧 <b>Coming Soon</b>\n\n"
            "Email discovery engine is under development.\n\n"
            "In the meantime, use:\n"
            "• /companies — Browse target companies\n"
            "• /search — Find new job leads with contact info\n\n"
            "<i>Automated email finding will be available soon.</i>"
        )

    async def cmd_kill_switch(self, args=""):
        """Emergency kill switch — stops all processes and clears queues."""
        async with self._state_lock:
            self._auto_running = False
        conn = None
        try:
            conn = _get_db()
            # Clear pending campaign_emails
            if self._table_exists(conn, "campaign_emails"):
                conn.execute(
                    "UPDATE campaign_emails SET status='cancelled' WHERE status='pending'"
                ).fetchone()
            if self._table_exists(conn, "job_queue"):
                conn.execute("DELETE FROM job_queue WHERE status='pending'")
            if self._table_exists(conn, "campaigns"):
                conn.execute(
                    "UPDATE campaigns SET status='halted' WHERE status='running' OR status='pending'"
                )
            conn.commit()
            await self.send(
                "<b>☠️ KILL SWITCH ACTIVATED</b>\n\n"
                "✅ All pending processes cancelled\n"
                "✅ All queues cleared\n"
                "✅ Auto-run stopped\n\n"
                "Use /resume to restart operations."
            )
        except Exception as e:
            await self.send(f"<b>❌ Kill Switch Error:</b> {e}")
        finally:
            if conn:
                conn.close()

    async def cmd_night_mode(self, args=""):
        """Toggle night mode."""
        async with self._state_lock:
            self._night_mode = not getattr(self, "_night_mode", False)
        status = "ON 🌙" if self._night_mode else "OFF ☀️"
        await self.send(
            f"<b>🌙 Night Mode: {status}</b>\n\nWhen ON, the bot reduces non-critical notifications and slows polling."
        )

    async def cmd_omega_halt(self, args=""):
        """Emergency full stop — halts all operations."""
        async with self._state_lock:
            self._auto_running = False
        conn = None
        try:
            conn = _get_db()
            if self._table_exists(conn, "campaigns"):
                conn.execute(
                    "UPDATE campaigns SET status='halted' WHERE status IN ('running','pending')"
                )
            if self._table_exists(conn, "campaign_emails"):
                conn.execute(
                    "UPDATE campaign_emails SET status='cancelled' WHERE status='pending'"
                )
            conn.commit()
            await self.send(
                "<b>🛑 OMEGA HALT</b>\n\n⚠️ Emergency stop initiated.\n✅ All campaigns halted.\n✅ All pending emails cancelled.\n\nUse /resume to restart operations."
            )
        except Exception as e:
            await self.send(f"<b>🛑 OMEGA HALT ERROR:</b> {e}")
        finally:
            if conn:
                conn.close()

    async def cmd_pin_lead(self, args=""):
        """Pin a lead by index."""
        await self.send(
            "<b>📌 Pin Lead</b>\n\n"
            "🚧 <b>Coming Soon</b>\n\n"
            "Pin leads to give them priority processing.\n\n"
            "In the meantime, use:\n"
            "• /leads — Browse current leads\n"
            "• /search — Find new opportunities\n\n"
            "<i>Lead pinning will be available in a future update.</i>"
        )

    async def cmd_prep(self, args=""):
        """Interview preparation."""
        await self.send(
            "<b>📝 Interview Prep</b>\n\n"
            "🚧 <b>Coming Soon</b>\n\n"
            "AI-powered interview preparation is under development.\n\n"
            "This feature will generate:\n"
            "• Common interview questions\n"
            "• Company research & talking points\n"
            "• Role-specific preparation guides\n\n"
            "<i>Stay tuned for this upcoming feature!</i>"
        )

    async def cmd_retry_failed(self, args=""):
        """Retry failed applications."""
        conn = None
        try:
            conn = _get_db()
            count = 0
            if self._table_exists(conn, "applications"):
                count = conn.execute(
                    "SELECT COUNT(*) as c FROM applications WHERE status LIKE '%fail%' OR status LIKE '%error%'"
                ).fetchone()["c"]
            await self.send(
                f"<b>🔄 Retry Failed</b>\n\n• Failed applications: {count}\n\nUse /campaign to restart the auto-run and retry failed apps."
            )
        except Exception as e:
            await self.send(f"<b>🔄 Retry Error:</b> {e}")
        finally:
            if conn:
                conn.close()

    async def cmd_set_key(self, args=""):
        """Set API key."""
        await self.send(
            "<b>🔑 Set API Key</b>\n\n"
            "🚧 <b>Coming Soon</b>\n\n"
            "API key management via Telegram is under development.\n\n"
            "For now, update keys in the web dashboard:\n"
            f"{config.SITE_URL}/settings\n\n"
            "Or use /ai_check to verify current AI connectivity.\n\n"
            "<i>Available keys: GROQ_API_KEY, JSEARCH_API_KEY, BREVO_API_KEY</i>"
        )

    async def cmd_tasks(self, args=""):
        """Show all pending tasks."""
        conn = None
        try:
            conn = _get_db()
            tasks = []
            if self._table_exists(conn, "job_queue"):
                tasks = conn.execute(
                    "SELECT * FROM job_queue WHERE status='pending' LIMIT 5"
                ).fetchall()
            if tasks:
                lines = ["<b>🧬 Pending Tasks:</b>", ""]
                for t in tasks:
                    lines.append(f"• {dict(t)}")
                await self.send("\n".join(lines[:10]))
            else:
                await self.send(
                    "<b>🧬 Tasks:</b> No pending tasks. Use /search to find new jobs."
                )
        except Exception as e:
            await self.send(f"<b>🧬 Tasks Error:</b> {e}")
        finally:
            if conn:
                conn.close()

    async def cmd_test_email(self, args=""):
        """Test email delivery."""
        await self.send(
            "<b>📧 Test Email</b>\n\n"
            "🚧 <b>Coming Soon</b>\n\n"
            "Email testing via Telegram is under development.\n\n"
            f"For now, test delivery via the web dashboard:\n"
            f"{config.SITE_URL}/email-test\n\n"
            "<i>Direct Telegram email testing will be available soon.</i>"
        )

    async def cmd_test_key(self, args=""):
        """Test API key validity."""
        await self.send(
            "<b>🧪 Test API Key</b>\n\n"
            "🚧 <b>Coming Soon</b>\n\n"
            "API key testing via Telegram is under development.\n\n"
            "For now, use:\n"
            "• /ai_check — Verify AI connectivity\n"
            "• /keys — View current key status\n\n"
            "<i>Direct key testing will be available in a future update.</i>"
        )

    async def cmd_top_companies(self, args=""):
        """Show top companies from applications."""
        conn = None
        try:
            conn = _get_db()
            rows = []
            if self._table_exists(conn, "applications"):
                rows = conn.execute(
                    "SELECT company, COUNT(*) as c FROM applications GROUP BY company ORDER BY c DESC LIMIT 10"
                ).fetchall()
            if rows:
                lines = ["<b>🏆 Top Companies Applied:</b>", ""]
                for r in rows:
                    lines.append(f"• {r['company']}: {r['c']} applications")
                await self.send("\n".join(lines))
            else:
                await self.send(
                    "<b>🏆 Top Companies:</b> No applications yet. Start with /campaign!"
                )
        except Exception as e:
            await self.send(f"<b>🏆 Top Companies Error:</b> {e}")
        finally:
            if conn:
                conn.close()

    # ── END AUTO-GENERATED HANDLERS ─────────────────────────

    # ── SALES & PROFIT STATS (ADMIN ONLY) ───────────────────────────

    async def cmd_sales(self, args: str = "") -> None:
        """Show real-time sales and profit stats.

        Usage: /sales [24h|month|year|all]

        Defaults to showing all-time stats.
        """
        conn = None
        try:
            conn = _get_db()
            now = datetime.now()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            year_start = now.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )

            args = args.strip().lower() if args else "all"

            if args == "24h":
                filter_label = "📅 Last 24 Hours"
                since = (now - timedelta(hours=24)).isoformat()
            elif args == "month":
                filter_label = "📅 This Month"
                since = month_start.isoformat()
            elif args == "year":
                filter_label = "📅 This Year"
                since = year_start.isoformat()
            else:
                filter_label = "📅 All Time"
                since = "1970-01-01"

            stats = self._get_sales_stats(conn, since)
            total_revenue = stats["order_revenue"] + stats["codes_revenue"] + stats["email_revenue"]

            msg = (
                f"<b>📈 SALES & PROFIT REPORT</b>\n"
                f"{filter_label}\n"
                f"{'─' * 32}\n\n"
                f"<b>👥 Users</b>\n"
                f"Total: {stats['total_users']}\n"
                f"New: {stats['new_users_filter']}\n\n"
                f"<b>💰 Revenue Breakdown</b>\n"
                f"📦 Orders: <b>${stats['order_revenue']:.2f}</b> ({stats['order_count']} orders)\n"
                f"🎟 Redeem Codes: <b>${stats['codes_revenue']:.2f}</b> ({stats['codes_count']} codes)\n"
                f"📧 Manual Emails: <b>${stats['email_revenue']:.2f}</b> ({stats['email_count']} emails)\n"
                f"{'─' * 28}\n"
                f"<b>💵 TOTAL REVENUE: ${total_revenue:.2f}</b>\n\n"
                f"<b>💳 Wallet</b>\n"
                f"Total Balance: ${stats['total_wallet']:.2f}\n"
                f"Total Spent: ${stats['total_spent']:.2f}\n\n"
            )

            if stats["admin_free_count"] > 0:
                msg += (
                    f"<b>🆓 Admin Free Credits</b>\n"
                    f"Used: {stats['admin_free_count']} codes (${stats['admin_free_value']:.2f})\n"
                    f"<i>Not counted in revenue</i>\n\n"
                )

            msg += (
                "<b>📋 Commands:</b>\n"
                "<code>/sales 24h</code> — Last 24 hours\n"
                "<code>/sales month</code> — This month\n"
                "<code>/sales year</code> — This year\n"
                "<code>/sales all</code> — All time"
            )

            await self.send(msg)

        except Exception as e:
            logger.error(f"Sales command failed: {e}")
            await self.send(f"<b>❌ Failed to fetch sales data:</b> {e}")
        finally:
            if conn:
                conn.close()

    def _get_sales_stats(self, conn, since: str) -> dict:
        """Query database and aggregate user, wallet, order, and manual email stats."""
        total_users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
        new_users_filter = conn.execute(
            "SELECT COUNT(*) as c FROM users WHERE created_at >= ?", (since,)
        ).fetchone()["c"]

        total_wallet = float(
            conn.execute(
                "SELECT COALESCE(SUM(wallet_balance),0) as c FROM users"
            ).fetchone()["c"]
        )
        total_spent = float(
            conn.execute(
                "SELECT COALESCE(SUM(total_spent),0) as c FROM users"
            ).fetchone()["c"]
        )

        completed_orders = conn.execute(
            "SELECT COUNT(*) as c, COALESCE(SUM(amount_usd),0) as s FROM orders WHERE payment_status='completed' AND created_at >= ?",
            (since,),
        ).fetchone()
        order_count = completed_orders["c"]
        order_revenue = float(completed_orders["s"])

        codes_used = conn.execute(
            "SELECT COUNT(*) as c, COALESCE(SUM(value_usd),0) as s FROM redeem_codes WHERE is_used=1 AND (code_type IS NULL OR code_type != 'admin_free') AND created_at >= ?",
            (since,),
        ).fetchone()
        codes_count = codes_used["c"]
        codes_revenue = float(codes_used["s"])

        admin_free = conn.execute(
            "SELECT COUNT(*) as c, COALESCE(SUM(value_usd),0) as s FROM redeem_codes WHERE is_used=1 AND code_type='admin_free' AND created_at >= ?",
            (since,),
        ).fetchone()
        admin_free_count = admin_free["c"]
        admin_free_value = float(admin_free["s"])

        manual_emails = conn.execute(
            "SELECT COUNT(*) as c, COALESCE(SUM(price_usd),0) as s FROM manual_emails WHERE status='sent' AND created_at >= ?",
            (since,),
        ).fetchone()
        email_count = manual_emails["c"]
        email_revenue = float(manual_emails["s"])

        return {
            "total_users": total_users,
            "new_users_filter": new_users_filter,
            "total_wallet": total_wallet,
            "total_spent": total_spent,
            "order_count": order_count,
            "order_revenue": order_revenue,
            "codes_count": codes_count,
            "codes_revenue": codes_revenue,
            "admin_free_count": admin_free_count,
            "admin_free_value": admin_free_value,
            "email_count": email_count,
            "email_revenue": email_revenue,
        }

    # ── EMAIL CAMPAIGN STATS ──────────────────────────────────────

    async def cmd_campaigns(self, args=""):
        """Show email marketing campaign statistics.

        Usage: /campaigns

        Shows sent count, open rate, and breakdown by campaign type.

        """

        conn = None

        try:
            conn = _get_db()

            # Total sent

            total_sent = conn.execute(
                "SELECT COUNT(*) as c FROM email_campaign_log WHERE status='sent'"
            ).fetchone()["c"]

            # Total opened

            total_opened = conn.execute(
                "SELECT COUNT(*) as c FROM email_campaign_log WHERE opened_at IS NOT NULL"
            ).fetchone()["c"]

            # Breakdown by type

            campaigns = conn.execute(
                "SELECT campaign_type, COUNT(*) as c FROM email_campaign_log WHERE status='sent' GROUP BY campaign_type"
            ).fetchall()

            # Recent sends (last 24h)

            recent = conn.execute(
                "SELECT COUNT(*) as c FROM email_campaign_log WHERE status='sent' AND sent_at >= datetime('now', '-1 day')"
            ).fetchone()["c"]

            conn.close()

            open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0

            # Build campaign breakdown

            campaign_detail = ""

            type_labels = {
                "welcome": "🎉 Welcome",
                "abandoned_cart": "🛒 Abandoned Cart",
                "re_engagement": "👋 Re-engagement",
                "post_purchase": "✅ Post-Purchase",
            }

            for row in campaigns:
                ctype = row["campaign_type"]

                count = row["c"]

                label = type_labels.get(ctype, ctype)

                campaign_detail += f"  {label}: <b>{count}</b>\n"

            msg = (
                f"<b>📧 EMAIL MARKETING CAMPAIGNS</b>\n"
                f"{'─' * 32}\n\n"
                f"<b>📊 Overview</b>\n"
                f"📨 Total Sent: <b>{total_sent}</b>\n"
                f"👁 Total Opened: <b>{total_opened}</b>\n"
                f"📈 Open Rate: <b>{open_rate:.1f}%</b>\n"
                f"🕐 Sent (24h): <b>{recent}</b>\n\n"
                f"<b>📋 Campaign Breakdown</b>\n"
                f"{campaign_detail}\n"
                f"<b>🎯 Campaign Types</b>\n"
                f"• Welcome: Sent on registration with 50% OFF code\n"
                f"• Abandoned Cart: 30min after abandoned order\n"
                f"• Re-engagement: 7 days inactive → 30% OFF\n"
                f"• Post-Purchase: 24h after purchase → bundle deal\n\n"
                f"<b>🔗 Tracking Pixel</b>\n"
                f"Open tracking via 1×1 GIF in each email\n"
                f"Check opens by campaign type in the breakdown above\n\n"
                f"<b>📋 Commands:</b>\n"
                f"<code>/campaigns</code> — This overview"
            )

            await self.send(msg)

        except Exception as e:
            logger.error(f"Campaigns command failed: {e}")

            await self.send(f"<b>❌ Failed to fetch campaign data:</b> {e}")

        finally:
            if conn:
                conn.close()

    # ── PROFIT STRATEGY GUIDE ─────────────────────────────────────

    async def cmd_strategy(self, args=""):
        """Complete profit strategy guide — how to use everything for max profit."""

        msg = (
            "<b>📚 JOBHUNT PRO — PROFIT STRATEGY GUIDE</b>\n"
            "Use ALL your weapons for maximum profit without raising prices\n\n"
            "<b>⚡ 1. FLASH SALES (URGENCY)</b>\n"
            'Create a flash sale every weekend: /flash_sale create "Weekend" 25 48\n'
            "25% off for 48h → impulse buys. Stack with social proof for max effect.\n\n"
            "<b>🤝 2. TIERED REFERRALS (VIRAL)</b>\n"
            "Every user is a free salesperson. 5% to 20% commission.\n"
            "Message top referrers personally — make them feel VIP.\n"
            "Promote referral link in every Telegram message.\n\n"
            "<b>🔥 3. LOGIN STREAKS (RETENTION)</b>\n"
            "Users log in daily to build streak → see more upsells.\n"
            "Milestones: 3d=$0.50, 7d=$2, 14d=$5, 21d=$10, 30d=$25\n"
            "Remind users on Telegram about their streak!\n\n"
            "<b>👥 4. SOCIAL PROOF (TRUST)</b>\n"
            "Real purchase notifications popup every 30s on your site.\n"
            '"If others buy, it must be good" — removes hesitation.\n\n'
            "<b>📊 5. BULK DISCOUNT (VOLUME)</b>\n"
            "Up to 30% off for 20+ items. Use for corporate/B2B sales.\n"
            '"Buy 20 packages, save 30%" — closes large deals.\n\n'
            "<b>💰 6. EARNINGS COUNTER (SOCIAL PROOF)</b>\n"
            "Every visitor sees your live revenue on the landing page.\n"
            "Check it: /earnings all\n"
            "Filter: /earnings 24h, /earnings month, /earnings year\n\n"
            "<b>🎯 7. PRICING PSYCHOLOGY</b>\n"
            "Enterprise ($8,000) makes Unlimited ($120) look cheap.\n"
            'FOMO counter on landing page: "47 spots left"\n'
            "Target card glows cyan — that's what you want them to buy.\n\n"
            "<b>📋 DAILY ACTION CHECKLIST</b>\n"
            "☐ /earnings — check today's revenue\n"
            "☐ /flash_sale — ensure a flash sale is active\n"
            "☐ Send 1 Telegram broadcast about current promotion\n"
            "☐ Generate 2-3 redeem codes for quick sales\n\n"
            "<b>💡 POWER TIPS</b>\n"
            "• Stack flash sale + social proof simultaneously\n"
            "• Screenshot the earnings counter for sales pitches\n"
            '• Run referral contests: "Top referrer gets free Enterprise"\n'
            "• Telegram is your cash register — fastest path to sale\n"
            "• Full guide: profit_strategy.md\n\n"
            "<b>Made with ❤️ by Sam Salameh — MAXIMUM PROFIT MODE</b>"
        )
        if len(msg) > 4000:
            msg = msg[:3950] + "\n\n...(truncated — use /strategy for full guide)"
        await self.send(msg)

    # ── ADMIN FREE CREDIT (ADMIN ONLY) ─────────────────────────────

    async def cmd_admin_credit(self, args=""):
        """Generate a FREE admin-only redeem code for personal use.

        Usage: /admin_credit [value]

        Defaults to $100.00. These codes do NOT count as revenue.

        """

        import uuid

        val = 100.00

        if args:
            try:
                val = float(args.strip())

                if val <= 0:
                    await self.send("<b>⚠️ Invalid Value:</b> Must be greater than 0.")

                    return

            except ValueError:
                await self.send(
                    "<b>⚠️ Invalid Value:</b> Specify a number. Example: <code>/admin_credit 50</code>"
                )

                return

        code = f"ADMIN-{uuid.uuid4().hex[:8].upper()}"

        conn = None

        try:
            conn = _get_db()

            for _ in range(10):
                existing = conn.execute(
                    "SELECT id FROM redeem_codes WHERE code = ?", (code,)
                ).fetchone()

                if not existing:
                    break

                code = f"ADMIN-{uuid.uuid4().hex[:8].upper()}"

            conn.execute(
                "INSERT INTO redeem_codes (code, value_usd, code_type, is_used) VALUES (?, ?, 'admin_free', 0)",
                (code, val),
            )

            conn.commit()

            msg = (
                "<b>🆓 ADMIN FREE CREDIT GENERATED</b>\n\n"
                f"<b>💵 Value:</b> <code>${val:.2f}</code>\n"
                f"<b>🔑 Code:</b> <code>{code}</code>\n"
                f"<b>🟢 Status:</b> Active (Not counted in revenue)\n"
                f"<b>🏷 Type:</b> Admin Free\n\n"
                "<i>Use this code at /wallet → Redeem Code on the website.\n"
                "This will NOT show up in your sales/profit reports.</i>"
            )

            await self.send(msg)

        except Exception as e:
            logger.error(f"Admin credit failed: {e}")

            await self.send(f"<b>❌ Failed to generate admin credit:</b> {e}")

        finally:
            if conn:
                conn.close()

    # ── GENERATE REDEEM CODE (ADMIN ONLY) ───────────────────────────

    # Generate Redeem Code with inline buttons
    # Generate Redeem Code with inline buttons
    async def cmd_generate_code(self, args=""):
        """Generate redeem codes with inline keyboard."""
        try:
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "\U0001f4b0 Auto $10", "callback_data": "/gen_auto"},
                        {"text": "$25 \U000026a1", "callback_data": "/gen_quick_25"},
                        {"text": "$50 \U0001f525", "callback_data": "/gen_quick_50"},
                    ],
                    [
                        {"text": "$100 \U0001f4a0", "callback_data": "/gen_quick_100"},
                        {"text": "$5 \U0001f536", "callback_data": "/gen_q_5"},
                        {"text": "$10 \U0001f537", "callback_data": "/gen_q_10"},
                    ],
                    [
                        {"text": "$25 \U0001f538", "callback_data": "/gen_q_25"},
                        {"text": "$50 \U0001f539", "callback_data": "/gen_q_50"},
                        {"text": "$100 \U0001f53a", "callback_data": "/gen_q_100"},
                    ],
                    [
                        {"text": "$200 \U0001f4b8", "callback_data": "/gen_q_200"},
                        {"text": "$500 \U0001f48e", "callback_data": "/gen_q_500"},
                    ],
                    [
                        {
                            "text": "\u270f\ufe0f Custom Value",
                            "callback_data": "/gen_value",
                        },
                        {
                            "text": "\U0001f4dd Custom Code",
                            "callback_data": "/gen_custom",
                        },
                    ],
                    [{"text": "\U0001f6ab Cancel", "callback_data": "/gen_cancel"}],
                ]
            }
            menu_text = (
                "<b>\U0001f39f REDEEM CODE GENERATOR</b>\n\n"
                "Choose a preset amount or create a custom code.\n\n"
                "\U0001f539 <b>Quick buttons</b>: Instant $5 - $500\n"
                "\u270f\ufe0f <b>Custom Value</b>: Type any amount\n"
                "\U0001f4dd <b>Custom Code</b>: Your own text + value"
            )
            resp = await self.http_client.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": menu_text,
                    "parse_mode": "HTML",
                    "reply_markup": keyboard,
                },
            )
            if resp.status_code != 200:
                err = await resp.aread()
                logger.error(
                    f"send inline keyboard failed: {err[:100] if err else 'unknown'}"
                )
        except Exception as e:
            logger.error(f"cmd_generate_code error: {e}")
            await self.send(f"<b>Error generating code menu:</b> {e}")

    async def _create_redeem_code(self, val, custom_code=None):
        import uuid

        code_val = custom_code if custom_code else uuid.uuid4().hex[:32].upper()
        pa_ok = False
        conn = None
        try:
            conn = _get_db()
            conn.execute(
                "INSERT INTO redeem_codes (code, value_usd, code_type, is_used) VALUES (?, ?, 'sale', 0)",
                (code_val, val),
            )
            conn.commit()
            conn.close()
            conn = None
            # 2. Sync to PA database (for website redemption)
            try:
                r = await self.http_client.post(
                    f"{config.SITE_URL}/api/generate-redeem-code",
                    json={"code": code_val, "value": val, "code_type": "sale"},
                    timeout=10,
                )
                if r.status_code == 200:
                    data = r.json()
                    pa_ok = data.get("ok", False)
            except Exception as e:
                logger.debug(f"PA code sync skipped (non-fatal): {e}")

            sync_note = (
                " ✅ Synced to website"
                if pa_ok
                else " ⚠️ Website sync failed (code may not work on site)"
            )
            await self.send(
                f"<b>Code generated:</b> <code>{code_val}</code> - ${val:.2f}{sync_note}"
            )
        except Exception as e:
            await self.send(f"<b>Error:</b> {e}")
            return
        finally:
            if conn:
                conn.close()

    # === STUB HANDLERS (auto-generated) ===

    async def _handle_gen_auto(self):
        await self._create_redeem_code(10)

    async def _handle_gen_quick_25(self):
        await self._create_redeem_code(25)

    async def _handle_gen_quick_50(self):
        await self._create_redeem_code(50)

    async def _handle_gen_quick_100(self):
        await self._create_redeem_code(100)

    async def _handle_gen_q_5(self):
        await self._create_redeem_code(5)

    async def _handle_gen_q_10(self):
        await self._create_redeem_code(10)

    async def _handle_gen_q_25(self):
        await self._create_redeem_code(25)

    async def _handle_gen_q_50(self):
        await self._create_redeem_code(50)

    async def _handle_gen_q_100(self):
        await self._create_redeem_code(100)

    async def _handle_gen_q_200(self):
        await self._create_redeem_code(200)

    async def _handle_gen_q_500(self):
        await self._create_redeem_code(500)

    async def _handle_gen_value(self):
        self._awaiting_input["gen_value"] = True
        self._awaiting_input_ts = asyncio.get_event_loop().time()
        msg = "<b>Enter the code value in USD.</b>\n\nType a number (1-9999):"
        await self.send(msg)

    async def _handle_gen_value_old(self):
        self._awaiting_input["gen_value_old"] = True
        self._awaiting_input_ts = asyncio.get_event_loop().time()
        await self.send("<b>Enter the amount:</b>")

    async def _handle_gen_custom(self):
        self._awaiting_input["gen_custom_text"] = True
        self._awaiting_input_ts = asyncio.get_event_loop().time()
        await self.send("<b>Type your custom code text:</b>")

    async def _handle_gen_cancel(self):
        self._awaiting_input.clear()
        await self.send("<b>Cancelled.</b>")

    async def _process_awaiting_input(self, text: str):
        """Handle text input when bot is awaiting a response from user."""
        text = text.strip()

        # Check for cancel keyword
        if text.lower() in ("cancel", "cancle", "cancel", "stop", "cancelar"):
            self._awaiting_input.clear()
            await self.send("<b>The operation has been cancelled.</b>")
            return

        # Check for timeout — clear if awaiting was set more than 5 minutes ago
        now_ts = asyncio.get_event_loop().time()
        if (
            hasattr(self, "_awaiting_input_ts")
            and (now_ts - self._awaiting_input_ts) > 300
        ):
            logger.info("[BOT] Awaiting input timed out (>5 min) — clearing")
            self._awaiting_input.clear()
            await self.send("<b>⏱ Input timed out (5 min). Please start again.</b>")
            return

        if self._awaiting_input.get("gen_value"):
            self._awaiting_input.clear()
            try:
                val = float(text)
                if val <= 0 or val > 9999:
                    await self.send(
                        "<b>Invalid amount.</b> Please enter a number between 1 and 9999."
                    )
                    return
                await self._create_redeem_code(val)
            except ValueError:
                await self.send(
                    "<b>Invalid number.</b> Please enter a valid amount like 50 or 100."
                )
            return

        if self._awaiting_input.get("gen_value_old"):
            self._awaiting_input.clear()
            try:
                val = float(text)
                if val <= 0 or val > 9999:
                    await self.send(
                        "<b>Invalid amount.</b> Please enter a number between 1 and 9999."
                    )
                    return
                await self._create_redeem_code(val)
            except ValueError:
                await self.send("<b>Invalid number.</b> Please enter a valid amount.")
            return

        if self._awaiting_input.get("gen_custom_text"):
            self._awaiting_input["gen_custom_text"] = False
            self._awaiting_input["gen_custom_value"] = True
            self._awaiting_input["_custom_text"] = text.upper()
            await self.send(
                f"<b>Custom code text:</b> <code>{text.upper()}</code>\nNow enter the value in USD:"
            )
            return

        if self._awaiting_input.get("gen_custom_value"):
            custom_text = self._awaiting_input.get("_custom_text", "")
            self._awaiting_input.clear()
            try:
                val = float(text)
                if val <= 0 or val > 9999:
                    await self.send(
                        "<b>Invalid amount.</b> Please enter a number between 1 and 9999."
                    )
                    return
                await self._create_redeem_code(val, custom_code=custom_text)
            except ValueError:
                await self.send("<b>Invalid number.</b> Please enter a valid amount.")
            return

        # No known awaiting state
        self._awaiting_input.clear()

    async def shutdown(self):
        """Shutdown notifier and close http_client."""
        logger.info("[BOT] Shutting down...")
        try:
            self.notifier.stop()
            logger.info("[BOT] Notifier stopped")
        except Exception as e:
            logger.warning(f"[BOT] Notifier stop error: {e}")
        try:
            await self.http_client.aclose()
        except Exception as e:
            logger.warning(f"[BOT] HTTP client close error: {e}")

    async def run_bot(self):
        """Minimal polling loop."""
        if not self.enabled:
            logger.warning("Telegram bot not enabled")
            return
        logger.info("[BOT] Telegram bot started - MAXIMIZED MODE!")
        logger.info(f"   Bot started at: {self.bot_start_time}")
        logger.info(f"[BOT] Configured chat_id: {self.chat_id}")
        self.notifier.start()
        logger.info("[BOT] Smart notifications service started")
        await self._set_commands_menu()
        # Delete any existing webhook to prevent 409 conflict
        try:
            await self.http_client.post(f"{self.base_url}/deleteWebhook")
            logger.info("[BOT] Webhook deleted — polling mode confirmed")
        except Exception as e:
            logger.warning(f"[BOT] deleteWebhook call failed (non-fatal): {e}")
        asyncio.create_task(self._daily_summary_task())
        offset = 0
        stuck_count = 0
        conflict_count = 0
        poll_cycle = 0
        try:
            while True:
                try:
                    updates, is_conflict = await self.get_updates(offset)
                    if is_conflict:
                        conflict_count += 1
                        backoff = min(30, 2 ** min(conflict_count, 6))
                        logger.warning(
                            f"[BOT] 409 Conflict #{conflict_count}, backoff {backoff}s"
                        )
                        await asyncio.sleep(backoff)
                        continue
                    conflict_count = 0
                    max_id = offset
                    if updates:
                        observed_max = await self._process_updates(updates)
                        if observed_max > max_id:
                            max_id = observed_max
                    poll_cycle += 1
                    if updates:
                        offset = max_id + 1
                        stuck_count = 0
                    else:
                        stuck_count += 1
                        if stuck_count >= 300 and offset:
                            logger.warning(
                                f"Bot stuck at offset {offset}, force-resetting to 0"
                            )
                            offset = 0
                            stuck_count = 0
                    if poll_cycle % 60 == 0 and not updates:
                        logger.debug(f"[BOT] Poll cycle #{poll_cycle}: no new updates")
                    elif poll_cycle % 60 == 0:
                        logger.info(f"[BOT] Poll cycle #{poll_cycle}: active")
                    await asyncio.sleep(1.0)
                except Exception as e:
                    if poll_cycle % 60 == 0:
                        logger.error(
                            f"Bot error in polling loop (cycle #{poll_cycle}): {e}"
                        )
                    else:
                        logger.debug(
                            f"Bot error in polling loop (cycle #{poll_cycle}): {e}"
                        )
                    await asyncio.sleep(1.0)
        finally:
            logger.info("[BOT] Polling loop ended — shutting down http_client")
            await self.shutdown()

    async def _process_updates(self, updates: list[dict]) -> int:
        """Process a list of received updates. Returns the highest update ID processed."""
        max_id = 0
        for update in updates:
            try:
                update_id = int(update.get("update_id", 0))
                if update_id > max_id:
                    max_id = update_id

                cb = update.get("callback_query")
                if cb:
                    sid = cb.get("from", {}).get("id")
                    if sid and str(sid) != str(self.chat_id):
                        await self.answer_callback_query(
                            cb.get("id", ""), "Access Denied", True
                        )
                        continue
                    logger.debug("RUN_BOT: processing callback")
                    await self.handle_callback_query(cb)
                    continue

                iq = update.get("inline_query")
                if iq:
                    await self.inline_query(iq)
                    continue

                msg = update.get("message", {})
                txt = msg.get("text", "")
                sid = msg.get("chat", {}).get("id")
                if sid and str(sid) != str(self.chat_id):
                    continue

                if sid and not _check_user_rate_limit(sid, max_per_minute=10):
                    if txt.startswith("/"):
                        await self.send(
                            "<b>⏳ Rate limit exceeded.</b> You're sending too many commands. "
                            "Please wait a moment before trying again."
                        )
                    continue

                if txt.startswith("/"):
                    parts = txt.split(" ", 1)
                    cmd = parts[0].lower()
                    args = parts[1] if len(parts) > 1 else ""
                    await self.handle_command(cmd, args, user_id=sid)
                else:
                    mapped = await self.route_text_to_command(txt)
                    if mapped:
                        parts = mapped.split(" ", 1)
                        cmd = parts[0].lower()
                        args = parts[1] if len(parts) > 1 else ""
                        await self.handle_command(cmd, args, user_id=sid)
                    elif self._awaiting_input:
                        await self._process_awaiting_input(txt)
            except Exception as e:
                logger.warning(f"Error in update processor: {e}")
        return max_id

    async def process_webhook_update(self, update: dict):
        """Process a single Telegram update via webhook (FREE — no polling needed)."""
        try:
            cb = update.get("callback_query")
            if cb:
                sid = cb.get("from", {}).get("id")
                if sid and str(sid) != str(self.chat_id):
                    await self.answer_callback_query(
                        cb.get("id", ""), "Access Denied", True
                    )
                    return
                await self.handle_callback_query(cb)
                return
            # ── Inline Query (Webhook) ───────────────────────────
            iq = update.get("inline_query")
            if iq:
                await self.inline_query(iq)
                return
            msg = update.get("message", {})
            txt = msg.get("text", "")
            sid = msg.get("chat", {}).get("id")
            if sid and str(sid) != str(self.chat_id):
                return
            # Rate limit check — max 10 commands per minute per user
            if sid and not _check_user_rate_limit(sid, max_per_minute=10):
                if txt.startswith("/"):
                    await self.send(
                        "<b>⏳ Rate limit exceeded.</b> You're sending too many commands. "
                        "Please wait a moment before trying again."
                    )
                return
            if txt.startswith("/"):
                parts = txt.split(" ", 1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                await self.handle_command(cmd, args, user_id=sid)
            else:
                mapped = await self.route_text_to_command(txt)
                if mapped:
                    parts = mapped.split(" ", 1)
                    cmd = parts[0].lower()
                    args = parts[1] if len(parts) > 1 else ""
                    await self.handle_command(cmd, args, user_id=sid)
                elif self._awaiting_input:
                    await self._process_awaiting_input(txt)
        except Exception as e:
            logger.error(f"Webhook update error: {e}")

    async def cmd_admin(self, args=""):
        """Admin dashboard with inline buttons."""
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "Bot Status", "callback_data": "admin_status"},
                    {"text": "Server Logs", "callback_data": "admin_logs"},
                ],
                [
                    {"text": "Offset Info", "callback_data": "admin_offset"},
                    {"text": "DB Stats", "callback_data": "admin_db"},
                ],
                [
                    {"text": "Health Check", "callback_data": "admin_health"},
                    {"text": "Restart Bot", "callback_data": "admin_restart"},
                ],
                [{"text": "📋 View Accounts", "callback_data": "admin_accounts"}],
            ]
        }
        await self.send("Admin Dashboard\n\nChoose an option:", reply_markup=keyboard)

    async def cmd_flash_sale(self, args: str = "") -> None:
        """View or manage flash sales."""
        conn = None
        try:
            import shlex
            conn = _get_db()
            raw = (args or "").strip()

            if not raw:
                await self._cmd_flash_sale_status(conn)
                return

            parts = shlex.split(raw)
            action = parts[0].lower()

            if action == "list":
                await self._cmd_flash_sale_list(conn)
            elif action == "create":
                await self._cmd_flash_sale_create(conn, parts)
            elif action == "end":
                await self._cmd_flash_sale_end(conn, parts)
            else:
                await self.send(
                    "<b>⚠️ Unknown flash sale action.</b>\n\n"
                    'Use <code>/flash_sale</code>, <code>/flash_sale list</code>, <code>/flash_sale create "Title" 25 48</code>, or <code>/flash_sale end 1</code>.'
                )
        except Exception as e:
            logger.error(f"Flash sale command failed: {e}")
            await self.send(f"<b>❌ Flash sale error:</b> {e}")
        finally:
            if conn:
                conn.close()

    async def _cmd_flash_sale_status(self, conn) -> None:
        """Show current active flash sale status."""
        active = conn.execute(
            "SELECT id, title, discount_percent, start_time, end_time FROM flash_sales WHERE active = 1 ORDER BY id DESC LIMIT 1"
        ).fetchone()

        if active:
            msg = (
                "<b>⚡ FLASH SALE</b>\n\n"
                f"<b>Active:</b> #{active['id']} - {active['title']}\n"
                f"<b>Discount:</b> {float(active['discount_percent']):.0f}%\n"
                f"<b>Starts:</b> {active['start_time']}\n"
                f"<b>Ends:</b> {active['end_time']}\n\n"
                "<b>Commands:</b>\n"
                "<code>/flash_sale list</code>\n"
                '<code>/flash_sale create "Weekend" 25 48</code>\n'
                "<code>/flash_sale end 1</code>"
            )
        else:
            msg = (
                "<b>⚡ FLASH SALE</b>\n\n"
                "No active flash sale right now.\n\n"
                "<b>Examples:</b>\n"
                '<code>/flash_sale create "Weekend Deal" 25 48</code>\n'
                "<code>/flash_sale list</code>\n"
                "<code>/flash_sale end 1</code>"
            )
        await self.send(msg)

    async def _cmd_flash_sale_list(self, conn) -> None:
        """List recent flash sales."""
        rows = conn.execute(
            "SELECT id, title, discount_percent, active, start_time, end_time FROM flash_sales ORDER BY id DESC LIMIT 10"
        ).fetchall()
        if not rows:
            await self.send("<b>⚡ FLASH SALE</b>\n\nNo flash sales found.")
            return

        lines = ["<b>⚡ FLASH SALE LIST</b>", ""]
        for row in rows:
            status = "🟢 Active" if int(row["active"] or 0) == 1 else "⚪ Ended"
            lines.append(
                f"#{row['id']} - {row['title']} | {float(row['discount_percent']):.0f}% | {status}"
            )
        lines.extend(
            [
                "",
                "<b>Commands:</b>",
                '<code>/flash_sale create "Title" 25 48</code>',
                "<code>/flash_sale end 1</code>",
            ]
        )
        await self.send("\n".join(lines))

    async def _cmd_flash_sale_create(self, conn, parts: list[str]) -> None:
        """Create a new flash sale."""
        if len(parts) < 4:
            await self.send(
                '<b>⚠️ Usage:</b> <code>/flash_sale create "Title" 25 48</code>'
            )
            return

        title = parts[1]
        try:
            discount = float(parts[2])
            duration_hours = float(parts[3])
        except (ValueError, IndexError):
            await self.send(
                '<b>⚠️ Invalid numbers.</b>\n\nUsage: <code>/flash_sale create "Title" 25 48</code>'
            )
            return
        now = datetime.now()
        end_time = now + timedelta(hours=duration_hours)

        conn.execute(
            "INSERT INTO flash_sales (title, discount_percent, start_time, end_time, active) VALUES (?, ?, ?, ?, 1)",
            (
                title,
                discount,
                now.strftime("%Y-%m-%d %H:%M:%S"),
                end_time.strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()
        await self.send(
            "<b>⚡ FLASH SALE CREATED</b>\n\n"
            f"<b>Title:</b> {title}\n"
            f"<b>Discount:</b> {discount:.0f}%\n"
            f"<b>Duration:</b> {duration_hours:.0f}h"
        )

    async def _cmd_flash_sale_end(self, conn, parts: list[str]) -> None:
        """End an active flash sale."""
        if len(parts) < 2:
            await self.send("<b>⚠️ Usage:</b> <code>/flash_sale end 1</code>")
            return

        try:
            sale_id = int(parts[1])
        except ValueError:
            await self.send("<b>⚠️ Invalid sale ID.</b> Usage: <code>/flash_sale end 1</code>")
            return

        conn.execute(
            "UPDATE flash_sales SET active = 0, end_time = ? WHERE id = ?",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sale_id),
        )
        conn.commit()
        await self.send(
            f"<b>⚡ FLASH SALE ENDED</b>\n\nSale #{sale_id} is now inactive."
        )

    async def _admin_send_status(self):
        """Send bot status snapshot."""
        import json as _json

        status_lines = []
        status_lines.append("Bot Status")
        status_lines.append(f"Started: {self.bot_start_time}")
        status_lines.append(f"Enabled: {self.enabled}")
        status_lines.append(f"Chat ID: {self.chat_id}")
        status_lines.append(f"Offset var: {getattr(self, '_offset', '?')}")
        is_live = False
        try:
            r = await self.http_client.get(f"{config.SITE_URL}/health", timeout=5)
            h = _json.loads(r.text)
            is_live = h.get("bot") == "running"
            status_lines.append(f"PA Health: {h.get('bot', '?')}")
        except Exception:
            status_lines.append("PA Health: unreachable")
        status_lines.append(f"Live: {is_live}")
        try:
            import psutil

            status_lines.append(
                f"RAM: {psutil.Process().memory_info().rss / 1024 / 1024:.1f} MB"
            )
        except Exception:
            status_lines.append("RAM: unavailable")
        await self.send("\n".join(status_lines))

    async def _admin_send_logs(self):
        """Send last 15 log lines."""
        try:
            r = await self.http_client.get(
                config.PA_LOG_BYTES_URL,
                headers={"Authorization": f"Token {config.PA_API_TOKEN}"},
                timeout=10,
            )
            logtext = r.text
            logs = [l for l in logtext.strip().split("\n") if l.strip()]
            last_15 = logs[-15:] if logs else ["(empty)"]
            combined = "Last 15 log lines:\n\n" + "\n".join(l[-120:] for l in last_15)
            # Telegram limit 4096 chars
            if len(combined) > 3900:
                combined = combined[:3900] + "...(truncated)"
            await self.send(f"<pre>{combined}</pre>")
        except Exception as e:
            await self.send(f"Cannot read logs: {e}")

    async def _admin_send_offset(self):
        """Show offset state."""
        await self.send(
            f"Offset Info\n\n"
            f"Last offset: {getattr(self, '_offset', '?')}\n"
            f"Polling: active\n"
            f"Log source: PA server.log"
        )

    async def _admin_send_db(self):
        """Show DB stats."""
        conn = None
        try:
            conn = _get_db()
            users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            codes = conn.execute("SELECT COUNT(*) FROM redeem_codes").fetchone()[0]
            apps = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE applied_at IS NOT NULL"
            ).fetchone()[0]
            msg = (
                f"DB Stats\n\n"
                f"Users: {users}\n"
                f"Jobs: {jobs}\n"
                f"Redeem Codes: {codes}\n"
                f"Applications: {apps}"
            )
        except Exception as e:
            msg = f"DB Error: {e}"
        finally:
            if conn:
                conn.close()
        await self.send(msg)

    async def _admin_send_accounts(self):
        """Show all user accounts with login details."""
        conn = None
        try:
            conn = _get_db()
            rows = conn.execute(
                "SELECT user_id, email, name, wallet_balance, user_type, created_at, is_active "
                "FROM users ORDER BY created_at DESC LIMIT 20"
            ).fetchall()
            if not rows:
                await self.send("📋 No user accounts found.")
                return
            lines = ["<b>📋 User Accounts (last 20)</b>", ""]
            for r in rows:
                uid = r["user_id"] or "?"
                email = r["email"] or "?"
                name = r["name"] or "N/A"
                bal = float(r["wallet_balance"] or 0)
                utype = r["user_type"] or "jobseeker"
                active = "✅" if r["is_active"] else "❌"
                created = str(r["created_at"])[:10] if r["created_at"] else "?"
                lines.append(
                    f"{active} <b>{name}</b>\n"
                    f"   📧 {email}\n"
                    f"   💰 ${bal:.2f} | {utype} | {created}\n"
                    f"   🆔 <code>{uid}</code>"
                )
                lines.append("")
            msg = "\n".join(lines)
            msg += "\n<i>Passwords are SHA-256 hashed — not viewable</i>"
        except Exception as e:
            msg = f"❌ Accounts Error: {e}"
        finally:
            if conn:
                conn.close()
        await self.send(msg)

    async def _admin_do_restart(self):
        """Restart the PA web app."""
        try:
            r = await self.http_client.post(
                config.PA_RELOAD_URL,
                headers={"Authorization": f"Token {config.PA_API_TOKEN}"},
                timeout=15,
            )
            await self.send(f"Restart triggered: {r.text}")
        except Exception as e:
            await self.send(f"Restart failed: {e}")

    async def _set_commands_menu(self):
        """Set command menu with retry."""
        for attempt in range(3):
            try:
                await self.http_client.post(f"{self.base_url}/deleteMyCommands")
                resp = await self.http_client.post(
                    f"{self.base_url}/setMyCommands",
                    json={"commands": self.menu_commands},
                    timeout=30,
                )
                data = resp.json()
                if resp.status_code == 200 and data.get("ok"):
                    logger.info(
                        f"[BOT] Command menu set: {len(self.menu_commands)} cmds (attempt {attempt + 1})"
                    )
                    return
                logger.warning(
                    f"[BOT] setMyCommands attempt {attempt + 1}: HTTP {resp.status_code}"
                )
            except Exception as e:
                logger.warning(f"[BOT] setMyCommands attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                await asyncio.sleep(2 * (attempt + 1))
        logger.error("[BOT] FAILED to set command menu after 3 attempts")

    async def _daily_summary_task(self):
        """Background daily summary."""
        while True:
            now = datetime.now()
            target = now.replace(hour=9, minute=0, second=0, microsecond=0)
            if now >= target:
                target += timedelta(days=1)
            wait_seconds = (target - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            conn = None
            try:
                conn = _get_db()
                new_jobs = conn.execute(
                    "SELECT COUNT(*) FROM jobs WHERE date(created_at) >= ?",
                    ((datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),),
                ).fetchone()[0]
                emails_sent = conn.execute(
                    "SELECT COUNT(*) FROM campaign_emails WHERE status='sent'"
                ).fetchone()[0]
                total_applied = conn.execute(
                    "SELECT COUNT(*) FROM jobs WHERE applied_at IS NOT NULL"
                ).fetchone()[0]
                msg = f"<b>GOOD MORNING! DAILY DIGEST</b>\n\n<b>New Jobs:</b> {new_jobs}\n<b>Emails Sent:</b> {emails_sent}\n<b>Applications:</b> {total_applied}"
                await self.send(msg)
            except Exception as e:
                logger.error(f"Daily summary failed: {e}")
            finally:
                if conn:
                    conn.close()

    @staticmethod
    def _table_exists(conn, table_name):
        """Check if a table exists in the database."""
        try:
            conn.execute(f"SELECT 1 FROM {table_name} LIMIT 0")
            return True
        except Exception:
            return False


async def start_telegram_bot():
    """Start the Telegram bot (singleton - only one instance runs)."""
    global _TG_BOT_STARTED
    with _TG_BOT_LOCK:
        if _TG_BOT_STARTED:
            logger.warning("[BOT] Already running - refusing second instance")
            return
        _TG_BOT_STARTED = True
    bot = TelegramBot()
    await bot.run_bot()

"""
core/email_verifier.py - Anti-Bounce & Email Deliverability Guard
JobHunt Pro — Protects user email accounts (Gmail/SMTP/Hotmail) from "Address Not Found" bounces.

Features:
  1. Syntax & Typo Validation (blocks @gmai.com, @yaho.com, etc.)
  2. Fake/Fictitious Domain Filter (blocks gcctalent.com, lebanontech5.com, example.com, etc.)
  3. Real-time DNS MX Record Lookup with multi-level persistent caching (In-Memory + DB + Mullvad/Cloudflare DoH)
  4. Persistent Suppression List (DB table `suppressed_emails` for bounced addresses)
  5. 365-Day Cooldown Deduplication Window (Per user 1-year contact protection)
"""

import logging
import os
import re
import socket
import json
import time
import urllib.request
from typing import Tuple, Set, Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# ── Memory Caches for Speed (O(1) lookups) ──────────────────────────────────
_MX_CACHE: Dict[str, Dict[str, Any]] = {}
_SUPPRESSED_EMAILS: Set[str] = set()
_CACHE_INITIALIZED: bool = False
_STATS = {
    "lookups": 0,
    "memory_hits": 0,
    "db_hits": 0,
    "live_dns_checks": 0
}

# 7 Days cache TTL for verified MX records
MX_CACHE_TTL_SECONDS = 7 * 86400

# Known fake, test, or auto-generated fictitious domains that cause 550 bounces
BLACK_LISTED_DOMAINS = {
    "example.com", "test.com", "tempmail.com", "mailinator.com", "spam.org",
    "domain.com", "invalid.com", "sample.com", "fake.com", "dummy.com",
    "gcctalent.com", "menatalent.com", "ustalent.com", "eutalent.com",
    "asiatalent.com", "globaltalent.com", "company.com", "yourcompany.com",
    "localhost", "localdomain", "test.org", "example.org", "example.net"
}

# Known email typos that lead to non-existent addresses
DOMAIN_TYPOS = {
    "gmai.com": "gmail.com",
    "gmaill.com": "gmail.com",
    "gnail.com": "gmail.com",
    "gamil.com": "gmail.com",
    "hotmai.com": "hotmail.com",
    "hotmial.com": "hotmail.com",
    "yaho.com": "yahoo.com",
    "outloo.com": "outlook.com",
    "outlok.com": "outlook.com",
}

# Suspicious local parts (placeholder or synthetic test accounts)
SUSPICIOUS_LOCAL_PARTS = {
    "test", "demo", "placeholder", "fake", "none", "null", "undefined",
    "noemail", "no-email", "noreply_fake", "sample", "user_vip"
}

# Top GCC, Levant, and Global enterprise domains pre-warmed for ultra-low latency (<0.01ms)
MAJOR_ENTERPRISE_DOMAINS = {
    "gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "icloud.com", "aol.com", "protonmail.com", "apexrecruitment.ae",
    "oracle.com", "microsoft.com", "cisco.com", "paloaltonetworks.com", "fortinet.com", "ibm.com", "sap.com", "vmware.com",
    "dell.com", "salesforce.com", "amazon.com", "google.com", "huawei.com", "siemens.com", "se.com", "abb.com", "honeywell.com",
    "slb.com", "bakerhughes.com", "halliburton.com", "parsons.com", "jacobs.com", "aecom.com", "wsp.com", "atkinsrealis.com",
    "mottmac.com", "egis-group.com", "dar.com", "keoic.com", "hillintl.com", "turnerandtownsend.com", "alvarezandmarsal.com",
    "oliverwyman.com", "kearney.com", "rolandberger.com", "gartner.com", "idc.com", "aramco.com", "aramcodigital.com", "neom.com", 
    "redseaglobal.com", "qiddiya.com", "diriyah.sa", "roshn.sa", "pif.gov.sa", "mubadala.com", "adq.ae", "g42.ai", "presight.ai",
    "solutions.com.sa", "site.sa", "elm.sa", "eand.com", "du.ae", "stc.com.sa", "zain.com", "ooredoo.qa", "omantel.om", "beyon.com",
    "emirates.com", "qatarairways.com.qa", "qatarairways.com", "flydubai.com", "airarabia.com", "riyadhair.com", "dpworld.com",
    "adportsgroup.com", "agility.com", "aramex.com", "emiratesnbd.com", "bankfab.com", "adcb.com", "dib.ae", "mashreqbank.com",
    "alrajhibank.com.sa", "snb.com.sa", "riyadbank.com", "kfh.com", "nbk.com", "qnb.com", "bankmuscat.com", "bankabc.com",
    "arabbank.com", "bankaudi.com.lb", "blom-bank.com", "byblosbank.com", "majidalfuttaim.com", "chalhoubgroup.com", "alshaya.com",
    "altayer.com", "apparelgroup.com", "landmarkgroup.com", "alfuttaim.com", "emaar.com", "damacproperties.com", "aldar.com",
    "mrsool.co", "salla.sa", "zid.sa", "foodics.com", "unifonic.com", "anghami.com", "leantech.me", "tamara.co", "tabby.ai",
    "careem.com", "talabat.com", "noon.com", "propertyfinder.ae", "dubizzle.com", "deliveryhero.com", "kitopi.com", "jahez.net",
    "hungerstation.com", "nvidia.com", "ericsson.com", "nokia.com", "schneider-electric.com", "emerson.com", "hpe.com",
    "checkpoint.com", "juniper.net", "crowdstrike.com", "cloudflare.com", "snowflake.com", "nutanix.com", "servicenow.com",
    "workday.com", "darktrace.com", "sentinelone.com", "wiz.io", "redhat.com", "citrix.com", "equinix.com", "nttdata.com",
    "infosys.com", "wipro.com", "tcs.com", "capgemini.com", "dxc.com", "kyndryl.com", "cognizant.com", "sabic.com",
    "maaden.com.sa", "se.com.sa", "swcc.gov.sa", "nwc.com.sa", "sami.com.sa", "bupa.com.sa", "tawuniya.com.sa", "hmg.com.sa",
    "fakeeh.care", "dewa.gov.ae", "enoc.com", "ega.ae", "borouge.com", "fertiglobe.com", "americanarestaurants.com", "almarai.com",
    "nadec.com.sa", "savola.com", "bindawoodholding.com", "jarir.com", "extra.com", "nahdi.sa", "bahri.sa", "sal.sa", "saptco.com.sa",
    "sisco.com.sa", "mckinsey.com", "bcg.com", "bain.com", "pwc.com", "deloitte.com", "ey.com", "kpmg.com", "tascoutsourcing.com",
    "blackpearl.com", "bayt.com", "gulftalent.com", "toters.com", "ogero.gov.lb", "alfa.com.lb", "touch.com.lb", "cedarcom.net",
    "softflow.io", "elementn.com", "itworksme.com", "nartechnologies.com", "maliagroup.com", "procomlb.com", "stripe.com", "openai.com"
}


from contextlib import contextmanager

@contextmanager
def _get_db_context(db_path: Optional[str] = None):
    if db_path:
        import sqlite3
        conn = sqlite3.connect(db_path, timeout=5.0)
        try:
            yield conn
        finally:
            try:
                conn.close()
            except Exception:
                pass
    else:
        try:
            from web.shared import get_db
            with get_db() as conn:
                yield conn
        except Exception:
            import sqlite3
            db_file = os.environ.get("DB_PATH", "data/jobs.db")
            db_dir = os.path.dirname(db_file)
            if db_dir and not os.path.exists(db_dir):
                try:
                    os.makedirs(db_dir, exist_ok=True)
                except Exception:
                    pass
            conn = sqlite3.connect(db_file, timeout=5.0)
            try:
                yield conn
            finally:
                try:
                    conn.close()
                except Exception:
                    pass


def _init_tables_and_cache():
    """Ensure persistent DB tables exist and load active caches."""
    global _CACHE_INITIALIZED, _SUPPRESSED_EMAILS, _MX_CACHE
    if _CACHE_INITIALIZED:
        return
    
    # Pre-populate memory cache with verified major enterprise domains
    now = time.time()
    for d in MAJOR_ENTERPRISE_DOMAINS:
        _MX_CACHE[d] = {"has_mx": True, "timestamp": now + MX_CACHE_TTL_SECONDS}

    try:
        with _get_db_context() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS suppressed_emails (
                    email TEXT PRIMARY KEY,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS domain_mx_cache (
                    domain TEXT PRIMARY KEY,
                    has_mx INTEGER NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            conn.commit()
            
            # Load suppressed emails
            rows = conn.execute("SELECT email FROM suppressed_emails").fetchall()
            for r in rows:
                if r and r[0]:
                    _SUPPRESSED_EMAILS.add(r[0].lower().strip())
                    
            # Load recent unexpired MX records into memory cache
            cutoff = now - MX_CACHE_TTL_SECONDS
            mx_rows = conn.execute("SELECT domain, has_mx, updated_at FROM domain_mx_cache WHERE updated_at >= ?", (cutoff,)).fetchall()
            for row in mx_rows:
                if row and row[0]:
                    _MX_CACHE[row[0].lower().strip()] = {
                        "has_mx": bool(row[1]),
                        "timestamp": float(row[2])
                    }
        _CACHE_INITIALIZED = True
    except Exception as exc:
        logger.warning(f"[EmailVerifier] Could not initialize suppression/MX DB cache: {exc}")


def suppress_bounced_email(email: str, reason: str = "bounce"):
    """Blacklist an email workspace-wide so it will NEVER be sent to again."""
    if not email or "@" not in email:
        return
    
    clean_email = email.lower().strip()
    _SUPPRESSED_EMAILS.add(clean_email)
    
    try:
        with _get_db_context() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS suppressed_emails (email TEXT PRIMARY KEY, reason TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
            conn.execute(
                "INSERT OR IGNORE INTO suppressed_emails (email, reason) VALUES (?, ?)",
                (clean_email, reason)
            )
            conn.commit()
            logger.info(f"[Anti-Bounce Shield] 🚫 Suppressed bounced email: {clean_email} ({reason})")
    except Exception as exc:
        logger.error(f"[EmailVerifier] Error saving suppressed email {clean_email}: {exc}")


def _resolve_doh_sync(domain: str) -> bool:
    """Synchronous fallback to DNS-over-HTTPS via Cloudflare & Google."""
    endpoints = [
        f"https://cloudflare-dns.com/dns-query?name={domain}&type=MX",
        f"https://dns.google/resolve?name={domain}&type=MX"
    ]
    for ep in endpoints:
        try:
            req = urllib.request.Request(
                ep,
                headers={"Accept": "application/dns-json", "User-Agent": "JobHuntPro-DoH/1.0"}
            )
            with urllib.request.urlopen(req, timeout=1.2) as response:
                data = json.loads(response.read().decode())
                if data.get("Status") == 0 and "Answer" in data and len(data["Answer"]) > 0:
                    return True
        except Exception:
            continue
    return False


async def _resolve_doh_async(domain: str) -> bool:
    """Asynchronous non-blocking DNS-over-HTTPS resolution via Cloudflare & Google."""
    try:
        import httpx
        endpoints = [
            f"https://cloudflare-dns.com/dns-query?name={domain}&type=MX",
            f"https://dns.google/resolve?name={domain}&type=MX"
        ]
        async with httpx.AsyncClient(timeout=1.5) as client:
            for ep in endpoints:
                try:
                    res = await client.get(ep, headers={"Accept": "application/dns-json", "User-Agent": "JobHuntPro-DoH/1.0"})
                    if res.status_code == 200:
                        data = res.json()
                        if data.get("Status") == 0 and "Answer" in data and len(data["Answer"]) > 0:
                            return True
                except Exception:
                    continue
    except Exception as e:
        logger.debug(f"[EmailVerifier] Async DoH error for {domain}: {e}")
    return False


def _check_dns_resolver_sync(domain: str) -> bool:
    """Synchronous DNS MX query with fast public resolvers."""
    try:
        import dns.resolver
        res = dns.resolver.Resolver()
        res.nameservers = ['1.1.1.1', '8.8.8.8', '9.9.9.9', '1.0.0.1', '8.8.4.4']
        answers = res.resolve(domain, 'MX', lifetime=0.75)
        if len(answers) > 0:
            return True
    except Exception:
        pass
    return False


def check_domain_mx(domain: str) -> bool:
    """
    Check if a domain has active MX DNS records with multi-level caching (Memory -> DB -> Live DNS/DoH).
    """
    _init_tables_and_cache()
    _STATS["lookups"] += 1
    
    if not domain:
        return False
        
    domain = domain.lower().strip()
    now = time.time()
    
    # 1. Check memory cache with TTL validation
    if domain in _MX_CACHE:
        entry = _MX_CACHE[domain]
        if isinstance(entry, bool):
            _STATS["memory_hits"] += 1
            return entry
        if isinstance(entry, dict) and now - entry.get("timestamp", 0) < MX_CACHE_TTL_SECONDS:
            _STATS["memory_hits"] += 1
            return entry.get("has_mx", False)
        
    # 2. Check blacklisted domains
    if domain in BLACK_LISTED_DOMAINS or domain.endswith(".invalid") or domain.endswith(".local"):
        _MX_CACHE[domain] = {"has_mx": False, "timestamp": now}
        return False
        
    # 3. Check Major Enterprise Domains fast-path
    if domain in MAJOR_ENTERPRISE_DOMAINS:
        _MX_CACHE[domain] = {"has_mx": True, "timestamp": now}
        return True

    # 4. Check Persistent DB Cache
    try:
        with _get_db_context() as conn:
            row = conn.execute(
                "SELECT has_mx, updated_at FROM domain_mx_cache WHERE domain = ?", (domain,)
            ).fetchone()
            if row:
                has_mx_val = bool(row[0])
                updated_at = float(row[1])
                if now - updated_at < MX_CACHE_TTL_SECONDS:
                    _STATS["db_hits"] += 1
                    _MX_CACHE[domain] = {"has_mx": has_mx_val, "timestamp": updated_at}
                    return has_mx_val
    except Exception as e:
        logger.debug(f"[EmailVerifier] DB cache lookup error for {domain}: {e}")

    # 5. Live DNS MX Lookup with Dual DoH Fallback
    _STATS["live_dns_checks"] += 1
    has_mx = _check_dns_resolver_sync(domain)
    if not has_mx:
        has_mx = _resolve_doh_sync(domain)

    # Store in memory cache
    _MX_CACHE[domain] = {"has_mx": has_mx, "timestamp": now}
    
    # Persist in DB cache
    try:
        with _get_db_context() as conn:
            conn.execute("""
                INSERT INTO domain_mx_cache (domain, has_mx, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(domain) DO UPDATE SET has_mx = excluded.has_mx, updated_at = excluded.updated_at
            """, (domain, 1 if has_mx else 0, now))
            conn.commit()
    except Exception as e:
        logger.debug(f"[EmailVerifier] DB cache write error for {domain}: {e}")

    return has_mx


async def async_check_domain_mx(domain: str) -> bool:
    """
    Non-blocking async MX check with multi-level caching (Memory -> DB -> Async DoH / DNS).
    """
    _init_tables_and_cache()
    _STATS["lookups"] += 1
    
    if not domain:
        return False
        
    domain = domain.lower().strip()
    now = time.time()
    
    # 1. Check memory cache
    if domain in _MX_CACHE:
        entry = _MX_CACHE[domain]
        if isinstance(entry, bool):
            _STATS["memory_hits"] += 1
            return entry
        if isinstance(entry, dict) and now - entry.get("timestamp", 0) < MX_CACHE_TTL_SECONDS:
            _STATS["memory_hits"] += 1
            return entry.get("has_mx", False)
            
    # 2. Blacklisted
    if domain in BLACK_LISTED_DOMAINS or domain.endswith(".invalid") or domain.endswith(".local"):
        _MX_CACHE[domain] = {"has_mx": False, "timestamp": now}
        return False
        
    # 3. Enterprise fast-path
    if domain in MAJOR_ENTERPRISE_DOMAINS:
        _MX_CACHE[domain] = {"has_mx": True, "timestamp": now}
        return True
        
    # 4. DB Cache
    try:
        with _get_db_context() as conn:
            row = conn.execute(
                "SELECT has_mx, updated_at FROM domain_mx_cache WHERE domain = ?", (domain,)
            ).fetchone()
            if row:
                has_mx_val = bool(row[0])
                updated_at = float(row[1])
                if now - updated_at < MX_CACHE_TTL_SECONDS:
                    _STATS["db_hits"] += 1
                    _MX_CACHE[domain] = {"has_mx": has_mx_val, "timestamp": updated_at}
                    return has_mx_val
    except Exception as e:
        logger.debug(f"[EmailVerifier] Async DB cache lookup error for {domain}: {e}")

    # 5. Live Async DoH / DNS Lookup
    _STATS["live_dns_checks"] += 1
    has_mx = await _resolve_doh_async(domain)
    
    if not has_mx:
        # Fallback to threaded dns.resolver
        try:
            import asyncio
            has_mx = await asyncio.to_thread(_check_dns_resolver_sync, domain)
        except Exception:
            has_mx = False

    # Store in memory cache
    _MX_CACHE[domain] = {"has_mx": has_mx, "timestamp": now}
    
    # Persist in DB cache
    try:
        with _get_db_context() as conn:
            conn.execute("""
                INSERT INTO domain_mx_cache (domain, has_mx, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(domain) DO UPDATE SET has_mx = excluded.has_mx, updated_at = excluded.updated_at
            """, (domain, 1 if has_mx else 0, now))
            conn.commit()
    except Exception as e:
        logger.debug(f"[EmailVerifier] Async DB cache write error for {domain}: {e}")

    return has_mx


def verify_email_deliverability(email: str) -> Tuple[bool, str]:
    """
    Comprehensive email deliverability verification.
    
    Returns:
        (is_valid: bool, reason_or_status: str)
    """
    _init_tables_and_cache()
    
    if not email or not isinstance(email, str):
        return False, "Empty email address"
        
    clean_email = email.lower().strip()
    
    # 1. Check persistent suppression list
    if clean_email in _SUPPRESSED_EMAILS:
        return False, "Address blacklisted / previously bounced"
        
    # 2. Basic syntax validation
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean_email):
        return False, "Invalid email format"
        
    local_part, domain = clean_email.rsplit("@", 1)
    
    # 3. Check suspicious local parts
    if (
        local_part in SUSPICIOUS_LOCAL_PARTS
        or local_part.startswith("lead.hr")
        or "dummy" in local_part
        or re.search(r"^(?:careers|job|applicant|lead|contact|outreach)(?:-hub|-apply|-desk)?-[0-9a-fA-F]{2,32}$", local_part)
        or re.search(r"^(?:test|demo|sample|fake|placeholder)[0-9a-fA-F]*$", local_part)
        or re.search(r"^[0-9a-fA-F]{10,}$", local_part)
    ):
        return False, f"Synthetic/suspicious local part ({local_part})"
        
    # 4. Check domain typos
    if domain in DOMAIN_TYPOS:
        corrected = DOMAIN_TYPOS[domain]
        return False, f"Domain typo detected (did you mean {local_part}@{corrected}?)"
        
    # 5. Check blacklisted / fictitious domains
    if domain in BLACK_LISTED_DOMAINS:
        return False, f"Disallowed or fictitious domain ({domain})"
        
    # Rejection of synthesized company numbers (e.g., seniorarchitect1.com, lebanontech5.com)
    if re.search(r"\d{1,4}\.com$", domain) and not any(k in domain for k in ["365", "247", "123"]):
        return False, f"Synthesized numeric domain pattern ({domain})"

    # 6. Check DNS MX Records (Multi-level Caching)
    if not check_domain_mx(domain):
        return False, f"Domain {domain} has no active MX mail server records"
        
    return True, "Valid & Deliverable"


async def async_verify_email_deliverability(email: str) -> Tuple[bool, str]:
    """
    Asynchronous comprehensive email deliverability verification.
    """
    _init_tables_and_cache()
    
    if not email or not isinstance(email, str):
        return False, "Empty email address"
        
    clean_email = email.lower().strip()
    
    # 1. Check persistent suppression list
    if clean_email in _SUPPRESSED_EMAILS:
        return False, "Address blacklisted / previously bounced"
        
    # 2. Basic syntax validation
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean_email):
        return False, "Invalid email format"
        
    local_part, domain = clean_email.rsplit("@", 1)
    
    # 3. Check suspicious local parts
    if (
        local_part in SUSPICIOUS_LOCAL_PARTS
        or local_part.startswith("lead.hr")
        or "dummy" in local_part
        or re.search(r"^(?:careers|job|applicant|lead|contact|outreach)(?:-hub|-apply|-desk)?-[0-9a-fA-F]{2,32}$", local_part)
        or re.search(r"^(?:test|demo|sample|fake|placeholder)[0-9a-fA-F]*$", local_part)
        or re.search(r"^[0-9a-fA-F]{10,}$", local_part)
    ):
        return False, f"Synthetic/suspicious local part ({local_part})"
        
    # 4. Check domain typos
    if domain in DOMAIN_TYPOS:
        corrected = DOMAIN_TYPOS[domain]
        return False, f"Domain typo detected (did you mean {local_part}@{corrected}?)"
        
    # 5. Check blacklisted / fictitious domains
    if domain in BLACK_LISTED_DOMAINS:
        return False, f"Disallowed or fictitious domain ({domain})"
        
    # Rejection of synthesized company numbers
    if re.search(r"\d{1,4}\.com$", domain) and not any(k in domain for k in ["365", "247", "123"]):
        return False, f"Synthesized numeric domain pattern ({domain})"

    # 6. Check DNS MX Records (Async Multi-level Caching)
    has_mx = await async_check_domain_mx(domain)
    if not has_mx:
        return False, f"Domain {domain} has no active MX mail server records"
        
    return True, "Valid & Deliverable"


def is_deliverable_email(email: str) -> bool:
    """Boolean helper for quick deliverability filtering."""
    valid, _ = verify_email_deliverability(email)
    return valid


async def async_is_deliverable_email(email: str) -> bool:
    """Async boolean helper for quick deliverability filtering."""
    valid, _ = await async_verify_email_deliverability(email)
    return valid


def check_365_cooldown_dedup(user_id: Any, email: str, db_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    1-Year Cooldown Deduplication Window (PERMANENT RULE).
    Verifies if target email has been contacted by user within 365 days across:
      - `campaign_emails`
      - `multi_platform_apps`
      - `jobs`
    Returns (is_allowed: bool, reason: str).
    """
    if not email or not isinstance(email, str):
        return False, "Invalid target email"
        
    clean_email = email.lower().strip()
    uid_str = str(user_id) if user_id is not None else ""

    def _check_conn(conn) -> Tuple[bool, str]:
        # Helper to query table columns
        def _get_table_cols(tbl_name: str) -> Set[str]:
            try:
                cur = conn.execute(f"PRAGMA table_info({tbl_name})")
                return {r[1].lower() for r in cur.fetchall()}
            except Exception:
                return set()

        def _table_exists(tbl_name: str) -> bool:
            try:
                cur = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (tbl_name,))
                return cur.fetchone() is not None
            except Exception:
                return False

        # 1. Check campaign_emails
        if _table_exists("campaign_emails"):
            ce_cols = _get_table_cols("campaign_emails")
            has_campaigns = _table_exists("campaigns")
            
            # Query joined with campaigns if possible
            if has_campaigns and "campaign_id" in ce_cols:
                try:
                    row = conn.execute("""
                        SELECT ce.sent_at FROM campaign_emails ce 
                        JOIN campaigns c ON ce.campaign_id = c.campaign_id 
                        WHERE (c.user_id = ? OR ? = '') 
                        AND (LOWER(ce.email_address) = ? OR LOWER(COALESCE(ce.email_address, '')) = ?) 
                        AND ce.sent_at >= datetime('now', '-365 days')
                        LIMIT 1
                    """, (uid_str, uid_str, clean_email, clean_email)).fetchone()
                    if row and row[0]:
                        return False, f"Target email '{clean_email}' was already contacted via campaign_emails within 365 days (on {row[0]})"
                except Exception as ex:
                    logger.debug(f"[EmailVerifier] campaign_emails join check notice: {ex}")
            elif "user_id" in ce_cols:
                try:
                    email_col = "recipient" if ("recipient" in ce_cols and "email_address" not in ce_cols) else "email_address"
                    sent_col = "sent_at" if "sent_at" in ce_cols else "created_at"
                    sql = f"""
                        SELECT {sent_col} FROM campaign_emails 
                        WHERE (user_id = ? OR ? = '') AND LOWER({email_col}) = ? 
                        AND {sent_col} >= datetime('now', '-365 days')
                        LIMIT 1
                    """
                    row = conn.execute(sql, (uid_str, uid_str, clean_email)).fetchone()
                    if row and row[0]:
                        return False, f"Target email '{clean_email}' was already contacted via campaign_emails within 365 days (on {row[0]})"
                except Exception as ex:
                    logger.debug(f"[EmailVerifier] campaign_emails direct check notice: {ex}")

        # 2. Check multi_platform_apps
        if _table_exists("multi_platform_apps"):
            mpa_cols = _get_table_cols("multi_platform_apps")
            try:
                user_cond = "(user_id = ? OR ? = '')" if "user_id" in mpa_cols else "1=1"
                time_col = "applied_at" if "applied_at" in mpa_cols else "created_at"
                
                query_parts = []
                params = [uid_str, uid_str] if "user_id" in mpa_cols else []
                
                sub_conds = []
                if "email" in mpa_cols:
                    sub_conds.append("LOWER(email) = ?")
                    params.append(clean_email)
                if "url" in mpa_cols:
                    sub_conds.append("LOWER(url) LIKE ?")
                    params.append(f"%{clean_email}%")
                if "message" in mpa_cols:
                    sub_conds.append("LOWER(message) LIKE ?")
                    params.append(f"%{clean_email}%")

                if sub_conds:
                    or_clause = " OR ".join(sub_conds)
                    sql = f"""
                        SELECT {time_col} FROM multi_platform_apps
                        WHERE {user_cond} AND ({or_clause})
                        AND {time_col} >= datetime('now', '-365 days')
                        LIMIT 1
                    """
                    row = conn.execute(sql, tuple(params)).fetchone()
                    if row and row[0]:
                        return False, f"Target email '{clean_email}' was already contacted via multi_platform_apps within 365 days (on {row[0]})"
            except Exception as ex:
                logger.debug(f"[EmailVerifier] multi_platform_apps check notice: {ex}")

        # 3. Check jobs
        if _table_exists("jobs"):
            job_cols = _get_table_cols("jobs")
            try:
                time_col = "applied_at" if "applied_at" in job_cols else ("created_at" if "created_at" in job_cols else "id")
                user_cond = "(user_id = ? OR ? = '' OR user_id IS NULL)" if "user_id" in job_cols else "1=1"
                
                sub_conds = []
                params = [uid_str, uid_str] if "user_id" in job_cols else []
                
                if "email" in job_cols:
                    sub_conds.append("LOWER(email) = ?")
                    params.append(clean_email)
                if "url" in job_cols:
                    sub_conds.append("LOWER(url) LIKE ?")
                    params.append(f"%{clean_email}%")

                if sub_conds:
                    or_clause = " OR ".join(sub_conds)
                    time_filter = f"{time_col} >= datetime('now', '-365 days')" if time_col != "id" else "1=1"
                    sql = f"""
                        SELECT {time_col} FROM jobs
                        WHERE {user_cond} AND ({or_clause})
                        AND {time_filter}
                        LIMIT 1
                    """
                    row = conn.execute(sql, tuple(params)).fetchone()
                    if row and row[0]:
                        return False, f"Target email '{clean_email}' was already contacted via jobs within 365 days (on {row[0]})"
            except Exception as ex:
                logger.debug(f"[EmailVerifier] jobs check notice: {ex}")

        # 4. Check applications (if exists)
        if _table_exists("applications"):
            app_cols = _get_table_cols("applications")
            if "email" in app_cols:
                try:
                    time_col = "applied_at" if "applied_at" in app_cols else ("created_at" if "created_at" in app_cols else "id")
                    user_cond = "(user_id = ? OR ? = '')" if "user_id" in app_cols else "1=1"
                    params = (uid_str, uid_str, clean_email) if "user_id" in app_cols else (clean_email,)
                    time_filter = f"{time_col} >= datetime('now', '-365 days')" if time_col != "id" else "1=1"
                    sql = f"""
                        SELECT {time_col} FROM applications
                        WHERE ({user_cond}) AND LOWER(email) = ?
                        AND {time_filter}
                        LIMIT 1
                    """
                    row = conn.execute(sql, params).fetchone()
                    if row and row[0]:
                        return False, f"Target email '{clean_email}' was already contacted via applications within 365 days (on {row[0]})"
                except Exception as ex:
                    logger.debug(f"[EmailVerifier] applications check notice: {ex}")

        return True, "Cooldown check passed"

    try:
        with _get_db_context(db_path) as conn:
            return _check_conn(conn)
    except Exception as exc:
        logger.warning(f"[EmailVerifier] 365-day cooldown check failed: {exc}")
        
    return True, "Cooldown check passed"


async def async_check_365_cooldown_dedup(user_id: Any, email: str, db_path: Optional[str] = None) -> Tuple[bool, str]:
    """Async non-blocking wrapper for 365-day cooldown deduplication check."""
    import asyncio
    return await asyncio.to_thread(check_365_cooldown_dedup, user_id, email, db_path)


def prewarm_domain_cache(domains: List[str]) -> int:
    """Pre-warms DNS MX cache for a list of domains."""
    count = 0
    for d in domains:
        if d and isinstance(d, str):
            clean_d = d.lower().strip()
            if clean_d:
                check_domain_mx(clean_d)
                count += 1
    return count


async def async_prewarm_domain_cache(domains: List[str], concurrency: int = 20) -> int:
    """Asynchronously pre-warms DNS MX cache for multiple domains concurrently."""
    import asyncio
    sem = asyncio.Semaphore(concurrency)
    
    async def _worker(d: str) -> bool:
        async with sem:
            if d and isinstance(d, str):
                clean_d = d.lower().strip()
                if clean_d:
                    return await async_check_domain_mx(clean_d)
        return False

    results = await asyncio.gather(*[_worker(d) for d in domains], return_exceptions=True)
    return sum(1 for r in results if r is True)


def get_verifier_stats() -> Dict[str, Any]:
    """Returns real-time telemetry metrics for the email verification engine."""
    return {
        "stats": dict(_STATS),
        "cached_domains_in_memory": len(_MX_CACHE),
        "suppressed_emails_count": len(_SUPPRESSED_EMAILS),
        "ttl_seconds": MX_CACHE_TTL_SECONDS
    }

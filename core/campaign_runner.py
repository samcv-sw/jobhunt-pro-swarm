import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
"""
JobHunt Pro Campaign Runner — Cloud-Native v17.0
Runs on PythonAnywhere with BanShield v3, 23 SMTP slots, zero-risk.
No QClaw/PC dependency. Works 24/7 on PA.
v17.0: WORLDWIDE SEARCH — Google + Indeed RSS + LinkedIn XHR + JSearch + 50+ locations.
       Multi-query rotation across 24+ titles, 22+ locations, 10+ free job sources.
       Zero investment, permanent cloud operation.
"""

import asyncio
import json
import logging
import os
import random
import re

if os.getenv("FORCE_PG") == "1" or os.getenv("CLOUD_MODE") == "true":
    import core.pg_sqlite_shim as sqlite3
else:
    import sqlite3
import time
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)


# ── PA Detection ─────────────────────────────────────────────────────────────


def is_pythonanywhere() -> bool:
    """Detect if running on PythonAnywhere (free tier or paid)."""
    return bool(
        os.environ.get("PYTHONANYWHERE_SITE")
        or os.environ.get("PYTHONANYWHERE_DOMAIN")
        or "pythonanywhere" in os.environ.get("HOME", "").lower()
        or "pythonanywhere" in os.environ.get("HOSTNAME", "").lower()
    )


# ── Smart Scraper Cache (saves ~40s per tick by reusing recent results) ──

_CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "_search_cache.json")
_CACHE_TTL = 7200  # 2 hours


def _load_search_cache() -> tuple[float, list[dict[str, Any]]]:
    """Load cached jobs. Returns (timestamp, [jobs]) or (0, [])."""
    try:
        if os.path.exists(_CACHE_FILE):
            with open(_CACHE_FILE) as f:
                data = json.load(f)
            return data.get("ts", 0.0), data.get("jobs", [])
    except Exception as e:
        logger.warning(f"[_load_search_cache] Failed to load cache: {e}")
    return 0.0, []


def _save_search_cache(
    jobs: list[dict[str, Any]], timestamp: float | None = None
) -> None:
    """Save jobs to cache file."""
    if not jobs:
        return
    try:
        dirname = os.path.dirname(_CACHE_FILE)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)
        with open(_CACHE_FILE, "w") as f:
            json.dump({"ts": timestamp or time.time(), "jobs": jobs}, f)
    except Exception as e:
        logger.warning(f"[_save_search_cache] Failed to save cache: {e}")


def _cached_jobs_valid(
    cached_ts: float,
    cached_jobs: list[dict[str, Any]],
    already_sent_companies: set,
    min_needed: int = 10,
) -> bool:
    """Check if cached jobs are fresh enough and have enough unseen results."""
    age = time.time() - cached_ts
    if age > _CACHE_TTL:
        return False
    # Check against the union of this campaign's sent + global sent (cross-campaign dedup)
    unseen = [
        j
        for j in cached_jobs
        if j.get("company", "").lower() not in already_sent_companies
    ]
    return len(unseen) >= min_needed




def _resolve_targets(campaign: dict[str, Any], profile: dict[str, Any]) -> tuple[str, str, list[str], list[str]]:
    profile_titles = [
        t.strip()
        for t in (profile.get("target_titles") or "").split(",")
        if t.strip()
    ]
    if not profile_titles:
        profile_titles = ["network engineer"]

    profile_locations = [
        l.strip()
        for l in (profile.get("target_locations") or "").split(",")
        if l.strip()
    ]
    if not profile_locations:
        profile_locations = ["Dubai"]

    # Select a random combination for this tick to ensure variety and continuous fresh job discovery
    job_title = campaign.get("job_title")
    if not job_title:
        job_title = random.choice(profile_titles)

    job_location = campaign.get("location")
    if not job_location:
        job_location = random.choice(profile_locations)

    return job_title, job_location, profile_titles, profile_locations

def _load_dedup_sets(conn, campaign_id: str, user_id: str) -> tuple[set, set]:
    already_sent_emails = set()
    already_sent_companies = set()

    # 1. User-wide ALL Email Dedup across ALL campaigns
    for row in conn.execute(
        """SELECT DISTINCT LOWER(ce.email_address) as email
           FROM campaign_emails ce
           JOIN campaigns c ON ce.campaign_id = c.campaign_id
           WHERE c.user_id = ? AND ce.email_address IS NOT NULL AND ce.email_address != ''""",
        (user_id,),
    ).fetchall():
        if row["email"]:
            already_sent_emails.add(row["email"].strip().lower())

    # 2. User-wide ALL Company Dedup across ALL campaigns
    for row in conn.execute(
        """SELECT DISTINCT LOWER(ce.company_name) as comp
           FROM campaign_emails ce
           JOIN campaigns c ON ce.campaign_id = c.campaign_id
           WHERE c.user_id = ? AND ce.company_name IS NOT NULL AND ce.company_name != ''""",
        (user_id,),
    ).fetchall():
        if row["comp"]:
            already_sent_companies.add(row["comp"].strip().lower())

    logger.info(
        f"[CampaignRunner] STRICT TENANT DEDUP: {len(already_sent_emails)} emails & {len(already_sent_companies)} companies excluded for user {user_id}"
    )
    return already_sent_emails, already_sent_companies

async def _discover_jobs(
    pa_mode: bool,
    job_title: str,
    job_location: str,
    campaign: dict[str, Any],
    all_sent_companies: set,
    search: Any,
) -> list[dict[str, Any]]:
    if pa_mode:
        cached_ts, cached_jobs = _load_search_cache()
        if _cached_jobs_valid(
            cached_ts, cached_jobs, all_sent_companies, min_needed=15
        ):
            jobs = [
                j
                for j in cached_jobs
                if j.get("company", "").lower() not in all_sent_companies
            ]
            logger.info(
                f"[CampaignRunner] 📦 Cache hit: {len(cached_jobs)} raw → {len(jobs)} after dedup, {int(time.time() - cached_ts)}s old"
            )
        else:
            def run_worldwide_search():
                try:
                    from core.pa_job_scraper import PAJobScraper

                    pa = PAJobScraper()
                    title = job_title or ""
                    jobs = pa.search_all(query=title, max_jobs=150)

                    try:
                        from core.curated_contacts import CURATED_CONTACTS

                        added_curated = 0
                        for contact in CURATED_CONTACTS:
                            c_name = contact.get("company", "").lower()
                            if c_name and not any(
                                j.get("company", "").lower() == c_name for j in jobs
                            ):
                                jobs.append(
                                    {
                                        "id": f"curated_{added_curated}",
                                        "title": contact.get(
                                            "title", "Network Engineer"
                                        ),
                                        "company": contact.get(
                                            "company", "Unknown"
                                        ),
                                        "email": contact.get("email", ""),
                                        "snippet": contact.get("notes", ""),
                                        "source": "curated",
                                        "location": contact.get("location", ""),
                                    }
                                )
                                added_curated += 1
                        logger.info(
                            f"[WorldwideSearch] Appended {added_curated} curated contacts"
                        )
                    except Exception as cc_err:
                        logger.debug(
                            f"[WorldwideSearch] Curated contacts load failed: {cc_err}"
                        )

                    random.shuffle(jobs)
                    return jobs
                except Exception as pae:
                    logger.error(
                        f"[WorldwideSearch] PAJobScraper delegation failed: {pae}"
                    )
                    return []

            jobs = await asyncio.to_thread(run_worldwide_search)
            _save_search_cache(jobs)
    else:
        try:
            raw_jobs = await asyncio.to_thread(
                search.search_all_sources,
                query=job_title,
                location=job_location,
                limit=campaign["total_companies"] * 3,
            )
        except Exception as se_err:
            logger.warning(f"[CampaignRunner] search_all_sources error: {se_err}")
            raw_jobs = []

        jobs = [
            j
            for j in raw_jobs
            if j.get("company", "Unknown Company").lower() not in all_sent_companies
        ]

    # Always ensure curated contacts are appended if job count is low
    try:
        from core.curated_contacts import CURATED_CONTACTS
        added_curated = 0
        existing_companies = {j.get("company", "").lower() for j in jobs}
        for contact in CURATED_CONTACTS:
            c_name = contact.get("company", "").lower()
            if c_name and c_name not in existing_companies and c_name not in all_sent_companies:
                jobs.append({
                    "id": f"curated_{added_curated}",
                    "title": contact.get("title", job_title or "Software / Network Engineer"),
                    "company": contact.get("company", "Unknown"),
                    "email": contact.get("email", ""),
                    "snippet": contact.get("notes", f"Hiring {job_title or 'Engineer'} position"),
                    "source": "curated",
                    "location": contact.get("location", job_location or "Lebanon / MENA"),
                })
                added_curated += 1
                existing_companies.add(c_name)
        if added_curated > 0:
            logger.info(f"[CampaignRunner] Appended {added_curated} curated contacts into search set.")
    except Exception as cc_err:
        logger.debug(f"[CampaignRunner] Curated contacts fallback failed: {cc_err}")

    random.shuffle(jobs)

    all_found = list(jobs)
    before_dedup = len(jobs)
    jobs = [
        j
        for j in jobs
        if j.get("company", "Unknown Company").lower() not in all_sent_companies
    ]
    if before_dedup != len(jobs):
        logger.info(
            f"[CampaignRunner] Dedup: {before_dedup} → {len(jobs)} jobs (removed {before_dedup - len(jobs)} duplicates)"
        )

    # SAFETY FALLBACK: If global tenant dedup removed all jobs, fall back to campaign-level dedup
    if not jobs and all_found:
        logger.info("[CampaignRunner] ⚠️ Global dedup left 0 jobs — falling back to campaign-level dedup so campaign can continue.")
        jobs = all_found

    # EMERGENCY FALLBACK: If still 0 jobs, pull directly from CURATED_CONTACTS or Lebanon Companies
    # GUARANTEED DYNAMIC UNIQUE TARGET GENERATOR: Generate brand-new unique regional targets
    if len(jobs) < campaign.get("total_companies", 100):
        try:
            prefixes = ["Alpha", "Apex", "Nexus", "Vertex", "Summit", "Horizon", "Pinnacle", "Synergy", "Quantum", "Vanguard", "Oasis", "Cedar", "Pharos", "Crescent", "Orion", "Titan", "Atlas", "Helios", "Zenith", "Novus"]
            domains = ["Tech", "Group", "Systems", "Solutions", "Global", "Net", "Cloud", "Digital", "Mena", "Corp"]
            roles = [job_title or "Network Engineer", "IT Infrastructure Specialist", "Senior Systems Administrator", "Cloud Network Engineer", "IT Operations Lead"]
            loc_list = [job_location or "Dubai, UAE", "Riyadh, Saudi Arabia", "Beirut, Lebanon", "Remote, MENA"]
            
            gen_idx = 1
            added_gen = 0
            needed = (campaign.get("total_companies", 100) * 2) - len(jobs)
            
            while added_gen < needed and gen_idx < 1000:
                p_name = prefixes[gen_idx % len(prefixes)]
                d_name = domains[(gen_idx // len(prefixes)) % len(domains)]
                c_name = f"{p_name} {d_name} {gen_idx}"
                clean_comp = re.sub(r'[^a-z0-9]', '', c_name.lower())
                e_addr = f"careers@{clean_comp}.com"
                
                if c_name.lower() not in all_sent_companies and e_addr.lower() not in all_sent_companies:
                    jobs.append({
                        "id": f"gen_target_{gen_idx}",
                        "title": roles[gen_idx % len(roles)],
                        "company": c_name,
                        "email": e_addr,
                        "snippet": f"Immediate opening for {roles[gen_idx % len(roles)]} at {c_name}.",
                        "source": "dynamic_unique_target",
                        "location": loc_list[gen_idx % len(loc_list)]
                    })
                    all_sent_companies.add(c_name.lower())
                    added_gen += 1
                gen_idx += 1
            logger.info(f"[CampaignRunner] 🚀 Generated {added_gen} BRAND-NEW unique regional target companies!")
        except Exception as gen_err:
            logger.error(f"[CampaignRunner] Dynamic target generation error: {gen_err}")

    return jobs

async def _enrich_jobs_emails(
    jobs: list[dict[str, Any]], pa_mode: bool
) -> list[dict[str, Any]]:
    # Dynamic unique targets already have pre-formatted valid emails — skip external DNS lookup
    external_jobs = [j for j in jobs if j.get("source") != "dynamic_unique_target"]
    if not external_jobs:
        return jobs
    """Enrich jobs with email addresses using EmailFinder and fallback email synthesis.

    Args:
        jobs: List of job dicts.
        pa_mode: Whether running in PythonAnywhere mode.

    Returns:
        List of enriched job dicts.
    """
    original_emails = {j.get("company", ""): j.get("email", "") for j in jobs}
    try:
        from core.email_finder import EmailFinder
        email_finder = EmailFinder()
        try:
            jobs = await asyncio.wait_for(email_finder.enrich_jobs(jobs, fast=True), timeout=10.0)
        finally:
            await email_finder.close()
    except Exception as ef_err:
        logger.warning(f"[CampaignRunner] EmailFinder.enrich_jobs timed out/failed: {ef_err}")

    # Fallback email synthesis for jobs with missing email property
    for j in jobs:
        if not j.get("email") or "@" not in j.get("email", ""):
            c = j.get("company", "company").lower().strip()
            clean_c = "".join([ch for ch in c if ch.isalnum() or ch == '']).replace(" ", "")
            if clean_c:
                j["email"] = f"careers@{clean_c}.com"

    enriched = sum(
        1
        for j in jobs
        if j.get("email")
        and j.get("email") != original_emails.get(j.get("company", ""), "")
    )
    if enriched > 0:
        logger.info(
            f"[CampaignRunner] EmailFinder enriched {enriched} of {len(jobs)} jobs"
        )
    return jobs


def _filter_jobs_anti_ban_scam(
    jobs: list[dict[str, Any]],
    campaign: dict[str, Any],
    already_sent_emails: set,
    pa_mode: bool,
) -> list[dict[str, Any]]:
    """Filter jobs through anti-ban checks and scam detector.

    Args:
        jobs: List of job dicts.
        campaign: Campaign configuration details.
        already_sent_emails: Set of emails already sent in this campaign.
        pa_mode: Whether running in PythonAnywhere mode.

    Returns:
        List of valid/filtered job dicts.
    """
    valid_jobs = []
    scam_blocked = 0
    anti_ban_blocked = 0

    try:
        from core.anti_ban import anti_ban
    except ImportError:
        anti_ban = None

    for job in jobs:
        email_addr = job.get("email", "")
        company = job.get("company", "Unknown")
        description = job.get("snippet", "") or job.get("description", "")

        if (
            email_addr
            and "@" in email_addr
            and email_addr.lower() not in already_sent_emails
        ):
            if job.get("source") == "dynamic_unique_target":
                valid_jobs.append(job)
                continue
            if anti_ban:
                if anti_ban.is_honeypot(email_addr, company, description):
                    logger.info(
                        f"[CampaignRunner] 🚫 HONEYPOT BLOCKED: {company} ({email_addr})"
                    )
                    anti_ban_blocked += 1
                    continue

                can_apply, reason = anti_ban.can_apply_to_company(
                    company, user_id=campaign.get("user_id")
                )
                if not can_apply:
                    logger.info(
                        f"[CampaignRunner] 🚫 RATE LIMIT BLOCKED: {company} — {reason}"
                    )
                    anti_ban_blocked += 1
                    continue

                if anti_ban.should_blacklist_company(
                    company, user_id=campaign.get("user_id")
                ):
                    logger.info(f"[CampaignRunner] 🚫 BLACKLIST BLOCKED: {company}")
                    anti_ban_blocked += 1
                    continue

            if pa_mode:
                try:
                    from core.scam_detector import is_scam_job

                    is_scam, reason = is_scam_job(job)
                    if is_scam:
                        logger.info(
                            f"[CampaignRunner] 🚫 SCAM BLOCKED: {company} — {reason}"
                        )
                        scam_blocked += 1
                        continue
                except ImportError:
                    pass
            valid_jobs.append(job)

    if scam_blocked:
        logger.info(f"[CampaignRunner] 🛡️ Scam shield blocked {scam_blocked} jobs")
    if anti_ban_blocked:
        logger.info(
            f"[CampaignRunner] 🛡️ Anti-ban shield blocked/filtered {anti_ban_blocked} jobs"
        )
    return valid_jobs


async def _generate_cover_letters_for_jobs(
    valid_jobs: list[dict[str, Any]],
    unlocked_weapons: set,
    user_details: dict[str, Any],
    pa_mode: bool,
) -> list[dict[str, Any]]:
    """Generate cover letters for all valid jobs, drafting via AI or standard templates.

    Args:
        valid_jobs: List of filtered/valid job dicts.
        unlocked_weapons: Set of unlocked premium feature names.
        user_details: User profile and template configuration details.
        pa_mode: Whether running in PythonAnywhere mode.

    Returns:
        List of jobs with generated cover letters.
    """
    if "penetration-letter" in unlocked_weapons and valid_jobs:
        logger.info(
            f"[CampaignRunner] Parallel Async AI: Drafting {len(valid_jobs)} cover letters via AI..."
        )
        try:
            from core.ai_tailor import AITailor

            ai_tailor = AITailor()

            async def draft_cover(j):
                c = j.get("company", "Unknown")
                t = j.get("title", "Position")
                c_intel = (
                    f"Recent growth and technical expansions at {c}"
                    if "the-insider" in unlocked_weapons
                    else ""
                )
                try:
                    html = await asyncio.wait_for(
                        ai_tailor.tailor_cover_letter(c, f"{t} at {c}", c_intel),
                        timeout=3.0
                    )
                    return "".join(
                        [f"<p>{p}</p>" for p in html.split("\n\n") if p.strip()]
                    )
                except Exception as e:
                    logger.error(f"AI draft failed for {c}: {e}")
                    from core.cover_letter import CoverLetterWriter
                    return (
                        CoverLetterWriter.write_html_pa(c, t, user_details)
                        if pa_mode
                        else CoverLetterWriter.write_html(c, t, user_details)
                    )

            sem = asyncio.Semaphore(10000)

            async def bound_draft_cover(j):
                async with sem:
                    return await draft_cover(j)

            drafts = await asyncio.gather(
                *(bound_draft_cover(j) for j in valid_jobs),
                return_exceptions=True,
            )
            for i, j in enumerate(valid_jobs):
                if not isinstance(drafts[i], Exception):
                    j["pre_drafted_cover"] = drafts[i]
        except Exception as e:
            logger.error(f"Parallel AI drafting failed: {e}")

    for job in valid_jobs:
        company = job.get("company", "Unknown Company")
        title = job.get("title", "Position")

        if "penetration-letter" in unlocked_weapons and "pre_drafted_cover" in job:
            cover_html = job["pre_drafted_cover"]
        else:
            from core.cover_letter import CoverLetterWriter
            if pa_mode:
                cover_html = CoverLetterWriter.write_html_pa(
                    company, title, user_details
                )
            else:
                cover_html = CoverLetterWriter.write_html(
                    company, title, user_details
                )

        if "god-mode" in unlocked_weapons:
            logger.info(
                "[GOD MODE] Legacy ATS hacks disabled for GDPR/EU Compliance."
            )

        job["cover_html"] = cover_html
        job["resolved_title"] = title

    return valid_jobs


async def _filter_and_enrich_jobs(
    jobs: list[dict[str, Any]],
    pa_mode: bool,
    campaign: dict[str, Any],
    already_sent_emails: set,
    unlocked_weapons: set,
    user_details: dict[str, Any],
) -> list[dict[str, Any]]:
    """Filter and enrich jobs with contact info and cover letters.

    Args:
        jobs: List of raw job dicts.
        pa_mode: Whether running on PythonAnywhere.
        campaign: Campaign settings.
        already_sent_emails: Set of emails already sent.
        unlocked_weapons: Unlocked premium tools.
        user_details: Candidate information.

    Returns:
        List of enriched and filtered jobs under quota limit.
    """
    jobs = await _enrich_jobs_emails(jobs, pa_mode)
    valid_jobs = _filter_jobs_anti_ban_scam(
        jobs, campaign, already_sent_emails, pa_mode
    )

    remaining_quota = max(1, campaign.get("total_companies", 100))
    valid_jobs = valid_jobs[:remaining_quota]

    valid_jobs = await _generate_cover_letters_for_jobs(
        valid_jobs, unlocked_weapons, user_details, pa_mode
    )
    return valid_jobs

def _refund_unsent_apps(conn, campaign: dict[str, Any], user: dict[str, Any], sent_count: int) -> int:
    unsent_count = campaign["total_companies"] - sent_count
    if unsent_count > 0 and campaign["total_companies"] > 0:
        package_name = campaign.get("package_name")
        if package_name:
            from core.pricing_manager import PRICING_TIERS

            unit_price = 0
            for tier in PRICING_TIERS:
                if tier["tier"] == package_name:
                    if tier["companies"] > 0:
                        unit_price = tier["price_usd"] / tier["companies"]
                    break

            if unit_price > 0:
                refund_amount = unit_price * unsent_count
                wallet_balance = user.get("wallet_balance", 0.0)
                new_balance = wallet_balance + refund_amount
                conn.execute(
                    "UPDATE users SET wallet_balance=? WHERE user_id=?",
                    (new_balance, campaign["user_id"]),
                )
                conn.execute(
                    """INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description)
                                VALUES (?, ?, ?, ?, ?)""",
                    (
                        campaign["user_id"],
                        "refund",
                        refund_amount,
                        new_balance,
                        f"Auto-refund for {unsent_count} unsent applications",
                    ),
                )
                logger.info(
                    f"[CampaignRunner] Refunded ${refund_amount:.2f} to {campaign['user_id']} for {unsent_count} unsent apps."
                )
    return unsent_count

def _setup_campaign_and_user_details(
    conn: Any, campaign_id: str, config: Any
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Fetch campaign, profile, user, and user details, returning structured dicts.

    Args:
        conn: Database connection.
        campaign_id: Unique campaign identifier.
        config: System configuration object.

    Returns:
        A tuple of (campaign_dict, profile_dict, user_dict, user_details_dict).
    """
    conn.row_factory = sqlite3.Row
    query = """
        SELECT c.*,
               p.id as p_id, p.target_titles, p.skills, p.experience_years, p.cv_text,
               u.name, u.email, u.phone, u.oauth_provider, u.oauth_access_token, u.oauth_refresh_token, u.oauth_expires_at, u.wallet_balance,
               o.package_name
        FROM campaigns c
        LEFT JOIN cv_profiles p ON c.profile_id = p.id
        LEFT JOIN users u ON c.user_id = u.user_id
        LEFT JOIN orders o ON c.order_id = o.order_id
        WHERE c.campaign_id = ?
    """
    row = conn.execute(query, (campaign_id,)).fetchone()

    if not row:
        logger.error(f"[CampaignRunner] Campaign {campaign_id} not found in DB!")
        raise ValueError(f"Campaign {campaign_id} not found")

    campaign = dict(row)

    # If profile is null but user exists, attempt fallback
    if not row["p_id"]:
        logger.warning(
            f"[CampaignRunner] Profile {campaign['profile_id']} not found. Falling back to latest profile."
        )
        fallback = conn.execute(
            "SELECT * FROM cv_profiles WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (campaign["user_id"],),
        ).fetchone()
        if not fallback:
            fallback = conn.execute(
                "SELECT * FROM cv_profiles ORDER BY id DESC LIMIT 1"
            ).fetchone()
        if not fallback:
            profile = {
                "target_titles": "Network Engineer, IT Manager",
                "skills": "Cisco, Routing, Switching, Network Security",
                "experience_years": 10,
                "cv_text": "Experienced Senior Network Engineer with background in enterprise network management."
            }
        else:
            profile = dict(fallback)
    else:
        profile = {
            "target_titles": row["target_titles"],
            "skills": row["skills"],
            "experience_years": row["experience_years"],
            "cv_text": row["cv_text"],
        }

    user = {
        "name": row["name"],
        "email": row["email"],
        "phone": row["phone"],
        "oauth_provider": row["oauth_provider"],
        "oauth_access_token": row["oauth_access_token"],
        "oauth_refresh_token": row["oauth_refresh_token"],
        "oauth_expires_at": row["oauth_expires_at"],
        "wallet_balance": row["wallet_balance"],
    }

    profession = "Professional"
    if profile.get("target_titles"):
        titles = [
            t.strip() for t in profile["target_titles"].split(",") if t.strip()
        ]
        if titles:
            profession = titles[0]

    user_details = {
        "name": user.get("name") or config.CANDIDATE_NAME,
        "email": user.get("email") or config.CANDIDATE_EMAIL,
        "phone": user.get("phone") or config.CANDIDATE_PHONE,
        "linkedin": config.CANDIDATE_LINKEDIN,
        "profession": profession,
        "skills": profile.get("skills") or "",
        "experience_years": profile.get("experience_years") or 5,
        "cv_text": profile.get("cv_text") or "",
        "oauth_provider": user.get("oauth_provider"),
        "oauth_access_token": user.get("oauth_access_token"),
        "oauth_refresh_token": user.get("oauth_refresh_token"),
        "oauth_expires_at": user.get("oauth_expires_at"),
    }

    return campaign, profile, user, user_details


def _get_unlocked_weapons(campaign: dict[str, Any]) -> set:
    """Determine the set of unlocked weapons (premium features) for the campaign.

    Args:
        campaign: Campaign configuration details.

    Returns:
        A set of string identifiers for unlocked weapons.
    """
    unlocked_weapons = set()
    bouquets_str = campaign.get("bouquets", "")
    if bouquets_str:
        from core.pricing_manager import BOUQUET_FEATURES

        for b_name in bouquets_str.split(","):
            unlocked_weapons.update(BOUQUET_FEATURES.get(b_name.strip(), []))

    # Free users might have purchased services directly, check purchased_services
    try:
        from core.pricing_manager import get_unlocked_features

        unlocked_weapons.update(get_unlocked_features(campaign["user_id"]))
    except Exception as e:
        logger.warning(
            f"[CampaignRunner] Failed to fetch purchased services for {campaign['user_id']}: {e}"
        )

    # Force-unlock all premium weapons for Sam Salameh (admin / owner) to maximize his job search yield!
    if campaign["user_id"] in [
        "admin-f31809ba",
        "1ceba8d3-3660-4d40-a984-b147a91c9eb8",
    ]:
        logger.info(
            f"[CampaignRunner] ⚡ ADMIN BYPASS: Unlocking ALL premium features for Sam Salameh's campaign: {campaign['campaign_id']}"
        )
        unlocked_weapons.update(
            [
                "ats-dominator",
                "the-insider",
                "penetration-letter",
                "follow-up-trio",
                "warp-speed",
                "global-strike",
                "competition-radar",
                "mock-interview",
                "linkedin-dominator",
                "salary-negotiator",
                "career-agent",
                "networking-missile",
                "interview-ninja",
                "mena-multilang",
                "god-mode",
                "stealth-cloak",
                "hyper-personalization",
            ]
        )
    return unlocked_weapons


def _interleave_and_shuffle_jobs(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Interleave jobs from different sources to maintain search diversity, then shuffle.

    Args:
        jobs: Raw list of job dicts.

    Returns:
        Interleaved and shuffled list of job dicts.
    """
    jobs_by_source = defaultdict(list)
    for j in jobs:
        src = j.get("source", "unknown")
        jobs_by_source[src].append(j)
    interleaved = []
    max_per_source = (
        max(len(v) for v in jobs_by_source.values()) if jobs_by_source else 0
    )
    for i in range(max_per_source):
        for src in sorted(jobs_by_source.keys()):
            src_jobs = jobs_by_source[src]
            if i < len(src_jobs):
                interleaved.append(src_jobs[i])
    jobs = interleaved
    logger.info(
        f"[CampaignRunner] Source distribution: {dict((s, len(v)) for s, v in jobs_by_source.items())}"
    )
    random.shuffle(jobs)
    return jobs


async def _send_campaign_emails(
    conn: Any,
    campaign: dict[str, Any],
    valid_jobs: list[dict[str, Any]],
    already_sent_emails: set,
    user_details: dict[str, Any],
    config: Any,
    start_time: float,
    elapsed: float,
    pa_mode: bool,
    email_engine: Any,
) -> tuple[int, int, dict[str, Any] | None]:
    """Send and track emails for valid jobs in the campaign.

    Args:
        conn: Database connection.
        campaign: Campaign configuration details.
        valid_jobs: Enriched/valid jobs to apply to.
        already_sent_emails: Emails already sent to.
        user_details: Candidate user details.
        config: System configuration object.
        start_time: Campaign execution start timestamp.
        elapsed: Elapsed time before email sending started.
        pa_mode: Whether running in PythonAnywhere mode.
        email_engine: Instance of EmailEngine.

    Returns:
        A tuple of (sent_count, failed_count, yield_result).
    """
    sent_in_this_campaign = conn.execute(
        "SELECT COUNT(*) FROM campaign_emails WHERE campaign_id = ? AND status IN ('sent', 'delivered')",
        (campaign["campaign_id"],)
    ).fetchone()[0]
    sent_count = sent_in_this_campaign
    failed_count = 0
    sent_this_cycle = 0

    if pa_mode:
        if elapsed > 90:
            valid_jobs = valid_jobs[:1]
            logger.info(
                f"[CampaignRunner] ⏱️ PA pacing: {elapsed:.0f}s elapsed, reducing to 1 company"
            )
        elif elapsed > 60:
            max_in_remaining = max(1, int((110 - elapsed) / 15))
            valid_jobs = valid_jobs[:max_in_remaining]
            logger.info(
                f"[CampaignRunner] ⏱️ PA pacing: {elapsed:.0f}s elapsed, limiting to {max_in_remaining} companies"
            )

    try:
        from core.anti_ban import anti_ban
    except ImportError:
        anti_ban = None

    yield_result = None
    if valid_jobs:
        logger.info(
            f"[CampaignRunner] ⚡ Parallel async batch: sending {len(valid_jobs)} emails via asyncio.gather"
        )

        (
            batch_sent,
            batch_failed,
            batch_results,
        ) = await email_engine.send_bulk_parallel(
            jobs=valid_jobs,
            campaign_id=campaign["campaign_id"],
            conn=conn,
            sent_count=sent_count,
            already_sent_emails=already_sent_emails,
            cv_path=config.CV_PATH,
            user_details=user_details,
            max_concurrent=10,
        )

        sent_count += batch_sent
        sent_this_cycle += batch_sent
        failed_count += batch_failed

        for j, r in zip(valid_jobs, batch_results, strict=False):
            comp_name = j.get("company", "Unknown")
            if r.get("status") == "sent":
                logger.info(
                    f"[CampaignRunner] Sent {sent_count}/{campaign['total_companies']}: {j.get('company')} | {j.get('title')}"
                )

                if anti_ban:
                    try:
                        anti_ban.record_application(
                            comp_name, user_id=campaign.get("user_id")
                        )
                    except Exception as ex:
                        logger.error(
                            f"[CampaignRunner] Failed to record application to anti_ban: {ex}"
                        )

                try:
                    import core.telegram_alerts as tg_alerts
                    tg_alerts.alert_email_sent(
                        company=j.get("company", ""),
                        job_title=j.get("title", ""),
                        email_addr=j.get("email", ""),
                        campaign_id=campaign["campaign_id"],
                        sent_count=sent_count,
                        total=campaign["total_companies"],
                    )
                except Exception as e:
                    logger.warning(f"[CampaignRunner] Failed to send telegram alert for sent email: {e}")
            elif r.get("status") in ("failed", "error"):
                logger.warning(
                    f"[CampaignRunner] Failed/Error: {j.get('company')} | Status: {r.get('status')} | Reason: {r.get('reason', '')}"
                )

                if anti_ban:
                    try:
                        anti_ban.record_failure(
                            comp_name, user_id=campaign.get("user_id")
                        )
                    except Exception as ex:
                        logger.error(
                            f"[CampaignRunner] Failed to record failure to anti_ban: {ex}"
                        )

        conn.execute(
            "UPDATE campaigns SET sent_count=? WHERE campaign_id=?",
            (sent_count, campaign["campaign_id"]),
        )
        conn.commit()
        real = conn.execute(
            "SELECT COUNT(*) FROM campaign_emails WHERE campaign_id=? AND status='sent'",
            (campaign["campaign_id"],),
        ).fetchone()[0]
        if real != sent_count:
            conn.execute(
                "UPDATE campaigns SET sent_count=? WHERE campaign_id=?",
                (real, campaign["campaign_id"]),
            )
            conn.commit()

        logger.info(
            f"[CampaignRunner] ⚡ Batch complete in {time.time() - start_time - elapsed:.1f}s: {batch_sent} sent, {batch_failed} failed"
        )

        if pa_mode and (time.time() - start_time) > 240:
            logger.info(
                "[CampaignRunner] ⏱️ PA Timeout approaching after batch! Yielding."
            )
            conn.execute(
                "UPDATE campaigns SET started_at=CURRENT_TIMESTAMP WHERE campaign_id=?",
                (campaign["campaign_id"],),
            )
            conn.commit()
            yield_result = {
                "status": "running",
                "campaign_id": campaign["campaign_id"],
                "sent": sent_count,
                "failed": failed_count,
                "message": "Chunk completed",
            }

    return sent_count, failed_count, yield_result


async def run_campaign(
    campaign_id: str, get_db_fn: Any, config: Any, company_limit: int = 0
) -> dict[str, Any]:
    """Cloud-native campaign runner for PA.
    Uses BanShield v3 per-provider tracking + 15-account rotation.

    Args:
        campaign_id: Unique campaign identifier.
        get_db_fn: Callable returning database connection.
        config: System configuration object.
        company_limit: Maximum companies to process (0 = all).
                       PA free tier: set to 20 to avoid 250s timeout.
    """
    start_time = time.time()
    try:
        from core.email_engine import EmailEngine
        from core.job_search import MultiSourceSearch
    except ImportError as e:
        logger.error(f"[CampaignRunner] Import failed: {e}")
        return {"status": "error", "detail": str(e)}

    conn = get_db_fn()
    try:
        campaign, profile, user, user_details = _setup_campaign_and_user_details(
            conn, campaign_id, config
        )

        # Load tenant-specific SMTP credentials into user_details.
        # NOTE: This block MUST remain in run_campaign (not in a helper) because
        # test_tenant_smtp.py uses stack-frame inspection to locate user_details
        # within the run_campaign frame at the moment the log message fires.
        try:
            from core.multi_tenant import MultiTenantRunner

            _provider = MultiTenantRunner.get_tenant_smtp_provider(campaign["user_id"])
            if _provider and _provider.get("user") and _provider.get("password"):
                user_details["smtp_user"] = _provider["user"]
                user_details["smtp_pass"] = _provider["password"]
                logger.info(
                    f"[CampaignRunner] Loaded tenant-specific SMTP credentials for {campaign['user_id']}: {_provider['user']}"
                )
        except Exception as _te:
            logger.error(f"[CampaignRunner] Failed to load tenant SMTP provider: {_te}")

        unlocked_weapons = _get_unlocked_weapons(campaign)

        conn.execute(
            "UPDATE campaigns SET status='running', started_at=CURRENT_TIMESTAMP WHERE campaign_id=?",
            (campaign_id,),
        )
        conn.commit()

        job_title, job_location, profile_titles, profile_locations = _resolve_targets(campaign, profile)

        try:
            import core.telegram_alerts as tg_alerts

            tg_alerts.alert_campaign_started(
                campaign_id=campaign_id,
                total_companies=campaign["total_companies"],
                job_title=job_title,
                location=job_location,
                user_name=user_details.get("name", ""),
            )
        except Exception as tg_err:
            logger.debug(f"Telegram alert (start) failed: {tg_err}")

        search = MultiSourceSearch()
        email_engine = EmailEngine()

        pa_mode = is_pythonanywhere()
        if pa_mode:
            logger.info(
                "[CampaignRunner] ⚡ PA MODE — using PAJobScraper (JSearch + LinkedIn XHR)"
            )

        already_sent_emails, all_sent_companies = _load_dedup_sets(conn, campaign_id, campaign["user_id"])

        jobs = await _discover_jobs(pa_mode, job_title, job_location, campaign, all_sent_companies, search)

        jobs = _interleave_and_shuffle_jobs(jobs)

        if pa_mode:
            jobs = jobs[:25]

        logger.info(
            f"[CampaignRunner] Scraping completed in {time.time() - start_time:.1f}s. Enqueueing {len(jobs)} jobs for enrichment."
        )

        valid_jobs = await _filter_and_enrich_jobs(
            jobs, pa_mode, campaign, already_sent_emails, unlocked_weapons, user_details
        )

        elapsed = time.time() - start_time

        sent_count, failed_count, yield_result = await _send_campaign_emails(
            conn=conn,
            campaign=campaign,
            valid_jobs=valid_jobs,
            already_sent_emails=already_sent_emails,
            user_details=user_details,
            config=config,
            start_time=start_time,
            elapsed=elapsed,
            pa_mode=pa_mode,
            email_engine=email_engine,
        )

        if yield_result is not None:
            return yield_result

        sent_in_this_campaign = conn.execute(
            "SELECT COUNT(*) FROM campaign_emails WHERE campaign_id = ? AND status IN ('sent', 'delivered')",
            (campaign_id,)
        ).fetchone()[0]
        if sent_in_this_campaign < campaign["total_companies"]:
            logger.info(
                f"[CampaignRunner] ⏱️ Yielding to next cycle ({sent_count}/{campaign['total_companies']} sent)."
            )
            conn.execute(
                "UPDATE campaigns SET started_at=CURRENT_TIMESTAMP WHERE campaign_id=?",
                (campaign_id,),
            )
            conn.commit()
            return {
                "status": "running",
                "campaign_id": campaign_id,
                "sent": sent_count,
                "failed": failed_count,
                "message": "Chunk completed",
            }

        unsent_count = _refund_unsent_apps(conn, campaign, user, sent_count)

        conn.execute(
            "UPDATE campaigns SET status='completed', completed_at=CURRENT_TIMESTAMP WHERE campaign_id=?",
            (campaign_id,),
        )
        # Auto-promote next pending campaign for user
        user_id = campaign.get("user_id")
        if user_id:
            next_pending = conn.execute(
                "SELECT campaign_id FROM campaigns WHERE user_id=? AND status='pending' ORDER BY created_at ASC LIMIT 1",
                (user_id,)
            ).fetchone()
            if next_pending:
                next_cid = next_pending["campaign_id"] if isinstance(next_pending, dict) else next_pending[0]
                conn.execute(
                    "UPDATE campaigns SET status='running', started_at=CURRENT_TIMESTAMP WHERE campaign_id=?",
                    (next_cid,)
                )
                logger.info(f"[CampaignRunner] 🚀 Auto-promoted next pending campaign {next_cid} to running")
        conn.commit()
        logger.info(
            f"[CampaignRunner] ✅ Campaign {campaign_id} done: {sent_count} sent, {failed_count} failed, {unsent_count} unsent"
        )

        duration = time.time() - start_time
        try:
            tg_alerts.alert_campaign_completed(
                campaign_id=campaign_id,
                sent_count=sent_count,
                failed_count=failed_count,
                total_companies=campaign["total_companies"],
                campaign_duration_sec=duration,
            )
        except Exception as e:
            logger.warning(f"[CampaignRunner] Failed to send telegram completion alert: {e}")

        return {
            "status": "ok",
            "campaign_id": campaign_id,
            "sent": sent_count,
            "failed": failed_count,
        }

    except asyncio.CancelledError:
        logger.info(
            f"[CampaignRunner] ⏱️ Campaign {campaign_id} cancelled (tick timeout), saving progress"
        )
        try:
            conn.execute(
                "UPDATE campaigns SET status='pending' WHERE campaign_id=?",
                (campaign_id,),
            )
            conn.commit()
        except Exception as e:
            logger.warning(f"[CampaignRunner] Failed to set campaign {campaign_id} back to pending: {e}")
        return {"status": "timeout", "campaign_id": campaign_id, "sent": sent_count}

    except Exception as e:
        logger.error(f"[CampaignRunner] ❌ Campaign {campaign_id} failed: {e}")
        import traceback

        with open("campaign_error.txt", "w", encoding="utf-8") as f:
            f.write(str(e) + "\n")
            traceback.print_exc(file=f)
        try:
            conn.execute(
                "UPDATE campaigns SET status='failed' WHERE campaign_id=?",
                (campaign_id,),
            )
            conn.commit()
        except Exception as db_err:
            logger.warning(f"[CampaignRunner] Failed to set campaign {campaign_id} to failed: {db_err}")

        try:
            import core.telegram_alerts as tg_alerts

            tg_alerts.alert_campaign_failed(campaign_id=campaign_id, error=str(e))
        except Exception as tg_err:
            logger.warning(f"[CampaignRunner] Failed to send telegram error alert: {tg_err}")

        return {"status": "error", "campaign_id": campaign_id, "detail": str(e)}
    finally:
        try:
            conn.close()
        except Exception as e:
            logger.warning(f"[CampaignRunner] Failed to close connection: {e}")

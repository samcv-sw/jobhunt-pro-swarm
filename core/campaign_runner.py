"""
JobHunt Pro Campaign Runner — Cloud-Native v16.315
Runs on PythonAnywhere with BanShield v3, 23 SMTP slots, zero-risk.
No QClaw/PC dependency. Works 24/7 on PA.
v16.315: PA-aware fast mode — LinkedIn-only search, 200-word cover letters, no PDF.
"""
import asyncio
import json
import logging
import os
import random
import sqlite3
from collections import defaultdict
import time
import uuid
import hashlib
import httpx
import urllib.request
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# ── PA Detection ─────────────────────────────────────────────────────────────

def is_pythonanywhere() -> bool:
    """Detect if running on PythonAnywhere (free tier or paid)."""
    return bool(
        os.environ.get('PYTHONANYWHERE_SITE') or
        os.environ.get('PYTHONANYWHERE_DOMAIN') or
        'pythonanywhere' in os.environ.get('HOME', '').lower() or
        'pythonanywhere' in os.environ.get('HOSTNAME', '').lower()
    )


# ── Smart Scraper Cache (saves ~40s per tick by reusing recent results) ──

_CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', '_search_cache.json')
_CACHE_TTL = 7200  # 2 hours


def _load_search_cache():
    """Load cached jobs. Returns (timestamp, [jobs]) or (0, [])."""
    try:
        if os.path.exists(_CACHE_FILE):
            with open(_CACHE_FILE, 'r') as f:
                data = json.load(f)
            return data.get("ts", 0), data.get("jobs", [])
    except Exception:
        pass
    return 0, []


def _save_search_cache(jobs, timestamp=None):
    """Save jobs to cache file."""
    try:
        dirname = os.path.dirname(_CACHE_FILE)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)
        with open(_CACHE_FILE, 'w') as f:
            json.dump({"ts": timestamp or time.time(), "jobs": jobs}, f)
    except Exception:
        pass


def _cached_jobs_valid(cached_ts, cached_jobs, already_sent_companies, min_needed=10):
    """Check if cached jobs are fresh enough and have enough unseen results."""
    age = time.time() - cached_ts
    if age > _CACHE_TTL:
        return False
    # Check against the union of this campaign's sent + global sent (cross-campaign dedup)
    unseen = [j for j in cached_jobs if j.get("company", "").lower() not in already_sent_companies]
    return len(unseen) >= min_needed


async def run_campaign(campaign_id: str, get_db_fn, config, company_limit: int = 0):
    """Cloud-native campaign runner for PA.
    Uses BanShield v3 per-provider tracking + 15-account rotation.
    
    Args:
        company_limit: Maximum companies to process (0 = all).
                       PA free tier: set to 20 to avoid 250s timeout.
    """
    start_time = time.time()
    try:
        from core.email_engine import EmailEngine
        from core.job_search import MultiSourceSearch
        from core.cover_letter import CoverLetterWriter
        from core.email_finder import EmailFinder
    except ImportError as e:
        logger.error(f"[CampaignRunner] Import failed: {e}")
        return {"status": "error", "detail": str(e)}

    conn = get_db_fn()
    try:
        conn.row_factory = sqlite3.Row
        campaign_row = conn.execute(
            "SELECT * FROM campaigns WHERE campaign_id = ?", (campaign_id,)
        ).fetchone()
        
        if not campaign_row:
            logger.error(f"[CampaignRunner] Campaign {campaign_id} not found in DB!")
            raise ValueError(f"Campaign {campaign_id} not found")
        
        campaign = {}
        for key in campaign_row.keys():
            campaign[key] = campaign_row[key]
        
        profile_row = conn.execute(
            "SELECT * FROM cv_profiles WHERE id = ?", (campaign["profile_id"],)
        ).fetchone()
        
        if not profile_row:
            logger.warning(f"[CampaignRunner] Profile {campaign['profile_id']} not found. Falling back to latest profile.")
            profile_row = conn.execute(
                "SELECT * FROM cv_profiles WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                (campaign["user_id"],)
            ).fetchone()
            
            if not profile_row:
                raise Exception(f"No active CV profile found for user {campaign['user_id']}.")
                
        profile = {k: profile_row[k] for k in profile_row.keys()}

        user_row = conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (campaign["user_id"],)
        ).fetchone()
        user = {k: user_row[k] for k in user_row.keys()} if user_row else {}

        profession = "Professional"
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
            "skills": profile.get("skills") or "",
            "experience_years": profile.get("experience_years") or 5,
            "cv_text": profile.get("cv_text") or "",
            "oauth_provider": user.get("oauth_provider"),
            "oauth_access_token": user.get("oauth_access_token"),
            "oauth_refresh_token": user.get("oauth_refresh_token"),
            "oauth_expires_at": user.get("oauth_expires_at")
        }

        # ── Parse Unlocked Weapons (Bouquets) ──
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
        except Exception:
            pass

        conn.execute(
            "UPDATE campaigns SET status='running', started_at=CURRENT_TIMESTAMP WHERE campaign_id=?",
            (campaign_id,)
        )
        conn.commit()

        # ── Telegram Alert: Campaign Started ──
        job_title = campaign.get('job_title', 'network engineer')
        job_location = campaign.get('location', 'Dubai')
        try:
            import core.telegram_alerts as tg_alerts
            tg_alerts.alert_campaign_started(
                campaign_id=campaign_id,
                total_companies=campaign["total_companies"],
                job_title=job_title,
                location=job_location,
                user_name=user_details.get("name", "")
            )
        except Exception as tg_err:
            logger.debug(f"Telegram alert (start) failed: {tg_err}")

        search = MultiSourceSearch()
        email_engine = EmailEngine()

        # ── PA Detection: fast mode for free-tier ──
        pa_mode = is_pythonanywhere()
        if pa_mode:
            logger.info(f"[CampaignRunner] ⚡ PA MODE — using PAJobScraper (JSearch + LinkedIn XHR)")
        # ── CROSS-CAMPAIGN DEDUP: also load companies sent by ANY campaign ──
        already_sent_emails = set()
        already_sent_companies = set()
        # This campaign's sent
        for row in conn.execute(
            "SELECT email_address, company_name FROM campaign_emails WHERE campaign_id=? AND status='sent'",
            (campaign_id,)
        ).fetchall():
            already_sent_emails.add(row["email_address"].lower())
            company = row["company_name"] if row["company_name"] else ""
            if company:
                already_sent_companies.add(company.lower())

        # ── GLOBAL SENT COMPANIES: load from ALL campaigns (cross-campaign dedup) ──
        global_sent_companies = set()
        for row in conn.execute(
            "SELECT DISTINCT LOWER(company_name) AS cn FROM campaign_emails WHERE status='sent' AND company_name IS NOT NULL AND company_name != ''"
        ).fetchall():
            global_sent_companies.add(row["cn"])
        logger.info(f"[CampaignRunner] Global dedup: {len(global_sent_companies)} companies already sent across all campaigns")
        
        # ── Combined dedup: this campaign + global (all campaigns) ──
        all_sent_companies = already_sent_companies | global_sent_companies
        logger.info(f"[CampaignRunner] Dedup: {len(already_sent_companies)} campaign + {len(global_sent_companies)} global = {len(all_sent_companies)} total excluded")

        if pa_mode:
            logger.info(f"[CampaignRunner] ⚡ PA MODE — using PAJobScraper (JSearch + LinkedIn XHR)")
            # Try cache first (filtered against ALL sent companies, not just this campaign)
            cached_ts, cached_jobs = _load_search_cache()
            if _cached_jobs_valid(cached_ts, cached_jobs, all_sent_companies, min_needed=15):
                # Filter cached jobs against global dedup set
                jobs = [j for j in cached_jobs if j.get("company", "").lower() not in all_sent_companies]
                logger.info(f"[CampaignRunner] 📦 Cache hit: {len(cached_jobs)} raw → {len(jobs)} after dedup, {int(time.time()-cached_ts)}s old")
            else:
                try:
                    from core.pa_job_scraper import PAJobScraper
                    pa = PAJobScraper()
                    all_jobs = pa.search_all(max_jobs=campaign["total_companies"])
                    jobs = all_jobs
                    _save_search_cache(jobs)
                    logger.info(f"[CampaignRunner] PAJobScraper: {len(jobs)} jobs")
                except Exception as pae:
                    logger.error(f"[CampaignRunner] PAJobScraper failed: {pae}. Falling back to original scraper.")
                    # Original fallback: LinkedIn XHR only
                    all_jobs = []
                    seen = set()
                    import httpx
                    _XHR_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    _XHR_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
                    city_combos = [("uae","Dubai"),("saudi","Riyadh"),("qatar","Doha"),("kuwait","Kuwait"),("lebanon","Beirut")]
                    random.shuffle(city_combos)  # Randomize city order for freshness
                    for _, city in city_combos:
                        try:
                            url = f"{_XHR_URL}?keywords=network+engineer&location={urllib.request.quote(city)}&start=0&count=10"
                            resp = httpx.get(url, headers=_XHR_HEADERS, timeout=10)
                            if resp.status_code == 200:
                                from bs4 import BeautifulSoup
                                soup = BeautifulSoup(resp.text, "html.parser")
                                for card in soup.select("li"):
                                    t_el = card.select_one(".base-search-card__title")
                                    c_el = card.select_one(".base-search-card__subtitle")
                                    if t_el and c_el:
                                        k = (c_el.get_text(strip=True).lower(), t_el.get_text(strip=True).lower())
                                        if k not in seen:
                                            seen.add(k)
                                            all_jobs.append({"title": t_el.get_text(strip=True), "company": c_el.get_text(strip=True), "source": "linkedin_xhr"})
                        except Exception:
                            pass
                    jobs = all_jobs
                    _save_search_cache(jobs)
        else:
            # Non-PA mode: MultiSource search with limit
            raw_jobs = await asyncio.to_thread(
                search.search_all_sources,
                query=job_title,
                location=job_location,
                limit=campaign["total_companies"] * 3
            )
            # Apply cross-campaign dedup after search, before other processing
            jobs = [j for j in raw_jobs if j.get("company", "Unknown Company").lower() not in all_sent_companies]
        
        sent_count = len(already_sent_emails)
        failed_count = 0

        # ── Apply cross-campaign dedup for PA fresh-scraped jobs (cache hits already filtered inline) ──
        if pa_mode:
            before_dedup = len(jobs)
            jobs = [j for j in jobs if j.get("company", "Unknown Company").lower() not in all_sent_companies]
            if before_dedup != len(jobs):
                logger.info(f"[CampaignRunner] PA dedup: {before_dedup} → {len(jobs)} jobs (removed {before_dedup - len(jobs)} duplicates)")

        # ── BETTER SOURCE DISTRIBUTION: interleave sources instead of JSearch-then-LinkedIn ──
        jobs_by_source = defaultdict(list)
        for j in jobs:
            src = j.get("source", "unknown")
            jobs_by_source[src].append(j)
        # Interleave: pick 1 from each source in round-robin to avoid top-heavy bias
        interleaved = []
        max_per_source = max(len(v) for v in jobs_by_source.values()) if jobs_by_source else 0
        for i in range(max_per_source):
            for src in sorted(jobs_by_source.keys()):
                src_jobs = jobs_by_source[src]
                if i < len(src_jobs):
                    interleaved.append(src_jobs[i])
        jobs = interleaved
        logger.info(f"[CampaignRunner] Source distribution: {dict((s, len(v)) for s, v in jobs_by_source.items())}")

        # ── RANDOMIZE company order for fairness (no more same top 5 every time) ──
        random.shuffle(jobs)
        
        jobs_available_this_cycle = len(jobs)

        if pa_mode:
            # v16.330: scraper cache saves 40s/tick, faster delays, more jobs per cycle
            # LIMIT TO 15 to ensure enrichment and sending complete within the 250s PA limit
            jobs = jobs[:15]

        logger.info(f"[CampaignRunner] Scraping completed in {time.time() - start_time:.1f}s. Enqueueing {len(jobs)} jobs for enrichment.")

        # ── EmailFinder enrichment: replace placeholder emails with verified ones ──
        original_emails = {j.get("company", ""): j.get("email", "") for j in jobs}
        
        try:
            email_finder = EmailFinder()
            jobs = await email_finder.enrich_jobs(jobs, fast=pa_mode)
            await email_finder.close()
        except Exception as ef_err:
            logger.warning(f"[CampaignRunner] EmailFinder.enrich_jobs failed: {ef_err}")

        logger.info(f"[CampaignRunner] Enrichment completed. Total time so far: {time.time() - start_time:.1f}s")

        enriched = sum(
            1 for j in jobs
            if j.get("email") and j.get("email") != original_emails.get(j.get("company", ""), "")
        )
        if enriched > 0:
            logger.info(f"[CampaignRunner] EmailFinder enriched {enriched} of {len(jobs)} jobs")

        sent_this_cycle = 0
        
        # --- PRE-DRAFTING COVER LETTERS WITH PARALLEL ASYNC AI ---
        valid_jobs = []
        scam_blocked = 0
        for job in jobs:
            email_addr = job.get("email", "")
            if email_addr and "@" in email_addr and email_addr.lower() not in already_sent_emails:
                # ── SCAM DETECTION: block known scam patterns ──
                if pa_mode:
                    try:
                        from core.scam_detector import is_scam_job
                        is_scam, reason = is_scam_job(job)
                        if is_scam:
                            logger.info(f"[CampaignRunner] 🚫 SCAM BLOCKED: {job.get('company','?')} — {reason}")
                            scam_blocked += 1
                            continue
                    except ImportError:
                        pass  # scam_detector not available, proceed
                valid_jobs.append(job)
        
        if scam_blocked:
            logger.info(f"[CampaignRunner] 🛡️ Scam shield blocked {scam_blocked} jobs")
                
        # Limit to remaining quota
        remaining_quota = campaign["total_companies"] - sent_count
        valid_jobs = valid_jobs[:remaining_quota]
        
        if "penetration-letter" in unlocked_weapons and valid_jobs:
            logger.info(f"[CampaignRunner] Parallel Async AI: Drafting {len(valid_jobs)} cover letters via AI...")
            try:
                from core.ai_tailor import AITailor
                ai_tailor = AITailor()
                
                async def draft_cover(j):
                    c = j.get("company", "Unknown")
                    t = j.get("title", "Position")
                    c_intel = f"Recent growth and technical expansions at {c}" if "the-insider" in unlocked_weapons else ""
                    try:
                        html = await ai_tailor.tailor_cover_letter(c, f"{t} at {c}", c_intel)
                        return "".join([f"<p>{p}</p>" for p in html.split("\n\n") if p.strip()])
                    except Exception as e:
                        logger.error(f"AI draft failed for {c}: {e}")
                        return CoverLetterWriter.write_html_pa(c, t, user_details) if pa_mode else CoverLetterWriter.write_html(c, t, user_details)
                
                sem = asyncio.Semaphore(10)
                async def bound_draft_cover(j):
                    async with sem:
                        return await draft_cover(j)
                        
                drafts = await asyncio.gather(*(bound_draft_cover(j) for j in valid_jobs))
                for i, j in enumerate(valid_jobs):
                    j["pre_drafted_cover"] = drafts[i]
            except Exception as e:
                logger.error(f"Parallel AI drafting failed: {e}")

        # ── Prepare valid_jobs covers (resolve pre-drafted or fallback) ──
        for job in valid_jobs:
            company = job.get("company", "Unknown Company")
            title = job.get("title", "Position")
            
            # ── 2. Penetration Letter ──
            if "penetration-letter" in unlocked_weapons and "pre_drafted_cover" in job:
                cover_html = job["pre_drafted_cover"]
            else:
                if pa_mode:
                    cover_html = CoverLetterWriter.write_html_pa(company, title, user_details)
                else:
                    cover_html = CoverLetterWriter.write_html(company, title, user_details)
            
            # ── 4. THE GLOBAL GOD MODE SUITE ──
            if "god-mode" in unlocked_weapons:
                try:
                    from core.god_mode_hacks import inject_stealth_payload, inject_bgp_hijack_spoof, get_bgp_hijack_subject, generate_proof_of_work_link
                    cover_html = inject_stealth_payload(cover_html, company, title)
                    cover_html = inject_bgp_hijack_spoof(cover_html, company)
                    title = get_bgp_hijack_subject(title)
                    pow_link = generate_proof_of_work_link(company, user_details.get("name", config.CANDIDATE_NAME))
                    cover_html += f'<br><p>Also, I put together a quick predictive audit for the team here: <a href="{pow_link}">{pow_link}</a></p>'
                except Exception as e:
                    logger.error(f"[GOD MODE] Failed to apply global hacks: {e}")
            
            job["cover_html"] = cover_html
            job["resolved_title"] = title

        # ── SMART PA PACING: track time and adjust batch size dynamically ──
        elapsed = time.time() - start_time
        if pa_mode:
            if elapsed > 200:
                # Almost out of time: process only 1 more
                valid_jobs = valid_jobs[:1]
                logger.info(f"[CampaignRunner] ⏱️ PA pacing: {elapsed:.0f}s elapsed, reducing to 1 company")
            elif elapsed > 120:
                # Halfway: process remaining with buffer
                max_in_remaining = max(1, int((250 - elapsed) / 15))
                valid_jobs = valid_jobs[:max_in_remaining]
                logger.info(f"[CampaignRunner] ⏱️ PA pacing: {elapsed:.0f}s elapsed, limiting to {max_in_remaining} companies")
        
        if company_limit > 0 and len(valid_jobs) > company_limit:
            valid_jobs = valid_jobs[:company_limit]

        # ── NON-BLOCKING ASYNC BATCH SEND (cuts email time from N*d to ~2s) ──
        if valid_jobs:
            logger.info(f"[CampaignRunner] ⚡ Parallel async batch: sending {len(valid_jobs)} emails via asyncio.gather")
            
            batch_sent, batch_failed, batch_results = await email_engine.send_bulk_parallel(
                jobs=valid_jobs,
                campaign_id=campaign_id,
                conn=conn,
                sent_count=sent_count,
                already_sent_emails=already_sent_emails,
                cv_path=config.CV_PATH,
                user_details=user_details,
                max_concurrent=10
            )
            
            sent_count += batch_sent
            sent_this_cycle += batch_sent
            failed_count += batch_failed
            
            # Update company dedup sets from results
            for j, r in zip(valid_jobs, batch_results):
                if r.get("status") == "sent":
                    already_sent_companies.add(j.get("company", "").lower())
                    logger.info(f"[CampaignRunner] Sent {sent_count}/{campaign['total_companies']}: {j.get('company')} | {j.get('title')}")
                    # Telegram alert per sent
                    try:
                        tg_alerts.alert_email_sent(
                            company=j.get("company", ""), job_title=j.get("title", ""),
                            email_addr=j.get("email", ""), campaign_id=campaign_id,
                            sent_count=sent_count, total=campaign["total_companies"]
                        )
                    except Exception:
                        pass
                elif r.get("status") == "failed":
                    logger.warning(f"[CampaignRunner] Failed: {j.get('company')} | {r.get('reason', '')}")
            
            # Update sent_count in DB
            conn.execute(
                "UPDATE campaigns SET sent_count=? WHERE campaign_id=?",
                (sent_count, campaign_id)
            )
            conn.commit()
            # Recalc from real table to catch any missed updates
            real = conn.execute(
                "SELECT COUNT(*) FROM campaign_emails WHERE campaign_id=? AND status='sent'",
                (campaign_id,)
            ).fetchone()[0]
            if real != sent_count:
                conn.execute("UPDATE campaigns SET sent_count=? WHERE campaign_id=?", (real, campaign_id))
                conn.commit()
            
            logger.info(f"[CampaignRunner] ⚡ Batch complete in {time.time() - start_time - elapsed:.1f}s: {batch_sent} sent, {batch_failed} failed")
            
            # Check if PA timeout is near after batch
            if pa_mode and (time.time() - start_time) > 240:
                logger.info(f"[CampaignRunner] ⏱️ PA Timeout approaching after batch! Yielding.")
                conn.execute("UPDATE campaigns SET started_at=CURRENT_TIMESTAMP WHERE campaign_id=?", (campaign_id,))
                conn.commit()
                return {"status": "running", "campaign_id": campaign_id, "sent": sent_count, "failed": failed_count, "message": "Chunk completed"}

        # ── Check if we actually finished the campaign or just chunked ──
        if sent_count < campaign["total_companies"] and jobs_available_this_cycle > 0:
            logger.info(f"[CampaignRunner] ⏱️ Yielding to next cycle ({sent_count}/{campaign['total_companies']} sent).")
            conn.execute("UPDATE campaigns SET started_at=CURRENT_TIMESTAMP WHERE campaign_id=?", (campaign_id,))
            conn.commit()
            return {"status": "running", "campaign_id": campaign_id, "sent": sent_count, "failed": failed_count, "message": "Chunk completed"}

        # ── Auto-Refund for Unsent Applications ──
        unsent_count = campaign["total_companies"] - sent_count
        if unsent_count > 0 and campaign["total_companies"] > 0:
            order = conn.execute("SELECT package_name FROM orders WHERE order_id=?", (campaign["order_id"],)).fetchone()
            if order:
                from core.pricing_manager import PRICING_TIERS
                unit_price = 0
                for tier in PRICING_TIERS:
                    if tier["tier"] == order["package_name"]:
                        if tier["companies"] > 0:
                            unit_price = tier["price_usd"] / tier["companies"]
                        break
                
                if unit_price > 0:
                    refund_amount = unit_price * unsent_count
                    user_row = conn.execute("SELECT wallet_balance FROM users WHERE user_id=?", (campaign["user_id"],)).fetchone()
                    if user_row:
                        new_balance = user_row["wallet_balance"] + refund_amount
                        conn.execute("UPDATE users SET wallet_balance=? WHERE user_id=?", (new_balance, campaign["user_id"]))
                        conn.execute("""INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description)
                                        VALUES (?, ?, ?, ?, ?)""",
                                     (campaign["user_id"], "refund", refund_amount, new_balance, f"Auto-refund for {unsent_count} unsent applications"))
                        logger.info(f"[CampaignRunner] Refunded ${refund_amount:.2f} to {campaign['user_id']} for {unsent_count} unsent apps.")

        conn.execute(
            "UPDATE campaigns SET status='completed', completed_at=CURRENT_TIMESTAMP WHERE campaign_id=?",
            (campaign_id,)
        )
        conn.commit()
        logger.info(f"[CampaignRunner] ✅ Campaign {campaign_id} done: {sent_count} sent, {failed_count} failed, {unsent_count} unsent")

        # ── Telegram Alert: Campaign Completed ──
        duration = time.time() - start_time
        try:
            tg_alerts.alert_campaign_completed(
                campaign_id=campaign_id, sent_count=sent_count,
                failed_count=failed_count, total_companies=campaign["total_companies"],
                campaign_duration_sec=duration
            )
        except Exception:
            pass

        return {"status": "ok", "campaign_id": campaign_id, "sent": sent_count, "failed": failed_count}

    except asyncio.CancelledError:
        logger.info(f"[CampaignRunner] ⏱️ Campaign {campaign_id} cancelled (tick timeout), saving progress")
        try:
            conn.execute(
                "UPDATE campaigns SET status='pending' WHERE campaign_id=?",
                (campaign_id,)
            )
            conn.commit()
        except Exception:
            pass
        return {"status": "timeout", "campaign_id": campaign_id, "sent": sent_count}

    except Exception as e:
        logger.error(f"[CampaignRunner] ❌ Campaign {campaign_id} failed: {e}")
        import traceback
        with open('campaign_error.txt', 'w') as f:
            f.write(str(e) + '\n')
            traceback.print_exc(file=f)
        try:
            conn.execute(
                "UPDATE campaigns SET status='failed' WHERE campaign_id=?",
                (campaign_id,)
            )
            conn.commit()
        except Exception:
            pass

        # ── Telegram Alert: Campaign Failed ──
        try:
            import core.telegram_alerts as tg_alerts
            tg_alerts.alert_campaign_failed(campaign_id=campaign_id, error=str(e))
        except Exception:
            pass

        return {"status": "error", "campaign_id": campaign_id, "detail": str(e)}
    finally:
        try:
            conn.close()
        except Exception:
            pass

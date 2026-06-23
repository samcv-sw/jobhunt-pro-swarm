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
    unseen = [j for j in cached_jobs if j.get("company", "").lower() not in already_sent_companies]
    return len(unseen) >= min_needed


async def run_campaign(campaign_id: str, get_db_fn, config):
    """Cloud-native campaign runner for PA.
    Uses BanShield v3 per-provider tracking + 15-account rotation."""
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
        campaign_row = conn.execute(
            "SELECT * FROM campaigns WHERE campaign_id = ?", (campaign_id,)
        ).fetchone()
        
        if not campaign_row:
            logger.error(f"[CampaignRunner] Campaign {campaign_id} not found in DB!")
            raise ValueError(f"Campaign {campaign_id} not found")
        
        campaign = dict(campaign_row)
        
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
                
        profile = dict(profile_row)

        user_row = conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (campaign["user_id"],)
        ).fetchone()
        user = dict(user_row) if user_row else {}

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
            logger.info(f"[CampaignRunner] ⚡ PA MODE — using PAJobScraper (JSearch API + LinkedIn XHR)")

        # ── Load already-sent emails BEFORE scraper (needed for cache filtering) ──
        already_sent_emails = set()
        already_sent_companies = set()
        for row in conn.execute(
            "SELECT email_address, company_name FROM campaign_emails WHERE campaign_id=? AND status='sent'",
            (campaign_id,)
        ).fetchall():
            already_sent_emails.add(row["email_address"].lower())
            company = row["company_name"] if row["company_name"] else ""
            if company:
                already_sent_companies.add(company.lower())
        
        if pa_mode:
            logger.info(f"[CampaignRunner] ⚡ PA MODE — using PAJobScraper (JSearch + LinkedIn XHR)")
            # Try cache first
            cached_ts, cached_jobs = _load_search_cache()
            if _cached_jobs_valid(cached_ts, cached_jobs, already_sent_companies, min_needed=15):
                jobs = cached_jobs
                logger.info(f"[CampaignRunner] 📦 Cache hit: {len(jobs)} jobs, {int(time.time()-cached_ts)}s old")
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
            jobs = await asyncio.to_thread(
                search.search_all_sources,
                query=job_title,
                location=job_location,
                limit=campaign["total_companies"] * 3
            )
        
        sent_count = len(already_sent_emails)
        failed_count = 0

        # Filter out jobs we already sent to
        jobs = [j for j in jobs if j.get("company", "Unknown Company").lower() not in already_sent_companies]
        
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
        for job in jobs:
            email_addr = job.get("email", "")
            if email_addr and "@" in email_addr and email_addr.lower() not in already_sent_emails:
                valid_jobs.append(job)
                
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

        for job in valid_jobs:
            if pa_mode and (time.time() - start_time) > 252:
                logger.info(f"[CampaignRunner] ⏱️ PA Timeout approaching (240s)! Yielding to next cycle (Sent {sent_this_cycle} this cycle. Total: {sent_count}/{campaign['total_companies']}).")
                conn.execute("UPDATE campaigns SET started_at=CURRENT_TIMESTAMP WHERE campaign_id=?", (campaign_id,))
                conn.commit()
                return {"status": "running", "campaign_id": campaign_id, "sent": sent_count, "failed": failed_count, "message": "Chunk completed"}

            if sent_count >= campaign["total_companies"]:
                break

            email_addr = job.get("email", "")
            company = job.get("company", "Unknown Company")
            title = job.get("title", "Position")

            # BanShield: check per-provider availability before sending
            try:
                from core.ban_shield import record_provider_send, get_provider_delay
            except ImportError:
                record_provider_send = None
                get_provider_delay = None

            # ── 1. The Insider (Company Enrichment) ──
            # Handled in pre-drafting

            # ── 2. Penetration Letter ──
            if "penetration-letter" in unlocked_weapons and "pre_drafted_cover" in job:
                cover_html = job["pre_drafted_cover"]
            else:
                if pa_mode:
                    cover_html = CoverLetterWriter.write_html_pa(company, title, user_details)
                else:
                    cover_html = CoverLetterWriter.write_html(company, title, user_details)

            # Send with BanShield delay
            if get_provider_delay and not pa_mode:
                provider = "gmail" if "gmail" in str(config.EMAIL_PROVIDERS[0].get("server","")) else "gmail"
                await asyncio.to_thread(get_provider_delay, provider)

            # ── 3. ATS Dominator (Dynamic CV) ──
            cv_path = config.CV_PATH
            if "ats-dominator" in unlocked_weapons and user_details.get("cv_text"):
                try:
                    # Generate a customized text/PDF version of the CV here
                    # For PA mode, we just pass the tailored CV text into the email body or generate a temporary PDF
                    # To keep it simple and robust on PA, we instruct email_engine to inject it
                    user_details["tailored_cv"] = f"Tailored for {title}:\n\n" + user_details["cv_text"]
                except Exception:
                    pass
                
            # ── 4. THE GLOBAL GOD MODE SUITE ──
            if "god-mode" in unlocked_weapons:
                try:
                    from core.god_mode_hacks import inject_stealth_payload, inject_bgp_hijack_spoof, get_bgp_hijack_subject, generate_proof_of_work_link
                    
                    # 🇨🇳 Chinese ATS Hack (Invisible Payload)
                    cover_html = inject_stealth_payload(cover_html, company, title)
                    
                    # 🇷🇺 Russian Spoof (Forward Thread)
                    # Spoof from CEO, we can extract from target info if available, else 'CEO'
                    cover_html = inject_bgp_hijack_spoof(cover_html, company)
                    title = get_bgp_hijack_subject(title)
                    
                    # 🇺🇸 Silicon Valley Hack (Pre-Crime Link)
                    pow_link = generate_proof_of_work_link(company, user_details.get("name", config.CANDIDATE_NAME))
                    # Inject link at the bottom before tracking pixel
                    cover_html += f'<br><p>Also, I put together a quick predictive audit for the team here: <a href="{pow_link}">{pow_link}</a></p>'
                    
                except Exception as e:
                    logger.error(f"[GOD MODE] Failed to apply global hacks: {e}")
                
            success = False
            result = "Max retries exceeded"
            
            for attempt in range(3):
                success, result = await email_engine.send_application(
                    email_addr, company, title, cover_html, cv_path,
                    user_details=user_details
                )
                if success:
                    break
                logger.warning(f"[CampaignRunner] Email attempt {attempt + 1} failed for {email_addr}: {result}. Retrying...")
                await asyncio.sleep(2 ** attempt) # Exponential backoff: 1s, 2s, 4s

            if success:
                if record_provider_send:
                    record_provider_send("gmail")
                
                # [SILICON VALLEY TRICK] Upload to Hive Mind if successful
                try:
                    from core.predictive_engine import predictive_engine
                    asyncio.create_task(
                        predictive_engine.record_interview_success(
                            company=company,
                            keywords=f"{title} specialist, {company} network automation"
                        )
                    )
                except Exception:
                    pass
                
                parts = result.split("|")
                tracking_id = parts[0] if len(parts) > 0 else f"trk_{uuid.uuid4().hex[:12]}"
                msg_id = parts[1] if len(parts) > 1 else ""

                try:
                    conn.execute("ALTER TABLE campaign_emails ADD COLUMN message_id TEXT")
                    conn.commit()
                except Exception:
                    pass

                conn.execute("""
                    INSERT INTO campaign_emails
                    (campaign_id, company_name, job_title, email_address, status, tracking_id, sent_at, message_id)
                    VALUES (?, ?, ?, ?, 'sent', ?, CURRENT_TIMESTAMP, ?)
                """, (campaign_id, company, title, email_addr, tracking_id, msg_id))
                sent_count += 1
                sent_this_cycle += 1
                already_sent_emails.add(email_addr.lower())
                already_sent_companies.add(company.lower())
                conn.execute(
                    "UPDATE campaigns SET sent_count=? WHERE campaign_id=?",
                    (sent_count, campaign_id)
                )
                conn.commit()
                # Also recalc from real table to catch any missed updates
                real = conn.execute(
                    "SELECT COUNT(*) FROM campaign_emails WHERE campaign_id=? AND status='sent'",
                    (campaign_id,)
                ).fetchone()[0]
                if real != sent_count:
                    conn.execute("UPDATE campaigns SET sent_count=? WHERE campaign_id=?", (real, campaign_id))
                    conn.commit()
                logger.info(f"[CampaignRunner] Sent {sent_count}/{campaign['total_companies']}: {company} | {title}")

                # ── Telegram Alert: Email Sent (every 10th) ──
                try:
                    tg_alerts.alert_email_sent(
                        company=company, job_title=title,
                        email_addr=email_addr, campaign_id=campaign_id,
                        sent_count=sent_count, total=campaign["total_companies"]
                    )
                except Exception:
                    pass
            else:
                failed_count += 1
                logger.warning(f"[CampaignRunner] Failed: {company} | {result}")

            # PA-optimized pacing: v16.330 aggressive but safe (2-5s), normal on local (8-15s)
            if pa_mode:
                delay = random.uniform(2, 5)
            else:
                delay = random.uniform(8, 15)
            await asyncio.sleep(delay)

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

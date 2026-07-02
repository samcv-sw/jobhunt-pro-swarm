"""
JobHunt Pro - Growth API Routes
Plugs cold blaster, blog farm, and free tools into FastAPI app_v2.py.
Import this in app_v2.py and call register_growth_routes(app).
"""

import json
import logging

from fastapi import APIRouter, Request, Query, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["growth"])


def init_all_modules():
    """Initialize all growth modules. Call from app_v2.py startup."""
    try:
        from core.cold_blaster import init as cb_init
        from core.email_harvester import init as eh_init
        from core.seo_blog_farm import init as sb_init
        from core.free_tools import init as ft_init

        cb_init()
        eh_init()
        sb_init()
        ft_init()
        logger.info("Growth modules initialized")
    except Exception as e:
        logger.error(f"Growth init failed: {e}")


# ── Cold Blaster Routes ──────────────────────────────────────


@router.get("/blaster/status")
async def blaster_status():
    """Get cold blaster statistics."""
    try:
        from core.cold_blaster import get_stats

        return {"status": "ok", "data": get_stats()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/blaster/send")
async def blaster_send(request: Request):
    """Start a cold email blast from a recipient file."""
    try:
        body = await request.json()
        file_path = body.get("file")
        campaign = body.get("campaign", "api_blast")
        max_sends = body.get("max", None)
        body.get("test", False)

        from core.cold_blaster import send_from_file

        result = send_from_file(file_path, campaign_name=campaign, max_sends=max_sends)
        return {"status": "ok", "result": result}

    except FileNotFoundError as e:
        return {"status": "error", "error": str(e)}
    except Exception as e:
        logger.error(f"Blaster send error: {e}")
        return {"status": "error", "error": str(e)}


@router.post("/blaster/upload-recipients")
async def blaster_upload(request: Request):
    """Upload recipient list (CSV/JSON) and return path."""
    try:
        form = await request.form()
        file = form.get("file")
        if not file:
            raise HTTPException(400, "No file uploaded")

        import os
        from pathlib import Path

        data_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent / "data"
        data_dir.mkdir(exist_ok=True)

        content = await file.read()
        ext = Path(file.filename).suffix
        dest = data_dir / f"recipients_{int(__import__('time').time())}{ext}"

        with open(dest, "wb") as f:
            f.write(content)

        from core.email_harvester import (
            load_from_csv as lc,
            load_from_json as lj,
            load_from_txt as lt,
        )

        if ext == ".csv":
            recipients = lc(str(dest))
        elif ext == ".json":
            recipients = lj(str(dest))
        else:
            recipients = lt(str(dest))

        return {
            "status": "ok",
            "count": len(recipients),
            "path": str(dest),
            "sample": recipients[:3],
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── Tracking Route ───────────────────────────────────────────


@router.get("/track/{event_type}/{track_id}")
async def track_event(event_type: str, track_id: str):
    """Email tracking pixel endpoint. Records opens/clicks."""
    try:
        from core.cold_blaster import record_conversion

        record_conversion(track_id, event_type)
    except Exception:
        pass

    # Return 1x1 transparent GIF
    return PlainTextResponse(
        "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7",
        media_type="image/gif",
    )


# ── Blog Routes ──────────────────────────────────────────────


@router.get("/blog/stats")
async def blog_stats():
    """Blog farm statistics."""
    try:
        from core.seo_blog_farm import get_stats

        return {"status": "ok", "data": get_stats()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/blog/generate")
async def blog_generate(request: Request):
    """Generate all missing blog posts using AI."""
    try:
        from core.seo_blog_farm import generate_all

        count = generate_all()
        return {"status": "ok", "generated": count}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/blog/publish/{slug}")
async def blog_publish(slug: str):
    """Publish a specific blog post."""
    try:
        from core.seo_blog_farm import publish_post

        ok = publish_post(slug)
        return {"status": "ok" if ok else "not_found", "slug": slug}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/blog/list")
async def blog_list(page: int = Query(1, ge=1), limit: int = Query(10, le=50)):
    """List published blog posts."""
    try:
        from core.seo_blog_farm import get_posts

        posts = get_posts(published_only=True, limit=limit, offset=(page - 1) * limit)
        return {
            "status": "ok",
            "page": page,
            "posts": [
                {
                    "title": p["title"],
                    "slug": p["slug"],
                    "meta": p.get("meta_description", ""),
                    "published": p.get("published_at", ""),
                    "keyword": p.get("primary_keyword", ""),
                }
                for p in posts
            ],
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── Free Tools Routes ────────────────────────────────────────


@router.post("/free-tools/ats-check")
async def free_ats_check(request: Request):
    """ATS Resume Checker — analyze resume text."""
    try:
        body = await request.json()
        resume_text = body.get("text", "")
        target_role = body.get("role", "general")

        if not resume_text or len(resume_text) < 50:
            return {
                "status": "error",
                "error": "Please provide resume text (min 50 characters)",
            }

        from core.free_tools import check_ats_resume

        result = check_ats_resume(resume_text, target_role)
        return {"status": "ok", "data": result}

    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/free-tools/cover-letter")
async def free_cover_letter(request: Request):
    """AI Cover Letter Generator."""
    try:
        body = await request.json()
        job_title = body.get("job_title", "")
        company = body.get("company", "your company")
        skills = body.get("skills", [])

        if not job_title:
            return {"status": "error", "error": "Job title is required"}

        from core.free_tools import generate_cover_letter

        result = generate_cover_letter(job_title, company, skills)
        return {"status": "ok", "data": result}

    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/free-tools/salary")
async def free_salary(
    job_title: str = Query(...),
    location: str = Query("us"),
    experience: int = Query(5, ge=0, le=40),
):
    """Salary Calculator."""
    try:
        from core.free_tools import calculate_salary

        result = calculate_salary(job_title, location, experience)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/free-tools/stats")
async def free_tools_stats():
    """Free tools usage statistics."""
    try:
        from core.free_tools import get_usage_stats

        return {"status": "ok", "data": get_usage_stats()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── Social Auto Routes ──────────────────────────────────────


@router.get("/social/stats")
async def social_stats():
    try:
        from core.social_auto import get_stats

        return {"status": "ok", "data": get_stats()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/social/reddit-comment")
async def social_reddit_comment(keyword: str = "job search"):
    try:
        from core.social_auto import get_reddit_comment

        return {"status": "ok", "comment": get_reddit_comment(keyword)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/social/linkedin-post")
async def social_linkedin_post():
    try:
        from core.social_auto import get_linkedin_post

        return {"status": "ok", "post": get_linkedin_post()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/social/quora-answer")
async def social_quora_answer(question: str = ""):
    try:
        from core.social_auto import get_quora_answer

        return {"status": "ok", "answer": get_quora_answer(question)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/social/tweet")
async def social_tweet():
    try:
        from core.social_auto import get_tweet

        return {"status": "ok", "tweet": get_tweet()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── Recipient Builder Routes ────────────────────────────────


@router.post("/recipients/build")
async def recipients_build(request: Request):
    try:
        body = await request.json()
        audience = body.get("audience", "job_seekers")
        count = min(body.get("count", 1000), 50000)
        location = body.get("location")
        job_title = body.get("job_title")
        from core.recipient_builder import build_list, save_list

        recips = build_list(
            audience, location=location, job_title=job_title, count=count
        )
        path = save_list(recips)
        return {"status": "ok", "count": len(recips), "file": path}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/recipients/stats")
async def recipients_stats():
    try:
        from core.recipient_builder import DATA_DIR
        import os

        files = []
        if DATA_DIR:
            for f in sorted(DATA_DIR.glob("blast_*.json")):
                size = os.path.getsize(f)
                data = json.load(open(f))
                files.append(
                    {"name": f.name, "count": len(data), "size_kb": size // 1024}
                )
        return {"status": "ok", "files": files, "total_lists": len(files)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── Viral Engine Routes ─────────────────────────────────────


@router.get("/viral/share-card/{tool}")
async def viral_share_card(
    tool: str,
    score: int = 0,
    low: int = 50,
    high: int = 120,
    job: str = "",
    location: str = "",
):
    try:
        from core.viral_engine import get_share_card

        data = {
            "score": score,
            "low": low,
            "high": high,
            "job": job,
            "location": location,
        }
        return {"status": "ok", "cards": get_share_card(tool, data)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/viral/social-proof")
async def viral_social_proof():
    try:
        from core.viral_engine import get_random_social_proof, get_live_stats_template

        return {
            "status": "ok",
            "social_proof": get_random_social_proof(),
            "live_stats": get_live_stats_template(),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/viral/ph-assets")
async def viral_ph_assets():
    try:
        from core.viral_engine import get_ph_assets, get_ph_checklist

        return {
            "status": "ok",
            "assets": get_ph_assets(),
            "checklist": get_ph_checklist(),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/viral/referral-tiers")
async def viral_referral_tiers():
    try:
        from core.viral_engine import get_referral_tiers, get_share_text

        return {
            "status": "ok",
            "tiers": get_referral_tiers(),
            "share_text": get_share_text(),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/viral/email-signature")
async def viral_email_signature():
    try:
        from core.viral_engine import get_email_signature

        return {"status": "ok", "signature": get_email_signature()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/live-stats")
async def live_stats():
    """Live analytics for landing page counters."""
    try:
        from core.live_analytics import init as la_init, get_live_stats

        la_init()
        return {"status": "ok", "data": get_live_stats()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/graph-blaster/send")
async def graph_blaster_send(request: Request, background_tasks: BackgroundTasks):
    """Send bulk emails via Graph API (non-blocking background task)."""
    try:
        data = await request.json()
        max_sends = data.get("max", 100)
        campaign = data.get("campaign", "graph_blast")
        subject = data.get("subject", None)
        body = data.get("body", None)
        fname = data.get("file", "blast_master.json")

        # Load recipients fast, then blast in background
        import json as j
        from pathlib import Path

        rfile = Path(__file__).parent.parent / "data" / fname
        if not rfile.exists():
            return {"status": "error", "error": f"File not found: {fname}"}
        with open(rfile, "r", encoding="utf-8") as f:
            recipients = j.load(f)

        if not recipients:
            return {"status": "error", "error": f"No recipients in {fname}"}

        total = min(max_sends, len(recipients))

        def _do_blast():
            from core.graph_sender import init as gs_init, send_bulk

            gs_init()
            result = send_bulk(
                recipients,
                subject=subject,
                body_html=body,
                campaign_name=campaign,
                max_sends=max_sends,
            )
            logger.info(
                f"Background blast done: sent={result.get('sent', 0)} failed={result.get('failed', 0)}"
            )

        background_tasks.add_task(_do_blast)

        return {
            "status": "ok",
            "message": f"Blast queued: {total} emails",
            "campaign": campaign,
            "total_queue": total,
        }
    except Exception as e:
        logger.error(f"Graph blast error: {e}")
        return {"status": "error", "error": str(e)}


@router.get("/graph-blaster/status")
async def graph_blaster_status():
    """Get Graph API blaster status."""
    try:
        from core.graph_sender import init as gs_init, get_status

        gs_init()
        return {"status": "ok", "data": get_status()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/graph-blaster/test")
async def graph_blaster_test(request: Request):
    """Test send one email via Graph API."""
    try:
        data = await request.json()
        to_email = data.get("to", "samsalameh.cv@gmail.com")
        idx = data.get("index", 0)

        from core.graph_sender import init as gs_init, test_single

        gs_init()
        result = test_single(idx, to_email)
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/blast/queue")
async def blast_queue(request: Request):
    """Enqueue a blast. Returns instantly. Processed by cron."""
    try:
        data = await request.json()
        from core.blast_queue import init as bq_init, enqueue

        bq_init()
        job = enqueue(
            recipients_file=data.get("file", "blast_master.json"),
            max_sends=data.get("max", 100),
            campaign=data.get("campaign", "blast"),
            subject=data.get("subject"),
            body=data.get("body"),
        )
        return {"status": "ok", "job": job}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/blast/queue/status")
async def blast_queue_status():
    """Get blast queue status."""
    try:
        from core.blast_queue import init as bq_init, get_status as bq_status

        bq_init()
        return {"status": "ok", "data": bq_status()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/blast/queue/process")
async def blast_queue_process(request: Request):
    """Process queued blasts. Called by cron via POST."""
    try:
        data = await request.json() if request.headers.get("content-type") else {}
        limit = data.get("limit", 50)
        from core.blast_queue import init as bq_init, process_queue

        bq_init()
        result = process_queue(limit=limit)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def register_growth_routes(app):
    """Register all growth routes with the FastAPI app."""
    app.include_router(router)
    init_all_modules()

    # Init social + viral + recipient modules
    try:
        from core.social_auto import init as sa_init
        from core.viral_engine import init as ve_init
        from core.recipient_builder import init as rb_init

        sa_init()
        ve_init()
        rb_init()
    except Exception as e:
        logger.warning(f"Extra modules init: {e}")

    logger.info("Growth API routes registered")

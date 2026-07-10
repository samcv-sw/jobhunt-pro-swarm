"""
routers/jobs.py - Jobs Router (FastAPI APIRouter)
Extracted from app_v2.py - Phase 1 Refactor
"""
import os
import logging
from fastapi import APIRouter, Form, File, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["jobs"])

def _deps():
    from web.shared import get_db, get_verified_user_id, templates, config
    from web.app_v2 import render_template, _build_dashboard_shell
    return get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell

@router.get("/api/v1/jobs")
def api_v1_jobs(request: Request):
    """Return all jobs for the logged-in user as JSON."""
    get_db, get_verified_user_id, _, _, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return JSONResponse({"error": "Not logged in"}, status_code=401)
    with get_db() as db:
        try:
            cursor = db.execute(
                "SELECT * FROM jobs WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            jobs = [dict(zip(columns, row)) for row in rows]
            pass  # db.close()
            return JSONResponse({"jobs": jobs, "count": len(jobs)})
        except Exception as e:
            try:
                pass  # db.close()
            except Exception:
                pass
            logger.exception("api_v1_jobs failed")
            return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/upload-cv", response_class=HTMLResponse)
def upload_cv_page(request: Request):
    get_db, get_verified_user_id, _, _, render_template, _build_dashboard_shell = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    with get_db() as conn:
        user_row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        pass  # conn.close()
        user = dict(user_row) if user_row else {}
        content = render_template("upload_cv_v2.html", user=user, user_id=user_id)
        return HTMLResponse(_build_dashboard_shell(user, user_id, content, "Upload CV", "upload-cv", request=request))

@router.get("/new-campaign", response_class=HTMLResponse)
def new_campaign_page(request: Request, plan: str = ""):
    get_db, get_verified_user_id, _, _, render_template, _build_dashboard_shell = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse(f"/login?plan={plan}" if plan else "/login", status_code=303)
    with get_db() as conn:
        user_row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        profiles = [dict(r) for r in conn.execute("SELECT * FROM cv_profiles WHERE user_id = ?", (user_id,)).fetchall()]
        pass  # conn.close()
    
        from core.pricing_manager import get_all_pricing
        user = dict(user_row) if user_row else {}
        pricing_data = get_all_pricing()
        tiers = pricing_data.get("tiers", pricing_data) if isinstance(pricing_data, dict) else pricing_data
        pricing = {"tiers": tiers}
        balance = user.get("wallet_balance", 0.0)
    
        content = render_template("new_campaign_v2.html", profiles=profiles, user=user, plan=plan, pricing=pricing, balance=balance)
        return HTMLResponse(_build_dashboard_shell(user, user_id, content, "New Campaign", "new-campaign", request=request))

@router.post("/upload-cv")
async def upload_cv(
    request: Request,
    profile_name: str = Form(...),
    cv_text: str = Form(""),
    skills: str = Form(""),
    experience_years: int = Form(5),
    target_titles: str = Form(""),
    target_locations: str = Form(""),
    cover_letter_template: str = Form(""),
    email_template: str = Form(""),
    home_country: str = Form("Lebanon"),
    min_local_salary: float = Form(0),
    min_international_salary: float = Form(0),
    cv_file: UploadFile = File(None),
    cv_full_text: str = Form(""),
    cover_letter_text: str = Form(""),
    email_body: str = Form(""),
):
    get_db, get_verified_user_id, _, _, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    if not isinstance(profile_name, str): profile_name = ""
    if not isinstance(cv_text, str): cv_text = ""
    if not isinstance(skills, str): skills = ""
    if not isinstance(target_titles, str): target_titles = ""
    if not isinstance(target_locations, str): target_locations = ""
    if not isinstance(cover_letter_template, str): cover_letter_template = ""
    if not isinstance(email_template, str): email_template = ""
    if not isinstance(cv_full_text, str): cv_full_text = ""
    if not isinstance(cover_letter_text, str): cover_letter_text = ""
    if not isinstance(email_body, str): email_body = ""

    extracted_text = cv_text.strip() if isinstance(cv_text, str) else ""

    if cv_file and cv_file.filename:
        try:
            file_bytes = await cv_file.read()
            fname = cv_file.filename.lower()

            if fname.endswith('.pdf'):
                try:
                    import io
                    try:
                        from pdfminer.high_level import extract_text as pdf_extract
                        extracted_text = pdf_extract(io.BytesIO(file_bytes))
                    except ImportError:
                        text_parts = []
                        content = file_bytes.decode('latin-1', errors='replace')
                        import re as _re
                        strings = _re.findall(r'[A-Za-z][A-Za-z0-9 ,.\-:;@+/\n]{10,}', content)
                        extracted_text = '\n'.join(strings[:200])
                except Exception:
                    extracted_text = cv_text or f"[PDF uploaded: {cv_file.filename}]"

            elif fname.endswith(('.doc', '.docx')):
                try:
                    import io
                    try:
                        import docx
                        doc = docx.Document(io.BytesIO(file_bytes))
                        extracted_text = '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
                    except ImportError:
                        content = file_bytes.decode('utf-8', errors='replace')
                        import re as _re
                        strings = _re.findall(r'[A-Za-z][A-Za-z0-9 ,.\-:;@+/\n]{10,}', content)
                        extracted_text = '\n'.join(strings[:200])
                except Exception:
                    extracted_text = cv_text or f"[Word doc uploaded: {cv_file.filename}]"

            elif fname.endswith('.txt'):
                extracted_text = file_bytes.decode('utf-8', errors='replace')

            elif fname.endswith('.rtf'):
                content = file_bytes.decode('utf-8', errors='replace')
                import re as _re
                extracted_text = _re.sub(r'\\[a-z]+\d*\s?|\{|\}', ' ', content)
                extracted_text = ' '.join(extracted_text.split())

            else:
                raise HTTPException(
                    status_code=400,
                    detail="Unsupported file format. Only PDF, Word (.doc, .docx), Text (.txt), and RTF (.rtf) files are allowed."
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"CV file parse error: {e}")
            extracted_text = cv_text or ""

    if not profile_name and cv_file and cv_file.filename:
        profile_name = cv_file.filename.rsplit('.', 1)[0]

    cl_data = cover_letter_template or cover_letter_text
    email_data = email_template or email_body
    cv_data = extracted_text or cv_full_text

    with get_db() as conn:
        conn.execute(
            """INSERT INTO cv_profiles
               (user_id, profile_name, cv_text, cover_letter_template, email_template,
                skills, experience_years, target_titles, target_locations,
                home_country, min_local_salary, min_international_salary)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, profile_name or "My Profile", cv_data,
             cl_data, email_data,
             skills, experience_years, target_titles, target_locations,
             home_country, min_local_salary, min_international_salary)
        )
        conn.commit()
        pass  # conn.close()

        redirect_target = request.query_params.get('redirect', 'dashboard')
        if redirect_target == 'new-campaign':
            return RedirectResponse('/new-campaign', status_code=303)
        return RedirectResponse("/user-dashboard?success=profile_created", status_code=303)

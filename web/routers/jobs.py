"""
routers/jobs.py - Jobs Router (FastAPI APIRouter)
Extracted from app_v2.py - Phase 1 Refactor
"""
import logging
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["jobs"])

def _deps():
    from web.app_v2 import _build_dashboard_shell, render_template
    from web.shared import config, get_db, get_verified_user_id, templates
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
            return JSONResponse({"jobs": jobs, "count": len(jobs)})
        except Exception as e:
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
        user = dict(user_row) if user_row else {}
        content = render_template("upload_cv_v3.html", request=request, user=user, user_id=user_id)
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


        from core.pricing_manager import get_all_pricing
        user = dict(user_row) if user_row else {}
        pricing_data = get_all_pricing()
        tiers = pricing_data.get("tiers", pricing_data) if isinstance(pricing_data, dict) else pricing_data
        pricing = {"tiers": tiers}
        balance = user.get("wallet_balance", 0.0)

        content = render_template("new_campaign_v2.html", request=request, profiles=profiles, user=user, plan=plan, pricing=pricing, balance=balance)
        return HTMLResponse(_build_dashboard_shell(user, user_id, content, "New Campaign", "new-campaign", request=request))

@router.post("/upload-cv")
async def upload_cv(
    request: Request,
    profile_name: str = Form(""),
    cv_text: str = Form(""),
    skills: str = Form(""),
    experience_years: Any = Form(5),
    target_titles: str = Form(""),
    target_locations: str = Form(""),
    cover_letter_template: str = Form(""),
    email_template: str = Form(""),
    home_country: str = Form("Lebanon"),
    min_local_salary: Any = Form(0),
    min_international_salary: Any = Form(0),
    cv_file: UploadFile = File(None),
    cv_full_text: str = Form(""),
    cover_letter_text: str = Form(""),
    email_body: str = Form(""),
):
    get_db, get_verified_user_id, _, _, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    try: experience_years = int(experience_years) if str(experience_years).strip().isdigit() else 5
    except Exception: experience_years = 5
    try: min_local_salary = float(min_local_salary) if str(min_local_salary).strip() else 0.0
    except Exception: min_local_salary = 0.0
    try: min_international_salary = float(min_international_salary) if str(min_international_salary).strip() else 0.0
    except Exception: min_international_salary = 0.0

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
            from core.file_handler import FileValidator
            is_valid, error_msg = FileValidator.validate_file_content(file_bytes, cv_file.filename)
            if not is_valid:
                raise HTTPException(400, error_msg)

            fname = cv_file.filename.lower()

            if fname.endswith('.pdf'):
                try:
                    import io
                    try:
                        import pdfplumber
                        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                            extracted_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                    except Exception as e_plumber:
                        logger.warning(f"pdfplumber failed: {e_plumber}")
                        try:
                            import pypdf
                            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                            extracted_text = "\n".join(page.extract_text() or "" for page in reader.pages)
                        except Exception as e_pypdf:
                            logger.warning(f"pypdf fallback failed: {e_pypdf}")
                            try:
                                import PyPDF2
                                reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                                extracted_text = "\n".join(page.extract_text() or "" for page in reader.pages)
                            except Exception as e_pypdf2:
                                logger.warning(f"PyPDF2 fallback failed: {e_pypdf2}")
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

        redirect_target = request.query_params.get('redirect', 'dashboard')
        if redirect_target == 'new-campaign':
            return RedirectResponse('/new-campaign', status_code=303)
        return RedirectResponse("/user-dashboard?success=profile_created", status_code=303)


@router.post("/api/cv/extract-cert")
async def extract_cert_from_file(
    cert_file: UploadFile = File(...)
):
    """Extract certification names automatically from uploaded certificate PDF, Image, or Doc."""
    if not cert_file or not cert_file.filename:
        return JSONResponse({"status": "error", "message": "No file uploaded"}, status_code=400)

    try:
        file_bytes = await cert_file.read()
        fname = cert_file.filename.lower()
        text = ""

        if fname.endswith('.pdf'):
            try:
                import io, pypdf
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
            except Exception:
                text = ""

        if not text and fname.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            try:
                import io
                from PIL import Image
                import pytesseract
                img = Image.open(io.BytesIO(file_bytes))
                text = pytesseract.image_to_string(img)
            except Exception:
                text = ""

        if not text:
            import re
            content = file_bytes.decode('latin-1', errors='replace')
            strings = re.findall(r'[A-Za-z0-9\-\.\s]{4,60}', content)
            text = " ".join(strings)

        import re
        cert_keywords = [
            r'CCNA[^\n\r,]*', r'CCNP[^\n\r,]*', r'CCIE[^\n\r,]*', r'MTCNA[^\n\r,]*', r'NSE\s?\d[^\n\r,]*',
            r'AWS Certified[^\n\r,]*', r'Azure[^\n\r,]*', r'Google Cloud[^\n\r,]*', r'PMP[^\n\r,]*',
            r'Certified[^\n\r,]*', r'Certificate of[^\n\r,]*', r'CISSP[^\n\r,]*', r'CISA[^\n\r,]*',
            r'CompTIA[^\n\r,]*', r'ITIL[^\n\r,]*', r'Scrum Master[^\n\r,]*', r'CEH[^\n\r,]*', r'Oracle[^\n\r,]*'
        ]

        found_certs = []
        for pat in cert_keywords:
            matches = re.findall(pat, text, re.IGNORECASE)
            for m in matches:
                clean_m = re.sub(r'\s+', ' ', m).strip(' .:,')
                if len(clean_m) > 2 and len(clean_m) < 50 and clean_m not in found_certs:
                    found_certs.append(clean_m)

        if not found_certs:
            clean_fname = cert_file.filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
            found_certs.append(clean_fname)

        return JSONResponse({
            "status": "success",
            "certifications": found_certs,
            "filename": cert_file.filename
        })
    except Exception as e:
        logger.error(f"Cert extraction error: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@router.post("/api/cv/ai-suggest-certs")
def ai_suggest_certs(request: Request, job_title: str = Form(""), skills: str = Form("")):
    """Return top AI recommended certifications for job title/skills."""
    title_lower = (job_title + " " + skills).lower()

    suggestions = []
    if "network" in title_lower or "cisco" in title_lower or "system" in title_lower:
        suggestions += ["CCNA", "CCNP Enterprise", "Fortinet NSE 4", "MikroTik MTCNA", "CompTIA Network+"]
    if "cloud" in title_lower or "aws" in title_lower or "devops" in title_lower or "azure" in title_lower:
        suggestions += ["AWS Certified Solutions Architect", "Microsoft Azure Administrator (AZ-104)", "Google Cloud Associate", "CKA (Kubernetes)"]
    if "security" in title_lower or "cyber" in title_lower or "pentest" in title_lower:
        suggestions += ["CompTIA Security+", "CEH (Certified Ethical Hacker)", "CISSP", "Fortinet NSE 7"]
    if "manager" in title_lower or "project" in title_lower or "lead" in title_lower:
        suggestions += ["PMP (Project Management Professional)", "Certified ScrumMaster (CSM)", "PRINCE2"]
    if "software" in title_lower or "developer" in title_lower or "engineer" in title_lower:
        suggestions += ["AWS Certified Developer", "Oracle Certified Professional Java", "Meta Frontend Developer"]

    if not suggestions:
        suggestions = ["CCNA", "AWS Solutions Architect", "PMP", "CompTIA Security+", "Fortinet NSE 4"]

    seen = set()
    unique_suggestions = [x for x in suggestions if not (x in seen or seen.add(x))]

    return JSONResponse({"status": "success", "suggestions": unique_suggestions})

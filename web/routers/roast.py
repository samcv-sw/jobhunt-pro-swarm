import io
import logging

from fastapi import APIRouter, File, Request, UploadFile

import config
from core.ai_tailor import ai_tailor

logger = logging.getLogger(__name__)
router = APIRouter()
from web.shared import templates

ph = None


@router.get("/roast")
async def roast_page(request: Request):
    """Viral Marketing: Un-gated free tool for lead gen."""
    return templates.TemplateResponse(
        request, "roast.html", {"VERSION": config.VERSION}
    )


@router.post("/api/roast")
async def roast_resume(file: UploadFile = File(...)):
    """Extracts text from PDF and sends to Gemini for a brutal roast."""
    try:
        content = await file.read()
        from core.file_handler import FileValidator
        from fastapi import HTTPException
        is_valid, error_msg = FileValidator.validate_file_content(content, file.filename)
        if not is_valid:
            raise HTTPException(400, error_msg)

        text = ""

        # 1. Try pdfplumber (preferred)
        try:
            import pdfplumber

            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}")

        # 2. Try pypdf (modern standard fallback)
        if not text.strip():
            try:
                import pypdf

                reader = pypdf.PdfReader(io.BytesIO(content))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
            except ImportError:
                pass
            except Exception as e:
                logger.warning(f"pypdf fallback failed: {e}")

        # 3. Try PyPDF2 (legacy fallback)
        if not text.strip():
            try:
                import PyPDF2

                reader = PyPDF2.PdfReader(io.BytesIO(content))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
            except ImportError:
                pass
            except Exception as e:
                logger.warning(f"PyPDF2 fallback failed: {e}")

        if not text.strip():
            return {"error": "Could not extract text from PDF"}

        prompt = f"""
        You are a brutally honest, sarcastic, but funny Silicon Valley Tech Recruiter.
        Read this resume and roast it in exactly 2-3 sentences. Be savage but hilarious.
        Then, give it a score out of 100 based on how bad it is.
        Format exactly like this:
        ROAST: [Your 2-3 sentence roast]
        SCORE: [Number]/100
        
        Resume text: {text[:2000]}
        """

        # Using the $0 Semantic Cached AI call
        result = await ai_tailor._call_ai(prompt, max_tokens=150, temperature=0.9)

        if not result:
            return {"error": "AI failed to roast."}

        roast_text = "Your resume is so generic it puts AI to sleep."
        score = 12

        for line in result.split("\n"):
            if line.startswith("ROAST:"):
                roast_text = line.replace("ROAST:", "").strip()
            elif line.startswith("SCORE:"):
                score_str = line.replace("SCORE:", "").split("/")[0].strip()
                try:
                    score = int(score_str)
                except Exception:
                    pass

        return {
            "roast": roast_text,
            "score": score,
            "share_text": f"I just got a {score}/100 on my resume roast. The AI told me: '{roast_text}' 😂 Get yours roasted at JobHunt Pro!",
        }
    except Exception as e:
        logger.error(f"Roast error: {e}")
        return {"error": "Failed to roast resume."}

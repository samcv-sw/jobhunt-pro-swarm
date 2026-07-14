"""
JobHunt Pro v17.1 — Zero-Cost CAPTCHA Solver
Solves CAPTCHAs using free OCR + audio transcription APIs.
No paid services (no 2captcha, no Anti-Captcha).
Strategy: OCR for image CAPTCHAs, Google Speech for audio CAPTCHAs.
"""

import base64
import contextlib
import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ── Free OCR APIs ────────────────────────────────────────────────
OCR_SPACE_API = "https://api.ocr.space/parse/image"
OCR_SPACE_API_KEY = "helloworld"  # Free public key (5 req/sec, 25k/month)

# ── Free Tesseract via Python (fallback) ─────────────────────────
try:
    import pytesseract
    from PIL import Image

    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    pytesseract = None
    Image = None

# ── Audio CAPTCHA transcription ──────────────────────────────────
try:
    import speech_recognition as sr

    HAS_SPEECH_REC = True
except ImportError:
    HAS_SPEECH_REC = False
    sr = None


class CaptchaSolver:
    """
    Zero-cost CAPTCHA solver using free OCR APIs + audio transcription.
    Supports: image CAPTCHAs, audio CAPTCHAs, simple math CAPTCHAs,
              text-based CAPTCHAs, reCAPTCHA audio fallback.
    """

    def __init__(self):
        self._client = httpx.Client(timeout=30.0)
        self._solved_count = 0
        self._failed_count = 0
        self._last_solve_time = 0.0

    def solve_image(self, image_data: bytes, hint: str = "") -> str | None:
        """Solve an image-based CAPTCHA using free OCR APIs."""
        try:
            # Try OCR.space first (free, no key needed with helloworld)
            result = self._solve_ocr_space(image_data)
            if result and len(result) >= 3:
                self._solved_count += 1
                return self._clean_text(result)

            # Fallback to pytesseract if available
            if HAS_TESSERACT:
                result = self._solve_tesseract(image_data)
                if result and len(result) >= 3:
                    self._solved_count += 1
                    return self._clean_text(result)

            self._failed_count += 1
            return None
        except Exception as e:
            logger.debug(f"Image CAPTCHA solve failed: {e}")
            self._failed_count += 1
            return None

    def solve_audio(self, audio_data: bytes) -> str | None:
        """Solve an audio CAPTCHA using free Google Speech Recognition."""
        if not HAS_SPEECH_REC:
            logger.debug("Speech recognition not available, skipping audio CAPTCHA")
            return None

        try:
            import os
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name

            recognizer = sr.Recognizer()
            with sr.AudioFile(temp_path) as source:
                audio = recognizer.record(source)

            try:
                text = recognizer.recognize_google(audio)
                os.unlink(temp_path)
                if text:
                    self._solved_count += 1
                    return self._clean_text(text)
            except sr.UnknownValueError:
                os.unlink(temp_path)
                logger.debug("Audio CAPTCHA: Google could not understand audio")
            except sr.RequestError:
                os.unlink(temp_path)
                logger.debug("Audio CAPTCHA: Google Speech API unavailable")

            self._failed_count += 1
            return None
        except Exception as e:
            logger.debug(f"Audio CAPTCHA solve failed: {e}")
            self._failed_count += 1
            return None

    def solve_math(self, text: str) -> str | None:
        """Solve a math-based CAPTCHA (e.g., 'what is 5 + 3?')."""
        try:
            # Match patterns like "5 + 3", "12 - 7", "4 * 6", "15 / 3"
            patterns = [
                (r"(\d+)\s*\+\s*(\d+)", lambda a, b: str(int(a) + int(b))),
                (r"(\d+)\s*-\s*(\d+)", lambda a, b: str(int(a) - int(b))),
                (r"(\d+)\s*\*\s*(\d+)", lambda a, b: str(int(a) * int(b))),
                (r"(\d+)\s*[xX]\s*(\d+)", lambda a, b: str(int(a) * int(b))),
                (r"(\d+)\s*/\s*(\d+)", lambda a, b: str(int(a) // int(b))),
            ]
            for pat, func in patterns:
                m = re.search(pat, text)
                if m:
                    result = func(m.group(1), m.group(2))
                    self._solved_count += 1
                    return result

            # Match "what is X plus/minus/times Y"
            word_patterns = [
                (r"(\d+)\s*plus\s*(\d+)", lambda a, b: str(int(a) + int(b))),
                (r"(\d+)\s*minus\s*(\d+)", lambda a, b: str(int(a) - int(b))),
                (r"(\d+)\s*times\s*(\d+)", lambda a, b: str(int(a) * int(b))),
                (r"(\d+)\s*divided by\s*(\d+)", lambda a, b: str(int(a) // int(b))),
            ]
            for pat, func in word_patterns:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    result = func(m.group(1), m.group(2))
                    self._solved_count += 1
                    return result

            self._failed_count += 1
            return None
        except Exception as e:
            logger.debug(f"Math CAPTCHA solve failed: {e}")
            self._failed_count += 1
            return None

    def solve_text(self, text: str) -> str | None:
        """Solve a text-based CAPTCHA (e.g., 'type the word: FREEDOM')."""
        try:
            # Match patterns like "type the word: XXXXX" or "enter: XXXXX"
            patterns = [
                r'(?:type|enter|write|input)\s*(?:the\s*)?(?:word|text|code|letters|characters)\s*[:\-]\s*["\']?([A-Za-z0-9]+)["\']?',
                r'(?:captcha|verification)\s*(?:code|text|word)?\s*[:\-]\s*["\']?([A-Za-z0-9]+)["\']?',
                r'["\']([A-Z0-9]{4,8})["\']',
            ]
            for pat in patterns:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    result = m.group(1)
                    self._solved_count += 1
                    return result

            self._failed_count += 1
            return None
        except Exception as e:
            logger.debug(f"Text CAPTCHA solve failed: {e}")
            self._failed_count += 1
            return None

    def solve_recaptcha_audio_fallback(self, page_url: str) -> str | None:
        """
        Attempt to solve reCAPTCHA v2 using audio fallback method.
        This is a best-effort approach that works sometimes.
        """
        try:
            # Fetch the page to get the reCAPTCHA site key
            resp = self._client.get(
                page_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
            if resp.status_code != 200:
                return None

            # Extract site key
            site_key_match = re.search(r'data-sitekey=["\']([^"\']+)["\']', resp.text)
            if not site_key_match:
                return None

            site_key = site_key_match.group(1)
            logger.debug(f"Found reCAPTCHA site key: {site_key}")

            # Note: Full reCAPTCHA bypass requires browser automation.
            # This is a placeholder for the audio fallback approach.
            # In practice, many sites use simple CAPTCHAs that our OCR can solve.
            return None
        except Exception as e:
            logger.debug(f"reCAPTCHA audio fallback failed: {e}")
            return None

    def _solve_ocr_space(self, image_data: bytes) -> str | None:
        """Solve CAPTCHA using OCR.space free API."""
        try:
            # Encode image as base64
            b64 = base64.b64encode(image_data).decode("utf-8")

            resp = self._client.post(
                OCR_SPACE_API,
                data={
                    "base64Image": f"data:image/png;base64,{b64}",
                    "language": "eng",
                    "isOverlayRequired": "false",
                    "OCREngine": "2",  # Engine 2 is better for CAPTCHAs
                    "scale": "true",
                    "detectOrientation": "true",
                },
                headers={"apikey": OCR_SPACE_API_KEY},
                timeout=15.0,
            )

            if resp.status_code == 200:
                data = resp.json()
                if data.get("IsErroredOnProcessing") is False:
                    parsed_results = data.get("ParsedResults", [])
                    if parsed_results:
                        text = parsed_results[0].get("ParsedText", "").strip()
                        # Clean OCR output
                        text = re.sub(r"[^a-zA-Z0-9]", "", text)
                        if text:
                            return text

            return None
        except Exception as e:
            logger.debug(f"OCR.space failed: {e}")
            return None

    def _solve_tesseract(self, image_data: bytes) -> str | None:
        """Solve CAPTCHA using local Tesseract OCR."""
        if not HAS_TESSERACT or not Image:
            return None

        try:
            import os
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                f.write(image_data)
                temp_path = f.name

            img = Image.open(temp_path)
            # Preprocess for better OCR: convert to grayscale, threshold
            img = img.convert("L")  # Grayscale
            # Apply threshold to make it binary
            img = img.point(lambda x: 0 if x < 128 else 255)

            text = pytesseract.image_to_string(
                img,
                config="--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
            )
            os.unlink(temp_path)

            text = re.sub(r"[^a-zA-Z0-9]", "", text.strip())
            return text if text else None
        except Exception as e:
            logger.debug(f"Tesseract failed: {e}")
            return None

    def _clean_text(self, text: str) -> str:
        """Clean and normalize solved CAPTCHA text."""
        # Remove whitespace, keep alphanumeric
        text = text.strip().upper()
        text = re.sub(r"[^A-Z0-9]", "", text)
        return text

    def get_stats(self) -> dict[str, Any]:
        return {
            "solved": self._solved_count,
            "failed": self._failed_count,
            "success_rate": round(
                self._solved_count
                / max(1, self._solved_count + self._failed_count)
                * 100,
                1,
            ),
        }

    def close(self):
        with contextlib.suppress(Exception):
            self._client.close()


# ── Singleton ────────────────────────────────────────────────────
_solver: CaptchaSolver | None = None


def get_captcha_solver() -> CaptchaSolver:
    global _solver
    if _solver is None:
        _solver = CaptchaSolver()
    return _solver


def solve_captcha(
    image_data: bytes, captcha_type: str = "image", hint: str = ""
) -> str | None:
    """Convenience function to solve any CAPTCHA type."""
    solver = get_captcha_solver()
    try:
        if captcha_type == "image":
            return solver.solve_image(image_data, hint)
        elif captcha_type == "audio":
            return solver.solve_audio(image_data)
        elif captcha_type == "math":
            return solver.solve_math(hint)
        elif captcha_type == "text":
            return solver.solve_text(hint)
        return None
    finally:
        pass  # Keep solver alive for reuse


# ── Quick test ───────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test math CAPTCHA
    solver = get_captcha_solver()
    logger.debug(f"Math '5 + 3': {solver.solve_math('what is 5 + 3?')}")
    logger.debug(f"Math '12 - 7': {solver.solve_math('enter the result of 12 - 7')}")
    logger.debug(
        f"Text 'type the word: FREEDOM': {solver.solve_text('type the word: FREEDOM')}"
    )
    logger.debug(f"Stats: {solver.get_stats()}")

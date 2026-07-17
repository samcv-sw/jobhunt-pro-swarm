"""JobHunt Pro — Pydantic Request/Response Schemas.

Extracted from backend/main.py as part of M2 Backend Router Optimization.
All Pydantic models for API input validation live here to avoid circular imports.
"""

import re

from pydantic import BaseModel, field_validator


class ScrapeRequest(BaseModel):
    """Pydantic model for triggering a target URL web scraping task — IMP-006: input validated."""

    user_id: str
    target_urls: list[str]

    @field_validator("user_id")
    @classmethod
    def sanitize_user_id(cls, v: str) -> str:
        """Strip HTML and enforce max_length for user_id."""
        v = re.sub(r"<[^>]+>", "", v).strip()
        if len(v) > 200:
            raise ValueError("user_id too long (max 200 chars)")
        return v

    @field_validator("target_urls", mode="before")
    @classmethod
    def validate_target_urls(cls, v: list) -> list:
        if not v or len(v) > 50:
            msg = "Must provide between 1 and 50 target URLs"
            raise ValueError(msg)
        return [str(url).strip()[:2048] for url in v]


class CoverLetterRequest(BaseModel):
    """Pydantic model for generating custom AI cover letters — IMP-006: input validated."""

    user_cv: str
    job_description: str
    tone: str = "professional"

    @field_validator("user_cv", "job_description")
    @classmethod
    def sanitize_text_fields(cls, v: str) -> str:
        """Strip HTML tags and enforce max_length on CV/JD text."""
        v = re.sub(r"<[^>]+>", "", v).strip()
        if len(v) > 50_000:
            raise ValueError("Text field too long (max 50,000 chars)")
        return v

    @field_validator("tone")
    @classmethod
    def validate_tone(cls, v: str) -> str:
        allowed = {"professional", "casual", "creative", "formal", "friendly", "confident"}
        v = v.strip().lower()
        if v not in allowed:
            msg = f"Tone must be one of {allowed}"
            raise ValueError(msg)
        return v


class AccountCreateRequest(BaseModel):
    """Pydantic model for local account balance profile generation — IMP-006: input validated."""

    tenant_id: str
    currency: str = "USD"
    balance_cents: int = 0

    @field_validator("tenant_id", "currency")
    @classmethod
    def sanitize_string_fields(cls, v: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_-]", "", v.strip())[:32]

    @field_validator("balance_cents")
    @classmethod
    def validate_balance(cls, v: int) -> int:
        if v < 0:
            msg = "Balance cannot be negative"
            raise ValueError(msg)
        return v


class EmailPreviewRequest(BaseModel):
    """Request model for email preview generation."""

    cv_text: str
    job_title: str
    company: str
    tone: str = "professional"
    recipient_email: str = ""

    @field_validator("cv_text")
    @classmethod
    def sanitize_cv(cls, v: str) -> str:
        return v.strip()[:10000]

    @field_validator("job_title", "company")
    @classmethod
    def sanitize_short_fields(cls, v: str) -> str:
        return v.strip()[:256]


class ReferralRequest(BaseModel):
    """Request model for referral tracking."""

    ref_code: str

    @field_validator("ref_code")
    @classmethod
    def sanitize_ref(cls, v: str) -> str:
        """Sanitize referral code."""
        v = re.sub(r"[^a-zA-Z0-9_-]", "", v).strip()
        if len(v) > 100:
            raise ValueError("ref_code too long")
        return v

# ──────────────────────────────────────────────────────────────────────────────
# validators.py - Common Input Validation Schemas
# Provides reusable Pydantic validators for API requests
# ──────────────────────────────────────────────────────────────────────────────

from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = Field(default=1, ge=1, le=1000)
    per_page: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: Optional[str] = Field(default="asc", regex="^(asc|desc)$")


class SearchParams(BaseModel):
    """Search/filter parameters."""
    q: Optional[str] = Field(None, max_length=255)
    filters: Optional[dict] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class UserProfileValidation(BaseModel):
    """User profile update validation."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, regex=r"^\+?1?\d{9,15}$")
    bio: Optional[str] = Field(None, max_length=1000)
    avatar_url: Optional[str] = None
    
    @validator("email")
    def email_must_be_valid(cls, v):
        if v and len(v) > 255:
            raise ValueError("Email too long")
        return v.lower() if v else v


class JobApplicationValidation(BaseModel):
    """Job application validation."""
    job_id: int
    cover_letter: Optional[str] = Field(None, max_length=5000)
    resume_url: Optional[str] = None
    custom_fields: Optional[dict] = None
    
    @validator("job_id")
    def job_id_positive(cls, v):
        if v <= 0:
            raise ValueError("job_id must be positive")
        return v


class CompanyFilterValidation(BaseModel):
    """Company search/filter validation."""
    industry: Optional[str] = None
    location: Optional[str] = None
    min_employees: Optional[int] = Field(None, ge=1)
    max_employees: Optional[int] = Field(None, ge=1)
    keywords: Optional[List[str]] = None


class DateRangeValidation(BaseModel):
    """Date range validation."""
    start_date: datetime
    end_date: datetime
    
    @validator("end_date")
    def end_date_after_start(cls, v, values):
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class PasswordValidation(BaseModel):
    """Password validation."""
    password: str = Field(min_length=8, max_length=128)
    password_confirm: str
    
    @validator("password")
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        if not any(c in "!@#$%^&*" for c in v):
            raise ValueError("Password must contain special character")
        return v
    
    @validator("password_confirm")
    def passwords_match(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v


class BulkActionValidation(BaseModel):
    """Bulk operation validation."""
    ids: List[int] = Field(min_items=1, max_items=1000)
    action: str = Field(regex="^(delete|archive|approve|reject)$")
    reason: Optional[str] = Field(None, max_length=500)


class RateLimitValidation(BaseModel):
    """Rate limit configuration."""
    requests_per_minute: int = Field(default=100, ge=1, le=10000)
    requests_per_hour: int = Field(default=5000, ge=1, le=100000)
    burst_size: int = Field(default=10, ge=1, le=100)


def validate_pagination(page: int, per_page: int) -> tuple:
    """Validate and normalize pagination parameters."""
    page = max(1, min(page, 1000))
    per_page = max(1, min(per_page, 100))
    return page, per_page


def validate_email(email: str) -> bool:
    """Check if email format is valid."""
    try:
        EmailStr.validate(email)
        return True
    except ValueError:
        return False


def validate_url(url: str) -> bool:
    """Check if URL format is valid."""
    import re
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url))

# Codebase Exploration and Implementation Analysis - Explorer 3

## Overview
This report documents the results of a read-only exploration of the JobHunt Pro codebase. We have identified the file locations, architectural components, and designed implementation plans for:
1. **IMP-034**: N+1 query elimination audit (joinedload/selectinload optimizations).
2. **IMP-039**: Celery task group/chord for bulk email campaigns.
3. **IMP-183**: Arabic NLP job matching via AraBERT embeddings.
4. **IMP-247**: CV PDF parsing accuracy enhancement via pdfplumber layout integration.

---

## 1. IMP-034: N+1 Query Elimination Audit

### Observations
- Currently, database models are defined in `core/webhook_state.py` (using `core/database.py`'s `Base`). However, most database operations in the codebase (e.g., in `core/campaign_runner.py` and `web/routers/candidate.py`) rely on raw SQL queries executed via SQLite (`sqlite3` / `aiosqlite` / `core/async_db.py`).
- SQLAlchemy is set up in `backend/database.py` and `core/database.py`. It is imported for transaction processing in `web/routers/payments.py` (using `AsyncSessionLocal` to update `ProcessedWebhook`).
- There are no active SQLAlchemy relationships in place since `ProcessedWebhook` is a standalone single-table model. However, migrating to SQLAlchemy ORM models (e.g. for `User`, `Campaign`, `CampaignEmail`, `CVProfile`) would introduce N+1 query risks when accessing nested relationships in loops.

### Proposed Models & Relationship Definitions
```python
# proposed_models.py (Sketch)
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    campaigns = relationship("Campaign", back_populates="user")
    cv_profiles = relationship("CVProfile", back_populates="user")

class CVProfile(Base):
    __tablename__ = 'cv_profiles'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False)
    profile_name = Column(String)
    cv_text = Column(String)
    user = relationship("User", back_populates="cv_profiles")

class Campaign(Base):
    __tablename__ = 'campaigns'
    id = Column(Integer, primary_key=True)
    campaign_id = Column(String, unique=True, nullable=False)
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False)
    status = Column(String, default='pending')
    
    user = relationship("User", back_populates="campaigns")
    emails = relationship("CampaignEmail", back_populates="campaign")

class CampaignEmail(Base):
    __tablename__ = 'campaign_emails'
    id = Column(Integer, primary_key=True)
    campaign_id = Column(String, ForeignKey('campaigns.campaign_id'), nullable=False)
    company_name = Column(String)
    job_title = Column(String)
    email_address = Column(String)
    status = Column(String, default='pending')
    
    campaign = relationship("Campaign", back_populates="emails")
```

### Problematic Loop Design (N+1 Query Risk)
If we fetch campaigns and loop through them to generate reports or check status:
```python
# Bad Pattern (N+1 Queries)
async def check_campaigns_status(session):
    result = await session.execute(select(Campaign))
    campaigns = result.scalars().all()
    for campaign in campaigns:
        # Accessing campaign.user triggers 1 SELECT query to users table (Many-to-One)
        logger.info(f"User: {campaign.user.name}")
        # Accessing campaign.emails triggers 1 SELECT query to campaign_emails table (One-to-Many)
        for email in campaign.emails:
            logger.info(f"Email sent to: {email.email_address}")
```
This triggers `1 + 2N` database roundtrips.

### Elimination Plan via Eager Loading
To resolve N+1 queries, we load the parent-child relationships upfront:
- Use `joinedload` for **Many-to-One** relationships (`Campaign.user`).
- Use `selectinload` for **One-to-Many** relationships (`Campaign.emails`).

```python
# Optimized Query (2 Queries Total)
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import select

async def check_campaigns_status_optimized(session):
    stmt = select(Campaign).options(
        joinedload(Campaign.user),
        selectinload(Campaign.emails)
    )
    result = await session.execute(stmt)
    campaigns = result.scalars().all()
    # Now, accessing campaign.user and campaign.emails is fully cached in memory.
```

---

## 2. IMP-039: Celery Task Group/Chord for Bulk Email Campaigns

### Observations
- **Email Engines**: Email campaign sending is handled by `core/campaign_runner.py` calling `email_engine.send_bulk_parallel()` which performs asynchronous network requests (HTTP or SMTP) in a batch of 10 concurrent requests using `asyncio.gather`.
- **Celery Tasks**: Celery task definitions are housed in `backend/tasks.py` and routed in `backend/celery_app.py`.
- **Current Task Definition**: `backend/tasks.py` defines `send_application_email(self, cover_letter_subject, cover_letter_body, recipient)`, which is configured with retries and routed to the `email_sender` queue in `backend/celery_app.py`. However, it is not actively dispatched in any workflow endpoints.

### Design Plan for Task Group and Chord
To transition campaign email dispatch to a scalable, distributed Celery architecture:
1. **Individual Task**: Retain `send_application_email` as the unit of work.
2. **Bulk Task Creator**: Implement a task `send_bulk_campaign_emails` that generates a signature group of email tasks.
3. **Completion Callback**: Define `campaign_completed_callback` to update the campaign status to `completed` in the database, calculate statistics, and trigger alerts.
4. **Chord Execution**: Execute the group using Celery's `chord` primitive to invoke the callback once all parallel sends finish.

```python
# proposed_tasks.py (Sketch)
from celery import group, chord
from backend.celery_app import celery_app
from backend.tasks import send_application_email
from web.app import get_db

@celery_app.task
def campaign_completed_callback(results, campaign_id: str):
    """
    Callback executed when all campaign emails have finished processing.
    """
    logger.info(f"All emails for campaign {campaign_id} processed. Results: {results}")
    
    # 1. Calculate success/failure counts
    sent_count = sum(1 for r in results if r.get("status") == "success")
    failed_count = sum(1 for r in results if r.get("status") != "success")
    
    # 2. Update campaign status in the database
    conn = get_db()
    try:
        conn.execute(
            "UPDATE campaigns SET status='completed', completed_at=CURRENT_TIMESTAMP, sent_count=sent_count WHERE campaign_id=?",
            (campaign_id,)
        )
        conn.commit()
    finally:
        conn.close()
    
    # 3. Trigger Telegram Alert
    try:
        from core.telegram_alerts import alert_campaign_completed
        alert_campaign_completed(campaign_id=campaign_id, sent_count=sent_count, failed_count=failed_count)
    except Exception as e:
        logger.warning(f"Failed to alert campaign completion: {e}")

@celery_app.task
def launch_email_campaign_task(campaign_id: str, email_jobs: list[dict]):
    """
    Launches a bulk campaign by executing a group of email tasks in parallel,
    followed by a completion chord callback.
    
    email_jobs format: [{"recipient": "...", "subject": "...", "body": "..."}]
    """
    # Create the task header (Group of parallel tasks)
    header = group(
        send_application_email.s(job["subject"], job["body"], job["recipient"])
        for job in email_jobs
    )
    
    # Execute chord (Group + Callback)
    callback = campaign_completed_callback.s(campaign_id)
    chord(header)(callback)
    
    logger.info(f"Enqueued chord for campaign {campaign_id} with {len(email_jobs)} tasks.")
```

---

## 3. IMP-183: Arabic NLP Job Matching

### Observations
- **Matching Engine**: Currently, `core/ats_matcher.py` performs algorithmic keyword matching and synonyms normalization using `TECH_TAXONOMY` and `SYNONYM_MAP`.
- **Groq Integration**: For semantic evaluation, it leverages Groq AI fallback (`analyze_with_groq_async` via `LLMProviderPool` / direct API).
- **Arabic Support**: Currently, the matching engine contains no explicit Arabic language processing or Arabic keyword taxonomies. It is entirely English-centric.

### Design Plan for AraBERT Embeddings Integration
To implement highly accurate Arabic semantic matching for resume-to-job alignment, we will:
1. **Identify Language**: Detect if the input CV or Job Description (JD) contains Arabic text.
2. **Text Normalization**: Standardize spelling and strip diacritics using an AraBERT-aligned normalization pipeline.
3. **Vector Embeddings**: Compute semantic vector embeddings using a pre-trained AraBERT model (`aubmindlab/bert-base-arabertv2`).
4. **Similarity Metric**: Measure alignment using Cosine Similarity.
5. **Weighted Blend**: Merge the semantic score with the keyword match score.

#### Code Architecture Proposal
```python
# proposed_arabic_matching.py (Sketch)
import re
import math
import logging
from transformers import AutoTokenizer, AutoModel
import torch

logger = logging.getLogger(__name__)

# Lazy initialization of AraBERT elements
_arabert_tokenizer = None
_arabert_model = None

def get_arabert_client():
    global _arabert_tokenizer, _arabert_model
    if _arabert_tokenizer is None:
        model_name = "aubmindlab/bert-base-arabertv2"
        _arabert_tokenizer = AutoTokenizer.from_pretrained(model_name)
        _arabert_model = AutoModel.from_pretrained(model_name)
    return _arabert_tokenizer, _arabert_model

def is_arabic(text: str) -> bool:
    """Detect presence of Arabic characters."""
    arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
    return bool(arabic_pattern.search(text))

def normalize_arabic(text: str) -> str:
    """Normalize Arabic text by removing tashkeel and standardizing characters."""
    # Remove tashkeel/diacritics
    tashkeel = re.compile(r"[\u064B-\u0652]")
    text = re.sub(tashkeel, "", text)
    # Standardize alef, ya, and ta marbuta
    text = re.sub(r"[أإآ]", "ا", text)
    text = re.sub(r"ى", "ي", text)
    text = re.sub(r"ة", "ه", text)
    return text.strip()

def compute_arabert_embedding(text: str) -> list[float]:
    """Generates a 768-dimensional mean-pooled AraBERT embedding for text."""
    tokenizer, model = get_arabert_client()
    normalized = normalize_arabic(text)
    
    inputs = tokenizer(normalized, padding=True, truncation=True, max_length=512, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model(**inputs)
        
    # Mean Pooling
    attention_mask = inputs["attention_mask"]
    token_embeddings = outputs.last_hidden_state
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
    sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    embedding = (sum_embeddings / sum_mask).squeeze(0).tolist()
    return embedding

def calculate_cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calculate the cosine similarity between two vector lists."""
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude_v1 = sum(a * a for a in v1) ** 0.5
    magnitude_v2 = sum(b * b for b in v2) ** 0.5
    if not magnitude_v1 or not magnitude_v2:
        return 0.0
    return dot_product / (magnitude_v1 * magnitude_v2)

def match_arabic_job(cv_text: str, jd_text: str) -> float:
    """
    Integrated matcher: runs when Arabic text is detected.
    Returns blended match score (0-100).
    """
    if not is_arabic(cv_text) and not is_arabic(jd_text):
        # Fallback to default English ATSMatcher
        return None
        
    emb_cv = compute_arabert_embedding(cv_text)
    emb_jd = compute_arabert_embedding(jd_text)
    similarity = calculate_cosine_similarity(emb_cv, emb_jd)
    
    # Scale from [-1, 1] / [0, 1] to [0, 100]
    score = round(max(0.0, similarity) * 100.0, 1)
    return score
```

---

## 4. IMP-247: CV PDF Parsing Accuracy

### Observations
- **PDF Extraction Sites**: Text is extracted from PDF CV files in two main components:
  1. `core/resume_optimizer.py` (lines 685–730) within the `_load_cv_text` method.
  2. `core/ai_tailor.py` (lines 406–413) within the `get_dynamic_cv_context` method.
- **Current Library Priority**: In `core/resume_optimizer.py`, `pdfplumber` is correctly placed as the preferred parser, with `pypdf` and `PyPDF2` as fallbacks. In `core/ai_tailor.py`, `pdfplumber` is imported directly without fallbacks.
- **Current Usage**: Extraction is basic and lacks layout configuration. In multi-column or formatted CV tables, text can merge incorrectly across columns, which severely compromises ATS parsing accuracy.

### Design Plan for pdfplumber Enhancements
To maximize extraction accuracy, we should:
1. **Refactor to a Shared Module**: Extract PDF parsing into a unified helper `core/pdf_extractor.py` to prevent redundant code in `resume_optimizer.py` and `ai_tailor.py`.
2. **Optimize Layout Options**: Utilise `page.extract_text(layout=True)` in `pdfplumber` to keep columns aligned and prevent side-by-side textual lines from merging.
3. **Address Table Spacing**: Extract table data explicitly if tabular elements exist using `page.extract_tables()` and format them as Markdown or plain spacing so they maintain logical reading flow.

#### Implementation Proposal
```python
# core/pdf_extractor.py (Sketch)
import os
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from a CV PDF file with layout preservation (optimized for ATS).
    """
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found at {pdf_path}")
        return ""
        
    # 1. Try pdfplumber (preferred layout-preserving method)
    try:
        import pdfplumber
        
        with pdfplumber.open(pdf_path) as pdf:
            pages_text = []
            for page in pdf.pages:
                # Use layout=True to preserve columns and tabular alignment
                text = page.extract_text(layout=True)
                if text:
                    pages_text.append(text)
            
            full_text = "\n\n".join(pages_text)
            if full_text.strip():
                logger.info(f"Successfully extracted {len(full_text)} characters using pdfplumber layout mode.")
                return full_text
    except ImportError:
        logger.warning("pdfplumber not installed. Falling back to pypdf...")
    except Exception as e:
        logger.error(f"pdfplumber extraction failed: {e}")

    # 2. Try pypdf (modern standard fallback)
    try:
        import pypdf
        with open(pdf_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            pages_text = [page.extract_text() or "" for page in reader.pages]
            full_text = "\n\n".join(pages_text)
            if full_text.strip():
                logger.info("Successfully extracted text using pypdf fallback.")
                return full_text
    except ImportError:
        logger.warning("pypdf not installed. Falling back to PyPDF2...")
    except Exception as e:
        logger.error(f"pypdf fallback failed: {e}")

    # 3. Try PyPDF2 (legacy fallback)
    try:
        import PyPDF2
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            pages_text = [page.extract_text() or "" for page in reader.pages]
            full_text = "\n\n".join(pages_text)
            if full_text.strip():
                logger.info("Successfully extracted text using PyPDF2 fallback.")
                return full_text
    except Exception as e:
        logger.error(f"PyPDF2 fallback failed: {e}")

    logger.critical("All PDF extraction methods failed. Return empty string.")
    return ""
```

And update the loading code in `core/resume_optimizer.py` and `core/ai_tailor.py`:
```python
# In core/resume_optimizer.py
from core.pdf_extractor import extract_text_from_pdf
...
elif ext == ".pdf":
    return extract_text_from_pdf(cv_path)

# In core/ai_tailor.py
from core.pdf_extractor import extract_text_from_pdf
...
elif ext == ".pdf":
    raw_text = extract_text_from_pdf(cv_path)
```

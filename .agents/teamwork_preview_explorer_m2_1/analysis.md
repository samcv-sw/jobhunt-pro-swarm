# Milestone 2 Read-Only Investigation Report — Explorer 1

This report outlines the codebase analysis and implementation designs for Milestone 2 tasks: **IMP-034 (N+1 query audit)**, **IMP-039 (Celery bulk email)**, **IMP-183 (Arabic NLP matching)**, and **IMP-247 (CV PDF parsing)**.

---

## 1. IMP-034: N+1 Query Elimination Audit

### Observations
1. **Model Relationships**: 
   - `backend/models.py` lines 55-56 define the only ORM relationships in the codebase:
     ```python
     transaction = relationship("Transaction", lazy="selectin")
     account = relationship("Account", lazy="selectin")
     ```
     These already use `lazy="selectin"` by default, which successfully mitigates N+1 reads when loading `LedgerEntry` collections.
2. **N+1 Database Operations in Loops**:
   - **DLQ Requeue Endpoint** (`backend/main.py` lines 676-683):
     ```python
     for sid in stale_ids:
         await session.execute(
             text("UPDATE sync_outbox SET synced = 0 WHERE id = :sid"),
             {"sid": sid}
         )
     ```
     This executes an individual database `UPDATE` query for each stale ID in a loop.
   - **Outbox Sync Worker** (`backend/sync_worker.py` lines 255-267):
     ```python
     for record in unsynced_records:
         success = await _push_record_to_cloud(cloud_conn, record)
         if success:
             record.synced = True
         ...
     await session.commit()
     ```
     Although records are updated in memory, modifying N objects in a session and calling `commit()` forces SQLAlchemy's unit of work to execute N individual SQL `UPDATE` queries sequentially.

### Proposed Solution
- **DLQ Requeue**: Simplify the select-and-update sequence to a single raw SQL bulk update:
  ```python
  cutoff = datetime.now(UTC) - timedelta(hours=24)
  async with async_session() as session:
      result = await session.execute(
          text("UPDATE sync_outbox SET synced = 0 WHERE synced = 0 AND created_at < :cutoff"),
          {"cutoff": cutoff.isoformat()}
      )
      requeued_count = result.rowcount
      await session.commit()
  ```
- **Sync Worker**: Aggregate successful and DLQ outbox record IDs into arrays, and perform bulk updates:
  ```python
  from sqlalchemy import update
  successful_ids = [r.id for r in successful_records]
  if successful_ids:
      await session.execute(
          update(SyncOutbox).where(SyncOutbox.id.in_(successful_ids)).values(synced=True)
      )
  ```

---

## 2. IMP-039: Celery Task Group/Chord for Bulk Email

### Observations
1. **Background Tasks**: `backend/tasks.py` defines `send_application_email(self, cover_letter_subject, cover_letter_body, recipient)`, which leverages exponential backoff retries and SMTP rotation. However, it is never invoked in the codebase.
2. **Current Email Dispatch**: `core/campaign_runner.py` uses `email_engine.send_bulk_parallel(...)` (lines 783-792) to send emails in parallel on the running application process using `asyncio.gather` and a semaphore.

### Proposed Solution
We propose moving parallel execution from blocking `asyncio.gather` on the main process to Celery workers using a **Group & Chord** workflow:
1. **Define a Callback Task** in `backend/tasks.py`:
   ```python
   @celery_app.task
   def campaign_completed_callback(results, campaign_id: str, user_id: str):
       """Executes once all emails in the bulk campaign have completed/failed."""
       sent_count = sum(1 for r in results if r.get("status") == "success")
       failed_count = sum(1 for r in results if r.get("status") == "failed")
       # Update campaign state in DB to 'completed'
       # Optionally send a Telegram alert summarizing the batch
       logger.info(f"Campaign {campaign_id} completed: {sent_count} sent, {failed_count} failed")
       return {"campaign_id": campaign_id, "sent": sent_count, "failed": failed_count}
   ```
2. **Construct and Dispatch the Chord** in `core/campaign_runner.py` or a dedicated email dispatch route:
   ```python
   from celery import chord
   from backend.tasks import send_application_email, campaign_completed_callback

   tasks = [
       send_application_email.s(
           cover_letter_subject=subject,
           cover_letter_body=body,
           recipient=job["email"]
       ) for job in valid_jobs
   ]
   callback = campaign_completed_callback.s(
       campaign_id=campaign["campaign_id"],
       user_id=campaign["user_id"]
   )
   # Trigger async parallel execution on workers
   chord_result = chord(tasks)(callback)
   ```

---

## 3. IMP-183: Arabic NLP Job Matching

### Observations
1. **ATS Matcher**: `core/ats_matcher.py` contains the `ATSMatcher` class, which handles keyword extraction via English tokenizers and taxonomic keyword filtering (`TECH_TAXONOMY` and `STOP_WORDS`).
2. **Limitation**: The regex filters (`NORMALIZE_RE`) and token counts assume English text and standard punctuation. Direct matching fails on Arabic scripts or mixed-language profiles (e.g. English CV with Arabic JD).

### Proposed Solution
Integrate **AraBERT** embeddings for semantic matching of Arabic/bilingual text:
1. **Arabic Detection**: Add helper method using a regex check:
   ```python
   def contains_arabic(text: str) -> bool:
       return bool(re.search(r"[\u0600-\u06FF]", text))
   ```
2. **AraBERT Vector Embedding Pipeline**:
   - Install `transformers` and `preprocess` libraries.
   - Load pre-trained AraBERT tokenizers/models (`aubmindlab/bert-base-arabertv02`).
   - If Arabic script is detected in either the CV or JD:
     - Normalize text using `ArabertPreprocessor`.
     - Generate word/sentence embeddings by mean-pooling the output hidden states of AraBERT.
     - Calculate semantic similarity using **cosine similarity**:
       $$\text{Similarity} = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|\|\mathbf{v}\|}$$
     - Map the similarity (range 0 to 1) into a 0-100 score.
3. **Hybrid Scoring**: Blend the semantic score (e.g., 50% weight) with any extracted token overlap (e.g., 50% weight) to handle mixed-language matching robustly.

---

## 4. IMP-247: CV PDF Parsing Accuracy

### Observations
1. **PDF Text Extraction**: 
   - `core/resume_optimizer.py` lines 685-731 tries loading PDF text via `pdfplumber`, falling back to `pypdf`, and then `PyPDF2`.
   - `core/ai_tailor.py` lines 406-412 extracts text using `pdfplumber` directly, but **lacks fallbacks**, causing it to crash or fail silently if `pdfplumber` is not installed or raises an error.
2. **Current Settings**: Both extractors call basic `page.extract_text()` without parameters, which can jumble text on multi-column resume layouts.

### Proposed Solution
1. **Consolidate to Shared Extractor**:
   Create `core/pdf_extractor.py` and implement a unified, robust text extractor with the existing fallbacks:
   ```python
   def extract_pdf_text(pdf_path: str) -> str:
       # Try pdfplumber, fallback to pypdf, fallback to PyPDF2
       ...
   ```
   Both `resume_optimizer.py` and `ai_tailor.py` should import and use `extract_pdf_text`.
2. **Optimize pdfplumber Accuracy**:
   - Resumes are frequently multi-column. Configure `pdfplumber` layout settings or sort characters:
     ```python
     with pdfplumber.open(pdf_path) as pdf:
         text = ""
         for page in pdf.pages:
             # Sort elements from top-to-bottom, left-to-right to avoid column jumbling
             text += page.extract_text(layout=True, x_tolerance=3, y_tolerance=3) or ""
     ```
   - This prevents text from sidebar columns from getting merged into main experience texts incorrectly.

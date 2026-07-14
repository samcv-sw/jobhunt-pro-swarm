# Handoff Report — Milestone 2 Exploration (Explorer 1)

This report details the findings and implementation designs for Milestone 2 tasks: N+1 audit (IMP-034), Celery bulk email group/chord (IMP-039), Arabic NLP match scoring (IMP-183), and CV PDF parsing accuracy (IMP-247).

---

## 1. Observation
We directly observed the following code structures and patterns:
- **IMP-034 (N+1 Query Audit)**:
  - `backend/models.py` (lines 55-56) uses `lazy="selectin"` which eagerly loads relationships:
    ```python
    transaction = relationship("Transaction", lazy="selectin")
    account = relationship("Account", lazy="selectin")
    ```
  - `backend/main.py` (lines 676-683) runs database updates inside a loop:
    ```python
    for sid in stale_ids:
        await session.execute(
            text("UPDATE sync_outbox SET synced = 0 WHERE id = :sid"),
            {"sid": sid}
        )
    ```
  - `backend/sync_worker.py` (lines 255-267) mutates N loaded `SyncOutbox` records individually inside a loop:
    ```python
    for record in unsynced_records:
        ...
        record.synced = True
    ...
    await session.commit()
    ```
    SQLAlchemy's unit-of-work translates these mutations into N individual `UPDATE` queries.
- **IMP-039 (Celery Bulk Email)**:
  - `backend/tasks.py` (lines 124-134) defines the `send_application_email` task with retries, but it is not invoked anywhere in the source files.
  - `core/campaign_runner.py` (lines 783-792) triggers bulk email sending in-process on the main thread via:
    ```python
    (batch_sent, batch_failed, batch_results) = await email_engine.send_bulk_parallel(...)
    ```
- **IMP-183 (Arabic NLP Job Matching)**:
  - `core/ats_matcher.py` (lines 717 and 738-740) extracts and normalizes keywords based on an English taxonomy (`TECH_TAXONOMY` / `STOP_WORDS`):
    ```python
    text = NORMALIZE_RE.sub(" ", text.lower())
    ...
    is_tech = term in TECH_TAXONOMY or any(w in TECH_TAXONOMY for w in words_in_term)
    ```
    This fails on Arabic resume text or job descriptions since it lacks Arabic token mapping and taxonomy.
- **IMP-247 (CV PDF Parsing)**:
  - `core/resume_optimizer.py` (lines 685-697) implements `pdfplumber` extraction with fallbacks to `pypdf` and `PyPDF2` in case of errors.
  - `core/ai_tailor.py` (lines 406-412) imports and opens the PDF using `pdfplumber` directly:
    ```python
    import pdfplumber
    with pdfplumber.open(cv_path) as pdf:
        raw_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    ```
    If `pdfplumber` fails or is missing, this crashes or fails without falling back.
  - Both files extract text without layout options, causing multi-column resumes to be merged incorrectly.

---

## 2. Logic Chain
- **N+1 Query Elimination**:
  - The loop in `backend/main.py:dlq_requeue` creates N database round-trips for N stale records, which should be done in 1 bulk UPDATE query.
  - Mutating model attributes in a loop in `backend/sync_worker.py:sync_outbox_to_cloud` forces SQLAlchemy to emit N separate updates. Replacing this with a single `update(SyncOutbox).where(SyncOutbox.id.in_(successful_ids))` bulk operation reduces round-trips to 1 or 2.
- **Celery Bulk Email group/chord**:
  - Because `send_application_email` is already configured for Celery queues and retries, moving bulk sending from in-process `asyncio.gather` to Celery signatures is straightforward.
  - A group `group(send_application_email.s(...) for job in jobs)` scales task execution horizontally. Combining it with a chord callback (`campaign_completed_callback`) allows post-batch summaries to execute exactly once.
- **Arabic NLP Matcher**:
  - Exact token matching fails on Arabic terms because of morphology, synonyms, and translations.
  - Integrating AraBERT (`aubmindlab/bert-base-arabertv02`) allows for dense vector representations. Computing the cosine similarity of these vectors provides a semantic match score that works for Arabic/bilingual text.
- **CV PDF Parsing Accuracy**:
  - The duplication of PDF logic and lack of fallbacks in `ai_tailor.py` can be fixed by consolidating the code into a shared `core/pdf_extractor.py` helper.
  - resuming columns can be parsed accurately by using `pdfplumber` parameter tuning (e.g. `layout=True` or `x_tolerance=3`).

---

## 3. Caveats
- Downloading AraBERT weights is restricted under `CODE_ONLY` network mode, so the weights must be pre-downloaded or mounted in the local environment.
- The SQL array binding syntax (`id IN :ids`) requires proper formatting to ensure compatibility across SQLite and PostgreSQL databases.

---

## 4. Conclusion
The codebase has been fully audited. Actions, file paths, and proposals for N+1 query elimination, Celery task group/chord bulk emails, AraBERT embeddings, and unified PDF parsing are completely structured, documented, and ready for implementation.

---

## 5. Verification Method
- Verify the audited locations by viewing files:
  - `backend/main.py` (lines 676-683)
  - `backend/sync_worker.py` (lines 255-267)
  - `core/ats_matcher.py` (lines 710-760)
  - `core/ai_tailor.py` (lines 406-412)
- Test suite can be run via:
  ```powershell
  pytest tests/e2e/test_e2e_backend.py
  ```

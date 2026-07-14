# Scope: Milestone 2: Backend Concurrency, Database & NLP

## Architecture
- Database query optimizations, Celery task routing improvements, Arabic NLP matching and CV parsing.

## Work Items
1. **IMP-034**: N+1 query elimination audit (Add selectinload/joinedload where queries loop).
2. **IMP-039**: Celery task group/chord for bulk email (celery.group() for parallel batch email dispatch).
3. **IMP-183**: Arabic NLP job matching (AraBERT embeddings for Arabic job-CV similarity).
4. **IMP-247**: CV PDF parsing accuracy (Switch from pdfminer to pdfplumber for multi-column CVs).

## Interface Contracts
- AraBERT embeddings or NLP matching in `core/ats_matcher.py` or new module.
- `pdfplumber` based extraction in CV upload handler/parser.

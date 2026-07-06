# Tasks: Refactoring JobHunt Pro

- [x] Consolidate databases and configure Neon pooling in `web/shared.py`
- [x] Complete FastAPI Application Factory initialization in `web/__init__.py`
- [x] Extract routes from `web/app_v2.py` to `web/routers/`
  - [x] Extract `campaigns.py` routes
  - [x] Extract `jobs.py` routes
  - [x] Extract `payments.py` routes
  - [x] Extract `admin.py` routes
- [x] Clean up monolithic routes in `web/app_v2.py` and direct to factory
- [x] Move plain JSON credentials to `.env` / database (already migrated/deleted)
- [x] Delete `web/app_v2.py.corrupted` (already deleted)
- [x] Verify FastAPI compilation and local server execution

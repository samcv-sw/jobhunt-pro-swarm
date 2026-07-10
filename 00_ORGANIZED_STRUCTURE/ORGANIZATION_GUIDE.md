# Project Organization Guide

This folder contains a properly organized structure for your CV/JobHunt SaaS project.

## Folder Structure

### 1-SOURCE_CODE
Core application files:
- `core/` - Core application logic
- `api/` - API endpoints
- `config.py` - Configuration files
- `requirements.txt` - Python dependencies
- `README.md` - Main project documentation

### 2-FRONTEND
All frontend-related code:
- `frontend/` - Main frontend application
- `frontend-vue/` - Vue.js frontend
- `chrome-extension/` - Chrome extension
- `dashboard/` - Dashboard UI
- `static_webapp/` - Static web assets
- `mobile/` - Mobile application

### 3-BACKEND
Backend server implementations:
- `backend/` - Python backend
- `backend-node/` - Node.js backend
- `services/` - Microservices
- `payments/` - Payment processing
- `scrapers/` - Web scrapers
- `bot/` - Bot implementations

### 4-DEVOPS
Deployment and infrastructure:
- `docker/` - Docker configurations (Dockerfile, docker-compose files)
- `k8s/` - Kubernetes configurations
- `deploy/` - Deployment scripts
- `nginx.conf` - Nginx configuration
- `Procfile` - Heroku configuration
- `railway.toml` - Railway configuration
- `render.yaml` - Render configuration
- `vercel.json` - Vercel configuration
- `infra/` - Infrastructure as code
- `scripts/deploy_*.sh` - Deployment scripts

### 5-DOCUMENTATION
All documentation files:
- `*.md` files (BLUEPRINT, ARCHITECTURE, DEPLOYMENT guides, etc.)
- `docs/` - Documentation folder
- `walkthrough.md` - Project walkthrough
- `STEP_BY_STEP_GUIDE.md` - Setup guide

### 6-TESTING
Testing and QA:
- `tests/` - Test files
- `test_*.py` - Individual test scripts
- `pytest.ini` - Pytest configuration
- `qa_*.py` - QA scripts

### 7-LOGS_AND_CACHE
Temporary files (can be deleted):
- `*.log` - Log files
- `.pytest_cache/` - Pytest cache
- `.ruff_cache/` - Ruff cache
- `__pycache__/` - Python cache
- `.env` - Environment variables (sensitive)
- `cache/` - Application cache

### 8-ARCHIVE
Old/backup files:
- `archive/` - Old project versions
- `_archive_temp/` - Temporary archives
- Backup folders

## Quick Start

1. **Set up locally**: Use files in `1-SOURCE_CODE` and `2-FRONTEND` + `3-BACKEND`
2. **For deployment**: Follow guides in `5-DOCUMENTATION` and use configs in `4-DEVOPS`
3. **Run tests**: Execute tests from `6-TESTING`
4. **View logs**: Check `7-LOGS_AND_CACHE` for debugging

## Notes

- Move files from root to appropriate folders gradually
- Keep `.git`, `.gitignore`, `.env.example` at project root
- Delete old log files and cache to save space
- Archive old versions in `8-ARCHIVE` before cleanup

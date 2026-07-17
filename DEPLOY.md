# JobHunt Pro — PythonAnywhere Deployment Guide

Production URL: **https://jhfguf.pythonanywhere.com**
Project root on PythonAnywhere: **`/home/jhfguf/jobhunt/`**
WSGI file: **`/var/www/jhfguf_pythonanywhere_com_wsgi.py`**
Active app: **`web/app_v2.py`** (FastAPI, bridged to WSGI via `a2wsgi`)

---

## 1. Architecture Overview

PythonAnywhere only supports **WSGI**, but JobHunt Pro is a **FastAPI (ASGI)** app.
We bridge ASGI → WSGI using [`a2wsgi`](https://pypi.org/project/a2wsgi/).

```
Browser
  │  HTTP
  ▼
PythonAnywhere WSGI Loader
  │  imports `application`
  ▼
/var/www/jhfguf_pythonanywhere_com_wsgi.py
  │  sys.path.insert(0, "/home/jhfguf/jobhunt")
  │  from web.app_v2 import wsgi_app as application
  ▼
web/app_v2.py  →  wsgi_app = ASGIMiddleware(app, send_queue_size=20)
  │  (FastAPI ASGI app wrapped for WSGI)
  ▼
Routers (web/routers/*)  →  Templates (web/templates/*)  →  Static (web/static/*)
```

The `wsgi_app` object is created at the bottom of `web/app_v2.py`:

```python
# web/app_v2.py  (end of file)
from a2wsgi import ASGIMiddleware
try:
    wsgi_app = ASGIMiddleware(app, send_queue_size=20)
except TypeError:
    wsgi_app = ASGIMiddleware(app)
```

---

## 2. One-Time Setup

### 2.1 Install a2wsgi (in the PA Bash console)

```bash
pip install --user a2wsgi
```

Or run the bundled installer (uses the PythonAnywhere API to install + reload):

```bash
python /home/jhfguf/jobhunt/web/install_a2wsgi.py
```

`web/install_a2wsgi.py` does:
- `pip install --user a2wsgi` in a PA console
- POSTs to `https://www.pythonanywhere.com/api/v0/user/JHFGUF/webapps/jhfguf.pythonanywhere.com/reload/`
  (authenticated with the account API token)

### 2.2 Create / edit the WSGI file

In the PythonAnywhere **Web** tab, open the WSGI file
(`/var/www/jhfguf_pythonanywhere_com_wsgi.py`) and replace its contents with:

```python
# /var/www/jhfguf_pythonanywhere_com_wsgi.py
import sys
from pathlib import Path

# Make the project root importable so `import web.app_v2` resolves.
PROJECT_ROOT = "/home/jhfguf/jobhunt"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# a2wsgi bridges the FastAPI (ASGI) app to WSGI for PythonAnywhere.
from web.app_v2 import wsgi_app as application
```

> **Why `sys.path.insert(0, PROJECT_ROOT)`?**
> `web/app_v2.py` itself does `sys.path.insert(0, str(Path(__file__).parent.parent))`
> (i.e. adds `/home/jhfguf/jobhunt`). The WSGI loader runs *outside* that file's
> module scope, so we replicate the same insertion here. Without it,
> `import web.app_v2` fails with `ModuleNotFoundError: No module named 'web'`.

---

## 3. Webapp Configuration (PythonAnywhere **Web** tab)

| Field | Value |
|-------|-------|
| **Source code** | `/home/jhfguf/jobhunt` |
| **WSGI configuration file** | `/var/www/jhfguf_pythonanywhere_com_wsgi.py` |
| **Python version** | `3.12` |
| **Static files** | URL: `/static/` → Directory: `/home/jhfguf/jobhunt/web/static` |
| **Working directory** | `/home/jhfguf/jobhunt` |

> The app also serves static files via FastAPI (`/static/...` → `web/static/`),
> but configuring the PA static mapping offloads them to Nginx (free, faster,
> no Python worker used).

---

## 4. Reload the App

After any code change, reload so PythonAnywhere picks up the new bytecode:

**Option A — Touch the WSGI file** (recommended, no token needed):
```bash
touch /var/www/jhfguf_pythonanywhere_com_wsgi.py
```

**Option B — Dashboard button:** Web tab → **Reload jhfguf.pythonanywhere.com**

**Option C — API** (used by `web/install_a2wsgi.py` and `app_v2.py` self-reload):
```bash
curl -X POST \
  -H "Authorization: Token 7f8bf3e6ad742bcb9e3c25e446cf664d6710b31d" \
  https://www.pythonanywhere.com/api/v0/user/JHFGUF/webapps/jhfguf.pythonanywhere.com/reload/
```

> `app_v2.py` also self-reloads on certain admin actions by calling
> `os.utime("/var/www/jhfguf_pythonanywhere_com_wsgi.py", None)` (equivalent to touch).

---

## 5. Local Development

Run the ASGI app directly with Uvicorn (no a2wsgi needed locally):

```bash
cd /home/jhfguf/jobhunt      # or your local project root
pip install -r requirements.txt
uvicorn web.app_v2:app --host 0.0.0.0 --port 8000 --reload
```

`web/app_v2.py` already contains the `uvicorn.run("web.app_v2:app", ...)`
entrypoint for `python -m web.app_v2` / `python web/app_v2.py` execution.

---

## 6. Scheduled Tasks (Cron)

The app uses a 30-minute heartbeat / worker tick. Configure in the PA **Tasks** tab
or add to the user crontab:

```cron
*/30 * * * * python /home/jhfguf/jobhunt/web/cron_trigger.py
```

`web/cron_trigger.py` lives at the project root and triggers the background
worker tick (campaign processing, ghost-hunter, viral factory, etc.).

---

## 7. Health Checks

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/health` | Queue + DB health (JSON) |
| `GET /` | Arabic/RTL landing (`web/templates/index_v4.html`) |
| `GET /en/` | English landing (`web/templates/en/index_v4.html`) |

---

## 8. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: No module named 'web'` | `sys.path` missing project root in WSGI | Add `sys.path.insert(0, "/home/jhfguf/jobhunt")` to WSGI file |
| `ImportError: No module named 'a2wsgi'` | a2wsgi not installed | `pip install --user a2wsgi` |
| `AttributeError: module 'web.app_v2' has no attribute 'wsgi_app'` | a2wsgi bridge block missing | Ensure end of `web/app_v2.py` defines `wsgi_app = ASGIMiddleware(app, ...)` |
| 500 after deploy, old code still running | WSGI not reloaded | `touch /var/www/jhfguf_pythonanywhere_com_wsgi.py` |
| Static assets 404 | Static mapping wrong | Web tab → Static files → `/static/` → `/home/jhfguf/jobhunt/web/static` |
| High CPU / timeouts | Uncached heavy queries | Check `web/routers/*` DB calls; verify connection reuse |

---

## 9. Deploy Checklist (copy-paste)

```bash
# 1. SSH / PA console
cd /home/jhfguf/jobhunt

# 2. Pull / sync latest code
git pull   # or upload via PA editor / Files tab

# 3. Ensure deps
pip install --user -r requirements.txt
pip install --user a2wsgi

# 4. Reload
touch /var/www/jhfguf_pythonanywhere_com_wsgi.py

# 5. Verify
curl -sS https://jhfguf.pythonanywhere.com/api/v1/health
```

# JobHunt Pro — Hugging Face Spaces Deployment Guide

This guide explains how to deploy **JobHunt Pro** on [Hugging Face Spaces](https://huggingface.co/spaces) using the **Docker (CPU Basic)** runtime.

---

## Prerequisites

| Requirement | Details |
|---|---|
| Hugging Face account | Free tier is sufficient |
| Space type | **Docker** (not Gradio / Streamlit) |
| Hardware | CPU Basic (free) |
| Secrets | See the table below |

---

## 1 — Create a new Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space).
2. Choose **Docker** as the Space SDK.
3. Pick **CPU Basic** (free) as the hardware tier.
4. Set visibility to **Public** or **Private** as needed.
5. Click **Create Space**.

---

## 2 — Configure Repository Secrets

In your Space → **Settings → Repository secrets**, add:

| Secret Name | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL / Neon connection string |
| `GEMINI_API_KEY` | Google Gemini API key |
| `GROQ_API_KEY` | Groq API key |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Telegram chat ID for notifications |
| `BREVO_API_KEY` | Brevo (SendinBlue) API key |
| `BREVO_ACCOUNT_EMAIL` | Sender e-mail address |
| `GMAIL_SMTP_USER_1` | Primary Gmail SMTP user |
| `GMAIL_APP_PASSWORD_1` | Primary Gmail app password |
| `GMAIL_SMTP_USER_2` | Secondary Gmail SMTP user |
| `GMAIL_APP_PASSWORD_2` | Secondary Gmail app password |
| `API_KEY` | Internal bearer token for trigger endpoints |

> **Tip:** Hugging Face Space secrets are injected as environment variables at runtime and are never exposed in logs.

---

## 3 — Push Your Code

Clone the auto-created Space repo and push your project:

```bash
# Clone the HF Space repo
git clone https://huggingface.co/spaces/<YOUR_USERNAME>/<YOUR_SPACE_NAME>
cd <YOUR_SPACE_NAME>

# Copy project files (or add HF remote to your existing repo)
cp -r /path/to/jobhunt-pro/* .

# Commit & push — HF will build the Docker image automatically
git add .
git commit -m "chore: initial Hugging Face Spaces deployment"
git push
```

Alternatively, add the HF Space as a second remote to your existing repo:

```bash
git remote add huggingface https://huggingface.co/spaces/<YOUR_USERNAME>/<YOUR_SPACE_NAME>
git push huggingface main
```

---

## 4 — Dockerfile Overview

The `Dockerfile` at the project root is already configured for HF Spaces:

| Setting | Value |
|---|---|
| Base image | `python:3.11-slim` |
| Exposed port | **7860** (HF standard) |
| `PORT` env var | `7860` |
| `PLAYWRIGHT_BROWSERS_PATH` | `/ms-playwright` |
| Entry-point | `uvicorn web.app_v2:app --host 0.0.0.0 --port 7860` |
| Browser driver | `chromium` + `chromium-driver` pre-installed |

HF Spaces automatically routes external traffic to port **7860**.

---

## 5 — Health Check

Once deployed, your app will be live at:

```
https://<YOUR_USERNAME>-<YOUR_SPACE_NAME>.hf.space
```

Test the health endpoint:

```bash
curl https://<YOUR_USERNAME>-<YOUR_SPACE_NAME>.hf.space/api/v1/health
```

Expected response:

```json
{"status": "ok"}
```

---

## 6 — Keeping the Space Alive

Hugging Face free-tier Spaces sleep after ~48 hours of inactivity. The GitHub Actions workflow at `.github/workflows/keepalive.yml` pings your **Render** backend every 12 minutes. For the HF Space itself, periodically visit the Space URL or upgrade to a paid hardware tier.

---

## 7 — Troubleshooting

| Problem | Solution |
|---|---|
| Build fails on `libgconf-2-4` | Verify the Debian package name for the slim image; substitute `libgconf2-4` if needed |
| `web.app_v2` not found | Ensure `web/app_v2.py` exists and `PYTHONPATH=/app` is set |
| Port not exposed | HF requires exactly port **7860**; do not change `EXPOSE` or `--port` |
| Secrets not injected | Check Space → Settings → Repository secrets |
| Chromium crashes | Add `--no-sandbox` flag in your Selenium/Playwright config when running inside Docker |

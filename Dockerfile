# ============================================
# JobHunt Pro — Hugging Face Spaces (Docker CPU Basic)
# ============================================
FROM python:3.11-slim

# Metadata
LABEL maintainer="JobHunt Pro" \
      description="JobHunt Pro FastAPI backend – Hugging Face Spaces Docker runtime"

# Avoid interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

# ---- System dependencies ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    chromium-driver \
    chromium \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# ---- Environment variables ----
ENV PORT=7860 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# ---- Working directory ----
WORKDIR /app

# ---- Python dependencies ----
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---- Copy project files ----
COPY web/       ./web/
COPY backend/   ./backend/
COPY scrapers/  ./scrapers/
COPY core/      ./core/
COPY config.py  .
COPY templates/ ./templates/
COPY static_webapp/ ./static_webapp/

# ---- Expose Hugging Face standard port ----
EXPOSE 7860

# ---- Start application ----
CMD ["uvicorn", "web.app_v2:app", "--host", "0.0.0.0", "--port", "7860"]

# ============================================
# JobHunt Pro — Multi-Stage Build
# Stage 1: builder  (has build-essential, gcc, etc.)
# Stage 2: runtime  (slim, no build tools)
# ============================================

# ---- Stage 1: Builder ----
FROM python:3.12-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---- Stage 2: Runtime ----
FROM python:3.11-slim AS runtime

LABEL maintainer="JobHunt Pro" \
      description="JobHunt Pro FastAPI backend"

ENV DEBIAN_FRONTEND=noninteractive

# Runtime-only system deps (no build-essential)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    chromium-driver \
    chromium \
    libglib2.0-0 \
    libnss3 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Environment variables
ENV PORT=7860 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy only the application code needed at runtime
COPY web/           ./web/
COPY backend/       ./backend/
COPY scrapers/      ./scrapers/
COPY core/          ./core/
COPY config.py      .
COPY templates/     ./templates/
COPY static_webapp/ ./static_webapp/

# Expose Hugging Face standard port
EXPOSE 7860

# Non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser /app
USER appuser

CMD ["uvicorn", "web.app_v2:app", "--host", "0.0.0.0", "--port", "7860"]

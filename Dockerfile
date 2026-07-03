# ============================================
# JobHunt Pro - Backend (FastAPI + Celery)
# ============================================
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY scrapers/ ./scrapers/
COPY tests/ ./tests/

# Set Python path so `backend` can be resolved
ENV PYTHONPATH=/app

# Expose FastAPI port
EXPOSE 8000

# Default command: start FastAPI
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

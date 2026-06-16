FROM python:3.11-slim

# Install Chromium, Xvfb (Virtual Display for stealth scraper), and FFmpeg (for edge-tts)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    xvfb \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copy application code
COPY . .

# Set Environment Variables for headless Chromium
ENV CHROME_BIN=/usr/bin/chromium
ENV DISPLAY=:99

# Health server on 9999 (internal), uvicorn web app on 10000 (Render default)
# swarm_master runs as background daemon
EXPOSE 10000
CMD ["sh", "-c", "Xvfb :99 -screen 0 1280x1024x24 & python -m core.swarm_master & sleep 2 && python -m uvicorn web.app_v2:app --host 0.0.0.0 --port 10000"]

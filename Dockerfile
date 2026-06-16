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

# Start swarm_master background + gunicorn+uvicorn web server foreground
# Gunicorn binds port immediately (Render health scan passes), loads app asynchronously
EXPOSE 10000
CMD ["sh", "-c", "Xvfb :99 -screen 0 1280x1024x24 & python -m core.swarm_master & sleep 3 && python render_boot.py"]

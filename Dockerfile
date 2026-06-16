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
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Environment Variables for headless Chromium
ENV CHROME_BIN=/usr/bin/chromium
ENV DISPLAY=:99

# Make start script executable
COPY start.sh .
RUN chmod +x start.sh

# Start the application
CMD ["./start.sh"]

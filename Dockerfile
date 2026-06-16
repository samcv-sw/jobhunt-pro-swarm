FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    chromium chromium-driver xvfb ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY . .

ENV CHROME_BIN=/usr/bin/chromium
ENV DISPLAY=:99
ENV HEALTH_PORT=10000

EXPOSE 10000
CMD ["sh", "-c", "Xvfb :99 -screen 0 1280x1024x24 & sleep 2 && python -m core.swarm_master"]

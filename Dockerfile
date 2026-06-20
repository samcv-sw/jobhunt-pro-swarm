FROM python:3.12-slim

# Install dependencies and Supervisor
RUN apt-get update && apt-get install -y supervisor build-essential wget curl unzip xvfb libxi6 libgconf-2-4 libnss3 libasound2t64 libatk-bridge2.0-0 libgtk-3-0 libgbm1 && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app
COPY . /app

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install uvicorn

# Configure Supervisor for Monolith Mode
RUN echo "[supervisord]" > /etc/supervisor/conf.d/supervisord.conf && \
    echo "nodaemon=true" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "[program:fastapi]" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "command=gunicorn web.app_v2:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:7860 --timeout 120" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "autostart=true" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "autorestart=true" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "[program:worker]" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "command=python core/queue_worker.py" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "autostart=true" >> /etc/supervisor/conf.d/supervisord.conf && \
    echo "autorestart=true" >> /etc/supervisor/conf.d/supervisord.conf

# Create Cluster Entrypoint
RUN echo '#!/bin/bash\n\
if [ "$MODE" = "WORKER" ]; then\n\
    echo "🚀 Starting in WORKER ONLY mode..."\n\
    python core/queue_worker.py\n\
elif [ "$MODE" = "API" ]; then\n\
    echo "🚀 Starting in API ONLY mode..."\n\
    gunicorn web.app_v2:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:7860 --timeout 120\n\
else\n\
    echo "🚀 Starting in MONOLITH mode (API + WORKER)..."\n\
    supervisord -c /etc/supervisor/conf.d/supervisord.conf\n\
fi' > /app/start.sh && chmod +x /app/start.sh

# Expose port 7860 for Hugging Face Spaces
EXPOSE 7860

# Run the Cluster Entrypoint
CMD ["bash", "/app/start.sh"]

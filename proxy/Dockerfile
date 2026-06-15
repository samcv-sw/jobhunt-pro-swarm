FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a user with ID 1000 (required for HF Spaces)
RUN useradd -m -u 1000 user
RUN chown -R user:user /app

ENV PORT=7860
ENV HOST=0.0.0.0

USER user

CMD ["python", "proxy_app.py"]

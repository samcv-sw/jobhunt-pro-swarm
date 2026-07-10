# JobHunt Pro - FREE Cloud Deployment Guide

## Render.com (100% Free, No Credit Card)

### Step 1: Push to GitHub
```bash
cd "C:\Users\samde\Desktop\cv sam new ma3 kimi"
git init
git add .
git commit -m "JobHunt Pro - Initial cloud deploy"
```

Create a NEW GitHub repo (private), then:
```bash
git remote add origin https://github.com/YOUR_USERNAME/jobhunt-pro.git
git push -u origin main
```

### Step 2: Deploy on Render
1. Go to https://render.com (sign up with GitHub)
2. Click "New" -> "Blueprint"
3. Select your jobhunt-pro repo
4. Render reads render.yaml automatically
5. Click "Apply" - done!

### Step 3: Set Environment Variables (Secrets)
In Render dashboard -> Environment tab, add these secrets from your `.env` file:
- **GROQ_API_KEY** = your_groq_api_key
- **JSEARCH_API_KEY** = your_jsearch_api_key
- **GMAIL_SMTP_USER_1** = your_gmail@gmail.com
- **GMAIL_APP_PASSWORD_1** = your_gmail_app_password
- **BREVO_API_KEY** = your_brevo_api_key
- **BREVO_ACCOUNT_EMAIL** = your_brevo_sender_email
- **TELEGRAM_BOT_TOKEN** = your_telegram_bot_token
- **TELEGRAM_CHAT_ID** = your_telegram_chat_id
- **SECRET_KEY** = your_random_secret_key

### Step 4: Your app URL
After deploy (2-3 min), you get: https://jobhunt-pro.onrender.com

### Free Tier Limits
- 750 hours/month (enough for 24/7)
- 512MB RAM
- Spins down after 15min idle (wakes in ~30s)
- SQLite database (persistent on disk)

---

## Alternative: PythonAnywhere (Also Free)

### Step 1: Upload files
1. Go to https://pythonanywhere.com (sign up)
2. Files tab -> Upload all project files

### Step 2: Set up
```bash
cd ~/jobhunt-pro
pip install -r requirements-cloud.txt
```

### Step 3: Create WSGI file
```python
# /var/www/your_username_pythonanywhere_com_wsgi.py
import sys
project_home = '/home/YOUR_USERNAME/jobhunt-pro'
if project_home not in sys.path:
    sys.path.insert(0, project_home)
from web.app_v2 import app as application
```

### Step 4: Web app config
- URL: YOUR_USERNAME.pythonanywhere.com
- Source: /home/YOUR_USERNAME/jobhunt-pro
- WSGI: /var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py

---

## JSearch API Key Activation

1. Go to https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
2. Click "Subscribe to Test" (free plan: 500 req/month)
3. Copy your key from "Header Parameters"
4. Set it as `JSEARCH_API_KEY` in Render Dashboard

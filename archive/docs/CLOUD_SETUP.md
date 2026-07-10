# JobHunt Pro — Cloud Setup Guide
# خطوة بخطوة للتشغيل على الـ Cloud

---

## الخيار 1: Railway (الأسهل — 5 دقائق)

### المتطلبات
- حساب GitHub
- حساب Railway (مجاني)

### الخطوات

**1. ارفع الكود على GitHub**
```bash
git init
git add .
git commit -m "JobHunt Pro v5"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/jobhunt-pro.git
git push -u origin main
```

**2. افتح Railway**
- روح على https://railway.app
- سجل دخول بـ GitHub
- اضغط "New Project" → "Deploy from GitHub repo"
- اختار الـ repo

**3. أضف PostgreSQL**
- بالـ project dashboard: "New" → "Database" → "Add PostgreSQL"
- Railway بيربطه تلقائياً

**4. أضف Redis**
- "New" → "Database" → "Add Redis"

**5. حط الـ Environment Variables**
اضغط على الـ app service → "Variables" → أضف:
```
CANDIDATE_EMAIL=samsalameh.cv@gmail.com
CANDIDATE_PHONE=+961 71 019 053
CV_PATH=assets/Sam_Salameh_CV.pdf
GMAIL_SMTP_USER_1=samsalameh.cv@gmail.com
GMAIL_APP_PASSWORD_1=xxxx xxxx xxxx xxxx
SECRET_KEY=any-random-long-string-here
DRY_RUN=false
MAX_WORKERS=100
DAILY_SEND_LIMIT=2000
```

**6. Deploy**
- Railway بيبني ويشغل تلقائياً
- بعد دقيقتين: https://your-app.up.railway.app

---

## الخيار 2: Render.com (مجاني — بس بيتوقف بعد 15 دقيقة idle)

**1. ارفع على GitHub** (نفس الخطوات فوق)

**2. افتح Render**
- روح على https://render.com
- "New" → "Blueprint"
- ربط الـ GitHub repo
- Render بيقرأ `render.yaml` تلقائياً
- اضغط "Apply"

**3. حط الـ Variables**
بعد ما يخلص الـ deploy، روح على الـ service → "Environment":
```
GMAIL_APP_PASSWORD_1=xxxx xxxx xxxx xxxx
SECRET_KEY=any-random-long-string-here
DRY_RUN=false
```

**4. Access**
- https://your-app.onrender.com

---

## الخيار 3: Oracle Cloud (مجاني للأبد — الأقوى)

### ليش Oracle Cloud؟
- 4 CPU + 24GB RAM مجاناً للأبد
- ما بيتوقف أبداً
- أقوى من الـ paid tiers على Railway/Render

### الخطوات

**1. إنشاء حساب**
- روح على https://cloud.oracle.com/free
- سجل (ما في حاجة لـ credit card للـ Always Free)

**2. إنشاء VM**
- Dashboard → "Create a VM Instance"
- Name: `jobhunt-pro`
- Image: Ubuntu 22.04
- Shape: VM.Standard.E4.Flex (4 OCPU, 24GB RAM)
- أضف SSH key
- اضغط Create
- احفظ الـ Public IP

**3. اتصل بالـ VM**
```bash
ssh -i your-key.pem ubuntu@YOUR_VM_IP
```

**4. ارفع الكود**
```bash
# من جهازك:
scp -i your-key.pem -r "C:\Users\samde\Desktop\cv sam new ma3 kimi" ubuntu@YOUR_VM_IP:~/jobhunt-pro
```

**5. شغل الـ Deploy Script**
```bash
ssh -i your-key.pem ubuntu@YOUR_VM_IP
cd ~/jobhunt-pro
chmod +x deploy_vm.sh
./deploy_vm.sh
```

**6. حط الـ Credentials**
```bash
nano .env
# حط Gmail App Password وباقي الـ credentials
# Ctrl+X ثم Y للحفظ
```

**7. شغل**
```bash
docker-compose up -d
```

**8. تحقق**
```bash
curl http://localhost:8000/health
# يرجع: {"status": "healthy", ...}
```

**Access من أي مكان:**
```
http://YOUR_VM_IP:8000
http://YOUR_VM_IP:8000/dashboard
```

---

## إضافة SSL (HTTPS) — اختياري

بعد ما يشتغل الـ app على VM:

**1. سجل دومين مجاني**
- روح على https://freedns.afraid.org
- سجل subdomain مثل: `jobhunt.mooo.com`
- وجهه على IP الـ VM

**2. احصل على SSL Certificate**
```bash
# على الـ VM:
docker-compose run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d your-domain.com \
  --email your@email.com \
  --agree-tos --no-eff-email
```

**3. فعّل HTTPS بالـ nginx.conf**
- افتح `nginx.conf`
- شيل الـ `#` من الـ HTTPS server block
- غير `your-domain.com` لدومينك
- `docker-compose restart nginx`

---

## بعد الـ Deploy — تحقق من كل شي

```bash
# Health check
curl https://your-app-url/health

# شوف الـ logs
docker-compose logs -f app

# شوف الـ containers
docker-compose ps
```

---

## المشاكل الشائعة

| المشكلة | الحل |
|---------|------|
| App مش بيشتغل | `docker-compose logs app` |
| Database error | `docker-compose restart postgres` |
| Email مش بيتبعت | تحقق من `GMAIL_APP_PASSWORD_1` بالـ `.env` |
| Port 8000 مش شغال | `sudo ufw allow 8000/tcp` |
| Out of memory | غير `MAX_WORKERS=50` بالـ `.env` |

---

## ملخص التكاليف

| Platform | التكلفة | الـ RAM | يتوقف؟ |
|----------|---------|---------|--------|
| Oracle Cloud | **$0 للأبد** | 24GB | لا |
| Railway | $5-20/شهر | 512MB-1GB | لا |
| Render | $0 (free) | 512MB | نعم (15 دقيقة) |
| Fly.io | $5-10/شهر | 256MB-512MB | لا |

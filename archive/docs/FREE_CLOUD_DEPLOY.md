# ============================================
# JobHunt Pro - FREE Cloud Deployment Guide
# $0 Investment — Runs Forever
# ============================================

## BEST OPTION: Oracle Cloud Always Free

### Why Oracle Cloud?
- **2 VMs free forever** (4 OCPUs, 24GB RAM each)
- **No credit card required** for Always Free tier
- **Never spins down** — runs 24/7
- **More powerful** than paid tiers on other platforms
- **Free PostgreSQL** and Redis

### Step-by-Step Setup

#### 1. Create Oracle Cloud Account
```
1. Go to https://cloud.oracle.com/free
2. Click "Start for Free"
3. Fill in details (no credit card needed)
4. Verify email
5. You now have $300 free credit + Always Free tier
```

#### 2. Create VM Instance
```
1. Dashboard → "Create a VM Instance"
2. Name: jobhunt-pro
3. Image: Ubuntu 22.04 (or Oracle Linux)
4. Shape: VM.Standard.E4.Flex (Always Free eligible)
   - OCPUs: 4 (max free)
   - RAM: 24 GB (max free)
5. Add SSH key (generate new or paste existing)
6. Create
```

#### 3. Connect to VM
```bash
# Download SSH key from Oracle Cloud
# Connect:
ssh -i your-key.pem ubuntu@YOUR_VM_IP
```

#### 4. Install Docker on VM
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and back in
exit
```

#### 5. Upload Your Code
```bash
# From your local machine:
scp -i your-key.pem -r "cv sam new ma3 kimi/" ubuntu@YOUR_VM_IP:~/

# Or use git:
ssh -i your-key.pem ubuntu@YOUR_VM_IP
git clone https://github.com/YOUR_USERNAME/jobhunt-pro.git
```

#### 6. Configure Environment
```bash
ssh -i your-key.pem ubuntu@YOUR_VM_IP
cd ~/jobhunt-pro

# Create .env
cp .env.example .env
nano .env
# Fill in your credentials
```

#### 7. Deploy
```bash
# Start everything
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app

# Check health
curl http://localhost:8000/health
```

#### 8. Access from Anywhere
```
Your dashboard: http://YOUR_VM_IP:8000
Health check: http://YOUR_VM_IP:8000/health
Dashboard: http://YOUR_VM_IP:8000/dashboard
```

#### 9. (Optional) Add Free Domain
```
1. Go to https://freedns.afraid.org
2. Register free account
3. Add a subdomain (e.g., jobhunt.mooo.com)
4. Point it to YOUR_VM_IP
5. Access at: http://jobhunt.mooo.com
```

---

## ALTERNATIVE: Render.com Free Tier

### Setup
```bash
# 1. Push to GitHub
git init && git add . && git commit -m "v5"
git remote add origin https://github.com/YOUR/jobhunt-pro.git
git push -u origin main

# 2. Go to https://render.com
# 3. Click "New" → "Web Service"
# 4. Connect GitHub repo
# 5. Settings:
#    - Build Command: pip install -r requirements.txt
#    - Start Command: python auto_run.py
#    - Instance Type: Free
# 6. Add PostgreSQL (free tier)
# 7. Set environment variables
# 8. Deploy
```

### Limitations (Free Tier)
- Spins down after 15 min idle
- 512MB RAM (enough for 50 agents)
- 750 hours/month
- Good for testing, not production

---

## ALTERNATIVE: Fly.io Free Tier

### Setup
```bash
# 1. Install flyctl
curl -L https://fly.io/install.sh | sh
fly auth login

# 2. Initialize
cd "cv sam new ma3 kimi"
fly launch

# 3. Set secrets
fly secrets set CANDIDATE_EMAIL=your_email
fly secrets set GEMINI_API_KEY=your_key
fly secrets set DB_PASSWORD=your_password

# 4. Deploy
fly deploy

# 5. Access
# https://your-app.fly.dev
```

### Free Tier Limits
- 3 shared VMs
- 160GB bandwidth/month
- 1GB free Postgres
- Good for 50-100 agents

---

## RECOMMENDED: Full Free Stack

### Components (All Free)
| Component | Service | Cost |
|-----------|---------|------|
| VM | Oracle Cloud Always Free | $0 forever |
| Database | PostgreSQL on VM | $0 |
| Cache | Redis on VM | $0 |
| Domain | freedns.afraid.org | $0 |
| SSL | Let's Encrypt | $0 |
| Monitoring | UptimeRobot (free) | $0 |

### Total Cost: $0/month forever

### Performance on Free Tier
```
VM Specs (Oracle Always Free):
  - 4 OCPUs (AMD EPYC)
  - 24 GB RAM
  - 200GB storage
  - 10TB bandwidth/month

Can run:
  - 200 agents easily
  - 19 email providers
  - 2,100 emails/day
  - PostgreSQL + Redis
  - Nginx reverse proxy
  - Full web dashboard
```

---

## After Deployment

### 1. Verify Everything Works
```bash
# SSH into VM
ssh -i your-key.pem ubuntu@YOUR_VM_IP

# Check containers
docker-compose ps

# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f
```

### 2. Access Dashboard
```
Open browser: http://YOUR_VM_IP:8000
Login: your registered email
Dashboard: http://YOUR_VM_IP:8000/dashboard
```

### 3. Set Up Auto-Backup
```bash
# Add to crontab
crontab -e

# Backup database daily at 3 AM
0 3 * * * docker exec jobhunt-postgres pg_dump -U jobhunt jobhunt_pro > ~/backup/db_$(date +\%Y\%m\%d).sql
```

### 4. Monitor Uptime
```
1. Go to https://uptimerobot.com
2. Create free account
3. Add monitor: http://YOUR_VM_IP:8000/health
4. Set alert: email + Telegram
5. Free: 50 monitors
```

---

## Troubleshooting

### App won't start
```bash
# Check logs
docker-compose logs app

# Common fixes:
docker-compose down
docker-compose up -d --build
```

### Database connection failed
```bash
# Check PostgreSQL
docker-compose logs postgres

# Restart
docker-compose restart postgres
```

### Port already in use
```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill it or change port in docker-compose.yml
```

### Out of memory
```bash
# Check memory
free -h

# Reduce workers in .env
MAX_WORKERS=50

# Restart
docker-compose restart app
```

---

## Scaling Beyond Free Tier

When you start making money from subscriptions:

1. **Upgrade VM**: Oracle Cloud paid tier ($0.01/hr)
2. **Add CDN**: CloudFlare free tier
3. **Add monitoring**: Datadog free tier
4. **Add logging**: Papertrail free tier

### Break-Even Analysis
```
Free tier handles:
  - 1,000 users
  - $11,740 MRR
  - $140,880 ARR

When you hit 1,000 users:
  - Upgrade to paid VM: $20/mo
  - Add paid database: $10/mo
  - Total cost: $30/mo
  - Revenue: $11,740/mo
  - Profit: $11,710/mo (99.7% margin)
```

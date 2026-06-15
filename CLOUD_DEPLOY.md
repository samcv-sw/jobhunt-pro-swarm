# ============================================
# JobHunt Pro - Cloud Deployment Guide
# Step-by-step for Railway, Render, Fly.io
# ============================================

## Quick Deploy (Railway — Recommended)

### 1. Push to GitHub
```bash
cd "cv sam new ma3 kimi"
git init
git add .
git commit -m "JobHunt Pro v5 - Production"
git remote add origin https://github.com/YOUR_USERNAME/jobhunt-pro.git
git push -u origin main
```

### 2. Deploy on Railway
1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub"
3. Select your repo
4. Railway auto-detects Dockerfile
5. Add PostgreSQL: "New" → "Database" → "PostgreSQL"
6. Add Redis: "New" → "Database" → "Redis"
7. Set environment variables (see .env.example)
8. Deploy!

### 3. Custom Domain
1. Railway Dashboard → your app → Settings
2. "Networking" → "Generate Domain"
3. Or add custom domain: "Custom Domain" → enter your domain
4. Railway provides free SSL automatically

### 4. Access Dashboard
- Railway URL: https://your-app.up.railway.app
- Dashboard: https://your-app.up.railway.app/dashboard
- API Docs: https://your-app.up.railway.app/api/docs

---

## Alternative: Render.com

### 1. Create render.yaml
```yaml
services:
  - type: web
    name: jobhunt-pro
    runtime: docker
    dockerfilePath: ./Dockerfile
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: jobhunt-db
          property: connectionString
      - key: REDIS_URL
        fromRedis:
          name: jobhunt-redis
          property: connectionString
      - key: MAX_WORKERS
        value: 200
      - key: DAILY_SEND_LIMIT
        value: 2000
    healthCheckPath: /health
    autoDeploy: true

  - type: postgres
    name: jobhunt-db
    databaseName: jobhunt_pro
    plan: starter

  - type: redis
    name: jobhunt-redis
    plan: starter
```

### 2. Deploy
1. Go to https://render.com
2. "New" → "Blueprint"
3. Connect GitHub repo
4. Render reads render.yaml
5. Deploy!

---

## Alternative: Fly.io

### 1. Install flyctl
```bash
curl -L https://fly.io/install.sh | sh
fly auth login
```

### 2. Initialize
```bash
cd "cv sam new ma3 kimi"
fly launch
# Select: Yes to Dockerfile, Yes to PostgreSQL, No to Redis (add later)
```

### 3. Set secrets
```bash
fly secrets set CANDIDATE_EMAIL=your_email@gmail.com
fly secrets set GEMINI_API_KEY=your_key
fly secrets set TELEGRAM_BOT_TOKEN=your_token
fly secrets set DB_PASSWORD=your_password
fly secrets set SECRET_KEY=your_secret
```

### 4. Deploy
```bash
fly deploy
```

### 5. Add Redis
```bash
fly redis create jobhunt-redis
fly secrets set REDIS_URL=redis://default:password@fly-redis.upstash.io:6379
```

### 6. Custom domain
```bash
fly certs add your-domain.com
fly ips allocate-v4
# Point DNS to the IP shown
```

---

## Post-Deployment Checklist

### 1. Verify Health
```bash
curl https://your-app-url/health
# Should return: {"status": "healthy", ...}
```

### 2. Create Admin User
```bash
curl -X POST https://your-app-url/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@yourdomain.com","password":"secure_password","name":"Admin"}'
```

### 3. Configure Email Providers
Go to dashboard → Settings → Email Providers
Add at least 2 SMTP providers for rotation.

### 4. Set Up Monitoring
- Health check: https://your-app-url/health
- Dashboard: https://your-app-url/dashboard
- Logs: Check cloud provider dashboard

### 5. Enable Auto-Scaling (if needed)
Railway: Auto-scales by default
Render: Set min/max instances
Fly.io: `fly scale count 2`

---

## Troubleshooting

### App won't start
- Check logs: `fly logs` or Railway dashboard
- Verify DATABASE_URL is correct
- Ensure all env vars are set

### Database connection failed
- Check PostgreSQL is running
- Verify password matches
- Check network (VPC on Railway/Render)

### Email sending fails
- Verify SMTP credentials
- Check provider daily limits
- Enable "Less secure apps" for Gmail

### High memory usage
- Reduce MAX_WORKERS (e.g., 50)
- Check for memory leaks in logs
- Upgrade plan if needed

---

## Cost Estimate (Monthly)

### Railway (Recommended)
- Starter: $5/mo (512MB RAM, shared CPU)
- Pro: $20/mo (1GB RAM, dedicated CPU)
- PostgreSQL: $5-20/mo
- Redis: $5/mo
- **Total: $20-50/mo for full system**

### Render
- Starter: $7/mo (512MB RAM)
- Standard: $25/mo (2GB RAM)
- PostgreSQL: $7-20/mo
- Redis: $7/mo
- **Total: $25-60/mo**

### Fly.io
- Micro: $5/mo (256MB RAM)
- Small: $10/mo (512MB RAM)
- Medium: $20/mo (1GB RAM)
- PostgreSQL: $10-30/mo (Fly Postgres)
- Redis: $10/mo (Upstash)
- **Total: $30-70/mo**

---

## Scaling to 100,000 Users

### Current Capacity (Single Instance)
- 200 agents
- 2,100 emails/day
- 1,000 concurrent users

### To Handle 100,000 Users
1. **Horizontal scaling**: 10-20 instances
2. **Database**: PostgreSQL cluster (read replicas)
3. **Cache**: Redis cluster
4. **Queue**: Celery + RabbitMQ for background jobs
5. **CDN**: CloudFlare for static assets
6. **Load balancer**: CloudFlare or cloud provider LB

### Architecture for Scale
```
Users → CloudFlare CDN → Load Balancer
    ↓
[App Instance 1] [App Instance 2] ... [App Instance N]
    ↓
PostgreSQL (Primary + Read Replicas)
    ↓
Redis Cluster (Sessions + Cache)
    ↓
Celery Workers (Background Jobs)
```

---

## Security Checklist

- [ ] Change SECRET_KEY
- [ ] Change DB_PASSWORD
- [ ] Enable HTTPS (automatic on Railway/Render)
- [ ] Set CORS origins
- [ ] Enable rate limiting (nginx)
- [ ] Regular database backups
- [ ] Monitor for unusual activity
- [ ] Keep dependencies updated

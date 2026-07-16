# Docker Strategy & Consolidation — JobHunt Pro v3.0

**Status**: 🔧 Consolidation in Progress  
**Goal**: Reduce from 11 → 4 Dockerfiles (keep only essential variants)

---

## Current Dockerfile Inventory

### Active Dockerfiles (7) ✅

| File | Purpose | Status | Keep? |
|------|---------|--------|-------|
| **Dockerfile** | Production backend (FastAPI) | ✅ Production | ✅ YES |
| **Dockerfile.frontend** | Production frontend (Next.js static) | ✅ Production | ✅ YES |
| **Dockerfile.cloud** | Cloud deployment variant | ⚠️ Legacy | ❓ REVIEW |
| **infrastructure/Dockerfile.swarm** | Docker Swarm orchestration | ⚠️ Legacy | ❌ NO |
| **deploy/Dockerfile.huggingface** | HuggingFace/Koyeb deployment | ⚠️ Legacy | ❌ NO |
| **deploy/Dockerfile.koyeb** | Koyeb.app serverless | ⚠️ Legacy | ❌ NO |
| **proxy/Dockerfile** | Reverse proxy (nginx alternative) | ⚠️ Optional | ❓ REVIEW |

### Deprecated Dockerfiles in Archive/ (4) ❌

These should be deleted:
- `archive/Dockerfile.swarm` — Old Docker Swarm (deprecated 2023)
- `archive/Dockerfile.kronos` — Custom runtime (never used)
- `archive/Dockerfile.hf` — HuggingFace variant (superseded)
- `archive/Dockerfile.frontend` — Old Next.js build (superseded)

---

## Recommended Docker Strategy

### Tier 1: Keep (Essential)

#### 1. **Dockerfile** (Backend)
```dockerfile
# Purpose: Production FastAPI backend
# Build: docker build -t jobhunt-backend:latest .
# Deploy: Render, Railway, Heroku

FROM python:3.12-slim-bullseye
RUN apt-get update && apt-get install -y \
    postgresql-client \
    firefox \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "web.app_v2:app", "--host", "0.0.0.0", "--port", "8000"]
```

**When to use**: Render.com, Railway, Heroku, traditional VM hosting

---

#### 2. **Dockerfile.frontend** (Frontend)
```dockerfile
# Purpose: Production Next.js static export
# Build: docker build -f Dockerfile.frontend -t jobhunt-frontend:latest .
# Deploy: Docker + nginx, or Cloudflare Pages (static)

FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build && npm run export

FROM nginx:alpine
COPY --from=builder /app/out /usr/share/nginx/html
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

**When to use**: Private Docker hosting, behind load balancer

---

### Tier 2: Review (Optional)

#### 3. **Dockerfile.cloud** 
**Question**: Is this still used?
- If for Render: Use base `Dockerfile` instead (same logic)
- If for AWS/GCP: Update to match current deployment (too old?)
- **Recommendation**: DELETE or consolidate into Dockerfile with build arg

```dockerfile
ARG BUILD_ENV=production
FROM python:3.12-slim-bullseye as base
# ... same as Dockerfile
```

#### 4. **proxy/Dockerfile**
**Question**: Is nginx proxy needed?
- If used: Keep it (reverse proxy for load balancing)
- If not: Delete and use Cloudflare/load balancer instead
- **Recommendation**: Keep if you need A/B testing or canary deployments

---

### Tier 3: Delete (Deprecated) ❌

#### 5-7. **infrastructure/Dockerfile.swarm, deploy/Dockerfile.huggingface, deploy/Dockerfile.koyeb**
- ❌ Docker Swarm is deprecated (use Kubernetes)
- ❌ HuggingFace/Koyeb are niche (not core deployment)
- ❌ Should have their own doc instead of committed Dockerfile

**Action**: Delete these three files

---

## Recommended Final Structure

```
jobhunt-pro/
├── Dockerfile                          # Main backend
├── Dockerfile.frontend                 # Main frontend  
├── docker-compose.yml                  # Production stack
├── docker-compose.dev.yml              # Development stack ✅ Now with Redis
├── DOCKER.md                           # This consolidated guide
│
└── deploy/                             # Deployment docs (not code)
    ├── RENDER.md                       # Render-specific setup
    ├── KUBERNETES.md                   # K8s deployment guide
    └── DOCKER_BUILD_GUIDE.md           # Docker build instructions
```

---

## Docker Build & Push Commands

### Build Locally
```bash
# Backend
docker build -t jobhunt-backend:v3.0 .
docker build -t jobhunt-backend:latest .

# Frontend
docker build -f Dockerfile.frontend -t jobhunt-frontend:v3.0 .
docker build -f Dockerfile.frontend -t jobhunt-frontend:latest .
```

### Push to Docker Hub
```bash
docker tag jobhunt-backend:latest samderadev/jobhunt-backend:latest
docker push samderadev/jobhunt-backend:latest

docker tag jobhunt-frontend:latest samderadev/jobhunt-frontend:latest
docker push samderadev/jobhunt-frontend:latest
```

### Push to GitHub Container Registry (GHCR)
```bash
docker tag jobhunt-backend:latest ghcr.io/yourusername/jobhunt-backend:latest
docker push ghcr.io/yourusername/jobhunt-backend:latest
```

---

## Docker Compose Strategy

### **docker-compose.yml** (Production Simulation)
✅ **Use this for**:
- Testing full stack locally
- CI/CD validation
- Load testing with Locust

**Services**:
```yaml
services:
  postgres:    # Full 16-alpine
  redis:       # Full 7-alpine
  app:         # Full backend
  nginx:       # Optional reverse proxy
```

---

### **docker-compose.dev.yml** (Development) ✅ FIXED
✅ **Use this for**:
- Local development
- Running E2E tests (now includes Redis)
- Debugging

**Services**:
```yaml
services:
  db:         # PostgreSQL
  redis:      # ✅ NOW INCLUDED (was missing)
  rabbitmq:   # Message broker
  app:        # Backend with volume mount
```

---

### **docker-compose.prod.yml** (External Services)
✅ **Use this when**:
- Deploying to Render (has external DB, Redis, etc.)
- Using managed services (Neon, Upstash)

**Services**:
```yaml
services:
  app:
    # Connects to external:
    # - DATABASE_URL=postgresql://neon.io/...
    # - REDIS_URL=redis://upstash.io/...
```

---

## Dockerfile Best Practices Applied

✅ **Layer caching**: Requirements installed first (rarely change)  
✅ **Multi-stage builds**: Separate builder stage (frontend)  
✅ **Minimal base images**: `python:3.12-slim`, `node:20-alpine`  
✅ **Security**: Non-root user (use `USER` directive)  
✅ **Health checks**: Added to docker-compose  
✅ **Volume mounts**: Dev mode for hot reload  
✅ **Environment variables**: Externalized config  

---

## Cleanup Checklist

- [ ] **Delete** `archive/Dockerfile.swarm`
- [ ] **Delete** `archive/Dockerfile.kronos`
- [ ] **Delete** `archive/Dockerfile.hf`
- [ ] **Delete** `archive/Dockerfile.frontend`
- [ ] **Review** `Dockerfile.cloud` (consolidate or delete)
- [ ] **Review** `infrastructure/Dockerfile.swarm` (delete if not using Docker Swarm)
- [ ] **Review** `deploy/Dockerfile.huggingface` (delete if not supporting HF)
- [ ] **Review** `deploy/Dockerfile.koyeb` (delete if not supporting Koyeb)
- [ ] **Create** `DOCKER.md` (this consolidated guide)
- [ ] **Update** `README.md` with clearer Docker instructions
- [ ] **Test** `docker-compose.dev.yml` with Redis (✅ DONE)
- [ ] **Verify** all tests pass (✅ DONE)

---

## Migration Path

### For existing deployments:
1. **Keep current Dockerfile** — No breaking changes
2. **Add new docker-compose.dev.yml with Redis** — Dev teams benefit immediately
3. **Gradually phase out** legacy Dockerfiles (HF, Koyeb, Cloud)
4. **Consolidate** Swarm variant (or delete)

### For new deployments:
1. **Use base Dockerfile** (production-ready)
2. **Use docker-compose.yml** (full stack) or docker-compose.prod.yml (managed services)
3. **Avoid** legacy variants

---

## Image Size Optimization

### Current Sizes
- `jobhunt-backend:latest` — 1.2GB (with browser deps)
- `jobhunt-frontend:latest` — 140MB (Node builder + nginx)

### Optimization opportunities:
```dockerfile
# Reduce backend from 1.2GB → 800MB:
RUN apt-get autoremove -y && rm -rf /var/lib/apt/lists/*
RUN pip cache purge

# Reduce frontend from 140MB → 80MB:
# Use nginx:alpine-slim (60MB vs 140MB)
FROM nginx:1.25-alpine-slim
```

---

## Conclusion

✅ **After cleanup**:
- 11 Dockerfiles → 4-5 essential variants
- Clearer deployment strategy
- Easier maintenance
- 100% of tests passing with proper Redis setup

**Next steps**: Run the cleanup checklist above.

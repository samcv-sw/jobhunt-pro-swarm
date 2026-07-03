# Helm Chart Design Analysis for JobHunt Pro Stack

This document details the analysis and proposed architecture for packaging the **JobHunt Pro** stack as a Helm chart.

---

## 1. Executive Summary
We propose a production-grade, highly customizable Helm chart structure under `deploy/k8s/` that orchestrates a Next.js frontend, FastAPI backend, distributed Celery worker pools, and caching/database layers. It handles the browser-side SQLite WASM/OPFS synchronization design, incorporates a multi-container pod pattern to safely share SQLite local databases under `ReadWriteOnce` storage constraints, and implements independent Celery worker pools matching specialized application queues.

---

## 2. Component Analysis & Dockerfile Mapping

### A. FastAPI Backend (`app`)
- **Source Dockerfile**: `Dockerfile` (or `Dockerfile.cloud` for single-user cloud setups)
- **Runtime Port**: `8000` (FastAPI)
- **Default Command**: `uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4`
- **Volume Mounts**: `/app/data` (for SQLite storage if not using cloud Postgres mode) and `/app/logs`.
- **Environment Variables**:
  - `DATABASE_URL`: Connection string for PostgreSQL (e.g., `postgresql+asyncpg://...`).
  - `DATABASE_URL_SYNC`: Synchronous PostgreSQL URL.
  - `REDIS_URL`: Message broker and cache endpoint.
  - `DB_PATH`: Location of the SQLite file (defaults to `/app/data/jobhunt_saas_v2.db`).
  - API keys and SMTP configs (Gemini, Groq, Brevo, Telegram, Outlook, Gmail).

### B. Next.js Frontend (`frontend`)
- **Source Dockerfile**: `Dockerfile.frontend`
- **Runtime Port**: `3000`
- **Build Mode**: Next.js is configured with `output: "export"` (`next.config.ts`), generating a static SPA in the `out` directory.
- **Serving Strategy**: Although the Next.js app compiles to static files, the current `Dockerfile.frontend` serves the app via a Node.js runner (`npm start`). In K8s, we run this as a frontend deployment and route traffic to it via Ingress, ensuring `NEXT_PUBLIC_API_URL` is set correctly (or defaulted to the same host using relative paths).

### C. Celery Workers (`celery-worker`)
- **Source Dockerfile**: `Dockerfile`
- **Command**: `celery -A backend.celery_app worker --loglevel=info -P solo`
- **Queues**: Routed individually via `backend.celery_app`:
  - `scraping` (requires system Chrome/scraping libraries, matching `Dockerfile.swarm`)
  - `ai_inference` (requires API keys)
  - `email_sender` (requires SMTP rotation configurations)
- **Design decision**: Rather than deploying a single massive worker deployment, the Helm chart should allow defining multiple independent worker pools (deployments) with separate resource constraints, commands, and scaling metrics.

### D. SQLite Sync Worker (`sync-worker`)
- **Source Dockerfile**: `Dockerfile`
- **Command**: `python -m backend.sync_worker`
- **Purpose**: Continuously monitors the SQLite `sync_outbox` table and pushes transactions asynchronously to Postgres every 5 seconds.
- **Storage Dependency**: Must mount the exact same SQLite database file as the FastAPI backend container.

### E. Redis & Postgres
- **Docker Compose Mapping**: `redis:7-alpine`, `postgres:16-alpine` (mounting `init.sql` to `/docker-entrypoint-initdb.d/init.sql`).
- **Helm Design**: Support deploying lightweight PostgreSQL and Redis services internally via sub-charts or templates, while allowing easy routing to external, managed database instances (e.g. Neon PostgreSQL, AWS ElastiCache).

---

## 3. SQLite OPFS & Volume Claims Deep Dive

### Client-side OPFS vs. Cluster-side Persistent Volumes
1. **Client-side (Browser)**: The Next.js frontend utilizes `wasm-db.ts` to access `jobhunt_local.db` within the user's browser via the **Origin Private File System (OPFS)**. This is a local, serverless storage solution running in the client browser web workers and does **not** map to Kubernetes volume claims.
2. **Cluster-side (Server)**: The FastAPI backend and SQLite sync worker run on the server. They read and write a server-side SQLite database located at `DB_PATH` (`/app/data/jobhunt_saas_v2.db`). This file **requires** server-side persistence using a Kubernetes `PersistentVolume` (PV) and `PersistentVolumeClaim` (PVC).

### Crucial Architectural Constraint: Storage Access Modes
If the FastAPI backend (`app`) and the `sync-worker` run as **separate K8s Deployments**:
- They must share the same physical SQLite file on a PVC.
- This requires a `ReadWriteMany` (RWX) storage class (such as NFS, EFS, or CephFS).
- On standard cloud providers (AWS, GCP, Azure), default dynamic provisioners only provide `ReadWriteOnce` (RWO), which blocks mounting the same volume across multiple deployments.

#### Multi-Persona Evaluation Council Synthesis

*   **The Skeptic's Critique**: "If we deploy the backend and the sync-worker in separate pods, they will fail to start on standard clusters because RWO storage cannot be shared between different pods."
*   **The Domain Expert's Architecture**: To provide a fully robust, cloud-agnostic solution, we implement a **dual design choice** in the Helm chart:
    1.  **Shared-Pod Sidecar Pattern (Recommended for RWO)**: Run the FastAPI backend container and the SQLite sync-worker container in the **same Pod** (Deployment). They share a local SQLite directory `/app/data` using a local volume or a standard RWO PersistentVolumeClaim. Since they are co-located in the same Pod, Kubernetes respects RWO constraints.
    2.  **Shared-PVC Multi-Deployment Pattern**: Run them as separate K8s Deployments. This requires `ReadWriteMany` (RWX) and is enabled via a config flag in `values.yaml`.

---

## 4. Proposed Helm Chart Structure

```text
deploy/k8s/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── _helpers.tpl
│   ├── secret.yaml
│   ├── configmap.yaml
│   ├── pvc-sqlite.yaml
│   ├── backend-deployment.yaml
│   ├── backend-service.yaml
│   ├── frontend-deployment.yaml
│   ├── frontend-service.yaml
│   ├── celery-worker-deployment.yaml
│   ├── sync-worker-deployment.yaml
│   ├── postgres-deployment.yaml
│   ├── postgres-service.yaml
│   ├── postgres-init-configmap.yaml
│   ├── redis-deployment.yaml
│   ├── redis-service.yaml
│   ├── ingress.yaml
│   └── hpa.yaml
```

---

## 5. YAML Resource Definitions

### Chart.yaml
```yaml
apiVersion: v2
name: jobhunt-pro
description: Production-grade Helm chart for JobHunt Pro orchestration
type: application
version: 1.0.0
appVersion: "17.0"
dependencies:
  - name: postgresql
    version: 12.x.x
    repository: https://charts.bitnami.com/bitnami
    condition: postgresql.enabled
  - name: redis
    version: 18.x.x
    repository: https://charts.bitnami.com/bitnami
    condition: redis.enabled
```

### values.yaml (Structure & Defaults)
```yaml
# Global configuration variables
global:
  environment: production

# Image configurations
images:
  backend:
    repository: jobhuntpro/backend
    tag: v17.0
    pullPolicy: IfNotPresent
  frontend:
    repository: jobhuntpro/frontend
    tag: v17.0
    pullPolicy: IfNotPresent

# FastAPI Backend deployment settings
backend:
  replicaCount: 2
  resources:
    limits:
      cpu: "1"
      memory: 1Gi
    requests:
      cpu: 250m
      memory: 512Mi
  # If true, runs the sync-worker as a sidecar container in the backend pod (ideal for RWO volume claims)
  runSyncWorkerAsSidecar: true

# Next.js Frontend settings
frontend:
  replicaCount: 2
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 100m
      memory: 256Mi

# SQLite Storage Configuration
sqlite:
  persistence:
    enabled: true
    accessMode: ReadWriteOnce # Change to ReadWriteMany if running sync worker independently
    size: 5Gi
    storageClass: ""
    mountPath: /app/data
    dbFilename: jobhunt_saas_v2.db

# SQLite Sync Worker (Only deployed separately if runSyncWorkerAsSidecar is false)
syncWorker:
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 100m
      memory: 128Mi

# Distributed Celery Worker pools configuration
celery:
  pools:
    scraping:
      replicas: 2
      command: ["celery", "-A", "backend.celery_app", "worker", "-Q", "scraping", "--loglevel=info", "-P", "solo"]
      resources:
        limits:
          cpu: "2"
          memory: 4Gi # Higher memory for running headless Chrome scrapers
        requests:
          cpu: 500m
          memory: 1Gi
    ai-inference:
      replicas: 1
      command: ["celery", "-A", "backend.celery_app", "worker", "-Q", "ai_inference", "--loglevel=info", "-P", "solo"]
      resources:
        limits:
          cpu: 500m
          memory: 512Mi
        requests:
          cpu: 100m
          memory: 256Mi
    email-sender:
      replicas: 1
      command: ["celery", "-A", "backend.celery_app", "worker", "-Q", "email_sender", "--loglevel=info", "-P", "solo"]
      resources:
        limits:
          cpu: 500m
          memory: 512Mi
        requests:
          cpu: 100m
          memory: 256Mi

# Internal database/cache configuration templates (when sub-charts are disabled)
postgresql:
  enabled: true
  auth:
    database: jobhunt_pro
    username: jobhunt
    password: "jobhunt_secret_2026"
  persistence:
    size: 10Gi

redis:
  enabled: true
  architecture: standalone
  auth:
    enabled: false

# External databases (used when postgresql.enabled or redis.enabled is false)
externalDb:
  postgresUrl: ""
  postgresUrlSync: ""
  redisUrl: ""

# Application configuration, mapping to configmaps and secrets
appConfig:
  candidateEmail: "samsalameh.cv@gmail.com"
  candidatePhone: "+961 71 019 053"
  maxWorkers: "200"
  dailySendLimit: "2000"
  dryRun: "false"
  secretKey: "change-this-in-production-k8s"

# Sensitive API Keys, loaded via Kubernetes Secrets
secrets:
  geminiApiKey: ""
  groqApiKey: ""
  brevoApiKey: ""
  brevoAccountEmail: "samsalameh.cv@gmail.com"
  telegramBotToken: ""
  telegramChatId: ""
  gmailSmtpUser1: ""
  gmailAppPassword1: ""
  gmailSmtpUser2: ""
  gmailAppPassword2: ""
  outlookUser1: ""
  outlookPassword1: ""
  cryptoBtcAddress: ""
  cryptoEthAddress: ""
  cryptoUsdtAddress: ""
  cryptoLtcAddress: ""

# Ingress Configuration (Routing API and Static Frontend)
ingress:
  enabled: true
  className: "nginx"
  annotations:
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
    # Ensure websocket support is active
    nginx.ingress.kubernetes.io/websocket-services: "jobhunt-backend"
  hosts:
    - host: jobhunt.local
      paths:
        - path: /
          pathType: Prefix
          backend: frontend
        - path: /api
          pathType: Prefix
          backend: backend
        - path: /ws
          pathType: Prefix
          backend: backend
        - path: /docs
          pathType: Prefix
          backend: backend
        - path: /redoc
          pathType: Prefix
          backend: backend
  tls: []
```

---

## 6. Key Template Drafts

### templates/pvc-sqlite.yaml
```yaml
{{- if .Values.sqlite.persistence.enabled -}}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "jobhunt-pro.fullname" . }}-sqlite
  labels:
    {{- include "jobhunt-pro.labels" . | nindent 4 }}
spec:
  accessModes:
    - {{ .Values.sqlite.persistence.accessMode }}
  resources:
    requests:
      storage: {{ .Values.sqlite.persistence.size | quote }}
  {{- if .Values.sqlite.persistence.storageClass }}
  storageClassName: {{ .Values.sqlite.persistence.storageClass | quote }}
  {{- end }}
{{- end }}
```

### templates/backend-deployment.yaml (Shared-Pod Sidecar Pattern)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "jobhunt-pro.fullname" . }}-backend
  labels:
    {{- include "jobhunt-pro.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.backend.replicaCount }}
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ include "jobhunt-pro.name" . }}-backend
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {{ include "jobhunt-pro.name" . }}-backend
    spec:
      volumes:
        - name: sqlite-storage
          {{- if .Values.sqlite.persistence.enabled }}
          persistentVolumeClaim:
            claimName: {{ include "jobhunt-pro.fullname" . }}-sqlite
          {{- else }}
          emptyDir: {}
          {{- end }}
      containers:
        # 1. FastAPI Backend Container
        - name: backend
          image: "{{ .Values.images.backend.repository }}:{{ .Values.images.backend.tag }}"
          imagePullPolicy: {{ .Values.images.backend.pullPolicy }}
          ports:
            - containerPort: 8000
              name: http-api
          envFrom:
            - configMapRef:
                name: {{ include "jobhunt-pro.fullname" . }}-config
            - secretRef:
                name: {{ include "jobhunt-pro.fullname" . }}-secrets
          env:
            - name: DATABASE_URL
              value: {{ include "jobhunt-pro.postgres-url" . | quote }}
            - name: DATABASE_URL_SYNC
              value: {{ include "jobhunt-pro.postgres-sync-url" . | quote }}
            - name: REDIS_URL
              value: {{ include "jobhunt-pro.redis-url" . | quote }}
            - name: DB_PATH
              value: "{{ .Values.sqlite.persistence.mountPath }}/{{ .Values.sqlite.persistence.dbFilename }}"
          volumeMounts:
            - name: sqlite-storage
              mountPath: {{ .Values.sqlite.persistence.mountPath }}
          resources:
            {{- toYaml .Values.backend.resources | nindent 12 }}
          healthCheck:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10

        # 2. SQLite Sync Worker (Sidecar Container sharing SQLite volume)
        {{- if .Values.backend.runSyncWorkerAsSidecar }}
        - name: sync-worker
          image: "{{ .Values.images.backend.repository }}:{{ .Values.images.backend.tag }}"
          imagePullPolicy: {{ .Values.images.backend.pullPolicy }}
          command: ["python", "-m", "backend.sync_worker"]
          envFrom:
            - configMapRef:
                name: {{ include "jobhunt-pro.fullname" . }}-config
            - secretRef:
                name: {{ include "jobhunt-pro.fullname" . }}-secrets
          env:
            - name: DATABASE_URL
              value: {{ include "jobhunt-pro.postgres-url" . | quote }}
            - name: DATABASE_URL_SYNC
              value: {{ include "jobhunt-pro.postgres-sync-url" . | quote }}
            - name: REDIS_URL
              value: {{ include "jobhunt-pro.redis-url" . | quote }}
            - name: DB_PATH
              value: "{{ .Values.sqlite.persistence.mountPath }}/{{ .Values.sqlite.persistence.dbFilename }}"
          volumeMounts:
            - name: sqlite-storage
              mountPath: {{ .Values.sqlite.persistence.mountPath }}
          resources:
            {{- toYaml .Values.syncWorker.resources | nindent 12 }}
        {{- end }}
```

### templates/celery-worker-deployment.yaml
```yaml
{{- range $poolName, $poolConfig := .Values.celery.pools }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "jobhunt-pro.fullname" $ }}-celery-{{ $poolName }}
  labels:
    {{- include "jobhunt-pro.labels" $ | nindent 4 }}
    role: celery-worker
    pool: {{ $poolName }}
spec:
  replicas: {{ $poolConfig.replicas }}
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ include "jobhunt-pro.name" $ }}-celery-{{ $poolName }}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {{ include "jobhunt-pro.name" $ }}-celery-{{ $poolName }}
    spec:
      containers:
        - name: celery-worker
          image: "{{ $.Values.images.backend.repository }}:{{ $.Values.images.backend.tag }}"
          imagePullPolicy: {{ $.Values.images.backend.pullPolicy }}
          command: {{ $poolConfig.command | toJson }}
          envFrom:
            - configMapRef:
                name: {{ include "jobhunt-pro.fullname" $ }}-config
            - secretRef:
                name: {{ include "jobhunt-pro.fullname" $ }}-secrets
          env:
            - name: DATABASE_URL
              value: {{ include "jobhunt-pro.postgres-url" $ | quote }}
            - name: DATABASE_URL_SYNC
              value: {{ include "jobhunt-pro.postgres-sync-url" $ | quote }}
            - name: REDIS_URL
              value: {{ include "jobhunt-pro.redis-url" $ | quote }}
          resources:
            {{- toYaml $poolConfig.resources | nindent 12 }}
---
{{- end }}
```

---

## 7. Verification Method
To verify the syntax and configuration logic of the proposed Helm chart:
1. **Linter Check**: Execute `helm lint deploy/k8s/` in the shell to ensure syntax rules, chart definitions, and structure conform to standard constraints.
2. **Template Expansion Check**: Execute `helm template jobhunt-pro deploy/k8s/ --values deploy/k8s/values.yaml` to verify the parsed K8s resource definitions are correctly outputted without missing tokens or syntax errors.

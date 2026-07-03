# JobHunt Pro — Kubernetes Helm Chart Architecture & Design Proposal

This report analyzes the architecture of the JobHunt Pro application stack and proposes a comprehensive, production-ready Helm chart design under `deploy/k8s/` to orchestrate all components in a scalable Kubernetes cluster.

---

## 1. Executive Summary & Component Analysis

Following a detailed investigation of the docker-compose configurations, Dockerfiles, and database shims in the codebase, the application architecture consists of the following components:

1.  **FastAPI Backend (App Service)**:
    *   **Dockerfile**: Uses `python:3.12-slim` (exposes port `8000`). Run command: `uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4`.
    *   **Dual-Database Shim**: Leverages `core/pg_sqlite_shim.py`. When `DATABASE_URL` (Postgres) is set, it uses Postgres for primary tables (like users, profiles, campaigns, orders, etc.). However, it writes transactional mutations locally to a SQLite database (`DB_PATH` or `/app/data/jobhunt_saas_v2.db`) in WAL mode for zero-latency operations, writing mutation logs to the `ps_crud_outbox` table.
2.  **Next.js Frontend**:
    *   **Dockerfile**: Uses a two-stage build (`node:20-alpine`, exposes port `3000`).
    *   **Wasm + OPFS Pattern**: Compiled in static export mode (`output: "export"`). It utilizes `frontend/src/app/db/wasm-db.ts` to spin up a client-side WebAssembly SQLite engine. This engine runs inside the user's browser in a background web worker and stores data via the browser's **Origin Private File System (OPFS)**. It requires **no server-side volume claims** for client-side SQLite storage.
3.  **SQLite Sync Worker**:
    *   **Execution**: Starts via `python -m backend.sync_worker`.
    *   **Role**: Continuously reads unsynced mutation records from the local SQLite database (`ps_crud_outbox`) and streams them to the remote Postgres database every 5 seconds.
    *   **Constraint**: Must read the exact same SQLite database file as the FastAPI backend container.
4.  **Celery Workers**:
    *   **Broker**: Uses Redis (on port `6379`).
    *   **Queues**: Task routing is configured in `backend/celery_app.py`:
        *   `backend.tasks.scrape_jobs` -> routed to `scraping` queue (requires browser engines/scraping tools, matching `Dockerfile.swarm`).
        *   `backend.tasks.generate_cover_letter` -> routed to `ai_inference` queue (requires API keys).
        *   `backend.tasks.send_application_email` -> routed to `email_sender` queue (requires SMTP credentials).
5.  **PostgreSQL & Redis**:
    *   **Postgres**: Initialized with `init.sql` schema and price seeds.
    *   **Redis**: Configured with `--appendonly yes` to persist caching and brokering states.

---

## 2. Multi-Persona Evaluation Council Review

Before finalizing the Helm chart specifications, the design was audited against key failure modes:

*   **Skeptic's Critique**: *"If the FastAPI backend and the SQLite sync-worker are deployed as separate Kubernetes pods, they will fail to mount the same SQLite file on standard cloud providers. Standard block storage (like AWS EBS or GCP Persistent Disk) only supports `ReadWriteOnce` (RWO), which blocks sharing between separate pods."*
*   **Domain Expert's Solution (Sidecar Injection)**: To ensure the Helm chart works on any cluster without requiring an expensive `ReadWriteMany` (RWX) network filesystem, we implement a **dual storage pattern**:
    1.  **Sidecar Mode (Default)**: The FastAPI pod runs both the `fastapi` backend container and the `sync-worker` container in the same pod. They share a local SQLite path (`/app/data`) via a standard RWO volume. This respects RWO limits and guarantees zero-latency, local-disk execution.
    2.  **Shared-PVC Mode**: If the user has a storage class supporting `ReadWriteMany` (RWX), they can set `sqlite.persistence.useSharedPvc=true` in `values.yaml`. This launches the `sync-worker` as an independent pod.
*   **Adversary's Critique**: *"Routing all Celery workers in one massive deployment will cause bottlenecking. Headless Chrome scraping tasks require huge memory limits (e.g. 4Gi) and cause CPU spikes. If they run on the same pods as the AI inference worker or SMTP sender, they will cause OOM crashes or block the light tasks."*
*   **Domain Expert's Solution (Queue-Isolated Worker Pools)**: We design the Celery templates using a loop over `.Values.celery.pools`. This creates **independent deployments** for each queue with tailored CPU/Memory limits, replica counts, and labels (e.g. higher memory for `scraping` workers, lighter resources for `email_sender`).

---

## 3. Proposed Helm Chart Directory Structure

We will create the Helm chart under `deploy/k8s/` with this layout:

```text
deploy/k8s/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── _helpers.tpl
    ├── configmap.yaml
    ├── secrets.yaml
    ├── pvc-sqlite.yaml
    ├── postgres-init-configmap.yaml
    ├── postgres-statefulset.yaml
    ├── postgres-service.yaml
    ├── redis-deployment.yaml
    ├── redis-service.yaml
    ├── backend-deployment.yaml
    ├── backend-service.yaml
    ├── frontend-deployment.yaml
    ├── frontend-service.yaml
    ├── celery-worker-deployment.yaml
    ├── sync-worker-deployment.yaml
    └── ingress.yaml
```

---

## 4. Helm Chart Configuration & Templates

Here are the complete, copy-paste-ready template files for the chart.

### `Chart.yaml`
```yaml
apiVersion: v2
name: jobhunt-pro
description: Production-grade Helm chart orchestrating Next.js, FastAPI, Celery, Redis, and Postgres for JobHunt Pro.
type: application
version: 1.0.0
appVersion: "3.0.0"
```

### `values.yaml`
```yaml
# Global Domain and Endpoint settings
global:
  domain: jobhunt.local
  apiUrl: "http://jobhunt.local/api"

# Image settings for Backend and Frontend
images:
  backend:
    repository: jobhuntpro/backend
    tag: latest
    pullPolicy: IfNotPresent
  frontend:
    repository: jobhuntpro/frontend
    tag: latest
    pullPolicy: IfNotPresent

# FastAPI Backend service configurations
backend:
  replicaCount: 1
  resources:
    limits:
      cpu: "1"
      memory: 1Gi
    requests:
      cpu: 250m
      memory: 256Mi
  # Runs the SQLite sync-worker as a sidecar container in the backend pod
  # Set this to true to support ReadWriteOnce (RWO) storage classes
  runSyncWorkerAsSidecar: true

# Next.js Frontend configurations
frontend:
  replicaCount: 1
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 100m
      memory: 128Mi

# Server-side SQLite Persistence
sqlite:
  persistence:
    enabled: true
    accessMode: ReadWriteOnce # Use ReadWriteMany if deploying sync-worker as a separate pod
    size: 5Gi
    storageClass: ""
    mountPath: /app/data
    dbFilename: jobhunt_saas_v2.db

# SQLite Sync Worker (Only deployed as separate pod if backend.runSyncWorkerAsSidecar is false)
syncWorker:
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 100m
      memory: 128Mi

# Isolated Celery Worker Pools
celery:
  pools:
    scraping:
      replicas: 2
      command: ["celery", "-A", "backend.celery_app", "worker", "-Q", "scraping", "--loglevel=info", "-P", "solo"]
      resources:
        limits:
          cpu: "2"
          memory: 4Gi # Chrome headless requires more memory
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

# Internal PostgreSQL (If disabled, uses externalDb settings)
postgres:
  enabled: true
  image:
    repository: postgres
    tag: 16-alpine
    pullPolicy: IfNotPresent
  db:
    name: jobhunt_pro
    user: jobhunt
    password: jobhunt_secret_2026
  persistence:
    size: 8Gi
    storageClass: ""

# Internal Redis
redis:
  enabled: true
  image:
    repository: redis
    tag: 7-alpine
    pullPolicy: IfNotPresent
  persistence:
    enabled: true
    size: 2Gi
    storageClass: ""

# External DBs (Used if internal postgres/redis are disabled)
externalDb:
  postgresUrl: ""
  postgresUrlSync: ""
  redisUrl: ""

# General application variables
appConfig:
  candidateEmail: "samsalameh.cv@gmail.com"
  candidatePhone: "+96171019053"
  maxWorkers: "200"
  dailySendLimit: "2000"
  dryRun: "false"
  secretKey: "change-this-in-production-secret"

# Secrets (Encrypted via templates/secrets.yaml)
secrets:
  geminiApiKey: "CHANGE_ME"
  groqApiKey: "CHANGE_ME"
  brevoApiKey: "CHANGE_ME"
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

# Ingress controller configurations
ingress:
  enabled: true
  className: "nginx"
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
    nginx.ingress.kubernetes.io/websocket-services: "jobhunt-backend"
```

### `templates/_helpers.tpl`
```tpl
{{/*
Expand the name of the chart.
*/}}
{{- define "jobhunt-pro.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "jobhunt-pro.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "jobhunt-pro.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "jobhunt-pro.labels" -}}
helm.sh/chart: {{ include "jobhunt-pro.chart" . }}
{{ include "jobhunt-pro.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "jobhunt-pro.selectorLabels" -}}
app.kubernetes.io/name: {{ include "jobhunt-pro.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
PostgreSQL connection URL resolver
*/}}
{{- define "jobhunt-pro.postgres-url" -}}
{{- if .Values.postgres.enabled -}}
{{- printf "postgresql+asyncpg://%s:%s@%s-postgres:5432/%s" .Values.postgres.db.user .Values.postgres.db.password (include "jobhunt-pro.fullname" .) .Values.postgres.db.name -}}
{{- else -}}
{{- .Values.externalDb.postgresUrl -}}
{{- end -}}
{{- end }}

{{/*
PostgreSQL synchronous connection URL resolver
*/}}
{{- define "jobhunt-pro.postgres-sync-url" -}}
{{- if .Values.postgres.enabled -}}
{{- printf "postgresql://%s:%s@%s-postgres:5432/%s" .Values.postgres.db.user .Values.postgres.db.password (include "jobhunt-pro.fullname" .) .Values.postgres.db.name -}}
{{- else -}}
{{- .Values.externalDb.postgresUrlSync -}}
{{- end -}}
{{- end }}

{{/*
Redis connection URL resolver
*/}}
{{- define "jobhunt-pro.redis-url" -}}
{{- if .Values.redis.enabled -}}
{{- printf "redis://%s-redis:6379/0" (include "jobhunt-pro.fullname" .) -}}
{{- else -}}
{{- .Values.externalDb.redisUrl -}}
{{- end -}}
{{- end }}
```

### `templates/configmap.yaml`
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "jobhunt-pro.fullname" . }}-config
  labels:
    {{- include "jobhunt-pro.labels" . | nindent 4 }}
data:
  DATABASE_URL: {{ include "jobhunt-pro.postgres-url" . | quote }}
  DATABASE_URL_SYNC: {{ include "jobhunt-pro.postgres-sync-url" . | quote }}
  REDIS_URL: {{ include "jobhunt-pro.redis-url" . | quote }}
  NEXT_PUBLIC_API_URL: {{ .Values.global.apiUrl | quote }}
  DB_PATH: "{{ .Values.sqlite.persistence.mountPath }}/{{ .Values.sqlite.persistence.dbFilename }}"
  LOCAL_DATABASE_URL: "sqlite+aiosqlite:///{{ .Values.sqlite.persistence.mountPath }}/jobhunt_local.db"
  CANDIDATE_EMAIL: {{ .Values.appConfig.candidateEmail | quote }}
  CANDIDATE_PHONE: {{ .Values.appConfig.candidatePhone | quote }}
  MAX_WORKERS: {{ .Values.appConfig.maxWorkers | quote }}
  DAILY_SEND_LIMIT: {{ .Values.appConfig.dailySendLimit | quote }}
  DRY_RUN: {{ .Values.appConfig.dryRun | quote }}
  SECRET_KEY: {{ .Values.appConfig.secretKey | quote }}
```

### `templates/secrets.yaml`
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "jobhunt-pro.fullname" . }}-secrets
  labels:
    {{- include "jobhunt-pro.labels" . | nindent 4 }}
type: Opaque
data:
  GEMINI_API_KEY: {{ .Values.secrets.geminiApiKey | b64enc | quote }}
  GROQ_API_KEY: {{ .Values.secrets.groqApiKey | b64enc | quote }}
  BREVO_API_KEY: {{ .Values.secrets.brevoApiKey | b64enc | quote }}
  BREVO_ACCOUNT_EMAIL: {{ .Values.secrets.brevoAccountEmail | b64enc | quote }}
  TELEGRAM_BOT_TOKEN: {{ .Values.secrets.telegramBotToken | b64enc | quote }}
  TELEGRAM_CHAT_ID: {{ .Values.secrets.telegramChatId | b64enc | quote }}
  GMAIL_SMTP_USER_1: {{ .Values.secrets.gmailSmtpUser1 | b64enc | quote }}
  GMAIL_APP_PASSWORD_1: {{ .Values.secrets.gmailAppPassword1 | b64enc | quote }}
  GMAIL_SMTP_USER_2: {{ .Values.secrets.gmailSmtpUser2 | b64enc | quote }}
  GMAIL_APP_PASSWORD_2: {{ .Values.secrets.gmailAppPassword2 | b64enc | quote }}
  OUTLOOK_USER_1: {{ .Values.secrets.outlookUser1 | b64enc | quote }}
  OUTLOOK_PASSWORD_1: {{ .Values.secrets.outlookPassword1 | b64enc | quote }}
  CRYPTO_BTC_ADDRESS: {{ .Values.secrets.cryptoBtcAddress | b64enc | quote }}
  CRYPTO_ETH_ADDRESS: {{ .Values.secrets.cryptoEthAddress | b64enc | quote }}
  CRYPTO_USDT_ADDRESS: {{ .Values.secrets.cryptoUsdtAddress | b64enc | quote }}
  CRYPTO_LTC_ADDRESS: {{ .Values.secrets.cryptoLtcAddress | b64enc | quote }}
```

### `templates/pvc-sqlite.yaml`
```yaml
{{- if and .Values.sqlite.persistence.enabled (or (not .Values.backend.runSyncWorkerAsSidecar) .Values.sqlite.persistence.useSharedPvc) -}}
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

### `templates/postgres-init-configmap.yaml`
```yaml
{{- if .Values.postgres.enabled -}}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "jobhunt-pro.fullname" . }}-postgres-init
  labels:
    {{- include "jobhunt-pro.labels" . | nindent 4 }}
data:
  init.sql: |
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";

    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(64) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        name VARCHAR(255),
        phone VARCHAR(50),
        company_name VARCHAR(255),
        user_type VARCHAR(50) DEFAULT 'jobseeker',
        wallet_balance DECIMAL(10,2) DEFAULT 0,
        total_spent DECIMAL(10,2) DEFAULT 0,
        api_key VARCHAR(64) UNIQUE,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS cv_profiles (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(64) NOT NULL,
        profile_name VARCHAR(255),
        cv_text TEXT,
        cover_letter_template TEXT,
        email_template TEXT,
        skills TEXT,
        experience_years INTEGER,
        target_titles TEXT,
        target_locations TEXT,
        home_country VARCHAR(100) DEFAULT 'Lebanon',
        min_local_salary DECIMAL(10,2) DEFAULT 0,
        min_international_salary DECIMAL(10,2) DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS campaigns (
        id SERIAL PRIMARY KEY,
        campaign_id VARCHAR(64) UNIQUE NOT NULL,
        user_id VARCHAR(64) NOT NULL,
        order_id VARCHAR(64) NOT NULL,
        profile_id INTEGER,
        status VARCHAR(50) DEFAULT 'pending',
        total_companies INTEGER DEFAULT 0,
        sent_count INTEGER DEFAULT 0,
        open_count INTEGER DEFAULT 0,
        response_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        started_at TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS job_queue (
        id SERIAL PRIMARY KEY,
        task_type TEXT NOT NULL,
        payload TEXT,
        status TEXT DEFAULT 'pending',
        retry_count INTEGER DEFAULT 0,
        max_retries INTEGER DEFAULT 3,
        next_retry_at TIMESTAMP,
        priority INTEGER DEFAULT 5,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        locked_at TIMESTAMP,
        error TEXT
    );

    CREATE TABLE IF NOT EXISTS sync_outbox_log (
        id SERIAL PRIMARY KEY,
        table_name VARCHAR(100) NOT NULL,
        record_id VARCHAR(100) NOT NULL,
        operation VARCHAR(20) NOT NULL,
        payload JSONB NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
{{- end }}
```

### `templates/postgres-statefulset.yaml`
```yaml
{{- if .Values.postgres.enabled -}}
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: {{ include "jobhunt-pro.fullname" . }}-postgres
  labels:
    {{- include "jobhunt-pro.labels" . | nindent 4 }}
    app: postgres
spec:
  serviceName: {{ include "jobhunt-pro.fullname" . }}-postgres
  replicas: 1
  selector:
    matchLabels:
      {{- include "jobhunt-pro.selectorLabels" . | nindent 6 }}
      app: postgres
  template:
    metadata:
      labels:
        {{- include "jobhunt-pro.selectorLabels" . | nindent 8 }}
        app: postgres
    spec:
      containers:
        - name: postgres
          image: "{{ .Values.postgres.image.repository }}:{{ .Values.postgres.image.tag }}"
          imagePullPolicy: {{ .Values.postgres.image.pullPolicy }}
          ports:
            - containerPort: 5432
              name: postgres
          env:
            - name: POSTGRES_DB
              value: {{ .Values.postgres.db.name | quote }}
            - name: POSTGRES_USER
              value: {{ .Values.postgres.db.user | quote }}
            - name: POSTGRES_PASSWORD
              value: {{ .Values.postgres.db.password | quote }}
          readinessProbe:
            exec:
              command: ["pg_isready", "-U", "{{ .Values.postgres.db.user }}", "-d", "{{ .Values.postgres.db.name }}"]
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            exec:
              command: ["pg_isready", "-U", "{{ .Values.postgres.db.user }}", "-d", "{{ .Values.postgres.db.name }}"]
            initialDelaySeconds: 15
            periodSeconds: 20
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
            - name: init-script
              mountPath: /docker-entrypoint-initdb.d
      volumes:
        - name: init-script
          configMap:
            name: {{ include "jobhunt-pro.fullname" . }}-postgres-init
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
      spec:
        accessModes: [ "ReadWriteOnce" ]
        resources:
          requests:
            storage: {{ .Values.postgres.persistence.size }}
        {{- if .Values.postgres.persistence.storageClass }}
        storageClassName: {{ .Values.postgres.persistence.storageClass | quote }}
        {{- end }}
{{- end }}
```

### `templates/postgres-service.yaml`
```yaml
{{- if .Values.postgres.enabled -}}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "jobhunt-pro.fullname" . }}-postgres
  labels:
    {{- include "jobhunt-pro.labels" . | nindent 4 }}
spec:
  ports:
    - port: 5432
      targetPort: 5432
      name: postgres
  selector:
    {{- include "jobhunt-pro.selectorLabels" . | nindent 4 }}
    app: postgres
{{- end }}
```

### `templates/redis-deployment.yaml`
```yaml
{{- if .Values.redis.enabled -}}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "jobhunt-pro.fullname" . }}-redis
  labels:
    {{- include "jobhunt-pro.labels" . | nindent 4 }}
    app: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      {{- include "jobhunt-pro.selectorLabels" . | nindent 6 }}
      app: redis
  template:
    metadata:
      labels:
        {{- include "jobhunt-pro.selectorLabels" . | nindent 8 }}
        app: redis
    spec:
      containers:
        - name: redis
          image: "{{ .Values.redis.image.repository }}:{{ .Values.redis.image.tag }}"
          imagePullPolicy: {{ .Values.redis.image.pullPolicy }}
          command: ["redis-server", "--appendonly", "yes"]
          ports:
            - containerPort: 6379
              name: redis
          readinessProbe:
            exec:
              command: ["redis-cli", "ping"]
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            exec:
              command: ["redis-cli", "ping"]
            initialDelaySeconds: 10
            periodSeconds: 15
          volumeMounts:
            - name: redis-data
              mountPath: /data
      volumes:
        - name: redis-data
          {{- if .Values.redis.persistence.enabled }}
          persistentVolumeClaim:
            claimName: {{ include "jobhunt-pro.fullname" . }}-redis-pvc
          {{- else }}
          emptyDir: {}
          {{- end }}
{{- if .Values.redis.persistence.enabled }}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "jobhunt-pro.fullname" . }}-redis-pvc
  labels:
    {{- include "jobhunt-pro.labels" . | nindent 4 }}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.redis.persistence.size }}
  {{- if .Values.redis.persistence.storageClass }}
  storageClassName: {{ .Values.redis.persistence.storageClass | quote }}
  {{- end }}
{{- end }}
{{- end }}
```

### `templates/redis-service.yaml`
```yaml
{{- if .Values.redis.enabled -}}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "jobhunt-pro.fullname" . }}-redis
  labels:
    {{- include "jobhunt-pro.labels" . | nindent 4 }}
spec:
  ports:
    - port: 6379
      targetPort: 6379
      name: redis
  selector:
    {{- include "jobhunt-pro.selectorLabels" . | nindent 4 }}
    app: redis
{{- end }}
```

### `templates/backend-deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "jobhunt-pro.fullname" . }}-backend
  labels:
    {{- include "jobhunt-pro.labels" . | nindent 4 }}
    app: backend
spec:
  replicas: {{ .Values.backend.replicaCount }}
  selector:
    matchLabels:
      {{- include "jobhunt-pro.selectorLabels" . | nindent 6 }}
      app: backend
  template:
    metadata:
      labels:
        {{- include "jobhunt-pro.selectorLabels" . | nindent 8 }}
        app: backend
    spec:
      volumes:
        - name: sqlite-storage
          {{- if and .Values.sqlite.persistence.enabled (or (not .Values.backend.runSyncWorkerAsSidecar) .Values.sqlite.persistence.useSharedPvc) }}
          persistentVolumeClaim:
            claimName: {{ include "jobhunt-pro.fullname" . }}-sqlite
          {{- else }}
          # Local Ephemeral Volume for Sidecar co-location (RWO compliant)
          ephemeral:
            volumeClaimTemplate:
              spec:
                accessModes: [ "ReadWriteOnce" ]
                resources:
                  requests:
                    storage: {{ .Values.sqlite.persistence.size }}
                {{- if .Values.sqlite.persistence.storageClass }}
                storageClassName: {{ .Values.sqlite.persistence.storageClass | quote }}
                {{- end }}
          {{- end }}
      containers:
        # 1. FastAPI Web Container
        - name: fastapi
          image: "{{ .Values.images.backend.repository }}:{{ .Values.images.backend.tag }}"
          imagePullPolicy: {{ .Values.images.backend.pullPolicy }}
          ports:
            - containerPort: 8000
              name: http
          envFrom:
            - configMapRef:
                name: {{ include "jobhunt-pro.fullname" . }}-config
            - secretRef:
                name: {{ include "jobhunt-pro.fullname" . }}-secrets
          volumeMounts:
            - name: sqlite-storage
              mountPath: {{ .Values.sqlite.persistence.mountPath }}
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 20
          resources:
            {{- toYaml .Values.backend.resources | nindent 12 }}

        # 2. SQLite Sync Worker Sidecar (Deployed in same pod if runSyncWorkerAsSidecar is true)
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
          volumeMounts:
            - name: sqlite-storage
              mountPath: {{ .Values.sqlite.persistence.mountPath }}
          resources:
            {{- toYaml .Values.syncWorker.resources | nindent 12 }}
        {{- end }}
```

### `templates/backend-service.yaml`
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "jobhunt-pro.fullname" . }}-backend
  labels:
    {{- include "jobhunt-pro.labels" . | nindent 4 }}
spec:
  ports:
    - port: 8000
      targetPort: 8000
      name: http
  selector:
    {{- include "jobhunt-pro.selectorLabels" . | nindent 4 }}
    app: backend
```

### `templates/frontend-deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "jobhunt-pro.fullname" . }}-frontend
  labels:
    {{- include "jobhunt-pro.labels" . | nindent 4 }}
    app: frontend
spec:
  replicas: {{ .Values.frontend.replicaCount }}
  selector:
    matchLabels:
      {{- include "jobhunt-pro.selectorLabels" . | nindent 6 }}
      app: frontend
  template:
    metadata:
      labels:
        {{- include "jobhunt-pro.selectorLabels" . | nindent 8 }}
        app: frontend
    spec:
      containers:
        - name: frontend
          image: "{{ .Values.images.frontend.repository }}:{{ .Values.images.frontend.tag }}"
          imagePullPolicy: {{ .Values.images.frontend.pullPolicy }}
          ports:
            - containerPort: 3000
              name: http
          envFrom:
            - configMapRef:
                name: {{ include "jobhunt-pro.fullname" . }}-config
          readinessProbe:
            httpGet:
              path: /
              port: 3000
            initialDelaySeconds: 15
            periodSeconds: 15
          livenessProbe:
            httpGet:
              path: /
              port: 3000
            initialDelaySeconds: 20
            periodSeconds: 20
          resources:
            {{- toYaml .Values.frontend.resources | nindent 12 }}
```

### `templates/frontend-service.yaml`
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "jobhunt-pro.fullname" . }}-frontend
  labels:
    {{- include "jobhunt-pro.labels" . | nindent 4 }}
spec:
  ports:
    - port: 3000
      targetPort: 3000
      name: http
  selector:
    {{- include "jobhunt-pro.selectorLabels" . | nindent 4 }}
    app: frontend
```

### `templates/celery-worker-deployment.yaml`
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
      {{- include "jobhunt-pro.selectorLabels" $ | nindent 6 }}
      app: celery-{{ $poolName }}
  template:
    metadata:
      labels:
        {{- include "jobhunt-pro.selectorLabels" $ | nindent 8 }}
        app: celery-{{ $poolName }}
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
          resources:
            {{- toYaml $poolConfig.resources | nindent 12 }}
---
{{- end }}
```

### `templates/sync-worker-deployment.yaml`
```yaml
{{- if and (not .Values.backend.runSyncWorkerAsSidecar) .Values.sqlite.persistence.enabled -}}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "jobhunt-pro.fullname" . }}-sync-worker
  labels:
    {{- include "jobhunt-pro.labels" . | nindent 4 }}
    app: sync-worker
spec:
  replicas: 1
  selector:
    matchLabels:
      {{- include "jobhunt-pro.selectorLabels" . | nindent 6 }}
      app: sync-worker
  template:
    metadata:
      labels:
        {{- include "jobhunt-pro.selectorLabels" . | nindent 8 }}
        app: sync-worker
    spec:
      volumes:
        - name: sqlite-storage
          persistentVolumeClaim:
            claimName: {{ include "jobhunt-pro.fullname" . }}-sqlite
      containers:
        - name: sync-worker
          image: "{{ .Values.images.backend.repository }}:{{ .Values.images.backend.tag }}"
          imagePullPolicy: {{ .Values.images.backend.pullPolicy }}
          command: ["python", "-m", "backend.sync_worker"]
          envFrom:
            - configMapRef:
                name: {{ include "jobhunt-pro.fullname" . }}-config
            - secretRef:
                name: {{ include "jobhunt-pro.fullname" . }}-secrets
          volumeMounts:
            - name: sqlite-storage
              mountPath: {{ .Values.sqlite.persistence.mountPath }}
          resources:
            {{- toYaml .Values.syncWorker.resources | nindent 12 }}
{{- end }}
```

### `templates/ingress.yaml`
```yaml
{{- if .Values.ingress.enabled -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "jobhunt-pro.fullname" . }}
  labels:
    {{- include "jobhunt-pro.labels" . | nindent 4 }}
  annotations:
    {{- toYaml .Values.ingress.annotations | nindent 4 }}
spec:
  ingressClassName: {{ .Values.ingress.className | quote }}
  rules:
    - host: {{ .Values.global.domain | quote }}
      http:
        paths:
          # Route WebSockets directly to the FastAPI Backend
          - path: /ws/
            pathType: Prefix
            backend:
              service:
                name: {{ include "jobhunt-pro.fullname" . }}-backend
                port:
                  number: 8000
          # Route API endpoints directly to Backend
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: {{ include "jobhunt-pro.fullname" . }}-backend
                port:
                  number: 8000
          # Route interactive docs to Backend
          - path: /docs
            pathType: Prefix
            backend:
              service:
                name: {{ include "jobhunt-pro.fullname" . }}-backend
                port:
                  number: 8000
          - path: /redoc
            pathType: Prefix
            backend:
              service:
                name: {{ include "jobhunt-pro.fullname" . }}-backend
                port:
                  number: 8000
          # Route all other web traffic to the Next.js Frontend
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ include "jobhunt-pro.fullname" . }}-frontend
                port:
                  number: 3000
{{- end }}
```

---

## 5. Architectural Recommendations & Trade-offs

1.  **SQLite Storage Path & Concurrency**:
    *   SQLite is highly optimized via WAL mode, which allows multiple readers and a single writer. Sharing a block volume (e.g. AWS EBS) between separate pods is impossible due to `ReadWriteOnce` (RWO) limits.
    *   **Recommendation**: Run `sync_worker` as a sidecar container (default settings). This allows both FastAPI and the sync worker to access the same volume locally under RWO storage.
2.  **CORS Handling via Ingress Routing**:
    *   By exposing the frontend and backend on the same host using path-based ingress rules (e.g., `/` for frontend and `/api` for backend), the browser treats them as the same origin. This natively circumvents any cross-origin resource sharing (CORS) complexities.
3.  **Client-side SQLite WASM / OPFS isolation**:
    *   Because the frontend SPA uses client-side SQLite stored inside the browser's OPFS, it runs at zero cost on the client device. It does not require any Kubernetes storage volumes or server backend synchronization, making it extremely cost-effective.

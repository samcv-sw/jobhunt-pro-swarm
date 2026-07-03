# JobHunt Pro — Kubernetes Helm Chart Architecture & Design Proposal

This analysis report outlines the design, architecture, and deployment strategy for orchestrating the JobHunt Pro stack using a Helm chart. It is written in compliance with the project specifications and includes complete, copy-paste-ready template files to facilitate direct implementation.

---

## 1. Stack Components & Analysis

### A. FastAPI Backend (App Service)
- **Dockerfile**: Located in the root (`Dockerfile`), it uses `python:3.12-slim` as the base image. It copies the `backend/`, `scrapers/`, and `tests/` directories, sets `PYTHONPATH=/app`, exposes port `8000`, and starts the Uvicorn server:
  ```bash
  uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
  ```
- **Dependencies**: Requires Postgres and Redis to be healthy before starting (in the docker-compose environment).
- **Health check**: `/health` endpoint is available, returning `{"status": "ok", "architecture": "FastAPI + Celery + Redis"}`.
- **Data Persistence**: Requires persistence for logs and SQLite database files (`/app/data` and `/app/logs`).

### B. Next.js Frontend
- **Dockerfile**: Located in the root (`Dockerfile.frontend`), it uses a two-stage build (`node:20-alpine`) to build the static frontend files and then serve them using `npm start` (or a web server) on port `3000`.
- **Output Mode**: Built with `output: "export"` in `frontend/next.config.ts`, making it a fully client-side Single Page Application (SPA).
- **Communication**: Interacts with the backend via the `NEXT_PUBLIC_API_URL` environment variable.
- **Client Storage**: Leverages a client-side SQLite database using WebAssembly + OPFS (Origin Private File System) inside the user's browser, eliminating server-side SQLite dependencies for frontend queries.

### C. Celery Workers
- **Command**: Run using the same backend image:
  ```bash
  celery -A backend.celery_app worker --loglevel=info -P solo
  ```
- **Dependencies**: Requires Postgres and Redis.
- **Task Queues**: Configured in `backend/celery_app.py` for task routing:
  - `backend.tasks.scrape_jobs` -> `scraping`
  - `backend.tasks.generate_cover_letter` -> `ai_inference`
  - `backend.tasks.send_application_email` -> `email_sender`

### D. Redis Cache
- **Image**: `redis:7-alpine`.
- **Command**: Started with `redis-server --appendonly yes` to ensure database state persistence.
- **Service Port**: `6379`.

### E. PostgreSQL Database
- **Image**: `postgres:16-alpine`.
- **Service Port**: `5432`.
- **Initialization**: Mounts `./init.sql` to `/docker-entrypoint-initdb.d/init.sql` to initialize database schemas and tables on startup.

### F. SQLite OPFS & Dual Database Pattern
- **Analysis**: The backend uses a Dual Database Pattern. It writes changes locally to a SQLite database (`LOCAL_DATABASE_URL` / `/app/data/jobhunt_saas_v2.db`) for zero-latency operations and then pushes these changes asynchronously to a remote Postgres database using the Outbox pattern in `backend/sync_worker.py`.
- **Sync Worker Command**: Starts the sync worker using `python -m backend.sync_worker`.
- **K8s Storage Challenge**: Because the `app` pod and the `sync-worker` pod both need access to the same SQLite database file, they must share access to it:
  1. **Option 1 (Shared PVC)**: Deploy them as separate pods mounting a single `PersistentVolumeClaim` with `accessModes: [ReadWriteMany]`. This requires a backing storage provider that supports RWX (like NFS or AWS EFS).
  2. **Option 2 (Sidecar Deployment)**: Deploy the `sync-worker` as a sidecar container inside the backend `app` Pod. They can then share a simple `emptyDir` volume or a standard `ReadWriteOnce` (RWO) PVC mounted at `/app/data`. This is the recommended approach for local/microk8s clusters that do not support RWX out of the box.

---

## 2. Proposed Helm Chart Directory Structure

```text
deploy/k8s/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── _helpers.tpl
    ├── configmap.yaml
    ├── secrets.yaml
    ├── pvc.yaml
    ├── postgres-statefulset.yaml
    ├── postgres-service.yaml
    ├── redis-deployment.yaml
    ├── redis-service.yaml
    ├── backend-deployment.yaml
    ├── backend-service.yaml
    ├── frontend-deployment.yaml
    ├── frontend-service.yaml
    ├── celery-worker-deployment.yaml
    └── ingress.yaml
```

---

## 3. Helm Chart Files Design

Here are the complete, production-ready Helm chart definitions.

### `Chart.yaml`
```yaml
apiVersion: v2
name: jobhunt-pro
description: Production Helm chart for JobHunt Pro orchestrating Next.js, FastAPI, Celery, Redis, and Postgres.
type: application
version: 1.0.0
appVersion: "17.0"
```

### `values.yaml`
```yaml
# Global Configuration
global:
  domain: jobhunt.local
  apiUrl: "http://jobhunt.local/api"

# PostgreSQL Database Configuration
postgres:
  enabled: true
  image:
    repository: postgres
    tag: 16-alpine
    pullPolicy: IfNotPresent
  service:
    port: 5432
  persistence:
    size: 8Gi
    storageClassName: ""
  db:
    name: jobhunt_pro
    user: jobhunt
    # Change in production
    password: jobhunt_secret_2026

# Redis Configuration
redis:
  enabled: true
  image:
    repository: redis
    tag: 7-alpine
    pullPolicy: IfNotPresent
  service:
    port: 6379
  persistence:
    size: 2Gi
    storageClassName: ""

# Backend (FastAPI API Server) Configuration
backend:
  replicaCount: 1
  image:
    repository: jobhunt-backend
    tag: latest
    pullPolicy: Never
  service:
    type: ClusterIP
    port: 8000
  resources:
    limits:
      cpu: 1000m
      memory: 1024Mi
    requests:
      cpu: 250m
      memory: 256Mi
  sqlite:
    dbPath: "/app/data/jobhunt_saas_v2.db"
    persistence:
      size: 5Gi
      storageClassName: ""
      # Set to true to use ReadWriteMany PVC (requires backing storage plugin support)
      # If false, sync-worker should run as a sidecar container in the backend pod
      useSharedPvc: false
  logs:
    persistence:
      size: 2Gi
      storageClassName: ""
  env:
    cloudMode: "false"
    dryRun: "false"
    maxWorkers: "200"
    dailySendLimit: "2000"

# Next.js Frontend Configuration
frontend:
  replicaCount: 1
  image:
    repository: jobhunt-frontend
    tag: latest
    pullPolicy: Never
  service:
    type: ClusterIP
    port: 3000
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 100m
      memory: 128Mi

# Celery Worker Configuration
celeryWorker:
  replicaCount: 2
  resources:
    limits:
      cpu: 1000m
      memory: 1024Mi
    requests:
      cpu: 250m
      memory: 256Mi
  queues:
    - scraping
    - ai_inference
    - email_sender

# Secrets (Add values or inject via Kubernetes Secrets)
secrets:
  GEMINI_API_KEY: "change_me"
  GROQ_API_KEY: "change_me"
  BREVO_API_KEY: "change_me"
  BREVO_ACCOUNT_EMAIL: "samsalameh.cv@gmail.com"
  TELEGRAM_BOT_TOKEN: ""
  TELEGRAM_CHAT_ID: ""
  GMAIL_SMTP_USER_1: ""
  GMAIL_APP_PASSWORD_1: ""
  GMAIL_SMTP_USER_2: ""
  GMAIL_APP_PASSWORD_2: ""
  OUTLOOK_USER_1: ""
  OUTLOOK_PASSWORD_1: ""

# Ingress Configuration
ingress:
  enabled: true
  className: "nginx"
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "30"
```

### `templates/_helpers.tpl`
```tpl
{{/*
Expand the name of the chart.
*/}}
{{- define "jobhunt.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this.
*/}}
{{- define "jobhunt.fullname" -}}
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
{{- define "jobhunt.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "jobhunt.labels" -}}
helm.sh/chart: {{ include "jobhunt.chart" . }}
{{ include "jobhunt.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "jobhunt.selectorLabels" -}}
app.kubernetes.io/name: {{ include "jobhunt.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

### `templates/configmap.yaml`
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "jobhunt.fullname" . }}-config
  labels:
    {{- include "jobhunt.labels" . | nindent 4 }}
data:
  DATABASE_URL_SYNC: "postgresql://{{ .Values.postgres.db.user }}:{{ .Values.postgres.db.password }}@{{ include "jobhunt.fullname" . }}-postgres:5432/{{ .Values.postgres.db.name }}"
  DATABASE_URL: "postgresql+asyncpg://{{ .Values.postgres.db.user }}:{{ .Values.postgres.db.password }}@{{ include "jobhunt.fullname" . }}-postgres:5432/{{ .Values.postgres.db.name }}"
  REDIS_URL: "redis://{{ include "jobhunt.fullname" . }}-redis:6379/0"
  NEXT_PUBLIC_API_URL: {{ .Values.global.apiUrl | quote }}
  DB_PATH: {{ .Values.backend.sqlite.dbPath | quote }}
  LOCAL_DATABASE_URL: "sqlite+aiosqlite:///app/data/jobhunt_local.db"
  CLOUD_MODE: {{ .Values.backend.env.cloudMode | quote }}
  DRY_RUN: {{ .Values.backend.env.dryRun | quote }}
  MAX_WORKERS: {{ .Values.backend.env.maxWorkers | quote }}
  DAILY_SEND_LIMIT: {{ .Values.backend.env.dailySendLimit | quote }}
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "jobhunt.fullname" . }}-postgres-init
  labels:
    {{- include "jobhunt.labels" . | nindent 4 }}
data:
  init.sql: |
    -- Initialize database tables
    CREATE TABLE IF NOT EXISTS sync_outbox_log (
        id SERIAL PRIMARY KEY,
        table_name VARCHAR(100) NOT NULL,
        record_id VARCHAR(100) NOT NULL,
        operation VARCHAR(20) NOT NULL,
        payload JSONB NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    CREATE UNIQUE INDEX IF NOT EXISTS idx_sync_outbox_log_uniq ON sync_outbox_log(table_name, record_id, created_at);
```

### `templates/secrets.yaml`
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "jobhunt.fullname" . }}-secrets
  labels:
    {{- include "jobhunt.labels" . | nindent 4 }}
type: Opaque
data:
  GEMINI_API_KEY: {{ .Values.secrets.GEMINI_API_KEY | b64enc | quote }}
  GROQ_API_KEY: {{ .Values.secrets.GROQ_API_KEY | b64enc | quote }}
  BREVO_API_KEY: {{ .Values.secrets.BREVO_API_KEY | b64enc | quote }}
  BREVO_ACCOUNT_EMAIL: {{ .Values.secrets.BREVO_ACCOUNT_EMAIL | b64enc | quote }}
  TELEGRAM_BOT_TOKEN: {{ .Values.secrets.TELEGRAM_BOT_TOKEN | b64enc | quote }}
  TELEGRAM_CHAT_ID: {{ .Values.secrets.TELEGRAM_CHAT_ID | b64enc | quote }}
  GMAIL_SMTP_USER_1: {{ .Values.secrets.GMAIL_SMTP_USER_1 | b64enc | quote }}
  GMAIL_APP_PASSWORD_1: {{ .Values.secrets.GMAIL_APP_PASSWORD_1 | b64enc | quote }}
  GMAIL_SMTP_USER_2: {{ .Values.secrets.GMAIL_SMTP_USER_2 | b64enc | quote }}
  GMAIL_APP_PASSWORD_2: {{ .Values.secrets.GMAIL_APP_PASSWORD_2 | b64enc | quote }}
  OUTLOOK_USER_1: {{ .Values.secrets.OUTLOOK_USER_1 | b64enc | quote }}
  OUTLOOK_PASSWORD_1: {{ .Values.secrets.OUTLOOK_PASSWORD_1 | b64enc | quote }}
```

### `templates/pvc.yaml`
```yaml
{{- if and .Values.backend.sqlite.persistence.size .Values.backend.sqlite.persistence.useSharedPvc }}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "jobhunt.fullname" . }}-sqlite-pvc
  labels:
    {{- include "jobhunt.labels" . | nindent 4 }}
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: {{ .Values.backend.sqlite.persistence.size }}
  {{- if .Values.backend.sqlite.persistence.storageClassName }}
  storageClassName: {{ .Values.backend.sqlite.persistence.storageClassName | quote }}
  {{- end }}
{{- end }}
---
{{- if .Values.backend.logs.persistence.size }}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "jobhunt.fullname" . }}-logs-pvc
  labels:
    {{- include "jobhunt.labels" . | nindent 4 }}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.backend.logs.persistence.size }}
  {{- if .Values.backend.logs.persistence.storageClassName }}
  storageClassName: {{ .Values.backend.logs.persistence.storageClassName | quote }}
  {{- end }}
{{- end }}
```

### `templates/postgres-statefulset.yaml`
```yaml
{{- if .Values.postgres.enabled -}}
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: {{ include "jobhunt.fullname" . }}-postgres
  labels:
    {{- include "jobhunt.labels" . | nindent 4 }}
    app: postgres
spec:
  serviceName: {{ include "jobhunt.fullname" . }}-postgres
  replicas: 1
  selector:
    matchLabels:
      {{- include "jobhunt.selectorLabels" . | nindent 6 }}
      app: postgres
  template:
    metadata:
      labels:
        {{- include "jobhunt.selectorLabels" . | nindent 8 }}
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
            name: {{ include "jobhunt.fullname" . }}-postgres-init
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
      spec:
        accessModes: [ "ReadWriteOnce" ]
        resources:
          requests:
            storage: {{ .Values.postgres.persistence.size }}
        {{- if .Values.postgres.persistence.storageClassName }}
        storageClassName: {{ .Values.postgres.persistence.storageClassName | quote }}
        {{- end }}
{{- end }}
```

### `templates/postgres-service.yaml`
```yaml
{{- if .Values.postgres.enabled -}}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "jobhunt.fullname" . }}-postgres
  labels:
    {{- include "jobhunt.labels" . | nindent 4 }}
spec:
  ports:
    - port: 5432
      targetPort: 5432
      name: postgres
  selector:
    {{- include "jobhunt.selectorLabels" . | nindent 4 }}
    app: postgres
{{- end }}
```

### `templates/redis-deployment.yaml`
```yaml
{{- if .Values.redis.enabled -}}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "jobhunt.fullname" . }}-redis
  labels:
    {{- include "jobhunt.labels" . | nindent 4 }}
    app: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      {{- include "jobhunt.selectorLabels" . | nindent 6 }}
      app: redis
  template:
    metadata:
      labels:
        {{- include "jobhunt.selectorLabels" . | nindent 8 }}
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
          emptyDir: {}
{{- end }}
```

### `templates/redis-service.yaml`
```yaml
{{- if .Values.redis.enabled -}}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "jobhunt.fullname" . }}-redis
  labels:
    {{- include "jobhunt.labels" . | nindent 4 }}
spec:
  ports:
    - port: 6379
      targetPort: 6379
      name: redis
  selector:
    {{- include "jobhunt.selectorLabels" . | nindent 4 }}
    app: redis
{{- end }}
```

### `templates/backend-deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "jobhunt.fullname" . }}-backend
  labels:
    {{- include "jobhunt.labels" . | nindent 4 }}
    app: backend
spec:
  replicas: {{ .Values.backend.replicaCount }}
  selector:
    matchLabels:
      {{- include "jobhunt.selectorLabels" . | nindent 6 }}
      app: backend
  template:
    metadata:
      labels:
        {{- include "jobhunt.selectorLabels" . | nindent 8 }}
        app: backend
    spec:
      containers:
        # 1. Main FastAPI container
        - name: fastapi
          image: "{{ .Values.backend.image.repository }}:{{ .Values.backend.image.tag }}"
          imagePullPolicy: {{ .Values.backend.image.pullPolicy }}
          ports:
            - containerPort: 8000
              name: http
          envFrom:
            - configMapRef:
                name: {{ include "jobhunt.fullname" . }}-config
          env:
            - name: GEMINI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: {{ include "jobhunt.fullname" . }}-secrets
                  key: GEMINI_API_KEY
            - name: GROQ_API_KEY
              valueFrom:
                secretKeyRef:
                  name: {{ include "jobhunt.fullname" . }}-secrets
                  key: GROQ_API_KEY
            - name: BREVO_API_KEY
              valueFrom:
                secretKeyRef:
                  name: {{ include "jobhunt.fullname" . }}-secrets
                  key: BREVO_API_KEY
            - name: BREVO_ACCOUNT_EMAIL
              valueFrom:
                secretKeyRef:
                  name: {{ include "jobhunt.fullname" . }}-secrets
                  key: BREVO_ACCOUNT_EMAIL
            - name: TELEGRAM_BOT_TOKEN
              valueFrom:
                secretKeyRef:
                  name: {{ include "jobhunt.fullname" . }}-secrets
                  key: TELEGRAM_BOT_TOKEN
            - name: TELEGRAM_CHAT_ID
              valueFrom:
                secretKeyRef:
                  name: {{ include "jobhunt.fullname" . }}-secrets
                  key: TELEGRAM_CHAT_ID
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 5
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 20
            timeoutSeconds: 5
          resources:
            {{- toYaml .Values.backend.resources | nindent 12 }}
          volumeMounts:
            - name: sqlite-storage
              mountPath: /app/data
            - name: log-storage
              mountPath: /app/logs

        # 2. Sync Worker Sidecar Container (runs only if useSharedPvc is false, avoiding RWX PVC dependency)
        {{- if not .Values.backend.sqlite.persistence.useSharedPvc }}
        - name: sync-worker
          image: "{{ .Values.backend.image.repository }}:{{ .Values.backend.image.tag }}"
          imagePullPolicy: {{ .Values.backend.image.pullPolicy }}
          command: ["python", "-m", "backend.sync_worker"]
          envFrom:
            - configMapRef:
                name: {{ include "jobhunt.fullname" . }}-config
          resources:
            limits:
              cpu: 200m
              memory: 256Mi
            requests:
              cpu: 50m
              memory: 64Mi
          volumeMounts:
            - name: sqlite-storage
              mountPath: /app/data
        {{- end }}

      volumes:
        - name: sqlite-storage
          {{- if .Values.backend.sqlite.persistence.useSharedPvc }}
          persistentVolumeClaim:
            claimName: {{ include "jobhunt.fullname" . }}-sqlite-pvc
          {{- else }}
          # Local Persistent Volume (RWO) shared inside the Pod across both containers
          ephemeral:
            volumeClaimTemplate:
              spec:
                accessModes: [ "ReadWriteOnce" ]
                resources:
                  requests:
                    storage: {{ .Values.backend.sqlite.persistence.size }}
                {{- if .Values.backend.sqlite.persistence.storageClassName }}
                storageClassName: {{ .Values.backend.sqlite.persistence.storageClassName | quote }}
                {{- end }}
          {{- end }}
        - name: log-storage
          {{- if .Values.backend.logs.persistence.size }}
          persistentVolumeClaim:
            claimName: {{ include "jobhunt.fullname" . }}-logs-pvc
          {{- else }}
          emptyDir: {}
          {{- end }}
```

### `templates/backend-service.yaml`
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "jobhunt.fullname" . }}-backend
  labels:
    {{- include "jobhunt.labels" . | nindent 4 }}
spec:
  ports:
    - port: 8000
      targetPort: 8000
      name: http
  selector:
    {{- include "jobhunt.selectorLabels" . | nindent 4 }}
    app: backend
```

### `templates/frontend-deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "jobhunt.fullname" . }}-frontend
  labels:
    {{- include "jobhunt.labels" . | nindent 4 }}
    app: frontend
spec:
  replicas: {{ .Values.frontend.replicaCount }}
  selector:
    matchLabels:
      {{- include "jobhunt.selectorLabels" . | nindent 6 }}
      app: frontend
  template:
    metadata:
      labels:
        {{- include "jobhunt.selectorLabels" . | nindent 8 }}
        app: frontend
    spec:
      containers:
        - name: frontend
          image: "{{ .Values.frontend.image.repository }}:{{ .Values.frontend.image.tag }}"
          imagePullPolicy: {{ .Values.frontend.image.pullPolicy }}
          ports:
            - containerPort: 3000
              name: http
          envFrom:
            - configMapRef:
                name: {{ include "jobhunt.fullname" . }}-config
          readinessProbe:
            httpGet:
              path: /
              port: 3000
            initialDelaySeconds: 15
            periodSeconds: 15
            timeoutSeconds: 5
          livenessProbe:
            httpGet:
              path: /
              port: 3000
            initialDelaySeconds: 20
            periodSeconds: 20
            timeoutSeconds: 5
          resources:
            {{- toYaml .Values.frontend.resources | nindent 12 }}
```

### `templates/frontend-service.yaml`
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "jobhunt.fullname" . }}-frontend
  labels:
    {{- include "jobhunt.labels" . | nindent 4 }}
spec:
  ports:
    - port: 3000
      targetPort: 3000
      name: http
  selector:
    {{- include "jobhunt.selectorLabels" . | nindent 4 }}
    app: frontend
```

### `templates/celery-worker-deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "jobhunt.fullname" . }}-celery
  labels:
    {{- include "jobhunt.labels" . | nindent 4 }}
    app: celery
spec:
  replicas: {{ .Values.celeryWorker.replicaCount }}
  selector:
    matchLabels:
      {{- include "jobhunt.selectorLabels" . | nindent 6 }}
      app: celery
  template:
    metadata:
      labels:
        {{- include "jobhunt.selectorLabels" . | nindent 8 }}
        app: celery
    spec:
      containers:
        - name: celery
          image: "{{ .Values.backend.image.repository }}:{{ .Values.backend.image.tag }}"
          imagePullPolicy: {{ .Values.backend.image.pullPolicy }}
          # Started with celery worker command, logging level info, and routing queues
          command: ["celery", "-A", "backend.celery_app", "worker", "--loglevel=info", "-P", "solo"]
          envFrom:
            - configMapRef:
                name: {{ include "jobhunt.fullname" . }}-config
          env:
            - name: GEMINI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: {{ include "jobhunt.fullname" . }}-secrets
                  key: GEMINI_API_KEY
            - name: GROQ_API_KEY
              valueFrom:
                secretKeyRef:
                  name: {{ include "jobhunt.fullname" . }}-secrets
                  key: GROQ_API_KEY
            - name: BREVO_API_KEY
              valueFrom:
                secretKeyRef:
                  name: {{ include "jobhunt.fullname" . }}-secrets
                  key: BREVO_API_KEY
            - name: BREVO_ACCOUNT_EMAIL
              valueFrom:
                secretKeyRef:
                  name: {{ include "jobhunt.fullname" . }}-secrets
                  key: BREVO_ACCOUNT_EMAIL
            - name: TELEGRAM_BOT_TOKEN
              valueFrom:
                secretKeyRef:
                  name: {{ include "jobhunt.fullname" . }}-secrets
                  key: TELEGRAM_BOT_TOKEN
            - name: TELEGRAM_CHAT_ID
              valueFrom:
                secretKeyRef:
                  name: {{ include "jobhunt.fullname" . }}-secrets
                  key: TELEGRAM_CHAT_ID
          resources:
            {{- toYaml .Values.celeryWorker.resources | nindent 12 }}
```

### `templates/ingress.yaml`
```yaml
{{- if .Values.ingress.enabled -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "jobhunt.fullname" . }}
  labels:
    {{- include "jobhunt.labels" . | nindent 4 }}
  annotations:
    {{- toYaml .Values.ingress.annotations | nindent 4 }}
spec:
  ingressClassName: {{ .Values.ingress.className | quote }}
  rules:
    - host: {{ .Values.global.domain | quote }}
      http:
        paths:
          # Route WebSocket traffic to Backend
          - path: /ws/
            pathType: Prefix
            backend:
              service:
                name: {{ include "jobhunt.fullname" . }}-backend
                port:
                  number: 8000
          # Route API endpoints to Backend
          - path: /api/
            pathType: Prefix
            backend:
              service:
                name: {{ include "jobhunt.fullname" . }}-backend
                port:
                  number: 8000
          # Route documentation and health check endpoints to Backend
          - path: /health
            pathType: Exact
            backend:
              service:
                name: {{ include "jobhunt.fullname" . }}-backend
                port:
                  number: 8000
          # Route all other web traffic to Next.js Frontend
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ include "jobhunt.fullname" . }}-frontend
                port:
                  number: 3000
{{- end }}
```

---

## 4. Key Architectural Recommendations & Strategy

1. **Storage Access Mode Trade-off**:
   - The SQLite database is critical for the Dual Database Pattern. If `useSharedPvc` is `true`, a standard ReadWriteMany PV is required.
   - If `useSharedPvc` is `false` (default), the `sync-worker` container is automatically injected as a sidecar container inside the FastAPI pod. This design allows them to share a local storage volume (via an ephemeral volume template) using standard ReadWriteOnce (RWO) speeds. This eliminates the latency overhead and setup complexity of RWX network filesystems, ensuring peak SQLite performance.

2. **Ingress-Based API Routing (No CORS Native Solution)**:
   - Setting up the Ingress controller to route `/api/` traffic directly to the backend service and all other requests to the frontend service eliminates cross-origin issues entirely. It ensures that the client browser interacts with the API on the same domain and port, resolving CORS natively.

3. **Celery Worker Scaling**:
   - The worker runs inside the same docker image as the backend but with a different CMD override. We suggest configuring Horizontal Pod Autoscaling (HPA) for the worker deployment based on CPU utilization and/or queue length (using custom Prometheus metrics or KEDA).

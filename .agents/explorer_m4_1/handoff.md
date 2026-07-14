# Cloudflare Health-Check-Based DNS Failover Design (IMP-128)

This report details the exploration, analysis, and design for the Cloudflare health-check-based DNS failover solution for JobHunt Pro.

---

## 1. Observation

### Health Endpoint Implementations in `backend/main.py`
The FastAPI backend contains four health-related endpoints:
*   **`/health`** (lines 450–455):
    ```python
    @app.get("/health")
    async def health_check(request: Request = None) -> dict[str, str]:
        """Retrieve service health status of task queue and async loop runner."""
        logger.info("Health check verification endpoint requested.")
        return {"status": "ok", "architecture": "FastAPI + Celery + Redis"}
    ```
*   **`/healthz`** (lines 457–461):
    ```python
    @app.get("/healthz")
    async def healthz(request: Request = None) -> dict[str, str]:
        """Lightweight Render health check endpoint."""
        return {"status": "ok"}
    ```
*   **`/api/v1/health`** (lines 463–467):
    ```python
    @app.get("/api/v1/health")
    async def health_v1(request: Request = None) -> dict[str, str]:
        """Lightweight API v1 health check endpoint."""
        return {"status": "ok"}
    ```
*   **`/api/v1/health/detailed`** (lines 487–601):
    This endpoint executes checks against the database, Redis connection, SMTP server, and Groq API.
    *   *Database probe* (lines 494–504):
        ```python
        # Check DB
        db_start = time.monotonic()
        try:
            async with async_session() as session:
                from sqlalchemy import text
                await session.execute(text("SELECT 1"))
            result["components"]["db"] = {"status": "ok", "latency_ms": round((time.monotonic() - db_start) * 1000, 2)}
        except Exception as e:
            result["components"]["db"] = {"status": "error", "detail": str(e)}
            result["status"] = "degraded"
        ```
    *   *SMTP probe* (lines 534–570):
        Uses an outbound TCP socket probe to connect to the SMTP server (with a `0.9s` timeout).
    *   *Groq API probe* (lines 571–600):
        Sends an HTTP GET request to `https://api.groq.com/openai/v1/models` (with a `0.9s` timeout).
    *   *Response delivery* (line 601):
        ```python
        return result
        ```
        Crucially, if any component fails, `result["status"]` is set to `"degraded"`, but the response is returned as a normal dictionary without raising an exception or overriding the HTTP status code. Therefore, the server responds with an HTTP status of **`200 OK`** even when degraded or disconnected from the database.

### Health Check Implementations in `cloudflare/worker.js`
The Cloudflare Worker manages routing and routing-related health checks:
*   **`/api/cloud-health`** (lines 616–625):
    ```javascript
    // ═══════════ API: CLOUD-HEALTH ═══════════
    if (path === '/api/cloud-health') {
      await db.prepare('SELECT 1').all();
      const kvOk = !!kv;
      const r2Ok = !!r2;
      const aiOk = hasAI(env);
      return json({
        status: 'ok', db: 'd1_connected', kv: kvOk, r2: r2Ok, ai: aiOk, 
        version: '4.0', time: new Date().toISOString(),
      });
    }
    ```
    If D1 fails, it throws a JS exception, resulting in an HTTP `500 Internal Server Error`.
*   **`/health`** (lines 1007–1013):
    ```javascript
    // ═══════════ HEALTH ═══════════
    if (path === '/health') {
      return json({
        status: 'ok', worker: 'jobhunt-pro-router', version: '4.0',
        d1: !!db, kv: !!kv, r2: !!r2, ai: hasAI(env),
        cron: 'every 30min',
      });
    }
    ```
*   *Worker routing limitations* (lines 994–1015):
    Any endpoint that does not match sensitive paths or is not prefixed with `/_/pa/` returns a `404 Not Found` JSON response:
    ```javascript
    return json({ error: 'Not found' }, 404);
    ```
    This means routing a Cloudflare monitor to `/api/v1/health` or `/api/v1/health/detailed` via the Worker's default domain will fail with a `404 Not Found`, unless it targets the PythonAnywhere or specific origin domains directly.

---

## 2. Logic Chain

1.  **Suitability of `/api/v1/health/detailed` for Cloudflare monitors**:
    *   Cloudflare Load Balancer Monitors primarily check HTTP status codes (expecting `2xx` or specific codes like `200`).
    *   Since `/api/v1/health/detailed` returns HTTP `200 OK` even when database checks fail and the app status is `"degraded"` (Observation 1), a Cloudflare monitor will falsely evaluate the endpoint as healthy.
    *   Additionally, active TCP probes to SMTP and HTTP calls to the Groq API run on every request. High check frequencies from multiple Cloudflare edge nodes will overload the backend, introduce rate-limit issues, and trigger false failovers if the third-party providers (Groq/SMTP) experience minor outages, even if the primary JobHunt Pro application remains operational.
    *   *Conclusion*: `/api/v1/health/detailed` is **unsuitable** for Cloudflare health checks in its current form.
2.  **Suitability of `/health` and `/healthz`**:
    *   These endpoints are fast and return `200 OK` (Observation 1), but they do not check database connectivity. If the database is dead, they will still report `200 OK`, leading to a silent failure.
    *   *Conclusion*: They are **unsuitable** for comprehensive database failover monitoring.
3.  **Required Remediation**:
    *   We need a dedicated health endpoint (`/api/v1/health/failover`) that:
        1.  Validates core database availability.
        2.  Returns a non-200 HTTP status (e.g., `503 Service Unavailable` or `500 Internal Server Error`) if the database is down.
        3.  Omits external, non-blocking APIs (SMTP, Groq) to avoid false-positive failovers.
4.  **Active-Passive Failover Strategy**:
    *   Because primary traffic should target PythonAnywhere (`jhfguf.pythonanywhere.com`), and secondary traffic should target failover targets (Fly.io, Zeabur, Render) only when PythonAnywhere is down, we must define two distinct Cloudflare Pools (Primary and Failover) and configure the Load Balancer with `steering_policy = "off"`. This forces traffic to the primary pool unless its health check fails, at which point Cloudflare routes to the secondary pool.

---

## 3. Caveats

*   **Network Boundaries**: The investigation was conducted in CODE_ONLY mode, so actual Cloudflare API tokens could not be validated against Cloudflare endpoints. 
*   **Worker Routing**: The Cloudflare Load Balancer Pools must target the origin servers directly (e.g., PythonAnywhere, Fly.io) using their direct hostnames rather than proxying through the Worker, since the Worker does not expose backend health checks by default.
*   **Database Sync Latency**: When failover occurs, there may be replication/sync lag between D1, Turso shards, and local SQLite databases.

---

## 4. Conclusion & Design Proposal

### 4.1. Backend Endpoint Implementation

A new database-aware endpoint is proposed for `backend/main.py`:

```python
from fastapi import status
from fastapi.responses import JSONResponse

@app.get("/api/v1/health/failover")
async def health_failover() -> Response:
    """Dedicated failover health check. Checks database, returns 503 if down."""
    try:
        async with async_session() as session:
            from sqlalchemy import text
            # Lightweight database check
            await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=2.0)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "healthy", "database": "connected"}
        )
    except Exception as e:
        logger.error(f"Failover health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "error": "Database connection failed"}
        )
```

---

### 4.2. Python Failover Configuration Script

Here is the complete Python script to automatically provision the Cloudflare Monitors, Pools, and Load Balancers. It is idempotent: if resources exist, it updates them.

Save as: `scripts/setup_cloudflare_failover.py`

```python
import os
import sys
import httpx

# Load environment variables
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
ZONE_ID = os.getenv("CLOUDFLARE_ZONE_ID")
LB_DOMAIN = os.getenv("CLOUDFLARE_ZONE_NAME", "api.jobhuntpro.com")

if not all([API_TOKEN, ACCOUNT_ID, ZONE_ID]):
    print("Error: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID, and CLOUDFLARE_ZONE_ID are required.")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}

client = httpx.Client(headers=HEADERS, base_url="https://api.cloudflare.com/client/v4")

def get_monitor_id(name: str) -> str:
    """Retrieve existing monitor ID by description/path if it exists."""
    resp = client.get(f"/accounts/{ACCOUNT_ID}/load_balancers/monitors")
    resp.raise_for_status()
    for monitor in resp.json().get("result", []):
        if monitor.get("path") == "/api/v1/health/failover":
            return monitor["id"]
    return None

def get_pool_id(name: str) -> str:
    """Retrieve existing pool ID by name."""
    resp = client.get(f"/accounts/{ACCOUNT_ID}/load_balancers/pools")
    resp.raise_for_status()
    for pool in resp.json().get("result", []):
        if pool.get("name") == name:
            return pool["id"]
    return None

def get_lb_id() -> str:
    """Retrieve existing load balancer ID by hostname."""
    resp = client.get(f"/zones/{ZONE_ID}/load_balancers")
    resp.raise_for_status()
    for lb in resp.json().get("result", []):
        if lb.get("name") == LB_DOMAIN:
            return lb["id"]
    return None

def setup_failover():
    # 1. Create or Update Monitor
    monitor_payload = {
        "type": "https",
        "path": "/api/v1/health/failover",
        "method": "GET",
        "port": 443,
        "timeout": 5,
        "interval": 60,
        "retries": 2,
        "expected_codes": "2xx",
        "description": "JobHunt Pro Db Health Monitor"
    }
    
    monitor_id = get_monitor_id("JobHunt Pro Db Health Monitor")
    if monitor_id:
        print(f"Updating monitor {monitor_id}...")
        resp = client.put(f"/accounts/{ACCOUNT_ID}/load_balancers/monitors/{monitor_id}", json=monitor_payload)
    else:
        print("Creating new monitor...")
        resp = client.post(f"/accounts/{ACCOUNT_ID}/load_balancers/monitors", json=monitor_payload)
    resp.raise_for_status()
    monitor_id = resp.json()["result"]["id"]
    print(f"Monitor ID: {monitor_id}")

    # 2. Create or Update Primary Pool
    primary_pool_payload = {
        "name": "jobhunt-primary-pool",
        "origins": [
            {
                "name": "pythonanywhere",
                "address": "jhfguf.pythonanywhere.com",
                "enabled": True,
                "weight": 1,
                "header": {
                    "Host": "jhfguf.pythonanywhere.com"
                }
            }
        ],
        "monitor": monitor_id,
        "description": "Primary backend pool",
        "enabled": True,
        "minimum_origins": 1
    }
    
    primary_pool_id = get_pool_id("jobhunt-primary-pool")
    if primary_pool_id:
        print(f"Updating primary pool {primary_pool_id}...")
        resp = client.put(f"/accounts/{ACCOUNT_ID}/load_balancers/pools/{primary_pool_id}", json=primary_pool_payload)
    else:
        print("Creating primary pool...")
        resp = client.post(f"/accounts/{ACCOUNT_ID}/load_balancers/pools", json=primary_pool_payload)
    resp.raise_for_status()
    primary_pool_id = resp.json()["result"]["id"]
    print(f"Primary Pool ID: {primary_pool_id}")

    # 3. Create or Update Failover Pool
    failover_pool_payload = {
        "name": "jobhunt-failover-pool",
        "origins": [
            {
                "name": "fly-io",
                "address": "jobhunt-pro.fly.dev",
                "enabled": True,
                "weight": 1,
                "header": {
                    "Host": "jobhunt-pro.fly.dev"
                }
            },
            {
                "name": "zeabur",
                "address": "jobhunt-pro.zeabur.app",
                "enabled": True,
                "weight": 1,
                "header": {
                    "Host": "jobhunt-pro.zeabur.app"
                }
            }
        ],
        "monitor": monitor_id,
        "description": "Failover backend pool",
        "enabled": True,
        "minimum_origins": 1
    }
    
    failover_pool_id = get_pool_id("jobhunt-failover-pool")
    if failover_pool_id:
        print(f"Updating failover pool {failover_pool_id}...")
        resp = client.put(f"/accounts/{ACCOUNT_ID}/load_balancers/pools/{failover_pool_id}", json=failover_pool_payload)
    else:
        print("Creating failover pool...")
        resp = client.post(f"/accounts/{ACCOUNT_ID}/load_balancers/pools", json=failover_pool_payload)
    resp.raise_for_status()
    failover_pool_id = resp.json()["result"]["id"]
    print(f"Failover Pool ID: {failover_pool_id}")

    # 4. Create or Update Load Balancer
    lb_payload = {
        "name": LB_DOMAIN,
        "description": "JobHunt Pro Active-Passive Failover LB",
        "default_pools": [primary_pool_id, failover_pool_id],
        "fallback_pool": failover_pool_id,
        "proxied": True,
        "steering_policy": "off",  # Essential for strict active-passive failover
        "ttl": 30
    }
    
    lb_id = get_lb_id()
    if lb_id:
        print(f"Updating Load Balancer {lb_id}...")
        resp = client.put(f"/zones/{ZONE_ID}/load_balancers/{lb_id}", json=lb_payload)
    else:
        print("Creating Load Balancer...")
        resp = client.post(f"/zones/{ZONE_ID}/load_balancers", json=lb_payload)
    resp.raise_for_status()
    print("Cloudflare health-check-based failover successfully configured!")

if __name__ == "__main__":
    setup_failover()
```

---

### 4.3. Terraform Configuration

The equivalent Terraform configuration structure is defined below:

Save as: `infra/cloudflare_failover/main.tf`

```hcl
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

# ─── Variables ───────────────────────────────────────────────

variable "cloudflare_api_token" {
  description = "Cloudflare API Token"
  type        = string
  sensitive   = true
}

variable "cloudflare_account_id" {
  description = "Cloudflare Account ID"
  type        = string
}

variable "cloudflare_zone_id" {
  description = "Cloudflare Zone ID"
  type        = string
}

variable "domain_name" {
  description = "Domain name for the load balancer (e.g. api.jobhuntpro.com)"
  type        = string
}

# ─── Resources ───────────────────────────────────────────────

# Health Monitor
resource "cloudflare_load_balancer_monitor" "failover_monitor" {
  account_id     = var.cloudflare_account_id
  type           = "https"
  path           = "/api/v1/health/failover"
  method         = "GET"
  port           = 443
  timeout        = 5
  interval       = 60
  retries        = 2
  expected_codes = "2xx"
  description    = "JobHunt Pro database-aware failover health check monitor"
}

# Primary Origin Pool
resource "cloudflare_load_balancer_pool" "primary_pool" {
  account_id   = var.cloudflare_account_id
  name         = "jobhunt-primary-pool"
  description  = "JobHunt Pro Primary Origin Pool"
  monitor      = cloudflare_load_balancer_monitor.failover_monitor.id
  enabled      = true
  minimum_origins = 1

  origins {
    name    = "pythonanywhere"
    address = "jhfguf.pythonanywhere.com"
    enabled = true
    weight  = 1
    header {
      header = "Host"
      values = ["jhfguf.pythonanywhere.com"]
    }
  }
}

# Secondary/Failover Origin Pool
resource "cloudflare_load_balancer_pool" "failover_pool" {
  account_id   = var.cloudflare_account_id
  name         = "jobhunt-failover-pool"
  description  = "JobHunt Pro Secondary/Failover Pool"
  monitor      = cloudflare_load_balancer_monitor.failover_monitor.id
  enabled      = true
  minimum_origins = 1

  origins {
    name    = "fly-io"
    address = "jobhunt-pro.fly.dev"
    enabled = true
    weight  = 1
    header {
      header = "Host"
      values = ["jobhunt-pro.fly.dev"]
    }
  }

  origins {
    name    = "zeabur"
    address = "jobhunt-pro.zeabur.app"
    enabled = true
    weight  = 1
    header {
      header = "Host"
      values = ["jobhunt-pro.zeabur.app"]
    }
  }
}

# Active-Passive Load Balancer
resource "cloudflare_load_balancer" "lb" {
  zone_id          = var.cloudflare_zone_id
  name             = var.domain_name
  description      = "Active-Passive Load Balancer for JobHunt Pro DNS Failover"
  default_pool_ids = [
    cloudflare_load_balancer_pool.primary_pool.id,
    cloudflare_load_balancer_pool.failover_pool.id
  ]
  fallback_pool_id = cloudflare_load_balancer_pool.failover_pool.id
  proxied          = true
  steering_policy  = "off" # Strict priority-based ordering
  ttl              = 30
}
```

---

## 5. Verification Method

To independently verify the solution, follow these three steps:

### 1. Verification of Backend Health Endpoint
We can verify the new endpoint `/api/v1/health/failover` behaviour under different conditions.
*   **Test Script**: Add a test file `tests/test_failover_health.py` containing:
    ```python
    import pytest
    from fastapi.testclient import TestClient
    from unittest.mock import AsyncMock, patch
    from backend.main import app

    client = TestClient(app)

    @patch("backend.main.async_session")
    def test_health_failover_success(mock_session):
        # Mock successful database query execution
        mock_conn = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_conn
        
        response = client.get("/api/v1/health/failover")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    @patch("backend.main.async_session")
    def test_health_failover_db_error(mock_session):
        # Mock database connection failure
        mock_session.return_value.__aenter__.side_effect = Exception("Database connection failed")
        
        response = client.get("/api/v1/health/failover")
        assert response.status_code == 503
        assert response.json()["status"] == "unhealthy"
    ```
*   **Run command**:
    ```bash
    pytest tests/test_failover_health.py
    ```
    This verifies that the endpoint returns `503` upon database degradation and `200` when normal.

### 2. Verification of Configuration Script & Terraform syntax
*   Validate Terraform configuration files without applying:
    ```bash
    cd infra/cloudflare_failover
    terraform init -backend=false
    terraform validate
    ```
    This ensures that there are no schema errors in the resources or variables declaration.

### 3. Simulating Failover in Production
*   **Step A**: Perform a normal check using `curl`:
    ```bash
    curl -H "Host: api.jobhuntpro.com" https://api.jobhuntpro.com/api/v1/health/failover
    ```
    Verify it returns HTTP `200` and headers indicating it was served by `pythonanywhere`.
*   **Step B (Simulate Failure)**: Stop database access or block database traffic on PythonAnywhere.
*   **Step C**: Verify HTTP status transitions to `503`:
    ```bash
    curl -I -s https://jhfguf.pythonanywhere.com/api/v1/health/failover
    # Expected output: HTTP/1.1 503 Service Unavailable
    ```
*   **Step D**: Check Cloudflare's dashboard (under Traffic > Load Balancing) or run:
    ```bash
    curl -H "Host: api.jobhuntpro.com" https://api.jobhuntpro.com/api/v1/health/failover
    ```
    Wait ~60-90 seconds (2 failure intervals) and verify that the response is now served by `fly-io` or `zeabur` (the failover pool), confirming active-passive DNS failover worked correctly.

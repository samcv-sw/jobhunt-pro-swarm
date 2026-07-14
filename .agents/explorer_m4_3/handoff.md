# Handoff Report — Cloudflare Health-Check DNS Failover Design (IMP-128)

## 1. Observation

During our exploration of the codebase, we observed the following files and structural configurations:

1. **Lightweight Health Check Endpoint**:
   In `backend/main.py`, lines 457–460:
   ```python
   @app.get("/healthz")
   async def healthz(request: Request = None) -> dict[str, str]:
       """Lightweight Render health check endpoint."""
       return {"status": "ok"}
   ```
   We also observed a deep health check endpoint at `backend/main.py` lines 487–492:
   ```python
   @app.get("/api/v1/health/detailed")
   @cache(expire=15)
   async def health_detailed(request: Request = None) -> dict[str, Any]:
       """Detailed health check: reports DB, Redis, SMTP, and Groq API status."""
       import time
       result: dict[str, Any] = {"status": "ok", "components": {}}
   ```

2. **Frontend Backend URL Setting**:
   In `deploy/cloudflare-pages.toml`, lines 37–38:
   ```toml
   # Point to your Koyeb backend URL (set this as a Pages secret too)
   NEXT_PUBLIC_API_URL  = "https://your-app.koyeb.app"
   ```

3. **Backend Deployments & Guides**:
   In `deploy/DEPLOYMENT_GUIDE.md`, lines 49–54:
   ```markdown
   ## Step 2 — Backend API: Koyeb (FREE, 24/7 always-on)
   
   1. Sign up at **https://koyeb.com**
   2. Create a new **Service → Docker** service
   3. Connect your GitHub repo OR push the image manually
   4. Set the **Dockerfile path** to: `deploy/Dockerfile.koyeb`
   ```
   And on lines 98–101:
   ```markdown
   4. Add **Environment Variables**:
      - `NEXT_PUBLIC_API_URL` = `https://your-app.koyeb.app`
      - `NODE_VERSION` = `20`
   ```

4. **Multi-Backend Keepalive Lists**:
   In `cloudflare/worker.js`, lines 393–398:
   ```javascript
       const BACKENDS = [
         env.PA_BASE || "https://jhfguf.pythonanywhere.com",
         "https://jobhunt-pro.fly.dev",
         "https://jobhunt-pro.zeabur.app",
         "https://jobhunt-pro.onrender.com"
       ];
   ```

5. **Existing Infrastructure**:
   We found a main Terraform configuration file in `infra/k8s_terraform/main.tf` which configures AWS EKS, Multi-AZ RDS Postgres, and Redis.

---

## 2. Logic Chain

1. **Host Configuration & Dynamic Routing**:
   The current frontend configuration in `deploy/cloudflare-pages.toml` and `deploy/DEPLOYMENT_GUIDE.md` specifies a direct API URL endpoint (`https://your-app.koyeb.app` or similar direct service URL). This setup bypasses traffic routing proxies and binds frontend builds to a single region/provider, offering zero automatic failover.
   *Resolution*: Introducing a custom API subdomain (e.g. `api.jobhuntpro.link`) resolved through a Cloudflare Load Balancer allows us to decouple frontend build configuration from backend service changes.

2. **Mitigating DNS Propagation Delays**:
   Client-side DNS failover using traditional DNS record sets (like Round Robin or simple record replacement) suffers from long DNS propagation delays. This is due to client OS, browser, and local ISP caching of the DNS Time-to-Live (TTL).
   *Resolution*: By deploying the Cloudflare Load Balancer with the Proxy feature enabled (`proxied = true`), clients only resolve DNS to Cloudflare’s stable Anycast IPs. The actual routing decision between the Primary Pool (Koyeb) and the Backup Pool (Fly.dev/Render) is made dynamically by Cloudflare’s Edge router upon request arrival. This bypasses client-side cache restrictions, reducing failover time from hours to seconds (limited only by the monitor interval and retry configuration).

3. **Monitor Optimization**:
   Cloudflare health checks probe the backend at regular intervals. A deep probe like `/api/v1/health/detailed` hits PostgreSQL, Redis, SMTP, and Groq APIs, which introduces significant load when queried by multiple Cloudflare Anycast edge locations.
   *Resolution*: The lightweight `/healthz` endpoint (returning a raw HTTP `200 OK` and `{"status": "ok"}`) is chosen. This provides an efficient, low-overhead check that verifies the HTTP listener and ASGI event loop are running without overloading back-end resources.

4. **Priority-Based Failover**:
   Because the system is designed to run primarily on a fast, free-tier primary cloud node (Koyeb) and fall back to secondary free-tier runtimes (Fly.dev, Zeabur, or Render) only if the primary fails, we require an active-passive setup rather than active-active load sharing.
   *Resolution*: Setting the Load Balancer `steering_policy = "off"` forces the Cloudflare Edge to strictly respect the ordering of pools in `default_pool_ids`. All traffic will route to the first healthy pool (Primary) and fail over to the next (Backup) only if the first is marked unhealthy.

---

## 3. Caveats

1. **D1 Sync Coordination**:
   This failover solution handles API routing. It assumes both primary and backup environments are connected to the same shared or replicated database (such as the Turso serverless SQLite database, as detailed in `deploy/DEPLOYMENT_GUIDE.md` step 1). If independent local databases are used in each region without replication, failover will result in split-brain data inconsistency.
2. **Subscription Requirements**:
   Cloudflare Load Balancing is a paid add-on on Cloudflare Free/Pro plans (starts at $5/month for 2 origins). If the project must strictly cost $0, this feature will require manual DNS failover scripts via the Cloudflare DNS API rather than declarative Terraform Load Balancers.
3. **Session Cache Invalidation**:
   If Redis or temporary session stores are region-locked and not replicated globally, client sessions will be terminated during a failover event, requiring users to log back in.

---

## 4. Conclusion

The Cloudflare health-check-based DNS failover solution (IMP-128) can be fully implemented using a declarative Terraform layout. 
By utilizing `cloudflare_load_balancer`, `cloudflare_load_balancer_pool`, and `cloudflare_load_balancer_monitor` resources with the Edge Proxy enabled, the solution ensures zero-downtime routing with minimal failover latency (~60–120s depending on interval).

We have authored and saved two proposed configuration files in the agent directory that can be moved to the workspace production paths when ready for implementation:
- **Terraform Template**: `.agents/explorer_m4_3/proposed_dns_failover.tf`
- **Operations & Operator Guide**: `.agents/explorer_m4_3/proposed_DNS_FAILOVER.md` (which includes the step-by-step verification checklist and emergency runbook).

---

## 5. Verification Method

To verify the proposed design files:
1. Inspect the Terraform template at `.agents/explorer_m4_3/proposed_dns_failover.tf` and verify that the resources (`cloudflare_load_balancer_monitor`, `cloudflare_load_balancer_pool`, `cloudflare_load_balancer`) use standard Cloudflare Provider v4 syntax and variables.
2. Inspect the operator guide at `.agents/explorer_m4_3/proposed_DNS_FAILOVER.md` to ensure it matches the infrastructure architecture of the codebase and provides a detailed manual verification checklist.
3. To validate that the template contains no syntax issues, run:
   ```powershell
   terraform -chdir="C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m4_3" fmt -check
   ```
   (Alternatively, check the code structure manually).

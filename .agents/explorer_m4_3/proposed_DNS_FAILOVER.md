# 🛡️ JobHunt Pro — Cloudflare Health-Check DNS Failover Operator Guide (IMP-128)

This guide documents the design, deployment, testing, and operations of the active-passive multi-region DNS failover solution for the JobHunt Pro API backend.

---

## 🗺️ Architecture Overview

The DNS Failover solution relies on **Cloudflare Load Balancing** configured at the edge. 

```
                                  ┌───────────────────────────┐
                                  │      Cloudflare Edge      │
                                  │   (api.jobhuntpro.link)   │
                                  └─────────────┬─────────────┘
                                                │
                                  ┌─────────────▼─────────────┐
                                  │  Steering Policy: "off"   │
                                  │   (Strict Priority Order) │
                                  └─────────────┬─────────────┘
                                                │
                       ┌────────────────────────┴────────────────────────┐
             [Primary Pool Healthy]                            [Primary Pool Unhealthy]
                       │                                                 │
        ┌──────────────▼──────────────┐                   ┌──────────────▼──────────────┐
        │        Primary Pool         │                   │         Backup Pool         │
        │    (Koyeb Nano Cloud)       │                   │    (Fly.dev / Render)       │
        │  primary-api.jobhuntpro.link│                   │  backup-api.jobhuntpro.link │
        └──────────────┬──────────────┘                   └──────────────┬──────────────┘
                       │                                                 │
        ┌──────────────▼──────────────┐                   ┌──────────────▼──────────────┐
        │  FastAPI Backend (Koyeb)    │                   │   FastAPI Backend (Backup)  │
        │   Probes: /healthz (200 OK) │                   │  Probes: /healthz (200 OK)  │
        └─────────────────────────────┘                   └─────────────────────────────┘
```

### Key Technical Characteristics

1. **Proxy Mode (`proxied = true`)**: The DNS record is proxied through Cloudflare. Clients resolve `api.jobhuntpro.link` to Cloudflare's Anycast IP addresses. When a failover occurs, Cloudflare updates its internal routing at the edge instantly. This bypasses client-side DNS caching/propagation delays (TTL issues).
2. **Active Monitoring**: Cloudflare's edge nodes probe the `/healthz` endpoint on both origins every 60 seconds.
3. **Failover Threshold**: If the primary origin fails health checks twice consecutively (2 retries × 60s = 120s detection time), it is marked `unhealthy`, and Cloudflare reroutes all new traffic to the backup pool.
4. **Automatic Failback**: Once the primary origin passes health checks twice consecutively, traffic is restored to the primary pool automatically.

---

## 🛠️ Infrastructure Provisioning via Terraform

The failover configuration is managed declaratively in the `infra/cloudflare_failover` directory.

### Prerequisites

- Cloudflare account with active **Load Balancing subscription** or Enterprise plan.
- Cloudflare API Token with the following permissions:
  - `Zone - Load Balancers: Edit`
  - `Account - Load Balancers: Edit`
- Terraform CLI installed (version `>= 1.5.0`).

### Deployment Steps

1. Create a `terraform.tfvars` file containing:
   ```hcl
   cloudflare_api_token     = "your-sensitive-api-token"
   cloudflare_account_id    = "your-cloudflare-account-id"
   cloudflare_zone_id       = "your-cloudflare-zone-id"
   domain                   = "jobhuntpro.link"
   primary_origin_address   = "your-app.koyeb.app"
   backup_origin_address    = "jobhunt-pro.fly.dev"
   alert_notification_email = "ops@jobhuntpro.link"
   ```

2. Initialize and run Terraform:
   ```bash
   cd infra/cloudflare_failover
   terraform init
   terraform plan -out=tfplan
   terraform apply tfplan
   ```

---

## 🔍 Manual Verification & Testing Procedure

Follow this procedure to verify the failover mechanism.

### Phase 1: Baseline Verification (Both Healthy)

1. **Verify DNS Resolution**:
   Run `nslookup` or `dig` on the API domain:
   ```bash
   nslookup api.jobhuntpro.link
   ```
   *Expected result*: Resolves to Cloudflare's Anycast IPs (e.g., `104.21.x.x`, `172.67.x.x`). It must **not** resolve to the direct address of Koyeb or Fly.dev.

2. **Verify Request Flow**:
   Send a health check query:
   ```bash
   curl -i https://api.jobhuntpro.link/healthz
   ```
   *Expected result*: Returns HTTP `200 OK` with payload `{"status": "ok"}` and response header `cf-ray`.

3. **Confirm Primary Routing**:
   Inspect the live logs of the Primary Backend (Koyeb) to confirm it is receiving the traffic.
   ```bash
   koyeb service logs <primary-service-id>
   ```
   *Expected result*: Incoming requests for `/healthz` are logged.

---

### Phase 2: Simulating Primary Failure

1. **Stop / Pause the Primary Backend**:
   Scale the primary Koyeb deployment down to `0` or pause the service:
   ```bash
   koyeb service pause <primary-service-id>
   ```

2. **Monitor Cloudflare Pool Health Status**:
   Execute the following query to Cloudflare's API using your credentials (or view the Cloudflare Dashboard under Traffic -> Load Balancing):
   ```bash
   curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/load_balancers/pools/${PRIMARY_POOL_ID}/health" \
     -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
     -H "Content-Type: application/json" | jq .
   ```
   *Expected result*: Within 60-120 seconds, the pool transitions to `unhealthy`.

3. **Verify Failover Traffic Redirect**:
   Verify that clients continue to receive successful responses:
   ```bash
   curl -i https://api.jobhuntpro.link/healthz
   ```
   *Expected result*: Returns HTTP `200 OK`. 

4. **Verify Backup Logging**:
   Check the logs of the backup backend:
   ```bash
   fly logs -a <backup-app-name>
   ```
   *Expected result*: The backup backend starts logging incoming requests from `/healthz` and client traffic.

---

### Phase 3: Recovery & Failback

1. **Restore the Primary Backend**:
   Scale the primary Koyeb service back up:
   ```bash
   koyeb service resume <primary-service-id>
   ```

2. **Monitor Cloudflare Re-evaluation**:
   Wait ~120 seconds for the health checks to confirm recovery.
   Verify that Cloudflare's pool health returns to `healthy`.

3. **Verify Traffic Resumes on Primary**:
   Send a request and inspect logs on both Koyeb and Fly.dev:
   - Traffic should stop hitting Fly.dev (except for health checks).
   - Traffic should resume hitting Koyeb.

---

## 🚨 Emergency Operations

### Scenario: Primary Backend is unstable (flapping)
If the primary backend is flapping and causing transient issues, operators should manually disable the primary pool to force traffic to the backup pool.

1. **Via Terraform**:
   Set `enabled = false` in the primary origin block or pool:
   ```hcl
   # In terraform.tfvars
   # Modify configuration to remove primary pool or apply an emergency override variable
   ```

2. **Via Cloudflare API (Ad-hoc disable)**:
   ```bash
   curl -X PATCH "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/load_balancers/pools/${PRIMARY_POOL_ID}" \
     -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
     -H "Content-Type: application/json" \
     --data '{"origins":[{"name":"primary-backend","address":"your-app.koyeb.app","enabled":false}]}'
   ```

3. **Via Cloudflare Dashboard**:
   Go to Traffic -> Load Balancing -> Manage Pools -> Edit Primary Pool -> Toggle "primary-backend" origin to **Disabled** -> Save.

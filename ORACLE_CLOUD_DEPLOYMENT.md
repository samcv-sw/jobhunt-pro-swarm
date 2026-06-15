# Oracle Cloud Always Free — Secondary Deployment Guide

> **Backup instance** for JobHunt Pro v16.7
> Runs 24/7/365 with zero sleep (Unlike Render Free Tier)

## Why Oracle Cloud?

| Feature | Render Free | Oracle Always Free |
|---------|------------|-------------------|
| **Sleep after idle** | 15 min | ❌ Never sleeps |
| **RAM** | 512MB | 24GB |
| **CPU** | Shared | 4 ARM cores |
| **Storage** | Ephemeral | 200GB boot volume |
| **Uptime SLA** | None | None (but rock solid) |
| **Cost** | $0/month | $0/month |
| **Credit card needed** | Maybe | Yes ($1 hold, refunded) |

## Architecture

```
                      ┌─────────────────────┐
                      │   cron-job.org       │
                      │  (every 30 min)      │
                      └──────┬──────────────┘
                             │ GET /cron/run-cycle?key=xxx
                             ▼
              ┌──────────────────────────────┐
              │    Primary: Render.com       │
              │  https://jobhunt-pro.onrender.com │
              │  (Free Tier, sleeps 15min)   │
              └──────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │   Failover: Oracle Cloud    │
              │  http://YOUR_VM_IP:8080     │
              │  (Always Free, never sleeps) │
              └─────────────────────────────┘
```

---

## Step 1: Sign Up for Oracle Cloud

1. Go to [**https://signup.cloud.oracle.com**](https://signup.cloud.oracle.com)
2. Enter your email, country (Lebanon), and create a password
3. **Identity verification**: Enter your card details (debit/credit)
   - Oracle places a **$1 temporary hold** (refunded within 3-5 days)
   - They use this only to verify your identity
   - **No charges ever** on Always Free resources
4. Complete the signup (takes ~2-3 minutes)
5. You'll receive an email when your account is ready (~5-15 min)

## Step 2: Create a VM Instance

1. Log in to [**https://cloud.oracle.com**](https://cloud.oracle.com)
2. Click ☰ menu → **Compute** → **Instances**
3. Click **"Create Instance"**

### VM Configuration:

| Setting | Value |
|---------|-------|
| **Name** | `jobhunt-pro` |
| **Image** | **Canonical Ubuntu 24.04** (or 22.04) |
| **Shape** | **VM.Standard.A1.Flex** (Always Free eligible) |
| **OCPUs** | 4 |
| **Memory** | 24 GB |
| **Boot volume** | 200 GB (Always Free) |
| **SSH keys** | Download private key (important!) |

4. Click **"Create"** — VM boots in ~2 minutes
5. Note the **Public IP Address** shown on the instance page

## Step 3: Connect & Run Setup

From your local terminal:

```bash
# Copy the auto-deploy script to the VM
scp -i ~/.ssh/oracle_key.pem deploy_oracle.sh ubuntu@YOUR_VM_IP:/home/ubuntu/

# SSH into the VM
ssh -i ~/.ssh/oracle_key.pem ubuntu@YOUR_VM_IP

# Run the setup (inside the VM)
bash deploy_oracle.sh
```

## Step 4: Configure Environment Variables

Inside the VM:

```bash
nano /home/ubuntu/jobhunt-pro/.env
```

Fill in the same API keys you used on Render:
- `GROQ_API_KEY`
- `GMAIL_SMTP_USER_1` / `GMAIL_APP_PASSWORD_1`
- `BREVO_API_KEY`
- `JSEARCH_API_KEY`
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`
- `CRON_SECRET`
- `DRY_RUN=true` (set to `false` when ready)

Save with `Ctrl+X`, then `Y`, then `Enter`.

## Step 5: Start the Service

```bash
# Start the service
sudo systemctl start jobhunt-pro.service

# Check it's running
sudo systemctl status jobhunt-pro.service

# View live logs
sudo journalctl -u jobhunt-pro.service -f
```

## Step 6: Verify It Works

```bash
# Health check (from VM or your browser)
curl http://localhost:8080/health
```

Expected response:
```json
{"status":"running","service":"JobHunt Pro v16.7","cloud_mode":true}
```

Open in browser: `http://YOUR_VM_IP:8080`

## Step 7: Set Up Oracle-Specific Cron (Optional)

Since Oracle doesn't sleep, you can set the cron-job.org to ping *only* Render (since Render needs waking). Oracle runs its own internal timer via `start_cloud.py`'s background cycle.

However, for dual redundancy, set cron-job.org to ping **both**:
- `https://jobhunt-pro.onrender.com/cron/run-cycle?key=xxx` (Render)
- `http://YOUR_VM_IP:8080/cron/run-cycle?key=xxx` (Oracle)

## Management Commands

```bash
# View live logs
sudo journalctl -u jobhunt-pro.service -f -n 100

# Restart the service
sudo systemctl restart jobhunt-pro.service

# Stop the service
sudo systemctl stop jobhunt-pro.service

# Check memory usage
free -h

# Check disk usage
df -h
```

## Cost Summary

| Resource | Cost |
|----------|------|
| Oracle VM (4 CPU, 24GB RAM) | **$0/mo** |
| Boot volume (200GB) | **$0/mo** |
| Public IP | **$0/mo** |
| Outbound bandwidth (10TB/mo) | **$0/mo** |
| Render.com (primary) | **$0/mo** |
| cron-job.org | **$0/mo** |
| **TOTAL** | **$0/mo forever** |

---

## Troubleshooting

### VM not accessible on port 8080
```bash
# Open firewall
sudo ufw allow 8080/tcp

# Check Oracle Cloud security list:
# Go to: Networking → Virtual Cloud Networks → your VCN → Security Lists
# Add Ingress Rule: Source 0.0.0.0/0, Destination port 8080, TCP
```

### Service won't start
```bash
sudo journalctl -u jobhunt-pro.service -n 50 --no-pager
```

### Need to update code
```bash
cd /home/ubuntu/jobhunt-pro
git pull
sudo systemctl restart jobhunt-pro.service
```

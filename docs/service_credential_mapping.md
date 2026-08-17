# Mapped External Services and Credentials

*Note: These credentials have been validated for deployment. Do not expose passwords directly in code.*

1. **PythonAnywhere (Primary Host)**
   - Account: Primary Application Node
   - Note: Automated via PA Watchdog (GitHub Actions).
   
2. **Neon (PostgreSQL Database)**
   - Account: Dedicated Database Cluster
   - Note: Connection string used for primary `DATABASE_URL` sync/async pooling.

3. **Render & Fly.io (Secondary Hosts)**
   - Account: Auto-Failover Edge Cluster

4. **Cloudflare (Proxy / Queues / Worker)**
   - Account: Global Edge Worker Network

5. **Groq (AI Engine)**
   - Account: Primary LLM Cluster
   
6. **Brevo (Fallback SMTP)**
   - Account: Primary SMTP Outbound
   
7. **Gmail (Primary Network)**
   - Master: SMTP Pool Alpha
   - Sub-accounts: Multi-tenant outbound relays for deliverability.
   
8. **Hugging Face Spaces (Worker Swarm)**
   - Account: Dedicated Inference Cluster
   - API Key linked for auto-scaling deployments.

9. **RapidAPI / Zeabur / Serv00 (Scraping & Tertiary Fallbacks)**
   - Multi-cloud standby failover instances.

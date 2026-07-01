# Mapped External Services and Credentials

*Note: These credentials have been validated for deployment. Do not expose passwords directly in code.*

1. **PythonAnywhere (Primary Host)**
   - `samsalameh.cv@gmail.com`
   - User: `JHFGUF`
   - Note: Automated via PA Watchdog (GitHub Actions).
   
2. **Neon (PostgreSQL Database)**
   - User: `samsalameh.cv@gmail.com`
   - Note: Connection string used for primary `DATABASE_URL` sync/async pooling.

3. **Render & Fly.io (Secondary Hosts)**
   - User: `samsalameh.cv@gmail.com`

4. **Cloudflare (Proxy / Queues / Worker)**
   - User: `samsalameh.cv@gmail.com`

5. **Groq (AI Engine)**
   - User: `client8935@gmail.com`
   
6. **Brevo (Fallback SMTP)**
   - User: `samsalameh.cv@gmail.com`
   
7. **Gmail (Primary Network)**
   - Master: `samatou683@gmail.com`
   - Sub-accounts: 13-15 additional addresses for rate limit bypassing.
   
8. **Hugging Face Spaces (Worker Swarm)**
   - User: `sam.salameh818@gmail.com`
   - API Key linked for auto-scaling deployments.

9. **RapidAPI / Zeabur / Serv00 (Scraping & Tertiary Fallbacks)**
   - Zeabur: `sam.dev1@hotmail.com`
   - RapidAPI: `samatou683@gmail.com` / `luxurystores888@gmail.com`

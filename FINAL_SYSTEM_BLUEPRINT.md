# 🏗️ JobHunt Pro - Master System Blueprint

This document serves as the comprehensive architectural and operational blueprint for the **JobHunt Pro** ecosystem. It maps out all micro-services, APIs, security layers, and asynchronous agents that power the platform.

---

## 1. 🌐 Core Web Layer (`web/app_v2.py`)
The heart of the system is built on a high-performance **FastAPI** server that is wrapped in a WSGI adapter for deployment on PythonAnywhere.
*   **Dynamic Routing:** Loads multiple sub-routers on the fly (Admin, Auth, Dashboard, Payments, Campaigns, Squads, Voice Swarm, Webhook Bots).
*   **Template Engine (Jinja2):** Manages dynamic rendering for both Arabic (default) and English (`/lang/en` routing logic) interfaces.
*   **Database Shim (`pg_sqlite_shim.py`):** Intercepts PostgreSQL queries and translates them to work with local SQLite seamlessly without breaking the cloud-native architecture.
*   **Static Asset Management:** Serves CSS, JS, and compiled Tailwind assets with optimized caching headers.

## 2. 🛡️ Security & Anti-Ban Architecture
*   **Aegis Shield (`core/aegis_shield.py`):** A custom Web Application Firewall (WAF) and Rate Limiter. Defends against DDoS attacks, brute-force attempts, and scraping bots. Uses Upstash Redis (if configured) or an in-memory fallback.
*   **Iron Cloak Anti-Ban:** Protects outbound requests from being flagged by platforms like LinkedIn and Indeed.
*   **Stealth Scraper Injector (`inject_uas.py` / `pa_job_scraper.py`):** Uses advanced techniques (e.g., `curl_cffi` TLS fingerprinting spoofing and randomized User-Agents) to bypass Cloudflare and DataDome protections when scraping job boards.

## 3. 🤖 AI & Automation Engines
*   **Job Scraper (`core/pa_job_scraper.py`):** Fetches job listings from various sources using asynchronous HTTP requests. If primary sources fail, it falls back to stealth scraping to guarantee data delivery.
*   **Cold Blaster (`core/cold_blaster.py`):** Automates cold email outreach to recruiters and hiring managers.
*   **AI Scam Detector (`core/scam_detector.py`):** Analyzes job descriptions using AI to flag fake jobs, phishing attempts, or MLM scams.
*   **Voice Swarm & Squads:** Specialized AI agents designed to handle mock interviews, resume roasting, and personalized career advice.

## 4. 📧 Communication & Outreach
*   **Hotmail Pool (`core/hotmail_pool.py`):** Manages a massive pool of Microsoft Graph API accounts (e.g., 991/1000 active accounts) to distribute email sending load and avoid spam filters.
*   **Email Harvester (`core/email_harvester.py`):** Collects and verifies recruiter email addresses for the Cold Blaster engine.
*   **Telegram Bot Integration (`core/telegram_bot.py` & `core/telegram_enhanced.py`):** A fully-featured Telegram Mini-App and Bot that allows users to track applications, receive instant notifications, and even manage the server remotely via admin commands.

## 5. 📈 Growth & SEO Ecosystem
*   **Growth API (`core/growth_api.py`):** Handles gamification, user tracking, and retention metrics.
*   **SEO Blog Farm (`core/seo_blog_farm.py`):** Programmatically generates and serves SEO-optimized blog posts to capture organic search traffic (e.g., "Automate your job search").
*   **Viral Engine (`core/viral_engine.py`):** Manages referral systems, social sharing links, and viral loops (e.g., sharing ATS scores on LinkedIn/Twitter) to drive free user acquisition.

## 6. ⚙️ Infrastructure & Deployment
*   **Safe Deploy Pipeline (`safe_deploy.py`):** A zero-downtime deployment script that verifies AST syntax before pushing files directly to PythonAnywhere via their REST API, and automatically reloads the WSGI server.
*   **Self-Healing System (`core/auto_heal.py`):** Constantly monitors the system's health. If an endpoint fails, it attempts automated recovery strategies without human intervention.
*   **WSGI Override Fix:** A script (`fix_wsgi.py`) that prevents PythonAnywhere from automatically rolling back live edits to the GitHub `main` branch upon reload, ensuring live patches remain active.

## 7. 🗂️ Data Storage
*   **SQLite Database (`jobhunt_saas_v2.db`):** The central local database storing users, orders, job applications, campaigns, and system configurations. Optimized for fast reads/writes in a single-node setup.
*   **Cache Directory (`cache/`):** Stores panic states, temporary session data, and scraper results to reduce redundant network calls.

---
### 🚀 How the System Flows:
1.  **User Request:** A user visits the site. The **Aegis Shield** verifies they aren't a threat.
2.  **Routing & Language:** **FastAPI** determines if they want Arabic or English based on the `lang` cookie and serves the correct Jinja2 template.
3.  **Job Application:** When a user activates an agent, the request hits the **Job Scraper** (using Iron Cloak for stealth) to find jobs.
4.  **Verification:** Jobs are passed through the **AI Scam Detector**.
5.  **Execution:** The **Cold Blaster** and **Hotmail Pool** orchestrate sending targeted applications and cover letters.
6.  **Notification:** The user receives a real-time update via the **Telegram Bot** or the Web Dashboard.
7.  **Maintenance:** In the background, the **Self-Healing** module and **SEO Blog Farm** keep the system healthy and drive new traffic.

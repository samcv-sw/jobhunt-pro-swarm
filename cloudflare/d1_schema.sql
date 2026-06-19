-- JobHunt Pro — Cloudflare D1 Database Schema
-- $0 — 5GB storage, 5M rows, 50M reads/month
-- Global replication via CF CDN
-- Serves as PA database replica + failover

-- ── Users ──
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    password_hash TEXT NOT NULL,
    cv_url TEXT,
    linkedin_url TEXT,
    target_roles TEXT,        -- JSON array: ["Network Engineer", "DevOps"]
    target_locations TEXT,    -- JSON array: ["Lebanon", "UAE", "Remote"]
    target_salary_min INTEGER DEFAULT 1500,
    byo_smtp_email TEXT,      -- User's own Gmail
    byo_smtp_token TEXT,      -- Encrypted SMTP password
    byo_ai_key TEXT,          -- User's own Groq/Gemini key
    byo_ai_provider TEXT DEFAULT 'groq',
    created_at TEXT DEFAULT (datetime('now')),
    last_active TEXT DEFAULT (datetime('now')),
    status TEXT DEFAULT 'active'  -- active | paused | banned
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

-- ── Jobs ──
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT UNIQUE,         -- Job ID from platform
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    description TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    currency TEXT DEFAULT 'USD',
    job_type TEXT,                  -- full-time, part-time, contract
    work_mode TEXT,                 -- remote, onsite, hybrid
    platform TEXT NOT NULL,         -- linkedin, indeed, bayt, glassdoor
    url TEXT,
    keywords TEXT,                  -- extracted keywords for matching
    posted_at TEXT,
    scraped_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT,
    status TEXT DEFAULT 'active'    -- active | expired | filled
);

CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_platform ON jobs(platform);
CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);
CREATE INDEX IF NOT EXISTS idx_jobs_keywords ON jobs(keywords);
CREATE INDEX IF NOT EXISTS idx_jobs_posted ON jobs(posted_at);

-- ── Applications ──
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',   -- pending | sent | failed | rejected | interview
    email_sent INTEGER DEFAULT 0,
    email_body TEXT,
    cover_letter TEXT,
    sent_at TEXT,
    response_at TEXT,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);

CREATE INDEX IF NOT EXISTS idx_applications_user ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_job ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);

-- ── Campaigns ──
CREATE TABLE IF NOT EXISTS campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    status TEXT DEFAULT 'draft',     -- draft | running | paused | completed
    target_count INTEGER DEFAULT 50,
    sent_count INTEGER DEFAULT 0,
    match_rate REAL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT,
    config TEXT,                    -- JSON: filters, schedule, etc
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_campaigns_user ON campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);

-- ── Stats ──
CREATE TABLE IF NOT EXISTS stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_date TEXT NOT NULL,         -- YYYY-MM-DD
    platform TEXT NOT NULL,          -- overall | linkedin | indeed | etc
    apps_sent INTEGER DEFAULT 0,
    interviews INTEGER DEFAULT 0,
    responses INTEGER DEFAULT 0,
    avg_match_rate REAL DEFAULT 0,
    users_active INTEGER DEFAULT 0,
    PRIMARY KEY (stat_date, platform)
);

-- ── Sync tracking (PA <-> D1) ──
CREATE TABLE IF NOT EXISTS sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,            -- pa | d1 | worker
    action TEXT NOT NULL,            -- insert | update | delete
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    synced_at TEXT DEFAULT (datetime('now')),
    status TEXT DEFAULT 'pending'    -- pending | success | failed
);

-- ── Scraper cache ──
CREATE TABLE IF NOT EXISTS scraper_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    platform TEXT NOT NULL,
    content TEXT,                    -- Cached HTML/JSON
    content_hash TEXT,              -- For dedup
    scraped_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT,                -- When cache is stale
    status INTEGER DEFAULT 200      -- HTTP status
);

CREATE INDEX IF NOT EXISTS idx_cache_url ON scraper_cache(url);
CREATE INDEX IF NOT EXISTS idx_cache_platform ON scraper_cache(platform);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON scraper_cache(expires_at);

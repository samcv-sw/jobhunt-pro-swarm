-- core/db_migrations/003_outreach_deliverability_indices.sql
-- Pillar 2 / Milestone 2: Deliverability, 365-Day Deduplication & Scheduler Indices

-- 1. 365-Day Cooldown Optimization Indices
CREATE INDEX IF NOT EXISTS idx_campaign_emails_email_sent_user 
  ON campaign_emails (email_address, sent_at);

CREATE INDEX IF NOT EXISTS idx_multi_platform_apps_dedup 
  ON multi_platform_apps (user_id, applied_at);

CREATE INDEX IF NOT EXISTS idx_jobs_email_applied 
  ON jobs (email, applied_at);

-- 2. Smart Scheduler & MX Cache Optimization
CREATE INDEX IF NOT EXISTS idx_smart_scheduler_reset 
  ON smart_scheduler_state (last_reset_day, last_reset_hour);

CREATE INDEX IF NOT EXISTS idx_domain_mx_cache_lookup 
  ON domain_mx_cache (domain, updated_at);

-- 3. Telemetry & Failure Tracking Table
CREATE TABLE IF NOT EXISTS smtp_provider_telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_name TEXT NOT NULL,
    status TEXT NOT NULL,
    latency_ms REAL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_smtp_telemetry_prov_time 
  ON smtp_provider_telemetry (provider_name, created_at);

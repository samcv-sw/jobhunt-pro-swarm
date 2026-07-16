-- core/db_migrations/001_performance_indices.sql
-- Optimizing N+1 Problems and Missing Indices for Hydra V2

-- 1. Campaign Emails
CREATE INDEX IF NOT EXISTS idx_campaign_emails_campaign_status ON campaign_emails (campaign_id, status);
CREATE INDEX IF NOT EXISTS idx_campaign_emails_campaign_responded ON campaign_emails (campaign_id, responded_at);
CREATE INDEX IF NOT EXISTS idx_campaign_emails_sent_at ON campaign_emails (sent_at);
CREATE INDEX IF NOT EXISTS idx_campaign_emails_camp_sent ON campaign_emails (campaign_id, sent_at);
-- 2. Jobs
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs (status);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs (company);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs (source);
-- 3. Email Sends Rate Limit Optimization

-- 4. Applications Metrics
CREATE INDEX IF NOT EXISTS idx_applications_metrics ON applications (opened, responded, status);
CREATE INDEX IF NOT EXISTS idx_applications_tracking_id ON applications(tracking_id);
-- 7. CV Profiles User Lookup
CREATE INDEX IF NOT EXISTS idx_cv_profiles_user_id ON cv_profiles (user_id);
-- PostgreSQL Initialization Script
-- Run this when the database first starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create tables
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    phone VARCHAR(50),
    company_name VARCHAR(255),
    user_type VARCHAR(50) DEFAULT 'jobseeker',
    wallet_balance DECIMAL(10,2) DEFAULT 0,
    total_spent DECIMAL(10,2) DEFAULT 0,
    api_key VARCHAR(64) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key);

CREATE TABLE IF NOT EXISTS cv_profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    profile_name VARCHAR(255),
    cv_text TEXT,
    cover_letter_template TEXT,
    email_template TEXT,
    skills TEXT,
    experience_years INTEGER,
    target_titles TEXT,
    target_locations TEXT,
    home_country VARCHAR(100) DEFAULT 'Lebanon',
    min_local_salary DECIMAL(10,2) DEFAULT 0,
    min_international_salary DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_cv_profiles_user ON cv_profiles(user_id);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(64) UNIQUE NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    order_type VARCHAR(50) NOT NULL,
    package_name VARCHAR(100),
    company_count INTEGER,
    amount_usd DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50),
    payment_status VARCHAR(50) DEFAULT 'pending',
    redeem_code VARCHAR(50),
    pay_address VARCHAR(255),
    nowpayments_id BIGINT,
    nowpayments_invoice_url TEXT,
    pay_currency VARCHAR(50),
    pay_amount DECIMAL(20,8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(payment_status);

CREATE TABLE IF NOT EXISTS campaigns (
    id SERIAL PRIMARY KEY,
    campaign_id VARCHAR(64) UNIQUE NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    order_id VARCHAR(64) NOT NULL,
    profile_id INTEGER,
    status VARCHAR(50) DEFAULT 'pending',
    total_companies INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    open_count INTEGER DEFAULT 0,
    response_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_campaigns_user ON campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);

CREATE TABLE IF NOT EXISTS campaign_emails (
    id SERIAL PRIMARY KEY,
    campaign_id VARCHAR(64) NOT NULL,
    company_name VARCHAR(255),
    job_title VARCHAR(255),
    email_address VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    tracking_id VARCHAR(32),
    provider_used VARCHAR(50),
    followup_count INTEGER DEFAULT 0,
    sent_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    responded_at TIMESTAMP,
    response_type VARCHAR(50),
    response_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_campaign_emails_campaign ON campaign_emails(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_emails_status ON campaign_emails(status);
CREATE INDEX IF NOT EXISTS idx_campaign_emails_tracking ON campaign_emails(tracking_id);

CREATE TABLE IF NOT EXISTS wallet_transactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    balance_after DECIMAL(10,2),
    description TEXT,
    tx_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_wallet_tx_user ON wallet_transactions(user_id);

CREATE TABLE IF NOT EXISTS redeem_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    value_usd DECIMAL(10,2) NOT NULL,
    code_type VARCHAR(50) DEFAULT 'sale',
    is_used BOOLEAN DEFAULT FALSE,
    used_by VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_redeem_code ON redeem_codes(code);

CREATE TABLE IF NOT EXISTS referrals (
    id SERIAL PRIMARY KEY,
    referrer_id VARCHAR(64) NOT NULL,
    referred_id VARCHAR(64) NOT NULL,
    commission DECIMAL(10,2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (referrer_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (referred_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);

CREATE TABLE IF NOT EXISTS email_quota (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    count INTEGER DEFAULT 0,
    UNIQUE(provider, date)
);

CREATE INDEX IF NOT EXISTS idx_email_quota_provider_date ON email_quota(provider, date);

CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    subject VARCHAR(255),
    message TEXT,
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pricing_tiers (
    id SERIAL PRIMARY KEY,
    tier VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    companies INTEGER NOT NULL,
    price_usd DECIMAL(10,2) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS service_packages (
    id SERIAL PRIMARY KEY,
    package VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    price_usd DECIMAL(10,2) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS bouquet_packages (
    id SERIAL PRIMARY KEY,
    bouquet VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    price_usd DECIMAL(10,2) NOT NULL,
    description TEXT
);

-- Insert pricing tiers
INSERT INTO pricing_tiers (tier, name, companies, price_usd, description) VALUES
('trial', 'Free Trial', 5, 0, 'Try before you buy'),
('micro', 'Micro', 10, 1.00, '10 companies'),
('nano', 'Nano', 25, 2.00, '25 companies'),
('starter', 'Starter', 50, 3.00, '50 companies'),
('basic', 'Basic', 100, 5.00, '100 companies'),
('growth', 'Growth', 150, 7.00, '150 companies'),
('plus', 'Plus', 200, 10.00, '200 companies'),
('pro', 'Pro', 300, 14.00, '300 companies'),
('premium', 'Premium', 400, 18.00, '400 companies'),
('elite', 'Elite', 500, 22.00, '500 companies'),
('business', 'Business', 600, 26.00, '600 companies'),
('business-plus', 'Business+', 700, 30.00, '700 companies'),
('corporate', 'Corporate', 800, 34.00, '800 companies'),
('corporate-plus', 'Corporate+', 900, 38.00, '900 companies'),
('enterprise', 'Enterprise', 1000, 42.00, '1000 companies'),
('scale', 'Scale', 1500, 55.00, '1500 companies'),
('scale-plus', 'Scale+', 2000, 68.00, '2000 companies'),
('massive', 'Massive', 2500, 80.00, '2500 companies'),
('massive-plus', 'Massive+', 3000, 92.00, '3000 companies'),
('unlimited', 'Unlimited', 5000, 120.00, '5000 companies'),
('ultra', 'Ultra', 7500, 160.00, '7500 companies'),
('ultra-plus', 'Ultra+', 10000, 200.00, '10000 companies'),
('mega', 'Mega', 15000, 280.00, '15000 companies'),
('mega-plus', 'Mega+', 20000, 350.00, '20000 companies'),
('giga', 'Giga', 30000, 480.00, '30000 companies'),
('giga-plus', 'Giga+', 50000, 700.00, '50000 companies'),
('tera', 'Tera', 100000, 1200.00, '100000 companies'),
('peta', 'Peta', 200000, 2000.00, '200000 companies'),
('exa', 'Exa', 500000, 4500.00, '500000 companies'),
('zetta', 'Zetta', 1000000, 8000.00, '1M companies')
ON CONFLICT (tier) DO NOTHING;

-- Insert service packages
INSERT INTO service_packages (package, name, price_usd, description) VALUES
('cv-only', 'CV Optimization', 3.00, 'Professional CV review'),
('cover-only', 'Cover Letter', 2.00, 'AI-generated cover letter'),
('email-only', 'Email Template', 1.00, 'Professional email template'),
('basic-bundle', 'Basic Bundle', 5.00, 'CV + Cover Letter'),
('pro-bundle', 'Pro Bundle', 8.00, 'CV + Cover Letter + Email'),
('ultimate-bundle', 'Ultimate Bundle', 12.00, 'CV + Cover Letter + Email + LinkedIn')
ON CONFLICT (package) DO NOTHING;

-- Insert bouquet packages
INSERT INTO bouquet_packages (bouquet, name, price_usd, description) VALUES
('starter-pack', 'Starter Pack', 8.00, '50 companies + CV + Cover'),
('job-hunter-pack', 'Job Hunter Pack', 15.00, '150 companies + full bundle'),
('career-launcher-pack', 'Career Launcher Pack', 25.00, '300 companies + all features'),
('executive-pack', 'Executive Pack', 50.00, '500 companies + premium'),
('ceo-pack', 'CEO Pack', 100.00, '1000 companies + dedicated agent'),
('hr-basic-pack', 'HR Basic Pack', 75.00, '20 job posts'),
('hr-professional-pack', 'HR Professional Pack', 150.00, '50 job posts'),
('hr-enterprise-pack', 'HR Enterprise Pack', 400.00, 'Unlimited posts'),
('recruitment-agency-pack', 'Recruitment Agency Pack', 500.00, 'Unlimited + white-label'),
('staffing-pack', 'Staffing Company Pack', 800.00, 'Everything + SLA'),
('tech-pack', 'Tech Industry Pack', 30.00, '500 companies + tech CV'),
('healthcare-pack', 'Healthcare Pack', 35.00, '400 companies + medical CV'),
('finance-pack', 'Finance Pack', 35.00, '400 companies + finance CV'),
('engineering-pack', 'Engineering Pack', 30.00, '500 companies + technical CV'),
('marketing-pack', 'Marketing Pack', 25.00, '300 companies + creative CV')
ON CONFLICT (bouquet) DO NOTHING;

-- Daily Login Rewards (Gacha Retention Loop)
CREATE TABLE IF NOT EXISTS daily_logins (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    login_date DATE NOT NULL,
    streak_days INTEGER DEFAULT 1,
    reward_amount DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE(user_id, login_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_logins_user ON daily_logins(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_logins_date ON daily_logins(login_date);

-- New SaaS Store & Marketing Modules
CREATE TABLE IF NOT EXISTS flash_sales (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    discount_percent DECIMAL(5,2) NOT NULL DEFAULT 10,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS purchased_services (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    package_id VARCHAR(50) NOT NULL,
    package_name VARCHAR(255) NOT NULL,
    price_paid DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS manual_emails (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64),
    to_email VARCHAR(255) NOT NULL,
    subject VARCHAR(255),
    body TEXT,
    price_usd DECIMAL(10,2) DEFAULT 0.1,
    admin_email VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- ═══════════════════════════════════════════════════════════════════════════
-- APEX MATRIX: GDPR SOVEREIGN COMPLIANCE — SUPPRESSION LIST
-- ═══════════════════════════════════════════════════════════════════════════
-- Stores all opt-out / unsubscribe requests permanently.
-- Must be checked before EVERY outbound email to satisfy CNIL/GDPR Article 21
-- (Right to Object) and avoid fines of up to 4% global annual turnover.
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS suppression_list (
    id             SERIAL PRIMARY KEY,
    email          VARCHAR(255) UNIQUE NOT NULL,   -- normalized lowercase
    reason         VARCHAR(100) DEFAULT 'user_request',  -- user_request | bounce | complaint | admin
    suppressed_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active      BOOLEAN DEFAULT TRUE,           -- FALSE = re-opted-in (rare)
    source         VARCHAR(50) DEFAULT 'web_ui',   -- web_ui | email_link | api | telegram
    user_id        VARCHAR(64)                     -- link to user if known
);

CREATE INDEX IF NOT EXISTS idx_suppression_email    ON suppression_list(email);
CREATE INDEX IF NOT EXISTS idx_suppression_active   ON suppression_list(is_active);
CREATE INDEX IF NOT EXISTS idx_suppression_date     ON suppression_list(suppressed_at DESC);

-- ═══════════════════════════════════════════════════════════════════════════
-- APEX MATRIX: JOB QUEUE RETRY MECHANICS
-- ═══════════════════════════════════════════════════════════════════════════
-- Adds retry_count, max_retries, and next_retry_at columns to job_queue.
-- Enables exponential backoff at the queue level: failed tasks are
-- automatically rescheduled with increasing delays rather than silently dying.
-- ═══════════════════════════════════════════════════════════════════════════
ALTER TABLE job_queue ADD COLUMN IF NOT EXISTS retry_count   INTEGER DEFAULT 0;
ALTER TABLE job_queue ADD COLUMN IF NOT EXISTS max_retries   INTEGER DEFAULT 3;
ALTER TABLE job_queue ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMP;
ALTER TABLE job_queue ADD COLUMN IF NOT EXISTS priority      INTEGER DEFAULT 5; -- 1=highest, 10=lowest

CREATE INDEX IF NOT EXISTS idx_job_queue_retry ON job_queue(next_retry_at ASC)
    WHERE status = 'pending' OR status = 'failed';
CREATE INDEX IF NOT EXISTS idx_job_queue_priority ON job_queue(priority ASC, created_at ASC)
    WHERE status = 'pending';

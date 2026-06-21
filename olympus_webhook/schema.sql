CREATE TABLE users (
    telegram_id TEXT PRIMARY KEY,
    first_name TEXT,
    referral_code TEXT UNIQUE,
    referred_by TEXT,
    credits INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

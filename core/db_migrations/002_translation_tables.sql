-- core/db_migrations/002_translation_tables.sql
-- Create translation tables for multilingual support

-- 1. Job Translation Table
CREATE TABLE IF NOT EXISTS job_translation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    language_code VARCHAR(10) NOT NULL,
    title TEXT,
    description TEXT,
    requirements TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. User Translation Table
CREATE TABLE IF NOT EXISTS user_translation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    language_code VARCHAR(10) NOT NULL,
    bio TEXT,
    skills TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. UI Text Translation Table
CREATE TABLE IF NOT EXISTS ui_text_translation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language_code VARCHAR(10) NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Generic Translation Table
CREATE TABLE IF NOT EXISTS translation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language_code VARCHAR(10) NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_job_translation_job_id ON job_translation (job_id);
CREATE INDEX IF NOT EXISTS idx_job_translation_language_code ON job_translation (language_code);
CREATE INDEX IF NOT EXISTS idx_user_translation_user_id ON user_translation (user_id);
CREATE INDEX IF NOT EXISTS idx_user_translation_language_code ON user_translation (language_code);
CREATE INDEX IF NOT EXISTS idx_ui_text_translation_key ON ui_text_translation (key);
CREATE INDEX IF NOT EXISTS idx_ui_text_translation_language_code ON ui_text_translation (language_code);
CREATE INDEX IF NOT EXISTS idx_translation_language_code ON translation (language_code);
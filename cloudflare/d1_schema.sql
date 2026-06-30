-- Cloudflare D1 Schema for JobHunt Pro
-- This script migrates your SQLite tables to a globally distributed D1 Database.
-- Run this using: wrangler d1 execute swarm-db --file=cloudflare/d1_schema.sql

DROP TABLE IF EXISTS sync_queue;
CREATE TABLE sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    job_url TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    status TEXT DEFAULT 'synced',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Note: You should replicate all tables from app_v2.py here (users, invoices, etc.)
-- when you are ready to fully migrate off PythonAnywhere SQLite.

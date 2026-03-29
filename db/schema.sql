-- db/schema.sql
-- Run once to create all tables.
-- SQLite is used for simplicity. Upgrade to PostgreSQL at 1000+ users.

-- Users: stores login info, plan tier, and preferences
CREATE TABLE IF NOT EXISTS users (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    email          TEXT    UNIQUE NOT NULL,
    password_hash  TEXT    NOT NULL,
    name           TEXT    NOT NULL DEFAULT '',
    goal           TEXT    NOT NULL DEFAULT 'health',
    user_type      TEXT    NOT NULL DEFAULT 'other',
    timezone       TEXT    NOT NULL DEFAULT 'UTC',
    reminder_hour  INTEGER NOT NULL DEFAULT 8,
    reminder_min   INTEGER NOT NULL DEFAULT 0,
    plan_tier      TEXT    NOT NULL DEFAULT 'free',   -- free | pro | family
    stripe_cust_id TEXT    DEFAULT '',
    active_plan_id INTEGER DEFAULT NULL,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Habit plans: the full AI-generated JSON plan for a user
CREATE TABLE IF NOT EXISTS habit_plans (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       TEXT    NOT NULL DEFAULT 'My Habit Plan',
    goal        TEXT    NOT NULL,
    user_type   TEXT    NOT NULL,
    plan_json   TEXT    NOT NULL,   -- Full GPT-4o plan stored as JSON string
    total_days  INTEGER NOT NULL DEFAULT 30,
    current_day INTEGER NOT NULL DEFAULT 1,
    start_date  TEXT    NOT NULL,   -- ISO date string YYYY-MM-DD
    status      TEXT    NOT NULL DEFAULT 'active',  -- active | paused | completed
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily logs: one row per habit completion attempt per day
CREATE TABLE IF NOT EXISTS daily_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id     INTEGER NOT NULL REFERENCES habit_plans(id) ON DELETE CASCADE,
    habit_id    TEXT    NOT NULL,   -- matches habit["id"] in plan_json
    plan_day    INTEGER NOT NULL,
    log_date    TEXT    NOT NULL,   -- ISO date string YYYY-MM-DD
    completed   INTEGER NOT NULL DEFAULT 0,  -- 0 or 1 (SQLite has no BOOLEAN)
    logged_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, habit_id, log_date)     -- prevent duplicate completions
);

-- Chat history: stores AI coach conversation per user
CREATE TABLE IF NOT EXISTS chat_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role       TEXT    NOT NULL,    -- 'user' or 'assistant'
    message    TEXT    NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

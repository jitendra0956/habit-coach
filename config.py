"""
config.py
---------
Central configuration for AI Personal Habit Coach.
All environment variables and app-wide constants live here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── OpenAI ──────────────────────────────────────────────
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL    = "gpt-4o"

# ── Stripe ──────────────────────────────────────────────
STRIPE_SECRET_KEY      = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET  = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRO_PRICE_ID    = os.getenv("STRIPE_PRO_PRICE_ID", "")
STRIPE_FAMILY_PRICE_ID = os.getenv("STRIPE_FAMILY_PRICE_ID", "")

# ── Email ───────────────────────────────────────────────
SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", 587))
SMTP_USER     = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# ── App ─────────────────────────────────────────────────
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "dev-secret-change-in-production")
DB_PATH        = os.getenv("DB_PATH", "habit_coach.db")

# ── Plan settings ───────────────────────────────────────
PLAN_DURATIONS = [7, 14, 30]
DEFAULT_PLAN   = 30
MAX_FREE_PLAN_DAYS = 7          # Free users get 7-day plans only
MAX_FREE_COMPLETIONS_PER_DAY = 3  # Free users can complete 3 habits/day

import sqlite3

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

"""
db/queries.py
-------------
Every database read/write operation lives here.
We use raw SQLite for simplicity — no ORM needed at this scale.

HOW IT WORKS:
- get_db_connection() opens a connection to the SQLite file.
- All functions take a connection (conn) as first argument.
- This lets us reuse one connection per Streamlit session.
"""

import sqlite3
import json
from datetime import date, datetime
from config import DB_PATH


# ── Connection ────────────────────────────────────────────────────────────────

def get_db_connection() -> sqlite3.Connection:
    """
    Open (or create) the SQLite database and initialise the schema.
    Returns a connection object with dict-like row access.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row   # rows behave like dicts: row['name']
    conn.execute("PRAGMA journal_mode=WAL")  # faster concurrent writes

    # Create tables if they don't exist yet
    with open("db/schema.sql") as f:
        conn.executescript(f.read())
    conn.commit()
    return conn


# ── User operations ───────────────────────────────────────────────────────────

def create_user(conn, email: str, password_hash: str, name: str) -> int:
    """Insert a new user. Returns the new user's id."""
    cur = conn.execute(
        "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
        (email.lower().strip(), password_hash, name.strip())
    )
    conn.commit()
    return cur.lastrowid


def get_user_by_email(conn, email: str) -> sqlite3.Row | None:
    """Fetch one user by email. Returns None if not found."""
    return conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (email.lower().strip(),)
    ).fetchone()


def get_user_by_id(conn, user_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def update_user_profile(conn, user_id: int, name: str, goal: str,
                         user_type: str, timezone: str,
                         reminder_hour: int, reminder_min: int):
    conn.execute(
        """UPDATE users SET name=?, goal=?, user_type=?, timezone=?,
           reminder_hour=?, reminder_min=? WHERE id=?""",
        (name, goal, user_type, timezone, reminder_hour, reminder_min, user_id)
    )
    conn.commit()


def update_user_plan_tier(conn, user_id: int, tier: str):
    conn.execute("UPDATE users SET plan_tier=? WHERE id=?", (tier, user_id))
    conn.commit()


def get_all_users_with_reminders(conn) -> list:
    """Used by the scheduler to fetch users who need reminders."""
    return conn.execute(
        "SELECT id, email, name, goal, reminder_hour, reminder_min, timezone "
        "FROM users"
    ).fetchall()


# ── Habit plan operations ─────────────────────────────────────────────────────

def save_habit_plan(conn, user_id: int, goal: str, user_type: str,
                    plan_data: dict, total_days: int) -> int:
    """
    Save a new AI-generated habit plan.
    plan_data is the dict returned by ai_engine.generate_habit_plan().
    Returns the new plan id.
    """
    cur = conn.execute(
        """INSERT INTO habit_plans
           (user_id, title, goal, user_type, plan_json, total_days, start_date)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            plan_data.get("plan_title", "My Habit Plan"),
            goal,
            user_type,
            json.dumps(plan_data),
            total_days,
            date.today().isoformat()
        )
    )
    plan_id = cur.lastrowid
    # Set this plan as the user's active plan
    conn.execute(
        "UPDATE users SET active_plan_id=? WHERE id=?", (plan_id, user_id)
    )
    conn.commit()
    return plan_id


def get_active_plan(conn, user_id: int) -> dict | None:
    """
    Returns the active habit plan as a Python dict, or None.
    The plan_json column is parsed from JSON string back to dict.
    """
    user = get_user_by_id(conn, user_id)
    if not user or not user["active_plan_id"]:
        return None
    row = conn.execute(
        "SELECT * FROM habit_plans WHERE id=?", (user["active_plan_id"],)
    ).fetchone()
    if not row:
        return None
    plan = dict(row)
    plan["plan_data"] = json.loads(plan["plan_json"])  # parse JSON string → dict
    return plan


def advance_plan_day(conn, plan_id: int):
    """Move the plan forward one day (called after all habits are done)."""
    conn.execute(
        "UPDATE habit_plans SET current_day = current_day + 1 WHERE id=?",
        (plan_id,)
    )
    conn.commit()


def mark_plan_complete(conn, plan_id: int):
    conn.execute(
        "UPDATE habit_plans SET status='completed' WHERE id=?", (plan_id,)
    )
    conn.commit()


# ── Daily log / completion operations ────────────────────────────────────────

def log_habit_completion(conn, user_id: int, plan_id: int,
                          habit_id: str, plan_day: int) -> bool:
    """
    Mark a specific habit as completed today.
    Uses INSERT OR IGNORE to avoid duplicates (the UNIQUE constraint).
    Returns True if newly logged, False if already done.
    """
    today = date.today().isoformat()
    cur = conn.execute(
        """INSERT OR IGNORE INTO daily_logs
           (user_id, plan_id, habit_id, plan_day, log_date, completed)
           VALUES (?, ?, ?, ?, ?, 1)""",
        (user_id, plan_id, habit_id, plan_day, today)
    )
    conn.commit()
    return cur.rowcount > 0  # rowcount=0 means it was already logged


def get_completions_for_user(conn, user_id: int) -> list[dict]:
    """All completion records for this user, newest first."""
    rows = conn.execute(
        "SELECT * FROM daily_logs WHERE user_id=? AND completed=1 ORDER BY log_date DESC",
        (user_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_today_completions(conn, user_id: int) -> set[str]:
    """Returns a set of habit_ids completed today."""
    today = date.today().isoformat()
    rows = conn.execute(
        "SELECT habit_id FROM daily_logs WHERE user_id=? AND log_date=? AND completed=1",
        (user_id, today)
    ).fetchall()
    return {r["habit_id"] for r in rows}


def get_completions_by_date(conn, user_id: int) -> dict[str, int]:
    """
    Returns a dict mapping ISO date string → number of habits completed.
    Used to render the progress heatmap.
    """
    rows = conn.execute(
        """SELECT log_date, COUNT(*) as cnt
           FROM daily_logs WHERE user_id=? AND completed=1
           GROUP BY log_date""",
        (user_id,)
    ).fetchall()
    return {r["log_date"]: r["cnt"] for r in rows}


# ── Chat history operations ───────────────────────────────────────────────────

def save_chat_message(conn, user_id: int, role: str, message: str):
    conn.execute(
        "INSERT INTO chat_history (user_id, role, message) VALUES (?, ?, ?)",
        (user_id, role, message)
    )
    conn.commit()


def get_chat_history(conn, user_id: int, limit: int = 20) -> list[dict]:
    """Last `limit` messages for the AI coach context window."""
    rows = conn.execute(
        """SELECT role, message FROM chat_history
           WHERE user_id=? ORDER BY id DESC LIMIT ?""",
        (user_id, limit)
    ).fetchall()
    # Reverse so oldest message is first (correct order for OpenAI)
    return [{"role": r["role"], "content": r["message"]} for r in reversed(rows)]


def clear_chat_history(conn, user_id: int):
    conn.execute("DELETE FROM chat_history WHERE user_id=?", (user_id,))
    conn.commit()

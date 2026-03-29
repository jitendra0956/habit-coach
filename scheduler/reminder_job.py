"""
scheduler/reminder_job.py
--------------------------
Background job that sends daily email reminders to all users.

HOW APSCHEDULER WORKS:
- APScheduler runs jobs in the background while your Streamlit app is running.
- We create a BackgroundScheduler (runs in a separate thread).
- We add a CronTrigger job: "run every day at 8:00 AM UTC" (adjustable).
- The scheduler checks each user's preferred reminder time.

IMPORTANT: In Streamlit, this scheduler starts when app.py loads.
APScheduler is good for development. For production (many users),
use a proper task queue like Celery + Redis.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Global scheduler instance — created once, reused
_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    """Get (or create) the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="UTC")
    return _scheduler


def start_scheduler():
    """Start the background scheduler. Call this once from app.py."""
    scheduler = get_scheduler()
    if not scheduler.running:
        # Add the main reminder job: runs every hour, checks who needs a reminder
        scheduler.add_job(
            func=_send_due_reminders,
            trigger=CronTrigger(minute=0),   # runs at the top of every hour
            id="hourly_reminders",
            replace_existing=True,
            misfire_grace_time=300,           # up to 5 minutes late is OK
        )
        scheduler.start()
        print("[Scheduler] Started. Hourly reminder job registered.")


def _send_due_reminders():
    """
    Check all users and send email reminders to those whose reminder
    time matches the current UTC hour.

    This function runs every hour in the background.
    """
    from datetime import datetime, timezone
    from db.queries import get_db_connection, get_all_users_with_reminders, get_today_completions
    from core.streak_tracker import calculate_streak
    from scheduler.email_sender import send_reminder_email

    now_utc = datetime.now(timezone.utc)
    conn = get_db_connection()

    try:
        users = get_all_users_with_reminders(conn)
        for user in users:
            # Convert current UTC time to user's timezone
            try:
                user_tz = pytz.timezone(user["timezone"] or "UTC")
            except pytz.UnknownTimeZoneError:
                user_tz = pytz.UTC

            user_now = now_utc.astimezone(user_tz)

            # Check if this hour matches the user's preferred reminder hour
            if user_now.hour != user["reminder_hour"]:
                continue

            # Don't remind users who already completed habits today
            done_today = get_today_completions(conn, user["id"])
            if done_today:
                continue

            streak_data = calculate_streak(conn, user["id"])

            send_reminder_email(
                to_email=user["email"],
                name=user["name"] or "Friend",
                streak=streak_data["current"],
                goal=user["goal"],
            )
    finally:
        conn.close()

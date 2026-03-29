"""
core/streak_tracker.py
----------------------
Calculates habit streaks from the daily_logs table.

HOW STREAKS WORK:
A "streak" is the number of consecutive days where the user completed
at least one habit. We walk backwards from today, counting consecutive days.

Example:
  Completed dates: [2024-03-01, 2024-03-02, 2024-03-04, 2024-03-05]
  Today = 2024-03-05
  Walking back: 2024-03-05 ✓, 2024-03-04 ✓, 2024-03-03 ✗ → streak = 2
"""

from datetime import date, timedelta
from db.queries import get_completions_for_user, get_today_completions


def calculate_streak(conn, user_id: int) -> dict:
    """
    Calculate the current and longest streak for a user.

    Returns a dict:
    {
        "current":         int,   # days in a row up to today
        "longest":         int,   # best streak ever
        "completed_today": bool,  # True if at least 1 habit done today
        "total_days":      int,   # total calendar days with any completion
        "completion_dates":set    # all ISO dates with completions
    }
    """
    completions = get_completions_for_user(conn, user_id)

    # Build a set of date strings where user completed at least 1 habit
    completion_dates: set[str] = {c["log_date"] for c in completions}

    today = date.today()
    today_str = today.isoformat()

    # ── Current streak ────────────────────────────────────────────────────────
    current_streak = 0
    check_date = today
    while check_date.isoformat() in completion_dates:
        current_streak += 1
        check_date -= timedelta(days=1)

    # ── Longest streak (iterate over sorted dates) ───────────────────────────
    longest = 0
    if completion_dates:
        sorted_dates = sorted(date.fromisoformat(d) for d in completion_dates)
        temp = 1
        longest = 1
        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
                temp += 1
                longest = max(longest, temp)
            else:
                temp = 1

    return {
        "current":          current_streak,
        "longest":          longest,
        "completed_today":  today_str in completion_dates,
        "total_days":       len(completion_dates),
        "completion_dates": completion_dates,
    }


def get_week_completion_rate(conn, user_id: int, plan_id: int,
                              last_n_days: int = 7) -> float:
    """
    Return what fraction of habits were completed in the last N days.
    Used by the difficulty adapter to decide if the plan is too hard/easy.

    Returns a float 0.0 → 1.0
    """
    completions = get_completions_for_user(conn, user_id)
    today = date.today()

    recent = [
        c for c in completions
        if c["plan_id"] == plan_id
        and (today - date.fromisoformat(c["log_date"])).days <= last_n_days
    ]

    if not recent:
        return 0.0

    completed = sum(1 for c in recent if c["completed"])
    return completed / len(recent)


def get_habit_heatmap_data(conn, user_id: int) -> dict[str, int]:
    """
    Returns {date_string: count} for the last 365 days.
    Used to render the GitHub-style contribution heatmap.
    """
    from db.queries import get_completions_by_date
    raw = get_completions_by_date(conn, user_id)

    today = date.today()
    heatmap = {}
    for i in range(365):
        d = (today - timedelta(days=i)).isoformat()
        heatmap[d] = raw.get(d, 0)

    return heatmap

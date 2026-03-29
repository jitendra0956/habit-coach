"""
core/difficulty_adapter.py
--------------------------
Analyses the user's recent completion rate and suggests whether
the current plan needs to be made easier or harder.

THE LOGIC (Goldilocks principle):
- If completion rate > 90% for 5+ days → plan is TOO EASY → suggest harder habits
- If completion rate < 50% for 5+ days → plan is TOO HARD → suggest easier habits
- Otherwise → plan is JUST RIGHT → no change needed

We don't auto-change the plan (that would surprise users).
Instead, we surface a suggestion card in the UI.
"""

from core.streak_tracker import get_week_completion_rate


def get_adaptation_suggestion(conn, user_id: int, plan_id: int) -> dict | None:
    """
    Check recent completion rate and return an adaptation suggestion if needed.

    Returns None if no change is needed, or a dict:
    {
        "direction": "easier" | "harder",
        "message":   "Human-readable suggestion",
        "rate":      float (0.0 → 1.0)
    }
    """
    rate = get_week_completion_rate(conn, user_id, plan_id, last_n_days=7)

    if rate == 0.0:
        return None  # Not enough data yet

    if rate > 0.90:
        return {
            "direction": "harder",
            "message": (
                f"You're completing {int(rate * 100)}% of your habits — amazing! "
                "Your habits might be too easy. Ready to level up the challenge?"
            ),
            "rate": rate,
        }

    if rate < 0.50:
        return {
            "direction": "easier",
            "message": (
                f"You're completing {int(rate * 100)}% of your habits. "
                "That's okay — let's make the habits a bit easier so you build momentum."
            ),
            "rate": rate,
        }

    return None  # In the Goldilocks zone — no change needed


def should_advance_day(today_habits: list[dict], completed_ids: set[str]) -> bool:
    """
    Return True if all of today's habits have been completed.
    Used to automatically advance the plan to the next day.
    """
    if not today_habits:
        return False
    return all(h["id"] in completed_ids for h in today_habits)

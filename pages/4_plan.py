"""
pages/4_plan.py
---------------
Display the user's full habit plan — all weeks and days.

Users can browse their entire plan, see upcoming habits,
and understand how difficulty progresses week by week.
"""

import streamlit as st
from auth.auth_handler import require_login
from db.queries import get_active_plan, get_today_completions
from utils.constants import HABIT_CATEGORIES, TIME_OF_DAY_LABELS

st.set_page_config(page_title="My Plan", page_icon="📋", layout="wide")
require_login()

conn       = st.session_state["db_conn"]
user_id    = st.session_state["user_id"]
active_plan = get_active_plan(conn, user_id)

if not active_plan:
    st.title("No active plan")
    st.info("You don't have a habit plan yet.")
    st.page_link("pages/1_onboarding.py", label="Create my plan →", icon="✨")
    st.stop()

plan_data   = active_plan["plan_data"]
current_day = active_plan["current_day"]
total_days  = active_plan["total_days"]

# ── Header ────────────────────────────────────────────────────────────────────
st.title(plan_data.get("plan_title", "My Habit Plan"))
st.caption(plan_data.get("plan_summary", ""))

# Progress bar
progress = (current_day - 1) / total_days
st.progress(progress, text=f"Day {current_day} of {total_days} ({int(progress*100)}%)")

# ── Success tips ──────────────────────────────────────────────────────────────
tips = plan_data.get("success_tips", [])
if tips:
    with st.expander("Tips for success from your coach"):
        for tip in tips:
            st.write(f"• {tip}")

st.divider()

# ── Completed habit IDs today (to show checkmarks) ───────────────────────────
completed_today = get_today_completions(conn, user_id)

# ── Browse weeks ──────────────────────────────────────────────────────────────
phases = plan_data.get("weekly_phases", [])

for phase in phases:
    week_num   = phase.get("week", "?")
    week_theme = phase.get("theme", f"Week {week_num}")

    # Check if this week has any days that are current or past
    days_in_week = phase.get("days", [])
    first_day    = days_in_week[0]["day"] if days_in_week else 0
    last_day     = days_in_week[-1]["day"] if days_in_week else 0

    if first_day > current_day:
        status_icon = "🔒"
    elif last_day < current_day:
        status_icon = "✅"
    else:
        status_icon = "▶️"

    with st.expander(f"{status_icon} Week {week_num}: {week_theme}",
                     expanded=(first_day <= current_day <= last_day)):

        for day_obj in days_in_week:
            day_num  = day_obj["day"]
            habits   = day_obj.get("habits", [])
            is_today = (day_num == current_day)
            is_past  = (day_num < current_day)

            # Day label
            day_style = "**" if is_today else ""
            if is_today:
                st.markdown(f"### Day {day_num} ← Today")
            elif is_past:
                st.markdown(f"**Day {day_num}** ✓")
            else:
                st.markdown(f"Day {day_num}")

            # Show habits for this day
            cols = st.columns(len(habits)) if habits else []
            for i, habit in enumerate(habits):
                with (cols[i] if cols else st.container()):
                    habit_id = habit["id"]
                    done     = habit_id in completed_today if is_today else is_past

                    with st.container(border=True):
                        header = f"{'✓ ' if done else ''}{habit['name']}"
                        st.write(f"**{header}**")
                        diff = habit.get("difficulty", 1)
                        st.caption(
                            f"{habit['duration_minutes']} min · "
                            f"{'●' * diff}{'○' * (5 - diff)} · "
                            f"{TIME_OF_DAY_LABELS.get(habit.get('time_of_day',''), '')}"
                        )
                        if is_today or not is_past:
                            st.write(habit["description"])

            st.markdown("---")

# ── Start a new plan ─────────────────────────────────────────────────────────
st.divider()
st.subheader("Want to start fresh?")
if st.button("Create a new habit plan"):
    st.page_link("pages/1_onboarding.py",
                 label="Start new plan →", icon="✨")

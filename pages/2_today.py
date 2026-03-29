"""
pages/2_today.py
----------------
The main daily page — users check off today's habits here.

THIS IS THE MOST IMPORTANT PAGE. It should feel satisfying and motivating.

FLOW:
1. Load the user's active plan and find today's habits
2. Show each habit as a card with a "Complete" button
3. When clicked, log the completion in daily_logs table
4. When all done: show celebration + motivational message
5. If completion rate suggests difficulty change, show suggestion
"""

import streamlit as st
from datetime import date
from auth.auth_handler import require_login
from db.queries import (
    get_active_plan, log_habit_completion,
    get_today_completions, advance_plan_day
)
from core.streak_tracker import calculate_streak
from core.ai_engine import generate_motivation_message
from core.difficulty_adapter import get_adaptation_suggestion, should_advance_day
from utils.constants import HABIT_CATEGORIES, TIME_OF_DAY_LABELS

st.set_page_config(page_title="Today's Habits", page_icon="✅", layout="wide")
require_login()

conn       = st.session_state["db_conn"]
user_id    = st.session_state["user_id"]
user_name  = st.session_state.get("user_name", "Friend")
goal       = st.session_state.get("goal", "health")

# ── Load plan ─────────────────────────────────────────────────────────────────
active_plan = get_active_plan(conn, user_id)

if not active_plan:
    st.title("No active plan")
    st.info("You don't have a habit plan yet. Let's create one!")
    st.page_link("pages/1_onboarding.py", label="Create my plan →", icon="✨")
    st.stop()

plan_data   = active_plan["plan_data"]
plan_id     = active_plan["id"]
current_day = active_plan["current_day"]
total_days  = active_plan["total_days"]

# ── Find today's habits in the plan JSON ─────────────────────────────────────
today_habits: list[dict] = []
for phase in plan_data.get("weekly_phases", []):
    for day_obj in phase.get("days", []):
        if day_obj["day"] == current_day:
            today_habits = day_obj.get("habits", [])
            break

# ── Streak header ─────────────────────────────────────────────────────────────
streak_data     = calculate_streak(conn, user_id)
completed_today = get_today_completions(conn, user_id)

st.title(f"Day {current_day} of {total_days}")
st.caption(date.today().strftime("%A, %B %d, %Y"))

col1, col2, col3, col4 = st.columns(4)
col1.metric("Streak",        f"{streak_data['current']} days 🔥")
col2.metric("Longest",       f"{streak_data['longest']} days")
col3.metric("Habits done today", f"{len(completed_today)}/{len(today_habits)}")
col4.metric("Plan progress", f"{current_day}/{total_days} days")

st.divider()

# ── Habit cards ───────────────────────────────────────────────────────────────
if not today_habits:
    st.info("No habits scheduled for today. Check the plan page.")
    st.stop()

# Group habits by time of day for better visual organisation
groups = {"morning": [], "afternoon": [], "evening": [], "anytime": []}
for h in today_habits:
    groups.setdefault(h.get("time_of_day", "anytime"), []).append(h)

all_done = all(h["id"] in completed_today for h in today_habits)

for time_slot, habits in groups.items():
    if not habits:
        continue

    label = TIME_OF_DAY_LABELS.get(time_slot, time_slot.title())
    st.subheader(f"{label} habits")

    for habit in habits:
        habit_id   = habit["id"]
        is_done    = habit_id in completed_today
        difficulty = habit.get("difficulty", 1)

        # Colour the card border green if done
        border_color = "green" if is_done else None

        with st.container(border=True):
            col_text, col_btn = st.columns([5, 1])

            with col_text:
                # Difficulty indicator dots
                dots = "●" * difficulty + "○" * (5 - difficulty)
                st.markdown(
                    f"**{habit['name']}**  "
                    f"<span style='color:gray; font-size:12px'>{dots}</span>",
                    unsafe_allow_html=True
                )
                cat_label = HABIT_CATEGORIES.get(habit.get("category", ""), "")
                st.caption(
                    f"{habit['duration_minutes']} min  ·  "
                    f"{cat_label}  ·  "
                    f"Difficulty {difficulty}/5"
                )
                st.write(habit["description"])

                # Show cue/reward in expander
                with st.expander("Show cue & reward"):
                    st.write(f"**When:** {habit.get('cue', '')}")
                    st.write(f"**Reward:** {habit.get('reward', '')}")

            with col_btn:
                if is_done:
                    st.success("✓ Done")
                else:
                    if st.button("Complete", key=f"btn_{habit_id}",
                                 type="primary"):
                        was_new = log_habit_completion(
                            conn, user_id, plan_id, habit_id, current_day
                        )
                        if was_new:
                            st.toast(f"Great job! '{habit['name']}' completed!")
                        st.rerun()

st.divider()

# ── Completion celebration ────────────────────────────────────────────────────
if all_done:
    st.balloons()
    st.success("All habits done today! You're on a roll! 🎉")

    # AI motivational message
    with st.spinner("Your coach has a message for you..."):
        try:
            msg = generate_motivation_message(
                user_name=user_name,
                streak=streak_data["current"],
                goal=goal,
                completed_today=True,
            )
            st.info(f"💬 **Your coach says:** {msg}")
        except Exception:
            st.info("Great work today! Every habit completed is a step forward.")

    # Social share card text
    with st.expander("Share your progress"):
        share_text = (
            f"Day {current_day} done! 🌱 {streak_data['current']}-day streak "
            f"on my habit journey. #AIHabitCoach #SmallHabitsBigLife"
        )
        st.text_area("Copy to share:", share_text, height=80)

    # Advance to next day
    if current_day < total_days:
        if st.button("Mark day complete & advance to next day", type="primary"):
            advance_plan_day(conn, plan_id)
            st.success(f"Great! Moving to Day {current_day + 1}.")
            st.rerun()
    else:
        st.success("You completed the full plan! 🏆")
        st.balloons()

# ── Difficulty adaptation suggestion ─────────────────────────────────────────
suggestion = get_adaptation_suggestion(conn, user_id, plan_id)
if suggestion:
    direction_icon = "💪" if suggestion["direction"] == "harder" else "🤗"
    st.info(f"{direction_icon} **Coach suggestion:** {suggestion['message']}")
    if st.button("Get a new adapted plan"):
        st.page_link("pages/1_onboarding.py", label="Create a new plan →")

"""
pages/1_onboarding.py
---------------------
Step-by-step onboarding: user picks their goal, user type,
available time, and plan duration. Then we call OpenAI to generate
a personalized habit plan and save it to the database.

WHAT HAPPENS HERE:
1. User fills in the form
2. We call generate_habit_plan() from ai_engine.py
3. The returned dict is saved as JSON in the habit_plans table
4. User is redirected to Today's Habits
"""

import streamlit as st
from auth.auth_handler import require_login
from db.queries import save_habit_plan
from core.ai_engine import generate_habit_plan
from utils.constants import GOALS, USER_TYPES, PLAN_TIER_FEATURES

st.set_page_config(page_title="Set Up Your Plan", page_icon="✨")

require_login()

conn = st.session_state["db_conn"]
user_id   = st.session_state["user_id"]
plan_tier = st.session_state.get("plan_tier", "free")

st.title("✨ Create Your Personalized Habit Plan")
st.caption("The AI will design a custom plan based on your answers below.")

# ── Step indicators ───────────────────────────────────────────────────────────
st.progress(0.0, text="Step 1 of 3 — About you")

# ── Form ──────────────────────────────────────────────────────────────────────
with st.form("onboarding_form"):

    st.subheader("Step 1: Your goal")
    goal = st.selectbox(
        "What do you want to improve?",
        options=list(GOALS.keys()),
        format_func=lambda k: GOALS[k],
    )

    st.subheader("Step 2: Your profile")
    user_type = st.selectbox(
        "Which best describes you?",
        options=list(USER_TYPES.keys()),
        format_func=lambda k: USER_TYPES[k],
    )

    col1, col2 = st.columns(2)
    with col1:
        sessions_per_day = st.slider(
            "How many habit sessions per day?",
            min_value=1, max_value=3, value=2,
            help="Each session = 1 habit (5 minutes). Start with 2."
        )
    with col2:
        # Plan duration depends on plan tier
        max_days = PLAN_TIER_FEATURES[plan_tier]["max_plan_days"]
        available_durations = [d for d in [7, 14, 30] if d <= max_days]
        plan_days = st.selectbox(
            "Plan duration",
            options=available_durations,
            index=len(available_durations) - 1,
            format_func=lambda d: f"{d}-day plan",
        )

    if plan_tier == "free" and 30 not in available_durations:
        st.info("Free plan includes 7-day plans. Upgrade to Pro for 14 and 30-day plans.")

    st.subheader("Step 3: Confirm")
    st.write(f"**Goal:** {GOALS[goal]}")
    st.write(f"**Profile:** {USER_TYPES[user_type]}")
    st.write(f"**Plan:** {plan_days} days, {sessions_per_day} habits/day")

    submitted = st.form_submit_button(
        "Generate My Habit Plan ✨",
        type="primary",
        use_container_width=True
    )

# ── Generate plan on submit ───────────────────────────────────────────────────
if submitted:
    with st.spinner("AI is crafting your personalized plan... (this takes 15-30 seconds)"):
        try:
            plan_data = generate_habit_plan(
                goal=goal,
                user_type=user_type,
                plan_days=plan_days,
                sessions_per_day=sessions_per_day,
            )

            plan_id = save_habit_plan(
                conn,
                user_id=user_id,
                goal=goal,
                user_type=user_type,
                plan_data=plan_data,
                total_days=plan_days,
            )

            # Update session state so the rest of the app knows
            st.session_state["goal"]      = goal
            st.session_state["user_type"] = user_type

            st.success(f"Your {plan_days}-day plan is ready!")
            st.balloons()

            # Show a preview
            st.subheader(plan_data.get("plan_title", "Your Plan"))
            st.write(plan_data.get("plan_summary", ""))

            # Show day 1 habits
            phases = plan_data.get("weekly_phases", [])
            if phases:
                day1 = phases[0]["days"][0] if phases[0]["days"] else None
                if day1:
                    st.subheader("Day 1 preview")
                    for h in day1.get("habits", []):
                        with st.container(border=True):
                            st.write(f"**{h['name']}** — {h['duration_minutes']} min")
                            st.caption(h["description"])

            st.page_link("pages/2_today.py",
                         label="Start today's habits →", icon="✅")

        except Exception as e:
            st.error(f"Could not generate plan: {e}")
            st.info("Check that your OPENAI_API_KEY is set in the .env file.")

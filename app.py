"""
app.py
------
Main entry point for AI Personal Habit Coach.
This is what Streamlit runs first: `streamlit run app.py`

WHAT THIS FILE DOES:
1. Sets up the app title and sidebar navigation
2. Shows Login / Register if the user is not logged in
3. Starts the background reminder scheduler
4. Displays a welcome dashboard if the user is logged in
"""

import streamlit as st
from db.queries import get_db_connection
from auth.auth_handler import (
    register_user, login_user_with_credentials,
    is_logged_in, logout_user, is_pro_user
)
from scheduler.reminder_job import start_scheduler

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="AI Habit Coach",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Start background scheduler (once per app lifecycle) ───────────────────────
# Using session state flag so it only starts once, not on every rerun
if "scheduler_started" not in st.session_state:
    start_scheduler()
    st.session_state["scheduler_started"] = True

# ── Database connection (shared via session state) ────────────────────────────
# We store the connection in session_state so all pages can reuse it
if "db_conn" not in st.session_state:
    st.session_state["db_conn"] = get_db_connection()

conn = st.session_state["db_conn"]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🌱 AI Habit Coach")
    st.caption("Small habits. Big life changes.")

    if is_logged_in():
        st.markdown(f"👋 **{st.session_state.get('user_name', 'Friend')}**")
        tier = st.session_state.get("plan_tier", "free")
        if tier == "pro":
            st.success("Pro member")
        elif tier == "family":
            st.success("Family member")
        else:
            st.info("Free plan")

        st.divider()
        st.page_link("pages/2_today.py",    label="Today's Habits",    icon="✅")
        st.page_link("pages/3_progress.py", label="My Progress",       icon="📊")
        st.page_link("pages/4_plan.py",     label="View My Plan",      icon="📋")
        st.page_link("pages/5_coach.py",    label="AI Coach Chat",     icon="💬")
        st.page_link("pages/6_account.py",  label="Account & Settings",icon="⚙️")
        st.divider()

        if st.button("Log out", use_container_width=True):
            logout_user()
            st.rerun()


# ── Main page logic ───────────────────────────────────────────────────────────

if is_logged_in():
    # ── Welcome dashboard ─────────────────────────────────────────────────────
    from db.queries import get_active_plan
    from core.streak_tracker import calculate_streak

    name = st.session_state.get("user_name", "Friend")
    st.title(f"Welcome back, {name}! 👋")

    streak_data  = calculate_streak(conn, st.session_state["user_id"])
    active_plan  = get_active_plan(conn, st.session_state["user_id"])

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current streak",  f"{streak_data['current']} days 🔥")
    col2.metric("Longest streak",  f"{streak_data['longest']} days")
    col3.metric("Total days done", f"{streak_data['total_days']} days")
    if active_plan:
        col4.metric("Plan progress",
                    f"Day {active_plan['current_day']} / {active_plan['total_days']}")
    else:
        col4.metric("Plan", "No active plan")

    st.divider()

    if not active_plan:
        st.info("You don't have an active habit plan yet.")
        st.page_link("pages/1_onboarding.py",
                     label="Create your personalized plan →", icon="✨")
    else:
        st.subheader("What would you like to do today?")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.page_link("pages/2_today.py",
                         label="Complete today's habits", icon="✅")
        with c2:
            st.page_link("pages/3_progress.py",
                         label="View my progress", icon="📊")
        with c3:
            st.page_link("pages/5_coach.py",
                         label="Chat with AI coach", icon="💬")

        st.divider()
        # Quick habit preview
        plan_data   = active_plan["plan_data"]
        current_day = active_plan["current_day"]
        phases      = plan_data.get("weekly_phases", [])

        today_habits = []
        for phase in phases:
            for day_obj in phase.get("days", []):
                if day_obj["day"] == current_day:
                    today_habits = day_obj.get("habits", [])
                    break

        if today_habits:
            st.subheader(f"Today — Day {current_day} habits")
            for h in today_habits:
                st.write(f"**{h['name']}** · {h['duration_minutes']} min · {h['time_of_day']}")

else:
    # ── Login / Register ──────────────────────────────────────────────────────
    st.title("🌱 AI Personal Habit Coach")
    st.subheader("Build life-changing habits in just 5 minutes a day")

    col_info, col_auth = st.columns([1, 1])

    with col_info:
        st.markdown("""
        **What you get:**
        - AI-personalized 30-day habit plans
        - Habit streak tracking
        - Daily reminders
        - Progress heatmap & analytics
        - AI life coach chat (Pro)
        """)
        st.markdown("""
        **Goals you can work on:**
        - Improve health & energy
        - Increase productivity
        - Reduce stress & anxiety
        - Improve focus
        - Family wellness
        - Healthy pregnancy routines
        """)

    with col_auth:
        tab_login, tab_register = st.tabs(["Log in", "Create account"])

        with tab_login:
            with st.form("login_form"):
                email    = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Log in", use_container_width=True)

            if submitted:
                ok, msg = login_user_with_credentials(conn, email, password)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        with tab_register:
            with st.form("register_form"):
                name      = st.text_input("Your name")
                email_r   = st.text_input("Email")
                password_r= st.text_input("Password (min 6 chars)", type="password")
                submitted_r = st.form_submit_button("Create account",
                                                     use_container_width=True)

            if submitted_r:
                ok, msg = register_user(conn, email_r, password_r, name)
                if ok:
                    st.success(msg)
                    st.page_link("pages/1_onboarding.py",
                                 label="Set up your habit plan →")
                    st.rerun()
                else:
                    st.error(msg)

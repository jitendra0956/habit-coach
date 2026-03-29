"""
pages/5_coach.py
-----------------
AI Life Coach chat page — a conversational assistant that knows
the user's full habit plan and progress.

HOW THE CHAT WORKS:
1. Chat history is stored in the `chat_history` database table.
2. On each message, we load the last 10 messages from the DB.
3. We pass those + the user's plan context to OpenAI.
4. The response is saved back to the DB and displayed.

This means the coach 'remembers' the conversation across sessions!
"""

import streamlit as st
from auth.auth_handler import require_login, is_pro_user
from db.queries import (
    get_active_plan, get_chat_history,
    save_chat_message, clear_chat_history
)
from core.ai_engine import coach_chat_response
from core.streak_tracker import calculate_streak

st.set_page_config(page_title="AI Coach Chat", page_icon="💬", layout="wide")
require_login()

conn      = st.session_state["db_conn"]
user_id   = st.session_state["user_id"]
user_name = st.session_state.get("user_name", "Friend")
goal      = st.session_state.get("goal", "health")
user_type = st.session_state.get("user_type", "other")

st.title("💬 AI Coach Chat")
st.caption("Chat with Sage, your personal AI habit coach.")

# ── Pro gate ──────────────────────────────────────────────────────────────────
if not is_pro_user():
    st.warning("AI Coach Chat is a Pro feature.")
    st.markdown("""
    **Upgrade to Pro** to unlock:
    - Unlimited conversations with your AI coach
    - Personalised advice based on your plan & progress
    - Habit adjustment recommendations
    - Motivational support when you're struggling
    """)
    st.page_link("pages/6_account.py", label="Upgrade to Pro →", icon="⭐")
    st.stop()

# ── Load plan context ─────────────────────────────────────────────────────────
active_plan  = get_active_plan(conn, user_id)
streak_data  = calculate_streak(conn, user_id)

plan_context = {
    "goal":        goal,
    "user_type":   user_type,
    "streak":      streak_data["current"],
    "current_day": active_plan["current_day"] if active_plan else 1,
    "total_days":  active_plan["total_days"]  if active_plan else 30,
    "plan_title":  active_plan["plan_data"].get("plan_title", "") if active_plan else "",
}

# ── Suggested questions ───────────────────────────────────────────────────────
st.subheader("Ask your coach anything")

quick_questions = [
    "Why is this habit good for me?",
    "I missed 2 days. Should I restart?",
    "What should I focus on this week?",
    "How do I make this habit stick?",
    "I'm feeling unmotivated. Help!",
]

cols = st.columns(len(quick_questions))
for i, q in enumerate(quick_questions):
    with cols[i]:
        if st.button(q, key=f"quick_{i}", use_container_width=True):
            st.session_state["pending_message"] = q

st.divider()

# ── Chat history display ──────────────────────────────────────────────────────
chat_history = get_chat_history(conn, user_id, limit=40)

# Display existing messages
for msg in chat_history:
    with st.chat_message(msg["role"],
                          avatar="🌱" if msg["role"] == "assistant" else "👤"):
        st.write(msg["content"])

# ── Handle pending quick-question ────────────────────────────────────────────
if "pending_message" in st.session_state:
    pending = st.session_state.pop("pending_message")

    with st.chat_message("user", avatar="👤"):
        st.write(pending)

    save_chat_message(conn, user_id, "user", pending)

    with st.chat_message("assistant", avatar="🌱"):
        with st.spinner("Sage is thinking..."):
            try:
                response = coach_chat_response(
                    user_message=pending,
                    plan_context=plan_context,
                    chat_history=get_chat_history(conn, user_id, limit=10),
                )
            except Exception as e:
                response = (
                    "I'm having trouble connecting right now. "
                    "Please check your OpenAI API key and try again."
                )
        st.write(response)

    save_chat_message(conn, user_id, "assistant", response)
    st.rerun()

# ── Chat input ────────────────────────────────────────────────────────────────
user_input = st.chat_input("Ask Sage anything about your habits...")

if user_input:
    with st.chat_message("user", avatar="👤"):
        st.write(user_input)

    save_chat_message(conn, user_id, "user", user_input)

    with st.chat_message("assistant", avatar="🌱"):
        with st.spinner("Sage is thinking..."):
            try:
                response = coach_chat_response(
                    user_message=user_input,
                    plan_context=plan_context,
                    chat_history=get_chat_history(conn, user_id, limit=10),
                )
            except Exception as e:
                response = (
                    "I'm having trouble connecting right now. "
                    "Please check your OpenAI API key in your .env file."
                )
        st.write(response)

    save_chat_message(conn, user_id, "assistant", response)
    st.rerun()

# ── Clear history button ──────────────────────────────────────────────────────
if chat_history:
    st.divider()
    if st.button("Clear chat history", type="secondary"):
        clear_chat_history(conn, user_id)
        st.rerun()

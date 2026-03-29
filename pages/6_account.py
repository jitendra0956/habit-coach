"""
pages/6_account.py
-------------------
Account settings page:
- View and update profile (name, goal, user type, reminder time, timezone)
- View current plan tier
- Upgrade to Pro (Stripe integration)
- Danger zone: delete account

HOW STRIPE WORKS (simplified):
- We create a Stripe Checkout Session (a hosted payment page).
- User is redirected to Stripe to pay.
- After payment, Stripe sends a webhook to our server.
- The webhook handler upgrades the user's plan_tier in the database.

For the MVP without Stripe, upgrading is done manually by changing
plan_tier in the database directly (instructions in README).
"""

import streamlit as st
import pytz
from auth.auth_handler import require_login, logout_user
from db.queries import update_user_profile, update_user_plan_tier
from utils.constants import GOALS, USER_TYPES, PRICING

st.set_page_config(page_title="Account & Settings", page_icon="⚙️")
require_login()

conn      = st.session_state["db_conn"]
user_id   = st.session_state["user_id"]
plan_tier = st.session_state.get("plan_tier", "free")

st.title("⚙️ Account & Settings")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_profile, tab_billing, tab_reminders = st.tabs(
    ["Profile", "Plan & Billing", "Reminders"]
)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: Profile
# ═══════════════════════════════════════════════════════════════════════════════
with tab_profile:
    st.subheader("Your profile")

    with st.form("profile_form"):
        name = st.text_input(
            "Name",
            value=st.session_state.get("user_name", "")
        )
        goal = st.selectbox(
            "Primary goal",
            options=list(GOALS.keys()),
            format_func=lambda k: GOALS[k],
            index=list(GOALS.keys()).index(
                st.session_state.get("goal", "health")
            ),
        )
        user_type = st.selectbox(
            "Your profile type",
            options=list(USER_TYPES.keys()),
            format_func=lambda k: USER_TYPES[k],
            index=list(USER_TYPES.keys()).index(
                st.session_state.get("user_type", "other")
            ),
        )

        save = st.form_submit_button("Save changes", type="primary")

    if save:
        # We'll update reminder settings below; use defaults for now
        update_user_profile(
            conn, user_id,
            name=name, goal=goal, user_type=user_type,
            timezone=st.session_state.get("user_timezone", "UTC"),
            reminder_hour=8, reminder_min=0
        )
        st.session_state["user_name"] = name
        st.session_state["goal"]      = goal
        st.session_state["user_type"] = user_type
        st.success("Profile updated!")

    st.divider()
    st.write(f"**Email:** {st.session_state.get('user_email', '')}")
    st.caption("Email cannot be changed after registration.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: Plan & Billing
# ═══════════════════════════════════════════════════════════════════════════════
with tab_billing:
    st.subheader("Your current plan")

    tier_labels = {"free": "Free", "pro": "Pro", "family": "Family"}
    tier_label  = tier_labels.get(plan_tier, plan_tier.title())

    if plan_tier == "free":
        st.info("You are on the **Free** plan.")

        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                st.markdown("### Pro — $9/month")
                st.write("""
                ✅ Unlimited 7, 14, 30-day plans  
                ✅ AI Coach chat  
                ✅ Progress heatmap  
                ✅ PDF export  
                ✅ Social sharing cards  
                """)
                if st.button("Upgrade to Pro", type="primary",
                             use_container_width=True):
                    _handle_upgrade(conn, user_id, "pro")

        with col2:
            with st.container(border=True):
                st.markdown("### Family — $19/month")
                st.write("""
                ✅ Up to 5 family accounts  
                ✅ Parent dashboard  
                ✅ Kids-safe habits  
                ✅ All Pro features  
                """)
                if st.button("Upgrade to Family", type="primary",
                             use_container_width=True):
                    _handle_upgrade(conn, user_id, "family")

    elif plan_tier == "pro":
        st.success("You are on the **Pro** plan.")
        st.write("All premium features are unlocked.")

        if st.button("Cancel subscription", type="secondary"):
            st.warning(
                "To cancel, contact support@habitcoach.app "
                "or manage via your Stripe customer portal."
            )

    elif plan_tier == "family":
        st.success("You are on the **Family** plan.")
        st.write("All premium features are unlocked for up to 5 accounts.")

    # ── DEV NOTE: Manual upgrade for testing ─────────────────────────────────
    st.divider()
    with st.expander("Developer: manually change plan tier (for testing)"):
        st.caption(
            "In production this is handled by Stripe webhooks. "
            "Use this only during local development."
        )
        new_tier = st.selectbox("Set plan tier", ["free", "pro", "family"])
        if st.button("Apply tier change"):
            update_user_plan_tier(conn, user_id, new_tier)
            st.session_state["plan_tier"] = new_tier
            st.success(f"Plan changed to {new_tier}. Reload the page.")
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: Reminders
# ═══════════════════════════════════════════════════════════════════════════════
with tab_reminders:
    st.subheader("Daily reminder settings")
    st.caption(
        "We'll send you an email reminder if you haven't done "
        "your habits by your chosen time."
    )

    # Common timezones
    common_timezones = [
        "UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
        "Europe/London", "Europe/Paris", "Europe/Berlin",
        "Asia/Kolkata", "Asia/Dubai", "Asia/Singapore",
        "Australia/Sydney", "Pacific/Auckland",
    ]

    with st.form("reminder_form"):
        timezone = st.selectbox(
            "Your timezone",
            options=common_timezones,
            index=0,
        )
        reminder_hour = st.slider(
            "Reminder hour (24h format)",
            min_value=6, max_value=22, value=8,
            help="8 = 8:00 AM, 20 = 8:00 PM"
        )
        st.caption(
            f"You'll get a reminder at "
            f"{'12 PM' if reminder_hour == 12 else f'{reminder_hour % 12 or 12} {'AM' if reminder_hour < 12 else 'PM'}'} "
            f"{timezone}"
        )

        save_reminder = st.form_submit_button("Save reminder settings",
                                               type="primary")

    if save_reminder:
        update_user_profile(
            conn, user_id,
            name=st.session_state.get("user_name", ""),
            goal=st.session_state.get("goal", "health"),
            user_type=st.session_state.get("user_type", "other"),
            timezone=timezone,
            reminder_hour=reminder_hour,
            reminder_min=0
        )
        st.session_state["user_timezone"] = timezone
        st.success("Reminder settings saved!")


# ── Helper: upgrade handler ───────────────────────────────────────────────────
def _handle_upgrade(conn, user_id: int, tier: str):
    """
    In a real app this would create a Stripe Checkout Session.
    For the MVP, we provide instructions.
    """
    from config import STRIPE_SECRET_KEY
    if not STRIPE_SECRET_KEY:
        # No Stripe configured — show manual instructions
        st.info(
            f"To upgrade to {tier.title()}, add your Stripe keys to .env "
            "and restart the app. See README for setup instructions."
        )
        return

    try:
        import stripe
        from config import (STRIPE_PRO_PRICE_ID, STRIPE_FAMILY_PRICE_ID)
        stripe.api_key = STRIPE_SECRET_KEY

        price_id = STRIPE_PRO_PRICE_ID if tier == "pro" else STRIPE_FAMILY_PRICE_ID
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url="http://localhost:8501/6_account?upgraded=1",
            cancel_url="http://localhost:8501/6_account",
            metadata={"user_id": str(user_id), "tier": tier},
        )
        st.markdown(f"[Complete payment →]({session.url})")
    except Exception as e:
        st.error(f"Stripe error: {e}")

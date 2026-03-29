"""
auth/auth_handler.py
--------------------
Handles user registration, login, and Streamlit session management.

HOW PASSWORDS WORK:
- We NEVER store plain-text passwords.
- bcrypt.hashpw() turns "mypassword" into a scrambled string like "$2b$12$..."
- bcrypt.checkpw() verifies a password against the stored hash.
- Even if the database leaks, passwords are safe.
"""

import bcrypt
import streamlit as st
from db.queries import create_user, get_user_by_email, get_user_by_id


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Turn a plain-text password into a bcrypt hash string."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if the plain password matches the stored hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── Register / Login ──────────────────────────────────────────────────────────

def register_user(conn, email: str, password: str, name: str) -> tuple[bool, str]:
    """
    Create a new user account.
    Returns (success: bool, message: str).
    """
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if not email or "@" not in email:
        return False, "Please enter a valid email address."
    if not name.strip():
        return False, "Please enter your name."

    # Check if email already registered
    if get_user_by_email(conn, email):
        return False, "An account with that email already exists."

    hashed = hash_password(password)
    user_id = create_user(conn, email, hashed, name)
    login_user(conn, user_id)
    return True, "Account created! Welcome."


def login_user_with_credentials(conn, email: str,
                                  password: str) -> tuple[bool, str]:
    """
    Verify credentials and log the user in via session state.
    Returns (success: bool, message: str).
    """
    user = get_user_by_email(conn, email)
    if not user:
        return False, "No account found with that email."
    if not verify_password(password, user["password_hash"]):
        return False, "Incorrect password."

    login_user(conn, user["id"])
    return True, f"Welcome back, {user['name'] or email}!"


def login_user(conn, user_id: int):
    """
    Store user info in st.session_state — this is how Streamlit
    'remembers' a logged-in user across page navigations.
    """
    user = get_user_by_id(conn, user_id)
    st.session_state["user_id"]   = user["id"]
    st.session_state["user_name"] = user["name"] or user["email"].split("@")[0]
    st.session_state["user_email"]= user["email"]
    st.session_state["goal"]      = user["goal"]
    st.session_state["user_type"] = user["user_type"]
    st.session_state["plan_tier"] = user["plan_tier"]


def logout_user():
    """Clear all session state — effectively logs the user out."""
    for key in ["user_id", "user_name", "user_email", "goal",
                "user_type", "plan_tier"]:
        st.session_state.pop(key, None)


def is_logged_in() -> bool:
    return "user_id" in st.session_state


def require_login():
    """
    Call at the top of any page that needs authentication.
    Stops the page and shows the login prompt if not logged in.
    """
    if not is_logged_in():
        st.warning("Please log in to continue.")
        st.page_link("app.py", label="Go to login page")
        st.stop()


def is_pro_user() -> bool:
    return st.session_state.get("plan_tier") in ("pro", "family")

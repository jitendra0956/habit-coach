"""
payments/stripe_handler.py
---------------------------
Handles incoming Stripe webhook events.

WHAT IS A WEBHOOK?
When a user pays via Stripe, Stripe sends a POST request to your server
with the payment details. This code listens for that and upgrades the user.

HOW TO SET UP STRIPE WEBHOOKS:
1. Sign up at stripe.com (free)
2. Create products: "Pro Plan - $9/month" and "Family Plan - $19/month"
3. Copy the Price IDs to your .env file
4. In Stripe Dashboard → Developers → Webhooks
5. Add endpoint: https://yourdomain.com/webhook/stripe
6. Select events: checkout.session.completed, customer.subscription.deleted
7. Copy the webhook signing secret to .env as STRIPE_WEBHOOK_SECRET

NOTE: For local testing, use the Stripe CLI:
  stripe listen --forward-to localhost:8501/webhook/stripe

This webhook handler is designed to be called from a FastAPI endpoint.
For the MVP with Streamlit only, use the manual tier change in Account settings.
"""

import stripe
from config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET

stripe.api_key = STRIPE_SECRET_KEY


def handle_stripe_webhook(payload: bytes, sig_header: str) -> dict:
    """
    Verify and process a Stripe webhook event.

    Returns {"success": True, "action": "..."} or raises an exception.

    HOW STRIPE WEBHOOK VERIFICATION WORKS:
    - Stripe signs each webhook payload with your STRIPE_WEBHOOK_SECRET.
    - construct_event() verifies the signature — this prevents fake webhooks.
    - If the signature doesn't match, it raises a SignatureVerificationError.
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise ValueError("Invalid Stripe signature — possible fake webhook")

    # ── Handle specific event types ───────────────────────────────────────────
    if event["type"] == "checkout.session.completed":
        return _handle_checkout_completed(event["data"]["object"])

    if event["type"] == "customer.subscription.deleted":
        return _handle_subscription_cancelled(event["data"]["object"])

    # Unhandled event type — safe to ignore
    return {"success": True, "action": "ignored", "event": event["type"]}


def _handle_checkout_completed(session: dict) -> dict:
    """
    A user just paid successfully. Upgrade their plan tier in the database.
    The user_id and tier are passed in the session metadata.
    """
    from db.queries import get_db_connection, update_user_plan_tier

    metadata = session.get("metadata", {})
    user_id  = metadata.get("user_id")
    tier     = metadata.get("tier", "pro")

    if not user_id:
        return {"success": False, "error": "No user_id in metadata"}

    conn = get_db_connection()
    try:
        update_user_plan_tier(conn, int(user_id), tier)
        print(f"[Stripe] Upgraded user {user_id} to {tier}")
        return {"success": True, "action": f"upgraded_user_{user_id}_to_{tier}"}
    finally:
        conn.close()


def _handle_subscription_cancelled(subscription: dict) -> dict:
    """
    A user cancelled their subscription. Downgrade them to free.
    """
    from db.queries import get_db_connection
    import sqlite3

    stripe_customer_id = subscription.get("customer")
    if not stripe_customer_id:
        return {"success": False, "error": "No customer ID"}

    conn = get_db_connection()
    try:
        # Find user by Stripe customer ID
        row = conn.execute(
            "SELECT id FROM users WHERE stripe_cust_id = ?",
            (stripe_customer_id,)
        ).fetchone()

        if row:
            conn.execute(
                "UPDATE users SET plan_tier = 'free' WHERE id = ?", (row["id"],)
            )
            conn.commit()
            print(f"[Stripe] Downgraded user {row['id']} to free")
            return {"success": True, "action": f"downgraded_user_{row['id']}"}

        return {"success": False, "error": "User not found"}
    finally:
        conn.close()

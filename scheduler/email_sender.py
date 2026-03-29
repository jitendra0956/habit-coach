"""
scheduler/email_sender.py
--------------------------
Sends HTML email reminders via SMTP (works with Gmail, SendGrid, etc.)

TO USE WITH GMAIL:
1. Enable 2-factor authentication on your Gmail account.
2. Go to Google Account → Security → App Passwords.
3. Create an App Password for "Mail".
4. Put that 16-char password in .env as SMTP_PASSWORD.
5. Set SMTP_USER to your Gmail address.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD


def send_reminder_email(
    to_email: str,
    name: str,
    streak: int,
    goal: str,
    habits_today: list[str] = None,
):
    """
    Send a daily reminder email to a user.

    Args:
        to_email:     recipient email
        name:         user's first name
        streak:       current streak count (for motivational subject line)
        goal:         the user's goal key (e.g. "health")
        habits_today: list of today's habit names (optional, shown in email)
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        # Email not configured — skip silently
        print(f"[Email] Would have sent reminder to {to_email} (SMTP not configured)")
        return

    # ── Subject line — escalate urgency with streak length ────────────────────
    if streak >= 14:
        subject = f"Don't break your {streak}-day streak! Your habits are waiting."
    elif streak >= 7:
        subject = f"Your {streak}-day streak needs you today!"
    elif streak >= 3:
        subject = f"Keep going — {streak} days and counting."
    else:
        subject = "Your daily habit reminder is here."

    # ── Build habits list for email body ──────────────────────────────────────
    habits_html = ""
    if habits_today:
        items = "".join(f"<li>{h}</li>" for h in habits_today[:3])
        habits_html = f"<p><strong>Today's habits:</strong></p><ul>{items}</ul>"

    # ── HTML email body ───────────────────────────────────────────────────────
    html_body = f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 500px; margin: auto; padding: 20px;">
      <h2 style="color: #1a1a2e;">Hi {name},</h2>
      <p>Your daily habits are ready and waiting for you.</p>
      {habits_html}
      <p style="font-size: 24px; text-align: center; margin: 20px 0;">
        🔥 {streak}-day streak
      </p>
      <p>Just 5 minutes today keeps your streak alive and your goals moving forward.</p>
      <p style="text-align: center; margin: 30px 0;">
        <a href="http://localhost:8501"
           style="background: #6c63ff; color: white; padding: 12px 24px;
                  border-radius: 6px; text-decoration: none; font-weight: bold;">
          Complete Today's Habits
        </a>
      </p>
      <p style="color: #999; font-size: 12px;">
        You're receiving this because you set up a daily reminder.
      </p>
    </body></html>
    """

    # ── Send the email ────────────────────────────────────────────────────────
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SMTP_USER
    msg["To"]      = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        print(f"[Email] Reminder sent to {to_email}")
    except Exception as e:
        print(f"[Email] Failed to send to {to_email}: {e}")

# 🌱 AI Personal Habit Coach

A full-stack AI-powered habit coaching app built with Python + Streamlit + OpenAI.

---

## What This App Does

Users pick a goal (health, productivity, stress, focus, family, pregnancy), and the AI
generates a personalised 7, 14, or 30-day micro-habit plan — one habit at a time,
5 minutes per session. The app tracks streaks, shows progress charts, sends email
reminders, and includes an AI life coach chat assistant (Pro).

---

## Project Structure (Every File Explained)

```
habit_coach/
│
├── app.py                    ← ENTRY POINT: Login/register + home dashboard
├── config.py                 ← All environment variables in one place
├── requirements.txt          ← Python packages to install
├── .env.example              ← Copy to .env and fill in your API keys
├── .streamlit/
│   └── config.toml           ← Streamlit theme and server settings
│
├── pages/                    ← Each file = one page in the sidebar
│   ├── 1_onboarding.py       ← Step-by-step plan setup + AI generation
│   ├── 2_today.py            ← Daily habit check-off (main usage page)
│   ├── 3_progress.py         ← Charts, streaks, activity heatmap
│   ├── 4_plan.py             ← Browse the full 30-day plan
│   ├── 5_coach.py            ← AI chat coach (Pro feature)
│   └── 6_account.py          ← Profile settings, billing, reminders
│
├── core/                     ← Business logic (no UI code here)
│   ├── ai_engine.py          ← ALL OpenAI calls: plan gen, motivation, chat
│   ├── streak_tracker.py     ← Streak calculation from completion logs
│   └── difficulty_adapter.py ← Suggests easier/harder habits based on rate
│
├── db/                       ← Database layer
│   ├── schema.sql            ← SQLite table definitions (runs once)
│   └── queries.py            ← All database read/write functions
│
├── auth/
│   └── auth_handler.py       ← Register, login, bcrypt password hashing
│
├── scheduler/
│   ├── reminder_job.py       ← APScheduler background job (hourly check)
│   └── email_sender.py       ← SMTP email with HTML templates
│
├── payments/
│   └── stripe_handler.py     ← Stripe webhook: upgrade user on payment
│
└── utils/
    ├── constants.py          ← Goals, user types, categories (static data)
    └── social_card.py        ← PIL image generator for sharing cards
```

---

## Setup Guide (Step by Step)

### Step 1: Install Python

Make sure you have Python 3.11 or newer.

```bash
python --version    # Should show 3.11 or higher
```

If not, download from https://python.org/downloads

---

### Step 2: Download the project

If you have Git:
```bash
git clone https://github.com/yourusername/habit_coach.git
cd habit_coach
```

Or just unzip the downloaded folder, then open a terminal inside it.

---

### Step 3: Create a virtual environment

A virtual environment keeps this project's packages separate from other projects.

```bash
# Create the virtual environment
python -m venv venv

# Activate it — IMPORTANT: do this every time you work on the project
# On Mac/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# You'll see (venv) in your terminal prompt — that means it's active
```

---

### Step 4: Install dependencies

```bash
pip install -r requirements.txt
```

This installs: Streamlit, OpenAI, APScheduler, bcrypt, Stripe, Altair, Pandas, Pillow, pytz.

---

### Step 5: Get your OpenAI API key

1. Go to https://platform.openai.com
2. Sign up / log in
3. Click your profile → View API Keys
4. Click "Create new secret key"
5. Copy the key (starts with sk-)

**Cost estimate:** GPT-4o costs about $0.005 per habit plan generation.
For testing, $5 credit will last you hundreds of plans.

---

### Step 6: Create your .env file

```bash
# Copy the example file
cp .env.example .env

# Now open .env in any text editor and fill in your keys
```

Minimum required for the MVP to work:
```
OPENAI_API_KEY=sk-your-actual-key-here
APP_SECRET_KEY=any-random-string-at-least-32-characters
```

---

### Step 7: Run the app!

```bash
streamlit run app.py
```

Your browser will open automatically at http://localhost:8501

---

## How to Use the App

1. **Register** — Create an account with your email and password
2. **Set up your plan** — Go to "Create Your Plan" (page 1), pick your goal
3. **Wait 20-30 seconds** — The AI generates your personalized plan
4. **Complete habits daily** — Go to "Today's Habits" every day
5. **Watch your streak grow** — Check "My Progress" for charts

---

## Optional Setup: Email Reminders

To receive daily email reminders:

### Using Gmail:
1. Enable 2-factor authentication on your Google account
2. Go to: Google Account → Security → 2-Step Verification → App Passwords
3. Click "Add app password" → name it "Habit Coach"
4. Copy the 16-character password
5. Add to your `.env`:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
```

---

## Optional Setup: Stripe Payments

For accepting real payments (skip this for MVP testing):

1. Create a Stripe account at https://stripe.com (free)
2. In Stripe Dashboard → Products → Create product "Pro Plan"
3. Set price to $9/month (recurring)
4. Copy the Price ID (starts with price_)
5. Go to Developers → API keys → copy Secret Key
6. Add to your `.env`:
```
STRIPE_SECRET_KEY=sk_test_your-key
STRIPE_PRO_PRICE_ID=price_your-price-id
STRIPE_WEBHOOK_SECRET=whsec_your-secret
```

**For testing without Stripe:**
- Go to Account & Settings → "Developer: manually change plan tier"
- Change to "pro" to test all Pro features

---

## Upgrading the Database

The database is created automatically when you first run the app.
The file `habit_coach.db` will appear in your project folder.

To inspect the database:
```bash
# Install sqlite3 browser: https://sqlitebrowser.org
# Or use the command line:
sqlite3 habit_coach.db
.tables
SELECT * FROM users;
.quit
```

---

## Deploying to the Internet

### Option 1: Streamlit Community Cloud (Free, easiest)

1. Push your code to GitHub (make sure .env is in .gitignore!)
2. Go to https://share.streamlit.io
3. Connect your GitHub repo
4. Set environment variables (OPENAI_API_KEY etc.) in the Streamlit secrets panel
5. Click Deploy — live in ~2 minutes at yourapp.streamlit.app

### Option 2: Railway.app ($5-20/month, always-on)

1. Go to https://railway.app
2. Connect GitHub repo
3. Add environment variables in the Railway dashboard
4. Railway auto-detects Python and deploys
5. Add a custom domain in Railway settings

**For production, change the DB_PATH to a persistent volume path.**

---

## How to Make Money

### Testing payments locally:
1. Install Stripe CLI: https://stripe.com/docs/stripe-cli
2. Run: `stripe listen --forward-to localhost:8501`
3. Use test card: 4242 4242 4242 4242

### Pricing strategy:
- Free: 7-day plans, basic tracking (hook users)
- Pro ($9/mo): 30-day plans, AI coach, heatmap, PDF export
- Family ($19/mo): 5 accounts, parent dashboard
- Corporate ($6/seat/mo): team admin, company goals

---

## Common Issues & Fixes

**"OpenAI API key not found"**
→ Make sure `.env` exists and has `OPENAI_API_KEY=sk-...`
→ Restart the Streamlit app after editing .env

**"No module named 'streamlit'"**
→ Make sure your virtual environment is activated: `source venv/bin/activate`
→ Run `pip install -r requirements.txt`

**"Database is locked"**
→ SQLite can't handle many concurrent users. At 100+ users, migrate to PostgreSQL.
→ For now, restart the app.

**Plan generation takes too long**
→ GPT-4o can be slow for 30-day plans. Normal time: 15-40 seconds.
→ To speed up: use gpt-4o-mini in config.py (cheaper but slightly lower quality)

**Email reminders not arriving**
→ Check spam folder
→ Make sure SMTP_PASSWORD is an App Password, not your Gmail login password

---

## How the AI Works (Plain English)

1. You fill out the onboarding form (goal + user type + days)
2. `core/ai_engine.py` builds a detailed prompt describing your profile
3. That prompt is sent to OpenAI's GPT-4o model
4. GPT-4o returns a JSON object with your full plan (weeks, days, habits)
5. That JSON is saved to the `habit_plans` table in SQLite
6. When you view today's habits, we parse the JSON and show day N's habits
7. Each "Complete" click writes a row to `daily_logs`
8. The streak tracker counts consecutive dates with at least one completion

---

## Architecture Diagram

```
User Browser
    │
    ▼
Streamlit UI (app.py + pages/)
    │
    ├── auth/auth_handler.py    ← Login/register (bcrypt)
    ├── core/ai_engine.py       ← OpenAI GPT-4o
    ├── core/streak_tracker.py  ← Completion analysis
    ├── db/queries.py           ← SQLite reads/writes
    └── scheduler/              ← Background email reminders
```

---

## Roadmap

**Week 1 (MVP):** Plan generation + habit check-off + auth
**Week 2:** Streaks + reminders + deploy online
**Week 3:** Stripe payments + Pro features gating
**Month 2:** Mobile PWA + social sharing + corporate beta
**Month 6:** FastAPI backend + React frontend + mobile app

---

## Questions?

The code is heavily commented — every function explains what it does and why.
Start with `app.py`, then follow the imports to understand each layer.

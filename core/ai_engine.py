"""
core/ai_engine.py
-----------------
Every call to OpenAI lives here. Nothing else imports openai directly.

WHY ONE FILE FOR ALL AI:
- Easy to swap the model (gpt-4o → gpt-4o-mini) in one place
- Easy to add caching later
- Easy to test by mocking this module

HOW OPENAI WORKS (plain English):
- We send a list of "messages": [{"role": "system", ...}, {"role": "user", ...}]
- "system" sets the AI's persona and rules
- "user" is what the user (or our code) is asking
- response_format={"type": "json_object"} forces the AI to always return valid JSON
"""

import json
import random
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL
from utils.constants import COMPLETION_QUOTES

# Initialise the OpenAI client once (reused across all calls)
client = OpenAI(api_key=OPENAI_API_KEY)

# ── Goal & user type descriptions (fed into prompts) ─────────────────────────

GOAL_DESCRIPTIONS = {
    "health":       "improve physical health, energy levels, and body wellness through gentle daily movement",
    "productivity": "increase daily output, sharpen focus, manage tasks better, and reduce procrastination",
    "stress":       "reduce anxiety and stress, build a calmer mind, and develop emotional resilience",
    "focus":        "sharpen concentration, reduce digital distractions, and build deep-work capacity",
    "children":     "build positive, fun daily habits for children in a safe, age-appropriate, playful way",
    "pregnancy":    "support a healthy, comfortable pregnancy with gentle, evidence-based daily routines",
    "family":       "build wellness routines that the whole family can do together and enjoy",
}

USER_TYPE_CONTEXT = {
    "developer":  "spends 8+ hours at a desk; eye strain, posture, and sedentary habits are key issues",
    "student":    "needs focus, memory, and study habits; has flexible time but prone to procrastination",
    "parent":     "extremely time-poor; habits must be under 5 minutes and family-compatible",
    "pregnant":   "ALL habits MUST be pregnancy-safe; avoid any intense exercise, jumping, or lying flat",
    "elderly":    "habits must be gentle, low-impact, balance-safe; avoid anything that risks falls",
    "freelancer": "irregular schedule; habits need to anchor the day and build self-discipline",
    "office":     "corporate setting; habits must be discreet, desk-friendly, no gym equipment",
    "gamer":      "sedentary, often slouching; needs posture, eye, and movement breaks",
    "child":      "must be playful, fun, simple, and reward-focused; 2-3 minutes max per habit",
    "housewife":  "home-based routine; habits can be integrated into household tasks",
    "other":      "general adult with standard fitness level and typical daily routine",
}


# ── 1. Generate a full habit plan ─────────────────────────────────────────────

def generate_habit_plan(
    goal: str,
    user_type: str,
    plan_days: int,
    sessions_per_day: int = 2
) -> dict:
    """
    Generate a complete N-day personalized habit plan.

    Returns a dict with this structure:
    {
        "plan_title": "...",
        "plan_summary": "...",
        "weekly_phases": [
            {
                "week": 1,
                "theme": "Foundation",
                "days": [
                    {
                        "day": 1,
                        "habits": [
                            {
                                "id": "h_001",
                                "name": "...",
                                "description": "...",
                                "duration_minutes": 5,
                                "time_of_day": "morning",
                                "category": "health",
                                "difficulty": 1,
                                "cue": "...",
                                "reward": "..."
                            }
                        ]
                    }
                ]
            }
        ],
        "success_tips": ["...", "...", "..."]
    }
    """

    system_prompt = (
        "You are an expert habit coach and behavioral psychologist. "
        "You design evidence-based micro-habit plans grounded in BJ Fogg's "
        "Tiny Habits and James Clear's Atomic Habits frameworks. "
        "Every habit you create: (1) takes 5 minutes or less, "
        "(2) is specific enough that the user knows exactly what to do, "
        "(3) includes a clear environmental cue and emotional reward. "
        "ALWAYS respond with valid JSON only — no prose, no markdown fences."
    )

    weeks = max(1, plan_days // 7)
    user_prompt = f"""Create a {plan_days}-day habit plan.

USER PROFILE:
- Goal: {GOAL_DESCRIPTIONS.get(goal, goal)}
- User type: {USER_TYPE_CONTEXT.get(user_type, user_type)}
- Sessions per day: {sessions_per_day}
- Plan weeks: {weeks}

WEEKLY DIFFICULTY PROGRESSION:
- Week 1: Very easy foundation habits (difficulty 1/5) — build confidence
- Week 2: Building momentum (difficulty 2/5) — add slight challenge
- Week 3: Deepening practice (difficulty 3/5) — integrate habits
- Week 4+: Integration and mastery (difficulty 4/5) — make it automatic

Return this EXACT JSON (fill in all {plan_days} days, {sessions_per_day} habits per day):
{{
  "plan_title": "30-Day [Goal] Transformation",
  "plan_summary": "2-3 sentences explaining what this plan will achieve",
  "weekly_phases": [
    {{
      "week": 1,
      "theme": "Short theme name e.g. Foundation Week",
      "days": [
        {{
          "day": 1,
          "habits": [
            {{
              "id": "h_d01_01",
              "name": "Short habit name (3-5 words)",
              "description": "Exactly what to do — specific actions",
              "duration_minutes": 5,
              "time_of_day": "morning",
              "category": "health",
              "difficulty": 1,
              "cue": "Do this habit immediately after [specific trigger]",
              "reward": "After completing, notice [specific positive feeling]"
            }}
          ]
        }}
      ]
    }}
  ],
  "success_tips": [
    "Practical tip 1",
    "Practical tip 2",
    "Practical tip 3"
  ]
}}"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=4000,
    )

    return json.loads(response.choices[0].message.content)


# ── 2. Daily motivational message ─────────────────────────────────────────────

def generate_motivation_message(
    user_name: str,
    streak: int,
    goal: str,
    completed_today: bool
) -> str:
    """
    Returns a short, warm, personalised motivational message (2-3 sentences).
    Uses a random quote as a fallback if the API key isn't set.
    """
    if not OPENAI_API_KEY:
        return random.choice(COMPLETION_QUOTES)

    status = "just completed all of today's habits" if completed_today \
             else "hasn't done today's habits yet"

    prompt = (
        f"Write a warm, personalised motivational message (2-3 sentences) for "
        f"{user_name}, who has a {streak}-day habit streak and is working on "
        f"their goal to {GOAL_DESCRIPTIONS.get(goal, goal)}. "
        f"They {status}. "
        "Be specific to their streak length and goal. End with a gentle action nudge. "
        "No hashtags, no emojis, no bullet points. Warm human tone only."
    )

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=120,
    )
    return response.choices[0].message.content.strip()


# ── 3. Difficulty-adapted suggestion ─────────────────────────────────────────

def suggest_habit_adjustment(
    habit_name: str,
    current_difficulty: int,
    direction: str  # "easier" or "harder"
) -> str:
    """
    Suggest how to tweak a habit based on the user's completion rate.
    direction = "easier" if they're struggling, "harder" if they're breezing through.
    """
    prompt = (
        f"The habit '{habit_name}' (current difficulty: {current_difficulty}/5) "
        f"needs to be made {direction}. "
        "Suggest ONE specific, concrete modification in one sentence. "
        "Keep it practical and encouraging."
    )
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=80,
    )
    return response.choices[0].message.content.strip()


# ── 4. AI coach chat ──────────────────────────────────────────────────────────

def coach_chat_response(
    user_message: str,
    plan_context: dict,
    chat_history: list[dict]
) -> str:
    """
    Respond as a personal AI habit coach, aware of the user's full plan context.

    plan_context should include:
        goal, user_type, streak, current_day, total_days, plan_title
    """
    system = (
        "You are a warm, encouraging personal habit coach named Sage. "
        "You are conversational, supportive, and evidence-based. "
        f"You know this user is working on: {GOAL_DESCRIPTIONS.get(plan_context.get('goal',''), '')}. "
        f"Their user type: {USER_TYPE_CONTEXT.get(plan_context.get('user_type',''), '')}. "
        f"Current streak: {plan_context.get('streak', 0)} days. "
        f"Plan progress: Day {plan_context.get('current_day', 1)} of {plan_context.get('total_days', 30)}. "
        "Answer questions about habits, provide motivation, suggest adjustments. "
        "Keep responses under 150 words. Be conversational, not clinical. "
        "Never use bullet points or headers in your response."
    )

    messages = [{"role": "system", "content": system}]
    messages += chat_history[-10:]   # last 10 messages for context
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.8,
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()

"""
utils/constants.py
------------------
All static data: goal types, user types, habit categories.
Centralised here so changing a label fixes it everywhere.
"""

GOALS = {
    "health":       "Improve health & energy",
    "productivity": "Increase productivity",
    "stress":       "Reduce stress & anxiety",
    "focus":        "Improve focus & attention",
    "children":     "Build good habits for children",
    "pregnancy":    "Healthy pregnancy routines",
    "family":       "Family wellness",
}

USER_TYPES = {
    "developer":  "Developer / remote worker",
    "student":    "Student",
    "parent":     "Parent",
    "pregnant":   "Pregnant woman",
    "elderly":    "Elderly person",
    "freelancer": "Freelancer",
    "office":     "Office worker",
    "gamer":      "Gamer",
    "child":      "Child (under 12)",
    "housewife":  "Housewife",
    "other":      "Other",
}

HABIT_CATEGORIES = {
    "health":      "Physical health",
    "mental":      "Mental wellness",
    "productivity":"Productivity",
    "learning":    "Learning",
    "social":      "Social connection",
    "sleep":       "Sleep",
}

TIME_OF_DAY_LABELS = {
    "morning":   "Morning",
    "afternoon": "Afternoon",
    "evening":   "Evening",
    "anytime":   "Anytime",
}

PLAN_TIER_FEATURES = {
    "free": {
        "max_plan_days":    7,
        "ai_coach":         False,
        "pdf_export":       False,
        "heatmap":          False,
        "social_cards":     False,
        "multiple_plans":   False,
    },
    "pro": {
        "max_plan_days":    30,
        "ai_coach":         True,
        "pdf_export":       True,
        "heatmap":          True,
        "social_cards":     True,
        "multiple_plans":   True,
    },
    "family": {
        "max_plan_days":    30,
        "ai_coach":         True,
        "pdf_export":       True,
        "heatmap":          True,
        "social_cards":     True,
        "multiple_plans":   True,
        "family_members":   5,
    },
}

PRICING = {
    "free":   {"price": 0,  "label": "Free"},
    "pro":    {"price": 9,  "label": "Pro — $9/month"},
    "family": {"price": 19, "label": "Family — $19/month"},
}

# Motivational quotes shown on completion
COMPLETION_QUOTES = [
    "Small steps every day lead to extraordinary results.",
    "Every habit completed is a vote for the person you're becoming.",
    "Consistency beats perfection every single time.",
    "You didn't come this far to only come this far.",
    "The secret of getting ahead is getting started.",
    "Your future self is cheering you on right now.",
    "Progress, not perfection.",
]

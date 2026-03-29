"""
pages/3_progress.py
--------------------
Progress dashboard: streak chart, completion heatmap, weekly stats.

CHARTS USED:
- Altair bar chart: completions per day (last 30 days)
- Custom HTML heatmap: GitHub-style contribution grid (last 12 weeks)
- Streamlit metrics: streak, total days, completion rate
"""

import streamlit as st
import pandas as pd
import altair as alt
from datetime import date, timedelta
from auth.auth_handler import require_login, is_pro_user
from core.streak_tracker import calculate_streak, get_habit_heatmap_data
from db.queries import get_completions_for_user, get_active_plan

st.set_page_config(page_title="My Progress", page_icon="📊", layout="wide")
require_login()

conn    = st.session_state["db_conn"]
user_id = st.session_state["user_id"]

st.title("📊 My Progress")

# ── Streak metrics ────────────────────────────────────────────────────────────
streak_data = calculate_streak(conn, user_id)
active_plan = get_active_plan(conn, user_id)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Current streak",  f"{streak_data['current']} 🔥",
            help="Consecutive days with at least 1 habit completed")
col2.metric("Longest streak",  f"{streak_data['longest']} days")
col3.metric("Total active days",f"{streak_data['total_days']} days")
if active_plan:
    pct = int((active_plan['current_day'] - 1) / active_plan['total_days'] * 100)
    col4.metric("Plan completion", f"{pct}%",
                f"Day {active_plan['current_day']} of {active_plan['total_days']}")

st.divider()

# ── Bar chart: completions per day (last 30 days) ─────────────────────────────
st.subheader("Daily completions — last 30 days")

completions = get_completions_for_user(conn, user_id)
today       = date.today()

# Build a DataFrame with a row for every day in the last 30 days
all_days = [(today - timedelta(days=i)).isoformat() for i in range(29, -1, -1)]
day_counts = {c: 0 for c in all_days} # initialise zeros
day_counts = {d: 0 for d in all_days}
for c in completions:
    if c["log_date"] in day_counts:
        day_counts[c["log_date"]] = day_counts.get(c["log_date"], 0) + 1

df = pd.DataFrame(
    [{"date": d, "count": day_counts.get(d, 0)} for d in all_days]
)
df["date"] = pd.to_datetime(df["date"])

chart = (
    alt.Chart(df)
    .mark_bar(color="#6c63ff", cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    .encode(
        x=alt.X("date:T", title="Date",
                axis=alt.Axis(format="%b %d", labelAngle=-45)),
        y=alt.Y("count:Q", title="Habits completed",
                scale=alt.Scale(domain=[0, max(df["count"].max() + 1, 5)])),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%B %d"),
            alt.Tooltip("count:Q", title="Habits completed")
        ]
    )
    .properties(height=220)
)
st.altair_chart(chart, use_container_width=True)

# ── Heatmap (Pro only) ────────────────────────────────────────────────────────
st.subheader("Activity heatmap — last 12 weeks")

if not is_pro_user():
    st.info("Upgrade to Pro to see your full activity heatmap.")
else:
    heatmap_data = get_habit_heatmap_data(conn, user_id)

    # Build 12-week grid (84 days)
    weeks = []
    for week_idx in range(11, -1, -1):
        week_days = []
        for day_idx in range(6, -1, -1):
            total_offset = week_idx * 7 + day_idx
            d = (today - timedelta(days=total_offset)).isoformat()
            count = heatmap_data.get(d, 0)
            week_days.append({"date": d, "count": count})
        weeks.append(week_days)

    # Render heatmap as HTML grid
    def count_to_color(n):
        if n == 0: return "#e8e8e8"
        if n == 1: return "#b5d4f4"
        if n == 2: return "#6c9ddd"
        if n >= 3: return "#2563eb"
        return "#e8e8e8"

    cells_html = ""
    for week in weeks:
        for day in week:
            color = count_to_color(day["count"])
            cells_html += (
                f'<div title="{day["date"]}: {day["count"]} habits" '
                f'style="width:14px;height:14px;background:{color};'
                f'border-radius:2px;margin:1px;display:inline-block"></div>'
            )

    grid_html = f"""
    <div style="display:grid;grid-template-columns:repeat(12,auto);gap:4px;
                padding:10px 0">
        {cells_html}
    </div>
    <div style="font-size:12px;color:#666;margin-top:4px">
        <span style="display:inline-block;width:12px;height:12px;
                     background:#e8e8e8;border-radius:2px;vertical-align:middle">
        </span> 0  
        <span style="display:inline-block;width:12px;height:12px;
                     background:#b5d4f4;border-radius:2px;vertical-align:middle;
                     margin-left:8px"></span> 1  
        <span style="display:inline-block;width:12px;height:12px;
                     background:#6c9ddd;border-radius:2px;vertical-align:middle;
                     margin-left:8px"></span> 2  
        <span style="display:inline-block;width:12px;height:12px;
                     background:#2563eb;border-radius:2px;vertical-align:middle;
                     margin-left:8px"></span> 3+
    </div>
    """
    st.html(grid_html)

# ── Weekly breakdown table ────────────────────────────────────────────────────
st.divider()
st.subheader("Last 4 weeks breakdown")

rows = []
for week_i in range(4):
    start = today - timedelta(days=(week_i + 1) * 7 - 1)
    end   = today - timedelta(days=week_i * 7)
    days_in_range = [(start + timedelta(days=i)).isoformat() for i in range(7)]
    active_days = sum(1 for d in days_in_range if d in streak_data["completion_dates"])
    total_habits = sum(day_counts.get(d, 0) for d in days_in_range)
    rows.append({
        "Week": f"{start.strftime('%b %d')} – {end.strftime('%b %d')}",
        "Active days": active_days,
        "Total habits completed": total_habits,
        "Completion rate": f"{int(active_days / 7 * 100)}%",
    })

df_weeks = pd.DataFrame(rows)
st.dataframe(df_weeks, use_container_width=True, hide_index=True)

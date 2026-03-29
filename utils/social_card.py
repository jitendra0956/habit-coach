"""
utils/social_card.py
---------------------
Generates shareable progress cards as PNG images using Pillow (PIL).

Users can download these and post on Instagram, Twitter, etc.
This is a powerful viral growth mechanism — every share is free advertising.

HOW PIL IMAGE GENERATION WORKS:
1. We create a blank Image object with a background color.
2. We draw shapes (rectangles, circles) using ImageDraw.
3. We add text using ImageFont (or default font if not installed).
4. We save to a BytesIO buffer (in-memory file).
5. Streamlit's download_button() uses the buffer bytes.
"""

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import date


def generate_progress_card(
    user_name: str,
    streak: int,
    goal_label: str,
    current_day: int,
    total_days: int,
    completion_dates: set[str],
) -> bytes:
    """
    Create a 1080×1080 social sharing card (Instagram square format).
    Returns PNG bytes that can be downloaded via Streamlit.
    """
    W, H = 1080, 1080

    # ── Canvas ────────────────────────────────────────────────────────────────
    img  = Image.new("RGB", (W, H), color="#0f0f1a")  # dark background
    draw = ImageDraw.Draw(img)

    # ── Background accent shapes ──────────────────────────────────────────────
    draw.ellipse([700, -100, 1200, 400], fill="#1a1040")   # top-right glow
    draw.ellipse([-100, 700, 400, 1200], fill="#0a2010")   # bottom-left glow

    # ── App name ──────────────────────────────────────────────────────────────
    _draw_text(draw, "🌱 AI Habit Coach", W // 2, 100,
               font_size=36, fill="#9b9dff", anchor="mm")

    # ── Streak number (BIG) ───────────────────────────────────────────────────
    _draw_text(draw, f"{streak}", W // 2, 350, font_size=240,
               fill="#ffffff", anchor="mm")
    _draw_text(draw, "day streak 🔥", W // 2, 490, font_size=52,
               fill="#ffa500", anchor="mm")

    # ── Divider line ──────────────────────────────────────────────────────────
    draw.line([(140, 560), (940, 560)], fill="#333355", width=2)

    # ── Goal and progress ─────────────────────────────────────────────────────
    _draw_text(draw, f"Goal: {goal_label}", W // 2, 630,
               font_size=40, fill="#aaaacc", anchor="mm")
    _draw_text(draw, f"Day {current_day} of {total_days}  ·  {user_name}",
               W // 2, 700, font_size=34, fill="#8888aa", anchor="mm")

    # ── Mini activity dots (last 30 days) ─────────────────────────────────────
    dot_size  = 22
    dot_gap   = 6
    cols_dots = 15
    start_x   = W // 2 - (cols_dots * (dot_size + dot_gap)) // 2
    start_y   = 780

    today = date.today()
    for i in range(30):
        d       = (today.toordinal() - 29 + i)
        d_str   = date.fromordinal(d).isoformat()
        done    = d_str in completion_dates
        col_i   = i % cols_dots
        row_i   = i // cols_dots
        x       = start_x + col_i * (dot_size + dot_gap)
        y       = start_y + row_i * (dot_size + dot_gap)
        color   = "#6c63ff" if done else "#2a2a3a"
        draw.rounded_rectangle([x, y, x + dot_size, y + dot_size],
                                radius=4, fill=color)

    # ── Hashtags ──────────────────────────────────────────────────────────────
    _draw_text(draw, "#AIHabitCoach  #SmallHabitsBigLife  #HabitStreak",
               W // 2, 950, font_size=28, fill="#555577", anchor="mm")

    # ── Export to bytes ───────────────────────────────────────────────────────
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.getvalue()


def _draw_text(draw, text: str, x: int, y: int, font_size: int,
               fill: str, anchor: str = "la"):
    """Helper to draw text — uses default PIL font (no font file needed)."""
    try:
        # Try to use a better font if available on the system
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                                   font_size)
    except (IOError, OSError):
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",
                                       font_size)
        except (IOError, OSError):
            font = ImageFont.load_default()

    draw.text((x, y), text, font=font, fill=fill, anchor=anchor)

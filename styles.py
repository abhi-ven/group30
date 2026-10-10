"""Shared colours and CSS. Change the look of the whole app from here."""
import streamlit as st

ACCENT = "#4F46E5"

# Timeline block colours by PlanBlock.type
BLOCK_COLOURS = {
    "fixed": "#64748B",   # lectures, meetings, meals: things that never move
    "task": ACCENT,       # study work the scheduler placed
    "break": "#0D9488",
}

# Deadline status colours
STATUS_COLOURS = {
    "safe": "#16A34A",
    "tight": "#D97706",
    "at_risk": "#DC2626",
    "done": "#64748B",
}
STATUS_LABELS = {
    "safe": "Safe",
    "tight": "Tight",
    "at_risk": "At risk",
    "done": "Done",
}

# PlanBlock.changeStatus colours (used on the Rescue My Day side-by-side view)
CHANGE_COLOURS = {
    "moved": "#2563EB",
    "shortened": "#D97706",
    "added": "#16A34A",
    "dropped": "#DC2626",
}

CSS = """
<style>
.ds-row { display: flex; gap: 14px; margin-bottom: 8px; }
.ds-time {
    width: 96px; flex-shrink: 0; padding-top: 10px;
    font-size: 0.85rem; opacity: 0.7; font-variant-numeric: tabular-nums;
}
.ds-card { flex: 1; border-left: 4px solid; border-radius: 8px; padding: 8px 12px; }
.ds-card.ds-now { box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.55); }
.ds-card.ds-dropped { opacity: 0.55; text-decoration: line-through; }
.ds-title { font-weight: 600; line-height: 1.35; }
.ds-sub { font-size: 0.82rem; opacity: 0.7; margin-top: 2px; }
.ds-badge {
    display: inline-block; padding: 1px 9px; border-radius: 999px;
    font-size: 0.75rem; font-weight: 600; margin-left: 8px; vertical-align: middle;
}
</style>
"""


def inject_css():
    """Call once at the top of every page."""
    st.markdown(CSS, unsafe_allow_html=True)


def tint(hex_colour: str, alpha: float = 0.12) -> str:
    """'#4F46E5' -> 'rgba(79,70,229,0.12)'. Works on light and dark themes."""
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"
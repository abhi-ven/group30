"""Reusable UI pieces and small display helpers, shared by every page.

Rescue My Day can reuse render_timeline() for the original vs revised view:
blocks with a changeStatus get a badge automatically.
"""
from __future__ import annotations

import html
from datetime import datetime
import streamlit as st
from styles import (BLOCK_COLOURS, ACCENT, STATUS_COLOURS, STATUS_LABELS,
                    CHANGE_COLOURS, tint)


# ---------- pure helpers (no Streamlit calls, easy to test) ----------

def parse_dt(value: str) -> datetime:
    """ISO string -> naive datetime. Timezone info is dropped, keeping the
    wall-clock time as written (all data is Europe/Dublin)."""
    dt = datetime.fromisoformat(value)
    return dt.replace(tzinfo=None) if dt.tzinfo else dt


def minutes_label(minutes: int) -> str:
    h, m = divmod(int(minutes), 60)
    if h and m:
        return f"{h}h {m:02d}m"
    return f"{h}h" if h else f"{m}m"


def block_minutes(block: dict) -> int:
    return int((parse_dt(block["end"]) - parse_dt(block["start"])).total_seconds() // 60)


def block_title(block: dict, state: dict) -> str:
    """Blocks only carry refId, so look the title up (or use block['title'] if present)."""
    if block.get("title"):
        return block["title"]
    for item in state["fixed_events"] + state["tasks"]:
        if item["id"] == block["refId"]:
            return item["title"]
    return "Break" if block["type"] == "break" else "Untitled"


def task_progress(task: dict) -> float:
    """0.0 to 1.0, from remainingMinutes vs estimatedMinutes."""
    if task["status"] == "done":
        return 1.0
    est = task["estimatedMinutes"] or 1
    return min(1.0, max(0.0, 1 - task["remainingMinutes"] / est))


def deadline_status(task: dict, now: datetime | None = None) -> str:
    """Simple display heuristic: done / at_risk / tight / safe.
    If the scheduler marks a task at_risk, that wins."""
    now = now or datetime.now()
    if task["status"] == "done":
        return "done"
    if task["status"] == "at_risk" or not task.get("due"):
        return "at_risk"
    hours_left = (parse_dt(task["due"]) - now).total_seconds() / 3600
    if hours_left < 0:
        return "at_risk"
    return "tight" if hours_left <= 48 else "safe"


def due_label(task: dict, now: datetime | None = None) -> str:
    now = now or datetime.now()
    if not task.get("due"):
        return "No date found. Add one to include it in your plan."
    due = parse_dt(task["due"])
    if due < now:
        return f"Overdue since {due:%a %d %b}"
    days = (due.date() - now.date()).days
    clock = due.strftime("%H:%M")
    if days == 0:
        return f"Due today at {clock}"
    if days == 1:
        return f"Due tomorrow at {clock}"
    return f"Due {due:%a %d %b} at {clock}, in {days} days"


# ---------- HTML pieces ----------

def _badge(text: str, colour: str) -> str:
    return (f'<span class="ds-badge" style="color:{colour};'
            f'background:{tint(colour, 0.14)}">{html.escape(text)}</span>')


def status_badge(status: str) -> str:
    """Returns HTML for a Safe / Tight / At risk / Done pill."""
    return _badge(STATUS_LABELS.get(status, status), STATUS_COLOURS.get(status, "#64748B"))


# ---------- Streamlit components ----------

def render_timeline(blocks: list[dict], state: dict, now: datetime | None = None):
    """Colour-coded day timeline. Highlights the block happening now and shows a
    badge for any block with a changeStatus of moved / shortened / added / dropped.

    Titles come from PDFs and the LLM, so everything is HTML-escaped."""
    now = now or datetime.now()
    rows = []
    for b in sorted(blocks, key=lambda b: parse_dt(b["start"])):
        start, end = parse_dt(b["start"]), parse_dt(b["end"])
        colour = BLOCK_COLOURS.get(b["type"], ACCENT)
        change = b.get("changeStatus")
        classes = "ds-card"
        if start <= now < end:
            classes += " ds-now"
        if change == "dropped":
            classes += " ds-dropped"

        title = html.escape(block_title(b, state))
        badge = _badge(change, CHANGE_COLOURS[change]) if change in CHANGE_COLOURS else ""
        kind = {"task": "Study", "break": "Break"}.get(b["type"], "")
        if b["type"] == "fixed":
            event = next((e for e in state["fixed_events"] if e["id"] == b["refId"]), {})
            kind = event.get("kind", "fixed").capitalize()
        sub = f"{kind}, {minutes_label(block_minutes(b))}"
        extra = (f'<div class="ds-sub">{html.escape(b["explanation"])}</div>'
                 if b.get("explanation") else "")

        rows.append(
            f'<div class="ds-row"><div class="ds-time">{start:%H:%M} to {end:%H:%M}</div>'
            f'<div class="{classes}" style="border-left-color:{colour};background:{tint(colour)}">'
            f'<div class="ds-title">{title}{badge}</div>'
            f'<div class="ds-sub">{html.escape(sub)}</div>{extra}</div></div>'
        )
    # No blank lines or indentation inside the HTML, or Markdown turns it into a code block.
    st.markdown("".join(rows), unsafe_allow_html=True)


def deadline_card(task: dict, now: datetime | None = None):
    status = deadline_status(task, now)
    with st.container(border=True):
        left, right = st.columns([3, 1], vertical_alignment="center")
        left.markdown(f"**{task['title']}**")
        right.markdown(status_badge(status), unsafe_allow_html=True)
        st.caption(due_label(task, now))
        st.progress(task_progress(task))
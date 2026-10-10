"""Main page: Aoife's day at a glance, with one-tap rescue when it falls apart."""
from __future__ import annotations
from datetime import datetime, timedelta
import streamlit as st
from streamlit.errors import StreamlitAPIException

from components import (parse_dt, minutes_label, block_minutes, block_title,
                        task_progress, deadline_status, due_label,
                        render_timeline, deadline_card)
from styles import inject_css

# ---- Set these to the filenames registered in app.py's st.Page(...) ----
ASSIGNMENTS_PAGE = "assignments.py"   # Connect Brightspace + review screen
TIMETABLE_PAGE = "planner.py"         # lecture timetable
RESCUE_PAGE = "rescue.py"             # Rescue My Day

PRESETS = ["I lost two hours", "My assignment will take twice as long",
           "An urgent task appeared", "I missed a study session"]


# ---------- small helpers ----------

def go(page: str):
    """Switch page, with a readable message if the filename is wrong."""
    try:
        st.switch_page(page)
    except StreamlitAPIException:
        st.error(f"Page '{page}' isn't registered in app.py. "
                 "Check the page filenames at the top of dashboard.py.")


def safe_page_link(page: str, label: str, icon: str | None = None):
    try:
        st.page_link(page, label=label, icon=icon)
    except StreamlitAPIException:
        st.caption(f"'{page}' isn't registered yet. Check the page filenames at the top of dashboard.py.")


def wide_button(container, label: str, **kwargs) -> bool:
    """Full-width button that works across Streamlit versions."""
    for extra in ({"width": "stretch"}, {"use_container_width": True}, {}):
        try:
            return container.button(label, **kwargs, **extra)
        except TypeError:
            continue
    return False


def send_to_rescue(text: str):
    st.session_state.pending_disruption = text     # Rescue My Day reads this
    go(RESCUE_PAGE)


def toggle_done(task_id: str):
    checked = st.session_state[f"done_{task_id}"]
    for t in st.session_state.state["tasks"]:
        if t["id"] == task_id:
            if checked:
                t["status"] = "done"
            else:
                t["status"] = "in_progress" if t["remainingMinutes"] < t["estimatedMinutes"] else "todo"


# ---------- data ----------

inject_css()
state = st.session_state.state
now = datetime.now()
plan = state.get("plan") or {"blocks": [], "warnings": []}
tasks = [t for t in state["tasks"] if not t.get("parentId")]    # top-level tasks only
open_tasks = [t for t in tasks if t["status"] != "done"]

# ---------- header ----------
hour = now.hour
greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
st.title(f"{greeting}, {state['student']['name']}")
st.caption(f"{now:%A} {now.day} {now:%B}, {state['student']['course']}")

# ---------- empty state ----------
if not tasks and not plan["blocks"]:
    with st.container(border=True):
        st.markdown("**Bring in your assessments**")
        st.write("Connect Brightspace and DayShift builds a study plan around your lectures.")
        safe_page_link(ASSIGNMENTS_PAGE, "Connect Brightspace (simulated)", "📄")
    st.stop()

# ---------- one-line status ----------
dated = [t for t in open_tasks if t.get("due")]
at_risk = [t for t in dated if deadline_status(t, now) == "at_risk"]
tight = [t for t in dated if deadline_status(t, now) == "tight"]
warnings = plan.get("warnings", [])

if warnings:                       # the scheduler's own flags take priority
    for w in warnings:
        st.warning(w)
elif at_risk:
    st.error("At risk: " + ", ".join(t["title"] for t in at_risk))
elif tight:
    st.warning(f"Tight on time: {tight[0]['title']}. {due_label(tight[0], now)}.")
else:
    st.success("You're on track. Everything fits.")

missing = [t for t in open_tasks if not t.get("due")]
if missing:
    st.warning("No deadline found for: " + ", ".join(t["title"] for t in missing)
               + ". Add a date so they can be scheduled.")

# ---------- metrics ----------
due_this_week = [t for t in dated if parse_dt(t["due"]) - now <= timedelta(days=7)]
planned_today = sum(block_minutes(b) for b in plan["blocks"] if b["type"] == "task")
upcoming = sorted((b for b in plan["blocks"]
                   if b["type"] == "task" and parse_dt(b["start"]) > now),
                  key=lambda b: parse_dt(b["start"]))

m1, m2, m3 = st.columns(3)
with m1.container(border=True):
    st.metric("Due this week", len(due_this_week))
with m2.container(border=True):
    st.metric("Study planned today", minutes_label(planned_today))
with m3.container(border=True):
    if upcoming:
        st.metric("Next study block", f"{parse_dt(upcoming[0]['start']):%H:%M}",
                  help=block_title(upcoming[0], state))
    else:
        st.metric("Next study block", "None left today")

# ---------- the day (left) and the rescue + deadlines (right) ----------
left, right = st.columns([3, 2], gap="large")

with left:
    st.subheader("Today")
    if plan["blocks"]:
        render_timeline(plan["blocks"], state, now)
    else:
        st.info("No plan for today yet. Add your lectures and free hours to generate one.")
        safe_page_link(TIMETABLE_PAGE, "Open your timetable", "🗓️")

with right:
    st.subheader("Rescue my day")
    with st.container(border=True):
        st.markdown("**Did something go wrong?**")
        st.caption("Tap one and DayShift rebuilds the rest of your day.")
        for text in PRESETS:
            if wide_button(st, text, key=f"preset_{text}"):
                send_to_rescue(text)
        typed = st.text_input("What happened?", key="dash_disruption_text",
                              placeholder="e.g. My bus was late and I lost two hours",
                              label_visibility="collapsed")
        if wide_button(st, "Rescue my day", type="primary", key="dash_go"):
            if typed.strip():
                send_to_rescue(typed.strip())
            else:
                st.warning("Describe what happened, or tap one of the options above.")

"""Dashboard: today's plan, upcoming deadlines and task progress."""
from datetime import datetime, timedelta
import streamlit as st
from components import (parse_dt, minutes_label, block_minutes, block_title,
                        task_progress, render_timeline, deadline_card)
from styles import inject_css
import streamlit_shadcn_ui as ui
from helper_functions import set_page

inject_css()

state = st.session_state.state
now = datetime.now()
plan = state.get("plan") or {"blocks": [], "warnings": []}
tasks = [t for t in state["tasks"] if not t.get("parentId")]   # top-level tasks only
open_tasks = [t for t in tasks if t["status"] != "done"]


def toggle_done(task_id: str):
    checked = st.session_state[f"done_{task_id}"]
    for t in st.session_state.state["tasks"]:
        if t["id"] == task_id:
            if checked:
                t["status"] = "done"
            else:
                t["status"] = "in_progress" if t["remainingMinutes"] < t["estimatedMinutes"] else "todo"


# ---------- header and page setup ----------
hour = now.hour
greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
st.set_page_config(page_title = "Dashboard", layout = "wide")
set_page(f"{greeting}, {state['student']['name']}", f"{now:%A} {now.day} {now:%B}, {state['student']['course']}")


# ---------- empty state ----------
if not tasks and not plan["blocks"]:
    st.info("Nothing planned yet. Upload an assignment brief and DayShift will build your plan.")
    st.page_link("views/assignments.py", label="Upload an assignment brief", icon="📄")
    st.stop()

# ---------- warnings ----------
for warning in plan.get("warnings", []):
    st.warning(warning)
missing_dates = [t for t in open_tasks if not t.get("due")]
if missing_dates:
    names = ", ".join(t["title"] for t in missing_dates)
    st.warning(f"No deadline found for: {names}. Add a date so they can be scheduled.")

# ---------- metrics ----------
due_this_week = [t for t in open_tasks
                 if t.get("due") and parse_dt(t["due"]) - now <= timedelta(days=7)]
planned_today = sum(block_minutes(b) for b in plan["blocks"] if b["type"] == "task")
total_est = sum(t["estimatedMinutes"] for t in tasks) or 1
overall = sum(t["estimatedMinutes"] * task_progress(t) for t in tasks) / total_est
upcoming_blocks = sorted((b for b in plan["blocks"]
                          if b["type"] == "task" and parse_dt(b["start"]) > now),
                         key=lambda b: parse_dt(b["start"]))

cols = st.columns(4)
with cols[0].container(border=True):
    ui.metric_card("Due this week", len(due_this_week),
                delta = "subtitle")
with cols[1].container(border=True):
    ui.metric_card("Study planned today", minutes_label(planned_today), delta = "subtitle")
with cols[2].container(border=True):
    ui.metric_card("Overall progress", f"{round(overall * 100)}%", delta = "subtitle")
with cols[3].container(border=True):
    if upcoming_blocks:
        nxt = upcoming_blocks[0]
        ui.metric_card("Next study block", f"{parse_dt(nxt['start']):%H:%M}",
                  delta = block_title(nxt, state))
    else:
        ui.metric_card("Next study block", "None left today")

# ---------- timeline + deadlines ----------
left, right = st.columns([3, 2], gap="large")

with left:
    st.subheader("Today")
    if plan["blocks"]:
        render_timeline(plan["blocks"], state, now)
    else:
        st.info("No plan for today yet. Add your lectures and free hours to generate one.")
        st.page_link("views/planner.py", label="Open Plan B", icon="🗓️")

with right:
    st.subheader("Upcoming deadlines")
    by_due = sorted(open_tasks, key=lambda t: parse_dt(t["due"]) if t.get("due") else datetime.max)
    if by_due:
        for t in by_due:
            deadline_card(t, now)
    else:
        st.success("Everything is done. Nice work.")

# ---------- task progress ----------
st.subheader("Task progress")
for t in tasks:
    c1, c2 = st.columns([2, 3], vertical_alignment="center")
    c1.checkbox(t["title"], value=t["status"] == "done", key=f"done_{t['id']}",
                on_change=toggle_done, args=(t["id"],))
    pct = task_progress(t)
    label = "Done" if t["status"] == "done" else f"{round(pct * 100)}%, {minutes_label(t['remainingMinutes'])} left"
    c2.progress(pct, text=label)

# ---------- quick disruptions ----------
st.subheader("Did something go wrong?")
PRESETS = ["I lost two hours", "My assignment will take twice as long",
           "An urgent task appeared", "I missed a study session"]
for col, text in zip(st.columns(len(PRESETS)), PRESETS):
    if col.button(text, key=f"preset_{text}"):
        st.session_state.pending_disruption = text      # Rescue My Day reads this
        st.switch_page("views/rescue.py")
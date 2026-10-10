"""Teammate's timeline/deadline components, using Dublin-aware times."""
import html
from datetime import datetime
import streamlit as st
from study_planner.helpers import DUBLIN
from styles import BLOCK_COLOURS,ACCENT,CHANGE_COLOURS,STATUS_COLOURS,STATUS_LABELS,tint

def parse_dt(value):
    dt=datetime.fromisoformat(value)
    return (dt.replace(tzinfo=DUBLIN) if dt.tzinfo is None else dt.astimezone(DUBLIN))
def local_now(now=None):
    now=now or datetime.now(DUBLIN)
    return now.replace(tzinfo=DUBLIN) if now.tzinfo is None else now.astimezone(DUBLIN)
def minutes_label(minutes):
    h,m=divmod(int(minutes),60)
    return f'{h}h {m:02d}m' if h and m else f'{h}h' if h else f'{m}m'
def block_minutes(block):return int((parse_dt(block['end'])-parse_dt(block['start'])).total_seconds()/60)
def block_title(block,state):
    if block['type']=='break':return 'Break'
    if block.get('title'):return block['title']
    return next((x['title'] for x in state['fixed_events']+state['tasks'] if x['id']==block['refId']),'Untitled')
def task_progress(task):
    return 1.0 if task['status']=='done' else min(1.,max(0.,1-task['remainingMinutes']/max(1,task['estimatedMinutes'])))
def deadline_status(task,now=None):
    if task['status']=='done':return 'done'
    if task['status']=='at_risk' or not task.get('due'):return 'at_risk'
    left=(parse_dt(task['due'])-local_now(now)).total_seconds()/3600
    return 'at_risk' if left<0 else 'tight' if left<=48 else 'safe'
def due_label(task,now=None):
    if not task.get('due'):return 'No deadline added.'
    return 'Due '+parse_dt(task['due']).strftime('%a %d %b at %H:%M')
def _badge(text,colour):
    return f'<span class="ds-badge" style="color:{colour};background:{tint(colour)}">{html.escape(text)}</span>'
def status_badge(status):return _badge(STATUS_LABELS.get(status,status),STATUS_COLOURS.get(status,'#64748B'))
def render_timeline(blocks,state,now=None):
    now=local_now(now);rows=[]
    for b in sorted(blocks,key=lambda b:parse_dt(b['start'])):
        start,end=parse_dt(b['start']),parse_dt(b['end']);colour=BLOCK_COLOURS.get(b['type'],ACCENT)
        change=b.get('changeStatus');badge=_badge(change,CHANGE_COLOURS[change]) if change in CHANGE_COLOURS else ''
        classes='ds-card'+(' ds-now' if start<=now<end else '')+(' ds-dropped' if change=='dropped' else '')
        kind={'task':'Study','break':'Break','fixed':'Class / commitment'}.get(b['type'],'')
        event=next((e for e in state['fixed_events'] if e['id']==b['refId']),{})
        location=html.escape(event.get('location',''))
        rows.append(f'<div class="ds-row"><div class="ds-time">{start:%H:%M} – {end:%H:%M}</div><div class="{classes}" style="border-left-color:{colour};background:{tint(colour)}"><div class="ds-title">{html.escape(block_title(b,state))}{badge}</div><div class="ds-sub">{kind}, {minutes_label(block_minutes(b))}</div><div class="ds-sub">{location}</div></div></div>')
    st.markdown(''.join(rows),unsafe_allow_html=True)
def deadline_card(task,now=None):
    with st.container(border=True):
        st.text(task['title']);st.markdown(status_badge(deadline_status(task,now)),unsafe_allow_html=True)
        st.caption(due_label(task,now));st.progress(task_progress(task))

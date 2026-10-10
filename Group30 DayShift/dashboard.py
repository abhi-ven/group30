"""Day at a glance, linked to the real planner and rescue page."""
from datetime import datetime,timedelta
import streamlit as st
from app_state import current_plan
from assignment_bridge import assignment_tasks
from components import parse_dt,minutes_label,block_minutes,block_title,render_timeline,deadline_card
from study_planner.helpers import DUBLIN
from styles import inject_css

inject_css()
now=datetime.now(DUBLIN)
state=st.session_state.state
result=current_plan()
tasks=result['state']['tasks'] if result else assignment_tasks(st.session_state.assignments)
state['tasks']=tasks
hour=now.hour
greeting='Good morning' if hour<12 else 'Good afternoon' if hour<18 else 'Good evening'
st.title(f"{greeting}, {state['student']['name']}")
st.caption(f"{now:%A, %d %B} · {state['student']['course']}")
if not tasks:
    st.info('Add your assignments, then import your timetable and generate a study plan.')
    st.page_link('assignments.py',label='Open assignments',icon='📄')
    st.page_link('planner.py',label='Open your timetable',icon='🗓️')
else:
    plan=result['plan'] if result else {'blocks':[],'warnings':[]}
    if result:
        for row in result['times']:
            if row['unscheduledMinutes']:
                st.warning(row['title']+': '+minutes_label(row['unscheduledMinutes'])+' does not fit in this day.')
        if not any(row['unscheduledMinutes'] for row in result['times']):
            st.success('All remaining work fits in this day’s plan.')
    else:
        st.info('Your assignments are ready. Generate a plan in My Timetable.')
    open_tasks=[t for t in tasks if t['status']!='done']
    due_week=[t for t in open_tasks if t.get('due') and now<=parse_dt(t['due'])<=now+timedelta(days=7)]
    upcoming=sorted((b for b in plan['blocks'] if b['type']=='task' and parse_dt(b['start'])>now),key=lambda b:parse_dt(b['start']))
    a,b,c=st.columns(3)
    a.metric('Due this week',len(due_week))
    b.metric('Study in selected plan',minutes_label(sum(block_minutes(x) for x in plan['blocks'] if x['type']=='task')))
    c.metric('Next study block',parse_dt(upcoming[0]['start']).strftime('%a %H:%M') if upcoming else 'None')
    left,right=st.columns([3,2],gap='large')
    with left:
        st.subheader('Your day' if not result else 'Plan for '+result['state']['date'])
        if plan['blocks']:render_timeline(plan['blocks'],state,now)
        else:st.info('No plan generated yet.')
        st.page_link('planner.py',label='Open your timetable',icon='🗓️')
    with right:
        st.subheader('Rescue my day')
        with st.container(border=True):
            st.caption('Describe what changed and we’ll reorganise the selected plan.')
            if st.button('I lost two hours',disabled=result is None):
                st.session_state.pending_disruption='I lost 2 hours'
                st.switch_page('rescue.py')
            typed=st.text_input('What happened?',placeholder='My Java lecture ran 30 minutes late')
            if st.button('Rescue my day',type='primary',disabled=result is None):
                if typed.strip():
                    st.session_state.pending_disruption=typed.strip();st.switch_page('rescue.py')
                else:st.warning('Describe what happened first.')
        st.subheader('Deadlines')
        for task in sorted(open_tasks,key=lambda t:parse_dt(t['due']) if t.get('due') else datetime.max.replace(tzinfo=DUBLIN)):
            deadline_card(task,now)

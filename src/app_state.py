"""One shared state for all four pages; no separate dashboard sample plan."""
from copy import deepcopy
import streamlit as st
from assignment_bridge import assignment_tasks
from study_planner import service

def initialise():
    st.session_state.setdefault('assignments',[])
    st.session_state.setdefault('day_plans',{})
    st.session_state.setdefault('state',{'student':{'name':'Student','course':'Year 2'},
          'fixed_events':[],'tasks':[],'plan':{'blocks':[],'warnings':[]}})

def store_plan(day,result):
    st.session_state.day_plans[day]=result
    # Adapter for the frontend teammate's snake_case fixed_events field.
    st.session_state.state={'student':st.session_state.state['student'],
       'fixed_events':deepcopy(result['state']['fixedEvents']),
       'tasks':deepcopy(result['state']['tasks']),'plan':deepcopy(result['plan'])}
    st.session_state.active_plan_day=day

def clear_plans():
    st.session_state.day_plans={}
    st.session_state.pop('active_plan_day',None)
    st.session_state.state['plan']={'blocks':[],'warnings':[]}
    st.session_state.state['fixed_events']=[]
    st.session_state.state['tasks']=assignment_tasks(st.session_state.assignments)

def current_plan():
    day=st.session_state.get('active_plan_day')
    return st.session_state.day_plans.get(day)

def rescue(text):
    previous=current_plan()
    if not previous:
        return {'ok':False,'violations':['Generate a plan in My Timetable first.']}
    day=previous['state']['date']
    now=service.now_iso()
    if day!=now[:10]: now=previous['state']['now']
    result=service.handle_disruption(previous,text,now=now)
    if result['ok']:store_plan(day,result)
    return result

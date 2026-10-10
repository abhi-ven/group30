from datetime import datetime, time
import streamlit as st
from calendar_import import events_for_day
from timetable_ui import render_timetable_import
from assignment_bridge import assignment_tasks
from study_planner import service
from study_planner.helpers import DUBLIN
from app_state import store_plan
from helper_functions import set_page
from components import render_timeline
from styles import inject_css
inject_css()
set_page('My Timetable','Your classes and study sessions, one day at a time.')

def show_events(events):
    blocks = [{'id':event['id'], 'refId':event['id'], 'type':event.get('type','fixed'),
               'start':event['start'], 'end':event['end'], 'title':event['title'],
               'changeStatus':event.get('changeStatus','unchanged')} for event in events]
    render_timeline(blocks, {'fixed_events':events, 'tasks':[]})


timetable = render_timetable_import(show_classes=False)
if timetable is not None:
    day = st.session_state['calendar_selected_day']
    events = events_for_day(timetable, day)
    st.session_state.setdefault('commitments', [])
    with st.expander('Add a commitment'):
        with st.form('commitment_form', clear_on_submit=True):
            name = st.text_input('Name')
            weekday = st.selectbox('Day of the week', ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
            begins = st.time_input('Starts at', value=time(9), key='commitment_start')
            ends = st.time_input('Ends at', value=time(10), key='commitment_end')
            added = st.form_submit_button('Add commitment')
        if added:
            if not name.strip() or ends <= begins:
                st.error('Enter a name and an end time after the start time.')
            else:
                from uuid import uuid4
                st.session_state.commitments.append({'id':'commitment:'+str(uuid4()),'title':name.strip(),
                    'weekday':weekday,'start':begins.strftime('%H:%M'),'end':ends.strftime('%H:%M')})
                from app_state import clear_plans
                clear_plans(); st.rerun()
        for commitment in st.session_state.commitments:
            st.text(commitment['weekday']+' '+commitment['start']+' – '+commitment['end']+': '+commitment['title'])
    for commitment in st.session_state.commitments:
        if datetime.fromisoformat(day).strftime('%A') == commitment['weekday']:
            events.append({'id':commitment['id'],'title':commitment['title'],
                'start':service._at(day,commitment['start']),'end':service._at(day,commitment['end']),
                'kind':'other','source':'manual','protected':True})
    current = st.session_state['day_plans'].get(day)
    if current: st.session_state.active_plan_day = day
    with st.expander('Study hours'):
        start = st.time_input('Available from', value=time(9), key='study_start')
        end = st.time_input('Available until', value=time(17), key='study_end')
        limit = st.slider('Max study hours per day', 1, 10, 4)
    if st.button('Plan my study time', type='primary', disabled=not st.session_state['assignments']):
        if end <= start:
            st.error('Study availability must end after it starts.')
        else:
            # Today uses real time. Other dates are explicit day-start previews.
            now = service.now_iso() if day == datetime.now(DUBLIN).date().isoformat() else service._at(day, start.strftime('%H:%M'))
            try:
                tasks = assignment_tasks(st.session_state['assignments'])
                state = service.new_state(day, start.strftime('%H:%M'), end.strftime('%H:%M'),
                                          events=events, tasks=tasks, now=now)
                state['studyMinuteLimit'] = limit * 60
                result = service.make_plan(state)
            except (ValueError, KeyError, TypeError) as error:
                result = {'ok': False, 'violations': [str(error)]}
            if result['ok']:
                store_plan(day, result)
                st.rerun()
            else:
                st.error('Could not create the plan: ' + '; '.join(result['violations']))
    if current is None:
        if not st.session_state['assignments']:
            st.caption('Add assignments in the Assignments tab to plan study time.')
        show_events(events)
        if not events:
            st.info('No classes today.')
    else:
        # This is the current plan, including fixed events explicitly changed
        # by a disruption. Do not re-add stale originals from the ICS file.
        show_events(current['calendar'])
        for row in current['times']:
            if row['unscheduledMinutes']:
                st.warning(row['title'] + ': ' + str(row['unscheduledMinutes']) + ' minutes do not fit in this day.')
        st.page_link('rescue_page.py',label='Rescue My Day',icon='🔄')
        st.download_button('Export this day', service.export_ics(current), file_name='dayshift-'+day+'.ics', mime='text/calendar')

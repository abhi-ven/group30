"""Rescue form embedded in My Timetable."""
import streamlit as st
from app_state import current_plan,rescue,store_plan
from study_planner import service
from components import render_timeline

def render_rescue():
    st.subheader('Rescue My Day')
    previous=current_plan()
    if previous is None:
        st.info('Generate a study plan in My Timetable first.')
        return
    else:
        st.caption('Editing the plan for '+previous['state']['date'])
        pending=st.session_state.pop('pending_disruption',None)
        if pending is not None:st.session_state.rescue_text=pending
        with st.form('rescue_form'):
            text=st.text_area('What changed?',key='rescue_text',placeholder='My Java lecture ran 30 minutes late')
            submitted=st.form_submit_button('Rescue my day',type='primary')
        if submitted:
            if not text.strip():st.warning('Describe what changed first.')
            else:
                with st.spinner('Reorganising…'):result=rescue(text.strip())
                if not result['ok']:st.error('Please clarify the change: '+'; '.join(result['violations']))
                else:st.rerun()
        # Every change can also be demonstrated without an API key.
        with st.expander('Report a change using a form'):
            kinds=['Lost time','Task takes longer','Urgent task','Missed study session','Cancelled event','Class ran late']
            kind=st.selectbox('Change',kinds)
            change=None
            if kind=='Lost time':change={'type':'lost_time','minutes':st.number_input('Minutes lost',min_value=1,max_value=1440,value=30)}
            elif kind=='Task takes longer':
                items=previous['state']['tasks']
                if items:
                    tid=st.selectbox('Assignment', [t['id'] for t in items],format_func=lambda x:next(t['title'] for t in items if t['id']==x))
                    change={'type':'task_takes_longer','taskId':tid,'multiplier':st.number_input('Effort multiplier',min_value=1.1,max_value=10.,value=2.,step=.1)}
            elif kind in ['Cancelled event','Class ran late']:
                items=previous['state']['fixedEvents']
                if items:
                    eid=st.selectbox('Class / commitment',[e['id'] for e in items],format_func=lambda x:next(e['title'] for e in items if e['id']==x))
                    change={'type':'cancelled_event' if kind=='Cancelled event' else 'late_running_event','eventId':eid}
                    if kind=='Class ran late':change['minutes']=st.number_input('Extra minutes',min_value=1,max_value=1440,value=30)
                else:st.info('No fixed events in this plan.')
            elif kind=='Missed study session':
                blocks=[b for b in previous['plan']['blocks'] if b['type']=='task']
                if blocks:
                    bid=st.selectbox('Session',[b['id'] for b in blocks],format_func=lambda x:next(b['start'][11:16]+' – '+b['end'][11:16] for b in blocks if b['id']==x))
                    change={'type':'missed_session','blockId':bid}
            else:
                title=st.text_input('Urgent assignment title')
                minutes=st.number_input('Estimated minutes',min_value=1,value=60)
                due=st.date_input('Urgent deadline')
                clock=st.time_input('Urgent deadline time')
                weight=st.number_input('Weighting (%)',min_value=0,max_value=100,value=20)
                if title.strip():change={'type':'urgent_task','newTask':{'title':title.strip(),'estimatedMinutes':minutes,'weighting':weight,'due':service._at(due.isoformat(),clock.strftime('%H:%M'))}}
            # Today uses actual time. Preview dates use the selected report time.
            default=service.now_iso() if previous['state']['date']==service.now_iso()[:10] else previous['state']['now']
            from datetime import datetime
            clock=st.time_input('Time the change is reported',value=datetime.fromisoformat(default).time(),key='report_clock')
            if st.button('Apply change',disabled=change is None):
                now=service._at(previous['state']['date'],clock.strftime('%H:%M'))
                result=service.apply_structured_disruption(previous,change,now=now)
                if result['ok']:store_plan(previous['state']['date'],result);st.rerun()
                else:st.error('; '.join(result['violations']))
        current=current_plan()
        if current.get('explanation'):st.write(current['explanation'])
        for notice in current['notices']:st.caption(notice)
        display={'fixed_events':current['state']['fixedEvents'],'tasks':current['state']['tasks']}
        if current.get('originalPlan'):
            a,b=st.columns(2)
            with a:
                st.subheader('Before')
                original=current.get('originalState',current['state'])
                render_timeline(current['originalPlan']['blocks'],{'fixed_events':original['fixedEvents'],'tasks':original['tasks']})
            with b:st.subheader('After');render_timeline(current['plan']['blocks'],display)
        else:
            st.subheader('Current schedule');render_timeline(current['plan']['blocks'],display)
        for row in current['times']:
            if row['unscheduledMinutes']:st.warning(row['title']+': '+str(row['unscheduledMinutes'])+' minutes do not fit in this day.')


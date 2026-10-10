"""Teammate's assignments flow, plus IDs, weighting, and optional PDF review."""
from datetime import date, timedelta, time
from uuid import uuid4
import streamlit as st
from study_planner import service


def changed_assignments():
    from app_state import clear_plans
    clear_plans()


def assignments_page():
    st.subheader('My assignments')
    st.session_state.setdefault('assignments', [])
    if st.button('Load demo assignments'):
        today = date.today()
        st.session_state['assignments'] = [
            {'id': 'demo-oop', 'title': 'Programming Lab 2', 'module': 'COMP20350: OOP',
             'deadline': (today + timedelta(days=3)).isoformat(), 'status': 'In progress',
             'tasks': ['Implement classes', 'Write unit tests', 'Complete documentation'],
             'estimated_hours': 3.0, 'weighting': 30},
            {'id': 'demo-networking', 'title': 'Problem Set 3', 'module': 'COMP20320: Computer Networking',
             'deadline': (today + timedelta(days=5)).isoformat(), 'status': 'Not started',
             'tasks': ['Complete questions', 'Check calculations'], 'estimated_hours': 4.0, 'weighting': 20},
            {'id': 'demo-digital', 'title': 'Logisim Assignment 2', 'module': 'COMP20020: Digital Systems',
             'deadline': (today + timedelta(days=10)).isoformat(), 'status': 'Not started',
             'tasks': ['Write assignment', 'Use Logisim simulator', 'Review and edit'],
             'estimated_hours': 5.0, 'weighting': 40}]
        changed_assignments()
        st.success('Demo assignments loaded.')

    with st.expander('Add an assignment'):
        with st.form('assignment_form', clear_on_submit=True):
            title = st.text_input('Assignment title')
            module = st.text_input('Module (optional)')
            deadline = st.date_input('Submission deadline')
            clock = st.time_input('Submission time', value=time(23, 59))
            tasks_text = st.text_area('Tasks (one per line)')
            hours = st.number_input('Estimated hours in total', min_value=0.5, step=0.5)
            has_weight = st.checkbox('I know the module grade weighting')
            weighting = st.number_input('Module grade weighting (%)', min_value=0.0, max_value=100.0, step=1.0)
            submitted = st.form_submit_button('Save assignment')
        if submitted:
            if not title.strip():
                st.warning('Please enter an assignment title.')
            else:
                st.session_state['assignments'].append({'id': 'assignment:' + str(uuid4()),
                    'title': title.strip(), 'module': module.strip(), 'deadline': deadline.isoformat(),
                    'deadline_time': clock.strftime('%H:%M'), 'estimated_hours': hours,
                    'weighting': weighting if has_weight else None, 'status': 'Not started',
                    'tasks': [t.strip() for t in tasks_text.splitlines() if t.strip()]})
                changed_assignments()
                st.success('Assignment saved.')

    # Optional: preserve your friend's PDF feature; it isn't required for the demo.
    with st.expander('Import an assignment PDF (optional)'):
        pdf = st.file_uploader('Assignment brief', type=['pdf'])
        if st.button('Read assignment PDF', disabled=pdf is None):
            with st.spinner('Reading assignment…'):
                review = service.read_assignment(pdf.getvalue())
            st.session_state['pdf_review'] = review
        review = st.session_state.get('pdf_review')
        if review:
            for notice in review['notices']:
                st.warning(notice)
            for task in review['tasks']:
                st.write(task['title'], '—', task['estimatedMinutes'], 'minutes')
            if review['tasks'] and st.button('Accept extracted tasks'):
                for task in review['tasks']:
                    st.session_state['assignments'].append({'id': task['id'], 'title': task['title'],
                        'deadline': task['due'][:10] if task['due'] else None, 'status': 'Not started',
                        'estimated_hours': task['estimatedMinutes'] / 60, 'tasks': [], 'plannerTask': task})
                del st.session_state['pdf_review']
                changed_assignments()
                st.rerun()

    st.subheader('Your saved assignments')
    if not st.session_state['assignments']:
        st.info('Load demo assignments or add your own.')
    for assignment in st.session_state['assignments']:
        with st.expander(assignment['title'] + ' — due ' + str(assignment.get('deadline') or 'date needed')):
            st.write('Module:', assignment.get('module') or 'Personal assignment')
            st.write('Status:', assignment.get('status', 'Not started'))
            st.write('Estimated hours:', assignment['estimated_hours'])
            if assignment.get('weighting') is not None:
                st.write('Module grade weighting:', str(assignment['weighting']) + '%')
            for task in assignment['tasks']:
                st.text('• ' + task)

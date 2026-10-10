"""A one-time calendar upload, followed by a simple daily class view."""
from datetime import date, timedelta
import json
import streamlit as st
from calendar_import import import_semester, events_for_day
from timetable_store import save_timetable, load_timetable


def move_day(day_key, direction, first_day, last_day):
    # Button callbacks run before Streamlit redraws the date picker.
    current = st.session_state[day_key]
    selected = current + timedelta(days=direction)
    st.session_state[day_key] = min(max(selected, first_day), last_day)


def render_timetable_import():
    """Return the timetable for the agent; show only daily classes after import."""
    if 'semester_timetable' not in st.session_state:
        identifier = st.query_params.get('timetable')
        if identifier:
            try:
                st.session_state['semester_timetable'] = load_timetable(identifier)
            except (ValueError, OSError, json.JSONDecodeError):
                pass  # If the saved record is unavailable, show the upload form.

    timetable = st.session_state.get('semester_timetable')
    if timetable is None:
        with st.form('semester_import_form'):
            uploaded = st.file_uploader('Upload your timetable', type=['ics'])
            first, last = st.columns(2)
            start = first.date_input('Semester starts', value=date.today())
            end = last.date_input('Semester ends', value=date.today() + timedelta(weeks=12))
            submitted = st.form_submit_button('Show my classes', type='primary')
        if submitted:
            if uploaded is None:
                st.error('Choose your calendar file first.')
            elif uploaded.size > 2 * 1024 * 1024:
                st.error('Choose a file smaller than 2 MB.')
            else:
                imported = import_semester(uploaded.getvalue(), start.isoformat(), end.isoformat())
                if not imported['ok']:
                    st.error('Could not read that timetable. Check the calendar file and semester dates.')
                elif not imported['fixedEvents']:
                    st.error('No classes found. Check the semester dates.')
                else:
                    try:
                        timetable = save_timetable(imported)
                    except OSError:
                        st.error('Could not save your timetable. Please try again.')
                    else:
                        st.session_state['semester_timetable'] = timetable
                        st.query_params['timetable'] = timetable['id']
                        st.rerun()
        return None

    first_day = date.fromisoformat(timetable['semesterStart'])
    last_day = date.fromisoformat(timetable['semesterEnd'])
    default_day = min(max(date.today(), first_day), last_day)
    day_key = 'class_day_' + timetable['id']
    if day_key not in st.session_state:
        st.session_state[day_key] = default_day
    current = st.session_state[day_key]
    previous, picker, following = st.columns([1, 6, 1], vertical_alignment='bottom')
    previous.button('←', help='Previous day', disabled=current <= first_day,
                    on_click=move_day, args=(day_key, -1, first_day, last_day),
                    key='previous_' + timetable['id'], width='stretch')
    selected = picker.date_input('Day', min_value=first_day, max_value=last_day,
                                  key=day_key, label_visibility='collapsed')
    following.button('→', help='Next day', disabled=current >= last_day,
                     on_click=move_day, args=(day_key, 1, first_day, last_day),
                     key='next_' + timetable['id'], width='stretch')
    st.subheader(selected.strftime('%A, %d %B'))
    classes = events_for_day(timetable, selected.isoformat())
    if not classes:
        st.info('No classes today.')
    for event in classes:
        with st.container(border=True):
            # st.text displays imported strings as plain text.
            st.text(event['title'])
            st.text(event['start'][11:16] + ' – ' + event['end'][11:16])
            if event.get('location'):
                st.caption(event['location'])
    return timetable

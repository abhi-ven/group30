"""Run: python3 -m streamlit run app.py."""
import streamlit as st
from app_state import initialise
st.set_page_config(page_title='DayShift',page_icon='📅',layout='wide')
initialise()
pg=st.navigation([
    st.Page('dashboard.py',title='Dashboard',icon=':material/dashboard:',default=True),
    st.Page('planner.py',title='My Timetable',icon=':material/calendar_month:'),
    st.Page('assignments.py',title='Assignments',icon=':material/assignment:'),
    st.Page('rescue_page.py',title='Rescue My Day',icon=':material/refresh:')],position='hidden')
st.markdown('<style>[data-testid="stSidebar"] [data-testid="stDivider"] {margin-top:0!important;margin-bottom:0.3rem!important;} [data-testid="stSidebar"] [data-testid="stDivider"] hr {margin:0.25rem 0!important;}</style>',unsafe_allow_html=True)
with st.sidebar:
    st.page_link('dashboard.py',label='Dashboard',icon=':material/dashboard:')
    st.divider()
    st.page_link('planner.py',label='My Timetable',icon=':material/calendar_month:')
    st.page_link('assignments.py',label='Assignments',icon=':material/assignment:')
    st.page_link('rescue_page.py',label='Rescue My Day',icon=':material/refresh:')
pg.run()

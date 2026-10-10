"""Run this file: python3 -m streamlit run app.py."""
import streamlit as st
from app_state import initialise
st.set_page_config(page_title='DayShift',page_icon='📅',layout='wide')
initialise()
pg=st.navigation({'🏫 PAGES':[
    st.Page('dashboard.py',title='Dashboard',icon=':material/dashboard:',default=True),
    st.Page('planner.py',title='My Timetable',icon=':material/calendar_month:'),
    st.Page('assignments.py',title='Assignments',icon=':material/assignment:'),
    st.Page('rescue.py',title='Rescue My Day',icon=':material/refresh:')]})
pg.run()

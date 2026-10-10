import streamlit as st
from sample_data import load_sample_state

if "state" not in st.session_state:
    st.session_state.state = load_sample_state()

navigation_page = st.Page("navigation.py", title = "Navigation", icon = ":material/add:");
dashboard_page = st.Page("dashboard.py", title = "Dashboard", icon = ":material/add:")
assignments_page = st.Page("assignments.py", title = "Assignments", icon = ":material/add:")


page_2 = st.Page("page2.py", title = "page2", icon = ":material/add:")

    
pg = st.navigation(
        {
            "🏫 PAGES": [navigation_page, dashboard_page, assignments_page]
        }
    )

pg.run()
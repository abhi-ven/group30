import streamlit as st
from helper_functions import set_page, shadcn_text


def timetable_page():
    set_page("My Timetable", "Plan study time around your existing commitments.")

    if "commitments" not in st.session_state:
        st.session_state.commitments = []

    shadcn_text("Add a lecture or work shift", variant="heading")
    with st.form("commitment_form", clear_on_submit=True):
        name = st.text_input("Name (e.g. COMP101 lecture, Shift at cafe)")
        day = st.selectbox(
            "Day",
            ["Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday"],
        )
        start = st.time_input("Starts at")
        end = st.time_input("Ends at")
        added = st.form_submit_button("Add commitment")

    if added:
        if not name.strip():
            st.warning("Please give it a name.")
        elif end <= start:
            st.warning("The end time must be after the start time.")
        else:
            st.session_state.commitments.append({
                "name": name,
                "day": day,
                "start": start.strftime("%H:%M"),
                "end": end.strftime("%H:%M"),
            })
            st.success(f"Added: {name}")

    shadcn_text("Your commitments", variant="heading")
    if not st.session_state.commitments:
        st.info("None added yet.")
    for c in st.session_state.commitments:
        st.write(f"- {c['day']} {c['start']}-{c['end']}: {c['name']}")

    shadcn_text("When can you study?", variant="heading")
    study_start = st.time_input("Earliest study time", key="study_start")
    study_end = st.time_input("Latest study time", key="study_end")
    hours_per_day = st.slider("Max study hours per day", 1, 10, 4)

    if st.button("Generate study plan"):
        # The backend teammate's scheduler gets connected here later.
        st.info("Scheduler not connected yet. Your inputs are ready to send:")
        st.write({
            "commitments": st.session_state.commitments,
            "study_window": [study_start.strftime("%H:%M"),
                             study_end.strftime("%H:%M")],
            "hours_per_day": hours_per_day,
        })



timetable_page()

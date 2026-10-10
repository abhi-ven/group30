import streamlit as st
from helper_functions import set_page, shadcn_text


def assignments_page():
    st.write("HELLO FROM ASSIGNMENTS") 
    set_page("My Assignments", "Upload and organise your college assignments.")

    if "assignments" not in st.session_state:
        st.session_state.assignments = []

    pdf = st.file_uploader("Upload an assignment brief", type=["pdf"])
    if pdf is not None:
        st.success(f"Uploaded: {pdf.name}")

    shadcn_text("Assignment details", variant="heading")

    with st.form("assignment_form", clear_on_submit=True):
        title = st.text_input("Assignment title")
        deadline = st.date_input("Submission deadline")
        tasks_text = st.text_area(
            "Tasks (one per line)",
            placeholder="Read the brief\nWrite the code\nWrite the report",
        )
        hours = st.number_input("Estimated hours in total", min_value=0.5, step=0.5)
        submitted = st.form_submit_button("Save assignment")

    if submitted:
        if title.strip():
            st.session_state.assignments.append({
                "title": title,
                "deadline": str(deadline),
                "tasks": [t.strip() for t in tasks_text.split("\n") if t.strip()],
                "estimated_hours": hours,
            })
            st.success(f"Saved: {title}")
        else:
            st.warning("Please enter an assignment title.")

    shadcn_text("Your saved assignments", variant="heading")
    if not st.session_state.assignments:
        st.info("Nothing saved yet.")
    for a in st.session_state.assignments:
        with st.expander(f"{a['title']} - due {a['deadline']}"):
            st.write(f"Estimated hours: {a['estimated_hours']}")
            for t in a["tasks"]:
                st.write("-", t)
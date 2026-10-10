import streamlit as st
from helper_functions import set_page, shadcn_text


def assignments_page():
    set_page(
        "My Assignments",
        "Upload and organise your college assignments."
    )

    if "assignments" not in st.session_state:
        st.session_state.assignments = []

    # Load fake Brightspace assignments
    if st.button("Load demo assignments"):
        st.session_state.assignments = [
            {
                "title": "Programming Lab 2",
                "module": "COMP20350: OOP",
                "deadline": "2026-10-15",
                "status": "In progress",
                "tasks": [
                    "Implement classes",
                    "Write unit tests",
                    "Complete documentation"
                ],
                "estimated_hours": 3.0,
            },
            {
                "title": "Problem Set 3",
                "module": "COMP20320: Computer Networking",
                "deadline": "2026-10-17",
                "status": "Not started",
                "tasks": [
                    "Complete questions",
                    "Check calculations"
                ],
                "estimated_hours": 4.0,
            },
            {
                "title": "Logisim Assignment 2",
                "module": "COMP20020: Digital Systems",
                "deadline": "2026-10-20",
                "status": "Not started",
                "tasks": [
                    "Write assignment",
                    "Use logism simulator",
                    "Review and edit"
                ],
                "estimated_hours": 5.0,
            },
        ]
        st.success("Demo assignments loaded!")

    # Upload assignment PDF
    pdf = st.file_uploader(
        "Upload an assignment brief",
        type=["pdf"]
    )

    if pdf is not None:
        st.success(f"Uploaded: {pdf.name}")

    # Add an assignment manually
    shadcn_text("Assignment details", variant="heading")

    with st.form("assignment_form", clear_on_submit=True):
        title = st.text_input("Assignment title")
        deadline = st.date_input("Submission deadline")

        tasks_text = st.text_area(
            "Tasks (one per line)",
            placeholder="Read the brief\nWrite the code\nWrite the report",
        )

        hours = st.number_input(
            "Estimated hours in total",
            min_value=0.5,
            step=0.5
        )

        submitted = st.form_submit_button("Save assignment")

    if submitted:
        if title.strip():
            st.session_state.assignments.append({
                "title": title.strip(),
                "deadline": str(deadline),
                "tasks": [
                    t.strip()
                    for t in tasks_text.split("\n")
                    if t.strip()
                ],
                "estimated_hours": hours,
            })

            st.success(f"Saved: {title}")
        else:
            st.warning("Please enter an assignment title.")

    # Display saved assignments
    shadcn_text("Your saved assignments", variant="heading")

    if not st.session_state.assignments:
        st.info("Nothing saved yet.")

    for a in st.session_state.assignments:
        with st.expander(
            f"{a['title']} - due {a['deadline']}"
        ):
            st.write(
                f"Module: {a.get('module', 'Personal assignment')}"
            )
            st.write(
                f"Status: {a.get('status', 'Not started')}"
            )
            st.write(
                f"Estimated hours: {a['estimated_hours']}"
            )

            st.write("Tasks:")

            for task in a["tasks"]:
                st.write(f"- {task}")


assignments_page()
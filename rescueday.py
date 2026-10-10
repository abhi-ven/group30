import streamlit as st
from helper_functions import set_page, shadcn_text


def rescue_page():
    set_page("Rescue My Day", "Something went wrong? Tell us what happened and we'll re-plan.")

    disruption = st.text_area(
        "What changed?",
        placeholder="I lost two hours today because my shift ran late, "
                    "and I still need to finish my programming assignment by Friday.",
    )

    if st.button("Rescue my day"):
        if disruption.strip():
            # The AI + scheduler teammates plug in here later.
            st.info("Backend not connected yet. This is what we'd send:")
            st.write(disruption)
        else:
            st.warning("Please describe what happened first.")

    shadcn_text("Revised schedule", variant="heading")
    st.caption("The new plan, what moved, and any deadline warnings will appear here.")

rescue_page();
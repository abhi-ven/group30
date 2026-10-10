import streamlit as st
import streamlit_shadcn_ui as ui

def shadcn_text(text: str, variant: str = "heading", color: str = "navy"):
    variant_styles = {
        "title": "font-size: 30px; font-weight: 700; letter-spacing: -0.05em; margin-bottom: 8px;",
        "heading": "font-size: 20px; font-weight: 600; letter-spacing: -0.025em; margin-top: 6px; margin-bottom: 8px;",
        "subheading": "font-size: 14px; font-weight: 400; margin-bottom: 0px; line-height: 1.4;"
    }
    
    palette = {
        "navy": "#101624",
        "sky": "#a7d5ec",
        "grey": "#a4a4a4"
    }
    
    base_css = variant_styles.get(variant, variant_styles["heading"])
    chosen_color = palette.get(color, palette["navy"])

    return st.markdown(
        f"""
        <style>
        @import url('https://googleapis.com');
        .shadcn-text-block {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            width: 100%;
        }}
        </style>
        <div class="shadcn-text-block" style="{base_css} color: {chosen_color};">
            {text}
        </div>
        """,
        unsafe_allow_html=True
    )

def set_page(title, subtitle):
    shadcn_text(title, variant = "title")
    shadcn_text(subtitle, variant = "subheading", color = "grey")
    st.write("____")
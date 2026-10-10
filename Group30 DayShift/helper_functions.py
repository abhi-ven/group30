import html
import streamlit as st

def shadcn_text(text,variant='heading',color='navy'):
    size={'title':30,'heading':20,'subheading':14}.get(variant,20)
    colour={'navy':'#101624','sky':'#a7d5ec','grey':'#a4a4a4'}.get(color,'#101624')
    st.markdown(f'<div style="font-size:{size}px;color:{colour};font-weight:600;margin:8px 0">{html.escape(text)}</div>',unsafe_allow_html=True)

def set_page(title,subtitle):
    st.title(title);st.caption(subtitle)

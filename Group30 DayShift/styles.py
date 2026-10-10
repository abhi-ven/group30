import streamlit as st
ACCENT='#4F46E5'
BLOCK_COLOURS={'fixed':'#64748B','task':ACCENT,'break':'#0D9488'}
STATUS_COLOURS={'safe':'#16A34A','tight':'#D97706','at_risk':'#DC2626','done':'#64748B'}
STATUS_LABELS={'safe':'Safe','tight':'Tight','at_risk':'At risk','done':'Done'}
CHANGE_COLOURS={'moved':'#2563EB','shortened':'#D97706','added':'#16A34A','dropped':'#DC2626'}
def tint(colour,alpha=0.12):
    c=colour.lstrip('#');r,g,b=(int(c[i:i+2],16) for i in (0,2,4))
    return f'rgba({r},{g},{b},{alpha})'
def inject_css():
    st.markdown('''<style>.ds-row{display:flex;gap:14px;margin-bottom:8px}.ds-time{width:105px;flex-shrink:0;padding-top:10px;font-size:.85rem;opacity:.7}.ds-card{flex:1;border-left:4px solid;border-radius:8px;padding:10px 12px}.ds-title{font-weight:600}.ds-sub{font-size:.82rem;opacity:.7;margin-top:2px}.ds-badge{padding:1px 9px;border-radius:999px;font-size:.75rem;margin-left:8px}.ds-dropped{opacity:.55;text-decoration:line-through}.ds-now{box-shadow:0 0 0 2px #4F46E5}</style>''',unsafe_allow_html=True)

import streamlit as st
from pathlib import Path

# Color Constants (Matching CSS)
COLOR_PRIMARY = "#3B82F6"
COLOR_SECONDARY = "#60A5FA"
COLOR_CTA = "#F97316"
COLOR_BACKGROUND = "#F8FAFC"
COLOR_TEXT = "#1E293B"

def apply_theme():
    """
    Applies the global CSS styles to the Streamlit app.
    Should be called at the beginning of every page.
    """
    css_file = Path(__file__).parent / "styles.css"
    if css_file.exists():
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ UI Error: styles.css not found.")

def ui_header(title, subtitle=None):
    """
    Renders a consistent header with the new typography.
    """
    subtitle_html = ""
    if subtitle:
        subtitle_html = f'<p style="font-family: \'Atkinson Hyperlegible\', sans-serif; color: #64748B; font-size: 1.1rem;">{subtitle}</p>'
    
    st.markdown(f"""
        <div style="margin-bottom: 2rem;">
            <h1 style="font-family: 'Crimson Pro', serif; color: {COLOR_TEXT}; margin-bottom: 0.5rem;">{title}</h1>
            {subtitle_html}
        </div>
    """, unsafe_allow_html=True)

def ui_card(content, title=None):
    """
    Renders a content block wrapped in the standard card style.
    """
    html = f"""
    <div class="card">
        {f'<h3 style="margin-top:0; color: {COLOR_PRIMARY};">{title}</h3>' if title else ''}
        <div style="color: {COLOR_TEXT};">
            {content}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def ui_metric_card(label, value, delta=None):
    """
    Custom HTML metric card if st.metric isn't sufficient.
    """
    delta_html = f'<span style="color: {"#10B981" if "+" in str(delta) else "#EF4444"}; font-size: 0.9rem;">{delta}</span>' if delta else ""
    st.markdown(f"""
    <div class="card" style="padding: 1.5rem; text-align: center;">
        <div style="font-size: 0.9rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">{label}</div>
        <div style="font-size: 2rem; font-family: 'Crimson Pro', serif; font-weight: 700; color: {COLOR_CTA};">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

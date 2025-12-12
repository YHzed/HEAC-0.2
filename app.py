
import streamlit as st
from core.localization import get_text
from core.data_processor import DataProcessor
from core.analysis import Analyzer
from core.models import ModelFactory, ModelTrainer
from core.dataset_manager import DatasetManager
from core.hea_cermet import MaterialProcessor
from core.model_manager import ModelManager
from core.activity_logger import ActivityLogger

# Shared Configuration
st.set_page_config(page_title="AI Visual Lab - Home", page_icon="🏠", layout="wide")

# Initialize Shared Session State
from core.session import initialize_session_state
initialize_session_state()

def t(key):
    return get_text(key, st.session_state.language)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background-color: #f0f2f6; 
    }
    .big-font {
        font-size:30px !important;
        font-weight: bold;
        color: #333;
    }
    .card {
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        transition: 0.3s;
        border-radius: 10px;
        padding: 20px;
        background-color: white;
        margin: 10px;
        text-align: center;
        height: 100%;
    }
    .card:hover {
        box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 style='text-align: center; color: #4B4B4B;'>🏠 AI Visual Lab</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'>{t('app_desc')}</p>", unsafe_allow_html=True)

st.divider()

# Language Selector
c_lang, _ = st.columns([1, 4])
with c_lang:
    st.session_state.language = st.selectbox("Language / 语言", ["简体中文", "English"], index=0 if st.session_state.language == '简体中文' else 1)


st.write("")
st.write("")

# Navigation Cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="card">
        <h2>🤖 General ML Lab</h2>
        <p>{t('nav_data')} • {t('nav_analysis')} • {t('nav_model')}</p>
        <p>Comprehensive tools for Data Analysis, Machine Learning Model Training, and Prediction.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Enter General ML Lab", use_container_width=True):
        st.switch_page("pages/1_General_ML_Lab.py")

with col2:
    st.markdown(f"""
    <div class="card">
        <h2>🧪 HEA Cermet Lab</h2>
        <p>{t('nav_hea')}</p>
        <p>Specialized tools for High Entropy Alloy Cermets: Density, Mean Free Path, and Binder Physics.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Enter HEA Cermet Lab", use_container_width=True):
        st.switch_page("pages/2_HEA_Cermet_Lab.py")

with col3:
    st.markdown(f"""
    <div class="card">
        <h2>{t('header_library')}</h2>
        <p>{t('nav_library')}</p>
        <p>{t('library_desc')}</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button(t('nav_library'), use_container_width=True):
        st.switch_page("pages/3_Cermet_Library.py")

st.divider()

# Recent Activity
with st.expander("📝 Recent Activity Logs", expanded=True):
    logs = st.session_state.activity_logger.get_logs()
    if logs:
        for log in reversed(logs[-5:]): # Show last 5
            icon = "✅" if log['status'] == 'Success' else "❌" if log['status'] == 'Failed' else "⏳"
            st.markdown(f"**{icon} {log['activity_type']}** - {log['timestamp']}")
            if log.get('details'): st.caption(log['details'])
    else:
        st.info("No activity recorded yet.")

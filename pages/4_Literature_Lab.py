
import streamlit as st
import os
import pandas as pd
from core.literature.manager import LibraryManager
from core.localization import get_text

# Initialize Manager
@st.cache_resource
def get_manager():
    return LibraryManager()

manager = get_manager()

# Localization Logic
if 'language' not in st.session_state:
    st.session_state.language = 'English'

def t(key):
    return get_text(key, st.session_state.language)

st.set_page_config(page_title=t('lit_title'), page_icon="📚", layout="wide")

st.title("📚 " + t('lit_title'))

# Sidebar for Navigation / Actions
with st.sidebar:
    st.header(t('lit_actions'))
    
    # Map keys to display strings for Radio Button
    mode_options = {
        'lit_upload_analyze': t('lit_upload_analyze'),
        'lit_db_view': t('lit_db_view'),
        'lit_search_sim': t('lit_search_sim')
    }
    
    # Helper to reverse lookup key from display string (for logic)
    # OR just use keys as values and format_func for display
    
    selected_mode_key = st.radio(
        t('lit_mode'), 
        options=list(mode_options.keys()), 
        format_func=lambda x: mode_options[x]
    )

if selected_mode_key == 'lit_upload_analyze':
    st.header(t('lit_header_upload'))
    uploaded_file = st.file_uploader(t('lit_choose_file'), type=['pdf', 'txt'])
    
    if uploaded_file is not None:
        if st.button(t('lit_analyze_btn')):
            with st.spinner(t('lit_analyzing')):
                # Save temp file
                temp_path = os.path.join("datasets", uploaded_file.name)
                # Ensure datasets dir exists
                os.makedirs("datasets", exist_ok=True)
                
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Analyze
                try:
                    record = manager.process_file(temp_path)
                    st.success(t('lit_success_analysis'))
                    
                    st.subheader(t('lit_text_preview'))
                    st.text_area("Text", record['text_preview'], height=150)
                    
                    st.subheader(t('lit_analysis_results'))
                    st.json(record['analysis'])
                    
                    if st.button(t('lit_save_lib')):
                        manager.add_to_library(record)
                        st.success(t('lit_save_success'))
                except Exception as e:
                    st.error(t('lit_error_analysis').format(e))
                    import traceback
                    st.text(traceback.format_exc())

elif selected_mode_key == 'lit_db_view':
    st.header(t('lit_header_db'))
    
    records = manager.extracted_data
    if not records:
        st.info(t('lit_no_records'))
    else:
        df = pd.DataFrame(records)
        st.dataframe(df)

elif selected_mode_key == 'lit_search_sim':
    st.header(t('lit_header_search'))
    
    formula = st.text_input(t('lit_enter_formula'))
    top_n = st.slider(t('lit_top_n'), 1, 10, 5)
    
    if st.button(t('lit_search_btn')):
        if formula:
            results = manager.analyzer.find_similar_materials(formula, topn=top_n)
            if results:
                st.write(t('lit_sim_result').format(formula))
                for mat, score in results:
                    st.write(f"- **{mat}**: {score:.4f}")
            else:
                st.warning(t('lit_no_result'))
        else:
            st.warning(t('lit_warn_formula'))

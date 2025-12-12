import streamlit as st
import json
import pandas as pd
import os
from core.localization import get_text
from core.session import initialize_session_state

# ==============================================================================
# INITIALIZATION
# ==============================================================================
initialize_session_state()

def t(key):
    return get_text(key, st.session_state.language)

st.set_page_config(page_title=t('nav_library'), page_icon="📚", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    h1 { color: #4B4B4B; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# DATA LOADING
# ==============================================================================
@st.cache_data
def load_json_data(filename):
    file_path = os.path.join(os.path.dirname(__file__), '..', 'core', 'data', filename)
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Data file not found: {filename}")
        return {}

elements_data = load_json_data('elements.json')
enthalpy_data = load_json_data('enthalpy.json')
compounds_data = load_json_data('compounds.json')

# ==============================================================================
# MAIN PAGE
# ==============================================================================
st.markdown(f"<h1>{t('header_library')}</h1>", unsafe_allow_html=True)
st.markdown(t('lib_intro'))
st.divider()

# Tabs
tab_elem, tab_enth, tab_cer, tab_proc = st.tabs([
    t('tab_elements'), 
    t('tab_enthalpy'), 
    t('tab_ceramic'), 
    t('tab_process')
])

# ------------------------------------------------------------------------------
# TAB 1: ELEMENTS
# ------------------------------------------------------------------------------
with tab_elem:
    st.subheader(t('tab_elements'))
    
    if elements_data:
        # Convert JSON structure { "Al": {...}, "Co": {...} } to DataFrame
        # Flatten the dictionary
        rows = []
        for el, props in elements_data.items():
            row = {'Element': el}
            row.update(props)
            rows.append(row)
        
        df_elem = pd.DataFrame(rows)
        
        # Map JSON keys (lowercase/snake_case) to Display keys
        df_elem = df_elem.rename(columns={
            'mass': 'AtomicWeight',
            'r': 'AtomicRadius',
            'vec': 'VEC',
            'electronegativity_pauling': 'Electronegativity',
            'melting_point': 'MeltingPoint'
        })
        
        col_map = {
            'Element': t('col_element'),
            'AtomicWeight': t('col_atomic_weight'),
            'AtomicRadius': t('col_radius'),
            'VEC': t('col_vec'),
            'Electronegativity': t('col_electronegativity'),
            'MeltingPoint': t('col_melting')
        }
        
        # Select only relevant columns
        cols_to_show = ['Element', 'AtomicWeight', 'AtomicRadius', 'VEC', 'Electronegativity', 'MeltingPoint']
        
        # Filter (ensure columns exist)
        cols_to_show = [c for c in cols_to_show if c in df_elem.columns]
        df_elem = df_elem[cols_to_show].rename(columns=col_map)
        
        st.dataframe(df_elem, use_container_width=True, hide_index=True)
    else:
        st.warning("No element data available.")

# ------------------------------------------------------------------------------
# TAB 2: ENTHALPY (Existing Logic)
# ------------------------------------------------------------------------------
with tab_enth:
    st.subheader(t('enthalpy_data'))
    search_term = st.text_input("🔍", placeholder=t('search_placeholder'), key="search_enth")

    if enthalpy_data:
        df_enthalpy = pd.DataFrame(list(enthalpy_data.items()), columns=['Pair', 'Enthalpy (kJ/mol)'])

        if search_term:
            df_enthalpy = df_enthalpy[df_enthalpy['Pair'].str.contains(search_term, case=False)]

        col1, col2 = st.columns([2, 1])
        with col1:
            st.dataframe(df_enthalpy, use_container_width=True, hide_index=True)
        with col2:
            st.info(t('library_desc'))
    else:
        st.warning("No enthalpy data available.")

# ------------------------------------------------------------------------------
# TAB 3: CERAMICS
# ------------------------------------------------------------------------------
with tab_cer:
    st.subheader(t('tab_ceramic'))
    
    if compounds_data:
        # Expected structure: { "WC": { "density": 15.63, "enthalpy": -40.0 } }
        rows_c = []
        for cmp, props in compounds_data.items():
            row = {'Compound': cmp}
            row.update(props)
            rows_c.append(row)
            
        df_cer = pd.DataFrame(rows_c)
        
        # Keys in JSON are lowercase 'density'
        df_cer = df_cer.rename(columns={'density': 'Density'})
        
        # Rename
        col_map_c = {
            'Compound': t('col_compound'),
            'Density': t('col_density')
        }
        
        # Filter and Rename
        available_cols = [c for c in ['Compound', 'Density'] if c in df_cer.columns or c == 'Compound']
        df_cer = df_cer[available_cols].rename(columns=col_map_c)
        
        st.dataframe(df_cer, use_container_width=True, hide_index=True)
        
        st.info("Currently focusing on WC (Tungsten Carbide) as the primary reinforcement phase.")
    else:
        st.warning("No ceramic data available.")

# ------------------------------------------------------------------------------
# TAB 4: PROCESS PARAMETERS
# ------------------------------------------------------------------------------
with tab_proc:
    st.subheader(t('tab_process'))
    
    # Manual table for process parameters used in Single Point Analysis
    process_data = [
        {
            "Parameter": t('param_temp'),
            "Description": "Sintering Temperature (T)",
            "Typical Choice": "1200 - 1600 °C"
        },
        {
            "Parameter": t('param_time'),
            "Description": "Sintering Time (t)",
            "Typical Choice": "30 - 240 min"
        },
        {
            "Parameter": t('param_grain'),
            "Description": "Initial Grain Size of Ceramic Phase",
            "Typical Choice": "0.1 - 10.0 µm"
        },
        {
            "Parameter": t('param_vol'),
            "Description": "Volume Fraction of Ceramic Phase",
            "Typical Choice": "10% - 90%"
        }
    ]
    
    df_proc = pd.DataFrame(process_data)
    # Rename columns for display
    df_proc.columns = [t('process_param'), t('process_desc'), t('process_range')]
    
    st.table(df_proc)

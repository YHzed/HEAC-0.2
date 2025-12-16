import streamlit as st
import json
import pandas as pd
import os

# 统一导入core模块
from core import get_text, initialize_session_state, db

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
elements_data = db.get_all_elements()
enthalpy_data = db.get_all_enthalpy_data()
compounds_data = db.get_all_compounds()
heac_library = db.get_heac_library()

# ==============================================================================
# MAIN PAGE
# ==============================================================================
st.markdown(f"<h1>{t('header_library')}</h1>", unsafe_allow_html=True)
st.markdown(t('lib_intro'))
st.divider()

# Tabs
# Tabs
tab_elem, tab_enth, tab_cer, tab_proc, tab_heac = st.tabs([
    t('tab_elements'), 
    t('tab_enthalpy'), 
    t('tab_ceramic'), 
    t('tab_process'),
    "HEAC Database (MP)"
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
        
        # 修复数据类型：将所有数值列转换为float，避免int和str混合比较错误
        numeric_cols_elem = ['AtomicWeight', 'AtomicRadius', 'VEC', 'Electronegativity', 'MeltingPoint']
        for col in numeric_cols_elem:
            if col in df_elem.columns:
                df_elem[col] = pd.to_numeric(df_elem[col], errors='coerce')
        
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
        
        # 修复数据类型：将Enthalpy列转换为float
        df_enthalpy['Enthalpy (kJ/mol)'] = pd.to_numeric(df_enthalpy['Enthalpy (kJ/mol)'], errors='coerce')

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
        
        # 修复数据类型：将Density列转换为float
        if 'Density' in df_cer.columns:
            df_cer['Density'] = pd.to_numeric(df_cer['Density'], errors='coerce')
        
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

# ------------------------------------------------------------------------------
# TAB 5: HEAC MP LIBRARY
# ------------------------------------------------------------------------------
with tab_heac:
    st.subheader("HEAC Materials Project Database")
    st.markdown("Comprehensive database of transition metal carbides, nitrides, and borides fetched from Materials Project.")
    
    if heac_library:
        materials = heac_library
        
        # Flatten for table
        rows_hea = []
        for mid, props in materials.items():
            # Basic info
            row = {
                'ID': mid,
                'Formula': props.get('formula_pretty'),
                'Density': props.get('density'),
                'Structure': props.get('symmetry', {}).get('crystal_system'),
                'Formation E': props.get('formation_energy_per_atom'),
                'Is Stable': props.get('is_stable'),
            }
            # Calculated Props
            row['VEC'] = props.get('vec')
            row['delta'] = props.get('delta_size_diff')
            row['H_mix'] = props.get('mixing_enthalpy')
            row['Omega'] = props.get('omega')
            
            # Mechanical (if available)
            row['Bulk Modulus'] = props.get('bulk_modulus')
            row['Shear Modulus'] = props.get('shear_modulus')
            row['Hv (Est)'] = props.get('hardness_chen')
            
            rows_hea.append(row)
            
        df_hea = pd.DataFrame(rows_hea)
        
        # 彻底修复数据类型问题：强制转换所有列
        # 1. 字符串列：强制转换为str类型
        string_columns = ['ID', 'Formula', 'Structure']
        for col in string_columns:
            if col in df_hea.columns:
                df_hea[col] = df_hea[col].fillna('N/A').astype(str)
        
        # 2. 布尔列：转换为字符串
        if 'Is Stable' in df_hea.columns:
            df_hea['Is Stable'] = df_hea['Is Stable'].map({True: 'Yes', False: 'No', None: 'Unknown'})
        
        # 3. 数值列：转换为float
        numeric_columns = ['Density', 'Formation E', 'VEC', 'delta', 'H_mix', 'Omega', 
                          'Bulk Modulus', 'Shear Modulus', 'Hv (Est)']
        for col in numeric_columns:
            if col in df_hea.columns:
                df_hea[col] = pd.to_numeric(df_hea[col], errors='coerce')
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            search_formula = st.text_input("Search Formula", placeholder="e.g., TiC", key="search_heac")
        with col2:
            st.info(f"Total Entries: {len(df_hea)}")
            
        if search_formula:
            df_hea = df_hea[df_hea['Formula'].str.contains(search_formula, case=False, na=False)]
            
        # Display
        st.dataframe(
            df_hea, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Formation E": st.column_config.NumberColumn("Formation E (eV/atom)", format="%.3f"),
                "Density": st.column_config.NumberColumn("Density (g/cm³)", format="%.2f"),
                "VEC": st.column_config.NumberColumn("VEC", format="%.1f"),
                "H_mix": st.column_config.NumberColumn("H_mix (kJ/mol)", format="%.1f"),
                "Omega": st.column_config.NumberColumn("Omega", format="%.1f"),
                "Hv (Est)": st.column_config.NumberColumn("Hv (GPa)", format="%.1f"),
            }
        )
    else:
        st.warning("HEAC Library not found or empty. Please run the build script.")



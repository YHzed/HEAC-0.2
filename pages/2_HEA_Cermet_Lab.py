
import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

from core.data_processor import DataProcessor
from core.localization import get_text
from core.dataset_manager import DatasetManager
from core.hea_cermet import MaterialProcessor
from core.activity_logger import ActivityLogger

# Import Core Architecture for Advanced Tabs
from core.system_architecture import DesignSpace, PhysicsEngine, AIPredictor, InverseOptimizer

# Page Config
st.set_page_config(page_title="HEA Cermet Lab", page_icon="🧪", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    .main-header { font-size: 2rem; color: #4B4B4B; text-align: center; }
    .stButton>button { color: white; background-color: #007bff; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# Initialization
from core.session import initialize_session_state
initialize_session_state()

def t(key):
    return get_text(key, st.session_state.language)

# Sidebar
with st.sidebar:
    st.title("🧪 HEA Cermet Lab")
    st.session_state.language = st.selectbox("Language / 语言", ["简体中文", "English"], index=0 if st.session_state.language == '简体中文' else 1)
    st.divider()
    st.info(t('hea_intro'))

# Main Content
st.markdown(f"<h1 class='main-header'>{t('header_hea')}</h1>", unsafe_allow_html=True)

# Tabs
tab_batch, tab_single, tab_inverse = st.tabs([t('mode_batch'), t('tab_single'), t('tab_inverse')])

# ==============================================================================
# TAB 1: BATCH PROCESSOR (Original functionality)
# ==============================================================================
with tab_batch:
    st.subheader(t('mode_batch'))
    
    # Option: Use Main Data or Upload
    use_main = st.checkbox("Use Main Dataset (from General ML Lab)", value=False)
    
    df_batch = None
    if use_main:
        if st.session_state.data_processor.data is not None:
            df_batch = st.session_state.data_processor.data
        else:
            st.warning(t('warning_upload'))
    else:
        uploaded = st.file_uploader(t('batch_upload'), type=['csv', 'xlsx'])
        if uploaded:
            try:
                df_batch = pd.read_csv(uploaded) if uploaded.name.endswith('csv') else pd.read_excel(uploaded)
            except Exception as e:
                st.error(f"Error: {e}")
    
    if df_batch is not None:
        st.dataframe(df_batch.head())
        
        c1, c2, c3 = st.columns(3)
        formula_col = c1.selectbox(t('select_formula_col'), df_batch.columns)
        
        is_cermet = st.checkbox("Enable Cermet Calculations (Mean Free Path)", value=False)
        is_wt_pct = st.checkbox("Interpret Formula as Weight Percent?", value=False)
        
        grain_col = None
        default_grain = 1.0
        
        if is_cermet:
            if st.checkbox("Use Grain Size Column?", value=False):
                grain_col = c2.selectbox("Select Grain Size Column (um)", df_batch.columns)
            else:
                default_grain = c2.number_input("Default Grain Size (um)", 0.1, 100.0, 1.0)
                
        if st.button(t('process_batch')):
            with st.spinner("Processing..."):
                try:
                    res = st.session_state.material_processor.process_batch_extended(
                        df_batch, formula_col, 
                        grain_size_col=grain_col, 
                        particle_size_default=default_grain,
                        is_weight_percent=is_wt_pct
                    )
                    st.subheader(t('calc_results'))
                    st.dataframe(res)
                    st.download_button(t('download_results'), res.to_csv(index=False).encode('utf-8'), 'hea_cermet_properties.csv', 'text/csv')
                    st.session_state.activity_logger.log_activity("HEA Processing", f"Rows: {len(res)}", "Success")
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.session_state.activity_logger.log_activity("HEA Processing", "Batch", "Failed", str(e))

# ==============================================================================
# TAB 2: SINGLE POINT ANALYSIS (From HEAC Framework)
# ==============================================================================
with tab_single:
    st.header(t('header_single'))
    
    # Input
    c_s1, c_s2 = st.columns([1, 2])
    
    with c_s1:
        st.subheader(t('hea_binder_comp'))
        c_co = st.slider("Co (Cobalt)", 0.0, 2.0, 1.0, 0.1)
        c_ni = st.slider("Ni (Nickel)", 0.0, 2.0, 1.0, 0.1)
        c_fe = st.slider("Fe (Iron)", 0.0, 2.0, 1.0, 0.1)
        c_cr = st.slider("Cr (Chromium)", 0.0, 2.0, 0.5, 0.1)
        c_mo = st.slider("Mo (Molybdenum)", 0.0, 1.0, 0.2, 0.1)
        
        st.subheader(t('microstructure'))
        vol_wc = st.slider(t('wc_vol_frac'), 10.0, 90.0, 50.0, 5.0) / 100.0
        grain_size = st.number_input(t('grain_size_label'), 0.1, 10.0, 1.0, 0.1, key='sp_grain')
        
        st.subheader(t('sintering_process'))
        temp = st.slider(t('temp_label'), 1200, 1600, 1400, 10)
        time = st.slider(t('time_label'), 30, 240, 60, 10)

    # Logic
    total_atomic = c_co + c_ni + c_fe + c_cr + c_mo
    if total_atomic == 0:
        st.warning(t('total_atomic_zero'))
    else:
        design = DesignSpace(
            hea_composition={'Co': c_co, 'Ni': c_ni, 'Fe': c_fe, 'Cr': c_cr, 'Mo': c_mo},
            ceramic_composition={'WC': 1.0},
            ceramic_vol_fraction=vol_wc,
            grain_size_um=grain_size,
            sinter_temp_c=temp,
            sinter_time_min=time
        )
        
        engine = PhysicsEngine()
        features = engine.compute_features(design)
        vol_stats = engine.calculate_volume_fractions(design)
        
        with c_s2:
            st.subheader(t('physics_output'))
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("VEC", f"{features['VEC']:.3f}", help=t('vec_help'))
            col2.metric("Lattice Mismatch", f"{features['Lattice_Mismatch']*100:.2f}%", help=t('mismatch_help'))
            col3.metric("Wettability", f"{features['Wettability_Index']:.2f}", help=t('wettability_help'))
            col4.metric("Homologous T", f"{features['T_homologous']:.2f}", help=t('homologous_help'))
            
            with st.expander(t('detailed_vol_frac'), expanded=True):
                v_col1, v_col2 = st.columns(2)
                with v_col1:
                    st.write(f"**{t('phase_dist')}**")
                    df_phase = pd.DataFrame({
                        "Phase": ["Ceramic (WC)", "Binder (HEA)"],
                        "Vol%": [vol_stats['Phase_Ceramic']*100, vol_stats['Phase_Binder']*100]
                    })
                    st.dataframe(df_phase, hide_index=True)
                with v_col2:
                    st.write(f"**{t('element_dist')}**")
                    el_data = []
                    for k, v in vol_stats.items():
                        if 'Elem_Vol_' in k:
                            el_data.append({"Element": k.replace('Elem_Vol_', ''), "Vol%": v*100})
                    st.dataframe(pd.DataFrame(el_data), hide_index=True)

            st.divider()
            st.divider()
            st.subheader(t('ai_pred'))
            predictor = AIPredictor()
            preds = predictor.predict(features)
            
            p_col1, p_col2, p_col3 = st.columns(3)
            p_col1.metric(t('pred_hv'), f"{preds['Predicted_HV']:.0f}")
            p_col2.metric(t('pred_k1c'), f"{preds['Predicted_K1C']:.2f}")
            p_col3.metric(t('interface_quality'), f"{preds['Interface_Quality']:.2f}")

# ==============================================================================
# TAB 3: INVERSE DESIGN (From HEAC Framework)
# ==============================================================================
with tab_inverse:
    st.header(t('header_inverse'))
    st.info(t('inverse_goal'))
    
    if st.button(t('run_opt'), type="primary"):
        with st.spinner(t('opt_running')):
            optimizer = InverseOptimizer()
            best_trials = optimizer.optimize(n_trials=20)
            
            st.success(t('opt_success').format(len(best_trials)))
            
            results = []
            for trial in best_trials:
                row = trial.params.copy()
                row['Predicted_HV'] = trial.values[0]
                row['Predicted_K1C'] = trial.values[1]
                results.append(row)
                
            df_opt = pd.DataFrame(results)
            st.dataframe(df_opt.style.highlight_max(axis=0, color='lightgreen'))
            
            if not df_opt.empty:
                fig = px.scatter(df_opt, x='Predicted_HV', y='Predicted_K1C', 
                                 color='Co', size='Ni',
                                 title=t('pareto_front'),
                                 hover_data=df_opt.columns)
                st.plotly_chart(fig)

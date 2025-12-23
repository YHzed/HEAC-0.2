
import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# 统一导入core模块
from core import (
    DataProcessor, 
    get_text, DatasetManager,
    MaterialProcessor, 
    ActivityLogger,
    initialize_session_state
)
# 导入高级架构组件
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
    
    # Input Layout
    c_s1, c_s2 = st.columns([1, 2])
    
    with c_s1:
        st.subheader("1. Design Inputs")
        
        # 1.1 Composition Mode
        use_mass = st.toggle("Input by Mass %", value=False, help="Toggle between Atomic Ratio and Mass Percent")
        label_suffix = "(wt%)" if use_mass else "(at ratio)"
        
        # 1.2 HEA Composition
        st.markdown(f"**Binder Composition {label_suffix}**")
        c_co = st.slider(f"Co {label_suffix}", 0.0, 2.0, 1.0, 0.1)
        c_ni = st.slider(f"Ni {label_suffix}", 0.0, 2.0, 1.0, 0.1)
        c_fe = st.slider(f"Fe {label_suffix}", 0.0, 2.0, 1.0, 0.1)
        c_cr = st.slider(f"Cr {label_suffix}", 0.0, 2.0, 0.5, 0.1)
        c_mo = st.slider(f"Mo {label_suffix}", 0.0, 1.0, 0.2, 0.1)
        
        # 1.3 Ceramic & Stickiness
        st.markdown("**Ceramic Phase**")
        ceramic_type = st.selectbox("Ceramic Type", ["WC", "TiC"])
        
        vol_wc = st.slider(t('wc_vol_frac').replace('WC', ceramic_type), 10.0, 90.0, 50.0, 5.0) / 100.0
        grain_size = st.number_input(t('grain_size_label'), 0.1, 10.0, 1.0, 0.1, key='sp_grain')
        
        # 1.4 Process
        st.markdown("**Process Parameters**")
        proc_route = st.selectbox("Process Route", ["Vacuum Sintering", "HIP", "Sinter-HIP", "Spark Plasma Sintering"])
        temp = st.slider(t('temp_label'), 1200, 1600, 1400, 10)
        time = st.slider(t('time_label'), 30, 240, 60, 10)

    # Logic Implementation
    total_comp = c_co + c_ni + c_fe + c_cr + c_mo
    if total_comp == 0:
        st.warning(t('total_atomic_zero'))
    else:
        # Create DesignSpace Object
        design = DesignSpace(
            hea_composition={'Co': c_co, 'Ni': c_ni, 'Fe': c_fe, 'Cr': c_cr, 'Mo': c_mo},
            is_mass_fraction=use_mass,
            ceramic_type=ceramic_type,
            ceramic_vol_fraction=vol_wc,
            grain_size_um=grain_size,
            sinter_temp_c=temp,
            sinter_time_min=time,
            process_route=proc_route
        )
        
        # Instantiate System Engines
        engine = PhysicsEngine()
        features = engine.compute_features(design)
        vol_stats = engine.calculate_volume_fractions(design)
        
        with c_s2:
            # ------------------------------------------------------------------
            # SECTION 2: PHYSICS ENGINE RESULTS
            # ------------------------------------------------------------------
            st.subheader(t('physics_output'))
            
            # Row 1: Key Physics Indicators
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("VEC", f"{features['VEC']:.2f}", help="Valence Electron Concentration (>8.0 ~ Ductile)")
            p2.metric(f"Mismatch ({ceramic_type})", f"{features['Lattice_Mismatch']*100:.2f}%", help=f"Lattice mismatch with {ceramic_type}")
            p3.metric("Homologous T", f"{features['T_Homologous']:.2f}", help="Sintering T / Liquidus T")
            p4.metric("Mixing Enthalpy", f"{features['H_mix']:.1f} kJ", help="Enthalpy of Mixing")

            # Row 2: Secondary Physics
            p5, p6, p7, p8 = st.columns(4)
            p5.metric("CTE Mismatch", f"{features['CTE_Mismatch']:.1f}", help="Delta CTE (Binder vs Ceramic)")
            p6.metric("Liquidus (Est)", f"{features['T_Liquidus_Est']-273.15:.0f} °C", help="Estimated Liquidus with Eutectic Depression")
            p7.metric("Mixing Entropy", f"{features['S_mix']:.1f} R", help="Entropy of mixing")
            p8.metric("Atomic Size Diff", f"{features['Delta_R']:.1f}%", help="Atomic size difference")
            
            with st.expander(t('detailed_vol_frac'), expanded=False):
                v_col1, v_col2 = st.columns(2)
                with v_col1:
                    st.write(f"**{t('phase_dist')}**")
                    df_phase = pd.DataFrame({
                        "Phase": [f"Ceramic ({ceramic_type})", "Binder (HEA)"],
                        "Vol%": [vol_stats['Phase_Ceramic']*100, vol_stats['Phase_Binder']*100]
                    })
                    st.dataframe(df_phase, hide_index=True)
                with v_col2:
                    st.write(f"**{t('element_dist')} (Composite)**")
                    el_data = []
                    for k, v in vol_stats.items():
                        if 'Elem_Vol_' in k:
                            el_data.append({"Element": k.replace('Elem_Vol_', ''), "Vol%": v*100})
                    st.dataframe(pd.DataFrame(el_data), hide_index=True)

            st.divider()
            
            # ------------------------------------------------------------------
            # SECTION 3: ML PREDICTION RESULTS
            # ------------------------------------------------------------------
            st.subheader("3. AI Prediction System")
            
            predictor = AIPredictor()
            
            # 捕获警告并显示给用户
            import warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                # 传递design对象以支持ModelX和ModelY预测
                preds = predictor.predict(design)
                
                # 如果有警告，显示给用户
                if w:
                    for warning in w:
                        st.warning(f"⚠️ {warning.message}")
            
            # Performance Metrics
            m1, m2 = st.columns(2)
            
            # HV
            hv_src = preds.get('HV_Source', 'Unknown')
            # 根据来源设置delta标签
            if 'ModelX' in hv_src:
                delta_hv = "🎯 ModelX"
            elif "ML" in hv_src:
                delta_hv = "ML"
            else:
                delta_hv = "Heuristic"
            m1.metric(t('pred_hv'), f"{preds['Predicted_HV']:.0f} HV", delta=delta_hv, help=f"Source: {hv_src}")
            
            # K1C
            k1c_src = preds.get('K1C_Source', 'Unknown')
            # 支持ModelY来源
            if 'ModelY' in k1c_src:
                delta_k1c = "🎯 ModelY"
            elif "ML" in k1c_src:
                delta_k1c = "ML"
            else:
                delta_k1c = "Heuristic"
            m2.metric(t('pred_k1c'), f"{preds['Predicted_K1C']:.2f} MPa·m½", delta=delta_k1c, help=f"Source: {k1c_src}")
            
            # Phase Stability Analysis
            st.markdown("**Phase Composition Analysis (AI)**")
            phase_analysis = preds.get('Phase_Analysis', 'N/A')
            if "No ML Model" in str(phase_analysis):
                st.warning(f"⚠️ {phase_analysis} - Please train a model in the Model Zoo to activate this feature.")
            else:
                st.success(f"✅ {phase_analysis}")


# ==============================================================================
# TAB 3: INVERSE DESIGN (From HEAC Framework)
# ==============================================================================
with tab_inverse:
    st.header(t('header_inverse'))
    st.info(t('inverse_goal'))
    
    # 优化参数
    n_trials = st.slider("优化迭代次数 (Trials)", 20, 100, 50, 10, 
                         help="使用ModelX时建议50+次迭代以充分探索设计空间")
    
    if st.button(t('run_opt'), type="primary"):
        with st.spinner(t('opt_running')):
            optimizer = InverseOptimizer()
            best_trials = optimizer.optimize(n_trials=n_trials)
            
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

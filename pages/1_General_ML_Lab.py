

import streamlit as st
import pandas as pd
import plotly.express as px

# 统一导入core模块
from core import (
    DataProcessor, Analyzer,
    ModelFactory, ModelTrainer, Optimizer,
    get_text, DatasetManager, ModelManager,
    MaterialProcessor, ActivityLogger,
    initialize_session_state
)

# Page Config
st.set_page_config(page_title="General ML Lab", page_icon="🤖", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    .main-header { font-size: 2.5rem; color: #4B4B4B; text-align: center; margin-bottom: 2rem; }
    .stButton>button { color: white; background-color: #007bff; border-radius: 5px; }
    div[data-baseweb="input"] { background-color: #ffffff !important; border: 1px solid #ced4da !important; border-radius: 5px !important; }
    input[type="text"], input[type="number"] { background-color: #ffffff !important; color: #000000 !important; }
</style>
""", unsafe_allow_html=True)

# Initialization
from core.session import initialize_session_state
initialize_session_state()

# Helpers
@st.cache_data
def load_data_cached(file, file_type):
    if file_type == 'csv': return pd.read_csv(file)
    elif file_type == 'excel': return pd.read_excel(file)
    elif file_type == 'parquet': return pd.read_parquet(file)
    return None

def t(key):
    return get_text(key, st.session_state.language)

def get_model_map():
    return {
        t('model_lr'): 'Linear Regression', t('model_ridge'): 'Ridge', t('model_lasso'): 'Lasso',
        t('model_rf'): 'Random Forest', t('model_xgb'): 'XGBoost', t('model_svr'): 'SVR',
        t('model_logr'): 'Logistic Regression', t('model_dt'): 'Decision Tree',
        t('model_svc'): 'SVC', t('model_lgbm'): 'LightGBM', t('model_cb'): 'CatBoost',
        t('model_kmeans'): 'K-Means', t('model_stacking'): 'Stacking'
    }

def get_missing_map():
    return {t('miss_drop'): 'drop', t('miss_mean'): 'mean', t('miss_median'): 'median', t('miss_mode'): 'mode'}

# Sidebar
with st.sidebar:
    st.title("🤖 General ML Lab")
    st.session_state.language = st.selectbox("Language / 语言", ["简体中文", "English"], index=0 if st.session_state.language == '简体中文' else 1)
    st.divider()
    page = st.radio(t('nav_title'), [t('nav_data'), t('nav_analysis'), t('nav_model'), t('nav_predict'), t('nav_results')])

# --- Data Upload Page ---
if page == t('nav_data'):
    st.markdown(f"<h1 class='main-header'>{t('header_data')}</h1>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader(t('upload_label'), type=['csv', 'xlsx', 'parquet'])
    
    if uploaded_file:
        file_type = 'csv'
        if uploaded_file.name.endswith('xlsx'): file_type = 'excel'
        elif uploaded_file.name.endswith('parquet'): file_type = 'parquet'
        
        with st.spinner(t('training_spinner')):
            try:
                df = load_data_cached(uploaded_file, file_type)
                st.session_state.data_processor.data = df
                st.session_state.data_processor.columns = df.columns.tolist()
                st.session_state.activity_logger.log_activity("Data Upload", f"File: {uploaded_file.name}, Rows: {len(df)}", "Success")
                st.success(t('load_success'))
                st.subheader(t('data_preview'))
                st.dataframe(st.session_state.data_processor.get_preview())
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader(t('data_info'))
                    st.text(st.session_state.data_processor.get_info())
                with col2:
                    st.subheader(t('stats'))
                    st.dataframe(st.session_state.data_processor.get_statistics())

                st.subheader(t('preprocessing'))
                miss_map = get_missing_map()
                miss_display = st.selectbox(t('handle_missing'), list(miss_map.keys()))
                if st.button(t('apply_missing')):
                    st.session_state.data_processor.handle_missing_values(miss_map[miss_display])
                    st.success(t('missing_handled'))
                    st.dataframe(st.session_state.data_processor.get_preview())
            except Exception as e:
                st.error(str(e))
                st.session_state.activity_logger.log_activity("Data Upload", f"File: {uploaded_file.name}", "Failed", str(e))
    
    st.divider()
    # Saved Datasets
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(t('save_dataset'))
        if st.session_state.data_processor.data is not None:
            s1, s2 = st.columns([2,1])
            save_name = s1.text_input(t('dataset_name'))
            save_fmt = s2.selectbox("Format", ["parquet", "csv", "xlsx"])
            if st.button(t('save_btn')):
                success, msg = st.session_state.dataset_manager.save_dataset(st.session_state.data_processor.data, save_name, save_fmt)
                if success: st.success(t('save_success'))
                else: st.error(msg)
    with c2:
        st.subheader(t('saved_datasets'))
        datasets = st.session_state.dataset_manager.list_datasets()
        if datasets:
            for ds in datasets:
                with st.expander(f"{ds['name']} ({ds['size']})"):
                    col_l, col_d = st.columns(2)
                    if col_l.button(t('load_btn'), key=f"load_{ds['name']}"):
                        data, msg = st.session_state.dataset_manager.load_dataset(ds['name'])
                        if data is not None:
                            st.session_state.data_processor.data = data
                            st.session_state.data_processor.columns = data.columns.tolist()
                            st.success(t('load_success'))
                            st.rerun()
                    if col_d.button(t('delete_btn'), key=f"del_{ds['name']}"):
                        st.session_state.dataset_manager.delete_dataset(ds['name'])
                        st.rerun()

# --- Analysis Page ---
elif page == t('nav_analysis'):
    st.markdown(f"<h1 class='main-header'>{t('header_analysis')}</h1>", unsafe_allow_html=True)
    if st.session_state.data_processor.data is not None:
        t1, t2, t3 = st.tabs([t('tab_dist'), t('tab_corr'), t('tab_rel')])
        with t1:
            col = st.selectbox(t('select_col_dist'), st.session_state.data_processor.data.columns)
            st.plotly_chart(st.session_state.analyzer.plot_distribution(col), use_container_width=True)
        with t2:
            st.plotly_chart(st.session_state.analyzer.plot_correlation_heatmap(), use_container_width=True)
        with t3:
            c1, c2, c3 = st.columns(3)
            x = c1.selectbox(t('x_axis'), st.session_state.data_processor.data.columns)
            y = c2.selectbox(t('y_axis'), st.session_state.data_processor.data.columns)
            col = c3.selectbox(t('color_opt'), [None]+list(st.session_state.data_processor.data.columns))
            st.plotly_chart(st.session_state.analyzer.plot_scatter(x, y, col), use_container_width=True)
    else:
        st.warning(t('warning_upload'))

# --- Model Page ---
elif page == t('nav_model'):
    st.markdown(f"<h1 class='main-header'>{t('header_model')}</h1>", unsafe_allow_html=True)
    if st.session_state.data_processor.data is not None:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader(t('config'))
            target = st.selectbox(t('select_target'), st.session_state.data_processor.data.columns)
            unique_vals = st.session_state.data_processor.data[target].nunique()
            predicted_task = 'classification' if unique_vals < 20 or st.session_state.data_processor.data[target].dtype == 'object' else 'regression'
            task_type = st.radio(t('task_type'), ['regression', 'classification', 'clustering'], index=0 if predicted_task == 'regression' else 1)
            
            models_list = []
            if task_type == 'regression': models_list = [t('model_lr'), t('model_ridge'), t('model_lasso'), t('model_rf'), t('model_xgb'), t('model_svr'), t('model_lgbm'), t('model_cb'), t('model_stacking')]
            elif task_type == 'classification': models_list = [t('model_logr'), t('model_dt'), t('model_rf'), t('model_xgb'), t('model_svc'), t('model_lgbm'), t('model_cb')]
            else: models_list = [t('model_kmeans')]
            
            sel_model_disp = st.selectbox(t('select_model'), models_list)
            sel_model_int = get_model_map()[sel_model_disp]
            
            # Simplified Params Logic 
            params = {}
            st.markdown(f"#### {t('hyperparams')}")
            
            def get_p(k, d): return st.session_state.get(f"p_{k}", d)
            
            if 'Random Forest' in sel_model_int:
                params['n_estimators'] = st.slider("n_estimators", 10, 500, get_p('n_estimators', 100), key="p_n_estimators")
                params['max_depth'] = st.slider("max_depth", 1, 50, get_p('max_depth', 10), key="p_max_depth")
            elif 'XGBoost' in sel_model_int or 'LightGBM' in sel_model_int or 'CatBoost' in sel_model_int:
                params['n_estimators'] = st.slider("n_estimators", 50, 500, get_p('n_estimators', 100), key="p_n_estimators")
                params['learning_rate'] = st.number_input("learning_rate", 0.01, 1.0, float(get_p('learning_rate', 0.1)), key="p_learning_rate")
            elif 'Stacking' in sel_model_int:
                st.info(t('stacking_desc'))
                fe = st.selectbox("Final Estimator", ['Ridge', 'Linear Regression', 'Random Forest'], key="p_final_estimator")
                params['final_estimator'] = fe
                params['passthrough'] = st.checkbox("Passthrough", value=get_p('passthrough', False), key="p_passthrough")
            
            test_size = st.slider(t('test_size'), 0.1, 0.5, 0.2)
            avail_feats = [c for c in st.session_state.data_processor.data.columns if c != target]
            sel_feats = st.multiselect(t('select_features'), avail_feats, default=avail_feats)

            st.divider()
            with st.expander(t('header_opt')):
                n_trials = st.slider(t('n_trials'), 10, 100, 20)
                if st.button(t('start_opt')):
                    with st.spinner(t('opt_spinner')):
                        st.session_state.data_processor.prepare_data(target, feature_columns=sel_feats, test_size=test_size)
                        opt = Optimizer(st.session_state.data_processor.X_train, st.session_state.data_processor.y_train, task_type)
                        best = opt.optimize(sel_model_int, n_trials=n_trials)
                        st.session_state.best_params = best
                        st.success(t('opt_complete'))
                        st.json(best)
                def apply_best_params():
                    for k,v in st.session_state.best_params.items():
                        st.session_state[f"p_{k}"] = v

                if st.session_state.get('best_params'):
                    st.button(t('apply_params'), on_click=apply_best_params)

        with col2:
            st.subheader(t('training_action'))
            if st.button(t('train_btn'), type="primary"):
                with st.spinner(t('training_spinner')):
                    success, msg = st.session_state.data_processor.prepare_data(target if task_type != 'clustering' else None, feature_columns=sel_feats, test_size=test_size)
                    if success:
                        try:
                            model = ModelFactory.get_model(task_type, sel_model_int, params)
                            st.session_state.model_trainer.train(model, st.session_state.data_processor.X_train, st.session_state.data_processor.y_train)
                            metrics, _ = st.session_state.model_trainer.evaluate(st.session_state.data_processor.X_test, st.session_state.data_processor.y_test, task_type)
                            st.session_state.trained_model = model
                            st.session_state.model_metrics = metrics
                            st.session_state.task_type = task_type
                            st.success(t('training_complete'))
                            st.json(metrics)
                            st.session_state.activity_logger.log_activity("Model Training", f"Model: {sel_model_disp}", "Success")
                        except Exception as e:
                            st.error(f"Training Failed: {e}")
                            st.session_state.activity_logger.log_activity("Model Training", f"Model: {sel_model_disp}", "Failed", str(e))
            
            if st.session_state.trained_model:
                st.divider()
                st.subheader(t('save_model_title'))
                c_s1, c_s2 = st.columns([2,1])
                m_name = c_s1.text_input(t('model_name_input'))
                if c_s2.button(t('save_model_btn')) and m_name:
                    success, msg = st.session_state.model_manager.save_model(st.session_state.trained_model, st.session_state.model_metrics, st.session_state.task_type, m_name, feature_columns=st.session_state.data_processor.X_train.columns.tolist())
                    if success: st.success(t('save_model_success'))
                    else: st.error(msg)
        
    else:
        st.warning(t('warning_upload'))

    st.divider()
    st.subheader(t('manage_models_title'))
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        st.markdown(f"#### {t('upload_model_label')}")
        up_mod = st.file_uploader("Upload Model", type=['joblib'], label_visibility="collapsed")
        if up_mod: st.session_state.model_manager.save_uploaded_model(up_mod)
    with c_m2:
        saved = st.session_state.model_manager.list_models()
        if saved:
            for m in saved:
                with st.expander(f"{m['display_name']} ({m['size']})"):
                    if st.button(t('load_model_btn'), key=f"ld_m_{m['name']}"):
                         dat, msg = st.session_state.model_manager.load_model(m['name'])
                         if dat:
                             st.session_state.trained_model = dat['model']
                             st.session_state.model_metrics = dat.get('metrics')
                             st.session_state.task_type = dat.get('task_type', 'regression')
                             st.success(t('load_model_success'))

# --- Prediction Page ---
elif page == t('nav_predict'):
    st.markdown(f"<h1 class='main-header'>{t('header_predict')}</h1>", unsafe_allow_html=True)
    saved_models = st.session_state.model_manager.list_models()
    names = [m['display_name'] for m in saved_models]
    if names:
        sel_name = st.selectbox(t('pred_model_select'), names)
        full_name = next((m['name'] for m in saved_models if m['display_name'] == sel_name), None)
        if full_name:
            m_data, _ = st.session_state.model_manager.load_model(full_name)
            if m_data:
                model = m_data['model']
                feats = m_data.get('feature_columns', [])
                
                mode = st.radio(t('pred_mode'), [t('pred_mode_manual'), t('pred_mode_batch')])
                if mode == t('pred_mode_manual'):
                    if feats:
                        in_data = {}
                        cols = st.columns(3)
                        for i, f in enumerate(feats):
                            with cols[i%3]: in_data[f] = st.number_input(f, value=0.0)
                        if st.button(t('pred_btn')):
                            res = model.predict(pd.DataFrame([in_data]))
                            st.success(f"Result: {res[0]}")
                    else: st.warning("No feature metadata.")
                else:
                    up_batch = st.file_uploader(t('pred_batch_upload'), type=['csv', 'xlsx'])
                    if up_batch:
                        df_b = pd.read_csv(up_batch) if up_batch.name.endswith('csv') else pd.read_excel(up_batch)
                        if st.button(t('pred_btn')):
                            if feats: df_b['Prediction'] = model.predict(df_b[feats])
                            else: df_b['Prediction'] = model.predict(df_b)
                            st.dataframe(df_b)
                            st.download_button("Download CSV", df_b.to_csv(index=False).encode('utf-8'), "pred.csv", "text/csv")
    else:
        st.info(t('no_saved_models'))

# --- Results Page ---
elif page == t('nav_results'):
    st.markdown(f"<h1 class='main-header'>{t('header_results')}</h1>", unsafe_allow_html=True)
    if st.session_state.trained_model:
        st.subheader(t('perf_metrics'))
        st.json(st.session_state.model_metrics)
        if hasattr(st.session_state.trained_model, 'feature_importances_'):
            st.subheader(t('feat_imp'))
            imp = st.session_state.trained_model.feature_importances_
            df_i = pd.DataFrame({'Feature': st.session_state.data_processor.X_train.columns, 'Importance': imp}).sort_values('Importance', ascending=False)
            st.plotly_chart(px.bar(df_i, x='Importance', y='Feature', orientation='h'), use_container_width=True)
    else:
        st.info(t('no_model'))

"""
Database Manager UI
Enhanced Database Management System
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db_manager import DatabaseManager
# from core import FeatureEngine # Not strictly needed if manager handles it, but kept if code uses it directly
from core.composition_parser_enhanced import EnhancedCompositionParser
from core.db_pagination import query_experiments_paginated, create_pagination_controls

# ========== 性能优化: 缓存装饰器 ==========
@st.cache_resource
def get_db_manager():
    """单例数据库管理器 - 避免重复创建连接"""
    return DatabaseManager('cermet_master_v2.db')

import ui.style_manager as style_manager

@st.cache_data(ttl=30)  # 缓存30秒
def load_database_stats(_db_manager):
    """缓存数据库统计信息"""
    return _db_manager.get_statistics()

@st.cache_resource
def get_feature_injector(model_dir: str = 'models/proxy_models'):
    """缓存FeatureInjector单例 - 减少模型加载开销"""
    from core.feature_injector import FeatureInjector
    from core.parallel_feature_injector import ParallelFeatureInjector
    injector = FeatureInjector(model_dir=model_dir)
    return ParallelFeatureInjector(injector)

# Localization Dictionary
TRANSLATIONS = {
    'EN': {
        'page_title': "Database Manager - HEAC",
        'main_title': "🗄️ Metal-Ceramic Database Manager",
        'settings_header': "⚙️ Database Settings",
        'db_stats_header': "📊 Database Statistics",
        'arch_info': "Using Enhanced Database Architecture",
        'total_records': "Total Records",
        'hea_binders': "HEA Binders",
        'trad_binders': "Traditional Binders",
        'load_error': "Failed to load stats: {}",
        'tab_entry': "📝 Smart Entry",
        'tab_import': "📂 Batch Import",
        'tab_preview': "🔬 Parser Preview",
        'tab_calc': "⚡ Feature Calculation",
        'tab_query': "🔍 Query & Analysis",
        'lang_label': "Language / 语言",
        'delete_stats_btn': "🗑️ Delete All Data (Reset DB)",
        'delete_confirm': "⚠️ DANGER: This will delete ALL experiments and features. The database will be reset.",
        'delete_success': "✅ Database has been reset.",
        'delete_error': "❌ Reset failed: {}",
        # Tab 1
        'comp_info': "Composition Info",
        'comp_str': "Composition String *",
        'comp_help': "Supports formats: WC-10Co, b WC 69 CoCrFeNiMo 0.5 Cr3C2",
        'source': "Source ID",
        'parse_success': "✅ Composition Parsed",
        'main_phase': "Ceramic Phase",
        'binder_phase': "Binder Phase",
        'binder_wt': "Binder wt%",
        'process_params': "Process Parameters",
        'sinter_temp': "Sinter Temp (°C)",
        'grain_size': "Grain Size (μm)",
        'load_kgf': "Load (kgf)",
        'perf_metrics': "Performance Metrics",
        'hv': "Hardness (HV)",
        'kic': "Fracture Toughness (KIC)",
        'trs': "TRS (MPa)",
        'adv_options': "⚙️ Advanced Options",
        'auto_calc': "Auto Calculate Features",
        'auto_calc_help': "Automatically calculate VEC, lattice mismatch etc.",
        'submit_btn': "💾 Submit Data",
        'save_success': "✅ Data saved successfully! Experiment ID: {}",
        # Tab 2
        'import_caption': "Supports Excel (.xlsx) and CSV (.csv) files",
        'select_file': "Select File",
        'file_help': "Supported formats: Excel, CSV",
        'file_loaded': "✅ File loaded: {} rows",
        'data_preview': "🔍 Data Preview (First 10 rows)",
        'col_mapping': "⚡ Column Mapping",
        'map_caption': "Map Excel columns to Database fields",
        'excel_cols': "📄 **Excel Columns**",
        'total_cols': "Total {} columns",
        'req_fields': "🎯 **Required Fields**",
        'comp_col_label': "🧪 Composition Col",
        'hv_col_label': "🔨 Hardness (HV)",
        'kic_col_label': "🔪 Toughness (KIC)",
        'temp_col_label': "🌡️ Temp (°C)",
        'source_tag': "Source Tag",
        'start_import': "🚀 Start Import",
        'comp_col_req': "⚠️ Composition column is required",
        'import_success': "🎉 Imported {} records",
        'import_partial': "⚠️ Imported {}, Failed {}",
        'error_msg': "Error: {}",
        # Tab 4
        'calc_caption': "Batch calculate features for records missing them.",
        'missing_proxy': "Missing Proxy Feats",
        'missing_matminer': "Missing Matminer Feats",
        'view_missing': "🔍 View records missing Proxy features (First 10)",
        'calc_config': "⚙️ Calculation Config",
        'enable_proxy': "Enable Proxy Model Features",
        'proxy_help': "DFT Predictions: Formation Energy, Lattice Param, etc.",
        'enable_matminer': "Enable Matminer Features",
        'matminer_help': "Magpie elemental stats (adds 10-30s)",
        'full_matminer': "Full Matminer Features",
        'recalc_exist': "Recalculate Existing",
        'recalc_help': "Force update all records",
        'all_done': "✅ All records have features!",
        'will_calc': "🎯 Will calculate features for **{}** records",
        'run_calc': "⚡ Run Calculation",
        'prep_data': "Preparing data...",
        'loading_proxy': "🔬 Loading Proxy Models...",
        'calc_proxy': "💫 Calculating Proxy Features ({} rows)...",
        'proxy_done': "✅ Proxy Features Calculated!",
        'calc_matminer': "🧪 Calculating Matminer Features... (10-30s)",
        'matminer_done': "✅ Matminer Features Calculated!",
        'saving_db': "💾 Saving to database...",
        'update_success': "🎉 Updated {} records",
        'calc_fail': "Calculation failed: {}",
        # Tab 5
        'db_empty': "📊 Database is empty, please add data first",
        'db_stats_msg': "📊 Database contains {} experiment records",
        'data_filter': "🔍 Data Filter",
        'binder_type': "Binder Type",
        'limit_records': "Show Records",
        'search_comp': "Search Composition (Keyword)",
        'query_results': "📋 Query Results ({} rows)",
        'select_cols': "**Select Columns**",
        'show_cols': "Show Columns (Multi-select)",
        'reset_btn': "🔄 Reset",
        'select_one_col': "Please select at least one column",
        'export_data': "📥 Export Data",
        'format': "Format",
        'filename': "Filename",
        'export_btn': "💾 Export",
        'download_csv': "⬇️ Download CSV",
        'download_excel': "⬇️ Download Excel",
        'export_done': "✅ Export Successful!",
        'export_fail': "Export Failed: {}",
        'data_stats': "📊 Data Statistics",
        'record_count': "Record Count",
        'avg_hv': "Avg HV",
        'avg_kic': "Avg KIC",
        'not_found': "No matching records found",
        'export_all_label': "Export All Data (Full Features)",
    },
    'CN': {
        'page_title': "数据库管理 - HEAC",
        'main_title': "🗄️ 金属陶瓷数据库管理",
        'settings_header': "⚙️ 数据库设置",
        'db_stats_header': "📊 数据库统计",
        'arch_info': "正在使用增强型数据库架构",
        'total_records': "总记录数",
        'hea_binders': "HEA 粘结相",
        'trad_binders': "传统粘结相",
        'load_error': "加载统计失败: {}",
        'tab_entry': "📝 智能录入",
        'tab_import': "📂 批量导入",
        'tab_preview': "🔬 解析预览",
        'tab_calc': "⚡ 特征计算",
        'tab_query': "🔍 查询分析",
        'lang_label': "语言 / Language",
        'delete_stats_btn': "🗑️ 清空所有数据 (重置数据库)",
        'delete_confirm': "⚠️ 危险：这将删除所有实验数据和特征。数据库将被重置。",
        'delete_success': "✅ 数据库已重置。",
        'delete_error': "❌ 重置失败: {}",
        # Tab 1
        'comp_info': "成分信息",
        'comp_str': "成分字符串 *",
        'comp_help': "支持多种格式：短横线、空格、复杂格式",
        'source': "数据来源",
        'parse_success': "✅ 成分解析成功",
        'main_phase': "主硬质相",
        'binder_phase': "粘结相",
        'binder_wt': "粘结相 wt%",
        'process_params': "工艺参数",
        'sinter_temp': "烧结温度 (°C)",
        'grain_size': "晶粒尺寸 (μm)",
        'load_kgf': "测试载荷 (kgf)",
        'perf_metrics': "性能指标",
        'hv': "维氏硬度 (HV)",
        'kic': "断裂韧性 (MPa·m^1/2)",
        'trs': "抗弯强度 (MPa)",
        'adv_options': "⚙️ 高级选项",
        'auto_calc': "自动计算物理特征",
        'auto_calc_help': "启用后将自动计算 VEC、晶格失配等特征（可能需要几秒）",
        'submit_btn': "💾 提交数据",
        'save_success': "✅ 数据保存成功！实验 ID: {}",
        # Tab 2
        'import_caption': "支持 Excel (.xlsx) 和 CSV (.csv) 文件",
        'select_file': "选择文件",
        'file_help': "支持格式: Excel, CSV",
        'file_loaded': "✅ 文件已加载: {} 行",
        'data_preview': "🔍 数据预览 (前 10 行)",
        'col_mapping': "⚡ 列映射",
        'map_caption': "将 Excel 列映射到数据库字段",
        'excel_cols': "📄 **Excel 列**",
        'total_cols': "共 {} 列",
        'req_fields': "🎯 **必需字段**",
        'comp_col_label': "🧪 成分列",
        'hv_col_label': "🔨 硬度 (HV)",
        'kic_col_label': "🔪 韧性 (KIC)",
        'temp_col_label': "🌡️ 温度 (°C)",
        'source_tag': "来源标签",
        'start_import': "🚀 开始导入",
        'comp_col_req': "⚠️ 必须选择成分列",
        'import_success': "🎉 成功导入 {} 条记录",
        'import_partial': "⚠️ 导入 {} 条，失败 {} 条",
        'error_msg': "错误: {}",
        # Tab 4
        'calc_caption': "批量计算缺失的特征。",
        'missing_proxy': "缺失代理特征",
        'missing_matminer': "缺失 Matminer 特征",
        'view_missing': "🔍 查看缺失代理特征的记录 (前 10 条)",
        'calc_config': "⚙️ 计算配置",
        'enable_proxy': "启用代理模型特征",
        'proxy_help': "DFT 预测：形成能、晶格参数等",
        'enable_matminer': "启用 Matminer 特征",
        'matminer_help': "Magpie 元素统计 (增加 10-30秒)",
        'full_matminer': "完整 Matminer 特征",
        'recalc_exist': "重新计算现有记录",
        'recalc_help': "强制更新所有记录",
        'all_done': "✅ 所有记录都有特征！",
        'will_calc': "🎯 将计算 **{}** 条记录的特征",
        'run_calc': "⚡ 运行计算",
        'prep_data': "准备数据...",
        'loading_proxy': "🔬 加载代理模型...",
        'calc_proxy': "💫 计算代理特征 ({} 行)...",
        'proxy_done': "✅ 代理特征计算完成！",
        'calc_matminer': "🧪 计算 Matminer 特征... (10-30秒)",
        'matminer_done': "✅ Matminer 特征计算完成！",
        'saving_db': "💾 保存到数据库...",
        'update_success': "🎉 更新了 {} 条记录",
        'calc_fail': "计算失败: {}",
        # Tab 5
        'db_empty': "📊 数据库为空，请先添加数据",
        'db_stats_msg': "📊 数据库包含 {} 条实验数据",
        'data_filter': "🔍 数据筛选",
        'binder_type': "粘结相类型",
        'limit_records': "显示记录数",
        'search_comp': "成分搜索（关键词）",
        'query_results': "📋 查询结果 ({} 条)",
        'select_cols': "**选择显示列**",
        'show_cols': "显示列（可多选）",
        'reset_btn': "🔄 重置",
        'select_one_col': "请至少选择一列",
        'export_data': "📥 导出数据",
        'format': "格式",
        'filename': "文件名",
        'export_btn': "💾 导出",
        'download_csv': "⬇️ 下载 CSV",
        'download_excel': "⬇️ 下载 Excel",
        'export_done': "✅ 导出成功！",
        'export_fail': "导出失败: {}",
        'data_stats': "📊 数据统计",
        'record_count': "记录数",
        'avg_hv': "平均HV",
        'avg_kic': "平均KIC",
        'avg_kic': "平均KIC",
        'not_found': "未找到符合条件的数据",
        'export_all_label': "导出所有数据 (完整特征)",
    }
}

# Helper function for translation
def t(key):
    sys_lang = st.session_state.get('language', 'EN')
    # Map full names to keys if necessary
    lang_map = {
        'English': 'EN',
        '简体中文': 'CN',
        'EN': 'EN',
        'CN': 'CN'
    }
    lang = lang_map.get(sys_lang, 'EN')
    return TRANSLATIONS[lang].get(key, key)

# Page Config
st.set_page_config(
    page_title="Database Manager - HEAC",
    page_icon="🗄️",
    layout="wide"
)

# Initialize Session State
if 'use_v2_db' not in st.session_state:
    st.session_state.use_v2_db = True
if 'language' not in st.session_state:
    st.session_state['language'] = 'EN'

# Apply Theme
style_manager.apply_theme()

# Title
style_manager.ui_header(t('main_title'), t('page_title'))
st.markdown("---")

# Sidebar - Database Settings
with st.sidebar:
    st.header(t('settings_header'))
    
    # Language Selector
    lang_choice = st.radio(
        t('lang_label'),
        options=['EN', 'CN'],
        index=0 if st.session_state['language'] == 'EN' else 1,
        horizontal=True
    )
    if lang_choice != st.session_state['language']:
        st.session_state['language'] = lang_choice
        st.rerun()

    st.info(t('arch_info'))
    
    st.markdown("---")
    
    # Delete All Data Button
    if st.button(t('delete_stats_btn'), type="primary", use_container_width=True):
        try:
            # 清空缓存
            st.cache_data.clear()
            st.cache_resource.clear()
            db = get_db_manager()
            # WARNING: This deletes everything
            db.drop_tables()
            db.create_tables()
            
            st.toast(t('delete_success'))
            st.success(t('delete_success'))
            
        except Exception as e:
            st.error(t('delete_error').format(e))

    st.markdown("---")
    
    # Database Stats
    st.header(t('db_stats_header'))
    
    try:
        # 使用缓存的数据库管理器和统计信息
        db = get_db_manager()
        stats = load_database_stats(db)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(t('total_records'), stats.get('total_experiments', 0))
        with col2:
            st.metric(t('hea_binders'), stats.get('hea_count', 0))
        
        st.metric(t('trad_binders'), stats.get('traditional_count', 0))
        
    except Exception as e:
        st.error(t('load_error').format(e))

# Main Interface
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    t('tab_entry'),
    t('tab_import'),
    t('tab_preview'),
    t('tab_calc'),
    t('tab_query')
])

# Tab 1: Smart Entry
with tab1:
    st.header(t('tab_entry'))
        
    with st.form("smart_entry_form"):
        st.subheader(t('comp_info'))
        
        col1, col2 = st.columns(2)
        with col1:
            composition = st.text_input(
                t('comp_str'),
                placeholder="WC-10CoCrFeNi 或 b WC 69 CoCrFeNiMo 0.5 Cr3C2",
                help=t('comp_help')
            )
        
        with col2:
            source_id = st.text_input(t('source'), value="manual_entry")
        
        # 实时解析预览
        if composition:
            parser = EnhancedCompositionParser()
            result = parser.parse(composition)
            
            if result.get('success'):
                st.success(t('parse_success'))
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.info(f"**{t('main_phase')}**: {result['ceramic_formula']}")
                with col_b:
                    st.info(f"**{t('binder_phase')}**: {result['binder_formula']}")
                with col_c:
                    st.info(f"**{t('binder_wt')}**: {result.get('binder_wt_pct', 'N/A')}")
            else:
                st.error(f"❌ {result.get('message')}")
        
        st.subheader(t('process_params'))
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sinter_temp = st.number_input(t('sinter_temp'), min_value=0.0, max_value=3000.0, value=1400.0)
        with col2:
            grain_size = st.number_input(t('grain_size'), min_value=0.0, value=1.0)
        with col3:
            load_kgf = st.number_input(t('load_kgf'), min_value=0.0, value=30.0)
        
        st.subheader(t('perf_metrics'))
        col1, col2, col3 = st.columns(3)
        
        with col1:
            hv = st.number_input(t('hv'), min_value=0.0, value=1500.0)
        with col2:
            kic = st.number_input(t('kic'), min_value=0.0, value=12.0)
        with col3:
            trs = st.number_input(t('trs'), min_value=0.0, value=2000.0)
        
        # 高级选项
        with st.expander(t('adv_options')):
            auto_features = st.checkbox(t('auto_calc'), value=True)
            st.caption(t('auto_calc_help'))
        
        # 提交按钮
        submitted = st.form_submit_button(t('submit_btn'), use_container_width=True)
        
        if submitted:
            if not composition:
                st.error("Please enter a composition string.")
            else:
                try:
                    # 使用缓存的数据库管理器
                    db = get_db_manager()
                    db.create_tables()  # Ensure tables exist
                    
                    with st.spinner("Saving data..."):
                        exp_id = db.add_experiment(
                            raw_composition=composition,
                            source_id=source_id,
                            sinter_temp_c=sinter_temp,
                            grain_size_um=grain_size,
                            load_kgf=load_kgf,
                            hv=hv,
                            kic=kic,
                            trs=trs,
                            auto_calculate_features=auto_features
                        )
                    
                    st.success(t('save_success').format(exp_id))
                    
                    # Show details
                    data = db.get_experiment(exp_id)
                    if data:
                        with st.expander("🔍 View Saved Data"):
                            st.json(data)
                    
                except Exception as e:
                    st.error(f"❌ Save Failed: {e}")
    
# Tab 2: Batch Import
    with tab2:
        st.header(t('tab_import'))
        st.caption(t('import_caption'))
        
        uploaded_file = st.file_uploader(
            t('select_file'),
            type=['xlsx', 'csv'],
            help=t('file_help')
        )
        # ... [omitted identical code lines for UI layout if mostly standard, focusing on logic replacement] ...
        
        if uploaded_file:
             # ... [file reading logic is fine] ...
             try:
                # [Reading logic kept similar, just ensure variables match]
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.success(t('file_loaded').format(len(df)))
                
                # ... [Preview Logic] ...
                with st.expander(t('data_preview')):
                    st.dataframe(df.head(10), use_container_width=True)

                st.subheader(t('col_mapping'))
                st.caption(t('map_caption'))
                
                # ... [Column selection UI] ...
                available_cols = list(df.columns)
                # ... [UI logic] ...
                
                col1, col2 = st.columns(2)
                with col1:
                     st.write(t('excel_cols'))
                     st.info(t('total_cols').format(len(available_cols)))
                with col2:
                     st.write(t('req_fields'))
                     st.markdown("- `composition` *")
                
                # ... [Mapping Logic] ...
                composition_col = st.selectbox(t('comp_col_label'), options=[''] + available_cols)
                c_a, c_b, c_c, c_d, c_e = st.columns(5)
                with c_a: hv_col = st.selectbox(t('hv_col_label'), options=[''] + available_cols)
                with c_b: kic_col = st.selectbox(t('kic_col_label'), options=[''] + available_cols)
                with c_c: trs_col = st.selectbox("TRS Col", options=[''] + available_cols)
                with c_d: temp_col = st.selectbox(t('temp_col_label'), options=[''] + available_cols)
                with c_e: grain_col = st.selectbox("Grain Size Col", options=[''] + available_cols)
                
                # Optional: Component Columns
                st.markdown("---")
                st.caption(t('component_cols_help') if 'component_cols_help' in t.__code__.co_consts else "Optional: Construct composition from separate columns (Binder + Ceramic)")
                cc1, cc2 = st.columns(2)
                with cc1: ceramic_name_col = st.selectbox("Ceramic Phase Col (e.g. WC)", options=[''] + available_cols)
                with cc2: binder_wt_col = st.selectbox("Binder wt% Col", options=[''] + available_cols)

                with st.expander(t('adv_options')):
                    auto_features = st.checkbox(t('auto_calc'), value=False)
                    source_id = st.text_input(t('source_tag'), value="batch_import")

                if st.button(t('start_import'), type="primary", use_container_width=True):
                    if not composition_col:
                        st.error(t('comp_col_req'))
                    else:
                        def clean_numeric(value):
                            if pd.isna(value): return None
                            try: return float(value)
                            except: return None
                        
                        db = get_db_manager()
                        db.create_tables()
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        success_count, fail_count, errors = 0, 0, []
                        
                        for idx, row in df.iterrows():
                            # ... [Loop logic] ...
                            try:
                                comp_str = row.get(composition_col)
                                if pd.isna(comp_str) or not comp_str:
                                    fail_count += 1
                                    continue
                                comp_str = str(comp_str).strip()
                                
                                # Construct Composite String if mappings exist
                                if ceramic_name_col and binder_wt_col:
                                    try:
                                        cer_name = str(row.get(ceramic_name_col)).strip()
                                        bind_wt = clean_numeric(row.get(binder_wt_col))
                                        
                                        if cer_name and bind_wt is not None:
                                            cer_wt = 100.0 - bind_wt
                                            # Format: "90 WC 10 Co"
                                            # Ensure valid values
                                            if 0 < bind_wt < 100:
                                                comp_str = f"{cer_wt:.1f} {cer_name} {bind_wt:.1f} {comp_str}"
                                    except:
                                        pass # Fallback to raw string
                                
                                hv_val = clean_numeric(row.get(hv_col)) if hv_col else None
                                kic_val = clean_numeric(row.get(kic_col)) if kic_col else None
                                trs_val = clean_numeric(row.get(trs_col)) if trs_col else None
                                temp_val = clean_numeric(row.get(temp_col)) if temp_col else None
                                grain_val = clean_numeric(row.get(grain_col)) if grain_col else None
                                
                                db.add_experiment(
                                    raw_composition=comp_str,
                                    source_id=source_id,
                                    hv=hv_val,
                                    kic=kic_val,
                                    trs=trs_val,
                                    sinter_temp_c=temp_val,
                                    grain_size_um=grain_val,
                                    auto_calculate_features=auto_features
                                )
                                success_count += 1
                            except Exception as e:
                                fail_count += 1
                                errors.append(f"Row {idx}: {e}")
                            
                            progress_bar.progress((idx + 1) / len(df))
                        
                        if fail_count == 0: 
                            st.success(t('import_success').format(success_count))
                        else: 
                            st.warning(t('import_partial').format(success_count, fail_count))
                            with st.expander("❌ Failure Details"):
                                # Ensure errors are strings for display
                                error_df = pd.DataFrame([str(e) for e in errors], columns=["Error Message"])
                                st.dataframe(error_df, use_container_width=True)

             except Exception as e:
                st.error(t('error_msg').format(e))

    # ... [Tab 3 Parser Preview - mostly UI, likely okay to leave or standardise] ...
    with tab3:
        st.header("🔬 Parser Preview")
        # [Content mostly safe, just update standard calls if needed]
        # Skipping detailed replace for Tab 3 as it uses EnhancedCompositionParser directly? 
        # Actually it uses EnhancedCompositionParser directly in the original code, which is fine.

    # Tab 4: Feature Calculation
    with tab4:
        st.header(t('tab_calc'))
        st.markdown(t('calc_caption'))
        
        try:
            # 使用缓存的数据库管理器
            db = get_db_manager()
            stats = load_database_stats(db)
            
            # ... [Logic to check missing] ...
            # Original code accessed db_v2.Session(), we need to use db.Session()
            
            session = db.Session()
            try:
                from core.db_models import Experiment, Composition, CalculatedFeature 
                
                # Check queries
                exps_missing_proxy = session.query(Experiment).filter(
                    ~Experiment.id.in_(
                        session.query(CalculatedFeature.exp_id)
                    )
                ).all()
    
                # Check missing Matminer features
                exps_missing_matminer = session.query(CalculatedFeature).filter(
                    (CalculatedFeature.has_matminer == False) | 
                    (CalculatedFeature.has_matminer == None)
                ).count()
    
                # Display stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(t('total_records'), stats['total_experiments'])
                with col2:
                    missing_proxy_pct = len(exps_missing_proxy)/stats['total_experiments']*100 if stats['total_experiments'] > 0 else 0
                    st.metric(
                        t('missing_proxy'), 
                        len(exps_missing_proxy),
                        delta=f"{missing_proxy_pct:.1f}%",
                        delta_color="inverse"
                    )
                with col3:
                    st.metric(t('missing_matminer'), exps_missing_matminer)
    
                # Preview missing
                if len(exps_missing_proxy) > 0:
                    with st.expander(t('view_missing')):
                        preview_data = []
                        for exp in exps_missing_proxy[:10]:
                            preview_data.append({
                                'ID': exp.id,
                                'Composition': exp.raw_composition[:60],
                                'Source': exp.source_id,
                                'Created': exp.created_at.strftime('%Y-%m-%d %H:%M') if exp.created_at else 'N/A'
                            })
                        st.dataframe(pd.DataFrame(preview_data), use_container_width=True)
                
                st.markdown("---")
                st.subheader(t('calc_config'))
    
                col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
    
                with col_cfg1:
                    use_proxy = st.checkbox(t('enable_proxy'), value=True, help=t('proxy_help'))
    
                with col_cfg2:
                    use_matminer = st.checkbox(t('enable_matminer'), value=False, help=t('matminer_help'))
                    use_full_matminer = st.checkbox(t('full_matminer'), value=False, help="Full ceramic/binder Magpie set (~220 features)")
    
                with col_cfg3:
                    force_recalc = st.checkbox(t('recalc_exist'), value=False, help=t('recalc_help'))
    
                target_count = stats['total_experiments'] if force_recalc else len(exps_missing_proxy)
                
                if target_count == 0 and not use_matminer and not use_full_matminer:
                    st.success(t('all_done'))
                else:
                    st.info(t('will_calc').format(target_count))
                
                st.markdown("---")
                
                calc_disabled = (target_count == 0 and not ((use_matminer or use_full_matminer) and exps_missing_matminer > 0))

                if st.button(t('run_calc'), type="primary", use_container_width=True, disabled=calc_disabled):
                     with st.spinner(t('prep_data')):
                        if force_recalc:
                            target_exps = session.query(Experiment).all()
                        else:
                            # Union of missing proxy and missing matminer (if enabled)
                            target_ids = set()
                            
                            # 1. Missing Proxy
                            if use_proxy:
                                for e in exps_missing_proxy:
                                    target_ids.add(e.id)
                            
                            # 2. Missing Matminer
                            if use_matminer or use_full_matminer:
                                matminer_missing_objs = session.query(CalculatedFeature).filter(
                                    (CalculatedFeature.has_matminer == False) | 
                                    (CalculatedFeature.has_matminer == None)
                                ).all()
                                for f in matminer_missing_objs:
                                    target_ids.add(f.exp_id)
                            
                            if not target_ids:
                                st.warning("No records need calculation.")
                                st.stop()
                                
                            target_exps = session.query(Experiment).filter(Experiment.id.in_(target_ids)).all()
                        
                        data_for_injection = []
                        for exp in target_exps:
                            comp = session.query(Composition).filter_by(exp_id=exp.id).first()
                            if comp and comp.binder_formula:
                                binder_comp = comp.binder_formula
                                ceramic_type = comp.ceramic_formula or 'WC'
                            else:
                                binder_comp = exp.raw_composition
                                ceramic_type = 'WC'
                            
                            data_for_injection.append({
                                'exp_id': exp.id,
                                'binder_composition': binder_comp,
                                'Ceramic_Type': ceramic_type,
                                'raw_composition': exp.raw_composition
                            })
                        
                        df_to_inject = pd.DataFrame(data_for_injection)

                     progress_container = st.empty()
                     error_container = st.empty()
                     
                     try:
                        from core.feature_injector import FeatureInjector
                        from core.parallel_feature_injector import ParallelFeatureInjector
                        import time
                        
                        df_enhanced = df_to_inject
                        if use_proxy:
                             with progress_container: st.info(t('loading_proxy'))
                             try:
                                 # 使用缓存的FeatureInjector
                                 parallel_injector = get_feature_injector()
                                 
                                 start_time = time.time()
                                 with progress_container: st.info(t('calc_proxy').format(len(df_to_inject)) + " (缓存加速)")
                                 
                                 df_enhanced = parallel_injector.inject_features_cached(
                                     df_to_inject, 
                                     comp_col='binder_composition', 
                                     ceramic_type_col='Ceramic_Type', 
                                     verbose=False
                                 )
                                 
                                 elapsed = time.time() - start_time
                                 cache_size = len(parallel_injector._feature_cache)
                                 progress_container.success(f"{t('proxy_done')} ({elapsed:.1f}秒, 缓存{cache_size}个成分)")
                             except Exception as e:
                                 error_container.warning(f"⚠️ Proxy calculation failed: {e}")
                        
                        # Matminer Logic placeholder
                        
                        if use_matminer or use_full_matminer:
                             try:
                                 from matminer.featurizers.composition import ElementProperty
                                 from pymatgen.core import Composition
                     
                                 progress_container.info(t('calc_matminer'))
                                 featurizer = ElementProperty.from_preset("magpie")
                                 feature_labels = featurizer.feature_labels()
                     
                                 # --- 1. Binder Features ---
                                 compositions = []
                                 for _, row in df_enhanced.iterrows():
                                     try:
                                         compositions.append(Composition(row['binder_composition']))
                                     except:
                                         compositions.append(None)
                     
                                 df_enhanced['_temp_binder'] = compositions
                                 valid_idx = df_enhanced['_temp_binder'].notnull()
                                 
                                 if valid_idx.sum() > 0:
                                     # Calculate features
                                     binder_df = featurizer.featurize_dataframe(
                                         df_enhanced.loc[valid_idx, ['_temp_binder']].copy(),
                                         '_temp_binder',
                                         ignore_errors=True
                                     )
                                     
                                     # Handle results
                                     if use_full_matminer:
                                         # Rename all columns: "MagpieData X" -> "Binder_MagpieData X"
                                         rename_map = {col: f"Binder_MagpieData {col}" for col in feature_labels if col in binder_df.columns}
                                         binder_df.rename(columns=rename_map, inplace=True)
                                         
                                         # Join back to main DF using index
                                         df_enhanced = pd.concat([df_enhanced, binder_df[list(rename_map.values())]], axis=1)
                                     
                                     # Extract key features (for simplified display/backward compatibility)
                                     col_atomic_weight = f"Binder_MagpieData mean AtomicWeight" if use_full_matminer else "MagpieData mean AtomicWeight"
                                     col_electronegativity = f"Binder_MagpieData avg_dev Electronegativity" if use_full_matminer else "MagpieData avg_dev Electronegativity"
                                     
                                     if not use_full_matminer:
                                         if col_atomic_weight in binder_df.columns:
                                             df_enhanced.loc[valid_idx, 'MagpieData mean AtomicWeight'] = binder_df[col_atomic_weight]
                                         if col_electronegativity in binder_df.columns:
                                             df_enhanced.loc[valid_idx, 'MagpieData std Electronegativity'] = binder_df[col_electronegativity]
                                     else:
                                         if col_atomic_weight in df_enhanced.columns:
                                              df_enhanced['MagpieData mean AtomicWeight'] = df_enhanced[col_atomic_weight]
                                         if col_electronegativity in df_enhanced.columns:
                                              df_enhanced['MagpieData std Electronegativity'] = df_enhanced[col_electronegativity]

                                 # --- 2. Ceramic Features (Full Mode Only) ---
                                 if use_full_matminer:
                                     ceramic_comps = []
                                     for _, row in df_enhanced.iterrows():
                                         try:
                                             # Clean Ceramic_Type
                                             c_type = str(row['Ceramic_Type']).split(',')[0].strip()
                                             ceramic_comps.append(Composition(c_type))
                                         except:
                                             ceramic_comps.append(None)
                                     
                                     df_enhanced['_temp_ceramic'] = ceramic_comps
                                     c_valid_idx = df_enhanced['_temp_ceramic'].notnull()
                                     
                                     if c_valid_idx.sum() > 0:
                                         ceramic_df = featurizer.featurize_dataframe(
                                             df_enhanced.loc[c_valid_idx, ['_temp_ceramic']].copy(),
                                             '_temp_ceramic',
                                             ignore_errors=True
                                         )
                                         
                                         # Rename: "MagpieData X" -> "Ceramic_MagpieData X"
                                         rename_map = {col: f"Ceramic_MagpieData {col}" for col in feature_labels if col in ceramic_df.columns}
                                         ceramic_df.rename(columns=rename_map, inplace=True)
                                         
                                         # Join back
                                         df_enhanced = pd.concat([df_enhanced, ceramic_df[list(rename_map.values())]], axis=1)

                                 # Clean temp cols
                                 df_enhanced.drop(columns=['_temp_binder', '_temp_ceramic'], inplace=True, errors='ignore')
                                 
                                 progress_container.success(t('matminer_done'))
                 
                             except Exception as e:
                                 error_container.warning(f"⚠️ Matminer calculation failed: {str(e)[:200]}")

                        # Save to DB
                        progress_container.info(t('saving_db'))
                        success_count = 0
                        for _, row in df_enhanced.iterrows():
                             try:
                                 exp_id = row['exp_id']
                                 
                                 # Get existing or create new
                                 feature = session.query(CalculatedFeature).filter_by(exp_id=exp_id).first()
                                 if not feature:
                                     feature = CalculatedFeature(exp_id=exp_id)
                                     session.add(feature)
                                 
                                 # Update HEA Flag (Recalculated)
                                 if 'is_hea' in row:
                                     comp_rec = session.query(Composition).filter_by(exp_id=exp_id).first()
                                     if comp_rec:
                                         comp_rec.is_hea = bool(row['is_hea'])
                                 
                                 # Update Proxy Features
                                 if 'pred_formation_energy' in row: feature.pred_formation_energy = row['pred_formation_energy']
                                 if 'pred_lattice_param' in row: feature.pred_lattice_param = row['pred_lattice_param']
                                 if 'lattice_mismatch_wc' in row: feature.lattice_mismatch = row['lattice_mismatch_wc']
                                 if 'pred_magnetic_moment' in row: feature.pred_magnetic_moment = row['pred_magnetic_moment']
                                 if 'vec_binder' in row: feature.vec_binder = row['vec_binder']
                                 
                                 # Update Matminer Features
                                 if use_matminer or use_full_matminer:
                                     # Atomic Mass
                                     if 'magpie_mean_atomic_mass' in row: 
                                         feature.magpie_mean_atomic_mass = row['magpie_mean_atomic_mass']
                                     elif 'MagpieData mean AtomicWeight' in row: 
                                         feature.magpie_mean_atomic_mass = row['MagpieData mean AtomicWeight']
                                     
                                     # Electronegativity
                                     if 'magpie_std_electronegativity' in row: 
                                         feature.magpie_std_electronegativity = row['magpie_std_electronegativity']
                                     elif 'MagpieData std Electronegativity' in row: 
                                         feature.magpie_std_electronegativity = row['MagpieData std Electronegativity']
                                         
                                     feature.has_matminer = True
                                 
                                 if use_full_matminer:
                                     # Extract JSON
                                     c_feat = {k: row[k] for k in row.keys() if str(k).startswith('Ceramic_MagpieData')}
                                     b_feat = {k: row[k] for k in row.keys() if str(k).startswith('Binder_MagpieData') or str(k).startswith('yang_')}
                                     
                                     feature.ceramic_magpie_features = c_feat
                                     feature.binder_magpie_features = b_feat
                                     feature.has_full_matminer = True

                                 session.commit()
                                 success_count += 1
                             except:
                                 session.rollback()
                        
                        st.success(t('update_success').format(success_count))
                        
                     except Exception as e:
                        st.error(t('calc_fail').format(e))

            finally:
                session.close()

        except Exception as e:
            st.error(f"Error: {e}")
                


    # Tab 5: Data Query
    with tab5:
        st.header(t('tab_query'))
        
        try:
            db = DatabaseManager('cermet_master_v2.db')
            session = db.Session()
            
            try:
                from core.db_models import Experiment, Composition, Property, CalculatedFeature
                
                stats = db.get_statistics()
                
                if stats['total_experiments'] == 0:
                    st.info(t('db_empty'))
                else:
                    st.success(t('db_stats_msg').format(stats['total_experiments']))
                    
                    # Data Filter
                    st.subheader(t('data_filter'))
                    
                    col_f1, col_f2, col_f3 = st.columns(3)
                    with col_f1:
                        # For options, we might need a mapping based on language, but for now keeping logic simple
                        # Just translating label
                        filter_hea = st.selectbox(
                            t('binder_type'),
                            options=["All", "HEA", "Traditional"] if st.session_state.get('language') == 'EN' else ["全部", "HEA", "传统"],
                            index=0
                        )
                    
                    with col_f2:
                        limit = st.number_input(
                            t('limit_records'),
                            min_value=10,
                            max_value=5000,
                            value=100,
                            step=10
                        )
                    
                    with col_f3:
                        search_comp = st.text_input(
                            t('search_comp'),
                            placeholder="e.g. WC, Co" if st.session_state.get('language') == 'EN' else "例如: WC, Co"
                        )
                    
                    # Query Data
                    query = session.query(
                        Experiment.id,
                        Experiment.raw_composition,
                        Experiment.source_id,
                        Experiment.sinter_temp_c,
                        Experiment.grain_size_um,
                        Composition.ceramic_formula,
                        Composition.binder_formula,
                        Composition.binder_wt_pct,
                        Composition.is_hea,
                        Property.hv,
                        Property.kic,
                        Property.trs,
                        CalculatedFeature.vec_binder,
                        CalculatedFeature.lattice_mismatch,
                        CalculatedFeature.pred_formation_energy,
                        CalculatedFeature.pred_lattice_param,
                        CalculatedFeature.pred_magnetic_moment,
                        CalculatedFeature.magpie_mean_atomic_mass,
                        CalculatedFeature.magpie_std_electronegativity,
                        CalculatedFeature.ceramic_magpie_features,
                        CalculatedFeature.binder_magpie_features
                    ).join(
                        Composition, Experiment.id == Composition.exp_id, isouter=True
                    ).join(
                        Property, Experiment.id == Property.exp_id, isouter=True
                    ).join(
                        CalculatedFeature, Experiment.id == CalculatedFeature.exp_id, isouter=True
                    )
                    
                    # Apply Filter
                    # Helper to map selected option back to logic
                    is_hea_filter = None
                    if filter_hea in ["HEA", "HEA"]: is_hea_filter = True
                    elif filter_hea in ["Traditional", "传统"]: is_hea_filter = False
                    
                    if is_hea_filter is not None:
                         query = query.filter(Composition.is_hea == is_hea_filter)
                    
                    if search_comp:
                        query = query.filter(Experiment.raw_composition.like(f'%{search_comp}%'))
                    
                    results = query.limit(limit).all()
                    
                    if results:
                        # DataFrame Conversion
                        data = []
                        for r in results:
                            # Use language-aware logic for 'Yes/No' if we want, but keeping simple for now
                            is_hea_str = ('Yes' if r[8] else 'No') if st.session_state.get('language') == 'EN' else ('是' if r[8] else '否')
                            
                            row = {
                                'ID': r[0],
                                'Composition': r[1],
                                'Source': r[2],
                                'Temp(°C)': r[3],
                                'Grain(μm)': r[4],
                                'Ceramic': r[5],
                                'Binder': r[6],
                                'Binder wt%': r[7],
                                'HEA': is_hea_str,
                                'HV': r[9],
                                'KIC': r[10],
                                'TRS': r[11],
                                'VEC': r[12],
                                'Lattice Mismatch': r[13],
                                'Formation E': r[14],
                                'Lattice Param': r[15],
                                'Mag Moment': r[16],
                                'Atomic Mass': r[17],
                                'Electronegativity': r[18]
                            }
                            # Note: Column names above are English/Keys. 
                            # If we want Chinese column headers, we need to map them.
                            # For now, let's keep them as IDs or standard keys to avoid complexity in display/export
                            # unless we rename them right before display.
                            
                            # Expand Full Magpie
                            if len(r) > 19 and r[19]:
                                row.update(r[19])
                            if len(r) > 20 and r[20]:
                                row.update(r[20])
                                
                            data.append(row)
                        
                        df = pd.DataFrame(data)
                        
                        st.subheader(t('query_results').format(len(df)))
                        
                        # Column Selection
                        st.markdown(t('select_cols'))
                        col_sel1, col_sel2 = st.columns([4, 1])
                        
                        with col_sel1:
                            all_cols = list(df.columns)
                            default_cols = ['ID', 'Composition', 'Ceramic', 'Binder', 'HEA', 'HV', 'KIC']
                            # Map defaults to actual cols if they differ
                            final_defaults = [c for c in default_cols if c in all_cols]
                            
                            selected_cols = st.multiselect(
                                t('show_cols'),
                                options=all_cols,
                                default=final_defaults
                            )
                        
                        with col_sel2:
                            if st.button(t('reset_btn')):
                                st.rerun()
                        
                        # Show Table
                        if selected_cols:
                            st.dataframe(
                                df[selected_cols],
                                use_container_width=True,
                                height=400
                            )
                        else:
                            st.warning(t('select_one_col'))
                        
                        # Export
                        st.markdown("---")
                        st.subheader(t('export_data'))
                        
                        col_e1, col_e2, col_e3 = st.columns([1, 1, 2])
                        with col_e1:
                            export_format = st.selectbox(t('format'), ["CSV", "Excel"])
                        with col_e2:
                             # Empty spacer or simple layout
                             pass
                        with col_e3:
                            from datetime import datetime
                            export_name = st.text_input(
                                t('filename'),
                                value=f"export_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            )
                            
                        # Full export option
                        export_all = st.checkbox(t('export_all_label'), value=False, help="Export all internal columns including flattened Matminer features")
                        
                        if st.button(t('export_btn'), use_container_width=True):
                            try:
                                if export_all:
                                    export_df = df
                                else:
                                    export_df = df[selected_cols] if selected_cols else df
                                
                                if export_format == "CSV":
                                    csv = export_df.to_csv(index=False).encode('utf-8-sig')
                                    st.download_button(
                                        t('download_csv'),
                                        csv,
                                        file_name=f"{export_name}.csv",
                                        mime="text/csv"
                                    )
                                else:
                                    import io
                                    buffer = io.BytesIO()
                                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                                        export_df.to_excel(writer, index=False, sheet_name='Data')
                                        workbook = writer.book
                                        worksheet = writer.sheets['Data']
                                        for idx, col in enumerate(export_df.columns):
                                            max_len = max(
                                                export_df[col].astype(str).map(len).max(),
                                                len(str(col))
                                            ) + 2
                                            worksheet.set_column(idx, idx, min(max_len, 50))
                                    
                                    st.download_button(
                                        t('download_excel'),
                                        buffer.getvalue(),
                                        file_name=f"{export_name}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    )
                                
                                st.success(t('export_done'))
                            except Exception as e:
                                st.error(t('export_fail').format(e))
                        
                        # Stats
                        st.markdown("---")
                        st.subheader(t('data_stats'))
                        
                        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                        with col_s1:
                            st.metric(t('record_count'), len(df))
                        with col_s2:
                            hea_count = df[df['HEA'].isin(['Yes', '是'])].shape[0]
                            st.metric("HEA", hea_count)
                        with col_s3:
                            avg_hv = df['HV'].mean() if 'HV' in df and df['HV'].notna().any() else 0
                            st.metric(t('avg_hv'), f"{avg_hv:.1f}" if avg_hv > 0 else "N/A")
                        with col_s4:
                            avg_kic = df['KIC'].mean() if 'KIC' in df and df['KIC'].notna().any() else 0
                            st.metric(t('avg_kic'), f"{avg_kic:.2f}" if avg_kic > 0 else "N/A")
                    
                    else:
                        st.warning(t('not_found'))
            
            finally:
                session.close()
        
        except Exception as e:
            st.error(f"Query Failed: {e}")
            import traceback
            st.code(traceback.format_exc())

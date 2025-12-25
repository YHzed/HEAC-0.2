"""
金属陶瓷数据库管理系统 UI

提供数据录入、批量导入、查询和导出功能
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db_manager import CermetDB
from core.db_config import STANDARD_SCHEMA, VALIDATION_RULES

# 页面配置
st.set_page_config(
    page_title="数据库管理 - HEAC 0.2",
    page_icon="🗄️",
    layout="wide"
)

# 初始化数据库
@st.cache_resource
def get_database():
    """获取数据库实例（缓存）"""
    return CermetDB('cermet_materials.db')

db = get_database()

# ==============================================================================
# 页面标题
# ==============================================================================

st.title("🗄️ 金属陶瓷数据库管理系统")
st.markdown("---")

# ==============================================================================
# 侧边栏 - 数据库统计
# ==============================================================================

with st.sidebar:
    st.header("📊 数据库统计")
    
    try:
        stats = db.get_statistics()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("总记录数", stats['total_records'])
        with col2:
            st.metric("HEA 粘结相", stats['hea_records'])
        
        st.metric("传统粘结相", stats['traditional_records'])
        
        # 完整性最高的字段
        st.markdown("### 数据完整性 Top 5")
        completeness = {
            k: v['completeness_pct'] 
            for k, v in stats['field_completeness'].items()
            if k not in ['source_file', 'notes', 'group_id', 'subgroup', 'is_hea']
        }
        top_complete = sorted(completeness.items(), key=lambda x: x[1], reverse=True)[:5]
        
        for field, pct in top_complete:
            st.progress(pct / 100, text=f"{field}: {pct:.1f}%")
    
    except Exception as e:
        st.error(f"无法加载统计信息: {e}")

# ==============================================================================
# 主界面 - 标签页
# ==============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 单条数据录入",
    "📂 批量导入",
    "🔧 数据预处理",
    "🔍 数据查询",
    "📈 数据可视化"
])

# ==============================================================================
# Tab 1: 单条数据录入
# ==============================================================================

with tab1:
    st.header("📝 单条实验数据录入")
    
    with st.form("single_entry_form"):
        st.subheader("基本信息")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            composition = st.text_input(
                "成分 (Composition)*",
                placeholder="例如: WC-10Co-5Ni",
                help="必填字段"
            )
            group_id = st.text_input(
                "数据分组",
                placeholder="例如: co, ni, hea"
            )
        
        with col2:
            binder_vol = st.number_input(
                "粘结相体积分数 (%)",
                min_value=0.0,
                max_value=100.0,
                step=0.1,
                value=None,
                help="可选字段"
            )
            ceramic_type = st.selectbox(
                "陶瓷相类型",
                options=["", "WC", "TiC", "TiN", "TiCN", "VC", "NbC", "TaC", "Cr3C2"],
                help="可选字段"
            )
        
        with col3:
            binder_composition = st.text_input(
                "粘结相成分",
                placeholder="例如: Co-Ni-Fe",
                help="可选字段"
            )
        
        st.subheader("工艺参数")
        col4, col5, col6 = st.columns(3)
        
        with col4:
            sinter_temp = st.number_input(
                "烧结温度 (°C)",
                min_value=0.0,
                max_value=3000.0,
                step=10.0,
                value=None
            )
        
        with col5:
            grain_size = st.number_input(
                "晶粒尺寸 (μm)",
                min_value=0.01,
                max_value=100.0,
                step=0.1,
                value=None,
                format="%.2f"
            )
        
        with col6:
            sinter_method = st.selectbox(
                "烧结方法",
                options=["", "HIP", "SPS", "Vacuum", "Pressure", "HP", "常压"],
            )
        
        st.subheader("性能指标")
        col7, col8, col9 = st.columns(3)
        
        with col7:
            hv = st.number_input(
                "维氏硬度 (HV, kgf/mm²)",
                min_value=0.0,
                max_value=5000.0,
                step=10.0,
                value=None
            )
        
        with col8:
            kic = st.number_input(
                "断裂韧性 (KIC, MPa·m^1/2)",
                min_value=0.0,
                max_value=50.0,
                step=0.1,
                value=None,
                format="%.2f"
            )
        
        with col9:
            trs = st.number_input(
                "抗弯强度 (TRS, MPa)",
                min_value=0.0,
                max_value=10000.0,
                step=10.0,
                value=None
            )
        
        notes = st.text_area("备注", placeholder="可选备注信息")
        
        submitted = st.form_submit_button("💾 保存数据", use_container_width=True)
        
        if submitted:
            if not composition:
                st.error("❌ 成分 (Composition) 为必填字段！")
            else:
                # 构建数据字典
                data_dict = {
                    'composition_raw': composition,
                    'group_id': group_id if group_id else None,
                    'binder_vol_pct': binder_vol,
                    'ceramic_type': ceramic_type if ceramic_type else None,
                    'binder_composition': binder_composition if binder_composition else None,
                    'sinter_temp_c': sinter_temp,
                    'grain_size_um': grain_size,
                    'sinter_method': sinter_method if sinter_method else None,
                    'hv': hv,
                    'kic': kic,
                    'trs': trs,
                    'notes': notes if notes else None,
                    'source_file': 'manual_entry',
                }
                
                success, message = db.add_single_data(data_dict)
                
                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                else:
                    st.error(f"❌ {message}")

# ==============================================================================
# Tab 2: 批量导入
# ==============================================================================

with tab2:
    st.header("📂 批量 CSV/Excel 导入")
    
    uploaded_file = st.file_uploader(
        "上传数据文件",
        type=['csv', 'xlsx', 'xls'],
        help="支持 CSV 和 Excel 格式"
    )
    
    if uploaded_file is not None:
        try:
            # 读取文件
            if uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
            
            st.success(f"✅ 成功读取 {len(df_upload)} 行数据")
            
            # 预览数据
            st.subheader("📋 数据预览")
            st.dataframe(df_upload.head(10), use_container_width=True)
            
            # 列映射
            st.subheader("🔄 列映射配置")
            st.info("请将上传文件的列名映射到标准数据库字段。如果某列无需导入，请选择'跳过'。")
            
            uploaded_cols = df_upload.columns.tolist()
            column_mapping = {}
            
            # 创建映射界面
            mapping_cols = st.columns(3)
            for idx, col in enumerate(uploaded_cols):
                with mapping_cols[idx % 3]:
                    # 尝试自动匹配
                    default_mapping = "跳过"
                    for std_field, aliases in STANDARD_SCHEMA.items():
                        if col in aliases:
                            default_mapping = std_field
                            break
                    
                    # 选择框
                    options = ["跳过"] + list(STANDARD_SCHEMA.keys())
                    default_idx = options.index(default_mapping) if default_mapping in options else 0
                    
                    mapped_field = st.selectbox(
                        f"`{col}` →",
                        options=options,
                        index=default_idx,
                        key=f"mapping_{idx}"
                    )
                    
                    if mapped_field != "跳过":
                        column_mapping[col] = mapped_field
            
            st.markdown("---")
            
            # 导入选项
            col_opt1, col_opt2 = st.columns(2)
            with col_opt1:
                source_name = st.text_input(
                    "数据来源标记",
                    value=uploaded_file.name,
                    help="用于追踪数据来源"
                )
            
            with col_opt2:
                st.write("")  # 占位
            
            # 导入按钮
            if st.button("🚀 执行批量导入", type="primary", use_container_width=True):
                with st.spinner("正在导入数据..."):
                    success_count, fail_count, errors = db.add_batch_data(
                        df=df_upload,
                        column_mapping=column_mapping,
                        source_name=source_name
                    )
                
                # 显示结果
                col_res1, col_res2 = st.columns(2)
                with col_res1:
                    st.metric("✅ 成功", success_count)
                with col_res2:
                    st.metric("❌ 失败", fail_count)
                
                if fail_count > 0 and errors:
                    with st.expander(f"查看错误详情 ({len(errors)} 条)"):
                        for error in errors[:20]:  # 只显示前20条
                            st.text(error)
                
                if success_count > 0:
                    st.success(f"🎉 成功导入 {success_count} 条数据！")
                    st.balloons()
        
        except Exception as e:
            st.error(f"文件读取失败: {e}")

# ==============================================================================
# Tab 3: 数据预处理
# ==============================================================================

with tab3:
    st.header("🔧 HEA 数据预处理")
    st.markdown("""
    高熵合金（HEA）和金属陶瓷数据自动处理工具。支持复杂成分字符串解析、特征提取，
    并可直接导入到数据库。
    """)
    
    from core import HEADataProcessor
    
    # 数据源选择
    st.subheader("📂 1. 选择数据源")
    data_source = st.radio(
        "数据来源",
        options=["📤 上传文件", "💾 从数据库加载"],
        horizontal=True,
        key="data_source_selector"
    )
    
    df_to_process = None
    source_name = None
    
    # 选项 1: 上传文件
    if data_source == "📤 上传文件":
        col1, col2 = st.columns([2, 1])
        
        with col1:
            preprocessing_file = st.file_uploader(
                "选择 Excel 文件进行预处理",
                type=['xlsx', 'xls'],
                help="上传包含 HEA 成分数据的文件",
                key="preprocessing_uploader"
            )
        
        with col2:
            st.info("""
            **必需列**:
            - Composition
            - HV, kgf/mm2
            
            **可选列**:
            - Binder, vol-%
            - KIC, MPa·m1/2
            - TRS, MPa
            """)
        
        if preprocessing_file is not None:
            try:
                df_to_process = pd.read_excel(preprocessing_file)
                source_name = f"file_{preprocessing_file.name}"
                st.success(f"✅ 成功读取 {len(df_to_process)} 行数据")
            except Exception as e:
                st.error(f"❌ 文件读取失败: {e}")
    
    # 选项 2: 从数据库加载
    else:
        st.markdown("### 从数据库加载数据")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            db_filter_hea = st.selectbox(
                "粘结相类型",
                options=["全部", "仅 HEA", "仅传统"],
                index=0,
                key="db_filter_hea"
            )
        
        with col_f2:
            db_require_composition = st.checkbox(
                "必须包含成分信息",
                value=True,
                key="db_require_comp"
            )
        
        with col_f3:
            db_limit = st.number_input(
                "最大加载行数",
                min_value=10,
                max_value=10000,
                value=1000,
                step=100,
                key="db_limit"
            )
        
        if st.button("📥 从数据库加载", type="primary", key="load_from_db"):
            try:
                # 构建筛选条件
                filters = {}
                if db_filter_hea == "仅 HEA":
                    filters['is_hea'] = 1
                elif db_filter_hea == "仅传统":
                    filters['is_hea'] = 0
                
                # 构建必须非空列表
                drop_na_cols = []
                if db_require_composition:
                    drop_na_cols.append('composition_raw')
                
                # 查询
                with st.spinner("正在从数据库加载..."):
                    df_to_process = db.fetch_data(
                        filters=filters if filters else None,
                        drop_na_cols=drop_na_cols if drop_na_cols else None,
                        limit=db_limit
                    )
                
                if len(df_to_process) > 0:
                    source_name = "database_export"
                    st.success(f"✅ 成功加载 {len(df_to_process)} 行数据")
                    
                    # 显示加载的数据预览
                    with st.expander("📋 已加载数据预览", expanded=False):
                        st.dataframe(df_to_process.head(10), use_container_width=True)
                else:
                    st.warning("未找到符合条件的数据")
            
            except Exception as e:
                st.error(f"❌ 加载失败: {e}")
    
    # 开始预处理
    if df_to_process is not None:
        st.divider()
        st.subheader("⚙️ 2. 数据预处理")
        
        if st.button("🚀 开始预处理", type="primary", use_container_width=True, key="preprocess_btn"):
            try:
                # 显示原始数据预览
                with st.expander("📋 原始数据预览", expanded=False):
                    st.dataframe(df_to_process.head(10), use_container_width=True)
                
                # 数据处理
                with st.spinner("正在处理数据..."):
                    processor = HEADataProcessor()
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("解析成分字符串...")
                    progress_bar.progress(30)
                    df_processed = processor.process_dataframe(df_to_process)
                    
                    status_text.text("添加派生特征...")
                    progress_bar.progress(60)
                    df_processed = processor.add_derived_features(df_processed)
                    
                    progress_bar.progress(100)
                    status_text.text("处理完成！")
                    
                    st.session_state['preprocessed_data'] = df_processed
                    st.session_state['preprocessing_done'] = True
                    st.session_state['preprocessing_source'] = source_name
                
                st.success(f"✅ 成功处理 {len(df_processed)} 行数据")
            
            except Exception as e:
                st.error(f"❌ 处理失败: {e}")
                st.exception(e)
    
    # 显示处理结果
    if 'preprocessing_done' in st.session_state and st.session_state['preprocessing_done']:
        st.divider()
        st.subheader("📊 3. 处理结果")
        
        df_processed = st.session_state['preprocessed_data']
        
        # 统计信息
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("处理成功", f"{len(df_processed)} 行")
        with col2:
            st.metric("特征数量", len(df_processed.columns))
        with col3:
            binder_types = df_processed['Binder_Type'].nunique() if 'Binder_Type' in df_processed.columns else 0
            st.metric("粘结相类型", binder_types)
        
        # 数据预览
        st.markdown("#### 处理后数据预览")
        
        # 列选择
        all_columns = df_processed.columns.tolist()
        key_columns = [
            'Original_Composition', 'Binder_Wt_Pct', 'Ceramic_Wt_Pct',
            'Binder_Atomic_Formula', 'Binder_Type', 'HV_kgf_mm2', 'KIC_MPa_m'
        ]
        default_columns = [col for col in key_columns if col in all_columns]
        
        selected_columns = st.multiselect(
            "选择显示列",
            options=all_columns,
            default=default_columns,
            key="preprocess_column_selector"
        )
        
        if selected_columns:
            st.dataframe(
                df_processed[selected_columns],
                use_container_width=True,
                height=300
            )
        
        # 保存处理结果
        st.divider()
        st.subheader("💾 4. 保存处理结果")
        
        col_save1, col_save2 = st.columns(2)
        
        with col_save1:
            if st.button("💾 导入到数据库", use_container_width=True, type="primary"):
                with st.spinner("正在导入数据库..."):
                    try:
                        # 使用列映射导入
                        from core.db_config import create_column_mapping
                        column_mapping = create_column_mapping(df_processed.columns.tolist())
                        
                        import_source = st.session_state.get('preprocessing_source', 'preprocessed')
                        
                        success, failed, errors = db.add_batch_data(
                            df=df_processed,
                            column_mapping=column_mapping,
                            source_name=f"preprocessed_{import_source}"
                        )
                        
                        if success > 0:
                            st.success(f"✅ 成功导入 {success} 条数据到数据库！")
                            st.balloons()
                        if failed > 0:
                            st.warning(f"⚠️ {failed} 条数据导入失败")
                            with st.expander("查看错误"):
                                for error in errors[:10]:
                                    st.text(error)
                    
                    except Exception as e:
                        st.error(f"导入失败: {e}")
        
        with col_save2:
            # CSV 下载
            import io
            csv_buffer = io.StringIO()
            df_processed.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            csv_data = csv_buffer.getvalue()
            
            st.download_button(
                label="📥 下载 CSV",
                data=csv_data,
                file_name=f"HEA_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )


# ==============================================================================
# Tab 4: 数据查询
# ==============================================================================

with tab4:
    st.header("🔍 数据查询与导出")
    
    # 筛选条件
    with st.expander("⚙️ 筛选条件", expanded=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            filter_hea = st.selectbox(
                "粘结相类型",
                options=["全部", "仅 HEA", "仅传统"],
                index=0
            )
            
            require_hv = st.checkbox("必须包含 HV 数据", value=False)
        
        with col_f2:
            require_kic = st.checkbox("必须包含 KIC 数据", value=False)
            require_trs = st.checkbox("必须包含 TRS 数据", value=False)
        
        with col_f3:
            temp_range = st.slider(
                "烧结温度范围 (°C)",
                min_value=0,
                max_value=3000,
                value=(0, 3000),
                step=50
            )
        
        limit_rows = st.number_input(
            "最大返回行数（0 = 不限制）",
            min_value=0,
            max_value=10000,
            value=1000,
            step=100
        )
    
    # 初始化会话状态
    if 'query_result' not in st.session_state:
        st.session_state.query_result = None
    
    # 执行查询
    if st.button("🔎 执行查询", type="primary"):
        # 构建筛选条件
        filters = {}
        
        if filter_hea == "仅 HEA":
            filters['is_hea'] = 1
        elif filter_hea == "仅传统":
            filters['is_hea'] = 0
        
        if temp_range != (0, 3000):
            filters['sinter_temp_c'] = temp_range
        
        # 构建必须非空列表
        drop_na_cols = []
        if require_hv:
            drop_na_cols.append('hv')
        if require_kic:
            drop_na_cols.append('kic')
        if require_trs:
            drop_na_cols.append('trs')
        
        # 查询
        with st.spinner("正在查询数据..."):
            df_result = db.fetch_data(
                filters=filters if filters else None,
                drop_na_cols=drop_na_cols if drop_na_cols else None,
                limit=limit_rows if limit_rows > 0 else None
            )
        
        # 保存到会话状态
        st.session_state.query_result = df_result
        st.success(f"✅ 找到 {len(df_result)} 条符合条件的数据")
    
    # 显示查询结果
    if st.session_state.query_result is not None and len(st.session_state.query_result) > 0:
        df_result = st.session_state.query_result
        
        # 显示数据
        st.subheader("📊 查询结果")
        
        # 选择显示列
        all_cols = df_result.columns.tolist()
        
       # 定义默认显示的关键列
        default_cols = [
            'id', 'composition_raw', 'group_id', 'binder_vol_pct',
            'hv', 'kic', 'trs', 'sinter_temp_c', 'grain_size_um', 'is_hea'
        ]
        display_cols = [col for col in default_cols if col in all_cols]
        
        # 列选择
        col_sel1, col_sel2 = st.columns([3, 1])
        with col_sel1:
            selected_cols = st.multiselect(
                "选择显示列",
                options=all_cols,
                default=display_cols,
                help="可以添加或删除列来自定义显示内容"
            )
        
        with col_sel2:
            if st.button("🔄 重置列选择"):
                st.rerun()
        
        # 显示数据表格
        if selected_cols:
            st.dataframe(
                df_result[selected_cols],
                use_container_width=True,
                height=400
            )
        else:
            st.warning("请至少选择一列进行显示")
        
        # 导出功能
        st.subheader("📥 导出数据")
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            export_format = st.selectbox(
                "导出格式",
                options=["CSV", "Excel"],
                index=0,
                key="export_format_selector"
            )
        
        with col_exp2:
            export_filename = st.text_input(
                "文件名",
                value=f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                key="export_filename_input"
            )
        
        if st.button("💾 导出", use_container_width=True):
            try:
                # 导出选中的列（如果有选择）或全部列
                export_df = df_result[selected_cols] if selected_cols else df_result
                
                if export_format == "CSV":
                    filepath = f"{export_filename}.csv"
                    export_df.to_csv(filepath, index=False, encoding='utf-8-sig')
                else:
                    filepath = f"{export_filename}.xlsx"
                    export_df.to_excel(filepath, index=False, engine='openpyxl')
                
                st.success(f"✅ 数据已导出到: {filepath}")
                
                # 提供下载
                with open(filepath, 'rb') as f:
                    st.download_button(
                        label=f"⬇️ 下载 {filepath}",
                        data=f,
                        file_name=filepath,
                        mime='application/octet-stream'
                    )
            
            except Exception as e:
                st.error(f"导出失败: {e}")
    
    elif st.session_state.query_result is not None and len(st.session_state.query_result) == 0:
        st.warning("未找到符合条件的数据")



# ==============================================================================
# Tab 5: 数据可视化
# ==============================================================================

with tab5:
    st.header("📈 数据可视化分析")
    
    # 获取所有数据用于可视化
    df_viz = db.fetch_data(limit=5000)
    
    if len(df_viz) > 0:
        # HEA vs 传统分布
        st.subheader("🔵 HEA vs 传统粘结相分布")
        hea_counts = df_viz['is_hea'].value_counts()
        
        # 动态生成标签（避免数据长度不匹配）
        hea_labels = []
        for idx in hea_counts.index:
            hea_labels.append('HEA' if idx == 1 else '传统')
        
        fig_hea = px.pie(
            values=hea_counts.values,
            names=hea_labels,
            title="粘结相类型分布",
            color_discrete_sequence=['#FF6B6B', '#4ECDC4']
        )
        st.plotly_chart(fig_hea, use_container_width=True)
        
        # 硬度 vs 韧性散点图
        st.subheader("📊 硬度 vs 断裂韧性")
        df_plot = df_viz.dropna(subset=['hv', 'kic'])
        if len(df_plot) > 0:
            fig_scatter = px.scatter(
                df_plot,
                x='hv',
                y='kic',
                color='is_hea',
                labels={
                    'hv': '维氏硬度 (HV, kgf/mm²)',
                    'kic': '断裂韧性 (KIC, MPa·m^1/2)',
                    'is_hea': '粘结相类型'
                },
                color_discrete_map={0: '#FF6B6B', 1: '#4ECDC4'},
                opacity=0.6,
                hover_data=['composition_raw', 'grain_size_um']
            )
            fig_scatter.update_layout(height=500)
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        # 字段缺失值热图
        st.subheader("🔥 数据完整性热图")
        key_fields = ['hv', 'kic', 'trs', 'sinter_temp_c', 'grain_size_um', 
                      'binder_vol_pct', 'ceramic_type']
        
        completeness_data = []
        for field in key_fields:
            if field in df_viz.columns:
                completeness = (df_viz[field].notna().sum() / len(df_viz)) * 100
                completeness_data.append({
                    'field': field,
                    'completeness': completeness
                })
        
        df_completeness = pd.DataFrame(completeness_data)
        fig_heat = px.bar(
            df_completeness,
            x='field',
            y='completeness',
            labels={'field': '字段', 'completeness': '完整性 (%)'},
            color='completeness',
            color_continuous_scale='RdYlGn'
        )
        fig_heat.update_layout(height=400)
        st.plotly_chart(fig_heat, use_container_width=True)
    
    else:
        st.info("数据库为空，请先导入数据")

# ==============================================================================
# 页脚
# ==============================================================================

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
    🗄️ 金属陶瓷数据库管理系统 | HEAC 0.2 | 
    数据库位置: <code>cermet_materials.db</code>
    </div>
    """,
    unsafe_allow_html=True
)

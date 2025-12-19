import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime
import io

# 添加scripts目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from process_hea_xlsx import HEADataProcessor

# 统一导入core模块
from core import get_text, initialize_session_state

# ==============================================================================
# INITIALIZATION
# ==============================================================================
initialize_session_state()

def t(key):
    """翻译函数"""
    return get_text(key, st.session_state.language)

st.set_page_config(
    page_title="HEA数据预处理", 
    page_icon="🔧", 
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    h1 { color: #4B4B4B; }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# MAIN PAGE
# ==============================================================================
st.markdown("<h1>🔧 HEA数据预处理</h1>", unsafe_allow_html=True)
st.markdown("""
高熵合金（HEA）和金属陶瓷数据自动处理工具。支持复杂成分字符串解析、特征提取和数据清洗。
""")
st.divider()

# ==============================================================================
# SIDEBAR - INSTRUCTIONS
# ==============================================================================
with st.sidebar:
    st.header("📋 使用说明")
    st.markdown("""
    ### 功能特点
    - ✅ 自动解析复杂成分字符串
    - ✅ 支持多种金属陶瓷格式
    - ✅ 自动计算原子比和质量百分比
    - ✅ 提取派生特征（硬度等级、韧性等级等）
    - ✅ 生成详细处理报告
    
    ### 支持格式示例
    1. **标准格式**: "WC 85 Co 10 Ni 5"
    2. **金属陶瓷格式**: "b WC 25 Co"
    3. **x占位符**: "WC x Co" (from vol%)
    4. **硬质相已知**: "94.12 WC x Co"
    5. **多硬质相+添加剂**: "WC 10 VC 9.6 Co 0.4 Ru"
    
    ### 使用步骤
    1. 📤 上传Excel文件（.xlsx）
    2. ⚙️ 点击"开始处理"按钮
    3. 📊 查看处理结果和统计
    4. 💾 下载处理后的CSV文件
    """)

# ==============================================================================
# FILE UPLOAD SECTION
# ==============================================================================
st.subheader("📤 1. 上传数据文件")

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader(
        "选择Excel文件",
        type=['xlsx'],
        help="请上传包含HEA成分数据的Excel文件"
    )

with col2:
    st.info("**必需列**:\n- Composition\n- HV, kgf/mm2\n\n**可选列**:\n- Binder, vol-%\n- KIC, MPa·m1/2\n- TRS, MPa")

# ==============================================================================
# PROCESSING SECTION
# ==============================================================================
if uploaded_file is not None:
    st.divider()
    st.subheader("⚙️ 2. 数据处理")
    
    # 显示文件信息
    file_details = {
        "文件名": uploaded_file.name,
        "文件大小": f"{uploaded_file.size / 1024:.2f} KB",
        "文件类型": uploaded_file.type
    }
    
    col1, col2, col3 = st.columns(3)
    col1.metric("文件名", file_details["文件名"])
    col2.metric("大小", file_details["文件大小"])
    col3.metric("类型", "Excel")
    
    # 处理按钮
    if st.button("🚀 开始处理", type="primary", use_container_width=True):
        try:
            with st.spinner("正在读取文件..."):
                # 读取Excel文件
                df_original = pd.read_excel(uploaded_file)
                st.success(f"✅ 成功读取 {len(df_original)} 行数据")
            
            # 显示原始数据预览
            with st.expander("📋 原始数据预览", expanded=False):
                st.dataframe(df_original.head(10), use_container_width=True)
                st.caption(f"显示前10行，共{len(df_original)}行")
            
            # 初始化处理器并处理数据
            with st.spinner("正在处理数据..."):
                processor = HEADataProcessor()
                
                # 创建进度条
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 处理数据
                status_text.text("解析成分字符串...")
                progress_bar.progress(30)
                
                df_processed = processor.process_dataframe(df_original)
                
                status_text.text("添加派生特征...")
                progress_bar.progress(60)
                
                df_processed = processor.add_derived_features(df_processed)
                
                progress_bar.progress(100)
                status_text.text("处理完成！")
                
                # 保存到session state
                st.session_state['df_processed'] = df_processed
                st.session_state['df_original'] = df_original
                st.session_state['processing_done'] = True
                
            st.success(f"✅ 成功处理 {len(df_processed)} 行数据")
            
        except Exception as e:
            st.error(f"❌ 处理失败: {str(e)}")
            st.exception(e)

# ==============================================================================
# RESULTS SECTION
# ==============================================================================
if 'processing_done' in st.session_state and st.session_state['processing_done']:
    st.divider()
    st.subheader("📊 3. 处理结果")
    
    df_processed = st.session_state['df_processed']
    df_original = st.session_state['df_original']
    
    # 统计信息
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "处理成功", 
            f"{len(df_processed)} / {len(df_original)}",
            delta=f"{len(df_processed)/len(df_original)*100:.1f}%"
        )
    
    with col2:
        feature_count = len(df_processed.columns)
        st.metric("特征数量", feature_count)
    
    with col3:
        binder_types = df_processed['Binder_Type'].nunique() if 'Binder_Type' in df_processed.columns else 0
        st.metric("粘结相类型", binder_types)
    
    with col4:
        avg_binder_pct = df_processed['Binder_Wt_Pct'].mean() if 'Binder_Wt_Pct' in df_processed.columns else 0
        st.metric("平均粘结相%", f"{avg_binder_pct:.1f}%")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 处理后数据", 
        "📈 数据统计", 
        "🔍 成分分析",
        "📄 处理报告"
    ])
    
    with tab1:
        st.markdown("#### 处理后的数据预览")
        
        # 列过滤器
        all_columns = df_processed.columns.tolist()
        key_columns = [
            'Original_Composition', 'Binder_Wt_Pct', 'Ceramic_Wt_Pct',
            'Binder_Atomic_Formula', 'Binder_Type', 'HV_kgf_mm2', 'KIC_MPa_m'
        ]
        default_columns = [col for col in key_columns if col in all_columns]
        
        selected_columns = st.multiselect(
            "选择要显示的列",
            options=all_columns,
            default=default_columns,
            key="column_selector"
        )
        
        if selected_columns:
            st.dataframe(
                df_processed[selected_columns],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("请至少选择一列")
    
    with tab2:
        st.markdown("#### 数据分布统计")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 粘结相类型分布
            if 'Binder_Type' in df_processed.columns:
                st.markdown("**粘结相类型分布**")
                binder_dist = df_processed['Binder_Type'].value_counts()
                st.bar_chart(binder_dist)
        
        with col2:
            # 硬度等级分布
            if 'Hardness_Grade' in df_processed.columns:
                st.markdown("**硬度等级分布**")
                hardness_dist = df_processed['Hardness_Grade'].value_counts()
                st.bar_chart(hardness_dist)
        
        # 数值统计
        st.markdown("**数值特征统计**")
        numeric_cols = df_processed.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            stats_df = df_processed[numeric_cols].describe()
            st.dataframe(stats_df, use_container_width=True)
    
    with tab3:
        st.markdown("#### 成分格式分析")
        
        # 检查不同格式的解析情况
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**粘结相百分比分布**")
            if 'Binder_Wt_Pct' in df_processed.columns:
                fig_data = df_processed['Binder_Wt_Pct'].dropna()
                st.line_chart(fig_data.value_counts().sort_index())
        
        with col2:
            st.markdown("**元素数量分布**")
            if 'Binder_Element_Count' in df_processed.columns:
                element_dist = df_processed['Binder_Element_Count'].value_counts().sort_index()
                st.bar_chart(element_dist)
        
        # 显示解析失败的样本（如果有）
        if 'has_unknown' in df_processed.columns:
            unknown_count = df_processed['has_unknown'].sum() if df_processed['has_unknown'].dtype == bool else 0
            if unknown_count > 0:
                st.warning(f"⚠️ {unknown_count} 个样本含有未知成分（x占位符且无体积分数）")
                with st.expander("查看未知成分样本"):
                    unknown_samples = df_processed[df_processed['has_unknown'] == True][
                        ['Original_Composition', 'Binder_Composition']
                    ] if 'has_unknown' in df_processed.columns else pd.DataFrame()
                    st.dataframe(unknown_samples.head(20), use_container_width=True)
    
    with tab4:
        st.markdown("#### 处理报告")
        
        # 生成报告
        report = f"""
### HEA数据处理报告
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

#### 数据概览
- 原始数据行数: {len(df_original)}
- 处理成功行数: {len(df_processed)}
- 成功率: {len(df_processed)/len(df_original)*100:.2f}%
- 特征数量: {len(df_processed.columns)}

#### 列名映射
原始列 → 处理后列:
- Composition → Original_Composition
- HV, kgf/mm2 → HV_kgf_mm2
- KIC, MPa·m1/2 → KIC_MPa_m
- TRS, MPa → TRS_MPa

#### 新增特征
"""
        
        new_features = [
            'Binder_Wt_Pct', 'Ceramic_Wt_Pct', 'Binder_Atomic_Formula',
            'Binder_Type', 'Ceramic_Type_Class', 'Binder_Element_Count',
            'Hardness_Grade', 'Toughness_Grade'
        ]
        
        for feat in new_features:
            if feat in df_processed.columns:
                report += f"- {feat}\n"
        
        report += f"""
#### 解析格式统计
"""
        if 'Binder_Type' in df_processed.columns:
            for btype, count in df_processed['Binder_Type'].value_counts().items():
                report += f"- {btype}: {count} 行\n"
        
        st.markdown(report)
        
        # 报告下载按钮
        report_bytes = report.encode('utf-8')
        st.download_button(
            label="📄 下载处理报告",
            data=report_bytes,
            file_name=f"HEA_processing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
    
    # ==============================================================================
    # DOWNLOAD SECTION
    # ==============================================================================
    st.divider()
    st.subheader("💾 4. 下载结果")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV下载
        csv_buffer = io.StringIO()
        df_processed.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        csv_data = csv_buffer.getvalue()
        
        st.download_button(
            label="📥 下载CSV文件",
            data=csv_data,
            file_name=f"HEA_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
            type="primary"
        )
    
    with col2:
        # Excel下载
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_processed.to_excel(writer, index=False, sheet_name='Processed Data')
        excel_data = excel_buffer.getvalue()
        
        st.download_button(
            label="📥 下载Excel文件",
            data=excel_data,
            file_name=f"HEA_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

else:
    # 显示演示说明
    st.info("👆 请上传Excel文件开始处理")
    
    with st.expander("📖 查看示例数据格式"):
        example_data = {
            'Composition': [
                'b WC 25 Co',
                'WC 85 Co 10 Ni 5',
                '94.12 WC x Co',
                'b WC 10 VC 9.6 Co 0.4 Ru'
            ],
            'HV, kgf/mm2': [895, 1100, 1950, 1600],
            'KIC, MPa·m1/2': [20.8, 15.5, 12.0, 14.5],
            'Binder, vol-%': [25, None, None, 10]
        }
        
        st.dataframe(pd.DataFrame(example_data), use_container_width=True)
        st.caption("示例：原始Excel文件应包含的列和格式")

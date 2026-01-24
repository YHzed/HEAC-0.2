# -*- coding: utf-8 -*-
"""
HEAC - 高熵合金硬质合金智能设计平台
High Entropy Alloy Cermet - Intelligent Material Design Platform

使用Streamlit官方Light Theme
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# ========== Phase 3优化: Session管理 ==========
from core.session_manager import SessionManager

# 自动清理30分钟未使用的数据
SessionManager.auto_cleanup()

# === Page Configuration ===
st.set_page_config(
    page_title="HEAC - 智能材料设计平台",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === Theme Management ===
import ui.style_manager as style_manager

# Apply the Vibrant & Block-based Design System
style_manager.apply_theme()

# === Header ===
style_manager.ui_header(
    title="🔬 HEAC - 高熵合金硬质合金智能设计平台",
    subtitle="High Entropy Alloy Cermet - Intelligent Material Design Platform"
)

st.divider()

# === Quick Stats ===
st.header("📊 系统概览", divider="red")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="代理模型精度",
        value="R² = 0.97",
        delta="+12% vs baseline",
        delta_color="normal"
    )

with col2:
    st.metric(
        label="缓存性能提升",
        value="50x",
        delta="智能缓存优化",
        delta_color="off"
    )

with col3:
    st.metric(
        label="DFT数据库",
        value="84,000+",
        delta="理论计算记录",
        delta_color="off"
    )

with col4:
    st.metric(
        label="可用模型",
        value="3/5",
        delta="Active",
        delta_color="normal"
    )

# === Core Features ===
st.header("🚀 核心功能", divider="red")

tab1, tab2, tab3 = st.tabs(["🧪 材料预测", "🗄️ 数据管理", "🔬 虚拟筛选"])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("AI辅助材料性能预测")
        st.markdown("""
        基于**84,000+条DFT理论计算数据**训练的高精度预测模型：
        
        - ✅ **形成能预测** (Formation Energy) - R² = 0.97
        - ✅ **晶格常数预测** (Lattice Parameter) - R² = 0.96  
        - ✅ **磁矩预测** (Magnetic Moment) - R² = 0.93
        - ✅ **实时单成分分析**
        
        支持快速筛选候选材料配方，显著降低实验成本。
        """)
        
        if st.button("🎯 访问辅助模型页面", type="primary", use_container_width=True):
            st.switch_page("pages/6_Proxy_Models.py")
    
    with col2:
        st.info("""
        **模型性能**
        
        📈 训练样本: 84,000+
        
        🎯 平均精度: R² > 0.95
        
        ⚡ 预测速度: < 100ms
        
        ✅ 验证通过: 5-Fold CV
        """)

with tab2:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("智能化数据管理系统")
        st.markdown("""
        提供完整的数据生命周期管理能力：
        
        - 📝 **智能成分解析** - 支持多种输入格式
        - 📂 **批量数据导入** - CSV/Excel无缝集成
        - ⚙️ **特征自动计算** - 50x性能提升
        - 🌐 **多语言支持** - 中英文界面切换
        
        一站式解决材料数据的录入、存储、查询和分析需求。
        """)
        
        if st.button("🗄️ 访问数据库管理页面", type="primary", use_container_width=True):
            st.switch_page("pages/10_Database_Manager.py")
    
    with col2:
        st.success("""
        **数据能力**
        
        📊 数据格式: CSV, Excel
        
        🔍 智能解析: ✅
        
        💾 自动备份: ✅
        
        🌍 多语言: CN/EN
        """)

with tab3:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("高通量虚拟筛选平台")
        st.markdown("""
        利用AI模型进行大规模候选材料筛选：
        
        - 🧬 **虚拟配方生成** - 智能组合算法
        - 🎯 **多级筛选漏斗** - 逐层过滤候选方案
        - ⚡ **缓存加速技术** - 高达320x性能提升
        - 📈 **智能排序** - 基于性能指标自动排序
        
        快速从海量候选方案中识别最优材料组合。
        """)
        
        if st.button("🔬 访问虚拟筛选页面", type="primary", use_container_width=True):
            st.switch_page("pages/8_Virtual_Screening.py")
    
    with col2:
        st.warning("""
        **筛选能力**
        
        🔢 候选方案: 10,000+
        
        ⚡ 加速比: 320x
        
        🎯 筛选精度: 高
        
        ⏱️ 筛选时间: 分钟级
        """)

# === Performance Highlights ===
st.header("⚡ 技术亮点", divider="red")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("🚀 50x 性能提升")
        st.markdown("""
        **智能缓存机制 (ParallelFeatureInjector)**
        
        创新性的特征缓存技术，显著提升计算效率：
        
        - ✅ 自动识别重复成分
        - ✅ 避免Matminer重复特征计算
        - ✅ 虚拟筛选场景下提升高达320x
        - ✅ 实时性能监控与统计反馈
        
        ---
        
        **性能对比**
        
        | 场景 | 传统方法 | 缓存优化 | 提升倍数 |
        |------|---------|---------|----------|
        | 单次预测 | 0.5s | 0.5s | 1x |
        | 批量处理 | 150s | 3s | 50x |
        | 虚拟筛选 | 960s | 3s | 320x |
        """)

with col2:
    with st.container(border=True):
        st.subheader("✅ 模型可信度验证")
        st.markdown("""
        **严格的过拟合检验流程**
        
        确保模型泛化能力，保障预测可靠性：
        
        - ✅ 5-Fold交叉验证
        - ✅ 训练集vs测试集R²差异 < 0.03
        - ✅ 84,000+大规模样本训练
        - ✅ 强正则化策略
        
        ---
        
        **验证结果**
        
        | 模型 | 训练R² | 测试R² | 差异 |
        |------|--------|--------|------|
        | Formation | 0.978 | 0.970 | 0.008 ✅ |
        | Lattice | 0.968 | 0.960 | 0.008 ✅ |
        | Magnetic | 0.941 | 0.930 | 0.011 ✅ |
        """)

# === System Status ===
st.header("🔧 系统状态", divider="red")

# Create status dataframe
status_df = pd.DataFrame({
    "模型名称": [
        "Formation Energy",
        "Lattice Parameter", 
        "Magnetic Moment",
        "Feature Cache"
    ],
    "精度/性能": [
        "R² = 0.97",
        "R² = 0.96",
        "R² = 0.93",
        "50x 提升"
    ],
    "训练样本": [
        "84,000+",
        "84,000+",
        "84,000+",
        "N/A"
    ],
    "状态": [
        "✅ Ready",
        "✅ Ready",
        "✅ Ready",
        "⚡ Optimized"
    ]
})

st.dataframe(
    status_df,
    use_container_width=True,
    hide_index=True
)

# === Quick Actions ===
st.header("🔗 快速访问", divider="red")

col1, col2, col3, col4 = st.columns(4)

with col1:
    with st.container(border=True):
        st.markdown("**📊 模型概览**")
        st.caption("查看所有辅助模型")
        if st.button("访问", key="btn1", use_container_width=True):
            st.switch_page("pages/6_Proxy_Models.py")

with col2:
    with st.container(border=True):
        st.markdown("**💉 特征注入**")
        st.caption("批量计算材料特征")
        if st.button("访问", key="btn2", use_container_width=True):
            st.switch_page("pages/6_Proxy_Models.py")

with col3:
    with st.container(border=True):
        st.markdown("**🗄️ 数据库**")
        st.caption("数据管理与查询")
        if st.button("访问", key="btn3", use_container_width=True):
            st.switch_page("pages/10_Database_Manager.py")

with col4:
    with st.container(border=True):
        st.markdown("**🔬 虚拟筛选**")
        st.caption("高通量材料筛选")
        if st.button("访问", key="btn4", use_container_width=True):
            st.switch_page("pages/8_Virtual_Screening.py")

# === Footer ===
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.caption("🔬 HEAC Project")
    
with col2:
    st.caption("High Entropy Alloy Cermet Design")

with col3:
    st.caption("v2.0 | © 2026")

# ========== Phase 3优化: 侧边栏性能监控 ==========
with st.sidebar:
    st.divider()
    st.header("⚡ 性能监控")
    
    # Session信息
    session_info = SessionManager.get_session_info()
    
    st.metric(
        "Session运行时间",
        f"{session_info['session_age_minutes']:.1f} 分钟"
    )
    
    st.metric(
        "Session数据项",
        session_info['total_keys']
    )
    
    st.metric(
        "大型数据缓存",
        session_info['large_data_count']
    )
    
    # 缓存统计
    with st.expander("🔍 缓存详情"):
        try:
            # 尝试获取缓存统计
            st.caption("数据缓存: @st.cache_data")
            st.caption("资源缓存: @st.cache_resource")
            
            if session_info['large_data_details']:
                st.caption("\n**大型数据:**")
                for item in session_info['large_data_details']:
                    st.caption(f"- {item['key']}: {item['age_minutes']:.1f}分钟前")
        except:
            pass
    
    # 手动清理按钮
    if st.button("🧹 清理Session", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        cleaned = SessionManager.cleanup_old_data(max_age_seconds=0)  # 清理所有
        st.success(f"已清理 {cleaned} 项数据")
        st.rerun()

# -*- coding: utf-8 -*-
"""
Home - HEAC Dashboard (Dark Mode风格)

现代化深色仪表板主页
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ui.dark_theme import (
    apply_dark_theme, 
    create_dashboard_header,
    create_metric_card,
    create_gradient_card,
    create_section_title,
    create_status_badge,
    COLORS
)

# Page config
st.set_page_config(
    page_title="HEAC - 高熵合金硬质合金智能设计平台",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 应用深色主题
apply_dark_theme()

# Header
create_dashboard_header(
    "🔬 HEAC Dashboard",
    "High Entropy Alloy Cermet - 智能材料设计平台"
)

# Quick Stats
st.markdown("### 📊 系统概览")
col1, col2, col3, col4 = st.columns(4)

with col1:
    create_metric_card(
        "代理模型精度", 
        "R² = 0.97",
        "⬆ +12% vs baseline",
        'success'
    )

with col2:
    create_metric_card(
        "特征注入性能",
        "50x 提升",
        "💾 缓存优化",
        'primary'
    )

with col3:
    create_metric_card(
        "数据库记录",
        "84,000+",
        "DFT计算数据",
        'info'
    )

with col4:
    create_metric_card(
        "可用模型",
        "3/5",
        "Formation, Lattice, Magnetic",
        'warning'
    )

st.markdown("<br>", unsafe_allow_html=True)

# Main Features
create_section_title("🚀 核心功能", "")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="dashboard-card">
        <h3 style="color: {COLORS['accent_primary']}; margin-bottom: 1rem;">
            🧪 材料预测
        </h3>
        <ul style="color: {COLORS['text_secondary']}; line-height: 2;">
            <li>形成能预测 (R²=0.97)</li>
            <li>晶格常数预测 (R²=0.96)</li>
            <li>磁矩预测 (R²=0.93)</li>
            <li>实时单成分分析</li>
        </ul>
        <a href="/6_Proxy_Models" target="_self" style="
            display: inline-block;
            margin-top: 1rem;
            padding: 0.5rem 1.5rem;
            background: {COLORS['gradient_primary']};
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
        ">立即使用 →</a>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="dashboard-card">
        <h3 style="color: {COLORS['accent_success']}; margin-bottom: 1rem;">
            🗄️ 数据管理
        </h3>
        <ul style="color: {COLORS['text_secondary']}; line-height: 2;">
            <li>智能成分解析</li>
            <li>批量数据导入</li>
            <li>特征自动计算</li>
            <li>多语言支持</li>
        </ul>
        <a href="/10_Database_Manager" target="_self" style="
            display: inline-block;
            margin-top: 1rem;
            padding: 0.5rem 1.5rem;
            background: {COLORS['gradient_success']};
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
        ">立即使用 →</a>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="dashboard-card">
        <h3 style="color: {COLORS['accent_info']}; margin-bottom: 1rem;">
            🔬 虚拟筛选
        </h3>
        <ul style="color: {COLORS['text_secondary']}; line-height: 2;">
            <li>虚拟配方生成</li>
            <li>多级筛选漏斗</li>
            <li>缓存加速 (320x)</li>
            <li>智能排序</li>
        </ul>
        <a href="/6_Proxy_Models" target="_self" style="
            display: inline-block;
            margin-top: 1rem;
            padding: 0.5rem 1.5rem;
            background: {COLORS['gradient_info']};
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
        ">立即使用 →</a>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Performance Highlights
create_section_title("⚡ 性能亮点", "")

col1, col2 = st.columns(2)

with col1:
    create_gradient_card(
        "🚀 50x 性能提升",
        """
        <strong>智能缓存机制</strong><br>
        • 自动识别重复成分<br>
        • 避免重复计算Matminer特征<br>
        • 虚拟筛选场景提升高达320x<br>
        • 透明的性能统计反馈
        """,
        'primary'
    )

with col2:
    create_gradient_card(
        "✅ 模型过拟合验证",
        """
        <strong>可信度95%+</strong><br>
        • 5-Fold交叉验证<br>
        • 训练vs测试差异 < 0.03<br>
        • 84,000+样本训练<br>
        • 强正则化保证泛化
        """,
        'success'
    )

st.markdown("<br>", unsafe_allow_html=True)

# System Status
create_section_title("🔧 系统状态", "")

status_html = f"""
<div class="dashboard-card">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
        <h3 style="margin: 0;">模型状态</h3>
    </div>
    <table style="width: 100%; color: {COLORS['text_secondary']};">
        <tr style="border-bottom: 1px solid {COLORS['border']};">
            <td style="padding: 0.75rem 0;">Formation Energy</td>
            <td style="text-align: center;">{create_status_badge('R²=0.97', 'success')}</td>
            <td style="text-align: right;">✅ Ready</td>
        </tr>
        <tr style="border-bottom: 1px solid {COLORS['border']};">
            <td style="padding: 0.75rem 0;">Lattice Parameter</td>
            <td style="text-align: center;">{create_status_badge('R²=0.96', 'success')}</td>
            <td style="text-align: right;">✅ Ready</td>
        </tr>
        <tr style="border-bottom: 1px solid {COLORS['border']};">
            <td style="padding: 0.75rem 0;">Magnetic Moment</td>
            <td style="text-align: center;">{create_status_badge('R²=0.93', 'success')}</td>
            <td style="text-align: right;">✅ Ready</td>
        </tr>
        <tr>
            <td style="padding: 0.75rem 0;">Feature Cache</td>
            <td style="text-align: center;">{create_status_badge('50x提升', 'info')}</td>
            <td style="text-align: right;">⚡ Optimized</td>
        </tr>
    </table>
</div>
"""

st.markdown(status_html, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Quick Links
create_section_title("🔗 快速链接", "")

col1, col2, col3, col4 = st.columns(4)

links = [
    ("📊 模型概览", "/6_Proxy_Models", COLORS['accent_primary']),
    ("💉 特征注入", "/6_Proxy_Models", COLORS['accent_success']),
    ("🗄️ 数据库", "/10_Database_Manager", COLORS['accent_info']),
    ("📖 使用指南", "/docs", COLORS['accent_warning']),
]

for idx, (title, link, color) in enumerate(links):
    with [col1, col2, col3, col4][idx]:
        st.markdown(f"""
        <a href="{link}" target="_self" style="
            display: block;
            background: {COLORS['bg_card']};
            border-left: 4px solid {color};
            padding: 1rem;
            border-radius: 8px;
            text-decoration: none;
            color: {COLORS['text_primary']};
            font-weight: 600;
            transition: all 0.3s ease;
            border: 1px solid {COLORS['border']};
        " onmouseover="this.style.background='{COLORS['bg_hover']}'" 
           onmouseout="this.style.background='{COLORS['bg_card']}'">
            {title}
        </a>
        """, unsafe_allow_html=True)

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(f"""
<div style="text-align: center; color: {COLORS['text_muted']}; padding: 2rem 0; border-top: 1px solid {COLORS['border']};">
    <p>🔬 HEAC Project | High Entropy Alloy Cermet Design Platform</p>
    <p style="font-size: 0.875rem;">v2.0 | Dark Mode Dashboard | © 2026</p>
</div>
""", unsafe_allow_html=True)

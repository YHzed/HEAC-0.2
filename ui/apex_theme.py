"""
HEAC Apex风格主题配置

基于apexlol.info的电竞风格深色仪表板设计
"""

# Apex风格配色方案
APEX_COLORS = {
    # 深色背景系统 (Tailwind slate系列)
    'bg_primary': '#020617',      # 主背景 (slate-950) - 深海军蓝黑
    'bg_card': '#0f172a',         # 卡片背景 (slate-900) - 深蓝灰
    'bg_hover': '#1e293b',        # 悬停/交互 (slate-800) - 中蓝灰
    'bg_input': '#1e293b',        # 输入框背景
    
    # 文本颜色
    'text_primary': '#f1f5f9',    # 主文本 (slate-100) - 近白色
    'text_secondary': '#94a3b8',  # 次要文本 (slate-400) - 灰色
    'text_muted': '#64748b',      # 弱化文本 (slate-500)
    
    # 强调色 - 青紫系
    'accent_cyan': '#22d3ee',     # 主强调色 - 亮青色
    'accent_purple': '#a855f7',   # 副强调色 - 紫色
    'accent_cyan_dark': '#0891b2',  # 深青色
    
    # 渐变
    'gradient_primary': 'linear-gradient(to right, #22d3ee, #a855f7)',
    'gradient_card': 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
    
    # 边框
    'border_default': '#1e293b',
    'border_accent': '#22d3ee',
    'border_hover': '#38bdf8',
    
    # 发光效果
    'glow_cyan': '0 0 15px -5px rgba(34, 211, 238, 0.3)',
    'glow_purple': '0 0 15px -5px rgba(168, 85, 247, 0.3)',
}

# Apex风格CSS
APEX_CSS = f"""
<style>
    /* Google Fonts导入 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* ===== 全局样式重置 ===== */
    * {{
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        text-rendering: optimizeLegibility;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}
    
    /* ===== 主容器 ===== */
    .stApp {{
        background: {APEX_COLORS['bg_primary']};
        color: {APEX_COLORS['text_primary']};
    }}
    
    /* ===== 侧边栏 ===== */
    [data-testid="stSidebar"] {{
        background: {APEX_COLORS['bg_card']};
        border-right: 1px solid {APEX_COLORS['border_default']};
    }}
    
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {{
        color: {APEX_COLORS['text_primary']};
    }}
    
    /* ===== Apex风格卡片 ===== */
    .apex-card {{
        background: {APEX_COLORS['bg_card']};
        border: 1px solid {APEX_COLORS['border_default']};
        border-radius: 0.75rem;
        padding: 1.5rem;
        transition: all 0.3s ease;
    }}
    
    .apex-card:hover {{
        background: {APEX_COLORS['bg_hover']};
        border-color: {APEX_COLORS['border_hover']};
        transform: translateY(-2px);
    }}
    
    /* 发光卡片 */
    .apex-card-glow {{
        background: {APEX_COLORS['bg_card']};
        border: 1px solid {APEX_COLORS['accent_cyan']};
        border-radius: 0.75rem;
        padding: 1.5rem;
        box-shadow: {APEX_COLORS['glow_cyan']};
    }}
    
    /* ===== 渐变标题 ===== */
    .apex-title {{
        font-size: 2.5rem;
        font-weight: 800;
        background: {APEX_COLORS['gradient_primary']};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.02em;
        margin-bottom: 0.5rem;
    }}
    
    .apex-subtitle {{
        font-size: 1.125rem;
        color: {APEX_COLORS['text_secondary']};
        font-weight: 500;
        margin-bottom: 2rem;
    }}
    
    /* ===== 指标卡片 ===== */
    .apex-metric {{
        background: {APEX_COLORS['bg_card']};
        border: 1px solid {APEX_COLORS['border_default']};
        border-left: 3px solid {APEX_COLORS['accent_cyan']};
        border-radius: 0.75rem;
        padding: 1.25rem;
    }}
    
    .apex-metric-label {{
        font-size: 0.875rem;
        font-weight: 600;
        color: {APEX_COLORS['text_secondary']};
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }}
    
    .apex-metric-value {{
        font-size: 2rem;
        font-weight: 800;
        color: {APEX_COLORS['accent_cyan']};
        line-height: 1;
    }}
    
    .apex-metric-delta {{
        font-size: 0.875rem;
        color: {APEX_COLORS['text_secondary']};
        margin-top: 0.5rem;
    }}
    
    /* ===== Streamlit组件覆盖 ===== */
    
    /* 按钮 */
    .stButton > button {{
        background: {APEX_COLORS['bg_card']};
        border: 1px solid {APEX_COLORS['accent_cyan']};
        color: {APEX_COLORS['accent_cyan']};
        border-radius: 0.75rem;
        padding: 0.65rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        background: {APEX_COLORS['accent_cyan']};
        color: {APEX_COLORS['bg_primary']};
        box-shadow: {APEX_COLORS['glow_cyan']};
        transform: translateY(-1px);
    }}
    
    /* 主要按钮 */
    .stButton > button[kind="primary"] {{
        background: {APEX_COLORS['gradient_primary']};
        border: none;
        color: white;
    }}
    
    /* 输入框 */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div,
    .stTextArea > div > div > textarea {{
        background: {APEX_COLORS['bg_input']};
        border: 1px solid {APEX_COLORS['border_default']};
        border-radius: 0.75rem;
        color: {APEX_COLORS['text_primary']};
    }}
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {{
        border-color: {APEX_COLORS['accent_cyan']};
        box-shadow: {APEX_COLORS['glow_cyan']};
    }}
    
    /* Tab导航 */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
        background: transparent;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: {APEX_COLORS['bg_card']};
        border: 1px solid {APEX_COLORS['border_default']};
        border-radius: 0.75rem;
        color: {APEX_COLORS['text_secondary']};
        font-weight: 600;
        padding: 0.75rem 1.5rem;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: {APEX_COLORS['gradient_primary']};
        border-color: {APEX_COLORS['accent_cyan']};
        color: white;
        box-shadow: {APEX_COLORS['glow_cyan']};
    }}
    
    /* 数据框 */
    .dataframe {{
        background: {APEX_COLORS['bg_card']};
        border: 1px solid {APEX_COLORS['border_default']};
        border-radius: 0.75rem;
        color: {APEX_COLORS['text_primary']};
    }}
    
    /* 进度条 */
    .stProgress > div > div {{
        background: {APEX_COLORS['gradient_primary']};
    }}
    
    .stProgress > div {{
        background: {APEX_COLORS['bg_input']};
        border-radius: 9999px;
    }}
    
    /* Metric组件 */
    [data-testid="stMetricValue"] {{
        font-size: 2rem;
        font-weight: 800;
        color: {APEX_COLORS['accent_cyan']};
    }}
    
    [data-testid="stMetricLabel"] {{
        color: {APEX_COLORS['text_secondary']};
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.875rem;
    }}
    
    /* 消息框 */
    .stSuccess {{
        background: rgba(34, 211, 238, 0.1);
        border-left: 4px solid {APEX_COLORS['accent_cyan']};
        border-radius: 0.75rem;
        color: {APEX_COLORS['text_primary']};
    }}
    
    .stInfo {{
        background: rgba(168, 85, 247, 0.1);
        border-left: 4px solid {APEX_COLORS['accent_purple']};
        border-radius: 0.75rem;
        color: {APEX_COLORS['text_primary']};
    }}
    
    .stWarning {{
        background: rgba(251, 146, 60, 0.1);
        border-left: 4px solid #fb923c;
        border-radius: 0.75rem;
        color: {APEX_COLORS['text_primary']};
    }}
    
    /* 展开器 */
    .streamlit-expanderHeader {{
        background: {APEX_COLORS['bg_card']};
        border: 1px solid {APEX_COLORS['border_default']};
        border-radius: 0.75rem;
        color: {APEX_COLORS['text_primary']};
        font-weight: 600;
    }}
    
    /* 文件上传器 */
    [data-testid="stFileUploader"] {{
        background: {APEX_COLORS['bg_card']};
        border: 2px dashed {APEX_COLORS['accent_cyan']};
        border-radius: 0.75rem;
    }}
    
    /* 隐藏默认元素 */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* ===== 自定义组件 ===== */
    
    /* 状态徽章 */
    .apex-badge {{
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    .apex-badge-cyan {{
        background: rgba(34, 211, 238, 0.2);
        color: {APEX_COLORS['accent_cyan']};
        border: 1px solid {APEX_COLORS['accent_cyan']};
    }}
    
    .apex-badge-purple {{
        background: rgba(168, 85, 247, 0.2);
        color: {APEX_COLORS['accent_purple']};
        border: 1px solid {APEX_COLORS['accent_purple']};
    }}
    
    /* 分隔线 */
    hr {{
        border-color: {APEX_COLORS['border_default']};
        opacity: 0.5;
    }}
    
    /* ===== 响应式 ===== */
    @media (max-width: 768px) {{
        .apex-title {{
            font-size: 2rem;
        }}
    }}
</style>
"""

def apply_apex_theme():
    """应用Apex风格主题"""
    import streamlit as st
    st.markdown(APEX_CSS, unsafe_allow_html=True)

def create_apex_header(title, subtitle=None):
    """创建Apex风格标题"""
    import streamlit as st
    
    html = f"""
    <div style="margin-bottom: 3rem;">
        <h1 class="apex-title">{title}</h1>
        {f'<p class="apex-subtitle">{subtitle}</p>' if subtitle else ''}
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)

def create_apex_metric(label, value, delta=None):
    """创建Apex风格指标卡片"""
    import streamlit as st
    
    html = f"""
    <div class="apex-metric">
        <div class="apex-metric-label">{label}</div>
        <div class="apex-metric-value">{value}</div>
        {f'<div class="apex-metric-delta">{delta}</div>' if delta else ''}
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)

def create_apex_card(content, glow=False):
    """创建Apex风格卡片"""
    import streamlit as st
    
    card_class = "apex-card-glow" if glow else "apex-card"
    
    html = f"""
    <div class="{card_class}">
        {content}
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)

def create_apex_badge(text, color='cyan'):
    """创建Apex风格徽章"""
    return f'<span class="apex-badge apex-badge-{color}">{text}</span>'

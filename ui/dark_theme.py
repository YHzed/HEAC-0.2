"""
HEAC Dark Mode Dashboard - 主题配置

现代化深色仪表板风格配置
"""

# 颜色方案
COLORS = {
    # 深色背景
    'bg_primary': '#0E1117',      # 主背景
    'bg_secondary': '#1A1D24',    # 次要背景
    'bg_card': '#262730',         # 卡片背景
    'bg_hover': '#2E3141',        # 悬停背景
    
    # 渐变色
    'gradient_primary': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'gradient_success': 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
    'gradient_warning': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    'gradient_info': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    
    # 文本颜色
    'text_primary': '#FFFFFF',
    'text_secondary': '#B8B8B8',
    'text_muted': '#6B6B6B',
    
    # 强调色
    'accent_primary': '#667eea',   # 主色调（紫色）
    'accent_success': '#38ef7d',   # 成功（绿色）
    'accent_warning': '#f5576c',   # 警告（红色）
    'accent_info': '#4facfe',      # 信息（蓝色）
    
    # 边框
    'border': '#363945',
    'border_light': '#484B5A',
}

# CSS样式
CUSTOM_CSS = f"""
<style>
    /* 导入优质字体 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap');
    
    /* 全局样式 */
    * {{
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        text-rendering: optimizeLegibility;
    }}
    
    .stApp {{
        background: {COLORS['bg_primary']};
        font-family: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}
    
    /* 改善中文字体渲染 */
    body, p, span, div {{
        font-family: 'Inter', 'Noto Sans SC', 'Microsoft YaHei', '微软雅黑', sans-serif;
        letter-spacing: 0.02em;
    }}
    
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Inter', 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
        font-weight: 700;
        letter-spacing: -0.01em;
    }}
    
    /* 侧边栏 */
    [data-testid="stSidebar"] {{
        background: {COLORS['bg_secondary']};
        border-right: 1px solid {COLORS['border']};
    }}
    
    /* 卡片样式 */
    .dashboard-card {{
        background: {COLORS['bg_card']};
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid {COLORS['border']};
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }}
    
    .dashboard-card:hover {{
        background: {COLORS['bg_hover']};
        border-color: {COLORS['border_light']};
        transform: translateY(-2px);
        box-shadow: 0 8px 12px rgba(0, 0, 0, 0.4);
    }}
    
    /* 渐变卡片 */
    .gradient-card-primary {{
        background: {COLORS['gradient_primary']};
        border-radius: 12px;
        padding: 1.5rem;
        color: white;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }}
    
    .gradient-card-success {{
        background: {COLORS['gradient_success']};
        border-radius: 12px;
        padding: 1.5rem;
        color: white;
        box-shadow: 0 4px 12px rgba(56, 239, 125, 0.4);
    }}
    
    /* 指标卡片 */
    .metric-card {{
        background: {COLORS['bg_card']};
        border-radius: 12px;
        padding: 1.25rem;
        border-left: 4px solid {COLORS['accent_primary']};
        border: 1px solid {COLORS['border']};
    }}
    
    .metric-card-success {{
        border-left-color: {COLORS['accent_success']};
    }}
    
    .metric-card-warning {{
        border-left-color: {COLORS['accent_warning']};
    }}
    
    .metric-card-info {{
        border-left-color: {COLORS['accent_info']};
    }}
    
    /* 标题样式 */
    .dashboard-title {{
        font-size: 2.5rem;
        font-weight: 700;
        background: {COLORS['gradient_primary']};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }}
    
    .section-title {{
        font-size: 1.5rem;
        font-weight: 600;
        color: {COLORS['text_primary']};
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid {COLORS['accent_primary']};
    }}
    
    /* 按钮样式 */
    .stButton > button {{
        background: {COLORS['gradient_primary']};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5);
    }}
    
    /* 数据框样式 */
    .dataframe {{
        background: {COLORS['bg_card']};
        border-radius: 8px;
        border: 1px solid {COLORS['border']};
    }}
    
    /* 进度条 */
    .stProgress > div > div {{
        background: {COLORS['gradient_primary']};
    }}
    
    /* 输入框 */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {{
        background: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        color: {COLORS['text_primary']};
    }}
    
    /* 文件上传器 */
    [data-testid="stFileUploader"] {{
        background: {COLORS['bg_card']};
        border: 2px dashed {COLORS['border']};
        border-radius: 12px;
        padding: 2rem;
    }}
    
    /* Tab样式 */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: {COLORS['bg_secondary']};
        border-radius: 8px;
        padding: 0.5rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        border-radius: 6px;
        color: {COLORS['text_secondary']};
        font-weight: 600;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: {COLORS['gradient_primary']};
        color: white;
    }}
    
    /* 指标样式增强 */
    [data-testid="stMetricValue"] {{
        font-size: 2rem;
        font-weight: 700;
        color: {COLORS['text_primary']};
    }}
    
    [data-testid="stMetricLabel"] {{
        color: {COLORS['text_secondary']};
        font-weight: 600;
    }}
    
    /* 成功/警告/信息消息 */
    .stSuccess {{
        background: {COLORS['gradient_success']};
        border-radius: 8px;
        border: none;
    }}
    
    .stWarning {{
        background: {COLORS['gradient_warning']};
        border-radius: 8px;
        border: none;
    }}
    
    .stInfo {{
        background: {COLORS['gradient_info']};
        border-radius: 8px;
        border: none;
    }}
    
    /* 展开器 */
    .streamlit-expanderHeader {{
        background: {COLORS['bg_card']};
        border-radius: 8px;
        border: 1px solid {COLORS['border']};
        color: {COLORS['text_primary']};
        font-weight: 600;
    }}
    
    /* 图表容器 */
    .plot-container {{
        background: {COLORS['bg_card']};
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid {COLORS['border']};
    }}
    
    /* 状态徽章 */
    .status-badge {{
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.875rem;
        font-weight: 600;
    }}
    
    .status-success {{
        background: {COLORS['gradient_success']};
        color: white;
    }}
    
    .status-warning {{
        background: {COLORS['gradient_warning']};
        color: white;
    }}
    
    .status-info {{
        background: {COLORS['gradient_info']};
        color: white;
    }}
    
    /* 隐藏Streamlit默认元素 */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* 响应式设计 */
    @media (max-width: 768px) {{
        .dashboard-title {{
            font-size: 2rem;
        }}
        
        .section-title {{
            font-size: 1.25rem;
        }}
    }}
</style>
"""

def apply_dark_theme():
    """应用深色主题"""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def create_metric_card(label, value, delta=None, card_type='primary'):
    """创建指标卡片
    
    Args:
        label: 标签
        value: 值
        delta: 变化值
        card_type: 'primary', 'success', 'warning', 'info'
    """
    import streamlit as st
    
    card_class = f'metric-card metric-card-{card_type}'
    
    html = f"""
    <div class="{card_class}">
        <div style="color: {COLORS['text_secondary']}; font-size: 0.875rem; font-weight: 600; margin-bottom: 0.5rem;">
            {label}
        </div>
        <div style="color: {COLORS['text_primary']}; font-size: 2rem; font-weight: 700;">
            {value}
        </div>
        {f'<div style="color: {COLORS["accent_success"]}; font-size: 0.875rem; margin-top: 0.5rem;">{delta}</div>' if delta else ''}
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)

def create_gradient_card(title, content, gradient_type='primary'):
    """创建渐变卡片
    
    Args:
        title: 标题
        content: 内容
        gradient_type: 'primary', 'success', 'warning', 'info'
    """
    import streamlit as st
    
    html = f"""
    <div class="gradient-card-{gradient_type}">
        <h3 style="margin: 0 0 1rem 0; font-size: 1.25rem; font-weight: 600;">{title}</h3>
        <div style="font-size: 0.9rem; line-height: 1.6;">{content}</div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)

def create_status_badge(text, status='info'):
    """创建状态徽章
    
    Args:
        text: 文本
        status: 'success', 'warning', 'info'
    """
    import streamlit as st
    
    html = f"""
    <span class="status-badge status-{status}">{text}</span>
    """
    
    return html

def create_dashboard_header(title, subtitle=None):
    """创建仪表板头部
    
    Args:
        title: 主标题
        subtitle: 副标题
    """
    import streamlit as st
    
    html = f"""
    <div style="margin-bottom: 2rem;">
        <h1 class="dashboard-title">{title}</h1>
        {f'<p style="color: {COLORS["text_secondary"]}; font-size: 1.125rem; margin-top: 0.5rem;">{subtitle}</p>' if subtitle else ''}
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)

def create_section_title(title, icon=None):
    """创建章节标题
    
    Args:
        title: 标题
        icon: 图标（emoji）
    """
    import streamlit as st
    
    html = f"""
    <div class="section-title">
        {f'{icon} ' if icon else ''}{title}
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)

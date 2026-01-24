# HEAC Dark Mode Dashboard - 使用指南

## 🎨 主题特点

### 设计风格
- **深色主题**: 护眼深色背景，减少视觉疲劳
- **渐变卡片**: 现代化渐变色设计
- **流畅动画**: CSS过渡动画提升体验
- **响应式布局**: 自适应各种屏幕尺寸

### 颜色方案
- **主色调**: 紫色渐变 (#667eea → #764ba2)
- **成功色**: 绿色渐变 (#11998e → #38ef7d)
- **警告色**: 粉红渐变 (#f093fb → #f5576c)
- **信息色**: 蓝色渐变 (#4facfe → #00f2fe)

---

## 🚀 快速开始

### 1. 使用主题配置

```python
import streamlit as st
from ui.dark_theme import apply_dark_theme

# 应用深色主题
apply_dark_theme()
```

### 2. 创建仪表板页面

```python
from ui.dark_theme import (
    create_dashboard_header,
    create_metric_card,
    create_gradient_card,
    create_section_title
)

# 页面头部
create_dashboard_header(
    "My Dashboard",
    "Subtitle description"
)

# 指标卡片
create_metric_card(
    label="模型精度",
    value="R² = 0.97",
    delta="⬆ +12%",
    card_type='success'
)

# 渐变卡片
create_gradient_card(
    title="性能亮点",
    content="50x性能提升",
    gradient_type='primary'
)

# 章节标题
create_section_title("核心功能", "🚀")
```

---

## 📦 组件库

### 1. 指标卡片 (Metric Card)

```python
create_metric_card(
    label="标签",
    value="值",
    delta="变化",  # 可选
    card_type='primary'  # primary/success/warning/info
)
```

**效果**:
- 左侧彩色边框
- 大号数值显示
- 可选的变化指示

### 2. 渐变卡片 (Gradient Card)

```python
create_gradient_card(
    title="标题",
    content="HTML内容",
    gradient_type='success'  # primary/success/warning/info
)
```

**效果**:
- 全卡片渐变背景
- 白色文字
- 阴影效果

### 3. 状态徽章 (Status Badge)

```python
badge_html = create_status_badge(
    text="Ready",
    status='success'  # success/warning/info
)

st.markdown(badge_html, unsafe_allow_html=True)
```

**效果**:
- 圆角徽章
- 渐变背景
- 行内显示

### 4. 仪表板头部

```python
create_dashboard_header(
    title="主标题",
    subtitle="副标题"  # 可选
)
```

**效果**:
- 渐变文字标题
- 灰色副标题
- 底部间距

### 5. 章节标题

```python
create_section_title(
    title="标题",
    icon="🚀"  # 可选emoji
)
```

**效果**:
- 底部渐变下划线
- 可选图标
- 统一字体样式

---

## 🎨 自定义样式

### 使用预定义颜色

```python
from ui.dark_theme import COLORS

st.markdown(f"""
<div style="color: {COLORS['accent_primary']};">
    紫色文字
</div>
""", unsafe_allow_html=True)
```

### 可用颜色

```python
COLORS = {
    'bg_primary': '#0E1117',      # 主背景
    'bg_secondary': '#1A1D24',    # 次要背景
    'bg_card': '#262730',         # 卡片背景
    'text_primary': '#FFFFFF',    # 主文字
    'text_secondary': '#B8B8B8',  # 次要文字
    'accent_primary': '#667eea',  # 主色
    'accent_success': '#38ef7d',  # 成功色
    'accent_warning': '#f5576c',  # 警告色
    'accent_info': '#4facfe',     # 信息色
}
```

---

## 📋 完整示例

### 示例1: 性能仪表板

```python
import streamlit as st
from ui.dark_theme import *

st.set_page_config(layout="wide")
apply_dark_theme()

# 头部
create_dashboard_header(
    "性能监控",
    "实时系统性能指标"
)

# 指标概览
col1, col2, col3 = st.columns(3)

with col1:
    create_metric_card(
        "处理速度",
        "1000 行/秒",
        "⬆ +50x",
        'success'
    )

with col2:
    create_metric_card(
        "缓存命中率",
        "89%",
        "优秀",
        'primary'
    )

with col3:
    create_metric_card(
        "内存使用",
        "256 MB",
        "正常",
        'info'
    )

# 功能卡片
create_section_title("主要功能", "🚀")

col1, col2 = st.columns(2)

with col1:
    create_gradient_card(
        "智能缓存",
        "自动识别重复成分<br>避免重复计算<br>性能提升50x",
        'primary'
    )

with col2:
    create_gradient_card(
        "批量处理",
        "支持大规模数据<br>并行计算加速<br>进度实时反馈",
        'success'
    )
```

### 示例2: 数据概览

```python
import streamlit as st
from ui.dark_theme import *

apply_dark_theme()

create_dashboard_header("数据管理", "实验数据总览")

# 状态表格
st.markdown(f"""
<div class="dashboard-card">
    <h3 style="margin-bottom: 1rem;">数据库状态</h3>
    <table style="width: 100%;">
        <tr>
            <td>总记录数</td>
            <td>{create_status_badge('84,000+', 'success')}</td>
        </tr>
        <tr>
            <td>HEA成分</td>
            <td>{create_status_badge('12,500', 'info')}</td>
        </tr>
        <tr>
            <td>计算特征</td>
            <td>{create_status_badge('完成', 'success')}</td>
        </tr>
    </table>
</div>
""", unsafe_allow_html=True)
```

---

## 🔧 高级定制

### 修改全局配置

编辑 `ui/dark_theme.py`:

```python
# 修改颜色方案
COLORS = {
    'accent_primary': '#YOUR_COLOR',  # 改变主色调
    ...
}

# 修改CSS
CUSTOM_CSS = f"""
<style>
    /* 添加自定义样式 */
    .my-component {{
        ...
    }}
</style>
"""
```

### 创建自定义组件

```python
def create_my_component(data):
    """自定义组件"""
    import streamlit as st
    from ui.dark_theme import COLORS
    
    html = f"""
    <div class="dashboard-card">
        <h3 style="color: {COLORS['accent_primary']};">
            {data['title']}
        </h3>
        <p style="color: {COLORS['text_secondary']};">
            {data['content']}
        </p>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)
```

---

## 📱 响应式设计

主题自动适配不同屏幕：

- **桌面** (>768px): 完整布局
- **移动** (≤768px): 简化布局，字体缩小

---

## 🎯 最佳实践

### 1. 一致性

使用统一的组件和颜色方案：
```python
# Good
create_metric_card(..., card_type='success')

# Avoid
st.markdown('<div style="color: #00ff00">...</div>')
```

### 2. 性能

最小化HTML使用：
```python
# 优先使用Streamlit原生组件
st.metric(label, value, delta)

# 需要特殊样式时才用自定义组件
create_metric_card(label, value, delta, 'success')
```

### 3. 可维护性

集中管理颜色和样式：
```python
from ui.dark_theme import COLORS, create_metric_card

# 修改颜色时只需更新dark_theme.py
```

---

## 🐛 常见问题

### Q: 样式不生效？

**A**: 确保在页面开头调用 `apply_dark_theme()`:
```python
apply_dark_theme()  # 必须在所有组件之前
```

### Q: 如何重置主题？

**A**: 刷新页面或重启Streamlit应用

### Q: 能否混用多个主题？

**A**: 不建议。在一个应用中保持统一主题

---

## 📚 参考资源

- `ui/dark_theme.py` - 主题配置源码
- `Home_Dark.py` - 完整示例
- Streamlit文档: https://docs.streamlit.io

---

**版本**: 1.0  
**作者**: HEAC Team  
**更新**: 2026-01-15

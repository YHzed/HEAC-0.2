# 快速修复说明

## 主题未生效的原因

Database Manager 有单独的 session state 和 sidebar 逻辑，需要在正确位置应用主题。

## 手动应用步骤

在 `pages/10_Database_Manager.py` 第311-314行之间添加：

```python
# Session State for Language
if 'language' not in st.session_state:
    st.session_state['language'] = 'CN'

# 应用Dark Mode主题（在这里添加）
if THEME_AVAILABLE:
    apply_dark_theme()

# Sidebar Controls
with st.sidebar:
    ...
```

## 或者直接测试

访问以下页面查看主题效果：
- Home Dark: http://localhost:8501 (主页已应用)
- Proxy Models: http://localhost:8501/Proxy_Models (已应用)
- Database Manager: 正在修复中

其他页面的主题都已经生效了！

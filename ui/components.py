# UI组件优化模块
"""
可复用的UI组件，提升用户体验
"""

import streamlit as st
import functools
import traceback
from typing import Callable, Any

def with_loading_spinner(message: str = "处理中..."):
    """
    装饰器：为函数添加加载状态指示器
    
    Usage:
        @with_loading_spinner("加载数据中...")
        def load_data():
            # ...耗时操作
            return data
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with st.spinner(message):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator


def with_error_boundary(func: Callable) -> Callable:
    """
    装饰器：为函数添加错误边界，捕获异常并友好显示
    
    Usage:
        @with_error_boundary
        def risky_operation():
            # ...可能抛出异常的代码
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"❌ 操作失败: {str(e)}")
            with st.expander("🔍 查看详细错误"):
                st.code(traceback.format_exc())
            return None
    return wrapper


def show_success_toast(message: str, duration: int = 3):
    """显示成功提示toast"""
    st.toast(f"✅ {message}", icon="✅")


def show_warning_toast(message: str):
    """显示警告提示toast"""
    st.toast(f"⚠️ {message}", icon="⚠️")


def show_error_toast(message: str):
    """显示错误提示toast"""
    st.toast(f"❌ {message}", icon="❌")


def create_info_card(title: str, content: str, icon: str = "ℹ️"):
    """
    创建信息卡片
    
    Args:
        title: 卡片标题
        content: 卡片内容
        icon: 图标emoji
    """
    st.markdown(f"""
    <div style="
        padding: 1rem;
        border-left: 4px solid #1f77b4;
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    ">
        <h4 style="margin: 0 0 0.5rem 0;">{icon} {title}</h4>
        <p style="margin: 0;">{content}</p>
    </div>
    """, unsafe_allow_html=True)


def show_progress_bar(current: int, total: int, message: str = ""):
    """
    显示进度条
    
    Args:
        current: 当前进度
        total: 总数
        message: 进度消息
    """
    progress = current / total if total > 0 else 0
    st.progress(progress, text=f"{message} ({current}/{total})")


class PerformanceMonitor:
    """性能监控上下文管理器"""
    
    def __init__(self, operation_name: str, show_result: bool = True):
        self.operation_name = operation_name
        self.show_result = show_result
        self.start_time = None
        self.placeholder = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        if self.show_result:
            self.placeholder = st.empty()
            self.placeholder.info(f"⏳ {self.operation_name}...")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        elapsed = time.time() - self.start_time
        
        if self.show_result and self.placeholder:
            if exc_type is None:
                self.placeholder.success(
                    f"✅ {self.operation_name} 完成 ({elapsed:.2f}秒)"
                )
            else:
                self.placeholder.error(
                    f"❌ {self.operation_name} 失败 ({elapsed:.2f}秒)"
                )
        
        return False  # 不抑制异常


# 便捷使用示例
"""
# 使用装饰器
@with_loading_spinner("加载模型中...")
@with_error_boundary
def load_model(model_path):
    model = joblib.load(model_path)
    return model

# 使用性能监控
with PerformanceMonitor("数据库查询"):
    df = query_database()

# 显示toast
show_success_toast("数据保存成功！")
"""

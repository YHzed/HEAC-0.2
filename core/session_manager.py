# Session State管理模块
"""
自动管理Streamlit Session State，防止内存泄漏
"""

import streamlit as st
import time
from typing import List, Optional

class SessionManager:
    """Session State生命周期管理"""
    
    # 需要清理的大型数据键
    LARGE_DATA_KEYS = [
        'df_model',           # Model Training的训练数据
        'X_train', 'X_test',  # 训练/测试集
        'y_train', 'y_test',
        'all_candidates',     # Virtual Screening的全部候选
        'top_candidates',
        'screener',           # VirtualScreening对象
        'trained_model',      # 训练好的模型
        'shap_values',        # SHAP分析结果
        'optuna_study'        # Optuna优化历史
    ]
    
    @staticmethod
    def init_session_state():
        """初始化session state元数据"""
        if 'session_init_time' not in st.session_state:
            st.session_state.session_init_time = time.time()
        
        if 'data_access_times' not in st.session_state:
            st.session_state.data_access_times = {}
    
    @staticmethod
    def mark_data_accessed(key: str):
        """标记数据最后访问时间"""
        if 'data_access_times' not in st.session_state:
            st.session_state.data_access_times = {}
        st.session_state.data_access_times[key] = time.time()
    
    @staticmethod
    def cleanup_old_data(max_age_seconds: int = 1800):
        """
        清理超过30分钟未使用的大型数据
        
        Args:
            max_age_seconds: 最大数据年龄（秒），默认1800秒=30分钟
        """
        if 'data_access_times' not in st.session_state:
            return
        
        current_time = time.time()
        keys_to_delete = []
        
        for key in SessionManager.LARGE_DATA_KEYS:
            if key in st.session_state:
                last_access = st.session_state.data_access_times.get(key, 0)
                age = current_time - last_access
                
                if age > max_age_seconds:
                    keys_to_delete.append(key)
        
        # 执行删除
        for key in keys_to_delete:
            del st.session_state[key]
            if key in st.session_state.data_access_times:
                del st.session_state.data_access_times[key]
        
        return len(keys_to_delete)
    
    @staticmethod
    def get_session_info() -> dict:
        """获取session信息"""
        SessionManager.init_session_state()
        
        current_time = time.time()
        session_age = current_time - st.session_state.session_init_time
        
        # 统计大型数据
        large_data_count = 0
        large_data_list = []
        for key in SessionManager.LARGE_DATA_KEYS:
            if key in st.session_state:
                large_data_count += 1
                last_access = st.session_state.data_access_times.get(key, 0)
                age = current_time - last_access if last_access > 0 else session_age
                large_data_list.append({
                    'key': key,
                    'age_minutes': age / 60
                })
        
        return {
            'session_age_minutes': session_age / 60,
            'total_keys': len(st.session_state),
            'large_data_count': large_data_count,
            'large_data_details': large_data_list
        }
    
    @staticmethod
    def auto_cleanup():
        """
        自动清理逻辑，建议在每个页面开始时调用
        """
        SessionManager.init_session_state()
        cleaned = SessionManager.cleanup_old_data(max_age_seconds=1800)
        return cleaned


# 便捷装饰器
def with_session_cleanup(func):
    """装饰器：在函数执行前自动清理session"""
    def wrapper(*args, **kwargs):
        SessionManager.auto_cleanup()
        return func(*args, **kwargs)
    return wrapper

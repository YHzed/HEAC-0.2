# Database Manager 分页查询辅助函数
"""
为Database Manager Tab5添加分页和后端过滤功能
"""

import streamlit as st
import pandas as pd
from typing import Optional, Tuple

@st.cache_data(ttl=60)
def query_experiments_paginated(
    _db_manager,
    binder_type: Optional[str] = None,
    min_hv: Optional[float] = None,
    max_hv: Optional[float] = None,
    min_kic: Optional[float] = None,
    max_kic: Optional[float] = None,
    search_keyword: Optional[str] = None,
    page_num: int = 1,
    page_size: int = 100
) -> Tuple[pd.DataFrame, int]:
    """
    分页查询实验数据，带后端过滤
    
    Returns:
        (DataFrame, total_count): 当前页数据和总记录数
    """
    from core.db_models import Experiment, Composition, CalculatedFeature
    
    session = _db_manager.Session()
    try:
        # 构建基础查询
        query = session.query(Experiment)
        
        # 应用过滤条件
        filters = []
        
        if binder_type and binder_type != 'All':
            # Join Composition表
            query = query.join(Composition, Experiment.id == Composition.exp_id)
            if binder_type == 'HEA':
                filters.append(Composition.is_hea == True)
            else:
                filters.append(Composition.is_hea == False)
        
        if min_hv is not None:
            filters.append(Experiment.hv >= min_hv)
        if max_hv is not None:
            filters.append(Experiment.hv <= max_hv)
        if min_kic is not None:
            filters.append(Experiment.kic >= min_kic)
        if max_kic is not None:
            filters.append(Experiment.kic <= max_kic)
        
        if search_keyword:
            filters.append(Experiment.raw_composition.like(f'%{search_keyword}%'))
        
        # 应用所有过滤
        for f in filters:
            query = query.filter(f)
        
        # 获取总数
        total_count = query.count()
        
        # 分页
        offset = (page_num - 1) * page_size
        results = query.limit(page_size).offset(offset).all()
        
        # 转换为DataFrame
        data = []
        for exp in results:
            # 获取关联数据
            comp = session.query(Composition).filter_by(exp_id=exp.id).first()
            feat = session.query(CalculatedFeature).filter_by(exp_id=exp.id).first()
            
            row = {
                'ID': exp.id,
                'Composition': exp.raw_composition[:60] if exp.raw_composition else '',
                'Ceramic': comp.ceramic_formula if comp else '',
                'Binder': comp.binder_formula if comp else '',
                'HEA': 'Yes' if (comp and comp.is_hea) else 'No',
                'HV': exp.hv,
                'KIC': exp.kic,
                'TRS': exp.trs,
                'Temp_C': exp.sinter_temp_c,
                'Grain_um': exp.grain_size_um,
                'Source': exp.source_id
            }
            
            # 添加代理特征
            if feat:
                row['Pred_Formation'] = feat.pred_formation_energy
                row['Pred_Lattice'] = feat.pred_lattice_param
                row['Pred_Magnetic'] = feat.pred_magnetic_moment
            
            data.append(row)
        
        df = pd.DataFrame(data)
        return df, total_count
        
    finally:
        session.close()


def create_pagination_controls(total_count: int, page_size: int, current_page: int) -> int:
    """
    创建分页控件
    
    Returns:
        新的页码
    """
    total_pages = (total_count - 1) // page_size + 1 if total_count > 0 else 1
    
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col1:
        if st.button("⏮️ 首页", disabled=(current_page == 1)):
            return 1
    
    with col2:
        if st.button("◀️ 上一页", disabled=(current_page == 1)):
            return max(1, current_page - 1)
    
    with col3:
        st.markdown(f"<div style='text-align: center; padding-top: 0.5rem;'>第 **{current_page}** / {total_pages} 页 (共 {total_count} 条)</div>", unsafe_allow_html=True)
    
    with col4:
        if st.button("下一页 ▶️", disabled=(current_page >= total_pages)):
            return min(total_pages, current_page + 1)
    
    with col5:
        if st.button("末页 ⏭️", disabled=(current_page >= total_pages)):
            return total_pages
    
    return current_page

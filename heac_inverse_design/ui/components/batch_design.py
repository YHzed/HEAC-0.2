"""
批量设计界面组件

提供CSV上传和批量任务管理UI。
"""

import streamlit as st
import pandas as pd
from typing import List


def batch_design_panel():
    """批量设计面板"""
    
    st.header("📋 批量设计")
    st.markdown("一次性设计多组目标配方")
    
    # 选择输入方式
    input_method = st.radio(
        "输入方式",
        ["CSV上传", "表格输入"],
        horizontal=True
    )
    
    tasks_df = None
    
    if input_method == "CSV上传":
        st.markdown("**CSV格式示例**:")
        st.code("""Name,HV_Min,HV_Max,KIC_Min,KIC_Max
High Hardness,1800,2000,8,10
Balanced,1600,1800,10,13
High Toughness,1500,1700,12,15""")
        
        uploaded_file = st.file_uploader(
            "上传CSV文件",
            type=['csv'],
            help="包含多组设计目标的CSV文件"
        )
        
        if uploaded_file:
            try:
                tasks_df = pd.read_csv(uploaded_file)
                st.success(f"✅ 成功加载 {len(tasks_df)} 个任务")
                st.dataframe(tasks_df)
            except Exception as e:
                st.error(f"CSV读取失败: {e}")
    
    else:  # 表格输入
        st.markdown("**在表格中输入设计目标**:")
        
        # 创建可编辑表格
        num_tasks = st.number_input("任务数量", 1, 10, 3)
        
        default_data = pd.DataFrame({
            'Name': [f'Task {i+1}' for i in range(num_tasks)],
            'HV_Min': [1500] * num_tasks,
            'HV_Max': [2000] * num_tasks,
            'KIC_Min': [8.0] * num_tasks,
            'KIC_Max': [15.0] * num_tasks
        })
        
        tasks_df = st.data_editor(
            default_data,
            use_container_width=True,
            num_rows="dynamic"
        )
    
    return tasks_df


def show_batch_results(results_df: pd.DataFrame, all_solutions: List):
    """
    显示批量设计结果
    
    Args:
        results_df: 汇总结果DataFrame
        all_solutions: 所有设计方案列表
    """
    st.subheader("📊 批量设计结果")
    
    # 汇总表格
    st.dataframe(
        results_df.style.background_gradient(
            subset=['Best_HV', 'Best_KIC'],
            cmap='YlGnBu'
        ),
        use_container_width=True
    )
    
    # 统计信息
    col1, col2, col3 = st.columns(3)
    col1.metric("总任务数", len(results_df))
    col2.metric("成功任务", len(results_df[results_df['Status'] == 'OK']))
    col3.metric("总方案数", len(all_solutions))
    
    # 导出选项
    st.subheader("📥 导出结果")
    
    # 汇总表格导出
    csv_summary = results_df.to_csv(index=False)
    st.download_button(
        label="下载汇总表格 (CSV)",
        data=csv_summary,
        file_name="batch_design_summary.csv",
        mime="text/csv"
    )
    
    # 所有方案导出
    from heac_inverse_design.ui.visualizations import export_solutions_to_csv
    csv_all = export_solutions_to_csv(all_solutions)
    st.download_button(
        label="下载所有方案 (CSV)",
        data=csv_all,
        file_name="batch_design_all_solutions.csv",
        mime="text/csv"
    )

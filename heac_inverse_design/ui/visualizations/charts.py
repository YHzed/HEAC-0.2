"""
可视化组件 - 成分雷达图和其他图表
"""

import plotly.graph_objects as go
import numpy as np
from typing import Dict, List


def plot_composition_radar(composition: Dict[str, float], title: str = "Composition") -> go.Figure:
    """
    绘制成分雷达图
    
    Args:
        composition: 元素->分数字典
        title: 图表标题
        
    Returns:
        Plotly图表对象
    """
    # 过滤小于0.1%的元素
    comp_filtered = {k: v for k, v in composition.items() if v > 0.001}
    
    if not comp_filtered:
        return None
    
    elements = list(comp_filtered.keys())
    fractions = list(comp_filtered.values())
    
    # 闭合雷达图
    elements_closed = elements + [elements[0]]
    fractions_closed = fractions + [fractions[0]]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=fractions_closed,
        theta=elements_closed,
        fill='toself',
        name=title,
        line=dict(color='rgb(99, 110, 250)', width=2),
        fillcolor='rgba(99, 110, 250, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(fractions) * 1.1]
            )
        ),
        showlegend=False,
        title=title,
        height=400
    )
    
    return fig


def plot_pareto_front_interactive(solutions: List, highlight_index: int = None) -> go.Figure:
    """
    绘制交互式Pareto前沿图
    
    Args:
        solutions: 设计方案列表
        highlight_index: 高亮显示的解索引
        
    Returns:
        Plotly图表对象
    """
    hvs = [s.predicted_hv for s in solutions]
    kics = [s.predicted_kic for s in solutions]
    
    # 主散点图
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hvs,
        y=kics,
        mode='markers',
        marker=dict(
            size=10,
            color=kics,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="KIC<br>(MPa·m½)")
        ),
        text=[f"Solution {i+1}<br>HV: {h:.0f}<br>KIC: {k:.2f}" 
              for i, (h, k) in enumerate(zip(hvs, kics))],
        hovertemplate='<b>%{text}</b><extra></extra>',
        name='Pareto Solutions'
    ))
    
    # 高亮显示特定解
    if highlight_index is not None and highlight_index < len(solutions):
        fig.add_trace(go.Scatter(
            x=[hvs[highlight_index]],
            y=[kics[highlight_index]],
            mode='markers',
            marker=dict(
                size=15,
                color='red',
                symbol='star',
                line=dict(color='white', width=2)
            ),
            name='Selected',
            hovertemplate=f'<b>Selected Solution</b><br>HV: {hvs[highlight_index]:.0f}<br>KIC: {kics[highlight_index]:.2f}<extra></extra>'
        ))
    
    fig.update_layout(
        title="Pareto Front - Multi-Objective Optimization",
        xaxis_title="Hardness (HV)",
        yaxis_title="Fracture Toughness (KIC, MPa·m½)",
        height=500,
        hovermode='closest'
    )
    
    return fig


def plot_process_parameters(solution) -> go.Figure:
    """
    绘制工艺参数柱状图
    
    Args:
        solution: 设计方案对象
        
    Returns:
        Plotly图表对象
    """
    # 准备数据：显示值 vs 绘图值
    plot_keys = ['Ceramic Vol %', 'Grain Size (μm)', 'Sinter Temp (°C)']
    
    # 真实值（用于显示）
    real_values = [
        solution.ceramic_vol * 100,
        solution.grain_size,
        solution.sinter_temp
    ]
    
    # 绘图值（缩放以适应同一坐标系）
    # 将温度除以20，使其落在 ~70 左右 (1400/20 = 70)，与体积(50-70)和晶粒尺寸(1-5)更协调
    plot_values = [
        real_values[0],
        real_values[1],
        real_values[2] / 20.0 
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=plot_keys,
        y=plot_values,
        marker=dict(
            color=['#636EFA', '#EF553B', '#00CC96'],
            opacity=0.7
        ),
        # 显示真实值
        text=[f"{v:.1f}" for v in real_values],
        textposition='outside',
        # 自定义hover信息
        hovertemplate='%{x}<br>Value: %{text}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Process Parameters",
        yaxis_title="Value (scaled)",
        height=300,
        showlegend=False
    )
    
    return fig


def export_solutions_to_csv(solutions: List, filename: str = "designs.csv"):
    """
    导出设计方案到CSV
    
    Args:
        solutions: 方案列表
        filename: 文件名
        
    Returns:
        CSV内容（字符串）
    """
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 表头
    if solutions:
        sample_comp = solutions[0].composition
        element_cols = list(sample_comp.keys())
        header = ['Solution_ID', 'HV', 'KIC'] + element_cols + \
                 ['Grain_Size_um', 'Ceramic_Vol_Fraction', 'Sinter_Temp_C']
        writer.writerow(header)
        
        # 数据行
        for i, sol in enumerate(solutions, 1):
            row = [
                i,
                f"{sol.predicted_hv:.2f}",
                f"{sol.predicted_kic:.2f}"
            ] + [f"{sol.composition.get(el, 0):.4f}" for el in element_cols] + [
                f"{sol.grain_size:.2f}",
                f"{sol.ceramic_vol:.4f}",
                f"{sol.sinter_temp:.1f}"
            ]
            writer.writerow(row)
    
    return output.getvalue()

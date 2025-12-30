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
    
    # 陶瓷体积 (0-1)
    fig.add_trace(go.Bar(
        x=['Ceramic Vol %'],
        y=[solution.ceramic_vol * 100],
        name='Vol %',
        marker_color='#636EFA',
        text=[f"{solution.ceramic_vol*100:.1f}%"],
        textposition='auto',
        hovertemplate='<b>Ceramic Vol</b>: %{text}<extra></extra>'
    ))
    
    # 晶粒尺寸 (0.5-5) - 使用次坐标轴
    fig.add_trace(go.Bar(
        x=['Grain Size (μm)'],
        y=[solution.grain_size],
        name='Grain Size',
        marker_color='#EF553B',
        text=[f"{solution.grain_size:.2f}"],
        textposition='auto',
        hovertemplate='<b>Grain Size</b>: %{text} μm<extra></extra>',
        yaxis='y2'
    ))
    
    # 烧结温度 (1300-1600) - 使用第三坐标轴或标准化
    # 为了简化，我们把温度作为单独的指标或者让它除以100显示，但Tooltip显示真实的
    # 最好的办法是使用Subplots或者Multiple Y-axes，但Plotly Bar chart多Y轴比较拥挤
    # 既然只有三个，我们用Normalized Bar Chart (Percent of Max Range)
    
    # 重新设计：使用三个Gauge图或者Bullet Chart可能更好，但为了保持Bar风格，我们用Separate Subplots
    from plotly.subplots import make_subplots
    fig = make_subplots(rows=1, cols=3, 
                        shared_yaxes=False,
                        subplot_titles=('Ceramic Vol %', 'Grain Size (μm)', 'Sinter Temp (°C)'))

    fig.add_trace(go.Bar(
        x=['Value'], y=[solution.ceramic_vol * 100],
        marker_color='#636EFA',
        text=[f"{solution.ceramic_vol*100:.1f}"],
        textposition='auto',
        name='Vol %'
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=['Value'], y=[solution.grain_size],
        marker_color='#EF553B',
        text=[f"{solution.grain_size:.2f}"],
        textposition='auto',
        name='Grain Size'
    ), row=1, col=2)

    fig.add_trace(go.Bar(
        x=['Value'], y=[solution.sinter_temp],
        marker_color='#00CC96',
        text=[f"{solution.sinter_temp:.0f}"],
        textposition='auto',
        name='Temp'
    ), row=1, col=3)

    fig.update_layout(
        height=250,
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    # Update y-axes ranges to look good (optional)
    fig.update_yaxes(range=[0, 100], row=1, col=1)
    fig.update_yaxes(range=[0, 10], row=1, col=2)
    fig.update_yaxes(range=[1200, 1700], row=1, col=3) # Temperature range optimization
    
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

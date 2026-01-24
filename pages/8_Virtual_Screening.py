import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
from pathlib import Path

# 确保core可被导入
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.virtual_screening import VirtualScreening, format_composition_string

# ========== 性能优化: 模型资源缓存 ==========
@st.cache_resource
def load_screening_model(model_path: str):
    """缓存虚拟筛选模型 - 避免重复加载"""
    return VirtualScreening(model_path)

@st.cache_data(ttl=300)  # 缓存5分钟
def load_model_metadata(models_dir: Path) -> list:
    """缓存模型元数据"""
    import joblib
    model_files = list(models_dir.glob("*.pkl"))
    model_info = []
    for model_file in model_files:
        try:
            model_pkg = joblib.load(model_file)
            model_info.append({
                'path': str(model_file),
                'name': model_file.stem,
                'target': model_pkg.get('target_name', 'Unknown'),
                'cv_score': model_pkg.get('cv_score', None),
                'n_features': len(model_pkg.get('feature_names', []))
            })
        except Exception as e:
            pass  # 静默跳过无效模型
    return model_info

st.set_page_config(page_title="Virtual Screening", page_icon="🔬", layout="wide")

import ui.style_manager as style_manager
style_manager.apply_theme()

style_manager.ui_header("🔬 Virtual High-Throughput Screening")
st.markdown("""
**工作流程**：
1. 配置筛选参数（样本数、元素范围、工艺范围）
2. 选择训练好的模型
3. 生成虚拟配方 → 计算特征 → 预测性能 → 筛选Top N
4. 分析和导出结果

> 💡 **核心价值**：无需实验即可探索庞大的材料设计空间，发现高性能候选配方
""")

# ===================
# 侧边栏：参数配置
# ===================
with st.sidebar:
    st.header("⚙️ 筛选参数配置")
    
    # 样本数量
    n_samples = st.number_input(
        "虚拟样本数量",
        min_value=1000,
        max_value=100000,
        value=50000,
        step=1000,
        help="生成的虚拟配方数量，越多越能覆盖设计空间"
    )
    
    st.divider()
    
    # 粘结相元素选择
    st.subheader("粘结相元素")
    available_elements = ['Co', 'Cr', 'Fe', 'Ni', 'Mo', 'Ti', 'Al', 'V', 'Mn', 'W']
    
    selected_elements = st.multiselect(
        "选择粘结相元素",
        options=available_elements,
        default=['Co', 'Cr', 'Fe', 'Ni', 'Mo'],
        help="典型HEA元素：Co-Cr-Fe-Ni-Mo"
    )
    
    st.divider()
    
    # 硬质相选择
    st.subheader("硬质相")
    ceramic_type = st.selectbox(
        "选择硬质相类型",
        options=['WC', 'TiC', 'TaC', 'NbC', 'Cr3C2', 'VC'],
        index=0,
        help="碳化物硬质相"
    )
    
    st.divider()
    
    # 参数范围设置
    st.subheader("工艺参数范围")
    
    col1, col2 = st.columns(2)
    with col1:
        temp_min = st.number_input("烧结温度最小值 (°C)", value=1300, step=10)
    with col2:
        temp_max = st.number_input("烧结温度最大值 (°C)", value=1600, step=10)
    
    col1, col2 = st.columns(2)
    with col1:
        grain_min = st.number_input("晶粒尺寸最小值 (μm)", value=0.5, step=0.1)
    with col2:
        grain_max = st.number_input("晶粒尺寸最大值 (μm)", value=3.0, step=0.1)
    
    col1, col2 = st.columns(2)
    with col1:
        binder_min = st.number_input("粘结相含量最小值 (wt%)", value=5.0, step=1.0)
    with col2:
        binder_max = st.number_input("粘结相含量最大值 (wt%)", value=30.0, step=1.0)
    
    param_ranges = {
        'sinter_temp': (temp_min, temp_max),
        'grain_size': (grain_min, grain_max),
        'binder_wt_pct': (binder_min, binder_max)
    }
    
    st.divider()
    
    # Top N 设置
    n_top = st.slider(
        "筛选 Top N 配方",
        min_value=5,
        max_value=50,
        value=10,
        help="返回预测性能最高的N个配方"
    )

# ===================
# 主区域：模型选择
# ===================
st.header("📂 Step 1: 选择训练好的模型")

models_dir = Path("models")
if not models_dir.exists():
    st.error(f"模型目录不存在: {models_dir}")
    st.stop()

# 扫描模型文件
model_files = list(models_dir.glob("*.pkl"))

if not model_files:
    st.error(f"未找到模型文件（.pkl）在 {models_dir} 目录中")
    st.info("💡 请先在 'Model Training' 页面训练并保存模型")
    st.stop()

# 使用缓存加载模型元数据
model_info = load_model_metadata(models_dir)

if not model_info:
    st.error("无法加载任何模型")
    st.stop()

# 模型信息表格
model_df = pd.DataFrame(model_info)
st.dataframe(model_df[['name', 'target', 'cv_score', 'n_features']], use_container_width=True)

# 模型选择
selected_model_name = st.selectbox(
    "选择模型",
    options=[m['name'] for m in model_info],
    format_func=lambda x: f"{x} ({next(m['target'] for m in model_info if m['name'] == x)})"
)

selected_model_path = next(m['path'] for m in model_info if m['name'] == selected_model_name)

# ===================
# 执行虚拟筛选
# ===================
st.header("🚀 Step 2: 执行虚拟筛选")

# 参数验证
if len(selected_elements) == 0:
    st.error("请至少选择一个粘结相元素")
    st.stop()

if temp_min >= temp_max or grain_min >= grain_max or binder_min >= binder_max:
    st.error("参数范围设置错误：最小值必须小于最大值")
    st.stop()

# 显示配置摘要
with st.expander("📋 查看筛选配置", expanded=False):
    st.json({
        "样本数量": n_samples,
        "粘结相元素": selected_elements,
        "硬质相类型": ceramic_type,
        "烧结温度范围 (°C)": param_ranges['sinter_temp'],
        "晶粒尺寸范围 (μm)": param_ranges['grain_size'],
        "粘结相含量范围 (wt%)": param_ranges['binder_wt_pct'],
        "返回Top": n_top
    })

if st.button("🔬 开始虚拟筛选", type="primary"):
    try:
        # 使用缓存加载模型
        with st.spinner("加载模型..."):
            screener = load_screening_model(str(selected_model_path))
        
        st.success(f"✓ 模型已加载: {screener.target_name}")
        
        # 执行筛选
        with st.spinner(f"执行虚拟筛选（{n_samples:,} 样本）..."):
            # 捕获print输出到Streamlit
            import io
            import contextlib
            
            output_buffer = io.StringIO()
            
            with contextlib.redirect_stdout(output_buffer):
                top_candidates, all_candidates = screener.run_screening(
                    n_samples=n_samples,
                    n_top=n_top,
                    param_ranges=param_ranges,
                    binder_elements=selected_elements,
                    ceramic_type=ceramic_type,
                    return_all=True
                )
            
            # 显示输出
            with st.expander("📝 筛选日志"):
                st.text(output_buffer.getvalue())
        
        # 保存到session_state
        st.session_state.top_candidates = top_candidates
        st.session_state.all_candidates = all_candidates
        st.session_state.screener = screener
        
        st.success(f"✅ 筛选完成！发现 Top {n_top} 配方")
        
    except Exception as e:
        st.error(f"筛选失败: {e}")
        import traceback
        with st.expander("查看完整错误信息"):
            st.code(traceback.format_exc())

# ===================
# 结果展示
# ===================
if 'top_candidates' in st.session_state:
    st.header(f"📊 Step 3: Top {n_top} 候选配方")
    
    top_df = st.session_state.top_candidates
    screener = st.session_state.screener
    
    # 格式化成分字符串
    top_df['Binder_Formula'] = top_df['Binder_Composition'].apply(format_composition_string)
    
    # 显示表格
    display_cols = [
        'Ceramic_Type',
        'Binder_Formula',
        'Binder_Wt_Pct',
        'Ceramic_Wt_Pct',
        'Sinter_Temp_C',
        'Grain_Size_um',
        f'Predicted_{screener.target_name}'
    ]
    
    st.dataframe(
        top_df[display_cols].style.format({
            'Binder_Wt_Pct': '{:.2f}',
            'Ceramic_Wt_Pct': '{:.2f}',
            'Sinter_Temp_C': '{:.1f}',
            'Grain_Size_um': '{:.2f}',
            f'Predicted_{screener.target_name}': '{:.2f}'
        }),
        use_container_width=True
    )
    
    # 详细成分展示
    with st.expander("🔍 查看详细粘结相成分"):
        for idx, row in top_df.iterrows():
            rank = idx + 1
            pred_value = row[f'Predicted_{screener.target_name}']
            
            st.markdown(f"**Rank {rank}** - 预测 {screener.target_name}: **{pred_value:.2f}**")
            
            comp_dict = row['Binder_Composition']
            comp_df = pd.DataFrame(list(comp_dict.items()), columns=['Element', 'Fraction'])
            comp_df['Fraction'] = comp_df['Fraction'].apply(lambda x: f"{x:.4f}")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.dataframe(comp_df, hide_index=True)
            with col2:
                st.markdown(f"""
                - 硬质相: {row['Ceramic_Type']} ({row['Ceramic_Wt_Pct']:.2f} wt%)
                - 粘结相: {row['Binder_Formula']} ({row['Binder_Wt_Pct']:.2f} wt%)
                - 烧结温度: {row['Sinter_Temp_C']:.1f} °C
                - 晶粒尺寸: {row['Grain_Size_um']:.2f} μm
                """)
            
            st.divider()
    
    # 可视化
    st.header("📈 Step 4: 数据可视化")
    
    tab1, tab2, tab3 = st.tabs(["硬度分布", "参数分析", "成分空间"])
    
    with tab1:
        st.subheader("预测硬度分布")
        
        all_df = st.session_state.all_candidates
        
        # ========== 使用Plotly替换Matplotlib (性能优化) ==========
        import plotly.graph_objects as go
        import plotly.express as px
        
        # 创建直方图
        fig = px.histogram(
            all_df, 
            x=f'Predicted_{screener.target_name}',
            nbins=50,
            title=f'Distribution of Predicted {screener.target_name}',
            labels={f'Predicted_{screener.target_name}': screener.target_name},
            color_discrete_sequence=['skyblue']
        )
        
        # 添加Top N阈值线
        top_values = top_df[f'Predicted_{screener.target_name}']
        fig.add_vline(
            x=top_values.min(), 
            line_dash="dash", 
            line_color="red",
            annotation_text=f'Top {n_top} Threshold',
            annotation_position="top"
        )
        
        fig.update_layout(
            xaxis_title=screener.target_name,
            yaxis_title='Frequency',
            hovermode='x unified',
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 统计信息
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("平均值", f"{all_df[f'Predicted_{screener.target_name}'].mean():.2f}")
        with col2:
            st.metric("标准差", f"{all_df[f'Predicted_{screener.target_name}'].std():.2f}")
        with col3:
            st.metric("最小值", f"{all_df[f'Predicted_{screener.target_name}'].min():.2f}")
        with col4:
            st.metric("最大值", f"{all_df[f'Predicted_{screener.target_name}'].max():.2f}")
    
    with tab2:
        st.subheader("Top配方参数分析")
        
        # ========== 使用Plotly替换Matplotlib (性能优化) ==========
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # 创建2x2子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Temperature vs Performance', 'Grain Size vs Performance', 
                           'Binder Content vs Performance', 'Parameter Distributions'),
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        # 散点图颜色映射
        colors = px.colors.sequential.Viridis
        color_scale = [colors[int(i/(len(top_df)-1) * (len(colors)-1))] for i in range(len(top_df))]
        
        # 1. 烧结温度 vs 性能
        fig.add_trace(
            go.Scatter(
                x=top_df['Sinter_Temp_C'],
                y=top_df[f'Predicted_{screener.target_name}'],
                mode='markers',
                marker=dict(size=12, color=color_scale, line=dict(width=1, color='white')),
                text=[f"Rank {i+1}" for i in range(len(top_df))],
                hovertemplate='Temp: %{x:.1f}°C<br>Performance: %{y:.2f}<extra></extra>',
                showlegend=False
            ),
            row=1, col=1
        )
        
        # 2. 晶粒尺寸 vs 性能
        fig.add_trace(
            go.Scatter(
                x=top_df['Grain_Size_um'],
                y=top_df[f'Predicted_{screener.target_name}'],
                mode='markers',
                marker=dict(size=12, color=color_scale, line=dict(width=1, color='white')),
                text=[f"Rank {i+1}" for i in range(len(top_df))],
                hovertemplate='Grain: %{x:.2f}μm<br>Performance: %{y:.2f}<extra></extra>',
                showlegend=False
            ),
            row=1, col=2
        )
        
        # 3. 粘结相含量 vs 性能
        fig.add_trace(
            go.Scatter(
                x=top_df['Binder_Wt_Pct'],
                y=top_df[f'Predicted_{screener.target_name}'],
                mode='markers',
                marker=dict(size=12, color=color_scale, line=dict(width=1, color='white')),
                text=[f"Rank {i+1}" for i in range(len(top_df))],
                hovertemplate='Binder: %{x:.2f}wt%<br>Performance: %{y:.2f}<extra></extra>',
                showlegend=False
            ),
            row=2, col=1
        )
        
        # 4. 参数分布箱形图
        params = ['Sinter_Temp_C', 'Grain_Size_um', 'Binder_Wt_Pct']
        param_labels = ['Temp', 'Grain', 'Binder']
        
        for param, label in zip(params, param_labels):
            values = top_df[param].values
            norm_values = (values - values.min()) / (values.max() - values.min() + 1e-10)
            
            fig.add_trace(
                go.Box(
                    y=norm_values,
                    name=label,
                    boxmean='sd',
                    marker_color='lightblue'
                ),
                row=2, col=2
            )
        
        # 更新布局
        fig.update_xaxes(title_text="Temperature (°C)", row=1, col=1)
        fig.update_xaxes(title_text="Grain Size (μm)", row=1, col=2)
        fig.update_xaxes(title_text="Binder Content (wt%)", row=2, col=1)
        
        fig.update_yaxes(title_text=screener.target_name, row=1, col=1)
        fig.update_yaxes(title_text=screener.target_name, row=1, col=2)
        fig.update_yaxes(title_text=screener.target_name, row=2, col=1)
        fig.update_yaxes(title_text="Normalized Value (0-1)", row=2, col=2)
        
        fig.update_layout(
            height=800,
            showlegend=True,
            template='plotly_white',
            hovermode='closest'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("粘结相成分空间")
        
        # 提取元素含量
        element_data = {}
        for el in selected_elements:
            element_data[el] = top_df['Binder_Composition'].apply(lambda x: x.get(el, 0))
        
        comp_df = pd.DataFrame(element_data)
        comp_df['Predicted'] = top_df[f'Predicted_{screener.target_name}'].values
        
        # 相关性热图
        fig, ax = plt.subplots(figsize=(10, 8))
        
        corr_matrix = comp_df.corr()
        sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', 
                    center=0, ax=ax, cbar_kws={'label': 'Correlation'})
        ax.set_title('Element Fraction Correlation Matrix (Top Candidates)')
        
        st.pyplot(fig)
        
        # 元素平均含量
        st.markdown("#### 平均元素含量（Top配方）")
        
        avg_composition = comp_df[selected_elements].mean()
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(avg_composition.index, avg_composition.values, color='steelblue', alpha=0.7, edgecolor='black')
        ax.set_ylabel('Average Fraction')
        ax.set_xlabel('Element')
        ax.set_title(f'Average Binder Composition (Top {n_top})')
        ax.grid(True, alpha=0.3, axis='y')
        
        # 添加数值标签
        for i, v in enumerate(avg_composition.values):
            ax.text(i, v + 0.01, f'{v:.3f}', ha='center', va='bottom')
        
        st.pyplot(fig)
    
    # 导出功能
    st.header("💾 Step 5: 导出结果")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 导出Top N
        csv_top = top_df[display_cols].to_csv(index=False)
        st.download_button(
            label=f"📥 下载 Top {n_top} 配方 (CSV)",
            data=csv_top,
            file_name=f"virtual_screening_top{n_top}_{screener.target_name}.csv",
            mime="text/csv"
        )
    
    with col2:
        # 导出全部候选（可选）
        if st.checkbox("包含全部候选配方"):
            csv_all = all_df.to_csv(index=False)
            st.download_button(
                label=f"📥 下载全部 {len(all_df)} 个候选 (CSV)",
                data=csv_all,
                file_name=f"virtual_screening_all_{screener.target_name}.csv",
                mime="text/csv"
            )

# 侧边栏统计信息
if 'top_candidates' in st.session_state:
    with st.sidebar:
        st.divider()
        st.header("📊 筛选结果摘要")
        
        top_df = st.session_state.top_candidates
        all_df = st.session_state.all_candidates
        screener = st.session_state.screener
        
        st.metric("总候选数", f"{len(all_df):,}")
        st.metric("Top配方数", len(top_df))
        st.metric(f"最高 {screener.target_name}", 
                  f"{top_df[f'Predicted_{screener.target_name}'].max():.2f}")
        
        improvement = (
            (top_df[f'Predicted_{screener.target_name}'].min() - 
             all_df[f'Predicted_{screener.target_name}'].mean()) / 
            all_df[f'Predicted_{screener.target_name}'].mean() * 100
        )
        st.metric("相对平均值提升", f"{improvement:.1f}%")

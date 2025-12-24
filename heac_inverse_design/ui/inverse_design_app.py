"""
HEA Cermet 逆向设计系统 - Streamlit应用

专注于从目标性能反推最优成分和工艺参数。
"""

import streamlit as st
import sys
import os

# 添加路径 - 使用最简单的方式
project_root = r'd:\ML\HEAC 0.2'
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 调试：打印路径
print(f"Python path: {sys.path[:3]}")
print(f"Current dir: {os.getcwd()}")

# 直接导入
try:
    from heac_inverse_design.core.models import ModelX, ModelY, ProxyModelEnsemble
    from heac_inverse_design.core.features import FeatureExtractor
    from heac_inverse_design.core.optimization import InverseDesigner
    from heac_inverse_design.ui.visualizations import (
        plot_composition_radar,
        plot_pareto_front_interactive,
        plot_process_parameters,
        export_solutions_to_csv
    )
    print("✓ All imports successful")
except Exception as e:
    print(f"Import error: {e}")
    st.error(f"模块导入失败: {e}")
    st.stop()

import plotly.graph_objects as go
import pandas as pd


st.set_page_config(
    page_title="HEA Cermet Inverse Design",
    page_icon="🎯",
    layout="wide"
)


@st.cache_resource
def load_models():
    """加载所有模型"""
    try:
        # 模型文件位于 d:\ML\HEAC 0.2\models
        # project_root 已定义为 d:\ML\HEAC 0.2
        models_dir = os.path.join(project_root, 'models')
        
        # 打印调试信息
        print(f"Loading models from: {models_dir}")
        
        modelx = ModelX(os.path.join(models_dir, 'ModelX.pkl'))
        modely = ModelY(os.path.join(models_dir, 'ModelY.pkl'))
        proxy = ProxyModelEnsemble(os.path.join(models_dir, 'proxy_models'))
        extractor = FeatureExtractor()
        designer = InverseDesigner(modelx, modely, proxy, extractor)
        return designer, True, "模型加载成功"
    except Exception as e:
        return None, False, f"模型加载失败: {str(e)}"


# Pareto图函数已移至visualizations模块


def main():
    st.title("🎯 HEA Cermet 逆向设计系统")
    st.markdown("**基于ModelX、ModelY和Proxy模型的智能材料设计**")
    
    # 添加tab
    tab1, tab2 = st.tabs(["🎯 单个设计", "📋 批量设计"])
    
    with tab1:
        single_design_ui()
    
    with tab2:
        batch_design_ui()


def single_design_ui():
    """单个设计UI（原有功能）"""
    
    # 加载模型
    designer, success, message = load_models()
    
    if not success:
        st.error(message)
        st.stop()
    
    st.success("✅ " + message)
    
    # 侧边栏：设计目标和约束
    with st.sidebar:
        st.header("🎯 设计目标")
        
        # HV目标
        st.subheader("硬度 (HV)")
        col1, col2 = st.columns(2)
        hv_min = col1.number_input("最小值", 1000, 3000, 1500, key="hv_min")
        hv_max = col2.number_input("最大值", 1000, 3000, 2000, key="hv_max")
        
        # KIC目标
        st.subheader("断裂韧性 (KIC)")
        col1, col2 = st.columns(2)
        kic_min = col1.number_input("最小值", 5.0, 20.0, 8.0, key="kic_min")
        kic_max = col2.number_input("最大值", 5.0, 20.0, 15.0, key="kic_max")
        
        st.header("⚙️ 约束条件")
        
        # 元素选择
        elements = st.multiselect(
            "允许元素",
            ['Co', 'Ni', 'Fe', 'Cr', 'Mo', 'Nb', 'W', 'Ti', 'Al'],
            default=['Co', 'Ni', 'Fe', 'Cr']
        )
        
        if len(elements) < 2:
            st.warning("至少选择2个元素")
        
        # 陶瓷相
        ceramic_type = st.selectbox("陶瓷类型", ['WC', 'TiC', 'TiN', 'VC'])
        ceramic_range = st.slider(
            "陶瓷体积分数",
            0.4, 0.9, (0.5, 0.7),
            step=0.05
        )
        
        # 其他参数
        grain_range = st.slider(
            "晶粒尺寸 (μm)",
            0.5, 10.0, (0.5, 5.0),
            step=0.1
        )
        
        temp_range = st.slider(
            "烧结温度 (°C)",
            1200, 1700, (1350, 1550),
            step=10
        )
        
        # 优化参数
        st.header("🔧 优化设置")
        n_trials = st.number_input(
            "优化迭代次数",
            50, 500, 100,
            step=50,
            help="更多迭代=更好的解，但时间更长"
        )
        
        run_button = st.button(
            "🚀 开始逆向设计",
            type="primary",
            use_container_width=True
        )
    
    # 主区域
    if run_button:
        if len(elements) < 2:
            st.error("请至少选择2个元素")
            return
        
        # 运行优化
        with st.spinner("🔄 正在优化中，请稍候..."):
            try:
                solutions = designer.design(
                    target_hv_range=(hv_min, hv_max),
                    target_kic_range=(kic_min, kic_max),
                    allowed_elements=elements,
                    ceramic_type=ceramic_type,
                    ceramic_vol_range=ceramic_range,
                    grain_size_range=grain_range,
                    sinter_temp_range=temp_range,
                    n_trials=n_trials
                )
            except Exception as e:
                st.error(f"优化失败: {str(e)}")
                return
        
        if not solutions:
            st.warning("未找到满足条件的解，请放宽约束或增加迭代次数")
            return
        
        st.success(f"✅ 优化完成！找到 {len(solutions)} 个Pareto最优解")
        
        # 展示结果
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📊 Pareto前沿")
            fig = plot_pareto_front_interactive(solutions)
            st.plotly_chart(fig, use_container_width=True)
            
            # 导出按钮
            csv_data = export_solutions_to_csv(solutions)
            st.download_button(
                label="📥 导出所有方案 (CSV)",
                data=csv_data,
                file_name="hea_cermet_designs.csv",
                mime="text/csv",
                help="下载所有Pareto最优解到CSV文件"
            )
        
        with col2:
            st.subheader("📈 统计信息")
            hvs = [s.predicted_hv for s in solutions]
            kics = [s.predicted_kic for s in solutions]
            
            st.metric("HV范围", f"{min(hvs):.0f} - {max(hvs):.0f}")
            st.metric("KIC范围", f"{min(kics):.2f} - {max(kics):.2f}")
            st.metric("解的数量", len(solutions))
        
        # 推荐方案
        st.subheader("💡 推荐设计方案")
        
        # 选择前5个解（按HV和KIC的综合得分排序）
        solutions_sorted = sorted(
            solutions,
            key=lambda s: s.predicted_hv * 0.5 + s.predicted_kic * 100,
            reverse=True
        )[:5]
        
        for i, sol in enumerate(solutions_sorted, 1):
            with st.expander(
                f"方案 {i}: HV={sol.predicted_hv:.0f}, KIC={sol.predicted_kic:.2f}",
                expanded=(i == 1)
            ):
                col1, col2 = st.columns(2)
                
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    st.markdown("**成分 (原子分数)**")
                    comp_df = pd.DataFrame([
                        {'元素': el, '分数': f"{frac:.3f}"}
                        for el, frac in sol.composition.items()
                        if frac > 0.001
                    ])
                    st.dataframe(comp_df, hide_index=True)
                
                with col2:
                    st.markdown("**成分雷达图**")
                    radar_fig = plot_composition_radar(sol.composition, f"方案 {i}")
                    if radar_fig:
                        st.plotly_chart(radar_fig, use_container_width=True)
                
                with col3:
                    st.markdown("**工艺参数**")
                    proc_fig = plot_process_parameters(sol)
                    st.plotly_chart(proc_fig, use_container_width=True)
                
                st.markdown("**预测性能**")
                perf_col1, perf_col2 = st.columns(2)
                perf_col1.metric("硬度 (HV)", f"{sol.predicted_hv:.0f}")
                perf_col2.metric("断裂韧性 (KIC)", f"{sol.predicted_kic:.2f} MPa·m½")
    
    else:
        # 显示使用说明
        st.info("""
        ### 📖 使用说明
        
        1. **设置目标**: 在左侧面板设置期望的HV和KIC范围
        2. **选择约束**: 选择允许的元素、陶瓷类型和工艺参数范围
        3. **开始优化**: 点击"开始逆向设计"按钮
        4. **查看结果**: 系统自动找到Pareto最优解并推荐最佳方案
        
        ---
        
        ### ⚡ 特点
        
        - 🎯 **多目标优化**: 同时优化HV和KIC
        - 📊 **Pareto前沿**: 展示所有非支配解
        - 💡 **智能推荐**: 自动排序并推荐最佳方案
        - ⚙️ **灵活约束**: 支持元素、工艺等多种约束
        
        ---
        
        ### 🔬 技术栈
        
        - **ModelX**: HV预测 (R²=0.91)
        - **ModelY**: KIC预测 (R²=0.76)
        - **Proxy Models**: 形成能、晶格、磁矩
        - **优化算法**: NSGA-II (Optuna)
        """)


def batch_design_ui():
    """批量设计UI"""
    st.info("📋 批量设计功能正在开发中...")
    st.markdown("""
    **即将支持的功能**:
    - CSV文件上传
    - 表格输入多组目标
    - 批量运行优化
    - 汇总结果对比
    """)


if __name__ == "__main__":
    main()

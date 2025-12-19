# -*- coding: utf-8 -*-
"""
辅助模型展示与应用页面 - 完整版（包含虚拟筛选）

展示已训练的辅助模型，提供单成分预测、批量特征注入和虚拟筛选功能

Author: HEAC Team  
Updated: 2025-12-18 - 添加虚拟筛选功能
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import custom modules
try:
    from core.feature_injector import FeatureInjector
    from core.data_standardizer import standardize_dataframe, CompositionParser
    MODULES_AVAILABLE = True
except ImportError as e:
    MODULES_AVAILABLE = False
    import_error = str(e)

# Page config
st.set_page_config(
    page_title="辅助模型 - HEAC",
    page_icon="🔬",
    layout="wide"
)

# Title and description
st.title("🔬 辅助模型 (Proxy Models)")
st.markdown("""
基于84,000条DFT理论数据训练的辅助模型，为HEA粘结相预测深层物理属性。
""")

# Check module availability
if not MODULES_AVAILABLE:
    st.error(f"模块导入失败: {import_error}")
    st.stop()

# Load models
@st.cache_resource
def load_models_and_metrics():
    """加载所有模型和性能指标"""
    model_dir = Path('models/proxy_models')
    
    if not model_dir.exists():
        return None, "模型目录不存在"
    
    try:
        models = {}
        metrics = {}
        
        # Load models
        model_files = {
            'formation_energy': 'formation_energy_model.pkl',
            'lattice': 'lattice_model.pkl',
            'magnetic_moment': 'magnetic_moment_model.pkl'
        }
        
        for name, filename in model_files.items():
            model_path = model_dir / filename
            if model_path.exists():
                models[name] = joblib.load(model_path)
        
        # Load metrics
        metric_files = {
            'formation_energy': 'formation_energy_metrics.pkl',
            'lattice': 'lattice_metrics.pkl',
            'magnetic_moment': 'magnetic_moment_metrics.pkl'
        }
        
        for name, filename in metric_files.items():
            metric_path = model_dir / filename
            if metric_path.exists():
                metrics[name] = joblib.load(metric_path)
        
        # Load feature names
        feature_path = model_dir / 'feature_names.pkl'
        if feature_path.exists():
            models['features'] = joblib.load(feature_path)
        
        return {'models': models, 'metrics': metrics}, None
        
    except Exception as e:
        return None, f"加载失败: {str(e)}"

# Load models
data, error = load_models_and_metrics()

if error:
    st.error(error)
    st.info("请先训练模型：`python scripts/train_model_a_formation.py`")
    st.stop()

models = data['models']
metrics = data['metrics']

# Sidebar navigation
page = st.sidebar.radio(
    "选择功能",
    ["📊 模型概览", "🧪 单成分预测", "📁 批量特征注入", "🔬 虚拟筛选", "📈 性能可视化"]
)

# ==========================================
# Page 1: Model Overview
# ==========================================
if page == "📊 模型概览":
    st.header("模型性能概览")
    
    # Performance metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'formation_energy' in metrics:
            m = metrics['formation_energy']
            st.metric(
                label="模型A: 形成能",
                value=f"R² = {m.get('r2', 0):.4f}",
                delta="⭐ 超出预期",
                help=f"MAE: {m.get('mae', 0):.4f} eV/atom"
            )
        else:
            st.metric(label="模型A: 形成能", value="未训练")
    
    with col2:
        if 'lattice' in metrics:
            m = metrics['lattice']
            st.metric(
                label="模型B: 晶格常数",
                value=f"R² = {m.get('r2', 0):.4f}",
                delta="✅ 修复成功",
                help=f"MAE: {m.get('mae', 0):.4f} Å³"
            )
        else:
            st.metric(label="模型B: 晶格常数", value="未训练")
    
    with col3:
        if 'magnetic_moment' in metrics:
            m = metrics['magnetic_moment']
            st.metric(
                label="模型C: 磁矩",
                value=f"R² = {m.get('r2', 0):.4f}",
                delta="✅ 完成",
                help=f"MAE: {m.get('mae', 0):.4f} μB"
            )
        else:
            st.metric(label="模型C: 磁矩", value="未训练")
    
    # Detailed metrics table
    st.subheader("详细性能指标")
    
    metrics_data = []
    for name, m in metrics.items():
        if isinstance(m, dict) and 'r2' in m:
            metrics_data.append({
                '模型': name.replace('_', ' ').title(),
                '目标': m.get('target_name', 'N/A'),
                'R²': f"{m.get('r2', 0):.4f}",
                'MAE': f"{m.get('mae', 0):.4f}",
                'RMSE': f"{m.get('rmse', 0):.4f}" if 'rmse' in m else 'N/A',
                '样本数': m.get('n_samples', m.get('valid_samples', 'N/A'))
            })
    
    if metrics_data:
        df_metrics = pd.DataFrame(metrics_data)
        st.dataframe(df_metrics, use_container_width=True)
    
    # Model information
    st.subheader("模型信息")
    
    st.info("""
    **训练数据**: Zenodo HEA数据集 (84,024样本)  
    **特征工程**: Matminer特征化 (250维)  
    **算法**: XGBoost Regressor with 5-fold Cross-Validation  
    **物理意义**: 基于DFT计算的理论预测，用于增强实验数据
    """)
    
    # ROM models
    st.subheader("ROM趋势因子模型")
    st.markdown("""
    **模型D/E**: 基于混合规则(Rule of Mixtures)的趋势预测
    - 使用PyMatGen元素数据库
    - 提供弹性模量和Pugh比趋势
    - 用于相对比较，非绝对值预测
    """)

# ==========================================
# Page 2: Single Composition Prediction
# ==========================================
elif page == "🧪 单成分预测":
    st.header("单成分物理属性预测")
    
    st.markdown("""
    输入HEA成分，实时预测4个深层物理属性。支持多种成分格式。
    """)
    
    # Input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        comp_input = st.text_input(
            "成分输入",
            value="AlCoCrFeNi",
            help="支持格式: AlCoCrFeNi, Al0.2Co0.2Cr0.2Fe0.2Ni0.2, Al10Co20Cr20Fe20Ni30"
        )
    
    with col2:
        predict_btn = st.button("🔮 预测", type="primary", use_container_width=True)
    
    # Example compositions
    st.markdown("**示例成分**: ")
    examples = ["AlCoCrFeNi", "CoCrNi", "TiZrNbTa", "Co80Ni20"]
    cols = st.columns(len(examples))
    for i, ex in enumerate(examples):
        if cols[i].button(ex, key=f"ex_{i}"):
            comp_input = ex
            predict_btn = True
    
    if predict_btn and comp_input:
        with st.spinner("计算中..."):
            try:
                # Initialize injector
                injector = FeatureInjector(model_dir='models/proxy_models')
                
                # Parse composition
                composition = injector.composition_parser.parse(comp_input)
                
                if composition is None:
                    st.error("成分解析失败！请检查格式")
                else:
                    # Display parsed composition
                    st.success(f"✅ 成分解析成功")
                    comp_str = ', '.join([f"{elem}: {frac:.3f}" for elem, frac in composition.items()])
                    st.code(comp_str, language=None)
                    
                    # Predict properties
                    st.subheader("预测结果")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    # Formation energy
                    try:
                        ef = injector.predict_formation_energy(composition)
                        if ef is not None:
                            col1.metric("形成能", f"{ef:.4f} eV/atom")
                            if ef < -0.1:
                                col1.success("稳定性: 优秀")
                            elif ef < 0:
                                col1.info("稳定性: 良好")
                            else:
                                col1.warning("稳定性: 较弱")
                    except Exception as e:
                        col1.error(f"预测失败: {e}")
                    
                    # Lattice parameter
                    try:
                        lattice = injector.predict_lattice_parameter(composition)
                        if lattice is not None:
                            # Convert volume to lattice (FCC assumption)
                            a_fcc = (4 * lattice) ** (1/3)
                            col2.metric("晶格常数 (FCC)", f"{a_fcc:.3f} Å")
                            
                            # Lattice mismatch
                            mismatch = injector.calculate_lattice_mismatch(lattice)
                            col2.metric("晶格失配 vs WC", f"{mismatch:.2f} %")
                    except Exception as e:
                        col2.error(f"预测失败: {e}")
                    
                    # Magnetic moment
                    try:
                        magmom = injector.predict_magnetic_moment(composition)
                        if magmom is not None:
                            col3.metric("磁矩", f"{magmom:.2f} μB")
                            if magmom < 0.5:
                                col3.info("非磁性/低磁")
                            elif magmom < 2:
                                col3.info("中等磁性")
                            else:
                                col3.warning("高磁性")
                    except Exception as e:
                        col3.error(f"预测失败: {e}")
                    
                    # ROM predictions (if available)
                    st.subheader("弹性性能趋势 (ROM方法)")
                    st.info("基于混合规则的趋势预测，用于相对比较")
                    
                    try:
                        elastic = injector.predict_elastic_moduli(composition)
                        
                        col1, col2, col3 = st.columns(3)
                        
                        if elastic.get('bulk'):
                            col1.metric("体模量 (趋势)", f"{elastic['bulk']:.0f} GPa")
                        
                        if elastic.get('shear'):
                            col2.metric("剪切模量 (趋势)", f"{elastic['shear']:.0f} GPa")
                        
                        if elastic.get('bulk') and elastic.get('shear'):
                            pugh = elastic['bulk'] / elastic['shear']
                            nature = "韧性 (Ductile)" if pugh > 1.75 else "脆性 (Brittle)"
                            col3.metric("Pugh比", f"{pugh:.2f}", delta=nature)
                            
                    except Exception as e:
                        st.warning(f"ROM预测不可用: {e}")
                    
            except Exception as e:
                st.error(f"预测过程出错: {str(e)}")
                st.exception(e)

# ==========================================
# Page 3: Batch Feature Injection
# ==========================================
elif page == "📁 批量特征注入":
    st.header("批量特征注入")
    
    st.markdown("""
    上传包含HEA成分的CSV文件，自动添加4个基于DFT数据的辅助物理特征。
    
    **注入特征**：
    - 形成能 (Formation Energy)
    - 晶格常数 (Lattice Parameter)  
    - 晶格失配 vs WC (Lattice Mismatch)
    - 磁矩 (Magnetic Moment)
    """)
    
    # File upload
    uploaded_file = st.file_uploader(
        "上传CSV文件",
        type=['csv'],
        help="文件应包含HEA成分列"
    )
    
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            
            st.success(f"✅ 文件加载成功: {df.shape[0]} 行 × {df.shape[1]} 列")
            
            # Select composition column
            comp_col = st.selectbox(
                "选择成分列",
                df.columns,
                help="包含HEA成分的列（如: binder_composition）"
            )
            
            # Preview
            st.subheader("数据预览")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Inject features button
            if st.button("💉 注入特征", type="primary"):
                with st.spinner("处理中...这可能需要几分钟"):
                    try:
                        # Standardize
                        df_std = standardize_dataframe(df, merge_duplicates=True)
                        
                        # 标准化列名：将用户选择的列名转换为标准化后的列名
                        from core.data_standardizer import data_standardizer
                        data_standardizer._build_reverse_mapping()
                        comp_col_lower = comp_col.lower().strip().replace(' ', '_')
                        std_comp_col = data_standardizer._REVERSE_MAPPING.get(comp_col_lower, comp_col)
                        
                        # 检查标准化后的列是否存在
                        if std_comp_col not in df_std.columns:
                            st.error(f"缺少数据: 标准化后的成分列 '{std_comp_col}' 不存在于DataFrame中")
                            st.info(f"可用的列: {', '.join(df_std.columns.tolist())}")
                            st.stop()
                        
                        # Inject
                        injector = FeatureInjector(model_dir='models/proxy_models')
                        df_enhanced = injector.inject_features(
                            df_std,
                            comp_col=std_comp_col,
                            verbose=False
                        )
                        
                        st.success("✅ 特征注入完成！")
                        
                        # Show new features
                        new_cols = [col for col in df_enhanced.columns 
                                   if col.startswith('pred_') or col == 'lattice_mismatch_wc']
                        
                        st.info(f"新增 {len(new_cols)} 个特征: {', '.join(new_cols)}")
                        
                        # Preview enhanced data
                        st.subheader("增强数据预览")
                        display_cols = [std_comp_col] + new_cols
                        if all(col in df_enhanced.columns for col in display_cols):
                            st.dataframe(df_enhanced[display_cols].head(10), use_container_width=True)
                        
                        # Statistics
                        st.subheader("特征统计")
                        st.dataframe(df_enhanced[new_cols].describe(), use_container_width=True)
                        
                        # Download button
                        csv = df_enhanced.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 下载增强数据",
                            data=csv,
                            file_name="hea_enhanced_with_proxy.csv",
                            mime="text/csv",
                            type="primary"
                        )
                        
                    except Exception as e:
                        st.error(f"处理失败: {str(e)}")
                        st.exception(e)
                        
        except Exception as e:
            st.error(f"文件读取失败: {str(e)}")

# ==========================================
# Page 4: Virtual Screening
# ==========================================
elif page == "🔬 虚拟筛选":
    st.header("虚拟高通量筛选")
    
    st.markdown("""
    🔬 基于物理约束的多级筛选漏斗，从大量虚拟配方中筛选最优候选
    
    **三级筛选策略**：
    - 🔴 **Level 1**: 稳定性过滤（淘汰~80%）
    - 🟡 **Level 2**: 界面匹配（优选韧性）
    - 🟢 **Level 3**: 综合评分（多目标优化）
    """)
    
    # Parameters
    with st.expander("⚙️ 筛选参数配置", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            n_generate = st.slider(
                "虚拟配方数量",
                min_value=1000,
                max_value=100000,
                value=10000,
                step=1000,
                help="生成的虚拟配方总数（建议先用小数量测试）"
            )
            
            ef_threshold = st.slider(
                "形成能阈值 (eV/atom)",
                min_value=-0.5,
                max_value=0.2,
                value=-0.05,
                step=0.01,
                help="< 此值认为稳定"
            )
        
        with col2:
            mismatch_threshold = st.slider(
                "晶格失配阈值",
                min_value=0.0,
                max_value=0.2,
                value=0.05,
                step=0.01,
                help="界面匹配的可接受范围"
            )
            
            top_n = st.slider(
                "返回Top N",
                min_value=5,
                max_value=100,
                value=20,
                step=5
            )
    
    # Start button
    if st.button("🚀 开始虚拟筛选", type="primary", use_container_width=True):
        
        progress = st.progress(0, text="初始化...")
        
        try:
            # Import functions
            from scripts.virtual_screening import generate_virtual_recipes
            from scripts.inject_physics import filter_by_stability, filter_by_interface
            
            # Step 1: Generate
            progress.progress(10, text=f"[1/5] 生成 {n_generate:,} 个虚拟配方...")
            df_virtual = generate_virtual_recipes(n_samples=n_generate)
            st.success(f"✓ 生成完成: {len(df_virtual):,} 个配方")
            
            # Step 2: Inject
            progress.progress(30, text="[2/5] 调用辅助模型预测...")
            injector = FeatureInjector(model_dir='models/proxy_models')
            df_enhanced = injector.inject_features(
                df_virtual,
                comp_col='binder_composition',
                verbose=False
            )
            st.success("✓ 特征注入完成")
            
            # Step 3: Filter 1
            progress.progress(50, text="[3/5] 稳定性过滤...")
            df_stable = filter_by_stability(df_enhanced, ef_threshold=ef_threshold)
            
            if len(df_stable) == 0:
                st.error("所有配方都被淘汰！请放宽阈值")
                st.stop()
            
            st.info(f"稳定性: {len(df_virtual):,} → {len(df_stable):,} ({len(df_stable)/len(df_virtual)*100:.1f}%)")
            
            # Step 4: Filter 2
            progress.progress(70, text="[4/5] 界面匹配过滤...")
            df_matched = filter_by_interface(df_stable, mismatch_threshold=mismatch_threshold)
            
            if len(df_matched) == 0:
                st.warning("界面过滤淘汰所有配方，返回稳定性合格配方")
                df_matched = df_stable
            
            st.info(f"界面: {len(df_stable):,} → {len(df_matched):,} ({len(df_matched)/len(df_stable)*100:.1f}%)")
            
            # Step 5: Rank
            progress.progress(90, text="[5/5] 综合评分...")
            
            # Scoring
            df_matched['score'] = 0
            if 'pred_formation_energy' in df_matched.columns:
                df_matched['score'] += -df_matched['pred_formation_energy'] * 10
            if 'lattice_mismatch_wc' in df_matched.columns:
                df_matched['score'] += (1 - df_matched['lattice_mismatch_wc'].abs()) * 10
            if 'pred_pugh_ratio' in df_matched.columns:
                df_matched['score'] += (df_matched['pred_pugh_ratio'] - 1.75).clip(0, 1) * 5
            
            df_top = df_matched.sort_values('score', ascending=False).head(top_n)
            
            progress.progress(100, text="✅ 完成！")
            
            # Results
            st.success(f"🎯 筛选完成！从 {n_generate:,} → Top {top_n}")
            
            # Display
            st.subheader(f"🏆 Top {top_n} 候选配方")
            
            disp_cols = ['recipe_id', 'binder_composition', 
                        'pred_formation_energy', 'lattice_mismatch_wc', 'score']
            avail_cols = [c for c in disp_cols if c in df_top.columns]
            
            st.dataframe(df_top[avail_cols], use_container_width=True, height=400)
            
            # Download
            csv = df_top.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 下载候选配方",
                data=csv,
                file_name="virtual_screening_candidates.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"筛选失败: {str(e)}")
            st.exception(e)

# ==========================================
# Page 5: Performance Visualization
# ==========================================
elif page == "📈 性能可视化":
    st.header("模型性能可视化")
    
    st.info("此功能正在开发中")
    st.markdown("""
    计划功能：
    - Parity Plot
    - 误差分布
    - SHAP分析
    """)
    
    if metrics:
        chart_data = pd.DataFrame([
            {'模型': k.replace('_', ' ').title(), 'R²': v.get('r2', 0)}
            for k, v in metrics.items()
            if isinstance(v, dict) and 'r2' in v
        ])
        
        if not chart_data.empty:
            st.bar_chart(chart_data.set_index('模型'))

# Footer
st.markdown("---")
st.caption("🔬 HEAC项目 | 辅助模型系统 v1.0")

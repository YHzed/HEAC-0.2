import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.stats import spearmanr
from sklearn.feature_selection import RFECV
from sklearn.model_selection import cross_val_score
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="GBFS Feature Selection", page_icon="🎯", layout="wide")

st.title("🎯 GBFS Feature Selection Workflow")
st.markdown("""
**三层特征筛选策略**：
1. 分层聚类（Spearman相关性）
2. 目标导向簇内优选
3. RFECV自动优化
""")

# ====================
# 1. 数据加载
# ====================
st.header("📁 Step 1: Load Processed Data")

file_path = st.text_input("CSV文件路径", value=r"d:\ML\HEAC 0.2\datasets\hea_processed.csv")

if st.button("Load Data") or 'df_original' in st.session_state:
    try:
        if 'df_original' not in st.session_state:
            df = pd.read_csv(file_path)
            st.session_state.df_original = df
        else:
            df = st.session_state.df_original
        
        st.success(f"✓ 加载了 {df.shape[0]} 行 × {df.shape[1]} 列数据")
        st.dataframe(df.head())
        
        # 识别目标变量
        target_candidates = ['HV, kgf/mm2', 'TRS, MPa', 'KIC, MPa·m1/2']
        available_targets = [t for t in target_candidates if t in df.columns]
        st.info(f"可用目标变量: {', '.join(available_targets)}")
        
    except Exception as e:
        st.error(f"加载失败: {e}")

# ====================
# 2. 生成复合特征
# ====================
st.header("🧬 Step 2: Generate Composite Features")

st.markdown("""
**复合特征类型**：
- **加权平均**：整体材料性质 = Σ(各相性质 × 体积分数)
- **差异特征**：界面应力、失配 = |Ceramic - Binder|
- **比值特征**：相对关系 = Ceramic / Binder
- **界面特征**：界面复杂度、平均自由程
""")

def generate_composite_features(df):
    """生成硬质相-粘结相复合交互特征"""
    
    df_composite = df.copy()
    new_features = []
    
    # 1. 体积分数加权平均特征
    st.write("⏳ 生成加权平均特征...")
    
    # 识别MagpieData特征
    magpie_features = []
    for col in df.columns:
        if 'Ceramic_MagpieData mean' in col:
            feature_name = col.replace('Ceramic_MagpieData mean ', '')
            binder_col = f'Binder_MagpieData mean {feature_name}'
            
            if binder_col in df.columns:
                magpie_features.append(feature_name)
    
    for feat in magpie_features:
        ceramic_col = f'Ceramic_MagpieData mean {feat}'
        binder_col = f'Binder_MagpieData mean {feat}'
        composite_col = f'Composite_MagpieData mean {feat}'
        
        if 'Ceramic_Vol_Frac' in df.columns and 'Binder_Vol_Frac' in df.columns:
            df_composite[composite_col] = (
                df[ceramic_col] * df['Ceramic_Vol_Frac'] +
                df[binder_col] * df['Binder_Vol_Frac']
            )
            new_features.append(composite_col)
    
    st.success(f"✓ 生成了 {len(magpie_features)} 个加权平均特征")
    
    # 2. 差异特征
    st.write("⏳ 生成差异特征...")
    
    key_diff_features = ['Electronegativity', 'AtomicRadius', 'MeltingT', 'ModulusBulk',
                         'Number', 'AtomicWeight', 'Density', 'FusionHeat']
    
    diff_count = 0
    for feat in key_diff_features:
        ceramic_col = f'Ceramic_MagpieData mean {feat}'
        binder_col = f'Binder_MagpieData mean {feat}'
        
        if ceramic_col in df.columns and binder_col in df.columns:
            diff_col = f'Diff_{feat}'
            df_composite[diff_col] = abs(df[ceramic_col] - df[binder_col])
            new_features.append(diff_col)
            diff_count += 1
    
    st.success(f"✓ 生成了 {diff_count} 个差异特征")
    
    # 3. 比值特征
    st.write("⏳ 生成比值特征...")
    
    key_ratio_features = ['ModulusBulk', 'Density', 'MeltingT', 'AtomicWeight']
    
    ratio_count = 0
    for feat in key_ratio_features:
        ceramic_col = f'Ceramic_MagpieData mean {feat}'
        binder_col = f'Binder_MagpieData mean {feat}'
        
        if ceramic_col in df.columns and binder_col in df.columns:
            ratio_col = f'Ratio_{feat}'
            df_composite[ratio_col] = df[ceramic_col] / (df[binder_col] + 1e-6)
            new_features.append(ratio_col)
            ratio_count += 1
    
    st.success(f"✓ 生成了 {ratio_count} 个比值特征")
    
    # 4. 界面相关特征
    st.write("⏳ 生成界面特征...")
    
    if 'Ceramic_Vol_Frac' in df.columns:
        # 界面复杂度（最大值在50%时）
        df_composite['Interface_Complexity'] = (
            df['Ceramic_Vol_Frac'] * (1 - df['Ceramic_Vol_Frac']) * 4
        )
        new_features.append('Interface_Complexity')
    
    if 'Grain_Size_um' in df.columns and 'Binder_Vol_Frac' in df.columns:
        # 平均自由程
        df_composite['Mean_Free_Path'] = (
            df['Grain_Size_um'] * df['Binder_Vol_Frac'] / 
            (1 - df['Binder_Vol_Frac'] + 1e-6)
        )
        new_features.append('Mean_Free_Path')
    
    st.success(f"✓ 生成了界面特征")
    
    return df_composite, new_features

if 'df_original' in st.session_state:
    if st.button("🚀 Generate Composite Features"):
        with st.spinner("生成复合特征中..."):
            df_with_composite, new_feats = generate_composite_features(st.session_state.df_original)
            st.session_state.df_composite = df_with_composite
            st.session_state.composite_features = new_feats
            
            st.success(f"✅ 总共生成了 {len(new_feats)} 个复合特征！")
            
            # 显示特征分类
            with st.expander("📊 查看生成的复合特征"):
                composite_feats = [f for f in new_feats if f.startswith('Composite_')]
                diff_feats = [f for f in new_feats if f.startswith('Diff_')]
                ratio_feats = [f for f in new_feats if f.startswith('Ratio_')]
                interface_feats = [f for f in new_feats if f.startswith('Interface_') or f.startswith('Mean_')]
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("加权平均", len(composite_feats))
                with col2:
                    st.metric("差异特征", len(diff_feats))
                with col3:
                    st.metric("比值特征", len(ratio_feats))
                with col4:
                    st.metric("界面特征", len(interface_feats))

# ====================
# 3. 数据预清洗
# ====================
st.header("🧹 Step 3: Data Pre-cleaning")

if 'df_composite' in st.session_state:
    df_work = st.session_state.df_composite.copy()
    
    # 选择目标变量
    target_candidates = ['HV, kgf/mm2', 'TRS, MPa', 'KIC, MPa·m1/2']
    available_targets = [t for t in target_candidates if t in df_work.columns]
    
    selected_target = st.selectbox(
        "🎯 选择目标变量（Target）用于特征优化",
        available_targets,
        help="不同的Target会导致不同的特征选择结果"
    )
    
    if st.button("执行预清洗"):
        with st.spinner("清洗数据中..."):
            # 1. 处理缺失的目标值
            df_clean = df_work.copy()
            df_clean = df_clean.replace('-', np.nan)
            
            before_count = len(df_clean)
            df_clean = df_clean.dropna(subset=[selected_target])
            after_count = len(df_clean)
            
            st.info(f"移除了 {before_count - after_count} 行缺失目标值的数据")
            
            # 2. 选择数值特征
            numeric_cols = df_clean.select_dtypes(include=['number']).columns
            
            # 移除目标变量
            feature_cols = [c for c in numeric_cols if c not in target_candidates]
            
            X = df_clean[feature_cols]
            y = df_clean[selected_target]
            
            # 3. 移除常量特征
            constant_cols = []
            for col in X.columns:
                if X[col].nunique() <= 1:
                    constant_cols.append(col)
            
            if constant_cols:
                st.warning(f"移除了 {len(constant_cols)} 个常量特征")
                X = X.drop(columns=constant_cols)
            
            # 4. 处理特征缺失值和类型转换
            # 强制转换所有列为数值类型，避免spearmanr等函数出错
            for col in X.columns:
                X[col] = pd.to_numeric(X[col], errors='coerce')
            
            X = X.fillna(X.median())
            
            # 确保y也是数值类型
            y = pd.to_numeric(y, errors='coerce')
            y = y.fillna(y.median())
            
            st.session_state.X_clean = X
            st.session_state.y_clean = y
            st.session_state.selected_target = selected_target
            
            st.success(f"✅ 清洗完成！最终特征矩阵: {X.shape[0]} 行 × {X.shape[1]} 列")
            
            # 显示统计信息
            col1, col2, col3 = st.columns(3)
            with col1:
                ceramic_feats = len([c for c in X.columns if c.startswith('Ceramic_')])
                st.metric("硬质相特征", ceramic_feats)
            with col2:
                binder_feats = len([c for c in X.columns if c.startswith('Binder_')])
                st.metric("粘结相特征", binder_feats)
            with col3:
                composite_feats = len([c for c in X.columns if c.startswith('Composite_') or 
                                      c.startswith('Diff_') or c.startswith('Ratio_') or
                                      c.startswith('Interface_') or c.startswith('Mean_')])
                st.metric("复合特征", composite_feats)

# ====================
# 4. GBFS分层聚类
# ====================
st.header("🌳 Step 4: GBFS Hierarchical Clustering")

if 'X_clean' in st.session_state:
    st.markdown("""
    **算法流程**：
    1. 计算Spearman相关性矩阵
    2. 转换为距离矩阵: D = 1 - |Correlation|
    3. Ward's Linkage分层聚类
    4. 目标导向簇内优选（选择与Target相关性最高的特征）
    """)
    
    threshold = st.slider(
        "聚类距离阈值（Cutoff）",
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.05,
        help="阈值越低，聚类越细，保留特征越多"
    )
    
    if st.button("🚀 执行GBFS聚类"):
        X = st.session_state.X_clean
        y = st.session_state.y_clean
        
        with st.spinner("执行分层聚类..."):
            # 1. 计算Spearman相关性矩阵
            st.write("⏳ 计算Spearman相关性...")
            corr_matrix = X.corr(method='spearman').abs()
            
            # 2. 转换为距离矩阵
            distance_matrix = 1 - corr_matrix
            
            # 3. 分层聚类
            st.write("⏳ 执行Ward's Linkage聚类...")
            from scipy.spatial.distance import squareform
            condensed_dist = squareform(distance_matrix)
            linkage_matrix = linkage(condensed_dist, method='ward')
            
            # 4. 绘制树状图
            st.write("⏳ 绘制Dendrogram...")
            fig, ax = plt.subplots(figsize=(20, 8))
            dendrogram(
                linkage_matrix,
                labels=X.columns,
                leaf_rotation=90,
                leaf_font_size=8,
                ax=ax
            )
            ax.axhline(y=threshold, color='r', linestyle='--', linewidth=2, 
                      label=f'Cutoff={threshold}')
            ax.set_title('Feature Dendrogram (GBFS)', fontsize=16)
            ax.set_xlabel('Features', fontsize=12)
            ax.set_ylabel('Distance', fontsize=12)
            ax.legend()
            plt.tight_layout()
            st.pyplot(fig)
            
            # 5. 提取聚类簇
            clusters = fcluster(linkage_matrix, threshold, criterion='distance')
            n_clusters = len(np.unique(clusters))
            
            st.success(f"✓ 识别出 {n_clusters} 个特征簇")
            
            # 6. 目标导向簇内优选
            st.write("⏳ 簇内优选（选择与Target相关性最高的特征）...")
            
            selected_features = []
            cluster_info = []
            
            for cluster_id in np.unique(clusters):
                cluster_features = X.columns[clusters == cluster_id].tolist()
                
                # 计算每个特征与目标的相关性
                correlations = {}
                for feat in cluster_features:
                    corr, _ = spearmanr(X[feat], y)
                    correlations[feat] = abs(corr)
                
                # 选择相关性最高的特征
                best_feature = max(correlations, key=correlations.get)
                selected_features.append(best_feature)
                
                cluster_info.append({
                    'Cluster': cluster_id,
                    'Size': len(cluster_features),
                    'Selected_Feature': best_feature,
                    'Correlation_with_Target': correlations[best_feature],
                    'All_Features': ', '.join(cluster_features[:3]) + ('...' if len(cluster_features) > 3 else '')
                })
            
            st.session_state.selected_features_gbfs = selected_features
            st.session_state.cluster_info = pd.DataFrame(cluster_info)
            
            st.success(f"✅ GBFS完成！从 {X.shape[1]} 个特征中选出 {len(selected_features)} 个代表特征")
            
            # 显示聚类信息
            with st.expander("📊 查看聚类详情"):
                st.dataframe(st.session_state.cluster_info)

# ====================
# 5. RFECV进一步优化
# ====================
st.header("🎯 Step 5: RFECV Optimization")

if 'selected_features_gbfs' in st.session_state:
    st.markdown("""
    使用 **XGBoost + 交叉验证** 自动确定最优特征数量。
    """)
    
    cv_folds = st.slider("交叉验证折数", min_value=3, max_value=10, value=5)
    
    if st.button("🚀 执行RFECV"):
        X = st.session_state.X_clean
        y = st.session_state.y_clean
        selected_feats = st.session_state.selected_features_gbfs
        
        X_selected = X[selected_feats]
        
        with st.spinner("执行RFECV（可能需要几分钟）..."):
            # RFECV
            estimator = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
            
            rfecv = RFECV(
                estimator=estimator,
                step=1,
                cv=cv_folds,
                scoring='r2',
                n_jobs=-1
            )
            
            rfecv.fit(X_selected, y)
            
            optimal_features = X_selected.columns[rfecv.support_].tolist()
            
            st.session_state.optimal_features = optimal_features
            st.session_state.rfecv = rfecv
            
            st.success(f"✅ RFECV完成！最优特征数: {len(optimal_features)}")
            
            # 绘制RFECV曲线
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(range(1, len(rfecv.cv_results_['mean_test_score']) + 1),
                   rfecv.cv_results_['mean_test_score'],
                   marker='o')
            ax.axvline(x=rfecv.n_features_, color='r', linestyle='--',
                      label=f'Optimal: {rfecv.n_features_} features')
            ax.set_xlabel('Number of Features')
            ax.set_ylabel('Cross-Validation R² Score')
            ax.set_title('RFECV Feature Selection')
            ax.legend()
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
            
            # 显示最优特征
            with st.expander("📋 最优特征列表"):
                st.write(optimal_features)

# ====================
# 6. 保存结果
# ====================
st.header("💾 Step 6: Save Results")

if 'optimal_features' in st.session_state:
    output_path = st.text_input(
        "输出文件路径",
        value=r"d:\ML\HEAC 0.2\datasets\hea_selected_features.csv"
    )
    
    if st.button("💾 保存精简数据集"):
        optimal_feats = st.session_state.optimal_features
        target = st.session_state.selected_target
        df_final = st.session_state.df_composite
        
        # 创建最终数据集
        final_cols = optimal_feats + [target]
        df_output = df_final[final_cols].dropna(subset=[target])
        
        df_output.to_csv(output_path, index=False)
        
        st.success(f"✅ 已保存到: {output_path}")
        st.write(f"**最终维度**: {df_output.shape[0]} 行 × {df_output.shape[1]} 列")
        st.dataframe(df_output.head())
        
        # 特征重要性（使用最终模型）
        if st.checkbox("查看特征重要性"):
            X_final = df_output[optimal_feats]
            y_final = df_output[target]
            
            model = xgb.XGBRegressor(n_estimators=100, max_depth=5, random_state=42)
            model.fit(X_final, y_final)
            
            importance_df = pd.DataFrame({
                'Feature': optimal_feats,
                'Importance': model.feature_importances_
            }).sort_values('Importance', ascending=False)
            
            fig, ax = plt.subplots(figsize=(10, max(6, len(optimal_feats) * 0.3)))
            ax.barh(importance_df['Feature'], importance_df['Importance'])
            ax.set_xlabel('Feature Importance')
            ax.set_title(f'Feature Importance for {target}')
            plt.tight_layout()
            st.pyplot(fig)
            
            st.dataframe(importance_df)

# 侧边栏信息
with st.sidebar:
    st.header("📊 Process Summary")
    
    if 'df_original' in st.session_state:
        st.metric("原始特征数", st.session_state.df_original.shape[1])
    
    if 'composite_features' in st.session_state:
        st.metric("复合特征数", len(st.session_state.composite_features))
    
    if 'X_clean' in st.session_state:
        st.metric("清洗后特征数", st.session_state.X_clean.shape[1])
    
    if 'selected_features_gbfs' in st.session_state:
        st.metric("GBFS筛选后", len(st.session_state.selected_features_gbfs))
    
    if 'optimal_features' in st.session_state:
        st.metric("RFECV最优数", len(st.session_state.optimal_features))
        
        reduction = (
            1 - len(st.session_state.optimal_features) / st.session_state.df_original.shape[1]
        ) * 100
        st.metric("特征削减率", f"{reduction:.1f}%")

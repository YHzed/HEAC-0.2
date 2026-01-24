import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
import warnings

warnings.filterwarnings('ignore')

# ========== 性能优化: 数据加载缓存 ==========
@st.cache_data
def load_training_data(file_path: str) -> pd.DataFrame:
    """缓存训练数据加载 - 避免重复读取CSV"""
    return pd.read_csv(file_path)

st.set_page_config(page_title="Model Training", page_icon="🎓", layout="wide")

import ui.style_manager as style_manager
style_manager.apply_theme()

style_manager.ui_header("🎓 HEA Model Training & Analysis")
st.markdown("""
**核心流程**：
1. 数据加载与分割
2. K-Fold交叉验证（评估真实泛化能力）
3. 超参数优化（Optuna）
4. 模型训练
5. **SHAP物理可解释性分析**（关键步骤）
6. 模型保存
""")

# ===================
# Step 1: 数据加载
# ===================
st.header("📁 Step 1: Load Selected Features")

file_path = st.text_input(
    "精简特征集路径",
    value=r"d:\ML\HEAC 0.2\datasets\hea_selected_features.csv"
)

if st.button("Load Data") or 'df_model' in st.session_state:
    try:
        if 'df_model' not in st.session_state:
            # 使用缓存加载数据
            df = load_training_data(file_path)
            st.session_state.df_model = df
        else:
            df = st.session_state.df_model
        
        st.success(f"✓ 加载了 {df.shape[0]} 行 × {df.shape[1]} 列")
        
        # 智能识别目标变量（支持多种格式）
        # 定义目标变量的关键词及其变体
        target_mappings = {
            'Hardness': ['HV, kgf/mm2', 'HV_kgf_mm2', 'HV', 'Hardness'],
            'Strength': ['TRS, MPa', 'TRS_MPa', 'TRS', 'Strength'],
            'Toughness': ['KIC, MPa·m1/2', 'KIC_MPa_m', 'KIC', 'Toughness']
        }
        
        available_targets = []
        target_info = []
        
        for category, variants in target_mappings.items():
            for variant in variants:
                if variant in df.columns:
                    # 检查缺失值比例
                    missing_pct = df[variant].isna().sum() / len(df) * 100
                    valid_count = df[variant].notna().sum()
                    
                    # 只保留缺失率<50%且有效值>10的目标变量
                    if missing_pct < 50 and valid_count >= 10:
                        available_targets.append(variant)
                        target_info.append(f"{variant} (有效值: {valid_count}, 缺失: {missing_pct:.1f}%)")
                        break  # 找到一个有效的就跳出
                    else:
                        st.warning(f"⚠️ 跳过 `{variant}`: 缺失率 {missing_pct:.1f}% 过高或有效值不足")
        
        if available_targets:
            st.session_state.available_targets = available_targets
            st.success(f"✓ 找到 {len(available_targets)} 个可用目标变量")
            with st.expander("📊 目标变量详情"):
                for info in target_info:
                    st.write(f"- {info}")
        else:
            st.error("⚠️ 无可用目标变量！请检查数据文件。")
            st.info("提示：系统会自动跳过缺失率>50%或有效值<10的目标变量。")
        
        with st.expander("📊 数据预览"):
            st.dataframe(df.head())
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总样本数", df.shape[0])
            with col2:
                st.metric("特征数", df.shape[1] - len(available_targets))
            with col3:
                st.metric("目标变量数", len(available_targets))
    
    except Exception as e:
        st.error(f"加载失败: {e}")

# ===================
# Step 2: 数据准备
# ===================
if 'df_model' in st.session_state:
    st.header("🔧 Step 2: Data Preparation")
    
    df = st.session_state.df_model
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_target = st.selectbox(
            "🎯 选择目标变量",
            st.session_state.available_targets,
            help="选择要预测的性能指标"
        )
    
    with col2:
        normalize = st.checkbox(
            "标准化特征（StandardScaler）",
            value=True,
            help="推荐开启，提高模型稳定性"
        )
    
    # 数据分割参数
    st.subheader("数据分割设置")
    col1, col2 = st.columns(2)
    
    with col1:
        test_size = st.slider(
            "测试集比例",
            min_value=0.1,
            max_value=0.3,
            value=0.2,
            step=0.05
        )
    
    with col2:
        random_state = st.number_input(
            "随机种子",
            value=42,
            help="保证结果可复现"
        )
    
    if st.button("准备数据"):
        with st.spinner("准备数据中..."):
            # 分离特征和目标
            feature_cols = [c for c in df.columns if c not in st.session_state.available_targets]
            
            X = df[feature_cols].copy()
            y = df[selected_target].copy()
            
            # 处理缺失值
            y = pd.to_numeric(y, errors='coerce')
            valid_idx = y.notna()
            
            X = X[valid_idx]
            y = y[valid_idx]
            
            st.info(f"移除了 {(~valid_idx).sum()} 行缺失目标值")
            
            # Train/Test分割
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=test_size,
                random_state=random_state
            )
            
            # 标准化
            if normalize:
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                
                # 转回DataFrame保留列名
                X_train = pd.DataFrame(X_train_scaled, columns=X_train.columns, index=X_train.index)
                X_test = pd.DataFrame(X_test_scaled, columns=X_test.columns, index=X_test.index)
                
                st.session_state.scaler = scaler
            else:
                st.session_state.scaler = None
            
            # 保存到session_state
            st.session_state.X_train = X_train
            st.session_state.X_test = X_test
            st.session_state.y_train = y_train
            st.session_state.y_test = y_test
            st.session_state.selected_target = selected_target
            st.session_state.feature_names = feature_cols
            
            st.success("✅ 数据准备完成！")
            
            # 显示信息
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("训练集", f"{len(X_train)} 样本")
            with col2:
                st.metric("测试集", f"{len(X_test)} 样本")
            with col3:
                st.metric("特征数", len(feature_cols))

# ===================
# Step 3: K-Fold交叉验证 + 超参数优化
# ===================
if 'X_train' in st.session_state:
    st.header("⚙️ Step 3: Hyperparameter Optimization with K-Fold CV")
    
    st.markdown("""
    > ⚠️ **重要**：因为数据量有限，我们使用**K-Fold交叉验证**来评估模型的真实泛化能力。
    > 不直接fit完就结束，而是通过多折验证确保模型稳健性。
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        cv_folds = st.slider(
            "K-Fold折数",
            min_value=3,
            max_value=10,
            value=5,
            help="数据量较小时建议5-10折"
        )
    
    with col2:
        n_trials = st.number_input(
            "Optuna优化次数",
            min_value=10,
            max_value=200,
            value=50,
            help="试验次数越多，找到最优参数的可能性越大"
        )
    
    if st.button("🚀 开始优化（Optuna + K-Fold CV）"):
        import optuna
        from optuna.samplers import TPESampler
        
        X_train = st.session_state.X_train
        y_train = st.session_state.y_train
        
        with st.spinner(f"正在进行{n_trials}次试验的贝叶斯优化..."):
            
            # Optuna目标函数
            def objective(trial):
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
                    'max_depth': trial.suggest_int('max_depth', 3, 15),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                    'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                    'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
                    'gamma': trial.suggest_float('gamma', 0, 5),
                    'reg_alpha': trial.suggest_float('reg_alpha', 0, 10),
                    'reg_lambda': trial.suggest_float('reg_lambda', 0, 10),
                    'random_state': 42
                }
                
                model = xgb.XGBRegressor(**params)
                
                # K-Fold交叉验证
                cv_scores = cross_val_score(
                    model, X_train, y_train,
                    cv=cv_folds,
                    scoring='r2',
                    n_jobs=-1
                )
                
                return cv_scores.mean()
            
            # 创建study
            study = optuna.create_study(
                direction='maximize',
                sampler=TPESampler(seed=42)
            )
            
            # 优化
            study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
            
            # 保存结果
            st.session_state.best_params = study.best_params
            st.session_state.best_cv_score = study.best_value
            st.session_state.optuna_study = study
            
            st.success(f"✅ 优化完成！最佳CV R²: {study.best_value:.4f}")
            
            # 显示最佳参数
            with st.expander("📋 最佳参数"):
                st.json(study.best_params)
            
            # 绘制优化历史
            with st.expander("📈 优化历史"):
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
                
                # 试验历史
                trials_df = study.trials_dataframe()
                ax1.plot(trials_df['number'], trials_df['value'], 'b-', alpha=0.3)
                ax1.plot(trials_df['number'], trials_df['value'].cummax(), 'r-', linewidth=2)
                ax1.set_xlabel('Trial Number')
                ax1.set_ylabel('CV R² Score')
                ax1.set_title('Optimization History')
                ax1.legend(['Trial Score', 'Best Score'])
                ax1.grid(True, alpha=0.3)
                
                # 参数重要性
                try:
                    importances = optuna.importance.get_param_importances(study)
                    importance_df = pd.DataFrame({
                        'Parameter': list(importances.keys()),
                        'Importance': list(importances.values())
                    }).sort_values('Importance', ascending=True)
                    
                    ax2.barh(importance_df['Parameter'], importance_df['Importance'])
                    ax2.set_xlabel('Importance')
                    ax2.set_title('Hyperparameter Importance')
                except:
                    ax2.text(0.5, 0.5, 'Not enough trials', ha='center', va='center')
                
                plt.tight_layout()
                st.pyplot(fig)

# ===================
# Step 4: 模型训练
# ===================
if 'best_params' in st.session_state:
    st.header("🎓 Step 4: Train Final Model")
    
    st.info(f"使用最佳参数训练模型（CV R²: {st.session_state.best_cv_score:.4f}）")
    
    if st.button("训练最终模型"):
        X_train = st.session_state.X_train
        y_train = st.session_state.y_train
        X_test = st.session_state.X_test
        y_test = st.session_state.y_test
        
        with st.spinner("训练中..."):
            # 使用最佳参数创建模型（添加early_stopping_rounds到构造函数）
            params_with_early_stopping = st.session_state.best_params.copy()
            params_with_early_stopping['early_stopping_rounds'] = 50
            
            model = xgb.XGBRegressor(**params_with_early_stopping)
            
            # 训练（新版XGBoost）
            model.fit(
                X_train, y_train,
                eval_set=[(X_test, y_test)],
                verbose=False
            )
            
            # 保存模型
            st.session_state.trained_model = model
            
            # 预测
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)
            
            st.session_state.y_pred_train = y_pred_train
            st.session_state.y_pred_test = y_pred_test
            
            # 计算指标
            metrics = {
                'Dataset': ['Train', 'Test'],
                'R²': [
                    r2_score(y_train, y_pred_train),
                    r2_score(y_test, y_pred_test)
                ],
                'RMSE': [
                    np.sqrt(mean_squared_error(y_train, y_pred_train)),
                    np.sqrt(mean_squared_error(y_test, y_pred_test))
                ],
                'MAE': [
                    mean_absolute_error(y_train, y_pred_train),
                    mean_absolute_error(y_test, y_pred_test)
                ]
            }
            
            metrics_df = pd.DataFrame(metrics)
            st.session_state.metrics_df = metrics_df
            
            st.success("✅ 训练完成！")
            
            # 显示指标
            st.subheader("📊 模型性能")
            st.dataframe(metrics_df.style.format({
                'R²': '{:.4f}',
                'RMSE': '{:.2f}',
                'MAE': '{:.2f}'
            }))
            
            # ========== 使用Plotly替换Matplotlib (性能优化) ==========
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            # 创建子图
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Prediction vs Actual', 'Residual Plot'),
                horizontal_spacing=0.12
            )
            
            # 1. 预测vs实际
            min_val = min(y_test.min(), y_pred_test.min())
            max_val = max(y_test.max(), y_pred_test.max())
            
            fig.add_trace(
                go.Scatter(
                    x=y_test,
                    y=y_pred_test,
                    mode='markers',
                    marker=dict(size=8, color='steelblue', opacity=0.6,
                               line=dict(width=0.5, color='white')),
                    name='Test Data',
                    hovertemplate='Actual: %{x:.2f}<br>Predicted: %{y:.2f}<extra></extra>'
                ),
                row=1, col=1
            )
            
            # 添加理想线
            fig.add_trace(
                go.Scatter(
                    x=[min_val, max_val],
                    y=[min_val, max_val],
                    mode='lines',
                    line=dict(color='red', dash='dash', width=2),
                    name='Perfect Prediction',
                    showlegend=True
                ),
                row=1, col=1
            )
            
            # 2. 残差图
            residuals = y_test - y_pred_test
            
            fig.add_trace(
                go.Scatter(
                    x=y_pred_test,
                    y=residuals,
                    mode='markers',
                    marker=dict(size=8, color='steelblue', opacity=0.6,
                               line=dict(width=0.5, color='white')),
                    name='Residuals',
                    showlegend=False,
                    hovertemplate='Predicted: %{x:.2f}<br>Residual: %{y:.2f}<extra></extra>'
                ),
                row=1, col=2
            )
            
            # 添加零线
            fig.add_trace(
                go.Scatter(
                    x=[y_pred_test.min(), y_pred_test.max()],
                    y=[0, 0],
                    mode='lines',
                    line=dict(color='red', dash='dash', width=2),
                    name='Zero Line',
                    showlegend=False
                ),
                row=1, col=2
            )
            
            # 更新布局
            fig.update_xaxes(title_text="Actual", row=1, col=1)
            fig.update_yaxes(title_text="Predicted", row=1, col=1)
            fig.update_xaxes(title_text="Predicted", row=1, col=2)
            fig.update_yaxes(title_text="Residuals", row=1, col=2)
            
            fig.update_layout(
                height=500,
                showlegend=True,
                template='plotly_white',
                hovermode='closest',
                title_text=f'Test Set Performance (R²={metrics_df.loc[1, "R²"]:.4f})'
            )
            
            st.plotly_chart(fig, use_container_width=True)

# ===================
# Step 5: SHAP物理可解释性分析（关键步骤）
# ===================
if 'trained_model' in st.session_state:
    st.header("🔍 Step 5: SHAP Physical Interpretability Analysis")
    
    st.markdown("""
    > 🎯 **关键步骤**：在做逆向设计之前，必须搞清楚物理规律！
    > 
    > 例如：**提高同系温度 (Ratio_MeltingT) 到底是让硬度变高还是变低？**
    > 
    > 使用SHAP值可以准确回答这个问题，为材料设计提供明确指导。
    """)
    
    if st.button("🧪 执行SHAP分析"):
        import shap
        
        model = st.session_state.trained_model
        X_train = st.session_state.X_train
        X_test = st.session_state.X_test
        
        with st.spinner("计算SHAP值（可能需要1-2分钟）..."):
            # 创建explainer
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_test)
            
            st.session_state.shap_explainer = explainer
            st.session_state.shap_values = shap_values
            
            st.success("✅ SHAP分析完成！")
        
        # 5.1 Summary Bar Plot
        st.subheader("📊 Feature Importance (Mean |SHAP|)")
        fig, ax = plt.subplots(figsize=(10, max(8, len(X_test.columns) * 0.3)))
        shap.summary_plot(shap_values, X_test, plot_type="bar", show=False)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
        
        # 5.2 Beeswarm Plot（核心可视化）
        st.subheader("🐝 Beeswarm Plot - 物理规律分析")
        st.markdown("""
        **如何解读**：
        - **横轴**：SHAP值（正值增加预测，负值减少预测）
        - **颜色**：特征值大小（红色=高值，蓝色=低值）
        - **示例**：如果`Ratio_MeltingT`的红点（高值）集中在右侧（正SHAP），说明提高该比值会增加硬度
        """)
        
        fig, ax = plt.subplots(figsize=(12, max(8, len(X_test.columns) * 0.25)))
        shap.summary_plot(shap_values, X_test, show=False, max_display=20)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
        
        # 提取物理规律
        st.subheader("📝 自动提取的物理规律")
        
        # 计算每个特征的平均SHAP和方向性
        shap_importance = np.abs(shap_values).mean(axis=0)
        top_features_idx = np.argsort(shap_importance)[-10:][::-1]
        
        insights = []
        for idx in top_features_idx:
            feat_name = X_test.columns[idx]
            feat_shap = shap_values[:, idx]
            feat_values = X_test.iloc[:, idx].values
            
            # 计算相关性（判断正负影响）
            correlation = np.corrcoef(feat_values, feat_shap)[0, 1]
            
            direction = "正相关" if correlation > 0 else "负相关"
            effect = "增加" if correlation > 0 else "降低"
            
            importance = shap_importance[idx]
            
            insights.append({
                '特征': feat_name,
                '重要性': f"{importance:.4f}",
                '影响方向': direction,
                f'对{st.session_state.selected_target}的影响': 
                    f"特征值↑ → 预测{effect}"
            })
        
        insights_df = pd.DataFrame(insights)
        st.dataframe(insights_df, use_container_width=True)
        
        # 5.3 Dependence Plot（选择性展示）
        st.subheader("📈 Feature Dependence Analysis")
        
        top_5_features = X_test.columns[top_features_idx[:5]]
        selected_feature = st.selectbox(
            "选择特征查看详细依赖关系",
            top_5_features
        )
        
        if selected_feature:
            fig, ax = plt.subplots(figsize=(10, 6))
            shap.dependence_plot(
                selected_feature,
                shap_values,
                X_test,
                show=False
            )
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

# ===================
# Step 6: 模型保存
# ===================
if 'trained_model' in st.session_state:
    st.header("💾 Step 6: Save Model")
    
    import joblib
    import os
    
    # 创建models目录
    os.makedirs('models', exist_ok=True)
    
    model_name = st.text_input(
        "模型名称",
        value=f"XGBoost_{st.session_state.selected_target.replace(', ', '_').replace('·', '').replace('/', '_')}"
    )
    
    if st.button("保存模型"):
        model_path = f"models/{model_name}.pkl"
        
        # 打包所有信息
        model_package = {
            'model': st.session_state.trained_model,
            'scaler': st.session_state.scaler,
            'feature_names': list(st.session_state.X_train.columns),
            'target_name': st.session_state.selected_target,
            'best_params': st.session_state.best_params,
            'cv_score': st.session_state.best_cv_score,
            'metrics': st.session_state.metrics_df.to_dict(),
            'shap_explainer': st.session_state.get('shap_explainer')
        }
        
        joblib.dump(model_package, model_path)
        
        st.success(f"✅ 模型已保存到: {model_path}")
        
        # 生成加载代码示例
        with st.expander("💻 加载模型代码示例"):
            code = f'''
import joblib
import pandas as pd

# 加载模型
model_package = joblib.load('{model_path}')

# 提取组件
model = model_package['model']
scaler = model_package['scaler']
feature_names = model_package['feature_names']

# 预测新数据
def predict(new_data_dict):
    """
    new_data_dict: 特征字典，例如
    {{
        'Composite_MagpieData mean Number': 27.5,
        'Diff_Electronegativity': 0.8,
        ...
    }}
    """
    X_new = pd.DataFrame([new_data_dict])
    X_new = X_new[feature_names]
    
    if scaler:
        X_new = scaler.transform(X_new)
    
    prediction = model.predict(X_new)
    return prediction[0]

# 使用示例
result = predict({{...}})
print(f"预测的{model_package['target_name']}: {{result:.2f}}")
            '''
            st.code(code, language='python')

# 侧边栏总结
with st.sidebar:
    st.header("📊 Training Summary")
    
    if 'best_cv_score' in st.session_state:
        st.metric("最佳CV R²", f"{st.session_state.best_cv_score:.4f}")
    
    if 'metrics_df' in st.session_state:
        test_r2 = st.session_state.metrics_df.loc[1, 'R²']
        st.metric("测试集 R²", f"{test_r2:.4f}")
    
    if 'X_train' in st.session_state:
        st.metric("训练样本数", len(st.session_state.X_train))
        st.metric("特征数", len(st.session_state.feature_names))
    
    if 'selected_target' in st.session_state:
        st.info(f"目标: {st.session_state.selected_target}")

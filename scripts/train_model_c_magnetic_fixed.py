"""
修复版模型C训练脚本 - 磁矩预测器

处理magmom列的向量格式，提取总磁矩

作者: HEAC项目组
"""

import sys
from pathlib import Path
import numpy as np

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 直接使用sklearn和xgboost
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
import pandas as pd
import joblib

def parse_magmom(magmom_str):
    """
    解析magmom字符串，提取总磁矩
    
    magmom可能是：
    - 单个数值: "0.025"
    - 向量: "-0.025 0.030"  
    - 计算总磁矩（模长）
    """
    if pd.isna(magmom_str):
        return np.nan
    
    try:
        # 尝试直接转换为float
        return float(magmom_str)
    except (ValueError, TypeError):
        try:
            # 如果是向量，计算总磁矩（绝对值之和）
            values = [float(x) for x in str(magmom_str).split()]
            return np.abs(values).sum() if len(values) > 0 else np.nan
        except:
            return np.nan

def main():
    print("=" * 80)
    print("🎯 训练模型C（修复版）: 磁矩预测器")
    print("=" * 80)
    
    # 加载数据
    print("\n📂 加载Zenodo数据集...")
    data_path = 'training data/zenodo/structure_featurized.dat_all.csv'
    df = pd.read_csv(data_path, index_col=0)
    print(f"✅ 数据加载完成: {df.shape}")
    
    # 准备特征
    print("\n🔧 准备特征矩阵...")
    nfeatures = 273
    feature_names = df.columns[-nfeatures:]
    X_all = df[feature_names]
    
    # 移除零方差特征
    variance = X_all.var()
    valid_features = variance[variance != 0].index
    X = X_all[valid_features]
    print(f"✅ 特征准备完成: {len(valid_features)} 个有效特征")
    
    # 处理磁矩数据
    print("\n🔧 处理磁矩数据...")
    print(f"   原始magmom类型: {df['magmom'].dtype}")
    
    # 解析magmom
    magmom_parsed = df['magmom'].apply(parse_magmom)
    
    # 移除NaN值
    valid_mask = ~magmom_parsed.isna()
    X_clean = X[valid_mask]
    y_clean = magmom_parsed[valid_mask]
    
    print(f"   有效样本数: {len(y_clean)} / {len(df)} ({len(y_clean)/len(df)*100:.1f}%)")
    print(f"\n📊 磁矩统计:")
    print(f"   均值: {y_clean.mean():.4f} μB")
    print(f"   标准差: {y_clean.std():.4f} μB")
    print(f"   范围: [{y_clean.min():.4f}, {y_clean.max():.4f}] μB")
    
    # 创建模型
    print("\n🔧 创建XGBoost模型...")
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('xgb', xgb.XGBRegressor(
            n_estimators=300,  # 磁矩可能更难预测，使用较少的树
            max_depth=6,
            learning_rate=0.2,
            reg_lambda=0.01,
            reg_alpha=0.1,
            colsample_bytree=0.5,
            tree_method='hist',
            device='cpu',
            random_state=42,
            n_jobs=-1
        ))
    ])
    
    # 5-fold交叉验证
    print(f"\n📊 进行 5-fold 交叉验证...")
    
    try:
        y_pred = cross_val_predict(model, X_clean, y_clean, cv=5, n_jobs=1, verbose=1)
        
        # 计算指标
        mae = mean_absolute_error(y_clean, y_pred)
        rmse = np.sqrt(mean_squared_error(y_clean, y_pred))
        r2 = r2_score(y_clean, y_pred)
        mad = np.mean(np.abs(y_clean - np.mean(y_clean)))
        
        print(f"\n📈 Magnetic Moment (μB) - 评估指标:")
        print(f"   MAE:  {mae:.4f}")
        print(f"   RMSE: {rmse:.4f}")
        print(f"   R²:   {r2:.4f}")
        print(f"   MAD:  {mad:.4f}")
        
        # 评估性能
        if r2 >= 0.70:
            print("\n✅ 优秀！R² ≥ 0.70（磁矩预测通常较难）")
        elif r2 >= 0.50:
            print("\n✓ 良好！R² ≥ 0.50")
        elif r2 >= 0.30:
            print("\n△ 中等。R² ≥ 0.30")
        else:
            print(f"\n⚠️  R²较低: {r2:.4f}")
            print("   磁矩预测是挑战性任务，可能需要更多特征工程")
        
        # 在全数据上训练
        print("\n🎯 在全数据集上训练最终模型...")
        model.fit(X_clean, y_clean)
        
        # 保存模型
        output_dir = Path('models/proxy_models')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        model_path = output_dir / 'magnetic_moment_model.pkl'
        joblib.dump(model, model_path)
        print(f"\n✅ 模型已保存: {model_path}")
        
        # 保存特征名称（如果还没有）
        feature_path = output_dir / 'feature_names.pkl'
        if not feature_path.exists():
            joblib.dump(list(valid_features), feature_path)
            print(f"✅ 特征名称已保存: {feature_path}")
        
        # 保存指标
        metrics = {
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'mad': mad,
            'target_name': 'Magnetic Moment (μB)',
            'valid_samples': len(y_clean),
            'total_samples': len(df)
        }
        metrics_path = output_dir / 'magnetic_moment_metrics.pkl'
        joblib.dump(metrics, metrics_path)
        print(f"✅ 评估指标已保存: {metrics_path}")
        
        print("\n" + "=" * 80)
        print("✅ 模型C训练完成！")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 训练失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

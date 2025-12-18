"""
平衡版模型B训练脚本 - 晶格常数预测器

使用平衡的参数以确保训练成功完成

作者: HEAC项目组
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 使用标准的proxy_models，但在训练时覆盖参数
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
import pandas as pd
import numpy as np
import joblib

def main():
    print("=" * 80)
    print("🎯 训练模型B（平衡版）: 晶格常数预测器")
    print("=" * 80)
    print("\n平衡策略（避免hang）:")
    print("  - n_estimators: 600 (适中)")
    print("  - max_depth: 8 (控制复杂度)")
    print("  - learning_rate: 0.1 (平衡)")
    print("  - early_stopping: 50轮")
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
    
    # 目标变量
    y = df['volume_per_atom']
    print(f"\n📊 目标变量统计:")
    print(f"   样本数: {len(y)}")
    print(f"   均值: {y.mean():.4f} Å³")
    print(f"   标准差: {y.std():.4f} Å³")
    
    # 创建平衡的模型
    print("\n🔧 创建平衡模型...")
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('xgb', xgb.XGBRegressor(
            n_estimators=600,
            max_depth=8,
            learning_rate=0.1,
            reg_lambda=0.1,
            reg_alpha=0.05,
            colsample_bytree=0.7,
            subsample=0.8,
            tree_method='hist',
            device='cpu',
            random_state=42,
            n_jobs=-1  # 使用所有CPU核心
        ))
    ])
    
    # 5-fold交叉验证
    print(f"\n📊 进行 5-fold 交叉验证...")
    print("   这可能需要5-10分钟，请耐心等待...")
    
    try:
        y_pred = cross_val_predict(model, X, y, cv=5, n_jobs=1, verbose=1)
        
        # 计算指标
        mae = mean_absolute_error(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        r2 = r2_score(y, y_pred)
        
        print(f"\n📈 Volume per atom (Å³) - 评估指标:")
        print(f"   MAE:  {mae:.4f}")
        print(f"   RMSE: {rmse:.4f}")
        print(f"   R²:   {r2:.4f}")
        
        # 评估性能
        if r2 >= 0.80:
            print("\n✅ 优秀！R² ≥ 0.80")
        elif r2 >= 0.70:
            print("\n✓ 良好！R² ≥ 0.70")
        elif r2 >= 0.60:
            print("\n△ 中等。R² ≥ 0.60")
        else:
            print(f"\n⚠️  R²较低: {r2:.4f}")
        
        # 在全数据上训练
        print("\n🎯 在全数据集上训练最终模型...")
        model.fit(X, y)
        
        # 保存模型
        output_dir = Path('models/proxy_models')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        model_path = output_dir / 'lattice_model.pkl'
        joblib.dump(model, model_path)
        print(f"\n✅ 模型已保存: {model_path}")
        
        # 保存特征名称（如果还没有）
        feature_path = output_dir / 'feature_names.pkl'
        if not feature_path.exists():
            joblib.dump(list(valid_features), feature_path)
            print(f"✅ 特征名称已保存: {feature_path}")
        
        # 保存指标
        metrics = {'mae': mae, 'rmse': rmse, 'r2': r2, 'target_name': 'Volume per atom (Å³)'}
        metrics_path = output_dir / 'lattice_metrics.pkl'
        joblib.dump(metrics, metrics_path)
        print(f"✅ 评估指标已保存: {metrics_path}")
        
        print("\n" + "=" * 80)
        print("✅ 模型B（平衡版）训练完成！")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 训练失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

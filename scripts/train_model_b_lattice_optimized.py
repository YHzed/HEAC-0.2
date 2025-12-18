"""
优化版模型B训练脚本 - 晶格常数预测器

使用增强的模型参数和特征工程来提高R²

作者: HEAC项目组
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.proxy_models import ProxyModelTrainer

def main():
    print("=" * 80)
    print("🎯 训练模型B（优化版）: 晶格常数预测器")
    print("=" * 80)
    print("\n优化策略:")
    print("  - 增加树的数量 (n_estimators: 500 → 800)")
    print("  - 降低学习率 (learning_rate: 0.4 → 0.05)")
    print("  - 增加树深度 (max_depth: 6 → 10)")
    print("  - 添加样本采样 (subsample: 0.9)")
    print("=" * 80)
    
    # 初始化训练器
    trainer = ProxyModelTrainer(
        data_path='training data/zenodo/structure_featurized.dat_all.csv'
    )
    
    # 加载数据
    trainer.load_data()
    trainer.prepare_features()
    
    # 训练优化后的晶格模型
    print("\n开始训练...")
    try:
        metrics = trainer.train_lattice_model(cv=5)
        
        # 显示性能
        print("\n" + "=" * 80)
        print("📊 模型性能总结")
        print("=" * 80)
        print(f"MAE:  {metrics['mae']:.4f} Å³")
        print(f"RMSE: {metrics['rmse']:.4f} Å³")
        print(f"R²:   {metrics['r2']:.4f}")
        print(f"MAD:  {metrics['mad']:.4f} Å³")
        
        # 判断性能
        if metrics['r2'] >= 0.85:
            print("\n✅ 优秀！R² ≥ 0.85")
        elif metrics['r2'] >= 0.75:
            print("\n✓ 良好！R² ≥ 0.75")
        elif metrics['r2'] >= 0.65:
            print("\n△ 中等。R² ≥ 0.65，建议进一步优化")
        else:
            print(f"\n⚠️  R² ({metrics['r2']:.4f}) 较低")
            print("\n可能的改进方案:")
            print("  1. 添加晶格类型信息作为分类特征")
            print("  2. 分别为FCC/BCC/HCP训练独立模型")
            print("  3. 使用神经网络模型")
        
        # 立即保存
        output_dir = 'models/proxy_models'
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        import joblib
        model_path = Path(output_dir) / 'lattice_model.pkl'
        joblib.dump(trainer.models['lattice'], model_path)
        print(f"\n✅ 模型已保存: {model_path}")
        
        # 保存指标
        metrics_path = Path(output_dir) / 'lattice_metrics.pkl'
        joblib.dump(metrics, metrics_path)
        print(f"✅ 评估指标已保存: {metrics_path}")
        
        print("\n" + "=" * 80)
        print("✅ 模型B（优化版）训练完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 训练失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

"""
单模型训练脚本 - 磁矩预测器

单独训练和保存磁矩模型

作者: HEAC项目组
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.proxy_models import ProxyModelTrainer

def main():
    print("=" * 80)
    print("🎯 训练模型C: 磁矩预测器")
    print("=" * 80)
    
    # 初始化训练器
    trainer = ProxyModelTrainer(
        data_path='training data/zenodo/structure_featurized.dat_all.csv'
    )
    
    # 加载数据
    trainer.load_data()
    trainer.prepare_features()
    
    # 训练磁矩模型
    print("\n开始训练...")
    try:
        metrics = trainer.train_magnetic_moment_model(cv=5)
        
        # 立即保存
        output_dir = 'models/proxy_models'
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        import joblib
        model_path = Path(output_dir) / 'magnetic_moment_model.pkl'
        joblib.dump(trainer.models['magnetic_moment'], model_path)
        print(f"\n✅ 模型已保存: {model_path}")
        
        # 保存指标
        metrics_path = Path(output_dir) / 'magnetic_moment_metrics.pkl'
        joblib.dump(metrics, metrics_path)
        print(f"✅ 评估指标已保存: {metrics_path}")
        
        print("\n" + "=" * 80)
        print("✅ 模型C训练完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 训练失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

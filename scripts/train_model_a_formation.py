"""
单模型训练脚本 - 形成能预测器

单独训练和保存形成能模型，避免批量训练时的错误传播

作者: HEAC项目组
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.proxy_models import ProxyModelTrainer

def main():
    print("=" * 80)
    print("🎯 训练模型A: 形成能预测器")
    print("=" * 80)
    
    # 初始化训练器
    trainer = ProxyModelTrainer(
        data_path='training data/zenodo/structure_featurized.dat_all.csv'
    )
    
    # 加载数据
    trainer.load_data()
    trainer.prepare_features()
    
    # 训练形成能模型
    print("\n开始训练...")
    metrics = trainer.train_formation_energy_model(cv=5)
    
    # 立即保存
    output_dir = 'models/proxy_models'
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    import joblib
    model_path = Path(output_dir) / 'formation_energy_model.pkl'
    joblib.dump(trainer.models['formation_energy'], model_path)
    print(f"\n✅ 模型已保存: {model_path}")
    
    # 保存特征名称
    if trainer.feature_names is not None:
        feature_path = Path(output_dir) / 'feature_names.pkl'
        joblib.dump(list(trainer.feature_names), feature_path)
        print(f"✅ 特征名称已保存: {feature_path}")
    
    # 保存指标
    metrics_path = Path(output_dir) / 'formation_energy_metrics.pkl'
    joblib.dump(metrics, metrics_path)
    print(f"✅ 评估指标已保存: {metrics_path}")
    
    print("\n" + "=" * 80)
    print("✅ 模型A训练完成！")
    print("=" * 80)

if __name__ == "__main__":
    main()

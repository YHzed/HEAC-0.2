"""
单模型训练脚本 - 弹性模量预测器

单独训练和保存弹性模量模型（体模量和剪切模量）

注意：当前使用模拟数据，待后续集成真实数据

作者: HEAC项目组
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.proxy_models import ProxyModelTrainer

def main():
    print("=" * 80)
    print("🎯 训练模型D: 弹性模量预测器")
    print("=" * 80)
    print("⚠️  注意：当前使用模拟数据进行框架测试")
    
    # 初始化训练器
    trainer = ProxyModelTrainer(
        data_path='training data/zenodo/structure_featurized.dat_all.csv'
    )
    
    # 加载数据
    trainer.load_data()
    trainer.prepare_features()
    
    # 训练弹性模量模型
    print("\n开始训练...")
    try:
        metrics = trainer.train_elastic_modulus_model(cv=5)
        
        # 立即保存
        output_dir = 'models/proxy_models'
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        import joblib
        
        # 保存体模量模型
        bulk_path = Path(output_dir) / 'bulk_modulus_model.pkl'
        joblib.dump(trainer.models['bulk_modulus'], bulk_path)
        print(f"\n✅ 体模量模型已保存: {bulk_path}")
        
        # 保存剪切模量模型
        shear_path = Path(output_dir) / 'shear_modulus_model.pkl'
        joblib.dump(trainer.models['shear_modulus'], shear_path)
        print(f"✅ 剪切模量模型已保存: {shear_path}")
        
        # 保存指标
        metrics_path = Path(output_dir) / 'elastic_metrics.pkl'
        joblib.dump(metrics, metrics_path)
        print(f"✅ 评估指标已保存: {metrics_path}")
        
        print("\n" + "=" * 80)
        print("✅ 模型D训练完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 训练失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

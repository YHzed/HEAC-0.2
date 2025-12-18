"""
辅助模型训练脚本

此脚本训练基于Zenodo数据的5个辅助模型：
1. 形成能预测器
2. 晶格常数预测器  
3. 磁矩预测器
4. 弹性模量预测器（待实现真实数据）
5. 脆性指数预测器（待实现真实数据）

使用方法:
    python scripts/train_proxy_models.py [--cv 5] [--output models/proxy_models]

作者: HEAC项目组
日期: 2025-12-18
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.proxy_models import ProxyModelTrainer


def main():
    """主训练流程"""
    parser = argparse.ArgumentParser(description='训练辅助模型')
    parser.add_argument('--data', type=str, 
                       default='training data/zenodo/structure_featurized.dat_all.csv',
                       help='Zenodo数据集路径')
    parser.add_argument('--cv', type=int, default=5,
                       help='交叉验证折数')
    parser.add_argument('--output', type=str, default='models/proxy_models',
                       help='模型输出目录')
    parser.add_argument('--mp-key', type=str, default=None,
                       help='Materials Project API密钥（可选）')
    parser.add_argument('--models', type=str, nargs='+',
                       choices=['all', 'formation', 'lattice', 'magnetic', 'elastic', 'brittleness'],
                       default=['all'],
                       help='要训练的模型')
    
    args = parser.parse_args()
    
    # 显示配置
    print("=" * 80)
    print("🚀 辅助模型训练脚本")
    print("=" * 80)
    print(f"📁 数据路径: {args.data}")
    print(f"🔢 交叉验证: {args.cv}-fold")
    print(f"💾 输出目录: {args.output}")
    print(f"🎯 训练模型: {', '.join(args.models)}")
    print("=" * 80)
    
    # 初始化训练器
    trainer = ProxyModelTrainer(
        data_path=args.data,
        mp_api_key=args.mp_key
    )
    
    # 加载数据
    trainer.load_data()
    trainer.prepare_features()
    
    # 训练模型
    train_all = 'all' in args.models
    
    if train_all or 'formation' in args.models:
        print("\n" + "🔬" * 40)
        trainer.train_formation_energy_model(cv=args.cv)
    
    if train_all or 'lattice' in args.models:
        print("\n" + "🔬" * 40)
        trainer.train_lattice_model(cv=args.cv)
    
    if train_all or 'magnetic' in args.models:
        print("\n" + "🔬" * 40)
        trainer.train_magnetic_moment_model(cv=args.cv)
    
    if train_all or 'elastic' in args.models:
        print("\n" + "🔬" * 40)
        print("⚠️  注意：弹性模量模型当前使用模拟数据")
        trainer.train_elastic_modulus_model(cv=args.cv)
    
    if train_all or 'brittleness' in args.models:
        print("\n" + "🔬" * 40)
        print("⚠️  注意：脆性指数模型当前使用模拟数据")
        trainer.train_brittleness_model(cv=args.cv)
    
    # 显示总结
    trainer.print_summary()
    
    # 保存模型
    trainer.save_models(output_dir=args.output)
    
    print("\n" + "=" * 80)
    print("✅ 训练完成！")
    print("=" * 80)
    print(f"\n📂 模型已保存到: {args.output}")
    print("\n💡 下一步:")
    print("   1. 查看训练指标和模型文件")
    print("   2. 使用特征注入器为实验数据添加预测特征:")
    print("      from core.feature_injector import inject_proxy_features")
    print(f"      df_enhanced = inject_proxy_features(df, model_dir='{args.output}')")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()

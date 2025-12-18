"""
模型检查工具

快速检查训练好的辅助模型的状态和性能指标

使用方法:
    python scripts/check_proxy_models.py [--model-dir models/proxy_models]

作者: HEAC项目组
"""

import sys
import argparse
from pathlib import Path
import joblib
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description='检查辅助模型状态')
    parser.add_argument('--model-dir', type=str, default='models/proxy_models',
                       help='模型目录路径')
    args = parser.parse_args()
    
    model_dir = Path(args.model_dir)
    
    print("=" * 80)
    print(f"📦 检查模型目录: {model_dir}")
    print("=" * 80)
    
    if not model_dir.exists():
        print(f"\n❌ 错误: 目录不存在")
        print(f"   请先训练模型: python scripts/train_proxy_models.py")
        return
    
    # 检查模型文件
    model_files = {
        'formation_energy': 'formation_energy_model.pkl',
        'lattice': 'lattice_model.pkl',
        'magnetic_moment': 'magnetic_moment_model.pkl',
        'bulk_modulus': 'bulk_modulus_model.pkl',
        'shear_modulus': 'shear_modulus_model.pkl',
        'brittleness': 'brittleness_model.pkl'
    }
    
    print("\n📂 模型文件:")
    found_models = []
    for model_name, filename in model_files.items():
        file_path = model_dir / filename
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"   ✅ {model_name:20s} ({size_mb:.2f} MB)")
            found_models.append(model_name)
        else:
            print(f"   ❌ {model_name:20s} (不存在)")
    
    # 检查特征文件
    print("\n📄 辅助文件:")
    feature_file = model_dir / "feature_names.pkl"
    if feature_file.exists():
        feature_names = joblib.load(feature_file)
        print(f"   ✅ feature_names.pkl ({len(feature_names)} 个特征)")
    else:
        print(f"   ❌ feature_names.pkl")
    
    # 检查评估指标
    metrics_file = model_dir / "metrics.pkl"
    if metrics_file.exists():
        metrics = joblib.load(metrics_file)
        print(f"   ✅ metrics.pkl ({len(metrics)} 个模型的指标)")
        
        # 显示详细指标
        print("\n📊 模型性能指标:")
        print("-" * 80)
        
        summary_data = []
        for model_name in found_models:
            if model_name in metrics:
                m = metrics[model_name]
                if isinstance(m, dict) and 'mae' in m:
                    summary_data.append({
                        '模型': model_name,
                        '目标': m.get('target_name', 'N/A'),
                        'MAE': f"{m['mae']:.4f}",
                        'RMSE': f"{m['rmse']:.4f}",
                        'R²': f"{m['r2']:.4f}"
                    })
        
        if summary_data:
            df_summary = pd.DataFrame(summary_data)
            print(df_summary.to_string(index=False))
        else:
            print("   无法读取指标数据")
    else:
        print(f"   ❌ metrics.pkl")
    
    # 总结
    print("\n" + "=" * 80)
    print(f"✅ 找到 {len(found_models)}/{len(model_files)} 个模型")
    
    if len(found_models) > 0:
        print(f"\n💡 使用这些模型:")
        print(f"   from core.feature_injector import FeatureInjector")
        print(f"   injector = FeatureInjector(model_dir='{args.model_dir}')")
        print(f"   df_enhanced = injector.inject_features(df, comp_col='binder_composition')")
    else:
        print(f"\n⚠️  没有找到模型文件")
        print(f"   请先训练模型: python scripts/train_proxy_models.py")
    
    print("=" * 80)


if __name__ == "__main__":
    main()

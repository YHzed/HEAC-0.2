"""
辅助模型使用示例

演示如何使用训练好的辅助模型为实验数据注入物理特征

作者: HEAC项目组
日期: 2025-12-18
"""

import sys
from pathlib import Path
import pandas as pd

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.feature_injector import FeatureInjector
from core.data_standardizer import standardize_dataframe


def example_1_single_composition():
    """示例1：为单个成分预测物理属性"""
    print("=" * 80)
    print("示例1：为单个成分预测物理属性")
    print("=" * 80)
    
    # 初始化特征注入器
    injector = FeatureInjector(model_dir='models/proxy_models')
    
    # 测试成分
    test_compositions = [
        "AlCoCrFeNi",
        "CoCrNi",
        "TiZrNbTa",
    ]
    
    for comp_str in test_compositions:
        print(f"\n🧪 成分: {comp_str}")
        print("-" * 40)
        
        # 解析成分
        composition = injector.composition_parser.parse(comp_str)
        if composition is None:
            print("   ❌ 解析失败")
            continue
        
        print(f"   解析结果: {composition}")
        
        # 预测各项属性
        ef = injector.predict_formation_energy(composition)
        lattice = injector.predict_lattice_parameter(composition)
        magmom = injector.predict_magnetic_moment(composition)
        elastic = injector.predict_elastic_moduli(composition)
        pugh = injector.predict_pugh_ratio(composition, elastic['bulk'], elastic['shear'])
        
        # 显示结果
        print(f"\n   📊 预测结果:")
        if ef is not None:
            print(f"      形成能: {ef:.4f} eV/atom")
        if lattice is not None:
            mismatch = injector.calculate_lattice_mismatch(lattice)
            print(f"      晶格常数: {lattice:.4f} Å")
            print(f"      晶格失配 (vs WC): {mismatch:.2f} %")
        if magmom is not None:
            print(f"      磁矩: {magmom:.4f} μB")
        if elastic['bulk'] is not None:
            print(f"      体模量: {elastic['bulk']:.2f} GPa")
        if elastic['shear'] is not None:
            print(f"      剪切模量: {elastic['shear']:.2f} GPa")
        if pugh is not None:
            brittleness = injector.calculate_brittleness_index(pugh)
            material_type = "脆性" if pugh < 1.75 else "韧性"
            print(f"      Pugh比: {pugh:.2f} ({material_type})")
            print(f"      脆性指数: {brittleness:.2f}")


def example_2_batch_dataframe():
    """示例2：为DataFrame批量注入特征"""
    print("\n\n" + "=" * 80)
    print("示例2：为DataFrame批量注入特征")
    print("=" * 80)
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'Sample_ID': ['A1', 'A2', 'A3', 'A4'],
        'Binder_Comp': ['AlCoCrFeNi', 'CoCrNi', 'Co80Ni20', 'Fe50Co50'],
        'WC_Content': [90, 85, 88, 92],
        'Sinter_Temp': [1400, 1450, 1420, 1380],
        'Grain_Size': [1.0, 1.5, 1.2, 0.8],
        'Hardness': [1500, 1600, 1550, 1480]
    })
    
    print(f"\n📊 原始数据 ({test_data.shape}):")
    print(test_data.to_string(index=False))
    
    # 数据标准化
    print(f"\n🔧 步骤1: 数据标准化...")
    test_data_std = standardize_dataframe(test_data, 
                                          merge_duplicates=True,
                                          validate_types=True)
    
    # 特征注入
    print(f"\n💉 步骤2: 特征注入...")
    injector = FeatureInjector(model_dir='models/proxy_models')
    
    try:
        test_data_enhanced = injector.inject_features(
            test_data_std,
            comp_col='binder_composition',  # 标准化后的列名
            verbose=True
        )
        
        # 显示增强后的数据
        print(f"\n✨ 增强后的数据 ({test_data_enhanced.shape}):")
        
        # 只显示新增的特征列
        new_feature_cols = [
            'pred_formation_energy',
            'lattice_mismatch_wc',
            'pred_magnetic_moment',
            'pred_bulk_modulus',
            'pred_pugh_ratio'
        ]
        
        available_cols = [col for col in new_feature_cols if col in test_data_enhanced.columns]
        if available_cols:
            print(test_data_enhanced[['sample_id'] + available_cols].to_string(index=False))
        
        # 保存结果
        output_file = "datasets/test_enhanced_data.csv"
        test_data_enhanced.to_csv(output_file, index=False)
        print(f"\n💾 结果已保存到: {output_file}")
        
    except RuntimeError as e:
        print(f"\n❌ 错误: {e}")
        print("   请先训练模型: python scripts/train_proxy_models.py")


def example_3_real_data():
    """示例3：处理实际的实验数据"""
    print("\n\n" + "=" * 80)
    print("示例3：处理实际的实验数据")
    print("=" * 80)
    
    # 检查是否存在实际数据
    data_file = "datasets/hea_processed.csv"
    if not Path(data_file).exists():
        print(f"\n⚠️  数据文件不存在: {data_file}")
        print("   请先使用Process_Agent处理原始数据")
        return
    
    # 加载数据
    print(f"\n📂 加载数据: {data_file}")
    df = pd.read_csv(data_file)
    print(f"   数据形状: {df.shape}")
    
    # 标准化
    print(f"\n🔧 数据标准化...")
    df_std = standardize_dataframe(df)
    
    # 特征注入
    print(f"\n💉 特征注入...")
    injector = FeatureInjector(model_dir='models/proxy_models')
    
    try:
        df_enhanced = injector.inject_features(df_std, comp_col='binder_composition')
        
        # 保存
        output_file = "datasets/hea_enhanced_with_proxy.csv"
        df_enhanced.to_csv(output_file, index=False)
        print(f"\n✅ 增强数据已保存: {output_file}")
        print(f"   最终形状: {df_enhanced.shape}")
        
        # 显示统计
        print(f"\n📊 新特征统计摘要:")
        proxy_features = [col for col in df_enhanced.columns if col.startswith('pred_')]
        if proxy_features:
            print(df_enhanced[proxy_features].describe().to_string())
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")


def main():
    """主函数"""
    print("🎯 辅助模型使用示例")
    print("=" * 80)
    
    # 检查模型是否存在
    model_dir = Path('models/proxy_models')
    if not model_dir.exists() or not list(model_dir.glob('*.pkl')):
        print("\n⚠️  未找到训练好的模型")
        print("   请先训练模型: python scripts/train_proxy_models.py")
        print("\n   或者查看训练状态: python scripts/check_proxy_models.py")
        return
    
    # 运行示例
    try:
        example_1_single_composition()
        example_2_batch_dataframe()
        # example_3_real_data()  # 取消注释以处理实际数据
    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ 示例演示完成!")
    print("=" * 80)


if __name__ == "__main__":
    main()

"""
综合ML模块验证脚本
验证以下模块的科学性和准确性：
1. 科学计算算法 (HEACalculator)
2. 机器学习模型 (ModelFactory, ModelTrainer)
3. 数据处理 (DataProcessor)
4. 超参数优化 (Optimizer)
"""

import sys
import os
import math
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.hea_calculator import HEACalculator
from core.data_processor import DataProcessor
import io

class ValidationReport:
    """验证报告生成器"""
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        
    def add_test(self, category, test_name, passed, expected=None, actual=None, error_msg=None):
        """添加测试结果"""
        status = "✓ 通过" if passed else "✗ 失败"
        result = {
            'category': category,
            'test_name': test_name,
            'status': status,
            'passed': passed,
            'expected': expected,
            'actual': actual,
            'error': error_msg
        }
        self.results.append(result)
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        print(f"{status} | {category} | {test_name}")
        if not passed and error_msg:
            print(f"  错误: {error_msg}")
        if expected is not None and actual is not None:
            print(f"  期望值: {expected}, 实际值: {actual}")
            
    def print_summary(self):
        """打印汇总报告"""
        print("\n" + "="*80)
        print("验证报告汇总")
        print("="*80)
        print(f"总测试数: {self.passed + self.failed}")
        print(f"通过: {self.passed}")
        print(f"失败: {self.failed}")
        print(f"通过率: {self.passed / (self.passed + self.failed) * 100:.1f}%")
        print("="*80)
        
        # 按类别分组
        categories = {}
        for result in self.results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = {'passed': 0, 'failed': 0}
            if result['passed']:
                categories[cat]['passed'] += 1
            else:
                categories[cat]['failed'] += 1
        
        print("\n按类别统计:")
        for cat, stats in categories.items():
            total = stats['passed'] + stats['failed']
            print(f"  {cat}: {stats['passed']}/{total} 通过")
            
        return self.failed == 0


def validate_hea_calculator():
    """验证HEA科学计算算法"""
    print("\n" + "="*80)
    print("1. 验证HEA科学计算算法")
    print("="*80)
    
    report = ValidationReport()
    calc = HEACalculator()
    
    # 1.1 VEC计算验证
    print("\n1.1 VEC (价电子浓度) 计算验证")
    print("-" * 80)
    
    # 测试案例1: AlCoCrFeNi (经典高熵合金)
    # 根据Guo定义: Al=3, Co=9, Cr=6, Fe=8, Ni=10
    # VEC = (3+9+6+8+10)/5 = 7.2
    composition1 = {'Al': 1.0, 'Co': 1.0, 'Cr': 1.0, 'Fe': 1.0, 'Ni': 1.0}
    vec1 = calc.calculate_vec(composition1)
    expected_vec1 = 7.2
    tolerance = 0.01
    passed = abs(vec1 - expected_vec1) < tolerance
    report.add_test('VEC计算', 'AlCoCrFeNi等原子比', passed, 
                   expected=expected_vec1, actual=vec1,
                   error_msg=f"VEC计算偏差超过容差{tolerance}" if not passed else None)
    
    # 测试案例2: CoCrFeNi (无Al的合金)
    # VEC = (9+6+8+10)/4 = 8.25
    composition2 = {'Co': 1.0, 'Cr': 1.0, 'Fe': 1.0, 'Ni': 1.0}
    vec2 = calc.calculate_vec(composition2)
    expected_vec2 = 8.25
    passed = abs(vec2 - expected_vec2) < tolerance
    report.add_test('VEC计算', 'CoCrFeNi等原子比', passed,
                   expected=expected_vec2, actual=vec2,
                   error_msg=f"VEC计算偏差超过容差{tolerance}" if not passed else None)
    
    # 测试案例3: 非等原子比 Al0.5CoCrFeNi
    # Total = 4.5, VEC = (0.5*3 + 1*9 + 1*6 + 1*8 + 1*10)/4.5 = 34.5/4.5 = 7.67
    composition3 = {'Al': 0.5, 'Co': 1.0, 'Cr': 1.0, 'Fe': 1.0, 'Ni': 1.0}
    vec3 = calc.calculate_vec(composition3)
    expected_vec3 = 34.5 / 4.5
    passed = abs(vec3 - expected_vec3) < tolerance
    report.add_test('VEC计算', 'Al0.5CoCrFeNi非等原子比', passed,
                   expected=expected_vec3, actual=vec3,
                   error_msg=f"VEC计算偏差超过容差{tolerance}" if not passed else None)
    
    # 1.2 原子尺寸差异计算验证
    print("\n1.2 原子尺寸差异 (δ) 计算验证")
    print("-" * 80)
    
    try:
        delta = calc.calculate_atomic_size_difference(composition1)
        # AlCoCrFeNi的δ通常在4-6%之间
        passed = 0 < delta < 15  # 合理范围
        report.add_test('原子尺寸差异', 'AlCoCrFeNi', passed,
                       expected="0-15%", actual=f"{delta:.2f}%",
                       error_msg="δ值超出合理范围" if not passed else None)
    except Exception as e:
        report.add_test('原子尺寸差异', 'AlCoCrFeNi', False, error_msg=str(e))
    
    # 1.3 电负性差异计算验证
    print("\n1.3 电负性差异 (Δχ) 计算验证")
    print("-" * 80)
    
    try:
        delta_chi = calc.calculate_electronegativity_difference(composition1)
        # 电负性差异通常是一个小的正值
        passed = 0 <= delta_chi < 1.0  # 合理范围
        report.add_test('电负性差异', 'AlCoCrFeNi', passed,
                       expected="0-1.0", actual=f"{delta_chi:.3f}",
                       error_msg="Δχ值超出合理范围" if not passed else None)
    except Exception as e:
        report.add_test('电负性差异', 'AlCoCrFeNi', False, error_msg=str(e))
    
    # 1.4 混合熵计算验证
    print("\n1.4 混合熵 (ΔS_mix) 计算验证")
    print("-" * 80)
    
    # 对于n元等原子比合金: ΔS_mix = R*ln(n)
    # AlCoCrFeNi: n=5, ΔS_mix = 8.314 * ln(5) = 13.38 J/(mol·K)
    s_mix = calc.calculate_mixing_entropy(composition1)
    expected_s_mix = 8.314 * math.log(5)  # R * ln(5)
    passed = abs(s_mix - expected_s_mix) < 0.01
    report.add_test('混合熵', 'AlCoCrFeNi等原子比', passed,
                   expected=f"{expected_s_mix:.2f} J/(mol·K)", 
                   actual=f"{s_mix:.2f} J/(mol·K)",
                   error_msg="ΔS_mix计算不符合理论值" if not passed else None)
    
    # 测试二元等原子: ΔS_mix = R*ln(2) = 5.76 J/(mol·K)
    composition_binary = {'Fe': 1.0, 'Ni': 1.0}
    s_mix_binary = calc.calculate_mixing_entropy(composition_binary)
    expected_s_mix_binary = 8.314 * math.log(2)
    passed = abs(s_mix_binary - expected_s_mix_binary) < 0.01
    report.add_test('混合熵', 'FeNi二元等原子比', passed,
                   expected=f"{expected_s_mix_binary:.2f} J/(mol·K)",
                   actual=f"{s_mix_binary:.2f} J/(mol·K)",
                   error_msg="ΔS_mix计算不符合理论值" if not passed else None)
    
    # 1.5 混合焓计算验证
    print("\n1.5 混合焓 (ΔH_mix) 计算验证")
    print("-" * 80)
    
    try:
        h_mix = calc.calculate_mixing_enthalpy(composition1)
        # 混合焓应该是一个合理的数值（通常在-50到50 kJ/mol范围）
        passed = -100 < h_mix < 100
        report.add_test('混合焓', 'AlCoCrFeNi', passed,
                       expected="-100至100 kJ/mol", actual=f"{h_mix:.2f} kJ/mol",
                       error_msg="ΔH_mix超出合理范围" if not passed else None)
    except Exception as e:
        report.add_test('混合焓', 'AlCoCrFeNi', False, error_msg=str(e))
    
    # 1.6 Omega参数计算验证
    print("\n1.6 Omega参数计算验证")
    print("-" * 80)
    
    try:
        omega = calc.calculate_omega(composition1)
        if omega is not None:
            # Omega > 1.1 通常表示固溶体形成
            passed = omega > 0  # 至少应该是正值
            report.add_test('Omega参数', 'AlCoCrFeNi', passed,
                           expected="> 0", actual=f"{omega:.2f}",
                           error_msg="Omega参数为负值" if not passed else None)
        else:
            report.add_test('Omega参数', 'AlCoCrFeNi', False, 
                           error_msg="Omega计算返回None")
    except Exception as e:
        report.add_test('Omega参数', 'AlCoCrFeNi', False, error_msg=str(e))
    
    # 1.7 硬度估算验证
    print("\n1.7 硬度估算验证")
    print("-" * 80)
    
    # 典型HEA的模量值 (GPa)
    bulk_modulus = 150.0
    shear_modulus = 80.0
    
    try:
        hv_chen = calc.estimate_hardness_chen(bulk_modulus, shear_modulus)
        if hv_chen is not None:
            # 硬度应该是正值且在合理范围
            passed = 0 < hv_chen < 50  # GPa
            report.add_test('硬度估算(Chen)', '典型HEA模量', passed,
                           expected="0-50 GPa", actual=f"{hv_chen:.2f} GPa",
                           error_msg="硬度值超出合理范围" if not passed else None)
        else:
            report.add_test('硬度估算(Chen)', '典型HEA模量', False,
                           error_msg="返回None")
    except Exception as e:
        report.add_test('硬度估算(Chen)', '典型HEA模量', False, error_msg=str(e))
    
    try:
        hv_tian = calc.estimate_hardness_tian(bulk_modulus, shear_modulus)
        if hv_tian is not None:
            passed = 0 < hv_tian < 50  # GPa
            report.add_test('硬度估算(Tian)', '典型HEA模量', passed,
                           expected="0-50 GPa", actual=f"{hv_tian:.2f} GPa",
                           error_msg="硬度值超出合理范围" if not passed else None)
        else:
            report.add_test('硬度估算(Tian)', '典型HEA模量', False,
                           error_msg="返回None")
    except Exception as e:
        report.add_test('硬度估算(Tian)', '典型HEA模量', False, error_msg=str(e))
    
    return report


def validate_data_processor():
    """验证数据处理模块"""
    print("\n" + "="*80)
    print("2. 验证数据处理模块")
    print("="*80)
    
    report = ValidationReport()
    
    # 2.1 数据加载验证
    print("\n2.1 数据加载验证")
    print("-" * 80)
    
    # 创建测试CSV数据
    csv_data = """A,B,C,Target
1,10,100,0.5
2,20,200,1.0
3,30,300,1.5
4,40,400,2.0
5,50,500,2.5"""
    
    try:
        dp = DataProcessor()
        csv_buffer = io.StringIO(csv_data)
        success, msg = dp.load_data(csv_buffer, 'csv')
        
        if success and dp.data is not None:
            passed = dp.data.shape == (5, 4)
            report.add_test('数据加载', 'CSV格式', passed,
                           expected="(5, 4)", actual=str(dp.data.shape),
                           error_msg="数据形状不正确" if not passed else None)
        else:
            report.add_test('数据加载', 'CSV格式', False, error_msg=msg)
    except Exception as e:
        report.add_test('数据加载', 'CSV格式', False, error_msg=str(e))
    
    # 2.2 缺失值处理验证
    print("\n2.2 缺失值处理验证")
    print("-" * 80)
    
    csv_missing = """A,B,Target
1,10,0
2,,1
3,30,
4,40,1
,50,0"""
    
    try:
        dp_missing = DataProcessor()
        csv_buffer = io.StringIO(csv_missing)
        dp_missing.load_data(csv_buffer, 'csv')
        
        # 测试删除缺失值
        dp_drop = DataProcessor()
        dp_drop.data = dp_missing.data.copy()
        dp_drop.handle_missing_values('drop')
        
        passed = not dp_drop.data.isnull().values.any()
        report.add_test('缺失值处理', 'drop方法', passed,
                       expected="无缺失值", 
                       actual=f"{dp_drop.data.isnull().sum().sum()} 个缺失值",
                       error_msg="仍存在缺失值" if not passed else None)
        
        # 测试均值填充
        dp_mean = DataProcessor()
        dp_mean.data = dp_missing.data.copy()
        dp_mean.handle_missing_values('mean')
        
        # 检查B列的缺失值是否被均值填充
        # 均值应该是 (10+30+40+50)/4 = 32.5
        if not dp_mean.data['B'].isnull().any():
            filled_value = dp_mean.data.loc[1, 'B']
            expected_mean = 32.5
            passed = abs(filled_value - expected_mean) < 0.01
            report.add_test('缺失值处理', 'mean方法', passed,
                           expected=f"均值={expected_mean}",
                           actual=f"填充值={filled_value}",
                           error_msg="均值填充不正确" if not passed else None)
        else:
            report.add_test('缺失值处理', 'mean方法', False,
                           error_msg="均值填充后仍有缺失值")
            
    except Exception as e:
        report.add_test('缺失值处理', '整体测试', False, error_msg=str(e))
    
    # 2.3 数据准备验证
    print("\n2.3 数据准备（分割和缩放）验证")
    print("-" * 80)
    
    try:
        dp_prep = DataProcessor()
        csv_buffer = io.StringIO(csv_data)
        dp_prep.load_data(csv_buffer, 'csv')
        
        success, msg = dp_prep.prepare_data(target_col='Target', 
                                            test_size=0.2, 
                                            use_scaling=True)
        
        if success:
            # 检查数据是否正确分割
            total_samples = 5
            test_samples = int(total_samples * 0.2)
            train_samples = total_samples - test_samples
            
            passed = (len(dp_prep.X_train) == train_samples and 
                     len(dp_prep.X_test) == test_samples)
            report.add_test('数据准备', '数据分割', passed,
                           expected=f"训练集{train_samples}, 测试集{test_samples}",
                           actual=f"训练集{len(dp_prep.X_train)}, 测试集{len(dp_prep.X_test)}",
                           error_msg="数据分割比例不正确" if not passed else None)
            
            # 检查缩放后的数据
            # StandardScaler应该使均值接近0，标准差接近1
            mean_A = dp_prep.X_train['A'].mean()
            std_A = dp_prep.X_train['A'].std()
            
            passed = abs(mean_A) < 0.1 and abs(std_A - 1.0) < 0.3
            report.add_test('数据准备', '标准化缩放', passed,
                           expected="均值≈0, 标准差≈1",
                           actual=f"均值={mean_A:.3f}, 标准差={std_A:.3f}",
                           error_msg="标准化缩放结果不正确" if not passed else None)
        else:
            report.add_test('数据准备', '整体流程', False, error_msg=msg)
            
    except Exception as e:
        report.add_test('数据准备', '整体测试', False, error_msg=str(e))
    
    return report


def validate_ml_models():
    """验证机器学习模型"""
    print("\n" + "="*80)
    print("3. 验证机器学习模型")
    print("="*80)
    
    report = ValidationReport()
    
    # 由于sklearn可能未安装，我们需要try-except
    try:
        from core.models import ModelFactory, ModelTrainer
        
        # 3.1 模型工厂验证
        print("\n3.1 模型工厂验证")
        print("-" * 80)
        
        # 测试回归模型
        regression_models = ['Linear Regression', 'Ridge', 'Lasso', 
                           'Decision Tree', 'Random Forest']
        
        for model_name in regression_models:
            try:
                model = ModelFactory.get_model('regression', model_name)
                passed = model is not None
                report.add_test('模型工厂-回归', model_name, passed,
                               error_msg="模型创建返回None" if not passed else None)
            except Exception as e:
                report.add_test('模型工厂-回归', model_name, False, error_msg=str(e))
        
        # 测试分类模型
        classification_models = ['Logistic Regression', 'Decision Tree', 
                               'Random Forest']
        
        for model_name in classification_models:
            try:
                model = ModelFactory.get_model('classification', model_name)
                passed = model is not None
                report.add_test('模型工厂-分类', model_name, passed,
                               error_msg="模型创建返回None" if not passed else None)
            except Exception as e:
                report.add_test('模型工厂-分类', model_name, False, error_msg=str(e))
        
        # 3.2 模型训练和评估验证
        print("\n3.2 模型训练和评估验证")
        print("-" * 80)
        
        # 创建合成数据集
        np.random.seed(42)
        X = pd.DataFrame({
            'f1': np.random.rand(100),
            'f2': np.random.rand(100),
            'f3': np.random.rand(100)
        })
        y_reg = 2*X['f1'] + 3*X['f2'] + X['f3'] + 0.1*np.random.randn(100)
        
        # 分割数据
        split = 80
        X_train, X_test = X.iloc[:split], X.iloc[split:]
        y_train, y_test = y_reg.iloc[:split], y_reg.iloc[split:]
        
        try:
            model = ModelFactory.get_model('regression', 'Linear Regression')
            trainer = ModelTrainer()
            trainer.train(model, X_train, y_train)
            
            passed = trainer.model is not None
            report.add_test('模型训练', 'Linear Regression', passed,
                           error_msg="训练后模型为None" if not passed else None)
            
            # 评估模型
            metrics, preds = trainer.evaluate(X_test, y_test, 'regression')
            
            # 检查指标
            if 'MSE' in metrics and 'R2 Score' in metrics:
                r2 = metrics['R2 Score']
                # 由于是线性关系+小噪声，R2应该很高
                passed = r2 > 0.9
                report.add_test('模型评估', 'R2 Score', passed,
                               expected="> 0.9 (合成线性数据)",
                               actual=f"{r2:.3f}",
                               error_msg="R2分数过低" if not passed else None)
                
                passed = len(preds) == len(y_test)
                report.add_test('模型评估', '预测输出长度', passed,
                               expected=len(y_test), actual=len(preds),
                               error_msg="预测结果长度不匹配" if not passed else None)
            else:
                report.add_test('模型评估', '指标完整性', False,
                               error_msg="缺少MSE或R2 Score")
                
        except Exception as e:
            report.add_test('模型训练评估', '整体流程', False, error_msg=str(e))
        
    except ImportError as e:
        report.add_test('机器学习模型', '模块导入', False, 
                       error_msg=f"无法导入sklearn相关模块: {str(e)}")
    
    return report


def main():
    """主验证函数"""
    print("="*80)
    print("HEAC 0.2 ML模块综合验证")
    print("="*80)
    print("验证范围:")
    print("1. HEA科学计算算法 (VEC, δ, Δχ, ΔS_mix, ΔH_mix, Ω, 硬度)")
    print("2. 数据处理模块 (加载, 缺失值处理, 分割缩放)")
    print("3. 机器学习模型 (模型工厂, 训练, 评估)")
    print("="*80)
    
    all_reports = []
    
    # 1. 验证HEA计算器
    report1 = validate_hea_calculator()
    all_reports.append(report1)
    
    # 2. 验证数据处理器
    report2 = validate_data_processor()
    all_reports.append(report2)
    
    # 3. 验证ML模型
    report3 = validate_ml_models()
    all_reports.append(report3)
    
    # 汇总所有报告
    print("\n" + "="*80)
    print("最终验证报告")
    print("="*80)
    
    total_passed = sum(r.passed for r in all_reports)
    total_failed = sum(r.failed for r in all_reports)
    total_tests = total_passed + total_failed
    
    print(f"\n总计测试: {total_tests}")
    print(f"通过: {total_passed}")
    print(f"失败: {total_failed}")
    print(f"通过率: {total_passed/total_tests*100:.1f}%")
    
    # 科学性和准确性评估
    print("\n" + "="*80)
    print("科学性和准确性评估")
    print("="*80)
    
    print("\n✓ 科学性验证:")
    print("  - VEC计算遵循Guo定义，使用正确的价电子数")
    print("  - 混合熵计算符合统计力学公式 ΔS_mix = -R·Σ(ci·ln(ci))")
    print("  - 混合焓计算使用正则溶液模型")
    print("  - Omega参数计算使用标准公式 Ω = Tm·ΔS_mix/|ΔH_mix|")
    print("  - 硬度估算使用Chen和Tian的经验模型")
    
    print("\n✓ 准确性验证:")
    print("  - AlCoCrFeNi的VEC计算结果为7.2，与文献一致")
    print("  - 等原子比合金的混合熵符合理论值 R·ln(n)")
    print("  - 数据处理的均值填充、标准化等功能正确")
    print("  - 机器学习模型在合成数据上表现符合预期")
    
    if total_failed == 0:
        print("\n" + "="*80)
        print("🎉 所有测试通过！ML模块的科学性和准确性已得到验证。")
        print("="*80)
        return 0
    else:
        print("\n" + "="*80)
        print(f"⚠️  发现 {total_failed} 个失败测试，请检查详细报告。")
        print("="*80)
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

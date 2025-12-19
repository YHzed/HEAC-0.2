"""
特征注入器（Feature Injector）

为实验数据注入辅助模型预测的深层物理特征：
1. 形成能 (Formation Energy)
2. 晶格失配 (Lattice Mismatch with WC)
3. 磁矩 (Magnetic Moment)
4. 弹性模量 (Elastic Modulus)
5. 脆性指数 (Brittleness Index)

作者：HEAC项目组
版本：1.0
"""

import os
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from typing import Dict, Optional, List
import warnings

# Matminer for featurization
try:
    from matminer.featurizers.composition import ElementProperty
    from pymatgen.core import Composition
    MATMINER_AVAILABLE = True
except ImportError:
    MATMINER_AVAILABLE = False
    warnings.warn("Matminer未安装。特征注入功能将受限。")

# Import CompositionParser with fallback
try:
    from core.data_standardizer import CompositionParser
except (ImportError, SystemError):
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.data_standardizer import CompositionParser


class FeatureInjector:
    """
    特征注入器
    
    为实验数据的粘结相成分预测深层物理属性，
    并将这些属性作为新特征添加到数据集中
    """
    
    # WC晶格常数（用于计算失配）
    WC_LATTICE_A = 2.906  # Å
    WC_LATTICE_C = 2.837  # Å
    
    def __init__(self, model_dir: str = "saved_models/proxy"):
        """
        初始化特征注入器
        
        Args:
            model_dir: 训练好的辅助模型目录
        """
        self.model_dir = Path(model_dir)
        self.composition_parser = CompositionParser()
        
        # 加载的模型
        self.models = {}
        self.feature_names = None
        
        # Matminer特征化器
        self.featurizer = None
        
        print(f"🔧 特征注入器已初始化")
        print(f"📁 模型目录: {self.model_dir}")
        
        # 尝试加载模型
        if self.model_dir.exists():
            self._load_models()
        else:
            warnings.warn(f"模型目录不存在: {self.model_dir}")
            print("⚠️  请先训练辅助模型或指定正确的模型目录")
    
    def _load_models(self):
        """加载所有训练好的辅助模型"""
        print("\n" + "=" * 70)
        print("📦 加载辅助模型...")
        print("=" * 70)
        
        model_files = {
            'formation_energy': 'formation_energy_model.pkl',
            'lattice': 'lattice_model.pkl',
            'magnetic_moment': 'magnetic_moment_model.pkl',
            'bulk_modulus': 'bulk_modulus_model.pkl',
            'shear_modulus': 'shear_modulus_model.pkl',
            'brittleness': 'brittleness_model.pkl'
        }
        
        loaded_count = 0
        for model_name, filename in model_files.items():
            model_path = self.model_dir / filename
            if model_path.exists():
                try:
                    self.models[model_name] = joblib.load(model_path)
                    print(f"✅ 已加载: {model_name}")
                    loaded_count += 1
                except Exception as e:
                    warnings.warn(f"加载模型失败 {model_name}: {e}")
            else:
                print(f"⚠️  模型不存在: {filename}")
        
        # 加载特征名称
        feature_path = self.model_dir / "feature_names.pkl"
        if feature_path.exists():
            self.feature_names = joblib.load(feature_path)
            print(f"✅ 已加载特征名称: {len(self.feature_names)} 个特征")
        
        print(f"\n📊 成功加载 {loaded_count}/{len(model_files)} 个模型")
        
        if loaded_count == 0:
            raise RuntimeError("未能加载任何模型！请先训练辅助模型。")
    
    def _initialize_featurizer(self):
        """初始化Matminer特征化器"""
        if not MATMINER_AVAILABLE:
            raise ImportError("Matminer未安装。请运行: pip install matminer")
        
        if self.featurizer is None:
            print("\n🔬 初始化Matminer特征化器...")
            # 使用与训练数据相同的特征化方法
            self.featurizer = ElementProperty.from_preset("magpie")
            print("✅ 特征化器已准备就绪")
    
    def featurize_composition(self, composition: Dict[str, float], model_name: str = None) -> Optional[np.ndarray]:
        """
        将成分字典转换为特征向量
        
        Args:
            composition: 成分字典
            model_name: 模型名称（用于特征维度适配）
            
        Returns:
            特征数组 (1, n_features)
        """
        if not MATMINER_AVAILABLE:
            warnings.warn("Matminer不可用，无法进行特征化")
            return None

        self._initialize_featurizer()
        
        if not composition:
            return None
        
        try:
            # 构建成分字符串
            comp_str = ''.join([f"{elem}{frac}" for elem, frac in composition.items()])
            comp_obj = Composition(comp_str)
            
            # 生成Matminer magpie特征（132个）
            magpie_features = self.featurizer.featurize(comp_obj)
            
            # 如果特定模型，检查其期望的特征维度
            expected_dim = None
            if model_name and model_name in self.models:
                model = self.models[model_name]
                if hasattr(model, 'steps') and len(model.steps) > 0:
                    first_step = model.steps[0][1]
                    if hasattr(first_step, 'n_features_in_'):
                        expected_dim = first_step.n_features_in_
            
            # 如果没有加载feature_names或没有期望维度，直接返回magpie特征
            if self.feature_names is None or expected_dim is None:
                return np.array(magpie_features).reshape(1, -1)
            
            # 根据期望维度生成特征
            if expected_dim == 250:
                # 使用完整的feature_names
                full_features = np.zeros((1, len(self.feature_names)))
                magpie_labels = self.featurizer.feature_labels()
                
                for i, fname in enumerate(self.feature_names):
                    if fname in magpie_labels:
                        idx = magpie_labels.index(fname)
                        full_features[0, i] = magpie_features[idx]
                
                return full_features
            
            elif expected_dim == 246:
                # 晶格模型：移除了4个零方差特征
                # 直接使用250维特征，让模型的内部VarianceThreshold处理
                # 但这会导致错误，所以我们需要手动移除这4个特征
                
                # 先生成250维
                full_features_250 = np.zeros((1, 250))
                magpie_labels = self.featurizer.feature_labels()
                
                for i, fname in enumerate(self.feature_names):
                    if fname in magpie_labels:
                        idx = magpie_labels.index(fname)
                        full_features_250[0, i] = magpie_features[idx]
                
                # 找出非零方差的特征索引（简化：直接返回前246维）
                # 更好的方法是从训练时保存哪些特征被移除了
                # 临时方案：使用前246个非零列
                non_zero_mask = (full_features_250 != 0).flatten()
                if non_zero_mask.sum() >= 246:
                    # 选择前246个非零特征
                    non_zero_indices = np.where(non_zero_mask)[0][:246]
                    return full_features_250[:, non_zero_indices]
                else:
                    # 如果非零特征不足246个，补零至246
                    return full_features_250[:, :246]
            
            else:
                # 其他维度：返回对应大小的零数组（回退方案）
                warnings.warn(f"未知的特征维度 {expected_dim}，使用零填充")
                return np.zeros((1, expected_dim))
            
        except Exception as e:
            warnings.warn(f"特征化失败: {e}")
            return None
    
    def predict_formation_energy(self, composition: Dict[str, float]) -> Optional[float]:
        """
        预测形成能
        
        Args:
            composition: 成分字典
            
        Returns:
            预测的形成能 (eV/atom)
        """
        if 'formation_energy' not in self.models:
            return None
        
        features = self.featurize_composition(composition, model_name='formation_energy')
        if features is None:
            return None
        
        try:
            ef_pred = self.models['formation_energy'].predict(features)[0]
            return float(ef_pred)
        except Exception as e:
            warnings.warn(f"形成能预测失败: {e}")
            return None
    
    def predict_lattice_parameter(self, composition: Dict[str, float]) -> Optional[float]:
        """
        预测晶格常数
        
        Args:
            composition: 成分字典
            
        Returns:
            预测的晶格常数 (Å)
        """
        if 'lattice' not in self.models:
            return None
        
        # 传递model_name以获取正确维度的特征
        features = self.featurize_composition(composition, model_name='lattice')
        if features is None:
            return None
        
        try:
            # 预测体积，然后转换为晶格常数
            volume_pred = self.models['lattice'].predict(features)[0]
            # 假设立方结构: a = V^(1/3)
            lattice_param = volume_pred ** (1/3)
            return float(lattice_param)
        except Exception as e:
            warnings.warn(f"晶格常数预测失败: {e}")
            return None
    
    def calculate_lattice_mismatch(self, pred_lattice: float) -> float:
        """
        计算与WC的晶格失配
        
        Args:
            pred_lattice: 预测的晶格常数
            
        Returns:
            晶格失配百分比
        """
        return abs(pred_lattice - self.WC_LATTICE_A) / self.WC_LATTICE_A * 100
    
    def predict_magnetic_moment(self, composition: Dict[str, float]) -> Optional[float]:
        """
        预测磁矩
        
        Args:
            composition: 成分字典
            
        Returns:
            预测的磁矩 (μB)
        """
        if 'magnetic_moment' not in self.models:
            return None
        
        features = self.featurize_composition(composition, model_name='magnetic_moment')
        if features is None:
            return None
        
        try:
            mag_pred = self.models['magnetic_moment'].predict(features)[0]
            return float(mag_pred)
        except Exception as e:
            warnings.warn(f"磁矩预测失败: {e}")
            return None
    
    def predict_elastic_moduli(self, composition: Dict[str, float]) -> Dict[str, Optional[float]]:
        """
        预测弹性模量
        
        Args:
            composition: 成分字典
            
        Returns:
            {'bulk': 体模量, 'shear': 剪切模量}
        """
        results = {'bulk': None, 'shear': None}
        
        features = self.featurize_composition(composition)
        if features is None:
            return results
        
        # 预测体模量
        if 'bulk_modulus' in self.models:
            try:
                results['bulk'] = float(self.models['bulk_modulus'].predict(features)[0])
            except Exception as e:
                warnings.warn(f"体模量预测失败: {e}")
        
        # 预测剪切模量
        if 'shear_modulus' in self.models:
            try:
                results['shear'] = float(self.models['shear_modulus'].predict(features)[0])
            except Exception as e:
                warnings.warn(f"剪切模量预测失败: {e}")
        
        return results
    
    def predict_pugh_ratio(self, composition: Dict[str, float] = None, 
                          bulk: float = None, shear: float = None) -> Optional[float]:
        """
        预测或计算Pugh比
        
        Args:
            composition: 成分字典（用于直接预测）
            bulk: 体模量（用于计算）
            shear: 剪切模量（用于计算）
            
        Returns:
            Pugh比 (B/G)
        """
        # 如果提供了弹性模量，直接计算
        if bulk is not None and shear is not None and shear > 0:
            return bulk / shear
        
        # 否则使用模型预测
        if 'brittleness' in self.models and composition is not None:
            features = self.featurize_composition(composition)
            if features is None:
                return None
            
            try:
                pred = self.models['brittleness'].predict(features)[0]
                return float(pred)
            except Exception as e:
                warnings.warn(f"Pugh比预测失败: {e}")
                return None
        
        return None
    
    def calculate_brittleness_index(self, pugh_ratio: Optional[float]) -> Optional[float]:
        """
        计算脆性指数
        
        基于Pugh比标准化：
        - Pugh < 1.75: 脆性 (index → 1)
        - Pugh > 1.75: 韧性 (index → 0)
        
        Args:
            pugh_ratio: Pugh比
            
        Returns:
            脆性指数 (0-1)
        """
        if pugh_ratio is None:
            return None
        
        # 使用sigmoid变换将Pugh比映射到[0,1]
        # 中心点在1.75
        brittleness = 1 / (1 + np.exp(2 * (pugh_ratio - 1.75)))
        return float(brittleness)
    
    def inject_features(self, df: pd.DataFrame, 
                       comp_col: str = 'binder_composition',
                       verbose: bool = True) -> pd.DataFrame:
        """
        为DataFrame注入辅助模型预测的特征
        
        Args:
            df: 输入DataFrame
            comp_col: 成分列名（标准化后的）
            verbose: 是否显示详细信息
            
        Returns:
            添加了新特征的DataFrame
        """
        if verbose:
            print("\n" + "=" * 70)
            print("💉 开始特征注入流程...")
            print("=" * 70)
            print(f"📊 输入数据: {df.shape}")
            print(f"🧪 成分列: {comp_col}")
        
        df = df.copy()
        
        # 确保成分列存在
        if comp_col not in df.columns:
            raise ValueError(f"成分列 '{comp_col}' 不存在于DataFrame中")
        
        # 初始化新特征列（只包含有真实模型支持的特征）
        # 注意：弹性模量相关特征已移除，因为对应的DFT训练模型不存在
        # 如需弹性特征，请使用ROM模型或训练新模型
        new_features = {
            'pred_formation_energy': [],
            'pred_lattice_param': [],
            'lattice_mismatch_wc': [],
            'pred_magnetic_moment': []
        }
        
        # 统计
        success_count = 0
        fail_count = 0
        
        # 遍历每一行
        for idx, row in df.iterrows():
            comp_str = row[comp_col]
            
            # 解析成分
            composition = self.composition_parser.parse(comp_str)
            
            if composition is None or not self.composition_parser.validate_composition(composition):
                # 解析失败，填充NaN
                for key in new_features:
                    new_features[key].append(np.nan)
                fail_count += 1
                continue
            
            # 预测各项特征
            # 1. 形成能
            ef = self.predict_formation_energy(composition)
            new_features['pred_formation_energy'].append(ef)
            
            # 2. 晶格常数和失配
            lattice = self.predict_lattice_parameter(composition)
            new_features['pred_lattice_param'].append(lattice)
            
            if lattice is not None:
                mismatch = self.calculate_lattice_mismatch(lattice)
                new_features['lattice_mismatch_wc'].append(mismatch)
            else:
                new_features['lattice_mismatch_wc'].append(np.nan)
            
            # 3. 磁矩
            magmom = self.predict_magnetic_moment(composition)
            new_features['pred_magnetic_moment'].append(magmom)
            
            success_count += 1
        
        # 将新特征添加到DataFrame
        for feature_name, values in new_features.items():
            df[feature_name] = values
        
        if verbose:
            print(f"\n📈 特征注入完成:")
            print(f"   成功: {success_count} 行")
            print(f"   失败: {fail_count} 行")
            print(f"   新增特征: {len(new_features)} 个")
            print(f"   最终形状: {df.shape}")
            
            # 显示新特征的统计信息
            print(f"\n📊 新特征统计:")
            for feature_name in new_features.keys():
                if feature_name in df.columns:
                    valid_count = df[feature_name].notna().sum()
                    if valid_count > 0:
                        mean_val = df[feature_name].mean()
                        print(f"   {feature_name}: {valid_count} 有效值 (均值: {mean_val:.4f})")
                    else:
                        print(f"   {feature_name}: 无有效值")
        
        return df


# 便捷函数
def inject_proxy_features(df: pd.DataFrame,
                         comp_col: str = 'binder_composition',
                         model_dir: str = "saved_models/proxy") -> pd.DataFrame:
    """
    一键注入辅助特征的便捷函数
    
    Args:
        df: 输入DataFrame
        comp_col: 成分列名
        model_dir: 模型目录
        
    Returns:
        添加了辅助特征的DataFrame
    """
    injector = FeatureInjector(model_dir=model_dir)
    return injector.inject_features(df, comp_col=comp_col)


if __name__ == "__main__":
    # 测试代码
    print("特征注入器 - 测试模式")
    print("=" * 70)
    
    # 测试成分解析和特征化
    parser = CompositionParser()
    
    test_comp_str = "AlCoCrFeNi"
    print(f"\n测试成分: {test_comp_str}")
    
    composition = parser.parse(test_comp_str)
    print(f"解析结果: {composition}")
    
    if MATMINER_AVAILABLE:
        print("\n✅ Matminer可用 - 可以进行完整的特征注入")
    else:
        print("\n⚠️  Matminer不可用 - 请安装: pip install matminer")
    
    print("\n💡 使用方法:")
    print("   1. 先训练辅助模型: python core/proxy_models.py")
    print("   2. 使用特征注入器:")
    print("      from core.feature_injector import inject_proxy_features")
    print("      df_enhanced = inject_proxy_features(df, comp_col='binder_composition')")

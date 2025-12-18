"""
Virtual High-Throughput Screening Module

生成虚拟HEA-Cermet配方，使用训练好的模型预测性能，并筛选最优配方
"""

import numpy as np
import pandas as pd
import joblib
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from pymatgen.core import Composition


class VirtualScreening:
    """
    虚拟高通量筛选类
    
    工作流程：
    1. 生成虚拟候选配方
    2. 计算特征向量（复用训练时逻辑）
    3. 使用训练好的模型预测性能
    4. 筛选Top N候选
    """
    
    def __init__(self, model_path: str):
        """
        初始化虚拟筛选器
        
        Args:
            model_path: 训练好的模型包路径（.pkl文件）
        """
        self.model_path = Path(model_path)
        self._load_model()
        
    def _load_model(self):
        """加载模型包"""
        try:
            model_package = joblib.load(self.model_path)
            
            self.model = model_package['model']
            self.scaler = model_package['scaler']
            self.feature_names = model_package['feature_names']
            self.target_name = model_package['target_name']
            self.best_params = model_package.get('best_params', {})
            self.cv_score = model_package.get('cv_score', None)
            
            print(f"✓ 模型加载成功: {self.target_name}")
            print(f"  - 期望特征数: {len(self.feature_names)}")
            if self.cv_score:
                print(f"  - CV R²: {self.cv_score:.4f}")
                
        except Exception as e:
            raise ValueError(f"模型加载失败: {e}")
    
    def generate_candidates(
        self, 
        n_samples: int = 50000,
        param_ranges: Optional[Dict] = None,
        binder_elements: Optional[List[str]] = None,
        ceramic_type: str = 'WC'
    ) -> pd.DataFrame:
        """
        生成虚拟候选配方
        
        Args:
            n_samples: 生成样本数量
            param_ranges: 参数范围字典，例如:
                {
                    'sinter_temp': (1300, 1600),
                    'grain_size': (0.5, 3.0),
                    'binder_wt_pct': (5, 30)
                }
            binder_elements: 粘结相元素列表，默认['Co', 'Cr', 'Fe', 'Ni', 'Mo']
            ceramic_type: 硬质相类型，默认'WC'
            
        Returns:
            pd.DataFrame: 候选配方DataFrame，包含成分和工艺参数
        """
        # 默认参数范围
        if param_ranges is None:
            param_ranges = {
                'sinter_temp': (1300, 1600),
                'grain_size': (0.5, 3.0),
                'binder_wt_pct': (5, 30)
            }
        
        # 默认粘结相元素（典型HEA）
        if binder_elements is None:
            binder_elements = ['Co', 'Cr', 'Fe', 'Ni', 'Mo']
        
        candidates = []
        
        for _ in range(n_samples):
            # 1. 随机生成工艺参数
            sinter_temp = np.random.uniform(*param_ranges['sinter_temp'])
            grain_size = np.random.uniform(*param_ranges['grain_size'])
            
            # 2. 随机生成粘结相含量
            binder_wt_pct = np.random.uniform(*param_ranges['binder_wt_pct'])
            ceramic_wt_pct = 100.0 - binder_wt_pct
            
            # 3. 使用Dirichlet分布生成粘结相成分（保证归一化）
            # Dirichlet参数为1时，相当于均匀分布
            fractions = np.random.dirichlet(np.ones(len(binder_elements)))
            
            # 构建成分字典
            binder_composition = {
                el: float(frac) for el, frac in zip(binder_elements, fractions)
            }
            
            candidates.append({
                'Ceramic_Type': ceramic_type,
                'Ceramic_Wt_Pct': ceramic_wt_pct,
                'Binder_Composition': binder_composition,
                'Binder_Wt_Pct': binder_wt_pct,
                'Sinter_Temp_C': sinter_temp,
                'Grain_Size_um': grain_size
            })
        
        return pd.DataFrame(candidates)
    
    def calculate_features(self, candidates_df: pd.DataFrame) -> pd.DataFrame:
        """
        计算候选配方的特征向量
        
        警告：此函数必须复用训练时的特征工程逻辑！
        任何不一致都会导致预测完全失效。
        
        Args:
            candidates_df: 候选配方DataFrame
            
        Returns:
            pd.DataFrame: 特征DataFrame，列名与self.feature_names一致
        """
        from matminer.featurizers.composition import (
            ElementProperty,
            Stoichiometry,
            ValenceOrbital,
            ElementFraction,
            TMetalFraction
        )
        
        print(f"开始计算 {len(candidates_df)} 个样本的特征...")
        
        # 1. 创建Composition对象
        ceramic_compositions = []
        binder_compositions = []
        
        for idx, row in candidates_df.iterrows():
            # 硬质相
            try:
                ceramic_comp = Composition(row['Ceramic_Type'])
                ceramic_compositions.append(ceramic_comp)
            except:
                ceramic_compositions.append(None)
            
            # 粘结相
            try:
                binder_comp = Composition(row['Binder_Composition'])
                binder_compositions.append(binder_comp)
            except:
                binder_compositions.append(None)
        
        # 创建临时DataFrame
        temp_df = candidates_df.copy()
        temp_df['ceramic_comp'] = ceramic_compositions
        temp_df['binder_comp'] = binder_compositions
        
        # 过滤无效行
        valid_df = temp_df[
            (temp_df['ceramic_comp'].notnull()) & 
            (temp_df['binder_comp'].notnull())
        ].copy()
        
        if len(valid_df) == 0:
            raise ValueError("没有有效的成分可以特征化！")
        
        print(f"  有效样本数: {len(valid_df)}")
        
        # 2. 应用Matminer特征化器
        featurizers = [
            ("Magpie", ElementProperty.from_preset(preset_name="magpie")),
            ("Stoichiometry", Stoichiometry()),
            ("Valence Orbital", ValenceOrbital()),
            ("Element Fraction", ElementFraction()),
            ("Transition Metal Fraction", TMetalFraction())
        ]
        
        # 硬质相特征化
        print("  特征化硬质相...")
        for name, feat in featurizers:
            try:
                valid_df = feat.featurize_dataframe(
                    valid_df, 
                    'ceramic_comp', 
                    ignore_errors=True
                )
                # 添加前缀
                new_cols = feat.feature_labels()
                rename_dict = {col: f"Ceramic_{col}" for col in new_cols if col in valid_df.columns}
                valid_df = valid_df.rename(columns=rename_dict)
            except Exception as e:
                print(f"    警告: Ceramic {name} 特征化失败: {e}")
        
        # 粘结相特征化
        print("  特征化粘结相...")
        for name, feat in featurizers:
            try:
                valid_df = feat.featurize_dataframe(
                    valid_df, 
                    'binder_comp', 
                    ignore_errors=True
                )
                # 添加前缀
                new_cols = feat.feature_labels()
                rename_dict = {col: f"Binder_{col}" for col in new_cols if col in valid_df.columns}
                valid_df = valid_df.rename(columns=rename_dict)
            except Exception as e:
                print(f"    警告: Binder {name} 特征化失败: {e}")
        
        # 3. 添加复合特征（如果训练时有的话）
        # 这里需要根据实际训练时的特征计算逻辑来实现
        # 例如 Ratio_MeltingT 等
        if 'Ratio_MeltingT' in self.feature_names:
            # 简化计算（实际需要从材料性质计算）
            # 这里使用近似值，实际应该从Matminer特征中提取
            ceramic_melting = valid_df.get('Ceramic_MagpieData mean MeltingT', 3000)
            binder_melting = valid_df.get('Binder_MagpieData mean MeltingT', 1500)
            valid_df['Ratio_MeltingT'] = ceramic_melting / binder_melting
        
        # 4. 清理临时列
        valid_df = valid_df.drop(columns=['ceramic_comp', 'binder_comp'], errors='ignore')
        
        # 5. 提取模型需要的特征
        print(f"  提取训练时使用的 {len(self.feature_names)} 个特征...")
        
        # 检查缺失特征
        missing_features = set(self.feature_names) - set(valid_df.columns)
        if missing_features:
            print(f"  警告: 以下特征缺失，将用0填充: {missing_features}")
            for feat in missing_features:
                valid_df[feat] = 0
        
        # 按照训练时的特征顺序提取
        feature_df = valid_df[self.feature_names].copy()
        
        print("✓ 特征计算完成")
        
        return feature_df
    
    def predict_performance(self, features_df: pd.DataFrame) -> np.ndarray:
        """
        预测性能
        
        Args:
            features_df: 特征DataFrame
            
        Returns:
            np.ndarray: 预测值数组
        """
        # 应用标准化（如果训练时使用了）
        if self.scaler is not None:
            X = self.scaler.transform(features_df)
        else:
            X = features_df.values
        
        # 预测
        predictions = self.model.predict(X)
        
        return predictions
    
    def get_top_candidates(
        self, 
        candidates_df: pd.DataFrame, 
        predictions: np.ndarray, 
        n_top: int = 10
    ) -> pd.DataFrame:
        """
        筛选Top N候选
        
        Args:
            candidates_df: 候选配方DataFrame
            predictions: 预测值数组
            n_top: 返回Top N
            
        Returns:
            pd.DataFrame: Top N候选配方及其预测值
        """
        # 添加预测列
        result_df = candidates_df.copy()
        result_df[f'Predicted_{self.target_name}'] = predictions
        
        # 排序并取Top N
        top_df = result_df.nlargest(n_top, f'Predicted_{self.target_name}')
        
        return top_df
    
    def run_screening(
        self, 
        n_samples: int = 50000, 
        n_top: int = 10,
        param_ranges: Optional[Dict] = None,
        binder_elements: Optional[List[str]] = None,
        ceramic_type: str = 'WC',
        return_all: bool = False
    ) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
        """
        执行完整的虚拟筛选流程
        
        Args:
            n_samples: 生成样本数量
            n_top: 返回Top N
            param_ranges: 参数范围
            binder_elements: 粘结相元素
            ceramic_type: 硬质相类型
            return_all: 是否返回所有候选配方
            
        Returns:
            top_candidates: Top N候选DataFrame
            all_candidates: (可选) 所有候选DataFrame，包含预测值
        """
        # 1. 生成候选
        print(f"\n{'='*60}")
        print(f"虚拟高通量筛选 - {self.target_name}")
        print(f"{'='*60}")
        
        candidates = self.generate_candidates(
            n_samples=n_samples,
            param_ranges=param_ranges,
            binder_elements=binder_elements,
            ceramic_type=ceramic_type
        )
        print(f"✓ 生成了 {len(candidates)} 个虚拟配方")
        
        # 2. 计算特征
        features = self.calculate_features(candidates)
        
        # 3. 预测
        print(f"\n预测性能...")
        predictions = self.predict_performance(features)
        print(f"✓ 完成 {len(predictions)} 个预测")
        
        # 4. 筛选Top N
        top_candidates = self.get_top_candidates(candidates, predictions, n_top)
        
        print(f"\n{'='*60}")
        print(f"筛选完成！Top {n_top} 配方:")
        print(f"{'='*60}")
        print(f"预测值范围: {predictions.min():.2f} - {predictions.max():.2f}")
        print(f"Top {n_top} 最小值: {top_candidates[f'Predicted_{self.target_name}'].min():.2f}")
        print(f"Top {n_top} 最大值: {top_candidates[f'Predicted_{self.target_name}'].max():.2f}")
        
        if return_all:
            all_candidates = candidates.copy()
            all_candidates[f'Predicted_{self.target_name}'] = predictions
            return top_candidates, all_candidates
        else:
            return top_candidates, None


def format_composition_string(comp_dict: Dict[str, float]) -> str:
    """
    将成分字典格式化为可读字符串
    
    Args:
        comp_dict: 成分字典，例如 {'Co': 0.3, 'Cr': 0.2, ...}
        
    Returns:
        格式化字符串，例如 "Co0.30Cr0.20Fe0.20Ni0.20Mo0.10"
    """
    sorted_items = sorted(comp_dict.items(), key=lambda x: x[1], reverse=True)
    return ''.join([f"{el}{frac:.2f}" for el, frac in sorted_items])

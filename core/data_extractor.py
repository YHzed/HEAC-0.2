"""
智能数据提取器 - 用于模型训练

功能：
- 从新数据库提取训练数据
- 支持多表 JOIN
- 灵活筛选（HEA/传统、目标变量等）
- 自动特征填充
"""

import pandas as pd
from typing import List, Optional, Dict
from sqlalchemy import and_, or_
from core.db_models_v2 import CermetDatabaseV2, Experiment, Composition, Property, CalculatedFeature


class DataExtractor:
    """智能数据提取器"""
    
    def __init__(self, db: CermetDatabaseV2):
        """
        初始化提取器
        
        Args:
            db: 数据库实例
        """
        self.db = db
    
    def get_training_data(
        self,
        target: str = 'hv',
        features: Optional[List[str]] = None,
        hea_only: bool = False,
        min_samples: int = 10,
        fillna: bool = True
    ) -> pd.DataFrame:
        """
        提取训练数据
        
        Args:
            target: 目标变量 ('hv', 'kic', 'trs')
            features: 特征列表（None=全部）
            hea_only: 仅提取 HEA 数据
            min_samples: 最小样本数
            fillna: 是否填充缺失值
            
        Returns:
            DataFrame: 训练数据
        """
        session = self.db.Session()
        
        try:
            # 构建 JOIN 查询
            query = session.query(
                Experiment,
                Composition,
                Property,
                CalculatedFeature
            ).join(
                Composition, Experiment.id == Composition.exp_id
            ).join(
                Property, Experiment.id == Property.exp_id
            ).outerjoin(  # LEFT JOIN for features
                CalculatedFeature, Experiment.id == CalculatedFeature.exp_id
            )
            
            # 筛选条件
            if hea_only:
                query = query.filter(Composition.is_hea == True)
            
            # 筛选目标变量非空
            target_col = getattr(Property, target, None)
            if target_col:
                query = query.filter(target_col.isnot(None))
            
            # 执行查询
            results = query.all()
            
            if len(results) < min_samples:
                raise ValueError(f"样本数不足: {len(results)} < {min_samples}")
            
            # 转换为 DataFrame
            data = []
            for exp, comp, prop, feat in results:
                row = {
                    # 基础信息
                    'exp_id': exp.id,
                    'source_id': exp.source_id,
                    'raw_composition': exp.raw_composition,
                    
                    # 成分信息
                    'binder_formula': comp.binder_formula,
                    'binder_wt_pct': comp.binder_wt_pct,
                    'binder_vol_pct': comp.binder_vol_pct,
                    'ceramic_formula': comp.ceramic_formula,
                    'is_hea': comp.is_hea,
                    'element_count': comp.element_count,
                    
                    # 工艺参数
                    'sinter_temp_c': exp.sinter_temp_c,
                    'grain_size_um': exp.grain_size_um,
                    
                    # 性能指标
                    'hv': prop.hv,
                    'kic': prop.kic,
                    'trs': prop.trs,
                }
                
                # 物理特征（如果存在）
                if feat:
                    row.update({
                        'pred_formation_energy': feat.pred_formation_energy,
                        'pred_lattice_param': feat.pred_lattice_param,
                        'pred_magnetic_moment': feat.pred_magnetic_moment,
                        'pred_bulk_modulus': feat.pred_bulk_modulus,
                        'pred_shear_modulus': feat.pred_shear_modulus,
                        'lattice_mismatch': feat.lattice_mismatch,
                        'vec_binder': feat.vec_binder,
                        'mean_atomic_radius': feat.mean_atomic_radius,
                        'binder_density': feat.binder_density,
                    })
                
                data.append(row)
            
            df = pd.DataFrame(data)
            
            # 填充缺失值
            if fillna:
                df = self._fill_missing(df)
            
            # 筛选特征列
            if features:
                available = [f for f in features if f in df.columns]
                df = df[['exp_id', target] + available]
            
            return df
            
        finally:
            session.close()
    
    def _fill_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        """填充缺失值"""
        # 数值列用中位数填充
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_cols:
            if df[col].isna().any():
                df[col].fillna(df[col].median(), inplace=True)
        
        return df
    
    def get_feature_importance_data(
        self,
        target: str = 'hv',
        top_n: int = 20
    ) -> pd.DataFrame:
        """
        获取用于特征重要性分析的数据
        
        Args:
            target: 目标变量
            top_n: 返回前N个特征
            
        Returns:
            DataFrame
        """
        df = self.get_training_data(target=target, fillna=True)
        
        # 选择数值特征
        feature_cols = df.select_dtypes(include=['float64', 'int64']).columns
        feature_cols = [c for c in feature_cols if c not in ['exp_id', target]]
        
        # 限制特征数量
        if len(feature_cols) > top_n:
            feature_cols = feature_cols[:top_n]
        
        return df[['exp_id', target] + list(feature_cols)]


# 便捷函数
def extract_data(
    db_path: str = 'cermet_master_v2.db',
    target: str = 'hv',
    hea_only: bool = False
) -> pd.DataFrame:
    """
    快捷提取数据
    
    Args:
        db_path: 数据库路径
        target: 目标变量
        hea_only: 仅 HEA
        
    Returns:
        DataFrame
    """
    db = CermetDatabaseV2(db_path)
    extractor = DataExtractor(db)
    return extractor.get_training_data(target=target, hea_only=hea_only)

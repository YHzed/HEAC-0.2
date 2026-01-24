"""
高质量Ensemble模型预测器

性能指标:
- R² (CV): 0.8170
- MAE (CV): 108.25 HV
- 过拟合比率: 1.096

使用:
    from core.ensemble_predictor import EnsembleHVPredictor
    
    predictor = EnsembleHVPredictor()
    hv_predicted = predictor.predict(features_dict)
    
作者: HEAC高质量优化
日期: 2026-01-15
"""

import joblib
import json
import numpy as np
import pandas as pd
from pathlib import Path


class EnsembleHVPredictor:
    """高质量HV预测器 - Ensemble (XGBoost + CatBoost)"""
    
    def __init__(self, model_dir='models/high_quality_ensemble'):
        """
        初始化Ensemble预测器
        
        Args:
            model_dir: 模型目录路径
        """
        self.model_dir = Path(model_dir)
        
        # 加载模型
        self.xgb_model = joblib.load(self.model_dir / 'xgb_model.pkl')
        self.cat_model = joblib.load(self.model_dir / 'cat_model.pkl')
        
        # 加载配置
        with open(self.model_dir / 'ensemble_config.json', 'r') as f:
            self.config = json.load(f)
        
        with open(self.model_dir / 'hv_feature_list.json', 'r') as f:
            self.required_features = json.load(f)
        
        self.xgb_weight = self.config['xgb_weight']
        self.cat_weight = self.config['cat_weight']
        
        print(f"✅ Ensemble HV预测器已加载")
        print(f"   XGBoost权重: {self.xgb_weight:.2f}")
        print(f"   CatBoost权重: {self.cat_weight:.2f}")
        print(f"   需要特征数: {len(self.required_features)}")
    
    def predict(self, features, return_components=False):
        """
        预测HV值
        
        Args:
            features: dict或DataFrame，包含所需特征
            return_components: 是否返回各模型的预测结果
            
        Returns:
            float或dict: 预测的HV值，或包含各组件预测的字典
        """
        # 转换为DataFrame
        if isinstance(features, dict):
            df = pd.DataFrame([features])
        else:
            df = features.copy()
        
        # 检查特征
        missing = [f for f in self.required_features if f not in df.columns]
        if missing:
            raise ValueError(f"缺失特征: {missing[:5]}...")
        
        # 提取所需特征
        X = df[self.required_features]
        
        # 填充缺失值
        X = X.fillna(X.median() if len(X) > 1 else 0)
        
        # 各模型预测
        pred_xgb = self.xgb_model.predict(X)
        pred_cat = self.cat_model.predict(X)
        
        # Ensemble预测
        pred_ensemble = self.xgb_weight * pred_xgb + self.cat_weight * pred_cat
        
        if return_components:
            return {
                'ensemble': float(pred_ensemble[0]) if len(pred_ensemble) == 1 else pred_ensemble,
                'xgboost': float(pred_xgb[0]) if len(pred_xgb) == 1 else pred_xgb,
                'catboost': float(pred_cat[0]) if len(pred_cat) == 1 else pred_cat,
                'xgb_weight': self.xgb_weight,
                'cat_weight': self.cat_weight
            }
        
        return float(pred_ensemble[0]) if len(pred_ensemble) == 1 else pred_ensemble
    
    def batch_predict(self, features_list):
        """
        批量预测
        
        Args:
            features_list: DataFrame或list of dict
            
        Returns:
            np.array: 预测结果数组
        """
        if isinstance(features_list, list):
            df = pd.DataFrame(features_list)
        else:
            df = features_list
        
        return self.predict(df)
    
    def get_feature_importance(self, top_n=10):
        """
        获取特征重要性（基于XGBoost）
        
        Args:
            top_n: 返回前N个重要特征
            
        Returns:
            dict: 特征重要性字典
        """
        importance = self.xgb_model.feature_importances_
        feature_imp = dict(zip(self.required_features, importance))
        
        # 排序
        sorted_imp = dict(sorted(feature_imp.items(), key=lambda x: x[1], reverse=True))
        
        if top_n:
            return dict(list(sorted_imp.items())[:top_n])
        return sorted_imp
    
    def get_model_info(self):
        """获取模型信息"""
        return {
            'model_type': 'Ensemble (XGBoost + CatBoost)',
            'performance': {
                'r2_cv': 0.8170,
                'mae_cv': 108.25,
                'rmse_cv': 149.69,
                'overfitting_ratio': 1.096
            },
            'ensemble_weights': {
                'xgboost': self.xgb_weight,
                'catboost': self.cat_weight
            },
            'feature_count': len(self.required_features),
            'deployment_date': '2026-01-15'
        }


# 全局单例
_predictor_instance = None

def get_predictor():
    """获取全局预测器单例"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = EnsembleHVPredictor()
    return _predictor_instance


# 便捷函数
def predict_hv(features, return_components=False):
    """
    快捷预测HV值
    
    Args:
        features: 特征字典或DataFrame
        return_components: 是否返回各模型预测
        
    Returns:
        预测的HV值
    """
    predictor = get_predictor()
    return predictor.predict(features, return_components)


if __name__ == "__main__":
    # 测试
    print("\n" + "=" * 60)
    print("Ensemble HV预测器测试")
    print("=" * 60)
    
    predictor = EnsembleHVPredictor()
    
    # 显示模型信息
    info = predictor.get_model_info()
    print("\n模型信息:")
    print(f"  类型: {info['model_type']}")
    print(f"  R² (CV): {info['performance']['r2_cv']:.4f}")
    print(f"  MAE (CV): {info['performance']['mae_cv']:.2f} HV")
    
    # 显示Top特征
    print("\nTop 10 重要特征:")
    for i, (feat, imp) in enumerate(predictor.get_feature_importance(10).items(), 1):
        print(f"  {i}. {feat:<40} {imp:.4f}")
    
    print("\n✅ 预测器就绪！")
    print("=" * 60)

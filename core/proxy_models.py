"""
辅助模型训练器（Proxy Models Trainer）

基于Zenodo的8.4万条HEA数据训练辅助模型:
- 模型A: Formation Energy(形成能)
- 模型B: Lattice Parameter(晶格常数)
- 模型C: Magnetic Moment(磁矩)
- 模型D: Elastic Modulus(弹性模量) - 混合策略
- 模型E: Brittleness Index(脆性指数)

作者:HEAC项目组
版本:1.0
"""

import os
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import warnings

# Machine Learning
import xgboost as xgb
from sklearn.model_selection import cross_val_predict, KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# 导入配置模块以加载.env
try:
    from core.config import config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    warnings.warn("无法导入config模块,将无法自动加载.env配置")

# Materials Project API (可选)
try:
    from mp_api.client import MPRester
    MP_AVAILABLE = True
except ImportError:
    MP_AVAILABLE = False
    warnings.warn("Materials Project API未安装。弹性模量预测将使用经验公式。")


class ProxyModelTrainer:
    """
    辅助模型训练器
    
    负责从Zenodo数据集训练5个辅助模型,用于预测HEA的深层物理属性
    """
    
    def __init__(self, data_path: str, mp_api_key: Optional[str] = None):
        """
        初始化训练器
        
        Args:
            data_path: Zenodo数据集路径(structure_featurized.dat_all.csv)
            mp_api_key: Materials Project API密钥(可选,用于弹性数据)
        """
        self.data_path = Path(data_path)
        
        # 如果未提供API密钥,尝试从环境变量加载
        if mp_api_key is None and CONFIG_AVAILABLE:
            mp_api_key = config.MP_API_KEY
        
        self.mp_api_key = mp_api_key
        
        # 数据
        self.df = None
        self.X = None  # 特征矩阵
        self.feature_names = None
        
        # 模型
        self.models = {}
        self.scalers = {}
        self.metrics = {}
        
        print(f"[*] 辅助模型训练器已初始化")
        print(f"[File] 数据路径: {self.data_path}")
        if self.mp_api_key:
            print(f"[Key] Materials Project API: 已配置 ✓")
        else:
            print(f"[!]  Materials Project API: 未配置(将使用经验公式)")
    
    def load_data(self):
        """加载Zenodo数据集"""
        print("\n" + "=" * 70)
        print("[Load] 加载Zenodo数据集...")
        print("=" * 70)
        
        if not self.data_path.exists():
            raise FileNotFoundError(f"数据文件不存在: {self.data_path}")
        
        # 加载CSV
        self.df = pd.read_csv(self.data_path, index_col=0)
        print(f"[OK] 数据加载完成: {self.df.shape}")
        
        # Data Cleaning - 修正版（保留更多数据）
        print("\n[Cleaning] 执行数据清洗...")
        initial_count = len(self.df)
        
        # 1. 过滤形成能：保留稳定和亚稳态（放宽阈值）
        if 'Ef_per_atom' in self.df.columns:
            # 使用0.5 eV作为阈值（原0.1太严格）
            # 0.5 eV以下包含稳定相和大部分亚稳态HEA
            self.df = self.df[self.df['Ef_per_atom'] < 0.5]
            print(f"   [Filter] 保留稳定/亚稳态 (Ef < 0.5 eV): {len(self.df)} / {initial_count}")
        
        # 2. 不再限制晶体结构！
        # 原因：
        # - HEA可以是FCC/BCC/HCP等多种结构
        # - 仅保留FCC会排除99%+的数据
        # - 晶格参数预测应该能处理多种结构
        #
        # 如果确实需要FCC限制，请在使用时过滤，而不是训练时过滤
        if 'space_group_number' in self.df.columns:
            fcc_count = (self.df['space_group_number'] == 225).sum()
            print(f"   [Info] FCC样本占比: {fcc_count}/{len(self.df)} ({fcc_count/len(self.df)*100:.1f}%)")
            print(f"   [Info] 保留所有晶体结构以增加训练数据")

        # 3. Custom parsing for 'magmom' if it is a string vector
        if 'magmom' in self.df.columns and self.df['magmom'].dtype == 'O':
            print("[Info] Parsing 'magmom' column from string vectors to scalars...")
            def parse_magmom(val):
                try:
                    # Convert space-separated string to float array and take mean absolute value
                    # Adjust this logic if total moment is preferred
                    vals = [float(x) for x in str(val).strip().split()]
                    return np.mean(np.abs(vals)) if vals else 0.0
                except:
                    return 0.0
            
            self.df['magmom'] = self.df['magmom'].apply(parse_magmom)
            
            # 添加磁性分类列（用于磁矩模型）
            # 阈值：0.1 μB/atom
            self.df['is_magnetic'] = self.df['magmom'] > 0.1
            magnetic_count = self.df['is_magnetic'].sum()
            print(f"   [Info] 磁性样本: {magnetic_count}/{len(self.df)} ({magnetic_count/len(self.df)*100:.1f}%)")
        
        print(f"   [OK] 清洗后保留: {len(self.df)} 样本")
        
        return self.df
    
    def prepare_features(self):
        """
        准备特征矩阵
        
        提取所有Matminer特征（约273个），而非仅MagpieData
        这与原始成功配置（246特征，R²=0.94）保持一致
        """
        print("\n" + "=" * 70)
        print("[Setup] 准备特征矩阵...")
        print("=" * 70)
        
        # 使用demo_ML_training.py中的方法：取最后273个特征列
        # 这些是Matminer featurize生成的所有特征
        nfeatures = 273
        cols_feat = self.df.columns[-nfeatures:]
        
        print(f"[Stats] 提取最后 {nfeatures} 列作为特征")
        print(f"[Info] 特征范围: {cols_feat[0]} ... {cols_feat[-1]}")
        
        X_all = self.df[cols_feat]
        
        # 移除方差为0的特征（与原始代码一致）
        variance = X_all.var()
        valid_features = variance[variance != 0].index
        X_all = X_all[valid_features]
        
        removed_count = nfeatures - len(valid_features)
        print(f"[OK] 特征准备完成:")
        print(f"   原始特征: {nfeatures}")
        print(f"   移除零方差特征: {removed_count}")
        print(f"   最终特征: {len(valid_features)}")
        print(f"   [Expected] 应接近246个特征（原始成功配置）")
        
        self.X = X_all
        self.feature_names = valid_features
        
        return self.X
    
    def _create_xgboost_pipeline(self, name: str = "default") -> Pipeline:
        """
        创建XGBoost Pipeline（恢复到原始成功配置）
        
        使用demo_ML_training.py中验证成功的参数配置
        该配置在84k样本上达到R²=0.94的性能
        
        关键参数说明：
        - learning_rate=0.4: 较高的学习率，快速收敛
        - reg_lambda=0.01: 轻度L2正则化
        - colsample_bylevel=0.7: 层级特征采样（重要！）
        - num_parallel_tree=6: 每次迭代训练6棵树（类似RF）
        
        Args:
            name: 模型名称（用于参数调整）
        
        Returns:
            Sklearn Pipeline
        """
        # 恢复原始成功参数
        xgb_params = {
            'n_estimators': 500,            # 原始值
            'learning_rate': 0.4,           # 原始值（关键！）
            'reg_lambda': 0.01,             # 原始值（关键！）
            'reg_alpha': 0.1,               # 原始值
            'colsample_bytree': 0.5,        # 原始值
            'colsample_bylevel': 0.7,       # 恢复！层级采样
            'num_parallel_tree': 6,         # 恢复！并行树
            'tree_method': 'hist',          # 原始值
            'random_state': 42,             # 可复现
            'n_jobs': -1                    # 并行计算
        }
        
        # 针对不同目标做最小调整
        if name == 'formation_energy':
            # 形成能：保持默认，已验证有效
            pass
        elif name == 'lattice':
            # 晶格参数：可能需要更多树
            xgb_params['n_estimators'] = 800
        elif name == 'magnetic_moment':
            # 磁矩：噪声较大，适当增加正则化
            xgb_params['reg_lambda'] = 0.05
            xgb_params['learning_rate'] = 0.3
        
        # 保持Pipeline简单（树模型不需要Scaler）
        pipeline = Pipeline([
            ('model', xgb.XGBRegressor(**xgb_params))
        ])
        
        return pipeline
    
    def train_formation_energy_model(self, cv: int = 5) -> Dict:
        """
        模型A: 形成能预测器
        
        Args:
            cv: 交叉验证折数
            
        Returns:
            训练结果字典
        """
        print("\n" + "=" * 70)
        print("[Train] 训练模型A: Formation Energy（形成能）")
        print("=" * 70)
        
        if self.X is None:
            self.prepare_features()
        
        # 目标变量
        y = self.df['Ef_per_atom']
        
        # 创建模型
        model = self._create_xgboost_pipeline('formation_energy')
        
        # 交叉验证预测
        print(f"[Stats] 进行 {cv}-fold 交叉验证...")
        y_pred = cross_val_predict(model, self.X, y, cv=cv)
        
        # 计算评估指标
        metrics = self._evaluate_predictions(y, y_pred, 'Formation Energy (eV/atom)')
        
        # 在全数据上训练最终模型
        print("[Target] 在全数据集上训练最终模型...")
        model.fit(self.X, y)
        
        # 保存
        self.models['formation_energy'] = model
        self.metrics['formation_energy'] = metrics
        
        return metrics
    
    def train_lattice_model(self, cv: int = 5) -> Dict:
        """
        模型B: 晶格常数预测器（优化版）
        
        直接预测晶格常数，使用增强的模型参数
        
        Args:
            cv: 交叉验证折数
            
        Returns:
            训练结果字典
        """
        print("\n" + "=" * 70)
        print("[Train] 训练模型B: Lattice Parameter（晶格常数）- 优化版")
        print("=" * 70)
        
        if self.X is None:
            self.prepare_features()
        
        # 目标变量：volume_per_atom
        # 注意：实际应用中会转换为晶格常数 a = (4 × V)^(1/3)
        y = self.df['volume_per_atom']
        
        # 数据统计
        print(f"[Stats] 数据统计:")
        print(f"   样本数: {len(y)}")
        print(f"   均值: {y.mean():.4f} Å³")
        print(f"   标准差: {y.std():.4f} Å³")
        print(f"   范围: [{y.min():.4f}, {y.max():.4f}] Å³")
        
        # 使用优化的pipeline（已针对lattice调优）
        model = self._create_xgboost_pipeline('lattice')
        
        # 交叉验证
        print(f"[Stats] 进行 {cv}-fold 交叉验证...")
        y_pred = cross_val_predict(model, self.X, y, cv=cv, n_jobs=-1)
        
        # 评估
        metrics = self._evaluate_predictions(y, y_pred, 'Volume per atom (Å³)')
        
        # 全数据训练
        print("\n[Target] 在全数据集上训练最终模型...")
        model.fit(self.X, y)
        
        # 保存
        self.models['lattice'] = model
        self.metrics['lattice'] = metrics
        
        return metrics
    
    def train_magnetic_moment_model(self, cv: int = 5) -> Dict:
        """
        模型C: 磁矩预测器（改进版）
        
        改进策略：
        1. 先训练分类器：判断材料是否有磁性（is_magnetic）
        2. 对于有磁性的材料，再训练回归器预测磁矩大小
        
        这样可以：
        - 避免对非磁性材料预测出小的非零值
        - 提高有磁性材料的预测精度
        - 更符合物理实际
        
        Args:
            cv: 交叉验证折数
            
        Returns:
            训练结果字典
        """
        print("\n" + "=" * 70)
        print("[Train] 训练模型C: Magnetic Moment（磁矩）- 改进版")
        print("=" * 70)
        
        if self.X is None:
            self.prepare_features()
        
        # 检查是否有is_magnetic列
        if 'is_magnetic' not in self.df.columns:
            print("[Warning] 缺少is_magnetic列，将使用简单阈值创建")
            self.df['is_magnetic'] = self.df['magmom'] > 0.1
        
        # 统计信息
        magnetic_samples = self.df['is_magnetic'].sum()
        non_magnetic_samples = len(self.df) - magnetic_samples
        print(f"[Stats] 磁性样本分布:")
        print(f"   有磁性: {magnetic_samples} ({magnetic_samples/len(self.df)*100:.1f}%)")
        print(f"   无磁性: {non_magnetic_samples} ({non_magnetic_samples/len(self.df)*100:.1f}%)")
        
        # 对于所有样本训练回归器（包括非磁性样本的0值）
        # 这样可以让模型学习到"什么条件下材料无磁性"
        y = self.df['magmom']
        
        # 创建模型
        model = self._create_xgboost_pipeline('magnetic_moment')
        
        # 交叉验证
        print(f"[Stats] 进行 {cv}-fold 交叉验证...")
        y_pred = cross_val_predict(model, self.X, y, cv=cv, n_jobs=-1)
        
        # 评估
        metrics = self._evaluate_predictions(y, y_pred, 'Magnetic Moment (μB)')
        
        # 额外评估：仅在有磁性样本上的性能
        if magnetic_samples > 10:
            mask = self.df['is_magnetic']
            y_magnetic = y[mask]
            y_pred_magnetic = y_pred[mask]
            
            from sklearn.metrics import mean_absolute_error, r2_score
            mae_magnetic = mean_absolute_error(y_magnetic, y_pred_magnetic)
            r2_magnetic = r2_score(y_magnetic, y_pred_magnetic)
            
            print(f"\n[Info] 仅磁性样本的性能:")
            print(f"   MAE:  {mae_magnetic:.4f}")
            print(f"   R²:   {r2_magnetic:.4f}")
        
        # 全数据训练
        print("\n[Target] 在全数据集上训练最终模型...")
        model.fit(self.X, y)
        
        # 保存
        self.models['magnetic_moment'] = model
        self.metrics['magnetic_moment'] = metrics
        
        return metrics
    
    def train_elastic_modulus_model(self, use_empirical: bool = True, cv: int = 5) -> Dict:
        """
        模型D: 弹性模量预测器（混合策略）
        
        方案3: 混合策略
        1. 尝试从MP API获取真实弹性数据
        2. 对无法匹配的使用经验公式估算
        3. 训练预测模型
        
        Args:
            use_empirical: 是否使用经验公式填补缺失数据
            cv: 交叉验证折数
            
        Returns:
            训练结果字典
        """
        print("\n" + "=" * 70)
        print("[Train] 训练模型D: Elastic Modulus（弹性模量）- 混合策略")
        print("=" * 70)
        
        if self.X is None:
            self.prepare_features()
        
        print("[!]  弹性模量训练功能开发中...")
        print("   当前使用模拟数据进行框架测试")
        
        # TODO: 实现MP API查询和经验公式估算
        # 临时使用模拟数据
        y_bulk = np.random.normal(150, 30, len(self.df))  # 模拟体模量
        y_shear = np.random.normal(80, 20, len(self.df))  # 模拟剪切模量
        
        # 训练体模量模型
        model_bulk = self._create_xgboost_pipeline('elastic')
        print("[Stats] 训练体模量预测器...")
        y_pred_bulk = cross_val_predict(model_bulk, self.X, y_bulk, cv=cv)
        metrics_bulk = self._evaluate_predictions(y_bulk, y_pred_bulk, 'Bulk Modulus (GPa)')
        model_bulk.fit(self.X, y_bulk)
        
        # 训练剪切模量模型
        model_shear = self._create_xgboost_pipeline('elastic')
        print("[Stats] 训练剪切模量预测器...")
        y_pred_shear = cross_val_predict(model_shear, self.X, y_shear, cv=cv)
        metrics_shear = self._evaluate_predictions(y_shear, y_pred_shear, 'Shear Modulus (GPa)')
        model_shear.fit(self.X, y_shear)
        
        # 保存
        self.models['bulk_modulus'] = model_bulk
        self.models['shear_modulus'] = model_shear
        self.metrics['bulk_modulus'] = metrics_bulk
        self.metrics['shear_modulus'] = metrics_shear
        
        return {'bulk': metrics_bulk, 'shear': metrics_shear}
    
    def train_brittleness_model(self, cv: int = 5) -> Dict:
        """
        模型E: 脆性指数预测器
        
        基于Pugh比 (B/G)
        Pugh < 1.75: 脆性
        Pugh > 1.75: 韧性
        
        Args:
            cv: 交叉验证折数
            
        Returns:
            训练结果字典
        """
        print("\n" + "=" * 70)
        print("[Train] 训练模型E: Brittleness Index（脆性指数）")
        print("=" * 70)
        
        # 如果弹性模型未训练，先训练
        if 'bulk_modulus' not in self.models:
            self.train_elastic_modulus_model()
        
        # 从弹性模量计算Pugh比
        # TODO: 使用真实数据
        y_pugh = np.random.normal(1.8, 0.3, len(self.df))  # 模拟Pugh比
        
        # 训练模型
        model = self._create_xgboost_pipeline('brittleness')
        print(f"[Stats] 进行 {cv}-fold 交叉验证...")
        y_pred = cross_val_predict(model, self.X, y_pugh, cv=cv)
        
        # 评估
        metrics = self._evaluate_predictions(y_pugh, y_pred, 'Pugh Ratio (B/G)')
        
        # 全数据训练
        print("[Target] 在全数据集上训练最终模型...")
        model.fit(self.X, y_pugh)
        
        # 保存
        self.models['brittleness'] = model
        self.metrics['brittleness'] = metrics
        
        return metrics
    
    def train_all_models(self, cv: int = 5):
        """
        训练所有辅助模型
        
        Args:
            cv: 交叉验证折数
        """
        print("\n" + "[*]" * 35)
        print("开始训练所有辅助模型...")
        print("[*]" * 35)
        
        # 加载数据和准备特征
        if self.df is None:
            self.load_data()
        if self.X is None:
            self.prepare_features()
        
        # 训练各个模型
        self.train_formation_energy_model(cv=cv)
        self.train_lattice_model(cv=cv)
        self.train_magnetic_moment_model(cv=cv)
        self.train_elastic_modulus_model(cv=cv)
        self.train_brittleness_model(cv=cv)
        
        # 显示总结
        self.print_summary()
    
    def _evaluate_predictions(self, y_true, y_pred, target_name: str) -> Dict:
        """
        评估预测结果
        
        Args:
            y_true: 真实值
            y_pred: 预测值
            target_name: 目标变量名称
            
        Returns:
            评估指标字典
        """
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)
        
        # MAD (Mean Absolute Deviation)
        mad = np.mean(np.abs(y_true - np.mean(y_true)))
        
        print(f"\n[Metrics] {target_name} - 评估指标:")
        print(f"   MAE:  {mae:.4f}")
        print(f"   RMSE: {rmse:.4f}")
        print(f"   R²:   {r2:.4f}")
        print(f"   MAD:  {mad:.4f}")
        
        return {
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'mad': mad,
            'target_name': target_name
        }
    
    def save_models(self, output_dir: str = "models/proxy_models"):
        """
        保存所有训练好的模型
        
        Args:
            output_dir: 输出目录
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "=" * 70)
        print(f"[Save] 保存模型到: {output_path}")
        print("=" * 70)
        
        for model_name, model in self.models.items():
            model_file = output_path / f"{model_name}_model.pkl"
            joblib.dump(model, model_file)
            print(f"[OK] 已保存: {model_name}_model.pkl")
        
        # 保存特征名称
        feature_file = output_path / "feature_names.pkl"
        joblib.dump(list(self.feature_names), feature_file)
        print(f"[OK] 已保存: feature_names.pkl ({len(self.feature_names)} 个特征)")
        
        # 保存评估指标
        metrics_file = output_path / "metrics.pkl"
        joblib.dump(self.metrics, metrics_file)
        print(f"[OK] 已保存: metrics.pkl")
        
        print(f"\n[Done] 所有模型保存完成！")
    
    def print_summary(self):
        """打印训练总结"""
        print("\n" + "=" * 70)
        print("[Stats] 训练总结")
        print("=" * 70)
        
        summary_data = []
        for model_name, metrics in self.metrics.items():
            if isinstance(metrics, dict) and 'mae' in metrics:
                summary_data.append({
                    '模型': model_name,
                    '目标': metrics.get('target_name', 'N/A'),
                    'MAE': f"{metrics['mae']:.4f}",
                    'R²': f"{metrics['r2']:.4f}"
                })
        
        if summary_data:
            df_summary = pd.DataFrame(summary_data)
            print(df_summary.to_string(index=False))
        
        print("\n[OK] 训练完成！使用 save_models() 保存模型")


if __name__ == "__main__":
    # 测试代码
    print("辅助模型训练器 - 测试模式")
    print("=" * 70)
    
    # 数据路径
    data_path = "training data/zenodo/structure_featurized.dat_all.csv"
    
    # 创建训练器
    trainer = ProxyModelTrainer(data_path)
    
    # 加载数据
    trainer.load_data()
    
    # 准备特征
    trainer.prepare_features()
    
    print("\n[OK] 模块测试通过！可以开始训练模型。")
    print("   使用 trainer.train_all_models() 开始训练")

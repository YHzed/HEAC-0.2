"""
新数据库架构 - ORM 模型定义（v2.0）

架构设计：
- experiments: 实验基础信息
- compositions: 成分详情（相分离）
- properties: 性能指标
- calculated_features: 物理特征缓存

依赖：
- SQLAlchemy ORM
- composition_parser: 成分解析
- physics_calculator: 物理计算
- feature_engine: 特征计算
"""

from sqlalchemy import (
    create_engine, Column, Integer, Float, String, Boolean, 
    DateTime, Text, ForeignKey, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


# ==============================================================================
# 表 1: experiments - 实验基础信息
# ==============================================================================

class Experiment(Base):
    """实验基础信息表"""
    __tablename__ = 'experiments'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 元数据
    source_id = Column(String(200), index=True, comment='数据来源标记')
    raw_composition = Column(Text, comment='原始成分字符串')
    
    # 工艺参数
    sinter_temp_c = Column(Float, comment='烧结温度 (°C)')
    grain_size_um = Column(Float, comment='晶粒尺寸 (μm)')
    sinter_method = Column(String(50), comment='烧结方法')
    load_kgf = Column(Float, comment='测试载荷 (kgf)')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    composition = relationship('Composition', back_populates='experiment', uselist=False, cascade='all, delete-orphan')
    properties = relationship('Property', back_populates='experiment', uselist=False, cascade='all, delete-orphan')
    features = relationship('CalculatedFeature', back_populates='experiment', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Experiment(id={self.id}, source={self.source_id}, comp='{self.raw_composition[:30]}...')>"


# ==============================================================================
# 表 2: compositions - 成分详情（核心）
# ==============================================================================

class Composition(Base):
    """成分详情表 - 相分离"""
    __tablename__ = 'compositions'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 外键
    exp_id = Column(Integer, ForeignKey('experiments.id'), nullable=False, index=True)
    
    # 粘结相信息
    binder_formula = Column(String(200), index=True, comment='粘结相化学式（归一化）')
    binder_wt_pct = Column(Float, comment='粘结相质量百分比')
    binder_vol_pct = Column(Float, comment='粘结相体积百分比')
    
    # 陶瓷相信息
    ceramic_formula = Column(String(100), comment='主陶瓷相化学式')
    secondary_phase = Column(String(100), comment='第二陶瓷相（可选）')
    ceramic_wt_pct = Column(Float, comment='陶瓷相质量百分比')
    ceramic_vol_pct = Column(Float, comment='陶瓷相体积百分比')
    
    # 分类标记
    is_hea = Column(Boolean, index=True, comment='是否为HEA粘结相')
    element_count = Column(Integer, comment='粘结相元素数量')
    
    # 关系
    experiment = relationship('Experiment', back_populates='composition')
    
    def __repr__(self):
        return f"<Composition(exp_id={self.exp_id}, binder={self.binder_formula}, HEA={self.is_hea})>"


# ==============================================================================
# 表 3: properties - 性能指标
# ==============================================================================

class Property(Base):
    """性能指标表"""
    __tablename__ = 'properties'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 外键
    exp_id = Column(Integer, ForeignKey('experiments.id'), nullable=False, index=True)
    
    # 力学性能
    hv = Column(Float, comment='维氏硬度 (kgf/mm²)')
    kic = Column(Float, comment='断裂韧性 (MPa·m^1/2)')
    trs = Column(Float, comment='抗弯强度 (MPa)')
    youngs_modulus = Column(Float, comment='杨氏模量 (GPa)')
    
    # 等级分类（派生特征）
    hardness_grade = Column(String(20), comment='硬度等级')
    toughness_grade = Column(String(20), comment='韧性等级')
    
    # 关系
    experiment = relationship('Experiment', back_populates='properties')
    
    def __repr__(self):
        return f"<Property(exp_id={self.exp_id}, HV={self.hv}, KIC={self.kic})>"


# ==============================================================================
# 表 4: calculated_features - 物理特征缓存
# ==============================================================================

class CalculatedFeature(Base):
    """物理特征缓存表"""
    __tablename__ = 'calculated_features'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 外键
    exp_id = Column(Integer, ForeignKey('experiments.id'), nullable=False, index=True)
    
    # === 优先级 1: Proxy Model 特征 ===
    pred_formation_energy = Column(Float, comment='预测形成能 (eV/atom)')
    pred_lattice_param = Column(Float, comment='预测晶格常数 (Å)')
    pred_magnetic_moment = Column(Float, comment='预测磁矩 (μB/atom)')
    pred_bulk_modulus = Column(Float, comment='预测体积模量 (GPa)')
    pred_shear_modulus = Column(Float, comment='预测剪切模量 (GPa)')
    
    # === 优先级 2: 物理计算特征 ===
    lattice_mismatch = Column(Float, comment='晶格失配度')
    vec_binder = Column(Float, comment='粘结相VEC')
    mean_atomic_radius = Column(Float, comment='平均原子半径 (Å)')
    binder_density = Column(Float, comment='粘结相密度 (g/cm³)')
    
    # === 优先级 3: Matminer 特征（可选） ===
    magpie_mean_atomic_mass = Column(Float, comment='Magpie: 平均原子质量')
    magpie_std_electronegativity = Column(Float, comment='Magpie: 电负性标准差')
    # ... 可扩展更多 Matminer 特征
    
    # 元数据
    has_matminer = Column(Boolean, default=False, comment='是否包含 Matminer 特征')
    calculated_at = Column(DateTime, default=datetime.now, comment='计算时间')
    
    # 关系
    experiment = relationship('Experiment', back_populates='features')
    
    def __repr__(self):
        return f"<Feature(exp_id={self.exp_id}, has_matminer={self.has_matminer})>"


# ==============================================================================
# 索引优化
# ==============================================================================

# 复合索引：常用查询优化
Index('idx_comp_hea_binder', Composition.is_hea, Composition.binder_formula)
Index('idx_prop_hv_kic', Property.hv, Property.kic)


# ==============================================================================
# 数据库管理器（v2.0）
# ==============================================================================

class CermetDatabaseV2:
    """金属陶瓷数据库管理器 v2.0"""
    
    def __init__(self, db_path: str = 'cermet_master_v2.db'):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
        # 延迟加载辅助模块
        self.parser = None
        self.physics_calc = None
        self.feature_engine = None
        
        logger.info(f"Database initialized: {db_path}")
    
    def _load_helpers(self):
        """延迟加载辅助模块"""
        if self.parser is None:
            from core.composition_parser_enhanced import EnhancedCompositionParser
            from core.physics_calculator import PhysicsCalculator
            from core.feature_engine import FeatureEngine
            
            self.parser = EnhancedCompositionParser()
            self.physics_calc = PhysicsCalculator()
            self.feature_engine = FeatureEngine()
            
            logger.info("Helper modules loaded")
    
    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created")
    
    def drop_tables(self):
        """删除所有表（危险操作）"""
        Base.metadata.drop_all(self.engine)
        logger.warning("All tables dropped")
    
    def add_experiment(
        self,
        raw_composition: str,
        source_id: str = 'manual',
        sinter_temp_c: float = None,
        grain_size_um: float = None,
        sinter_method: str = None,
        load_kgf: float = None,
        hv: float = None,
        kic: float = None,
        trs: float = None,
        binder_vol_pct: float = None,  # 可选：已知体积分数
        auto_calculate_features: bool = True
    ) -> int:
        """
        添加单个实验数据
        
        Args:
            raw_composition: 原始成分字符串
            source_id: 数据来源
            sinter_temp_c: 烧结温度
            grain_size_um: 晶粒尺寸
            sinter_method: 烧结方法
            load_kgf: 测试载荷
            hv: 维氏硬度
            kic: 断裂韧性
            trs: 抗弯强度
            binder_vol_pct: 粘结相体积分数（可选）
            auto_calculate_features: 是否自动计算物理特征
            
        Returns:
            实验 ID
        """
        self._load_helpers()
        
        session = self.Session()
        
        try:
            # 1. 解析成分
            parse_result = self.parser.parse(raw_composition)
            
            if not parse_result.get('success'):
                raise ValueError(f"Failed to parse composition: {raw_composition}")
            
            # 2. 创建 Experiment 记录
            experiment = Experiment(
                source_id=source_id,
                raw_composition=raw_composition,
                sinter_temp_c=sinter_temp_c,
                grain_size_um=grain_size_um,
                sinter_method=sinter_method,
                load_kgf=load_kgf
            )
            session.add(experiment)
            session.flush()  # 获取 ID
            
            # 3. 创建 Composition 记录
            binder_wt_pct = parse_result.get('binder_wt_pct')
            
            # 计算 vol%（如果有 wt%）
            binder_vol = None
            if binder_wt_pct is not None:
                binder_vol = self.physics_calc.wt_to_vol(
                    binder_wt_pct=binder_wt_pct,
                    binder_formula=parse_result['binder_formula'],
                    ceramic_formula=parse_result['ceramic_formula']
                )
            elif binder_vol_pct is not None:
                # 如果直接提供了 vol%，反算 wt%
                binder_wt_pct = self.physics_calc.vol_to_wt(
                    binder_vol_pct=binder_vol_pct,
                    binder_formula=parse_result['binder_formula'],
                    ceramic_formula=parse_result['ceramic_formula']
                )
                binder_vol = binder_vol_pct
            
            # 判断是否 HEA
            from core.db_config import is_hea_binder
            is_hea_flag = is_hea_binder(raw_composition)
            
            # 元素数量
            element_count = len(parse_result.get('binder_elements', {}))
            
            composition = Composition(
                exp_id=experiment.id,
                binder_formula=parse_result['binder_formula'],
                binder_wt_pct=binder_wt_pct,
                binder_vol_pct=binder_vol,
                ceramic_formula=parse_result['ceramic_formula'],
                secondary_phase=parse_result.get('second ary_phase'),
                ceramic_wt_pct=100 - binder_wt_pct if binder_wt_pct else None,
                is_hea=is_hea_flag,
                element_count=element_count
            )
            session.add(composition)
            
            # 4. 创建 Property 记录
            prop = Property(
                exp_id=experiment.id,
                hv=hv,
                kic=kic,
                trs=trs
            )
            session.add(prop)
            
            # 5. 计算物理特征（可选）
            if auto_calculate_features:
                try:
                    features_dict = self.feature_engine.calculate_features(
                        binder_formula=parse_result['binder_formula'],
                        ceramic_formula=parse_result['ceramic_formula'],
                        binder_wt_pct=binder_wt_pct,
                        use_matminer=False  # 默认不使用
                    )
                    
                    proxy_feat = features_dict.get('proxy_features', {})
                    physics_feat = features_dict.get('physics_features', {})
                    
                    feature = CalculatedFeature(
                        exp_id=experiment.id,
                        pred_formation_energy=proxy_feat.get('pred_formation_energy'),
                        pred_lattice_param=proxy_feat.get('pred_lattice_param'),
                        pred_magnetic_moment=proxy_feat.get('pred_magnetic_moment'),
                        pred_bulk_modulus=proxy_feat.get('pred_bulk_modulus'),
                        pred_shear_modulus=proxy_feat.get('pred_shear_modulus'),
                        lattice_mismatch=physics_feat.get('lattice_mismatch'),
                        vec_binder=physics_feat.get('vec_binder'),
                        mean_atomic_radius=physics_feat.get('mean_atomic_radius'),
                        binder_density=physics_feat.get('binder_density'),
                        has_matminer=False
                    )
                    session.add(feature)
                    
                except Exception as e:
                    logger.warning(f"Feature calculation failed: {e}")
                    # 继续，不阻塞数据插入
            
            session.commit()
            logger.info(f"Experiment added: ID={experiment.id}")
            
            return experiment.id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to add experiment: {e}")
            raise
        finally:
            session.close()
    
    def get_experiment(self, exp_id: int) -> dict:
        """
        获取完整的实验数据
        
        Args:
            exp_id: 实验 ID
            
        Returns:
            完整数据字典
        """
        session = self.Session()
        
        try:
            exp = session.query(Experiment).filter_by(id=exp_id).first()
            
            if not exp:
                return None
            
            return {
                'id': exp.id,
                'source_id': exp.source_id,
                'raw_composition': exp.raw_composition,
                'sinter_temp_c': exp.sinter_temp_c,
                'grain_size_um': exp.grain_size_um,
                'composition': {
                    'binder_formula': exp.composition.binder_formula if exp.composition else None,
                    'binder_wt_pct': exp.composition.binder_wt_pct if exp.composition else None,
                    'ceramic_formula': exp.composition.ceramic_formula if exp.composition else None,
                    'is_hea': exp.composition.is_hea if exp.composition else None,
                } if exp.composition else {},
                'properties': {
                    'hv': exp.properties.hv if exp.properties else None,
                    'kic': exp.properties.kic if exp.properties else None,
                    'trs': exp.properties.trs if exp.properties else None,
                } if exp.properties else {},
                'features': {
                    'lattice_mismatch': exp.features.lattice_mismatch if exp.features else None,
                    'vec_binder': exp.features.vec_binder if exp.features else None,
                } if exp.features else {}
            }
            
        finally:
            session.close()
    
    def get_statistics(self) -> dict:
        """获取数据库统计信息"""
        session = self.Session()
        
        try:
            total_exp = session.query(Experiment).count()
            hea_count = session.query(Composition).filter_by(is_hea=True).count()
            trad_count = session.query(Composition).filter_by(is_hea=False).count()
            
            return {
                'total_experiments': total_exp,
                'hea_count': hea_count,
                'traditional_count': trad_count
            }
        finally:
            session.close()

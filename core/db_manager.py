"""
金属陶瓷数据库管理器

基于 SQLAlchemy + SQLite 的数据库管理系统，支持：
- 批量导入（CSV/Excel）
- 单条数据录入
- 灵活查询与筛选
- 数据标准化与清洗
"""

import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import (
    create_engine, Column, Integer, Float, String, 
    DateTime, Text, Boolean, and_, or_
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .db_config import (
    STANDARD_SCHEMA,
    FIELD_CONVERTERS,
    MISSING_VALUE_INDICATORS,
    is_hea_binder,
    validate_field,
    get_standard_field_name,
    create_column_mapping,
)

Base = declarative_base()


# ==============================================================================
# ORM 模型定义
# ==============================================================================

class MaterialRecord(Base):
    """金属陶瓷材料数据表"""
    
    __tablename__ = 'cermet_materials'
    
    # ===== 主键和元数据 =====
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    source_file = Column(String(200), comment='数据来源文件')
    
    # ===== 身份字段 =====
    composition_raw = Column(Text, comment='原始成分字符串')
    group_id = Column(String(50), comment='数据分组标记')
    subgroup = Column(Float, comment='子组编号')
    
    # ===== 组分信息 =====
    binder_vol_pct = Column(Float, comment='粘结相体积百分比 (0-100)')
    binder_wt_pct = Column(Float, comment='粘结相质量百分比 (0-100)')
    ceramic_type = Column(String(50), comment='陶瓷相类型 (WC, TiC, etc.)')
    binder_composition = Column(String(200), comment='粘结相成分')
    
    # ===== 工艺参数 =====
    sinter_temp_c = Column(Float, comment='烧结温度 (°C)')
    grain_size_um = Column(Float, comment='晶粒尺寸 (μm)')
    sinter_method = Column(String(100), comment='烧结方法 (HIP, SPS, etc.)')
    load_kgf = Column(Float, comment='测试载荷 (kgf)')
    
    # ===== 性能指标 =====
    hv = Column(Float, comment='维氏硬度 (kgf/mm²)')
    kic = Column(Float, comment='断裂韧性 (MPa·m^1/2)')
    trs = Column(Float, comment='抗弯强度 (MPa)')
    
    # ===== 扩展字段 =====
    is_hea = Column(Integer, default=0, comment='是否为 HEA 粘结相 (0=否, 1=是)')
    notes = Column(Text, comment='备注信息')
    
    def __repr__(self):
        return (
            f"<MaterialRecord(id={self.id}, "
            f"composition='{self.composition_raw}', "
            f"HV={self.hv}, KIC={self.kic})>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'created_at': self.created_at,
            'source_file': self.source_file,
            'composition_raw': self.composition_raw,
            'group_id': self.group_id,
            'subgroup': self.subgroup,
            'binder_vol_pct': self.binder_vol_pct,
            'binder_wt_pct': self.binder_wt_pct,
            'ceramic_type': self.ceramic_type,
            'binder_composition': self.binder_composition,
            'sinter_temp_c': self.sinter_temp_c,
            'grain_size_um': self.grain_size_um,
            'sinter_method': self.sinter_method,
            'load_kgf': self.load_kgf,
            'hv': self.hv,
            'kic': self.kic,
            'trs': self.trs,
            'is_hea': self.is_hea,
            'notes': self.notes,
        }


# ==============================================================================
# 数据库管理器
# ==============================================================================

class CermetDB:
    """金属陶瓷数据库管理器"""
    
    def __init__(self, db_path: str = 'cermet_materials.db'):
        """
        初始化数据库连接
        
        Args:
            db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        
        # 创建数据库引擎
        if db_path == ':memory:':
            # 内存数据库（用于测试）
            self.engine = create_engine(
                'sqlite:///:memory:',
                connect_args={'check_same_thread': False},
                poolclass=StaticPool,
                echo=False
            )
        else:
            # 文件数据库
            self.engine = create_engine(
                f'sqlite:///{db_path}',
                echo=False
            )
        
        # 创建所有表
        Base.metadata.create_all(self.engine)
        
        # 创建会话工厂
        self.Session = sessionmaker(bind=self.engine)
    
    def _normalize_row(
        self, 
        row_dict: Dict[str, Any], 
        column_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        清洗和标准化单行数据
        
        Args:
            row_dict: 原始行数据字典
            column_mapping: 列映射 {原始列名: 标准字段名}，如果为 None 则自动推断
            
        Returns:
            标准化后的数据字典
        """
        clean_data = {}
        
        # 如果没有提供映射，自动创建
        if column_mapping is None:
            column_mapping = create_column_mapping(list(row_dict.keys()))
        
        # 遍历所有标准字段
        for std_field in STANDARD_SCHEMA.keys():
            value = None
            
            # 方式1: 使用提供的列映射
            if column_mapping:
                for orig_col, mapped_field in column_mapping.items():
                    if mapped_field == std_field and orig_col in row_dict:
                        value = row_dict[orig_col]
                        break
            
            # 方式2: 直接匹配别名
            if value is None:
                for alias in STANDARD_SCHEMA[std_field]:
                    if alias in row_dict:
                        value = row_dict[alias]
                        break
            
            # 应用字段转换器
            if std_field in FIELD_CONVERTERS:
                converter = FIELD_CONVERTERS[std_field]
                value = converter(value)
            
            # 验证数值字段
            if value is not None and std_field in ['hv', 'kic', 'trs', 
                                                     'sinter_temp_c', 'grain_size_um',
                                                     'binder_vol_pct', 'binder_wt_pct']:
                is_valid, error_msg = validate_field(std_field, value)
                if not is_valid:
                    print(f"  警告: {error_msg}, 将设为 NULL")
                    value = None
            
            clean_data[std_field] = value
        
        # 自动判定 is_hea
        if clean_data.get('composition_raw'):
            clean_data['is_hea'] = 1 if is_hea_binder(clean_data['composition_raw']) else 0
        else:
            clean_data['is_hea'] = 0
        
        return clean_data
    
    def add_batch_data(
        self, 
        df: pd.DataFrame, 
        column_mapping: Optional[Dict[str, str]] = None,
        source_name: str = "batch_import"
    ) -> Tuple[int, int, List[str]]:
        """
        批量添加数据
        
        Args:
            df: 待导入的 DataFrame
            column_mapping: 列映射 {原始列名: 标准字段名}
            source_name: 数据来源标记
            
        Returns:
            (成功数量, 失败数量, 错误信息列表)
        """
        session = self.Session()
        success_count = 0
        fail_count = 0
        errors = []
        
        try:
            for idx, row in df.iterrows():
                try:
                    # 标准化数据
                    clean_data = self._normalize_row(row.to_dict(), column_mapping)
                    clean_data['source_file'] = source_name
                    
                    # 创建记录
                    record = MaterialRecord(**clean_data)
                    session.add(record)
                    success_count += 1
                    
                except Exception as e:
                    fail_count += 1
                    error_msg = f"行 {idx}: {str(e)}"
                    errors.append(error_msg)
                    print(f"  ❌ {error_msg}")
            
            # 提交事务
            session.commit()
            print(f"✅ 成功导入 {success_count} 条数据")
            if fail_count > 0:
                print(f"⚠️  失败 {fail_count} 条数据")
            
        except Exception as e:
            session.rollback()
            errors.append(f"批量导入失败: {str(e)}")
            print(f"❌ 批量导入失败: {e}")
            
        finally:
            session.close()
        
        return success_count, fail_count, errors
    
    def add_single_data(self, data_dict: Dict[str, Any]) -> Tuple[bool, str]:
        """
        添加单条数据
        
        Args:
            data_dict: 数据字典（可以使用标准字段名或原始列名）
            
        Returns:
            (成功标志, 消息)
        """
        session = self.Session()
        
        try:
            # 标准化数据
            clean_data = self._normalize_row(data_dict)
            
            # 创建记录
            record = MaterialRecord(**clean_data)
            session.add(record)
            session.commit()
            
            record_id = record.id
            session.close()
            
            return True, f"成功添加记录 (ID: {record_id})"
            
        except Exception as e:
            session.rollback()
            session.close()
            return False, f"添加失败: {str(e)}"
    
    def fetch_data(
        self,
        filters: Optional[Dict[str, Any]] = None,
        drop_na_cols: Optional[List[str]] = None,
        allow_missing_pct: Optional[float] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        查询数据并返回 DataFrame
        
        Args:
            filters: 筛选条件字典
                - 'is_hea': 0 或 1
                - 'sinter_temp_c': (min, max) 或 单个值
                - 'group_id': 字符串或列表
                等等...
            drop_na_cols: 这些列必须非空，否则丢弃该行
            allow_missing_pct: 允许的最大缺失百分比 (0-100)
            limit: 最大返回行数
            
        Returns:
            查询结果 DataFrame
        """
        query = f"SELECT * FROM {MaterialRecord.__tablename__}"
        
        # 执行查询
        df = pd.read_sql(query, self.engine)
        
        # 应用筛选条件
        if filters:
            for field, condition in filters.items():
                if field not in df.columns:
                    continue
                
                if isinstance(condition, (list, tuple)) and len(condition) == 2:
                    # 范围筛选
                    min_val, max_val = condition
                    df = df[(df[field] >= min_val) & (df[field] <= max_val)]
                elif isinstance(condition, list):
                    # 多值筛选
                    df = df[df[field].isin(condition)]
                else:
                    # 单值筛选
                    df = df[df[field] == condition]
        
        # 处理缺失值
        if drop_na_cols:
            df = df.dropna(subset=drop_na_cols)
        
        if allow_missing_pct is not None:
            # 计算每行的缺失百分比
            missing_pct = df.isnull().sum(axis=1) / len(df.columns) * 100
            df = df[missing_pct <= allow_missing_pct]
        
        # 限制返回行数
        if limit:
            df = df.head(limit)
        
        return df
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        session = self.Session()
        
        try:
            total_records = session.query(MaterialRecord).count()
            hea_records = session.query(MaterialRecord).filter(
                MaterialRecord.is_hea == 1
            ).count()
            
            # 统计各字段的非空数量
            df = self.fetch_data()
            
            stats = {
                'total_records': total_records,
                'hea_records': hea_records,
                'traditional_records': total_records - hea_records,
                'field_completeness': {
                    col: {
                        'non_null': df[col].notna().sum(),
                        'null': df[col].isna().sum(),
                        'completeness_pct': (df[col].notna().sum() / len(df) * 100) if len(df) > 0 else 0
                    }
                    for col in df.columns if col not in ['id', 'created_at', 'updated_at']
                },
                'data_sources': df['source_file'].value_counts().to_dict() if 'source_file' in df.columns else {},
            }
            
            return stats
            
        finally:
            session.close()
    
    def delete_records(self, record_ids: List[int]) -> Tuple[int, str]:
        """
        删除指定记录
        
        Args:
            record_ids: 要删除的记录 ID 列表
            
        Returns:
            (删除数量, 消息)
        """
        session = self.Session()
        
        try:
            deleted = session.query(MaterialRecord).filter(
                MaterialRecord.id.in_(record_ids)
            ).delete(synchronize_session=False)
            
            session.commit()
            return deleted, f"成功删除 {deleted} 条记录"
            
        except Exception as e:
            session.rollback()
            return 0, f"删除失败: {str(e)}"
            
        finally:
            session.close()
    
    def update_record(self, record_id: int, updates: Dict[str, Any]) -> Tuple[bool, str]:
        """
        更新单条记录
        
        Args:
            record_id: 记录 ID
            updates: 要更新的字段字典
            
        Returns:
            (成功标志, 消息)
        """
        session = self.Session()
        
        try:
            record = session.query(MaterialRecord).filter(
                MaterialRecord.id == record_id
            ).first()
            
            if not record:
                return False, f"未找到 ID={record_id} 的记录"
            
            # 更新字段
            for field, value in updates.items():
                if hasattr(record, field):
                    setattr(record, field, value)
            
            record.updated_at = datetime.now()
            session.commit()
            
            return True, f"成功更新记录 ID={record_id}"
            
        except Exception as e:
            session.rollback()
            return False, f"更新失败: {str(e)}"
            
        finally:
            session.close()
    
    def export_to_csv(self, filepath: str, filters: Optional[Dict[str, Any]] = None):
        """
        导出数据到 CSV 文件
        
        Args:
            filepath: 导出文件路径
            filters: 筛选条件（同 fetch_data）
        """
        df = self.fetch_data(filters=filters)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"✅ 已导出 {len(df)} 条数据到: {filepath}")
    
    def export_to_excel(self, filepath: str, filters: Optional[Dict[str, Any]] = None):
        """
        导出数据到 Excel 文件
        
        Args:
            filepath: 导出文件路径
            filters: 筛选条件（同 fetch_data）
        """
        df = self.fetch_data(filters=filters)
        df.to_excel(filepath, index=False, engine='openpyxl')
        print(f"✅ 已导出 {len(df)} 条数据到: {filepath}")

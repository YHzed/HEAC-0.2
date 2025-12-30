"""
Database Models (V2 schema)
Separated from the manager logic for cleaner architecture.
"""

from sqlalchemy import (
    Column, Integer, Float, String, Boolean, 
    DateTime, Text, ForeignKey, Index, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# ==============================================================================
# Table 1: experiments - Basic Experiment Info
# ==============================================================================

class Experiment(Base):
    """Experiment basic information table"""
    __tablename__ = 'experiments'
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Metadata
    source_id = Column(String(200), index=True, comment='Source Identifier')
    raw_composition = Column(Text, comment='Raw Composition String')
    
    # Process Parameters
    sinter_temp_c = Column(Float, comment='Sintering Temperature (°C)')
    grain_size_um = Column(Float, comment='Grain Size (μm)')
    sinter_method = Column(String(50), comment='Sintering Method')
    load_kgf = Column(Float, comment='Test Load (kgf)')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now, comment='Created At')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='Updated At')
    
    # Relationships
    composition = relationship('Composition', back_populates='experiment', uselist=False, cascade='all, delete-orphan')
    properties = relationship('Property', back_populates='experiment', uselist=False, cascade='all, delete-orphan')
    features = relationship('CalculatedFeature', back_populates='experiment', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Experiment(id={self.id}, source={self.source_id}, comp='{self.raw_composition[:30]}...')>"


# ==============================================================================
# Table 2: compositions - Composition Details (Core)
# ==============================================================================

class Composition(Base):
    """Composition Details - Phase Separation"""
    __tablename__ = 'compositions'
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key
    exp_id = Column(Integer, ForeignKey('experiments.id'), nullable=False, index=True)
    
    # Binder Phase Info
    binder_formula = Column(String(200), index=True, comment='Binder Chemical Formula (Normalized)')
    binder_wt_pct = Column(Float, comment='Binder Weight Percent')
    binder_vol_pct = Column(Float, comment='Binder Volume Percent')
    
    # Ceramic Phase Info
    ceramic_formula = Column(String(100), comment='Primary Ceramic Phase')
    secondary_phase = Column(String(100), comment='Secondary Ceramic Phase (Optional)')
    ceramic_wt_pct = Column(Float, comment='Ceramic Weight Percent')
    ceramic_vol_pct = Column(Float, comment='Ceramic Volume Percent')
    
    # Classification Flags
    is_hea = Column(Boolean, index=True, comment='Is HEA Binder')
    element_count = Column(Integer, comment='Binder Element Count')
    
    # Relationships
    experiment = relationship('Experiment', back_populates='composition')
    
    def __repr__(self):
        return f"<Composition(exp_id={self.exp_id}, binder={self.binder_formula}, HEA={self.is_hea})>"


# ==============================================================================
# Table 3: properties - Performance Properties
# ==============================================================================

class Property(Base):
    """Performance Properties Table"""
    __tablename__ = 'properties'
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key
    exp_id = Column(Integer, ForeignKey('experiments.id'), nullable=False, index=True)
    
    # Mechanical Properties
    hv = Column(Float, comment='Vickers Hardness (kgf/mm²)')
    kic = Column(Float, comment='Fracture Toughness (MPa·m^1/2)')
    trs = Column(Float, comment='Transverse Rupture Strength (MPa)')
    youngs_modulus = Column(Float, comment='Young\'s Modulus (GPa)')
    
    # Derived Properties / Grades
    hardness_grade = Column(String(20), comment='Hardness Grade')
    toughness_grade = Column(String(20), comment='Toughness Grade')
    
    # Relationships
    experiment = relationship('Experiment', back_populates='properties')
    
    def __repr__(self):
        return f"<Property(exp_id={self.exp_id}, HV={self.hv}, KIC={self.kic})>"


# ==============================================================================
# Table 4: calculated_features - Physics Features Cache
# ==============================================================================

class CalculatedFeature(Base):
    """Calculated Features Cache Table"""
    __tablename__ = 'calculated_features'
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key
    exp_id = Column(Integer, ForeignKey('experiments.id'), nullable=False, index=True)
    
    # === Priority 1: Proxy Model Features ===
    pred_formation_energy = Column(Float, comment='Predicted Formation Energy (eV/atom)')
    pred_lattice_param = Column(Float, comment='Predicted Lattice Parameter (Å)')
    pred_magnetic_moment = Column(Float, comment='Predicted Magnetic Moment (μB/atom)')
    pred_bulk_modulus = Column(Float, comment='Predicted Bulk Modulus (GPa)')
    pred_shear_modulus = Column(Float, comment='Predicted Shear Modulus (GPa)')
    
    # === Priority 2: Physics Calculation Features ===
    lattice_mismatch = Column(Float, comment='Lattice Mismatch')
    vec_binder = Column(Float, comment='Binder VEC')
    mean_atomic_radius = Column(Float, comment='Mean Atomic Radius (Å)')
    binder_density = Column(Float, comment='Binder Density (g/cm³)')
    
    # === Priority 3: Matminer Simplified Features (Backward Compat) ===
    magpie_mean_atomic_mass = Column(Float, comment='Magpie: Mean Atomic Mass')
    magpie_std_electronegativity = Column(Float, comment='Magpie: Std Electronegativity')
    
    # === Priority 4: Full Matminer Features (JSON Storage) ===
    ceramic_magpie_features = Column(JSON, nullable=True, comment='Full Ceramic Magpie Features (JSON)')
    binder_magpie_features = Column(JSON, nullable=True, comment='Full Binder Magpie Features (JSON)')
    
    # Metadata
    has_matminer = Column(Boolean, default=False, comment='Has Simplified Matminer Features')
    has_full_matminer = Column(Boolean, default=False, comment='Has Full Matminer Features')
    calculated_at = Column(DateTime, default=datetime.now, comment='Calculation Timestamp')
    
    # Relationships
    experiment = relationship('Experiment', back_populates='features')
    
    def __repr__(self):
        return f"<Feature(exp_id={self.exp_id}, has_full={self.has_full_matminer})>"


# ==============================================================================
# Index Optimization
# ==============================================================================

# Composite Indexes for common queries
Index('idx_comp_hea_binder', Composition.is_hea, Composition.binder_formula)
Index('idx_prop_hv_kic', Property.hv, Property.kic)
